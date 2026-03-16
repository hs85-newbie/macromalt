"""
macromalt 자동화 시스템 - AI 블로그 생성 모듈 v7.0
=====================================================
3단계 교차 검증 파이프라인 (Phase 7):
  Step 1 — Gemini 2.5-flash  : 뉴스+리서치 → 구조화된 JSON 리포트 재료 (분석 엔진)
  Step 2 — GPT-4o            : JSON 재료 → HTML 최종 원고 (작성 엔진)
  Step 3 — Gemini 2.5-flash  : HTML 초안 → 팩트체크 + 필요 시 1회 수정 (검수 엔진)
  yfinance / 네이버금융       : 실시간 종가 + 기준일 조회
  portfolio.json             : 픽 히스토리 누적 저장
  cost_tracker               : 실제 토큰 기반 예상 비용 계산 + 예산 알림

공개 API:
  Post 1 — generate_deep_analysis(news, research)
  Post 2 — generate_stock_picks_report(theme, key_data, post1_content, news, research, materials=None)
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

import markdown as md_lib
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types as genai_types

import cost_tracker
from scraper import (
    run_dart_disclosure_scan,
    run_dart_financials,
    run_dart_company_info,
    format_dart_for_prompt,
    enrich_dart_disclosures_with_fulltext,
    enrich_research_with_pdf,
    _hankyung_login,
    run_dart_annual_report_sections,
)

load_dotenv()

logger = logging.getLogger("macromalt")

# 검수 실패 시 재작성 최대 횟수 (Phase 7: 검수 1회, 재작성 1회)
MAX_RETRIES = 1

# PDF 본문 발췌 프롬프트 삽입 최대 길이 (scraper._PDF_SNIPPET_MAX=800 추출 후 삽입 시 제한)
_PDF_PROMPT_SNIPPET_LEN = 400


# ──────────────────────────────────────────────────────────────────────────────
# SECTION A-0: Phase 10 — 슬롯 분기, 이력 관리
# ──────────────────────────────────────────────────────────────────────────────

import os as _os  # 경로 처리용 (상단 import os 이미 있음, 여기서는 alias 없이 재사용)

_PUBLISH_HISTORY_PATH = os.path.join(os.path.dirname(__file__), "publish_history.json")
_PUBLISH_HISTORY_MAX  = 5  # 최근 N건만 유지


# ── 슬롯별 Gemini 분석 질문 방향 (GEMINI_ANALYST_USER에 append) ──────────────

_SLOT_ANALYST_CONTEXTS: dict = {
    "morning": (
        "\n[슬롯: 아침 — 미국장 마감 → 한국장 개장 전]\n"
        "핵심 질문 방향:\n"
        "- 이 테마가 어젯밤 미국장 마감에 어떻게 작동했으며, 오늘 한국장 개장 전에 무엇을 확인해야 하는가?\n"
        "- theme_sub_axes 권장 구성: ① 미국장 마감 원인 ② 한국장 선반영 여부 ③ 오늘 개장 전 핵심 변수\n"
        "[주제 선정 가중치 — Phase 10]\n"
        "- [최근 7일] 자료 3건 이상 수렴하는 테마를 최우선 선택한다.\n"
        "- [7-30일] 자료만 있는 테마는 현재 시황 확인 불충분으로 처리, 선택 보류.\n"
        "- [날짜불명] 자료만 있는 테마는 선택 금지.\n"
        "- 최근 7일 자료가 뒷받침되지 않는 theme_sub_axes는 생성하지 않는다.\n"
    ),
    "evening": (
        "\n[슬롯: 저녁 — 한국장 마감 리뷰]\n"
        "핵심 질문 방향:\n"
        "- 이 테마가 오늘 한국장에서 실제로 어떤 업종/종목 차별화를 만들었으며, 내일 어디를 봐야 하는가?\n"
        "- theme_sub_axes 권장 구성: ① 오늘 한국장 주요 움직임 ② 예상 대비 차이와 원인 ③ 내일 체크포인트\n"
        "[주제 선정 가중치 — Phase 10]\n"
        "- [최근 7일] 자료 3건 이상 수렴하는 테마를 최우선 선택한다.\n"
        "- [7-30일] 자료만 있는 테마는 현재 시황 확인 불충분으로 처리, 선택 보류.\n"
        "- [날짜불명] 자료만 있는 테마는 선택 금지.\n"
        "- 최근 7일 자료가 뒷받침되지 않는 theme_sub_axes는 생성하지 않는다.\n"
    ),
    "us_open": (
        "\n[슬롯: 미국장 개장 전]\n"
        "핵심 질문 방향:\n"
        "- 오늘 밤 미국장에서 이 테마가 추가 반영될까, 되돌릴까?\n"
        "  뉴스/선물/금리/유가/실적 중 무엇이 가장 큰 변수인가?\n"
        "- theme_sub_axes 권장 구성: ① 오늘 밤 미국장 핵심 변수 ② 반영/되돌림 시나리오 ③ 주목 데이터 포인트\n"
        "[주제 선정 가중치 — Phase 10]\n"
        "- [최근 7일] 자료 3건 이상 수렴하는 테마를 최우선 선택한다.\n"
        "- [7-30일] 자료만 있는 테마는 현재 시황 확인 불충분으로 처리, 선택 보류.\n"
        "- [날짜불명] 자료만 있는 테마는 선택 금지.\n"
        "- 최근 7일 자료가 뒷받침되지 않는 theme_sub_axes는 생성하지 않는다.\n"
    ),
    "default": (
        "\n[슬롯: 일반 브리핑]\n"
        "핵심 질문 방향:\n"
        "- 특정 시장 개장/마감 문맥에 구애받지 않고, 현재 시점에서 가장 중요한 경제/금융 이슈를 중심으로 분석한다.\n"
        "- theme_sub_axes: 현재 데이터에서 인과관계가 가장 선명한 3개 하위 축으로 자유 구성.\n"
        "[주제 선정 가중치 — Phase 10]\n"
        "- [최근 7일] 자료 3건 이상 수렴하는 테마를 최우선 선택한다.\n"
        "- [7-30일] 자료만 있는 테마는 현재 시황 확인 불충분으로 처리, 선택 보류.\n"
        "- [날짜불명] 자료만 있는 테마는 선택 금지.\n"
        "- 최근 7일 자료가 뒷받침되지 않는 theme_sub_axes는 생성하지 않는다.\n"
    ),
}

# ── 슬롯별 GPT Post1 작성 방향 (GPT_WRITER_ANALYSIS_USER에 prepend) ──────────

_SLOT_POST1_WRITER_HINTS: dict = {
    "morning": (
        "[슬롯 작성 방향 — 아침]\n"
        "이 글은 '미국장 마감 원인 + 오늘 한국장 개장 전 프리뷰' 구조로 작성한다.\n"
        "- 섹션 1: overnight 핵심 변수가 미국장 마감에 어떻게 작용했는가\n"
        "- 섹션 2: 그 흐름이 한국장에 어떤 방향으로 연결될 수 있는가\n"
        "- 섹션 3: 오늘 한국 개장 전 확인해야 할 핵심 체크포인트\n"
    ),
    "evening": (
        "[슬롯 작성 방향 — 저녁]\n"
        "이 글은 '한국장 실제 결과 + 내일 체크포인트' 구조로 작성한다.\n"
        "- 섹션 1: 오늘 한국장의 실제 결과 — 어떤 업종/종목이 차별화됐는가\n"
        "- 섹션 2: 오전 예상과 실제 결과의 차이 — 무엇이 달랐는가, 왜인가\n"
        "- 섹션 3: 내일을 위한 변수 — 내일 체크해야 할 핵심 포인트\n"
    ),
    "us_open": (
        "[슬롯 작성 방향 — 미국장 개장 전]\n"
        "이 글은 '오늘 밤 미국장 핵심 변수 브리핑' 구조로 작성한다.\n"
        "- 섹션 1: 오늘 밤 미국장의 핵심 변수 — 뉴스/선물/금리/유가/실적 중 무엇인가\n"
        "- 섹션 2: 이 변수가 추가 반영될 시나리오 vs 되돌릴 시나리오\n"
        "- 섹션 3: 오늘 밤 주목할 데이터/이벤트 포인트\n"
    ),
    "default": (
        "[슬롯 작성 방향 — 일반 브리핑]\n"
        "특정 시장 개장/마감 시점에 구애받지 않는 중립 구조로 작성한다.\n"
        "- 섹션 1: 현재 시점의 핵심 경제·금융 이슈와 배경\n"
        "- 섹션 2: 이 이슈의 시장 파급 경로와 업종/자산 영향\n"
        "- 섹션 3: 향후 주목해야 할 변수와 체크포인트\n"
    ),
}

# ── 슬롯별 GPT Post2(캐시의 픽) 작성 방향 ────────────────────────────────────

_SLOT_POST2_WRITER_HINTS: dict = {
    "morning": (
        "[Post2 슬롯 방향 — 아침]\n"
        "한국장 개장 전, 이 테마 맥락에서 상대적으로 체크할 종목·섹터를 선정한다.\n"
        "오늘 개장 시 구체적 트리거가 있는 종목을 우선한다.\n"
    ),
    "evening": (
        "[Post2 슬롯 방향 — 저녁]\n"
        "오늘 한국장에서 이 테마 관련 실제로 의미 있었던 종목·섹터를 선정한다.\n"
        "내일도 논리가 지속될 근거가 있는 종목을 우선한다.\n"
    ),
    "us_open": (
        "[Post2 슬롯 방향 — 미국장 개장 전]\n"
        "오늘 밤 미국장에서 이 테마에 상대적으로 민감할 종목·섹터를 선정한다.\n"
        "오늘 밤 변수에 직접 노출되는 종목을 우선한다.\n"
    ),
    "default": (
        "[Post2 슬롯 방향 — 일반 브리핑]\n"
        "현재 테마 맥락에서 논리가 선명하고 데이터 근거가 풍부한 종목·섹터를 선정한다.\n"
    ),
}


def _load_publish_history() -> list:
    """publish_history.json에서 최근 발행 이력을 로드합니다."""
    if not os.path.exists(_PUBLISH_HISTORY_PATH):
        return []
    try:
        with open(_PUBLISH_HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_publish_history(slot: str, post1: dict, post2: Optional[dict]) -> None:
    """파이프라인 완료 후 발행 이력을 publish_history.json에 저장합니다.
    최대 _PUBLISH_HISTORY_MAX 건만 유지합니다 (오래된 것부터 제거).
    Phase 11: theme_fingerprint / sub_axes_fingerprint / tickers / stock_buckets 추가.
    """
    history = _load_publish_history()

    theme_str  = post1.get("theme", "")
    sub_axes   = post1.get("materials", {}).get("theme_sub_axes", [])
    tickers    = [p.get("ticker", "") for p in (post2.get("picks", []) if post2 else [])]

    theme_fp   = _make_theme_fingerprint(theme_str)
    axes_fp    = _make_axes_fingerprint(sub_axes)
    buckets    = _make_ticker_buckets(tickers)

    entry = {
        "published_at":        datetime.now().isoformat(),
        "slot":                slot,
        "theme":               theme_str,
        "theme_fingerprint":   theme_fp,
        "sub_axes":            sub_axes,
        "sub_axes_fingerprint": axes_fp,
        "post1_title":         post1.get("title", ""),
        "post2_title":         post2.get("title", "") if post2 else "",
        "tickers":             tickers,
        "stock_buckets":       buckets,
    }
    history.append(entry)
    # 최근 N건만 유지
    history = history[-_PUBLISH_HISTORY_MAX:]
    with open(_PUBLISH_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    logger.info(
        f"[Phase 11] 이력 저장 | 슬롯: {slot} | theme_fp: {theme_fp} | "
        f"axes_fp: {axes_fp} | buckets: {buckets} | 테마: {theme_str[:40]}"
    )


def _log_freshness_summary(articles: list, research: list) -> None:
    """수집 자료의 date_tier 분포를 INFO 로그로 기록합니다 (Phase 10)."""
    all_items = articles + research
    counts: dict = {"recent": 0, "extended": 0, "old": 0, "unknown": 0}
    for item in all_items:
        tier = item.get("date_tier", "unknown")
        counts[tier] = counts.get(tier, 0) + 1
    logger.info(
        f"[Phase 10] 자료 분류: 7일이내 {counts['recent']}건 | "
        f"8-30일 {counts['extended']}건 | 제외(old) {counts['old']}건 | "
        f"날짜불명 {counts['unknown']}건"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SECTION A-1: Phase 11 — 반복 완화 Fingerprint 엔진
# ──────────────────────────────────────────────────────────────────────────────

# ── A. theme fingerprint ─────────────────────────────────────────────────────
# macro 카테고리 10개. 복수 매칭 허용 (예: "에너지_유가|지정학_전쟁").
_THEME_KEYWORD_GROUPS: dict = {
    "관세_무역":    ["관세", "tariff", "무역전쟁", "무역", "통상", "수출규제", "보호무역", "관세장벽"],
    "금리_통화":    ["금리", "연준", "fed", "기준금리", "통화정책", "긴축", "완화", "피봇", "인상", "인하", "fomc"],
    "에너지_유가":  ["유가", "원유", "oil", "에너지", "wti", "brent", "opec", "정유", "석유"],
    "지정학_전쟁":  ["지정학", "전쟁", "분쟁", "긴장", "중동", "러시아", "우크라이나", "이란", "이스라엘", "북한"],
    "반도체_기술":  ["반도체", "chip", "ai", "인공지능", "빅테크", "기술주", "엔비디아", "hbm", "파운드리"],
    "환율_달러":    ["환율", "달러", "원달러", "강달러", "약달러", "외환", "달러인덱스", "dxy"],
    "인플레_물가":  ["인플레", "물가", "cpi", "pce", "소비자물가", "인플레이션", "디플레"],
    "고용_노동":    ["고용", "실업", "일자리", "nfp", "비농업", "임금", "고용지표"],
    "부동산_리츠":  ["부동산", "reit", "리츠", "주택", "모기지"],
    "중국_신흥":    ["중국", "위안", "yuan", "신흥국", "emerging", "홍콩", "항셍"],
}

def _make_theme_fingerprint(theme_str: str) -> str:
    """theme 문자열 → 정규화된 macro category fingerprint 문자열.

    복수 카테고리 매칭 허용. 매칭 없으면 '기타' (감점 없음).
    예: "중동 지정학 리스크와 국제유가 급등" → "에너지_유가|지정학_전쟁"
    """
    if not theme_str:
        return "기타"
    t = theme_str.lower()
    matched = sorted(
        cat for cat, kws in _THEME_KEYWORD_GROUPS.items()
        if any(kw in t for kw in kws)
    )
    return "|".join(matched) if matched else "기타"


# ── B. sub_axes fingerprint ───────────────────────────────────────────────────
# 11개 axis_id. 각 sub_axes 항목을 axis_id 하나로 매핑.
_AXES_KEYWORD_GROUPS: dict = {
    "미국장_마감":    ["미국장 마감", "overnight", "어젯밤", "뉴욕장 마감", "미장 마감"],
    "한국장_개장":    ["한국장 개장", "코스피 개장", "개장 전", "프리마켓", "장 전"],
    "한국장_마감":    ["한국장 마감", "코스피 마감", "오늘 한국장", "코스닥 마감"],
    "미국장_개장":    ["미국장 개장", "오늘 밤 미국장", "뉴욕 개장", "나스닥 선물"],
    "업종_차별화":    ["업종", "섹터", "차별화", "sector", "업종별"],
    "금리_채권":      ["금리", "채권", "국채", "yield", "금리인상", "금리인하"],
    "환율_달러":      ["환율", "달러", "원달러", "달러강세", "달러약세"],
    "수출_무역":      ["수출", "무역", "관세", "수입", "교역"],
    "에너지_원자재":  ["유가", "원자재", "에너지", "금값", "원유"],
    "실적_이벤트":    ["실적", "어닝", "earning", "발표", "이벤트", "어닝시즌"],
    "거시_시나리오":  ["시나리오", "전망", "outlook", "리스크", "경기침체", "연착륙"],
}

def _make_axes_fingerprint(axes: list) -> list:
    """sub_axes 리스트 → axis_id 리스트.

    각 항목을 _AXES_KEYWORD_GROUPS에서 첫 번째 매칭 axis_id로 변환.
    매칭 없으면 '기타'.
    """
    result = []
    for ax in (axes or []):
        ax_lower = ax.lower()
        matched = next(
            (ax_id for ax_id, kws in _AXES_KEYWORD_GROUPS.items()
             if any(kw in ax_lower for kw in kws)),
            "기타"
        )
        result.append(matched)
    return result


# ── C. 종목군 fingerprint ─────────────────────────────────────────────────────
# 티커 코드(숫자 KR 포함) → 버킷 8종. 미매핑은 '기타'.
_TICKER_BUCKET_MAP: dict = {
    # 에너지
    "XLE": "에너지", "XOM": "에너지", "CVX": "에너지", "COP": "에너지",
    "PSX": "에너지", "VLO": "에너지", "MPC": "에너지",
    "010950": "에너지",   # S-Oil
    "096770": "에너지",   # SK이노베이션
    "078930": "에너지",   # GS
    # 반도체·기술
    "NVDA": "반도체_기술", "AMD": "반도체_기술", "INTC": "반도체_기술",
    "SOXX": "반도체_기술", "SMH": "반도체_기술", "AVGO": "반도체_기술",
    "QCOM": "반도체_기술", "MU": "반도체_기술", "TSM": "반도체_기술",
    "005930": "반도체_기술",   # 삼성전자
    "000660": "반도체_기술",   # SK하이닉스
    "042700": "반도체_기술",   # 한미반도체
    "091990": "반도체_기술",   # 셀트리온헬스케어(보조)
    # 금융
    "XLF": "금융", "JPM": "금융", "GS": "금융", "BAC": "금융",
    "MS": "금융", "C": "금융", "BRK-B": "금융",
    "105560": "금융",   # KB금융
    "055550": "금융",   # 신한지주
    "086790": "금융",   # 하나금융
    # 방산·지정학
    "LMT": "방산", "RTX": "방산", "NOC": "방산", "GD": "방산", "BA": "방산",
    "012450": "방산",   # 한화에어로스페이스
    "047810": "방산",   # 한국항공우주
    "064350": "방산",   # 현대로템
    # 빅테크·인터넷
    "AAPL": "빅테크", "MSFT": "빅테크", "GOOGL": "빅테크", "META": "빅테크",
    "AMZN": "빅테크", "NFLX": "빅테크",
    "035420": "빅테크",   # NAVER
    "035720": "빅테크",   # 카카오
    # 소비재·유통
    "XLY": "소비재", "HD": "소비재", "TGT": "소비재", "WMT": "소비재",
    # 유틸·리츠
    "XLU": "유틸_리츠", "VNQ": "유틸_리츠", "O": "유틸_리츠",
    # 지수ETF
    "SPY": "지수ETF", "QQQ": "지수ETF", "IWM": "지수ETF",
    "DIA": "지수ETF", "VTI": "지수ETF",
    "069500": "지수ETF",   # KODEX 200
    "122630": "지수ETF",   # KODEX 레버리지
}

def _make_ticker_buckets(tickers: list) -> list:
    """티커 리스트 → 섹터 버킷 집합 (중복 제거, 정렬).

    미매핑 티커는 '기타'. '.KS'/'.KQ' 접미사는 제거 후 조회.
    """
    buckets: set = set()
    for t in (tickers or []):
        code = t.split(".")[0].upper()
        buckets.add(_TICKER_BUCKET_MAP.get(code, "기타"))
    return sorted(buckets)


# ── D/E. 반복 감지 + 회전 지시 생성 (Phase 11 핵심) ──────────────────────────

# 감점 강도 순위 (높을수록 강함)
_PENALTY_RANK = {"NONE": 0, "MILD": 1, "BUCKET": 2, "STRONG": 3}

def _build_history_context(slot: str) -> str:
    """최근 발행 이력 → Gemini 분석 프롬프트용 컨텍스트 문자열.

    Phase 11: theme_fingerprint 기반 per-theme 조건부 반복 감지.
    - D1 (STRONG): 같은 theme_fp + sub_axes_fp 있음 + ≤24h
                   → "이 theme를 다시 선정하면 다른 축을 쓰라"
    - D2 (BUCKET): 같은 theme_fp + non-기타 bucket + ≤24h
                   → "이 theme를 다시 선정하면 다른 섹터를 쓰라"
    - D3 (MILD):   같은 slot + ≤48h (theme 무관)
                   → "같은 슬롯에서 반복이므로 관점 최소 2개 교체"
    규칙은 per-theme으로 축적되고, 가장 강한 규칙 하나만 지시문으로 출력.
    다른 slot의 항목도 D1/D2 경고 대상이 된다 (이유: 뉴스가 같으면 theme도 같다).
    """
    history = _load_publish_history()
    if not history:
        return ""

    now = datetime.now()
    lines = [f"\n[최근 발행 이력 — {len(history)}건 | Phase 11 반복 완화 규칙]"]

    # per-theme 누적: theme_fp → {"worst": str, "axes": list, "buckets": set, "ages": list}
    theme_penalties: dict = {}
    mild_slot_hit = False

    for entry in reversed(history):  # 최신 순
        pub_str   = entry.get("published_at", "")
        e_slot    = entry.get("slot", "")
        theme_raw = entry.get("theme", "")
        p1_title  = entry.get("post1_title", "")

        # fingerprint: 이력에 저장된 값 우선, 없으면 즉석 계산
        theme_fp  = entry.get("theme_fingerprint") or _make_theme_fingerprint(theme_raw)
        axes_fp   = entry.get("sub_axes_fingerprint") or _make_axes_fingerprint(
                        entry.get("sub_axes", []))
        e_buckets = entry.get("stock_buckets") or _make_ticker_buckets(
                        entry.get("tickers", []))

        age_h     = None
        age_label = "시점불명"
        try:
            pub_dt    = datetime.fromisoformat(pub_str)
            age_h     = (now - pub_dt).total_seconds() / 3600
            age_label = f"{age_h:.0f}시간 전"
        except Exception:
            pass

        lines.append(
            f"- [{e_slot}] {age_label} | theme_fp={theme_fp} | "
            f"axes={axes_fp} | buckets={e_buckets} | 제목: {p1_title[:35]}"
        )

        if age_h is None:
            continue

        # ── D3: MILD — same slot + ≤48h (theme 무관) ─────────────────────
        if age_h <= 48 and e_slot == slot:
            mild_slot_hit = True

        if theme_fp == "기타":
            continue   # 미분류 theme는 D1/D2 감지 제외

        # ── D1/D2: per-theme 조건부 규칙 ─────────────────────────────────
        if theme_fp not in theme_penalties:
            theme_penalties[theme_fp] = {
                "worst": "NONE", "axes": [], "buckets": set(), "ages": []
            }
        rec = theme_penalties[theme_fp]
        rec["ages"].append(age_h)

        if age_h <= 24:
            # D1: STRONG — sub_axes_fp 있으면 "다른 축 사용" 지시
            if axes_fp:
                rec["axes"].extend(axes_fp)
                if _PENALTY_RANK["STRONG"] > _PENALTY_RANK[rec["worst"]]:
                    rec["worst"] = "STRONG"

            # D2: BUCKET — non-기타 bucket 있으면 "다른 섹터" 지시
            non_etc = [b for b in e_buckets if b != "기타"]
            if non_etc:
                rec["buckets"].update(non_etc)
                if _PENALTY_RANK["BUCKET"] > _PENALTY_RANK[rec["worst"]]:
                    rec["worst"] = "BUCKET"

    # ── 지시문 생성 ───────────────────────────────────────────────────────────
    instruction_lines = []
    log_details       = []

    # per-theme STRONG/BUCKET 지시 (theme_fp별)
    for fp, rec in theme_penalties.items():
        if rec["worst"] == "STRONG":
            avoid_axes = sorted(set(rec["axes"]))
            instruction_lines.append(
                f"\n[⚠ 반복 감지 STRONG | theme={fp}]\n"
                f"→ 24h 이내 이 theme 관련 발행이 있었습니다. "
                f"같은 theme를 다시 선정한다면:\n"
                f"  - theme_sub_axes 전체를 이전({avoid_axes})과 다른 인과 경로·축으로 교체하십시오.\n"
                f"  - Post1은 거시 메커니즘·파급 경로 중심, Post2는 종목·트리거·민감도 중심으로 역할을 분리하십시오."
            )
            log_details.append(f"STRONG(theme={fp}, axes={avoid_axes})")

        elif rec["worst"] == "BUCKET":
            hit_bkts  = sorted(rec["buckets"])
            all_bkts  = sorted(set(_TICKER_BUCKET_MAP.values()) - {"기타"} - set(hit_bkts))
            alt_sug   = "·".join(all_bkts[:3]) if all_bkts else "다른 섹터"
            instruction_lines.append(
                f"\n[⚠ 반복 감지 BUCKET | theme={fp}]\n"
                f"→ 24h 이내 이 theme에서 종목군({', '.join(hit_bkts)})이 사용되었습니다. "
                f"같은 theme를 다시 선정한다면:\n"
                f"  - Post2 종목은 위 버킷을 피하고 대안 섹터({alt_sug})에서 우선 선정하십시오.\n"
                f"  - 완전 회피가 어렵다면 같은 버킷 내에서도 다른 트리거 논거를 사용하십시오."
            )
            log_details.append(f"BUCKET(theme={fp}, buckets={hit_bkts})")

    # MILD: 전역 지시 (theme 무관, slot 기준)
    if mild_slot_hit:
        instruction_lines.append(
            f"\n[⚠ 반복 감지 MILD | slot={slot}]\n"
            f"→ 48h 이내 동일 슬롯에서 발행이 있었습니다. "
            f"같은 테마를 선정한다면 theme_sub_axes 중 최소 2개 이상을 이전과 다른 관점으로 교체하십시오."
        )
        log_details.append(f"MILD(slot={slot})")

    lines.extend(instruction_lines)

    # 로그
    if log_details:
        logger.info(f"[Phase 11] 반복 감지 지시 삽입 | {' / '.join(log_details)}")
    else:
        logger.info("[Phase 11] 반복 감지 없음 — 정상 발행")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# SECTION A-2: Phase 12 — 증거 밀도 & 글쓰기 품질 강화
# ──────────────────────────────────────────────────────────────────────────────

# ── 품질 임계값 설정 (튜닝 가능) ───────────────────────────────────────────────
_P12_QUALITY_THRESHOLDS: dict = {
    "numeric_density_pass":  5,   # 숫자 패턴 5개 이상 → PASS
    "numeric_density_warn":  2,   # 2~4개 → WARN, 2 미만 → FAIL
    "time_anchor_pass":      3,   # 시점 앵커 3개 이상 → PASS
    "time_anchor_warn":      1,   # 1~2개 → WARN, 0 → FAIL
    "counterpoint_pass":     2,   # 반론 마커 2개 이상 → PASS
    "counterpoint_warn":     1,   # 1개 → WARN, 0 → FAIL
    "generic_phrase_pass":   2,   # 일반어 2개 이하 → PASS
    "generic_phrase_warn":   5,   # 3~5개 → WARN, 6 이상 → FAIL
    "evidence_binding_pass": 2,   # 출처 패턴 2개 이상 → PASS
}

# ── 일반적(비근거) 표현 목록 ────────────────────────────────────────────────────
_P12_GENERIC_PHRASES: list = [
    "긍정적", "영향을 줄 수 있다", "주목할 필요", "관심이 필요",
    "부각될 수 있다", "기대감", "수혜 기대", "기대감이 높아", "전망이 밝",
    "불확실성이 높아", "변동성 확대", "면밀한 모니터링", "추이를 지켜볼",
    "관심이 집중", "주목받고 있", "시장의 관심",
]

# ── 반론 마커 목록 ──────────────────────────────────────────────────────────────
_P12_COUNTERPOINT_MARKERS: list = [
    "반대", "반론", "다만", "그러나", "하지만", "단,", "단 ",
    "리스크", "불확실", "우려", "하락 가능", "약세 전환", "체크포인트",
    "과도한 기대", "반영 과잉", "되돌림", "조정 가능", "역풍",
]

# ── Gemini 분석 단계 — 증거 밀도 지시 (user 메시지에 append) ─────────────────
_P12_ANALYST_EVIDENCE_RULES: str = """
[Phase 12 — 분석 재료 증거 밀도 규칙]
1. facts 배열 각 항목의 content 필드는 가능하면 수치(%, 금액, 성장률, 날짜, 분기)를 포함한다.
   수집 자료에 수치가 없는 경우 → writing_notes에 "수치 근거 부족: [해당 축]" 형태로 명시한다.
2. theme_sub_axes 3개는 각각 facts 배열의 다른 항목과 연결되어야 하며,
   최소 1개의 축은 구체적 수치(변화율, 금액, 날짜)를 포함한 팩트로 뒷받침되어야 한다.
3. market_impact는 추상 서술("우려 증가") 대신
   "지표 X 변화 → 섹터/시장 Y에 영향 Z" 구조로 작성한다.
4. counter_interpretations는 "불확실성 우려" 수준이 아니라
   구체적 조건("지표 X가 Y 수준 이상 지속되면 Z 이유로 역풍")으로 작성한다.
5. 수집 자료에 없는 수치를 임의로 생성·추정하지 않는다.
   근거 없는 수치는 생략하고 writing_notes에 부재 사실을 기록한다.
"""

# ── GPT Post1 — 증거 밀도 & 구조 지시 (user 메시지에 prepend) ─────────────────
_P12_POST1_EVIDENCE_RULES: str = """[Phase 12 — Post1 근거 밀도 & 구조 규칙]
1. 각 <h3> 섹션에 아래 4요소를 반드시 포함한다:
   ① 구체 사실(날짜·출처 포함) ② 수치 또는 시점 앵커 ③ 인과 경로 ④ 영향 대상(업종/국가/섹터)
2. 시점 앵커 필수: 각 섹션에 최소 1개의 날짜·기간 표현
   (예: "이번 주", "지난 분기", "2024년 Q3", "최근 3개월", "N일 기준")
   수집 자료에 날짜가 없으면 "시점 불명" 명시 후 서술한다.
3. 반대 시각 섹션은 추상("불확실성 우려") 대신
   구체 조건+수치+근거("X 지표가 Y 수준 유지 시 Z 리스크")로 작성한다.
4. 수집 자료에 없는 수치는 생성하지 않는다.
   수치 없이 서술해야 하면 "[수치 미확인]" 표시 후 사실 기반 서술로 대체한다.
5. Post1은 거시·시장 구조·파급 경로 중심. Post2 종목 분석과 동일 문장 반복 금지.
"""

# ── GPT Post2 — 증거 밀도 & 구조 지시 (user 메시지에 prepend) ─────────────────
_P12_POST2_EVIDENCE_RULES: str = """[Phase 12 — Post2 근거 밀도 & 구조 규칙]
1. 각 종목 섹션은 4단계 구조를 따른다:
   ① Why now: 최근 7일 이내 구체 사건·발표·수치 필수 (추상 이유 단독 불가)
   ② 실적·사업 근거: 매출/영업이익/성장률/PER/수주잔고 중 최소 1개
   ③ 리서치·데이터 연결: 애널리스트 의견 또는 산업 데이터 최소 2건
   ④ 반영된 변수: 이미 주가에 반영된 기대치 (PER 배수, 수급 집중 기간 등)
2. 수치 미확인 시: "[수치 미확인 — 사유]" 명시 후 이벤트·공시·발표 팩트로 대체한다.
3. Post1 거시 배경을 그대로 반복하지 않는다. 종목·섹터 레벨 구체 이유에 집중한다.
4. 수집 자료에 없는 수치·전망치는 절대 생성하지 않는다.
"""

# ── 수치 하이라이트 블록 생성 임계값 ────────────────────────────────────────────
_P12_HIGHLIGHT_MIN_ITEMS = 3    # 이 수 이상일 때만 블록 생성
_P12_HIGHLIGHT_MAX_ITEMS = 12   # 최대 항목 수


def _build_numeric_highlight_block(articles: list, research: list) -> str:
    """Phase 12: 수집 자료에서 수치/날짜 포함 문장을 요약해 Gemini 입력에 선주입.

    LLM이 구체적 수치를 더 쉽게 발견하도록 입력 패킹을 개선한다.
    수집 자료를 수정하지 않고, 별도 블록으로 prepend만 수행 (비파괴).
    """
    _num_pat = re.compile(
        r"[^\n]{5,50}"
        r"(?:\d+[.,]?\d*\s*[%\$₩원억조만배달러]"
        r"|\d{4}년|\d{1,2}월\s*\d{1,2}일"
        r"|[Qq][1-4]|[1-4]분기"
        r"|(?:전년|전월|전분기|YoY|QoQ)[\s비]*\d)"
        r"[^\n]{0,40}",
        re.IGNORECASE,
    )

    seen: set = set()
    evidence: list = []

    # 리서치 우선 (weight 높은 항목)
    sorted_res = sorted(research, key=lambda x: x.get("weight", 0), reverse=True)
    for item in sorted_res[:10]:
        for field in ("summary", "content", "pdf_snippet"):
            text = item.get(field) or ""
            for m in _num_pat.findall(text)[:2]:
                snippet = m.strip()
                if snippet not in seen and len(snippet) >= 10:
                    source = item.get("source", "리서치")
                    evidence.append(f"[{source}] {snippet}")
                    seen.add(snippet)

    # 뉴스 보완 (recent tier 우선)
    sorted_art = sorted(
        articles, key=lambda x: 0 if x.get("date_tier") == "recent" else 1
    )
    for item in sorted_art[:10]:
        text = item.get("summary") or ""
        for m in _num_pat.findall(text)[:1]:
            snippet = m.strip()
            if snippet not in seen and len(snippet) >= 10:
                source = item.get("source", "뉴스")
                evidence.append(f"[{source}] {snippet}")
                seen.add(snippet)

    evidence = evidence[:_P12_HIGHLIGHT_MAX_ITEMS]

    if len(evidence) < _P12_HIGHLIGHT_MIN_ITEMS:
        return ""   # 수치 항목이 너무 적으면 블록 생략 (noise 방지)

    lines = ["\n[📊 Phase 12 — 수치 근거 요약 | 아래 수치를 근거로 우선 활용하십시오]"]
    lines.extend(f"- {e}" for e in evidence)
    lines.append("")
    logger.info(f"[Phase 12] 수치 하이라이트 블록 생성: {len(evidence)}개 항목")
    return "\n".join(lines)


def _score_post_quality(content: str, label: str = "") -> dict:
    """Phase 12: 생성된 HTML post의 증거 밀도 & 구조 품질을 rule-based로 평가.

    비파괴적 진단 전용 — 출력을 수정하거나 차단하지 않음.
    결과는 로그에 기록되고 dict로 반환된다.

    Returns:
        {
          "numeric_density": "PASS"|"WARN"|"FAIL",
          "time_anchor": "PASS"|"WARN"|"FAIL",
          "counterpoint_presence": "PASS"|"WARN"|"FAIL",
          "generic_wording": "PASS"|"WARN"|"FAIL",
          "evidence_binding": "PASS"|"WARN"|"FAIL",
          + numeric counts
        }
    """
    t = _P12_QUALITY_THRESHOLDS

    # 1. 숫자 밀도
    num_patterns = re.findall(
        r"\d+[.,]?\d*\s*[%\$₩원억조만배달러엔]"
        r"|\d{4}년\s*\d{1,2}월"
        r"|\d{4}년\s*[Qq1-4]분기"
        r"|\d{1,3}[.,]\d+%"
        r"|[+-]?\d+[.,]?\d*\s*[pP][pP]"
        r"|[A-Z]{2,5}\s*\d{3,5}",
        content,
    )
    num_count = len(num_patterns)
    numeric_density = (
        "PASS" if num_count >= t["numeric_density_pass"]
        else "WARN" if num_count >= t["numeric_density_warn"]
        else "FAIL"
    )

    # 2. 시점 앵커
    time_anchors = re.findall(
        r"\d{4}년|\d{1,2}월\s*\d{1,2}일|\d{4}년\s*[Qq1-4]분기"
        r"|이번\s*주|지난\s*주|어제|오늘|최근\s*\d+[일주개월년]"
        r"|전월|전분기|전년|YoY|QoQ",
        content,
    )
    time_count = len(time_anchors)
    time_anchor = (
        "PASS" if time_count >= t["time_anchor_pass"]
        else "WARN" if time_count >= t["time_anchor_warn"]
        else "FAIL"
    )

    # 3. 반론 존재
    counter_hits = sum(content.count(m) for m in _P12_COUNTERPOINT_MARKERS)
    counterpoint_presence = (
        "PASS" if counter_hits >= t["counterpoint_pass"]
        else "WARN" if counter_hits >= t["counterpoint_warn"]
        else "FAIL"
    )

    # 4. 일반어 남용
    generic_count = sum(content.count(p) for p in _P12_GENERIC_PHRASES)
    generic_wording = (
        "PASS" if generic_count <= t["generic_phrase_pass"]
        else "WARN" if generic_count <= t["generic_phrase_warn"]
        else "FAIL"
    )

    # 5. 근거 결합 (출처 패턴)
    source_pats = re.findall(
        r"\([가-힣a-zA-Z\s]{2,20}\s*(?:발표|기준|추정|전망|분석|조사|집계|자료)\)"
        r"|\([가-힣a-zA-Z]{2,15}\s*(?:리서치|증권|투자|은행|연구소)\)"
        r"|출처\s*[:：]\s*.{2,30}"
        r"|[가-힣]{2,10}\s*(?:리서치|증권|투자|연구소|은행)\s*(?:에 따르면|자료|발표|보고서)",
        content,
    )
    src_count = len(source_pats)
    evidence_binding = "PASS" if src_count >= t["evidence_binding_pass"] else "WARN"

    scores = {
        "numeric_density":       numeric_density,
        "time_anchor":           time_anchor,
        "counterpoint_presence": counterpoint_presence,
        "generic_wording":       generic_wording,
        "evidence_binding":      evidence_binding,
        "numeric_count":         num_count,
        "time_anchor_count":     time_count,
        "generic_phrase_count":  generic_count,
        "source_pattern_count":  src_count,
    }

    if label:
        logger.info(
            f"[Phase 12] 품질 스코어 [{label}] | "
            f"숫자밀도: {numeric_density}({num_count}) | "
            f"시점앵커: {time_anchor}({time_count}) | "
            f"반론: {counterpoint_presence}({counter_hits}) | "
            f"일반어: {generic_wording}({generic_count}) | "
            f"근거결합: {evidence_binding}({src_count})"
        )
        flags = [k for k, v in scores.items()
                 if isinstance(v, str) and v in ("WARN", "FAIL")]
        if flags:
            logger.warning(f"[Phase 12] 품질 경고 [{label}] — 개선 대상: {flags}")

    return scores


def _check_post_separation(post1_content: str, post2_content: str) -> dict:
    """Phase 12: Post1/Post2 역할 분리 정도를 진단한다.

    <h3> 헤딩 중복 여부와 주요 단락 내용 교차 빈도를 체크한다.
    비파괴적 진단 전용 — 출력을 수정하거나 차단하지 않음.

    Returns:
        {"status": "PASS"|"WARN"|"FAIL", "overlap_headings": list, "overlap_count": int}
    """
    def _extract_h3s(html: str) -> set:
        raw = re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.DOTALL | re.IGNORECASE)
        return {re.sub(r"<[^>]+>", "", h).strip() for h in raw if h.strip()}

    p1_h3s = _extract_h3s(post1_content)
    p2_h3s = _extract_h3s(post2_content)
    overlap = p1_h3s & p2_h3s

    # 단락 단위 중복 체크 (80자 이상 단락이 상대편에도 있는 경우)
    p2_text = re.sub(r"<[^>]+>", "", post2_content)
    p1_paras = [
        s.strip() for s in
        re.sub(r"<[^>]+>", "", post1_content).split("\n")
        if len(s.strip()) >= 80
    ]
    deep_repeats = sum(1 for p in p1_paras if p in p2_text)

    total_overlap = len(overlap) + deep_repeats
    status = (
        "PASS" if total_overlap == 0
        else "WARN" if total_overlap <= 2
        else "FAIL"
    )

    logger.info(
        f"[Phase 12] Post1/Post2 역할 분리 | "
        f"h3 중복: {len(overlap)}개 | 단락 중복: {deep_repeats}개 | 상태: {status}"
    )
    if overlap:
        logger.warning(f"[Phase 12] 중복 h3 헤딩: {sorted(overlap)}")

    return {
        "status":           status,
        "overlap_headings": sorted(overlap),
        "overlap_count":    total_overlap,
    }


# ──────────────────────────────────────────────────────────────────────────────
# SECTION A-3: Phase 13 — 해석 지성 & 시간/수치 신뢰성 강화
# ──────────────────────────────────────────────────────────────────────────────

# ── Track A-1: 비자명성 기준 ────────────────────────────────────────────────
_P13_INTERPRETATION_STANDARD: str = """
[Phase 13 — 해석 지성: 비자명성 기준]
[해석] 레이블 문장은 독자가 헤드라인만 읽어도 유추할 수 있는 내용이어서는 안 됩니다.

다음은 [해석]이 아닌 상식적 인과로 금지합니다:
- "유가 상승 → 인플레이션 압력" (교과서 인과)
- "금리 상승 → 밸류에이션 부담" (교과서 인과)
- "이익 추정치 상향 → 투자자 관심 증가" (당연한 결론)
- "지정학 리스크 → 시장 불확실성" (동어 반복)

[해석]이 성립하려면 다음 중 하나 이상 충족이 필요합니다:
(a) 이 시점·이 데이터 조합에서만 나오는 특수한 함의
(b) 상식적으로 연결되지 않는 두 변수 간의 비자명적 연결
(c) 상충하는 신호들 사이의 긴장을 해소하는 판단
(d) 오늘이 같은 테마의 다른 날과 왜 다른지 구체적 설명
(e) 투자자의 판단 기준·섹터 선호·시나리오 가중치에 영향을 주는 해석

선호하는 해석 형태:
- 두 상충 신호의 우열 관계 ("X와 Y가 동시 발생 시 Z보다 W에 집중해야 하는 이유는...")
- 이차 효과·간접 전달 경로 ("이 움직임의 직접 피해자는 A이나, 간접 영향은 B가 더 크다")
- 섹터/종목 집중도 불균형 ("지수는 ±X%이나 이익 개선의 90%는 반도체 1개 섹터 집중")
- 레짐 전환 시사 ("이 조합은 단기 노이즈가 아닌 X 국면 전환 신호일 수 있다")

비자명적 [해석] 1개가 범용 인과 3개보다 낫습니다. 수를 줄이더라도 품질을 높이십시오."""

# ── Track A-2: 헤징 언어 3분류 ──────────────────────────────────────────────
_P13_HEDGING_TRIAGE_RULES: str = """
[Phase 13 — 헤징 언어 3분류 규칙]

Type 1 — 팩트 서술 (과거/현재 수치·날짜 명시 이벤트):
  규칙: 헤징 금지. 출처 또는 시점 명시 후 직접 서술.
  ❌ "KOSPI는 0.48% 하락한 것으로 파악됩니다"
  ✅ "KOSPI는 전일 대비 0.48% 하락한 X,XXX.XX pt에 마감했습니다 [출처]"

Type 2 — 분석적 연결 (인과·해석·함의):
  규칙: 문단당 1회 완화형 헤징 허용. 이후 지지 문장은 직접 서술.
  ❌ "금리 상승은 밸류에이션에 부담을 줄 것으로 보이며, 채권 시장에도 영향을 미치는 것으로 파악됩니다"
  ✅ "금리 상승은 밸류에이션 부담으로 작용한다. 현 수준에서 10bp 추가 상승 시 PER 압박 X%."

Type 3 — 전망·시나리오 (미래 경로, 조건부 기대):
  규칙: 헤징 허용. 단 반드시 명시적 조건(만약/발생 시/~한다면/if) 포함 필수.
  ❌ "유가 상승이 지속될 경우 긍정적 영향이 있을 것으로 예상됩니다"
  ✅ "WTI $X 돌파가 2주 이상 유지된다면, 에너지 기업 영업이익률은 Y%p 개선 압력을 받는다"

"것으로 파악됩니다/보입니다/추정됩니다/예상됩니다"를 모든 문장에 기계적으로 붙이지 마십시오."""

# ── Track A-3: 반론 최소 규격 ───────────────────────────────────────────────
_P13_COUNTERPOINT_SPEC: str = """
[Phase 13 — 반론 최소 규격]

반론 섹션 각 항목은 반드시 세 요소를 포함해야 합니다:
① 구체적 조건 — 어떤 상황이 발생해야 반론이 성립하는가
② 그 조건 하의 결과 — 무슨 일이 생기는가
③ 오늘의 핵심 논지와의 충돌 — 왜 오늘 분석을 약화시키는가

❌ 금지 형태:
- "반도체 시장의 변동성이 리스크로 작용할 수 있습니다" (카테고리 이름 = 리스크)
- "글로벌 불확실성이 지속될 경우 부담이 될 수 있습니다" (순환 논리)
- "유가 변동성은 여전히 리스크입니다" (동어 반복)

✅ 허용 형태 예시:
"IEA가 3분기 수요 전망을 X% 하향할 경우, 유가 상승 모멘텀은 2주 내 되돌림될 수 있으며,
이는 오늘 논지의 전제인 '에너지 기업 이익률 개선' 근거를 약화시킨다."

반론은 오늘의 분석을 구체적으로 '틀릴 수도 있음'을 보여야 합니다.
카테고리 리스크 나열은 반론으로 인정하지 않습니다."""

# ── Track A-4: 분석 뼈대 ────────────────────────────────────────────────────
_P13_ANALYTICAL_SPINE_RULE: str = """
[Phase 13 — 분석 뼈대(Analytical Spine)]

기사 작성 전 내부적으로 뼈대 문장 1개를 설정하십시오:
형식: "[팩트 X]와 [팩트 Y]가 동시 발생 중이며, 이는 투자자가 [Z] 대신 [W]에 주목해야 함을 시사"

뼈대 요건:
- 팩트 나열이 아닌 논지 (argument, not summary)
- 헤드라인 요약이 아닌 해석적 주장
- 전체 기사 구조가 이 뼈대를 뒷받침하는 방향으로 구성

뼈대는 기사 제목 또는 첫 단락 핵심 문장에 반영되어야 합니다.
평행 사실 나열 구조를 피하고 하나의 논지로 집중하십시오."""

# ── Track A-5: Post2 연속성 규칙 ────────────────────────────────────────────
_P13_POST2_CONTINUITY_RULE: str = """
[Phase 13 — Post2 연속성 규칙]

Post2(캐시의 픽)는 Post1(심층분석)이 종료된 시점에서 시작합니다.
Post1의 매크로/테마 설정을 다시 설명하지 마십시오.

'오늘 이 테마를 보는 이유' 섹션 구조:
  Post1이 도출한 결론 → 이 테마에서 가장 직접 영향받는 종목 탐색으로 즉시 진입

❌ 금지:
- "최근 X가 발생하면서..." 배경 재설명
- Post1에서 이미 나온 호르무즈/금리/환율 맥락 반복
- "최근 시장이 주목하는..." 류의 매크로 재진입

✅ 허용:
- "Post1 분석에서 [X]라는 결론이 도출되었다. 이 조건에서 직접 수혜/피해를 받는 종목은..."
- 종목 선정 기준과 그 기준이 이번 테마에서 갖는 특수성
- Post1 핵심 수치 1개 인용 후 바로 종목 분석 진입"""

# ── Track A: Gemini Step1 뼈대 협력 힌트 ─────────────────────────────────
_P13_GEMINI_SPINE_HINT: str = """
[Phase 13 — 분석 재료 뼈대 협력]
"theme" 필드는 단순 주제명이 아닌 분석적 논지를 포함하십시오.
❌ "글로벌 지정학적 리스크와 이익 추정치 상향"
✅ "지정학 리스크에도 이익 추정치 상향 지속 — 시장이 리스크를 단기 노이즈로 처리하는 국면에서 섹터 선별 기준 이동이 핵심"

"counter_interpretations" 항목은 "[조건]: [결과] — [논지와의 충돌]" 형식으로 작성하십시오.
범용 리스크 카테고리만 쓰지 마십시오."""

# ── Track A: 조합 규칙 문자열 (프롬프트 삽입용) ──────────────────────────
_P13_POST1_INTELLIGENCE_RULES: str = (
    _P13_ANALYTICAL_SPINE_RULE + "\n"
    + _P13_INTERPRETATION_STANDARD + "\n"
    + _P13_HEDGING_TRIAGE_RULES + "\n"
    + _P13_COUNTERPOINT_SPEC + "\n"
)

_P13_POST2_INTELLIGENCE_RULES: str = (
    _P13_POST2_CONTINUITY_RULE + "\n"
    + _P13_ANALYTICAL_SPINE_RULE + "\n"
    + _P13_INTERPRETATION_STANDARD + "\n"
    + _P13_HEDGING_TRIAGE_RULES + "\n"
    + _P13_COUNTERPOINT_SPEC + "\n"
)

# ── Track A: 해석 품질 진단 상수 ─────────────────────────────────────────
_P13_HEDGE_PHRASES: list = [
    "것으로 파악됩니다", "것으로 보입니다", "것으로 추정됩니다", "것으로 예상됩니다",
    "것으로 판단됩니다", "것으로 분석됩니다", "것으로 전망됩니다", "것으로 생각됩니다",
    "로 파악됩니다", "로 보입니다", "로 추정됩니다", "로 예상됩니다",
]

_P13_WEAK_INTERP_PATTERNS: list = [
    ("유가", "인플레"), ("유가", "물가"), ("금리 상승", "밸류에이션"),
    ("금리 상승", "부담"), ("이익 추정치", "관심 증가"), ("지정학", "불확실"),
    ("지정학", "변동성"), ("이익 상향", "시장 관심"), ("원화 약세", "수입 물가"),
    ("호르무즈", "유가 급등"), ("금리", "채권 부담"),
]

_P13_COUNTERPOINT_CONDITION_MARKERS: list = [
    "만약", "만일", "한다면", "발생 시", "경우", "하향 시", "상향 시",
    "지속 시", "현실화", "실제로", "봉쇄", "시나리오", "하락 전환",
]

# ── Track B: 수치 합리성 범위 (2024-2027 추정, 넓게 설정) ────────────────
_P13_SANITY_RANGES: dict = {
    "kospi":  (1800, 4500),
    "kosdaq": (500,  1800),
    "usdkrw": (1050, 1800),
}


def _score_interpretation_quality(content: str, label: str = "") -> dict:
    """Phase 13 Track A: 해석 품질을 rule-based로 진단한다.

    Returns:
        {hedge_overuse, hedge_count, hedge_ratio,
         weak_interpretation, weak_interp_hits,
         counterpoint_spec, condition_hits, overall}
    """
    import re as _re

    plain = _re.sub(r"<[^>]+>", " ", content)
    sentences = [s.strip() for s in _re.split(r"[.。!?！？]\s*", plain) if s.strip()]
    total_sent = max(len(sentences), 1)
    hedge_count = sum(plain.count(p) for p in _P13_HEDGE_PHRASES)
    hedge_ratio = hedge_count / total_sent
    hedge_status = (
        "FAIL" if hedge_ratio > 0.5
        else "WARN" if hedge_ratio > 0.30
        else "PASS"
    )

    weak_hits = sum(
        1 for (kw1, kw2) in _P13_WEAK_INTERP_PATTERNS
        if kw1 in plain and kw2 in plain
    )
    interp_status = (
        "FAIL" if weak_hits >= 3
        else "WARN" if weak_hits >= 1
        else "PASS"
    )

    ctr_match = _re.search(r"반대|반론|체크포인트|리스크|위험|Counter", plain, _re.IGNORECASE)
    if ctr_match:
        ctr_text = plain[ctr_match.start():]
        cond_hits = sum(ctr_text.count(m) for m in _P13_COUNTERPOINT_CONDITION_MARKERS)
        counter_status = "PASS" if cond_hits >= 2 else ("WARN" if cond_hits >= 1 else "FAIL")
    else:
        cond_hits = 0
        counter_status = "WARN"

    all_statuses = [hedge_status, interp_status, counter_status]
    overall = (
        "FAIL" if "FAIL" in all_statuses
        else "WARN" if "WARN" in all_statuses
        else "PASS"
    )

    result = {
        "hedge_overuse":       hedge_status,
        "hedge_count":         hedge_count,
        "hedge_ratio":         round(hedge_ratio, 2),
        "weak_interpretation": interp_status,
        "weak_interp_hits":    weak_hits,
        "counterpoint_spec":   counter_status,
        "condition_hits":      cond_hits,
        "overall":             overall,
    }

    logger.info(
        f"[Phase 13] 해석 품질 [{label}] | "
        f"헤징: {hedge_status}({hedge_count}회/{total_sent}문장) | "
        f"약한해석: {interp_status}({weak_hits}건) | "
        f"반론조건: {counter_status}({cond_hits}마커)"
    )
    flags = []
    if hedge_status != "PASS":
        flags.append(f"hedge_overuse({hedge_count}/{total_sent})")
    if interp_status != "PASS":
        flags.append(f"weak_interp({weak_hits}패턴)")
    if counter_status != "PASS":
        flags.append(f"counterpoint_spec({counter_status})")
    if flags:
        logger.warning(f"[Phase 13] 해석 품질 경고 [{label}] — {', '.join(flags)}")

    return result


def _check_temporal_sanity(content: str, run_date_str: str = "") -> dict:
    """Phase 13 Track B: 시간 일관성 및 연간 실적 혼용 여부를 검사.

    Returns:
        {status, flags, stale_date_count, forecast_confusion_count}
    """
    import re as _re
    from datetime import datetime as _dt

    plain = _re.sub(r"<[^>]+>", " ", content)
    flags = []
    run_year = int(run_date_str[:4]) if run_date_str and len(run_date_str) >= 4 else 2026

    fact_verbs = r"(기록했습니다|달성했습니다|증가했습니다|감소했습니다|마감했습니다)"
    for m in _re.finditer(r"(20\d{2})년[^.]{0,80}?" + fact_verbs, plain):
        year = int(m.group(1))
        if year >= run_year:
            flags.append(
                f"FUTURE_AS_FACT: {year}년 실적을 확정 사실 동사로 서술 (발행연도 {run_year})"
            )

    forecast_verbs = r"(전망됩니다|추정됩니다|것으로 전망|것으로 추정)"
    for m in _re.finditer(r"(20\d{2})년[^.]{0,80}?" + forecast_verbs, plain):
        year = int(m.group(1))
        if year < run_year - 1:
            flags.append(
                f"PAST_AS_FORECAST: {year}년을 전망 동사로 서술 (이미 확정 연도)"
            )

    stale_count = 0
    if run_date_str:
        try:
            run_dt = _dt.strptime(run_date_str[:10], "%Y-%m-%d")
            for d_str in _re.findall(r"(\d{4}-\d{2}-\d{2})", plain):
                try:
                    d = _dt.strptime(d_str, "%Y-%m-%d")
                    delta = (run_dt - d).days
                    if 7 < delta <= 365:
                        flags.append(f"STALE_DATE_REF: {d_str} ({delta}일 경과)")
                        stale_count += 1
                except ValueError:
                    pass
        except Exception:
            pass

    vague_count = plain.count("최근") + plain.count("근래")
    if vague_count >= 5:
        flags.append(f"VAGUE_RECENCY: '최근/근래' {vague_count}회 (날짜 없이 반복)")

    fc_count = sum(1 for f in flags if "FACT" in f or "FORECAST" in f)
    status = (
        "FAIL" if any("FUTURE_AS_FACT" in f for f in flags)
        else "WARN" if flags
        else "PASS"
    )

    result = {
        "status":                   status,
        "flags":                    flags[:8],
        "stale_date_count":         stale_count,
        "forecast_confusion_count": fc_count,
    }

    if flags:
        logger.warning(f"[Phase 13] 시간 일관성 이슈: {len(flags)}건")
        for f in flags[:5]:
            logger.warning(f"  ⚠ {f}")
    else:
        logger.info("[Phase 13] 시간 일관성: 이슈 없음")

    return result


def _check_numeric_sanity(content: str) -> dict:
    """Phase 13/14 Track B+D: 주요 시장 수치의 합리적 범위를 경량 점검.

    Phase 14 변경:
    - _P14_SANITY_RANGES 사용 (Phase 13 범위보다 넓음, 2026+ 레인지 수용)
    - 2단계 티어: SUSPICIOUS(광역범위 이탈) / HARD_FAIL(자릿수 오류 등 명백한 이상)
    - FAIL 조건: hard_fail 1건 이상 OR suspicious 2건 이상

    Returns:
        {status, flags, suspicious_count, hard_fail_count}
    """
    import re as _re

    flags = []
    hard_fail_flags = []
    plain = _re.sub(r"<[^>]+>", " ", content)

    def _check_range(label: str, nums_str: list, key: str) -> None:
        lo, hi = _P14_SANITY_RANGES[key]
        hf_lo, hf_hi = _P14_SANITY_HARD_FAIL_RANGES[key]
        for n_str in nums_str:
            try:
                n = float(n_str.replace(",", ""))
                if not (hf_lo <= n <= hf_hi):
                    hard_fail_flags.append(
                        f"HARD_FAIL_{label}: {n} (명백한 이상값 — 범위 {hf_lo}–{hf_hi})"
                    )
                elif not (lo <= n <= hi):
                    flags.append(
                        f"SUSPICIOUS_{label}: {n} (광역 범위 {lo}–{hi} 이탈)"
                    )
            except ValueError:
                pass

    # 4자리 이상 숫자 + pt/포인트 — 중간에 퍼센트 숫자가 있어도 포착
    kospi_raw = _re.findall(
        r"(?:KOSPI|코스피).{0,80}?([\d,]{4,}\.?\d*)\s*(?:pt|포인트)",
        plain, _re.IGNORECASE | _re.DOTALL,
    )
    _check_range("KOSPI", kospi_raw, "kospi")

    kosdaq_raw = _re.findall(
        r"(?:KOSDAQ|코스닥).{0,80}?([\d,]{4,}\.?\d*)\s*(?:pt|포인트)",
        plain, _re.IGNORECASE | _re.DOTALL,
    )
    _check_range("KOSDAQ", kosdaq_raw, "kosdaq")

    usdkrw_raw = (
        _re.findall(r"([\d,]+)\s*원[/\s]*달러", plain)
        + _re.findall(r"달러당\s*([\d,]+)\s*원", plain)
    )
    for n_str in usdkrw_raw:
        try:
            n = float(n_str.replace(",", ""))
            if 100 < n < 10_000:
                hf_lo, hf_hi = _P14_SANITY_HARD_FAIL_RANGES["usdkrw"]
                lo, hi = _P14_SANITY_RANGES["usdkrw"]
                if not (hf_lo <= n <= hf_hi):
                    hard_fail_flags.append(f"HARD_FAIL_USDKRW: {n} (명백한 이상값)")
                elif not (lo <= n <= hi):
                    flags.append(f"SUSPICIOUS_USDKRW: {n} (범위 {lo}–{hi} 이탈)")
        except ValueError:
            pass

    all_flags = hard_fail_flags + flags
    # FAIL 조건 (Phase 14): hard_fail >= 1 OR suspicious >= 2
    status = (
        "FAIL" if (len(hard_fail_flags) >= 1 or len(flags) >= 2)
        else "WARN" if flags
        else "PASS"
    )

    result = {
        "status":           status,
        "flags":            all_flags[:6],
        "suspicious_count": len(flags),
        "hard_fail_count":  len(hard_fail_flags),
    }

    if all_flags:
        logger.warning(f"[Phase 14] 수치 이상 감지: hard_fail={len(hard_fail_flags)}, suspicious={len(flags)}")
        for f in all_flags[:5]:
            logger.warning(f"  ⚠ {f}")
    else:
        logger.info("[Phase 14] 수치 합리성: 이슈 없음")

    return result


def _check_verifier_closure(issues: list, draft: str, revised: str) -> dict:
    """Phase 13 Track B: Gemini 검수 이슈가 Step3 수정 후 실제 해소되었는지 확인.

    Returns:
        {status, total_checked, resolved_count, unresolved_count, unresolved}
    """
    import re as _re

    if not issues or not revised:
        return {
            "status": "SKIP", "total_checked": 0,
            "resolved_count": 0, "unresolved_count": 0, "unresolved": [],
        }

    TEMPORAL_NUMERIC_KW = [
        "[1]", "[시점 일관성]", "[숫자", "[수치", "시점", "일관성",
        "기준 날짜", "출처 날짜", "연간", "전망치", "확정",
    ]

    high_risk = [
        iss for iss in issues
        if any(kw in iss for kw in TEMPORAL_NUMERIC_KW)
    ]

    resolved, unresolved = [], []
    for issue in high_risk:
        quoted = _re.findall(
            r"[\u2018\u2019\u201c\u201d']([^\u2018\u2019\u201c\u201d']{10,80})[\u2018\u2019\u201c\u201d']",
            issue,
        )
        if not quoted:
            quoted_pairs = _re.findall(r"'([^']{10,60})'|\"([^\"]{10,60})\"", issue)
            quoted = [q[0] or q[1] for q in quoted_pairs if (q[0] or q[1])]

        if not quoted:
            resolved.append(issue[:60] + "…")
            continue

        still_present = any(phrase in revised for phrase in quoted if phrase)
        (unresolved if still_present else resolved).append(issue[:80] + "…")

    total = len(high_risk)
    un_cnt = len(unresolved)
    status = (
        "FAIL"  if un_cnt >= 2
        else "WARN"  if un_cnt >= 1
        else "PASS"  if total > 0
        else "SKIP"
    )

    result = {
        "status":           status,
        "total_checked":    total,
        "resolved_count":   len(resolved),
        "unresolved_count": un_cnt,
        "unresolved":       unresolved[:3],
    }

    logger.info(
        f"[Phase 13] 검수 해소 확인 | 고위험 {total}건 | "
        f"해소 {len(resolved)} / 미해소 {un_cnt} | 상태: {status}"
    )
    for u in unresolved:
        logger.warning(f"  ⚠ 미해소 이슈: {u}")

    return result


def _check_post_continuity(post1_content: str, post2_content: str) -> dict:
    """Phase 13 Track A-5: Post2 도입부가 Post1 도입부를 반복하는지 진단.

    Returns:
        {status, ngram_overlap_count, bg_repeat_count, sample_overlaps}
    """
    import re as _re

    def _text(html: str, limit: int = 400) -> str:
        return _re.sub(r"<[^>]+>", " ", html)[:limit]

    p1_intro = _text(post1_content)
    p2_intro = _text(post2_content, 600)

    def _ngrams(text: str, n: int = 4) -> set:
        words = text.split()
        return {" ".join(words[i:i+n]) for i in range(max(0, len(words) - n + 1))}

    overlap = _ngrams(p1_intro) & _ngrams(p2_intro)
    overlap_count = len(overlap)

    BG_PATTERNS = [
        "최근 호르무즈", "호르무즈 해협", "미국채 금리 상승", "원화 약세",
        "유가가 급등", "원자재 가격", "지정학적 리스크가 고조",
    ]
    bg_repeat = sum(1 for p in BG_PATTERNS if p in p2_intro)

    status = (
        "FAIL" if (overlap_count >= 3 or bg_repeat >= 2)
        else "WARN" if (overlap_count >= 1 or bg_repeat >= 1)
        else "PASS"
    )

    result = {
        "status":              status,
        "ngram_overlap_count": overlap_count,
        "bg_repeat_count":     bg_repeat,
        "sample_overlaps":     sorted(overlap)[:3],
    }

    logger.info(
        f"[Phase 13] Post1/Post2 연속성 | n-gram 중복: {overlap_count}개 | "
        f"배경 재설명: {bg_repeat}건 | 상태: {status}"
    )
    if status != "PASS":
        logger.warning(f"[Phase 13] Post2 도입부 중복 감지 — {status}")

    return result


# ──────────────────────────────────────────────────────────────────────────────
# SECTION A-4: Phase 14 — 생성 강제 & 소스 정규화
# ──────────────────────────────────────────────────────────────────────────────

# ── Track A: Source Normalization 상수 ──────────────────────────────────────

_P14_CONFIRMED_FACT_VERBS: list = [
    "기록했습니다", "마감했습니다", "달성했습니다", "증가했습니다",
    "감소했습니다", "기록됐습니다", "집계됐습니다", "나타났습니다",
    "발표했습니다", "공시했습니다", "확인됐습니다", "기록하며", "마감하며",
    "달성하며", "기록한", "마감한", "달성한", "기록했다", "마감했다",
]

_P14_FORECAST_INDICATORS: list = [
    "예상됩니다", "전망됩니다", "추정됩니다", "보입니다", "파악됩니다",
    "것으로 예상", "것으로 전망", "것으로 추정", "할 것으로", "될 것으로",
    "예정입니다", "계획입니다", "목표로", "전망치", "추정치", "가이던스",
    "예상된다", "전망된다", "추정된다", "것으로 예상된", "것으로 전망된",
]


def _normalize_source_for_generation(materials: dict, run_date_str: str) -> str:
    """Phase 14 Track A: facts를 CONFIRMED/FORECAST/AMBIGUOUS로 분류해
    GPT 프롬프트 앞에 주입할 정규화 블록을 생성한다.

    소스 데이터에 포함된 전망 어미가 확정된 과거 사실에 붙어 GPT 출력을
    오염시키는 문제를 방지한다.

    Returns:
        GPT user_msg 앞에 prepend할 정규화 블록 텍스트.
    """
    from datetime import datetime as _dt
    import re as _re

    try:
        run_dt = _dt.strptime(run_date_str[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        run_dt = _dt.now()

    facts = materials.get("facts", [])
    if not facts:
        return ""

    confirmed: list = []
    forecast: list  = []
    ambiguous: list = []

    for fact in facts:
        content  = fact.get("content", "")
        date_str = fact.get("date", "") or ""
        source   = fact.get("source", "") or ""

        # 날짜 기반 분류
        is_past = False
        yr_m = _re.search(r"(20\d{2})", date_str)
        if yr_m:
            fact_year = int(yr_m.group(1))
            if fact_year < run_dt.year:
                is_past = True
            elif fact_year == run_dt.year:
                # 월일 있으면 정밀 비교
                md_m = _re.search(r"(\d{1,2})[월\-](\d{1,2})", date_str)
                if md_m:
                    try:
                        fact_dt = _dt(run_dt.year, int(md_m.group(1)), int(md_m.group(2)))
                        is_past = fact_dt <= run_dt
                    except ValueError:
                        is_past = True  # 날짜 파싱 실패 → 보수적으로 과거 처리
                else:
                    is_past = True  # 연도만 있고 같은 연도 → 과거로 처리

        has_forecast_lang  = any(kw in content for kw in _P14_FORECAST_INDICATORS)
        has_confirmed_lang = any(kw in content for kw in _P14_CONFIRMED_FACT_VERBS)

        if is_past and has_confirmed_lang and not has_forecast_lang:
            confirmed.append((content[:110], source))
        elif has_forecast_lang and not has_confirmed_lang:
            forecast.append((content[:110], source))
        elif is_past and not has_forecast_lang:
            confirmed.append((content[:110], source))
        else:
            ambiguous.append((content[:110], source))

    if not confirmed and not forecast and not ambiguous:
        return ""

    lines = [
        "\n[Phase 14 — 소스 시점 정규화]",
        "아래 분류에 따라 문장 언어 톤을 결정하십시오.\n",
    ]

    if confirmed:
        lines.append("✅ CONFIRMED 팩트 — 직접 서술 필수 (헤징 어미 금지, 과거 사실 동사 사용):")
        for c, src in confirmed[:8]:
            lines.append(f"  • [{src}] {c}")

    if forecast:
        lines.append("\n⚠ FORECAST 데이터 — [전망] 태그 + 조건부 서술 필수:")
        for c, src in forecast[:5]:
            lines.append(f"  • [{src}] {c}")

    if ambiguous:
        lines.append("\n❓ AMBIGUOUS — [해석] 또는 조건부로만 서술:")
        for c, src in ambiguous[:4]:
            lines.append(f"  • [{src}] {c}")

    lines.append("")
    block = "\n".join(lines)
    logger.info(
        f"[Phase 14] 소스 정규화 | CONFIRMED={len(confirmed)}, "
        f"FORECAST={len(forecast)}, AMBIGUOUS={len(ambiguous)}"
    )
    return block


def _extract_post1_spine(post1_content: str) -> str:
    """Phase 14 Track B-4: Post1 최종 콘텐츠에서 분석 뼈대 문장을 추출.

    우선순위:
        1. <!-- SPINE: ... --> HTML 주석
        2. 첫 번째 [해석] 문장 (20자 이상)
        3. 첫 번째 80자 이상 문장 (last resort)
        4. 빈 문자열
    """
    import re as _re

    spine_m = _re.search(r"<!--\s*SPINE:\s*(.+?)\s*-->", post1_content, _re.DOTALL)
    if spine_m:
        return spine_m.group(1).strip()[:300]

    plain = _re.sub(r"<[^>]+>", " ", post1_content)
    interp_m = _re.search(r"\[해석\]\s*([^.!?。]{20,200}[.!?。])", plain)
    if interp_m:
        return interp_m.group(1).strip()[:250]

    sentences = [s.strip() for s in _re.split(r"[.。!?！？]\s*", plain) if len(s.strip()) >= 80]
    if sentences:
        return sentences[0][:250]

    return ""


# ── Track B: Generation Enforcement — Few-shot 대조 예시 ─────────────────────

_P14_FEWSHOT_BAD_GOOD_INTERP: str = """
[Phase 14 — 해석 품질 BAD→GOOD 대조 예시]
아래 대조 예시를 기사 작성에 직접 적용하십시오.

❌ BAD [교과서 인과 — 사용 금지]:
"유가 상승으로 인플레이션 압력이 높아지고 있습니다."
✅ GOOD [수치 경로 명시]:
"유가 $95 상승이 수입 물가로 전달되는 규모는 원달러 환율 동반 여부에 달려있다.
현재 1,450원 환경에서 수입 에너지 비용 증가폭은 달러 환산 유가 상승폭의 약 1.3배다.
즉, 이번 유가 상승의 물가 충격은 환율 안정 시나리오보다 20-30% 클 수 있다."

❌ BAD [동어 반복]:
"금리 상승은 밸류에이션 부담으로 작용할 것으로 보입니다."
✅ GOOD [수치 연결 + 이중 함의]:
"금리 10bp 추가 상승 시 KOSPI 12MF P/E에 가해지는 이론적 할인율 압박은 -0.2x 수준이다.
현재 P/E 8.8x 기준 8.6x로 이동하는데, 이 구간은 2022년 저점(8.3x)에 근접한다.
따라서 금리 상승은 단순 밸류에이션 부담이 아니라 '바닥권 재인식 트리거'를 동시에 내포한다."

❌ BAD [범용 리스크 나열]:
"변동성 리스크와 불확실성이 여전히 존재합니다."
✅ GOOD [조건+결과+논지충돌]:
"IEA가 3분기 원유 수요를 일 100만 배럴 이상 하향할 경우, 유가 상승 모멘텀은 2주 내
되돌림될 수 있다. 이 시나리오에서 오늘 논지의 전제인 에너지 섹터 이익률 개선이 약화되고,
반도체 집중도가 지수 상승의 유일한 동력이 된다."

❌ BAD [당연한 결론]:
"이익 추정치 상향은 투자자들의 관심을 끌고 있습니다."
✅ GOOD [분포 분석 → 판단 기준 이동]:
"유니버스 200종목 이익 추정치 +1.2% 상향의 의미는 규모보다 분포에 있다.
이 상향분의 70% 이상이 반도체 1-2종목에 집중된다면, 지수 전체 이익 개선은 착시이며
비반도체 종목에서의 개별 접근이 지수 추종보다 더 중요해진다."

❌ BAD [Post2 — 매크로 재진입]:
"최근 호르무즈 해협 봉쇄 우려가 심화되면서 유가가 급등하고 있습니다."
✅ GOOD [Post2 — 결론 인용 후 종목 직행]:
"Post1 결론: 지정학 단기 노이즈 처리 국면에서 이익 모멘텀 종목이 상대 우위.
이 기준에서 가장 직접 수혜를 받는 종목은 삼성전자다 — 이번 주 이익 추정치 변화가
이 논지를 직접 확인해준다."
"""

_P14_ANALYTICAL_SPINE_ENFORCEMENT: str = """
[Phase 14 — 분석 뼈대 강제]
기사 작성 시작 전, HTML 첫 줄에 다음 형식의 뼈대 주석을 반드시 삽입하십시오:
<!-- SPINE: [팩트 X]와 [팩트 Y] 동시 발생 → 투자자는 [Z] 대신 [W]에 주목해야 한다 -->

예시:
<!-- SPINE: 이익 추정치 상향(+1.2%)과 KOSPI P/E 8.8x 동시 발생 → 밸류에이션 부담론보다 이익 모멘텀 종목 선별이 핵심 -->

이 뼈대가 기사 제목·도입부·핵심 섹션 3개를 모두 관통해야 합니다.
평행 사실 나열 구조를 피하고 단일 논지로 집중하십시오.
"""

_P14_HEDGE_DIRECT_PROHIBITION: str = """
[Phase 14 — 팩트 서술 헤징 직접 금지]
날짜가 명시된 과거 시장 데이터에는 다음 표현을 절대 사용하지 마십시오:
  ❌ "KOSPI는 X,XXX.XX pt에 마감할 것으로 예상됩니다" (과거 날짜 + 전망 어미)
  ❌ "0.48% 하락한 것으로 파악됩니다" (과거 수치 + 헤징 어미)
  ✅ "KOSPI는 전일 대비 0.48% 하락한 X,XXX.XX pt에 마감했습니다" (직접 서술)
  ✅ "국고채 금리는 3.649%를 기록했습니다" (직접 서술)

전망/시나리오에만 조건부 언어를 사용하십시오:
  ✅ "WTI $100 돌파가 2주 이상 유지된다면..." (명시적 조건 포함)
  ✅ "이익 추정치 추가 상향 시 P/E 재평가 가능성" (조건 명시)
"""

_P14_POST1_ENFORCEMENT_BLOCK: str = (
    _P14_ANALYTICAL_SPINE_ENFORCEMENT + "\n"
    + _P14_FEWSHOT_BAD_GOOD_INTERP + "\n"
    + _P14_HEDGE_DIRECT_PROHIBITION + "\n"
)

_P14_POST2_CONTINUATION_TEMPLATE: str = """
[Phase 14 — Post2 연속성 강제]
Post1 결론/뼈대:
{post1_spine}

Post2는 위 결론에서 즉시 출발합니다.
→ "Post1이 도출한 [위 결론]을 바탕으로, 가장 직접 노출되는 종목은..."
→ 또는: "[위 결론]의 조건에서, 섹터 선별 기준의 핵심은..."

다시 매크로 배경(지정학/금리/유가 등)을 설명하는 문단을 도입부에 쓰지 마십시오.
"""

# ── Track C: Rewrite Enforcement Loop 프롬프트 ──────────────────────────────

GEMINI_INTERP_REWRITE_SYSTEM: str = """
너는 매크로몰트(MacroMalt) 금융 콘텐츠 품질 강화 에디터다.
입력된 HTML 기사의 [해석] 섹션에서 교과서 인과관계와 범용 일반론을 찾아
비자명적 해석으로 교체한다.

[재작성 원칙]
1. 교체 대상: [해석] 레이블 없이 당연한 결론을 서술하거나,
   [해석] 레이블이 있어도 교과서 인과만 담긴 문장
2. 교체 기준:
   - 이 시점·이 데이터 조합에서만 나오는 함의 명시
   - 상충 신호의 우열 관계 명시 (어느 신호가 더 강한가)
   - 수치 기반 이차 효과 (직접 효과보다 간접 파급 경로)
   - 투자자 판단 기준 이동 명시 (Z 대신 W에 주목해야 하는 이유)
3. 보존 대상: 사실 서술, 숫자, 구체적 조건부 반론, 출처 표기
4. 분량 보존: 교체 후 원문보다 짧아지지 않도록 한다
5. 출력 형식: 수정된 HTML 전체를 그대로 출력 (JSON 래핑 없음, 코드블록 없음)

[절대 금지 패턴 — 발견 즉시 교체]
- "유가 상승 → 인플레이션 압력" 류 직접 인과 ([해석] 레이블 있어도 교체)
- "금리 상승 → 밸류에이션 부담" 류 직접 인과
- "지정학 리스크 → 시장 불확실성" 동어 반복
- "이익 추정치 상향 → 투자자 관심 증가" 당연한 결론
- "변동성/불확실성이 리스크" 카테고리 나열
"""

GEMINI_INTERP_REWRITE_USER: str = """
아래 HTML에서 약한 해석 패턴을 찾아 교체하고, 수정된 HTML 전체를 출력하라.

[Phase 13이 감지한 약한 해석 패턴]
{weak_patterns}

[수정 대상 HTML]
{draft}
"""

# ── Track C Hotfix: Targeted Block-Level Rewrite (Phase 14.1) ────────────────
# 문제: 기존 전체 기사 재작성은 weak_interp_hits를 실제로 줄이지 못함.
# 이유: 패턴이 기사 전체에 걸쳐 키워드 쌍을 감지하므로, Gemini가 전체를 재작성해도
#       다른 섹션에 남은 키워드가 패턴을 계속 유발함.
# 해결: 패턴 키워드가 실제로 동시 등장하는 HTML 블록만 추출→타겟 재작성→교체.

_P14H_BLOCK_TAGS_RE: str = r"<(p|li|blockquote|h[1-6]|div)[^>]*>.*?</\1>"

GEMINI_TARGETED_BLOCK_REWRITE_SYSTEM_POST1: str = """
너는 매크로몰트(MacroMalt) 금융 분석 콘텐츠의 해석 품질 개선 에디터다.
입력되는 각 HTML 블록은 약한 해석 패턴(교과서 인과, 범용 리스크 나열)이 감지된 단락이다.
각 블록을 다음 기준으로 재작성하라.

[재작성 목표 — Post1 심층분석 맥락]
1. 교과서 인과 제거: "A 상승 → B 압력" 형태의 단순 직접 연결 제거
2. 비자명적 해석으로 교체:
   - 이 시점·이 데이터 조합에서만 성립하는 함의
   - 상충 신호 간 긴장 해소 (어느 신호가 더 강한지 판단)
   - 투자자 프레이밍 이동 (Z 대신 W를 보아야 하는 이유)
   - 2차 효과 경로 (직접 효과보다 간접 파급)
3. 분석 뼈대(spine) 지지: 제공된 spine 문장과 논지를 강화하는 방향으로 재작성
4. 팩트 보존: 숫자, 날짜, 출처 표기 변경 금지

[절대 금지 패턴]
- "유가 상승 → 인플레이션 압력" / "금리 상승 → 밸류에이션 부담"
- "지정학 리스크 → 불확실성 증가" / "이익 추정치 상향 → 투자자 관심"
- "변동성이 리스크" / "불확실성이 지속"
- 기존 약한 패턴과 동일한 키워드 쌍을 다른 방식으로 표현한 문장

[출력 형식]
블록 번호와 함께 재작성된 HTML 블록만 출력하라.
형식:
BLOCK_1:
<p>재작성된 내용</p>
BLOCK_2:
<p>재작성된 내용</p>
(수정이 필요 없는 블록은 원본 그대로 BLOCK_N: 형식으로 출력하라)
"""

GEMINI_TARGETED_BLOCK_REWRITE_SYSTEM_POST2: str = """
너는 매크로몰트(MacroMalt) 금융 분석 콘텐츠의 해석 품질 개선 에디터다.
입력되는 각 HTML 블록은 약한 해석 패턴(교과서 인과, 범용 리스크 나열)이 감지된 단락이다.
각 블록을 다음 기준으로 재작성하라.

[재작성 목표 — Post2 종목 리포트 맥락]
1. 교과서 인과 제거: "반도체 수요 증가 + 기술력 강화 → 실적 개선" 등 당연한 결론 제거
2. 종목 레벨 비자명적 해석으로 교체:
   - "왜 이 종목이 이 테제(Post1 spine) 하에서 특히 유리한가"의 구체적 메커니즘
   - 동종 업종 대비 차별점 (같은 섹터에서 이 종목이 선택된 이유)
   - 수급/밸류에이션 비대칭 (외국인 매도 후 저PER 진입 기회 등)
   - 시나리오별 downside 구조 (단순 "리스크 존재" 아닌 조건+크기 명시)
3. [반대 포인트] 강화: 조건 + 결과 + 메인 픽 테제와의 충돌 3요소 필수
4. 팩트 보존: 숫자, 날짜, 출처 표기 변경 금지

[절대 금지 패턴]
- "반도체 수요 증가", "기술력 강화", "실적 개선 기대"만 나열
- "지정학 리스크 → 원가 부담" 단문 반론
- "변동성이 리스크" / "불확실성 지속" 카테고리 나열
- 기존 약한 패턴과 동일한 키워드 쌍을 다른 방식으로 표현한 문장

[출력 형식]
블록 번호와 함께 재작성된 HTML 블록만 출력하라.
형식:
BLOCK_1:
<p>재작성된 내용</p>
BLOCK_2:
<p>재작성된 내용</p>
(수정이 필요 없는 블록은 원본 그대로 BLOCK_N: 형식으로 출력하라)
"""

GEMINI_TARGETED_BLOCK_REWRITE_USER: str = """
아래 HTML 블록들은 약한 해석 패턴이 감지된 타겟 단락들이다.
각 블록을 시스템 프롬프트 기준으로 재작성하라.

[기사 분석 뼈대 (spine)]
{spine}

[감지된 약한 패턴]
{weak_patterns}

[재작성 타겟 블록들]
{target_blocks}
"""


def _extract_weak_interp_blocks(content: str) -> list:
    """Phase 14 Hotfix Track A: 약한 해석 패턴 키워드가 동시 등장하는 HTML 블록 추출.

    전략:
    1. HTML을 블록 단위(p, li, h1-h6)로 분리
    2. 각 블록 plain text에서 패턴 (kw1, kw2) 쌍이 동시 등장하는 블록 선별
    3. 동시 등장 없을 경우, [해석]/[전망] 문맥 블록에서 단일 패턴 키워드 포함 블록 보조 선별
    4. 최대 6개 블록 반환 (Gemini 컨텍스트 절약)

    Returns:
        list of {html_block, plain_text, matched_patterns, has_cooccurrence, section_hint}
    """
    import re as _re

    # 블록 단위 추출
    block_pattern = _re.compile(
        r"(<(?:p|li|blockquote|h[1-6])[^>]*>)(.*?)(</(?:p|li|blockquote|h[1-6])>)",
        _re.DOTALL | _re.IGNORECASE,
    )
    blocks = []
    for m in block_pattern.finditer(content):
        open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
        plain = _re.sub(r"<[^>]+>", " ", inner).strip()
        if len(plain) < 20:
            continue
        # 섹션 힌트 감지 ([해석], [전망], [반대])
        section_hint = ""
        for tag in ["[해석]", "[전망]", "[반대", "[반론"]:
            if tag in plain or tag in open_tag:
                section_hint = tag
                break
        blocks.append({
            "html_block": m.group(0),
            "open_tag": open_tag,
            "inner": inner,
            "close_tag": close_tag,
            "plain_text": plain,
            "section_hint": section_hint,
            "start": m.start(),
            "end": m.end(),
        })

    # 패턴별 코-오커런스 블록 우선, 섹션 힌트 블록 보조
    co_blocks = []
    hint_blocks = []
    plain_all = _re.sub(r"<[^>]+>", " ", content)

    for blk in blocks:
        txt = blk["plain_text"]
        matched = []
        for (kw1, kw2) in _P13_WEAK_INTERP_PATTERNS:
            if kw1 in txt and kw2 in txt:
                matched.append((kw1, kw2))
        if matched:
            blk["matched_patterns"] = matched
            blk["has_cooccurrence"] = True
            co_blocks.append(blk)
        elif blk["section_hint"]:
            # 섹션 내 단일 키워드라도 포함이면 보조 후보
            single_matched = []
            for (kw1, kw2) in _P13_WEAK_INTERP_PATTERNS:
                if kw1 in txt or kw2 in txt:
                    single_matched.append((kw1, kw2))
            if single_matched:
                blk["matched_patterns"] = single_matched
                blk["has_cooccurrence"] = False
                hint_blocks.append(blk)

    # 코-오커런스 우선, 이후 섹션 힌트 블록 보충 (최대 6개)
    result = co_blocks[:4] + hint_blocks[:max(0, 6 - len(co_blocks[:4]))]
    return result


def _rewrite_weak_blocks(
    targets: list,
    article_spine: str,
    post_type: str,
    label: str,
) -> dict:
    """Phase 14 Hotfix Track B: 타겟 블록들을 Gemini로 일괄 재작성.

    Args:
        targets:       _extract_weak_interp_blocks() 반환값
        article_spine: Post1 뼈대 문장 (없으면 빈 문자열)
        post_type:     "Post1" | "Post2"
        label:         로그 레이블

    Returns:
        {original_html_block: replacement_html_block} 매핑
    """
    if not targets:
        return {}

    system = (
        GEMINI_TARGETED_BLOCK_REWRITE_SYSTEM_POST1
        if "Post1" in post_type
        else GEMINI_TARGETED_BLOCK_REWRITE_SYSTEM_POST2
    )

    # 패턴 설명 빌드
    all_patterns = set()
    for blk in targets:
        for p in blk.get("matched_patterns", []):
            all_patterns.add(p)
    pattern_desc = "\n".join(
        f"- '{kw1}' + '{kw2}' 조합 감지" for (kw1, kw2) in all_patterns
    ) or "- 약한 해석 패턴 감지"

    # 타겟 블록 리스트업
    block_lines = []
    for i, blk in enumerate(targets, 1):
        cooc = "【코-오커런스】" if blk.get("has_cooccurrence") else "【섹션 내 패턴】"
        block_lines.append(f"BLOCK_{i}: {cooc}\n{blk['html_block']}")
    target_blocks_str = "\n\n".join(block_lines)

    user_msg = GEMINI_TARGETED_BLOCK_REWRITE_USER.format(
        spine=article_spine or "(뼈대 미제공)",
        weak_patterns=pattern_desc,
        target_blocks=target_blocks_str,
    )

    raw = _call_gemini(
        system,
        user_msg,
        f"Step2.5-P14H:타겟재작성[{label}]",
        temperature=0.35,
    )
    if not raw:
        logger.warning(f"[Phase 14H] 타겟 재작성 Gemini 응답 없음 [{label}]")
        return {}

    # BLOCK_N: 파싱
    replacements: dict = {}
    import re as _re
    block_re = _re.compile(
        r"BLOCK_(\d+)\s*:?\s*(?:\[.*?\]\s*)?\n?(.*?)(?=BLOCK_\d+\s*:|\Z)",
        _re.DOTALL,
    )
    for m in block_re.finditer(raw):
        idx = int(m.group(1)) - 1
        replacement_html = m.group(2).strip()
        if 0 <= idx < len(targets) and replacement_html:
            orig = targets[idx]["html_block"]
            # 길이 안전 가드: 교체본이 원본의 30% 미만이면 스킵
            if len(replacement_html) >= len(orig) * 0.30:
                replacements[orig] = replacement_html
            else:
                logger.warning(
                    f"[Phase 14H] BLOCK_{idx+1} 교체본 너무 짧음 "
                    f"({len(replacement_html)} < {len(orig)*0.3:.0f}) — 스킵"
                )

    logger.info(
        f"[Phase 14H] 타겟 재작성 완료 [{label}] | "
        f"타겟 {len(targets)}개 → 교체 {len(replacements)}개"
    )
    return replacements


def _apply_block_replacements(content: str, replacements: dict, label: str = "") -> str:
    """Phase 14 Hotfix Track C: 교체 블록을 원본 HTML에 삽입.

    Args:
        content:      원본 HTML
        replacements: {original_html_block: replacement_html_block}
        label:        로그 레이블

    Returns:
        교체 후 HTML (교체 실패 블록은 원본 유지)
    """
    result = content
    applied = 0
    for orig, replacement in replacements.items():
        if orig in result:
            result = result.replace(orig, replacement, 1)
            applied += 1
        else:
            logger.warning(
                f"[Phase 14H] 원본 블록 미탐지 — 교체 스킵 "
                f"[{label}] (블록 앞 40자: {orig[:40]!r})"
            )
    logger.info(f"[Phase 14H] HTML 교체 적용 [{label}]: {applied}/{len(replacements)}개")
    return result


def _enforce_interpretation_rewrite(
    content: str,
    weak_interp_hits: int,
    label: str = "",
    article_spine: str = "",
) -> str:
    """Phase 14 Track C (Hotfix): weak_interpretation FAIL 시 타겟 블록 교체 실행.

    Phase 14.1 변경:
    - 전체 기사 재작성 → 타겟 블록 단위 교체로 전환
    - 약한 패턴 키워드가 실제로 동시 등장하는 블록만 Gemini에 전달
    - 교체 후 re-score로 해소 여부 검증

    Args:
        content:          Phase 13 진단 후 콘텐츠 (HTML)
        weak_interp_hits: Phase 13 weak_hits 수 (>= 3 이면 FAIL)
        label:            로그 레이블 ("Post1" | "Post2" 등)
        article_spine:    Post1 분석 뼈대 문장 (선택)

    Returns:
        교체 후 콘텐츠 (실패/스킵 시 원본 반환)
    """
    if weak_interp_hits < 3:
        logger.info(
            f"[Phase 14] 재작성 패스 스킵 [{label}] — "
            f"weak_hits={weak_interp_hits} (임계값 3 미만)"
        )
        return content

    logger.info(
        f"[Phase 14] 타겟 재작성 시작 [{label}] — weak_hits={weak_interp_hits}"
    )

    # ── Step 1: 타겟 블록 추출 ──────────────────────────────────────────────
    targets = _extract_weak_interp_blocks(content)
    logger.info(
        f"[Phase 14H] 타겟 블록 추출 [{label}]: {len(targets)}개 "
        f"(코-오커런스 {sum(1 for t in targets if t.get('has_cooccurrence'))}개)"
    )

    if targets:
        # ── Step 2: 타겟 블록 Gemini 재작성 ──────────────────────────────
        post_type = "Post1" if "Post1" in label or "1" in label else "Post2"
        replacements = _rewrite_weak_blocks(targets, article_spine, post_type, label)

        if replacements:
            # ── Step 3: HTML 교체 적용 ────────────────────────────────────
            updated = _apply_block_replacements(content, replacements, label)

            # ── Step 4: PICKS 주석 보존 ───────────────────────────────────
            if "<!-- PICKS:" in content and "<!-- PICKS:" not in updated:
                picks_match = re.search(r"<!--\s*PICKS:.*?-->", content, re.DOTALL)
                if picks_match:
                    updated = updated.rstrip() + "\n" + picks_match.group(0)
                    logger.info(f"[Phase 14H] PICKS 주석 복원 [{label}]")

            # ── Step 5: re-score 검증 ────────────────────────────────────
            new_score = _score_interpretation_quality(updated, label=f"{label}-타겟교체후")
            new_hits = new_score.get("weak_interp_hits", weak_interp_hits)
            if new_hits < weak_interp_hits:
                logger.info(
                    f"[Phase 14H] 타겟 교체 성공 [{label}] — "
                    f"weak_hits {weak_interp_hits} → {new_hits}"
                )
            else:
                logger.warning(
                    f"[Phase 14H] 타겟 교체 후 weak_hits 불변 [{label}] — "
                    f"{weak_interp_hits} → {new_hits} (패턴이 비-해석 섹션에 잔존)"
                )
            logger.info(
                f"[Phase 14H] 교체 완료 [{label}] | "
                f"원본 {len(content)}자 → 교체 후 {len(updated)}자"
            )
            return updated
        else:
            logger.warning(
                f"[Phase 14H] 타겟 블록 재작성 결과 없음 [{label}] — "
                "전체 기사 재작성 폴백 시도"
            )
    else:
        logger.info(
            f"[Phase 14H] 타겟 블록 미추출 [{label}] — "
            "키워드가 다른 섹션에 분산됨, 전체 기사 폴백"
        )

    # ── Fallback: 전체 기사 재작성 (기존 Phase 14 방식) ─────────────────────
    logger.info(f"[Phase 14] 전체 기사 재작성 폴백 [{label}]")
    pattern_lines = []
    for (kw1, kw2) in _P13_WEAK_INTERP_PATTERNS[:8]:
        import re as _re
        plain = _re.sub(r"<[^>]+>", " ", content)
        if kw1 in plain and kw2 in plain:
            pattern_lines.append(f"- '{kw1}' + '{kw2}' 조합 (교과서 인과 의심)")
    pattern_desc = "\n".join(pattern_lines) if pattern_lines else "- 교과서 인과 패턴 다수 감지"

    user_msg = GEMINI_INTERP_REWRITE_USER.format(
        weak_patterns=pattern_desc,
        draft=content,
    )
    rewritten = _call_gemini(
        GEMINI_INTERP_REWRITE_SYSTEM,
        user_msg,
        f"Step2.5-P14:해석재작성폴백[{label}]",
        temperature=0.4,
    )

    if not rewritten or len(rewritten.strip()) < len(content) * 0.70:
        logger.warning(f"[Phase 14] 폴백 재작성 결과 불충분 [{label}] — 원본 유지")
        return content

    rewritten = _strip_code_fences(rewritten)
    if "<!-- PICKS:" in content and "<!-- PICKS:" not in rewritten:
        picks_match = re.search(r"<!--\s*PICKS:.*?-->", content, re.DOTALL)
        if picks_match:
            rewritten = rewritten.rstrip() + "\n" + picks_match.group(0)
    logger.info(
        f"[Phase 14] 폴백 재작성 완료 [{label}] | "
        f"원본 {len(content)}자 → 재작성 {len(rewritten)}자"
    )
    return rewritten


# ── Track D: Numeric Sanity Recalibration ────────────────────────────────────
# Phase 14: 2026년 실제 시장 레인지 반영 (KOSPI 5,500+ 수용)
# Phase 13의 4,500 상한을 상향해 false-positive HOLD 억제
_P14_SANITY_RANGES: dict = {
    "kospi":  (1500, 8000),   # 2026+ 5,500+ 레인지 수용
    "kosdaq": (400,  4000),
    "usdkrw": (900,  2500),
}

# 자릿수 오류 등 명백한 비정상값만 HARD_FAIL
_P14_SANITY_HARD_FAIL_RANGES: dict = {
    "kospi":  (100,  50000),
    "kosdaq": (50,   20000),
    "usdkrw": (100,  5000),
}


# ──────────────────────────────────────────────────────────────────────────────
# SECTION A: 내부 유틸 — API 호출 래퍼
# ──────────────────────────────────────────────────────────────────────────────

def _call_gpt(system: str, user: str, label: str,
              temperature: float = 0.7, max_tokens: int = 4000) -> str:
    """GPT-4o 호출 + 비용 기록. 실패 시 빈 문자열 반환."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env에 설정되지 않았습니다.")

    client = OpenAI(api_key=api_key)
    logger.info(f"GPT-4o 호출 시작 ({label})")

    if os.getenv("DEBUG_LLM"):
        logger.debug(
            f"[DEBUG_LLM] GPT payload ({label}) | "
            f"model=gpt-4o temperature={temperature} max_tokens={max_tokens} "
            f"system_len={len(system)} user_len={len(user)}"
        )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system.strip()},
            {"role": "user", "content": user.strip()},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    content = response.choices[0].message.content or ""
    logger.info(f"GPT-4o 완료 ({label}) | 길이: {len(content)}자")

    if response.usage:
        cost_tracker.record_openai_usage(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

    return content


def _call_gemini(system: str, user: str, label: str,
                 temperature: float = 0.3) -> Optional[str]:
    """Gemini 2.5-flash 호출 + 비용 기록. 실패 시 None 반환."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning(f"GEMINI_API_KEY 없음 — {label} 건너뜀")
        return None

    try:
        client = genai.Client(api_key=api_key)
        logger.info(f"Gemini 호출 시작 ({label})")

        if os.getenv("DEBUG_LLM"):
            logger.debug(
                f"[DEBUG_LLM] Gemini payload ({label}) | "
                f"model=gemini-2.5-flash temperature={temperature} "
                f"max_output_tokens=3000 thinking_budget=0 "
                f"system_len={len(system)} user_len={len(user)}"
            )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user.strip(),
            config=genai_types.GenerateContentConfig(
                system_instruction=system.strip(),
                max_output_tokens=3000,
                temperature=temperature,
                thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
            ),
        )

        result = response.text or ""
        logger.info(f"Gemini 완료 ({label}) | 길이: {len(result)}자")

        if response.usage_metadata:
            cost_tracker.record_gemini_usage(
                input_tokens=response.usage_metadata.prompt_token_count or 0,
                output_tokens=response.usage_metadata.candidates_token_count or 0,
            )

        return result

    except Exception as e:
        logger.warning(f"Gemini 호출 실패 ({label}): {e}")
        return None


def _parse_json_response(raw: str) -> Optional[dict]:
    """
    LLM 출력에서 JSON을 파싱합니다.
    ```json ... ``` 코드 블록을 자동으로 제거하고 json.loads를 시도합니다.
    실패 시 None 반환.
    """
    if not raw:
        return None
    # ```json ... ``` 또는 ``` ... ``` 블록 제거
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw.strip())
    try:
        result = json.loads(cleaned)
        return result
    except json.JSONDecodeError:
        # 중괄호/대괄호 블록만 추출 재시도
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    logger.warning("JSON 파싱 실패 — None 반환")
    return None


# ──────────────────────────────────────────────────────────────────────────────
# SECTION B: 내부 유틸 — 데이터 포맷팅
# ──────────────────────────────────────────────────────────────────────────────

_DATE_TIER_LABELS = {
    "recent":   "[최근 7일]",
    "extended": "[7-30일]",
    "unknown":  "[날짜불명]",
}


def format_articles_for_prompt(articles: list) -> str:
    """뉴스 기사 리스트를 프롬프트용 텍스트로 변환합니다 (v3: date_tier 마커 포함)."""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    lines = [f"[{today} 뉴스 데이터]\n"]

    grouped: dict = {}
    for article in articles:
        src = article.get("source", "기타")
        grouped.setdefault(src, []).append(article)

    for source_name, items in grouped.items():
        lines.append(f"\n## {source_name} ({len(items)}건)")
        for i, item in enumerate(items, 1):
            title = item.get("title", "제목 없음")
            summary = item.get("summary", "")
            url = item.get("url", "")
            tier = item.get("date_tier", "unknown")
            tier_label = _DATE_TIER_LABELS.get(tier, "[날짜불명]")
            lines.append(f"{i}. {tier_label} {title}")
            if url:
                lines.append(f"   URL: {url}")
            if summary:
                lines.append(f"   요약: {summary[:200]}")

    return "\n".join(lines)


# 리서치/뉴스 컨텍스트 구분자 (Phase 6)
RESEARCH_NEWS_SEPARATOR = (
    "─" * 40 + "\n[뉴스 기사 — 보조 컨텍스트]\n" + "─" * 40
)


def format_research_for_prompt(research: list) -> str:
    """
    리서치 데이터를 프롬프트용 텍스트로 변환합니다 (v3: date_tier 마커 + weight 정렬).
    weight 내림차순 정렬, [⭐ 핵심 리서치] + 시점 마커 포함.
    """
    if not research:
        return "(리서치 데이터 없음)"

    today = datetime.now().strftime("%Y년 %m월 %d일")
    lines = [f"[{today} 리서치·컨센서스 데이터 — 우선순위순]\n"]

    sorted_research = sorted(research, key=lambda x: x.get("weight", 1), reverse=True)

    for i, item in enumerate(sorted_research, 1):
        source  = item.get("source", "기타")
        title   = item.get("title", "제목 없음")
        summary = item.get("summary", "")
        url     = item.get("url", "")
        broker  = item.get("broker", "")
        target  = item.get("target_price", "")
        sector  = item.get("sector", "")
        weight  = item.get("weight", 1)
        tier    = item.get("date_tier", "unknown")
        tier_label = _DATE_TIER_LABELS.get(tier, "[날짜불명]")

        priority_marker = "[⭐ 핵심 리서치] " if weight >= 5 else ""
        lines.append(f"{i}. {priority_marker}{tier_label} [{source}] {title}")

        meta_parts = []
        if broker:
            meta_parts.append(f"증권사: {broker}")
        if sector:
            meta_parts.append(f"섹터: {sector}")
        if target:
            meta_parts.append(f"목표가: {target}")
        if meta_parts:
            lines.append(f"   {' | '.join(meta_parts)}")

        if url:
            lines.append(f"   URL: {url}")
        if summary:
            lines.append(f"   요약: {summary[:200]}")
        pdf_snippet = item.get("pdf_snippet", "")
        if pdf_snippet:
            lines.append(f"   [PDF 본문 발췌] {pdf_snippet[:_PDF_PROMPT_SNIPPET_LEN]}")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# SECTION C: 내부 유틸 — 주가 조회
# ──────────────────────────────────────────────────────────────────────────────

def _fetch_naver_price(ticker: str) -> Optional[str]:
    """
    네이버 금융 해외주식 페이지에서 종가를 스크래핑합니다.
    yfinance가 N/A를 반환할 때 폴백으로 호출됩니다.
    NASDAQ(.O) → NYSE(.N) 순서로 시도합니다.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Referer": "https://finance.naver.com/",
    }

    for suffix in [".O", ".N", ".K"]:
        url = f"https://finance.naver.com/world/sise.naver?symbol={ticker}{suffix}"
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue

            resp.encoding = resp.apparent_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            price_elem = (
                soup.select_one(".now")
                or soup.select_one("#rate_view .now")
                or soup.select_one(".price_now .num")
                or soup.select_one("strong.tit_sd")
            )

            if price_elem:
                raw = price_elem.get_text(strip=True).replace(",", "")
                digits = re.sub(r"[^\d.]", "", raw)
                if digits:
                    price_float = float(digits)
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    logger.info(f"네이버금융 종가 조회 성공: {ticker}{suffix} = ${price_float:,.2f}")
                    return f"${price_float:,.2f} ({date_str} 기준, 네이버금융)"

        except Exception as e:
            logger.debug(f"네이버금융 조회 실패 ({ticker}{suffix}): {e}")
            continue

    logger.warning(f"네이버금융에서도 {ticker} 종가를 찾지 못했습니다.")
    return None


def fetch_stock_prices(tickers: list) -> dict:
    """
    티커 리스트의 최신 종가를 조회합니다.
    - 성공 시: '$184.77 (2026-03-11 기준)' 형식 반환
    - yfinance N/A → 네이버 금융 폴백
    - 모두 실패 시: 'N/A' 반환
    """
    prices = {}
    for ticker_str in tickers:
        try:
            t = yf.Ticker(ticker_str)
            hist = t.history(period="1d")
            if not hist.empty:
                price = round(hist["Close"].iloc[-1], 2)
                price_date = hist.index[-1].strftime("%Y-%m-%d")
                prices[ticker_str] = f"${price:,.2f} ({price_date} 기준)"
            else:
                logger.info(f"{ticker_str} yfinance N/A → 네이버금융 폴백 시도")
                naver = _fetch_naver_price(ticker_str)
                prices[ticker_str] = naver if naver else "N/A"
        except Exception as e:
            logger.warning(f"{ticker_str} yfinance 조회 실패: {e} → 네이버금융 폴백 시도")
            naver = _fetch_naver_price(ticker_str)
            prices[ticker_str] = naver if naver else "N/A"

    logger.info(f"종가 조회 완료: {prices}")
    return prices


def _fetch_korean_stock_price(ticker_kr: str) -> str:
    """
    한국 주식 실시간 가격 조회.
    - yfinance: '005930.KS' 형식으로 조회
    - 실패 시 네이버금융 item 페이지 스크래핑
    - 반환: '₩84,500 (2026-03-12 기준)' 형식
    """
    try:
        t = yf.Ticker(ticker_kr)
        hist = t.history(period="1d")
        if not hist.empty:
            price = round(hist["Close"].iloc[-1], 0)
            price_date = hist.index[-1].strftime("%Y-%m-%d")
            return f"₩{int(price):,} ({price_date} 기준)"
    except Exception as e:
        logger.debug(f"{ticker_kr} yfinance 조회 실패: {e}")

    try:
        code = ticker_kr.split(".")[0]
        url = f"https://finance.naver.com/item/main.nhn?code={code}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Referer": "https://finance.naver.com/",
        }
        resp = requests.get(url, headers=headers, timeout=8)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        price_elem = (
            soup.select_one(".today .blind")
            or soup.select_one("#chart_area .rate_info .today")
            or soup.select_one("p.no_today em")
        )
        if price_elem:
            raw = re.sub(r"[^\d]", "", price_elem.get_text(strip=True))
            if raw:
                price_int = int(raw)
                date_str = datetime.now().strftime("%Y-%m-%d")
                logger.info(f"네이버금융 한국주식 조회 성공: {ticker_kr} = ₩{price_int:,}")
                return f"₩{price_int:,} ({date_str} 기준, 네이버금융)"
    except Exception as e:
        logger.debug(f"{ticker_kr} 네이버금융 한국주식 조회 실패: {e}")

    return "N/A"


def _get_price_for_ticker(ticker: str) -> str:
    """티커 형식에 따라 한국(.KS/.KQ) 또는 미국 주식 가격을 조회합니다."""
    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        return _fetch_korean_stock_price(ticker)
    else:
        prices = fetch_stock_prices([ticker])
        return prices.get(ticker, "N/A")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION D: 내부 유틸 — 포트폴리오 + 콘텐츠 조립
# ──────────────────────────────────────────────────────────────────────────────

def parse_picks_from_content(content: str) -> list:
    """<!-- PICKS: [...] --> 블록에서 티커 리스트를 추출합니다."""
    match = re.search(r"<!--\s*PICKS:\s*(\[.*?\])\s*-->", content, re.DOTALL)
    if not match:
        logger.warning("PICKS JSON 블록을 찾지 못했습니다.")
        return []
    try:
        picks = json.loads(match.group(1))
        return picks if isinstance(picks, list) else []
    except json.JSONDecodeError as e:
        logger.warning(f"PICKS JSON 파싱 실패: {e}")
        return []


def save_portfolio(picks: list, prices: dict) -> None:
    """픽 히스토리를 portfolio.json에 누적 저장합니다."""
    portfolio_path = os.path.join(os.path.dirname(__file__), "portfolio.json")

    existing: list = []
    if os.path.exists(portfolio_path):
        try:
            with open(portfolio_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []

    today = datetime.now().strftime("%Y-%m-%d")
    for pick in picks:
        ticker = pick.get("ticker", "")
        entry = {
            "date": today,
            "ticker": ticker,
            "price": prices.get(ticker, "N/A"),
            "reason": pick.get("reason", ""),
        }
        existing.append(entry)

    with open(portfolio_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    logger.info(f"portfolio.json 저장 완료 | 누적 {len(existing)}건")


def _strip_code_fences(text: str) -> str:
    """
    GPT/Gemini 출력에서 코드펜스(```html, ```)와 잔여 백틱 래퍼를 제거합니다.
    실제 HTML 콘텐츠는 보존됩니다.
    모든 게시 경로(Post1 draft, Post2 assemble, verify 수정본)에 공통 적용.

    Phase 4.3 강화:
    - 앞뒤 코드펜스 제거
    - 문서 내 잔여 코드펜스 제거 (중간 ```html 등)
    - 불필요한 시작/끝 따옴표 제거
    - HTML 본문 앞뒤의 설명용 래퍼 문자열 제거 (예: "다음은 HTML입니다:")
    """
    if not text:
        return text
    text = text.strip()

    # 1. 앞뒤 코드펜스 제거 (```html ... ``` 또는 ``` ... ```)
    text = re.sub(r"^```(?:html)?\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.IGNORECASE)

    # 2. 문서 내 잔여 코드펜스 제거
    text = re.sub(r"```(?:html)?\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?```", "", text)

    # 3. 불필요한 시작/끝 따옴표 제거 (HTML을 문자열로 감싼 경우)
    text = text.strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    elif text.startswith("'") and text.endswith("'"):
        text = text[1:-1]

    # 4. HTML 본문 앞의 설명 래퍼 문자열 제거
    #    (예: "다음은 HTML 출력입니다:\n<h1>..." → "<h1>...")
    html_start = re.search(r"<[a-zA-Z!]", text)
    if html_start and html_start.start() > 0:
        pre_html = text[: html_start.start()]
        # 앞부분이 200자 미만의 비HTML 텍스트라면 제거
        if len(pre_html) < 200 and not re.search(r"</[a-zA-Z]", pre_html):
            text = text[html_start.start():]

    # 5. HTML 본문 뒤의 설명 래퍼 문자열 제거
    #    (마지막 닫기 태그 또는 HTML 주석 이후의 짧은 설명 텍스트 제거)
    all_html_ends = list(re.finditer(r"</[a-zA-Z]+>|-->", text))
    if all_html_ends:
        last_end = all_html_ends[-1].end()
        post_html = text[last_end:].strip()
        if len(post_html) < 200 and not re.search(r"<[a-zA-Z]", post_html):
            text = text[:last_end]

    return text.strip()


def _fix_double_typing(content: str) -> str:
    """
    GPT/Gemini 출력에서 발생하는 중복 타이핑 패턴을 교정합니다.

    대상:
      - 태그 중복: [해해석] → [해석], [전전망] → [전망]
      - 공백 포함 태그: [해 해석] → [해석], [전 전망] → [전망]
      - 한글 2~4자 단어가 공백 하나를 사이에 두고 즉시 반복: "미 미", "을 을" 등
      - 연속 공백 → 단일 공백
    """
    # 1. 태그 중복 교정
    content = re.sub(r"\[해해석\]",  "[해석]", content)
    content = re.sub(r"\[전전망\]",  "[전망]", content)
    content = re.sub(r"\[해\s해석\]", "[해석]", content)
    content = re.sub(r"\[전\s전망\]", "[전망]", content)

    # 2. 한글 단어 즉시 중복 제거: "미 미칠" → "미칠", "을 을" → "을"
    #    패턴: (한글 1~4자) 공백 (동일 한글) — 단어 경계에서만
    content = re.sub(
        r"([가-힣]{1,4}) \1(?=[가-힣\s<])",
        lambda m: m.group(1),
        content,
    )

    # 3. 연속 공백 정리
    content = re.sub(r"[ \t]{2,}", " ", content)

    return content


def _format_source_section(content: str) -> str:
    """
    '참고 출처' 섹션을 증권사 리서치 / 뉴스 기사 / 기타로 분류해
    시각적으로 명확한 구조로 재구성합니다.
    """
    BROKER_KW = [
        "증권", "투자", "리서치", "Research", "securities", "애널리스트",
        # 1차 확장
        "카카오페이", "하이투자", "상상인", "유안타", "교보", "대신", "이베스트", "유진",
        # 2차 확장 — 단독 표기 대비 (일반어 위험 없는 것만)
        # 신한/NH/IBK: 은행·보험 계열 오탐 방지 위해 투자증권 표기로 한정
        "신한투자", "NH투자", "LS증권", "DB금융", "IBK투자", "BNK", "부국", "신영", "토스증권",
    ]
    NEWS_KW   = ["경제", "신문", "뉴스", "통신", "비즈", "Bloomberg", "Reuters",
                 "로이터", "블룸버그", "CNBC", "전자신문", "조선", "매일", "한경"]

    BOX_STYLE  = ("background:#f9f9f9;border-left:4px solid #b36b00;"
                  "padding:14px 18px;margin:30px 0 0 0;border-radius:0 4px 4px 0;")
    H_STYLE    = "font-size:13px;font-weight:700;color:#555;margin:0 0 8px 0;"
    CAT_STYLE  = "font-size:12px;color:#999;margin:6px 0 2px 0;"
    UL_STYLE   = "margin:0;padding-left:18px;"
    LI_STYLE   = "font-size:13px;line-height:1.8;color:#555;margin:2px 0;"

    def _rebuild(match: re.Match) -> str:
        raw = re.sub(r"<[^>]+>", " ", match.group(0))
        parts = re.split(r"[\n,·•]+", raw)
        items = [p.strip(" \t\r-") for p in parts if len(p.strip()) > 2]
        items = [i for i in items if i.lower() not in ("참고 출처", "참고출처")]

        brokers = [i for i in items if any(k in i for k in BROKER_KW)]
        news    = [i for i in items if any(k in i for k in NEWS_KW) and i not in brokers]
        others  = [i for i in items if i not in brokers and i not in news]

        out = [f'<div style="{BOX_STYLE}">',
               f'<h3 style="{H_STYLE}">참고 출처</h3>']

        def _section(label: str, icon: str, lst: list) -> None:
            if not lst:
                return
            out.append(f'<p style="{CAT_STYLE}">{icon} {label}</p>')
            out.append(f'<ul style="{UL_STYLE}">')
            for x in lst:
                out.append(f'<li style="{LI_STYLE}">{x}</li>')
            out.append("</ul>")

        _section("증권사 리서치", "📊", brokers)
        _section("뉴스 기사",    "📰", news)
        _section("기타",         "📌", others)

        out.append("</div>")
        return "\n".join(out)

    content = re.sub(
        r"<h3[^>]*>\s*참고\s*출처\s*</h3>.*?(?=<h3|<!--\s*PICKS|$)",
        _rebuild,
        content,
        flags=re.DOTALL,
    )
    return content


def assemble_final_content(raw_content: str, picks: list, prices: dict) -> str:
    """
    GPT 초고에서 PICKS JSON 주석을 제거하고,
    각 티커의 {PRICE_PLACEHOLDER}를 실제 종가(기준일 포함)로 교체합니다.
    Phase 5-A: 오탈자·중복 타이핑 교정 + 참고 출처 섹션 재구성 추가.
    """
    content = _strip_code_fences(raw_content)  # Phase 4.3: 코드펜스/백틱 제거
    content = re.sub(r"<!--\s*PICKS:\s*\[.*?\]\s*-->", "", content, flags=re.DOTALL)

    for pick in picks:
        ticker = pick.get("ticker", "")
        price = prices.get(ticker, "N/A")
        if "{PRICE_PLACEHOLDER}" in content:
            content = content.replace("{PRICE_PLACEHOLDER}", price, 1)

    content = content.replace("{PRICE_PLACEHOLDER}", "N/A")
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Phase 5-A 후처리
    content = _fix_double_typing(content)      # 오탈자/중복 타이핑 교정
    content = _format_source_section(content)  # 참고 출처 섹션 재구성

    return content.strip()


def extract_title(markdown_content: str) -> str:
    """마크다운에서 H1 제목을 추출합니다 (참조용 유지)."""
    for line in markdown_content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    today = datetime.now().strftime("%Y-%m-%d")
    return f"[오늘의 캐시픽] {today} 글로벌 마켓 브리핑"


def convert_to_html(content: str) -> str:
    """
    마크다운을 WordPress HTML로 변환합니다 (인프라 참조용 유지).
    Phase 7 파이프라인에서는 GPT가 HTML을 직접 출력하므로 일반적으로 호출되지 않습니다.
    """
    H1_STYLE = (
        "font-size:2em;font-weight:800;color:#1a1a1a;"
        "margin:0 0 30px 0;padding-bottom:14px;"
        "border-bottom:3px solid #1a1a1a;line-height:1.3;"
    )
    SUB_H_STYLE = (
        "border-left:6px solid #1a1a1a;padding:12px 18px;"
        "background-color:#f4f4f4;margin:45px 0 20px 0;"
        "color:#1a1a1a;font-size:1.4em;"
    )
    P_STYLE = "font-size:15px;line-height:1.9;color:#333;margin:0 0 16px 0;"
    HR_STYLE = "border:0;border-top:1px solid #eee;margin:30px 0;"
    BQ_STYLE = (
        "border-left:4px solid #b36b00;margin:12px 0;"
        "padding:10px 18px;background:#fffdf5;color:#555;"
    )
    UL_STYLE = "margin:0.5em 0 0.8em 1.4em;padding:0;color:#333;"
    OL_STYLE = "margin:0.5em 0 0.8em 1.4em;padding:0;color:#333;"
    LI_STYLE = "font-size:15px;line-height:1.8;margin:0.3em 0;"
    STRONG_STYLE = "font-weight:700;color:#1a1a1a;"
    A_STYLE = "color:#1a1a1a;text-decoration:underline;"
    PICKS_DIV_STYLE = (
        "padding:25px;background-color:#fffaf0;"
        "border-left:5px solid #b36b00;margin:30px 0;"
    )

    html = md_lib.markdown(content, extensions=["tables", "fenced_code"])

    for level in [2, 4]:
        html = html.replace(f"<h{level}>", f'<h3 style="{SUB_H_STYLE}">')
        html = html.replace(f"</h{level}>", "</h3>")
    html = html.replace("<h3>", f'<h3 style="{SUB_H_STYLE}">')
    html = html.replace("<h1>", f'<h1 style="{H1_STYLE}">')
    html = html.replace("<p>", f'<p style="{P_STYLE}">')
    html = html.replace("<hr>", f'<hr style="{HR_STYLE}">')
    html = html.replace("<hr />", f'<hr style="{HR_STYLE}">')
    html = html.replace("<blockquote>", f'<blockquote style="{BQ_STYLE}">')
    html = html.replace("<ul>", f'<ul style="{UL_STYLE}">')
    html = html.replace("<ol>", f'<ol style="{OL_STYLE}">')
    html = html.replace("<li>", f'<li style="{LI_STYLE}">')
    html = html.replace("<strong>", f'<strong style="{STRONG_STYLE}">')
    html = re.sub(r"<a ", f'<a style="{A_STYLE}" ', html)

    picks_pattern = re.compile(
        r"(<h3[^>]*>.*?캐시의\s*픽.*?</h3>)(.*?)(<h3[^>]*>.*?참고\s*출처.*?</h3>)",
        re.DOTALL,
    )

    def _wrap_picks_box(m: re.Match) -> str:
        return (
            f"{m.group(1)}"
            f'<div style="{PICKS_DIV_STYLE}">'
            f"{m.group(2).strip()}"
            f"</div>\n"
            f"{m.group(3)}"
        )

    html = picks_pattern.sub(_wrap_picks_box, html)
    return html


# ──────────────────────────────────────────────────────────────────────────────
# SECTION E: Phase 7 — v2 프롬프트 상수
# ──────────────────────────────────────────────────────────────────────────────

# ─── HTML 스타일 인라인 상수 (GPT 시스템 프롬프트에 삽입) ───────────────────
_H3_STYLE = (
    "border-left:6px solid #1a1a1a;padding:12px 18px;"
    "background-color:#f4f4f4;margin:45px 0 20px 0;"
    "color:#1a1a1a;font-size:1.4em;"
)
_HR_STYLE = "border:0;border-top:1px solid #eee;margin:30px 0;"
_P_STYLE  = "font-size:15px;line-height:1.9;color:#333;margin:0 0 16px 0;"
_H1_STYLE = (
    "font-size:2em;font-weight:800;color:#1a1a1a;"
    "margin:0 0 30px 0;padding-bottom:14px;"
    "border-bottom:3px solid #1a1a1a;line-height:1.3;"
)
_PICKS_DIV_STYLE = (
    "padding:25px;background-color:#fffaf0;"
    "border-left:5px solid #b36b00;margin:30px 0;"
)


# ─── Step 1: Gemini 분석 엔진 프롬프트 ──────────────────────────────────────

GEMINI_ANALYST_SYSTEM = """
너는 매크로몰트(MacroMalt) 리서치 데스크 수석 매크로 애널리스트다.

역할: 수집된 뉴스·리서치 데이터를 분석해 블로그 작성자(ChatGPT)가 사용할
      '구조화된 리포트 재료'를 생성한다.

[핵심 테마 선정 규칙 — 매크로몰트 Phase 4.3 최우선 준수]
- 핵심 테마는 반드시 1개만 선정한다.
- 가장 많은 출처가 수렴하고, 숫자 데이터가 풍부한 테마를 선택한다.
- 핵심 테마와 직접 관련 없는 자료는 facts 배열에서 제외하고 "보조 배경"으로 분리한다.
- 예시 (잘못된 방식): "지정학 리스크 + 유가 + 무역정책 + IT 실적" 4개를 병렬 나열
- 예시 (올바른 방식): "미국 관세 인상이 한국 IT 수출에 미치는 실질적 영향" 1개에 집중
  → 지정학/유가는 이 핵심 테마를 설명하는 배경으로만 활용

[자료 시점 정책 — 최우선 준수 (매크로몰트 운영 정책 v3)]
- [최근 7일] 마커가 붙은 자료를 최우선 근거로 사용한다. facts 배열에 포함.
- [7-30일] 마커가 붙은 자료는 보조 근거로만 사용한다. background_facts 배열에 별도 분리.
- [날짜불명] 자료는 uncertainties에 "출처·시점 불명"으로 등재. 핵심 근거 사용 금지.
- 30일 초과 자료는 현재 시황 근거로 절대 사용하지 않는다.
- 종목·지수·금리·환율·유가·목표가·투자의견 등 시점 민감 정보는
  [최근 7일] 자료에서만 facts에 포함한다.

[DART 공시 데이터 처리 지침 — Phase 5-C]
- 입력 데이터에 "[DART 주요사항보고서 — 최근 14일 공시 이벤트]" 섹션이 있으면 공식 공시 사실로 취급한다.
- "원문발췌:" 항목은 해당 공시의 실제 본문 내용이다. 수치·계약 조건·사건 발생일이 포함된 경우
  facts에 포함하되 source="DART 공시 (회사명)", date=접수일로 명시한다.
- 공시 이벤트 자체(수주계약·자기주식취득·무상증자 등)는 핵심 테마와 관련 있을 때만 facts에 포함.
- 관련 없는 공시는 auxiliary_context 1문장으로만 처리한다.

[출력 규칙 — 최우선]
- 반드시 아래 JSON 구조로만 출력할 것.
- 설명 텍스트, 마크다운 코드 블록(```), 서문 없이 JSON 객체 하나만 출력.
- 사실(fact)과 해석(interpretation)을 절대 혼합하지 말 것.
- 목표가·투자의견·현재가는 명확한 출처와 기준일이 있을 때만 facts에 포함.
- 출처가 불분명한 수치는 uncertainties에 이동.
- facts는 핵심 테마 관련성이 높은 순서로 정렬한다 (가장 중요한 사실이 첫 번째).

[출력 JSON 구조]
{
  "theme": "오늘의 핵심 경제 테마 (한 문장, 구체적으로 — 단일 주제여야 함)",
  "theme_sub_axes": [
    "핵심 테마를 분해하는 하위 축 1 (본문 섹션 1의 핵심)",
    "하위 축 2 (본문 섹션 2의 핵심)",
    "하위 축 3 (본문 섹션 3의 핵심)"
  ],
  "facts": [
    {
      "content": "확인된 사실 내용 (숫자·날짜·기관명 포함)",
      "source": "출처명 (언론사명, 기관명, 리포트명 등)",
      "date": "기준 시점 (YYYY-MM-DD 또는 'YYYY년 Q분기' 등)",
      "tier": "recent",
      "relevance_to_theme": "이 사실이 핵심 테마와 어떻게 연결되는지 한 줄 설명",
      "why_it_matters": "이 숫자/사실이 왜 중요한지 인과관계 한 줄 설명"
    }
  ],
  "background_facts": [
    {
      "content": "7~30일 자료 — 배경 설명용으로만 사용 가능한 사실",
      "source": "출처명",
      "date": "기준 시점",
      "tier": "extended",
      "relevance_to_theme": "배경으로서 역할 한 줄"
    }
  ],
  "auxiliary_context": "핵심 테마와 직접 관련 없지만 독자 이해를 위해 필요한 배경 정보 (1~2문장)",
  "market_impact": "이 테마가 금융시장에 미치는 영향 경로 (사실 기반, 해석 금지, 구체적 대상 포함)",
  "counter_interpretations": [
    "이 테마에 대한 반대 해석 — 이번 테마에 특화된 내용만 (범용 리스크 금지)",
    "반대 해석 2 (없으면 빈 배열 [])"
  ],
  "uncertainties": [
    "이 분석에서 불확실한 요소 또는 추가 확인이 필요한 사항"
  ],
  "writing_notes": "ChatGPT 작성자에게 전달할 주의사항 (과장 금지 항목, 반복 금지 표현, 민감한 표현 등)"
}

facts는 반드시 5개 이상 10개 이하 (핵심 테마와 직접 관련된 최근 7일 자료 중심).
background_facts는 있는 경우만 포함, 없으면 빈 배열 [].
핵심 테마와 무관한 사실은 facts에 포함하지 말고 auxiliary_context에 한 줄로 요약.

[facts 필터링 규칙 — Phase 4.3 추가]
- facts 배열에서 핵심 테마와 직접 관련이 없는 항목은 우선 제외한다.
- 예: 핵심 테마가 "AI 반도체 수요 급증"이라면 유가·지정학·금리 관련 사실은 facts에서 제외하고 auxiliary_context로 이동.
- relevance_to_theme 항목이 "간접적 영향" 또는 "배경" 수준이면 background_facts로 분류한다.
- facts에는 핵심 테마와 직접 인과관계를 가진 항목만 남긴다.
"""

GEMINI_ANALYST_USER = """
아래 데이터를 분석해 오늘의 구조화된 리포트 재료를 JSON으로 출력하라.

[⭐ 핵심 리서치 — 최우선 참고]
[⭐ 핵심 리서치] 마커가 붙은 항목은 전문 애널리스트 의견이므로 가장 높은 가중치로 반영.
{research_text}

[뉴스 기사 — 보조 참고]
{news_text}

{dart_text}
"""


# ─── Step 2a: GPT 작성 엔진 — Post 1 심층 분석 프롬프트 ─────────────────────

GPT_WRITER_ANALYSIS_SYSTEM = f"""
너는 매크로몰트(MacroMalt) 오너 바텐더 '캐시(Cash)'다.
Gemini 애널리스트가 정리한 구조화된 리포트 재료를 바탕으로 금융 분석 글을 작성한다.

[단일 테마 집중 규칙 — Phase 4.3 최우선 준수]
- 이 글은 핵심 테마 1개만 다룬다.
- 핵심 테마와 직접 연결되지 않는 이슈(지정학·유가·금리 등)는
  독립 섹션으로 다루지 말고, 핵심 테마를 보조하는 배경 1~2문장으로만 축소한다.
- 핵심 테마와 무관한 섹션은 자동으로 삭제하거나 핵심 테마 맥락으로 흡수한다.
- 보조 이슈(유가·지정학·금리 등)를 병렬로 나열해 섹션을 확장하는 것은 금지한다.
- 배경 설명이 핵심 테마의 집중도를 해칠 경우 과감히 생략한다.
- 글 제목·도입부·본문 핵심 섹션 3개가 모두 동일한 중심 테마를 향해야 한다.
- 같은 사실을 표현만 바꿔 2회 이상 반복하지 않는다.
- "긍정적이다", "영향을 줄 수 있다", "수혜가 예상된다", "중요한 요소다" 같은
  완충 문장은 단독으로 쓰지 않는다. 반드시 구체 근거와 함께 쓴다.

[자료 시점 규칙 — 반드시 준수 (매크로몰트 v3)]
- facts 배열 자료(최근 7일)를 중심으로 글을 구성한다.
- background_facts 자료(7~30일)는 현재 시황 근거로 절대 사용하지 않는다.
- background_facts를 활용할 경우 반드시 배경·구조 설명 맥락으로만 서술한다.
  (예: "구조적으로는...", "과거 사례를 보면...", "역사적 맥락에서...")
- 30일 초과 자료는 현재 시황 분석에 절대 사용하지 않는다.
- ★ 미래 연도 숫자(예: "2026년 매출", "연간 가이던스", "FY전망치", "추정치")는
  현재 확인된 사실처럼 단정 서술 금지. 반드시 [전망] 태그와 함께 서술한다.
  ❌ 금지 예: "삼성전자는 2026년 매출 300조 원을 기록할 것이다"
  ✅ 허용 예: "[전망] 삼성전자의 2026년 매출은 300조 원으로 예상된다(미래에셋 추정)"
  ※ 예외: "2024년 매출액 X조", "2025년 영업이익 Y억" 등 이미 발표된 과거 확정 실적·집계값은
    [전망] 태그 불필요. 과거 사실로 그대로 서술한다.

[작성 규칙]
1. 사실: 출처가 있는 내용은 일반 문장으로 자연스럽게 서술
2. 해석: 문장 앞에 반드시 [해석] 태그를 삽입
3. 전망: 문장 앞에 반드시 [전망] 태그를 삽입
4. 불확실한 내용: "확실하지 않다", "확인되지 않았다" 등 명확히 표기
5. 출처 없는 가격·목표가·투자의견: 절대 작성 금지
6. 도입부에서만 바텐더/위스키 비유를 딱 1회 사용. 이후 본문은 정보 전달·객관성에 집중.
7. 상투적 결론 문장("이상으로 살펴보았습니다", "결론적으로" 등) 금지
8. 기계적인 접속사 패턴 반복 금지

[문단 밀도 규칙 — Phase 4.3 강화판]
각 핵심 섹션 문단은 반드시 4요소를 포함한다:
  1) 확인 가능한 사실 (출처 있는 데이터)
  2) 숫자 또는 기준 시점 (숫자가 나오면 그 의미를 최소 1문장 이상 설명)
  3) 왜 중요한지 설명하는 인과관계 연결 문장
  4) 누구에게 어떤 방향으로 영향을 미치는지

- 핵심 섹션은 Gemini가 제공한 theme_sub_axes 3개를 각각 하나씩 다룬다.
- 사실에서 결론으로 바로 점프하지 말고 중간 고리를 반드시 설명한다.
- 숫자 없는 문단이 연속 2개 이상 이어지지 않도록 한다.
- 반대 시각은 이번 테마에 특화된 내용으로 제시한다 (범용 리스크 문장 금지).

[포맷 규칙 — 마크다운 절대 금지]
- 마크다운 기호(#, ##, **, *, `, ---, [ ]) 절대 사용 금지
- [해석], [전망] 텍스트 마커는 예외적으로 허용
- 코드 블록(```html 등) 절대 금지. HTML 태그로 바로 시작.
- 허용 태그 및 필수 인라인 스타일:
  * 글 제목: <h1 style="{_H1_STYLE}">제목</h1>
  * 소제목: <h3 style="{_H3_STYLE}">소제목</h3>
  * 단락: <p style="{_P_STYLE}">내용</p>
  * 구분선: <hr style="{_HR_STYLE}">
  * 강조: <strong style="font-weight:700;color:#1a1a1a;">강조어</strong>

[글 구조]
1. 제목: <h1>로 작성 — "[심층분석] {{테마}}" 형식 (핵심 테마 1개만 담을 것)
2. 도입부: <p>로 작성 — 위스키/바텐더 비유 1회 + 오늘의 핵심 테마 소개 (150자 내외)
3. 오늘의 시장 컨텍스트: <h3> + <p> — 최근 7일 데이터 중심 현황 정리
4. 핵심 분석 1: <h3> + <p> — theme_sub_axes[0] 에 해당하는 하위 축 (4요소 필수)
5. 핵심 분석 2: <h3> + <p> — theme_sub_axes[1] 에 해당하는 하위 축 (4요소 필수)
6. 핵심 분석 3: <h3> + <p> — theme_sub_axes[2] 에 해당하는 하위 축 (4요소 필수)
7. 반대 시각 및 체크포인트: <h3> + <p> — 이번 테마에 특화된 반론 및 불확실성
8. 참고 출처 섹션: <h3>참고 출처</h3> 후 <p>로 본문에서 실제 사용된 데이터의 출처만 나열
   (미사용 출처 제외 — 본문 데이터와 직접 대응되는 것만)

[자기검수 — 출력 전 반드시 확인]
□ 제목과 본문 3개 핵심 섹션이 모두 같은 핵심 테마를 다루는가
□ 각 핵심 섹션에 숫자 또는 기준 시점이 포함됐는가
□ 숫자가 논리에 연결되어 의미가 설명됐는가
□ 같은 사실을 다른 표현으로 반복한 문장이 있는가 (있으면 삭제)
□ "긍정적이다/영향을 줄 수 있다/수혜가 예상된다" 등 완충 문장이 단독으로 쓰였는가 (있으면 삭제)
□ 반대 시각이 이번 테마에 특화된 내용인가 (범용이면 수정)
□ ★ "2026년", "연간", "가이던스", "전망", "예상", "추정", "상향 조정", "하향 조정"이 포함된 문장이 [전망] 태그 없이 현재 사실로 단정 서술됐는가 (있으면 [전망] 태그 추가 또는 조건부 해석 문장으로 분리)
□ ★ "유망", "주목해야 한다", "담아야 한다", "기회다", "추천", "매력적인 선택지", "저평가 매력", "매수 기회", "하방 경직성 제공", "수혜를 받을 수 있는", "실적 개선 효과를 기대할 수 있는" 등 투자 권유성 표현이 있는가 (있으면 분析형 문장으로 교체)

[분량]
총 2,000자 이상의 HTML 출력
"""

GPT_WRITER_ANALYSIS_USER = """
아래 Gemini 분석 재료를 바탕으로 심층 경제 분석 글을 HTML로 작성하라.

[Gemini 분석 재료 (JSON)]
{materials_json}

[참고 컨텍스트]
{context_text}
"""


# ─── Step 2b: GPT 작성 엔진 — Post 2 종목 리포트 프롬프트 ────────────────────

GPT_WRITER_PICKS_SYSTEM = f"""
너는 매크로몰트(MacroMalt) 오너 바텐더 '캐시(Cash)'다.
오늘의 매크로 분석과 Gemini가 선정한 종목을 바탕으로 '캐시의 픽' 종목 리포트를 작성한다.
캐시의 픽은 종목 소개문이 아니라 종목 리포트다. 밀도와 논리가 핵심이다.

[메인 픽 / 보조 픽 구조 — Phase 4.3]
- 종목이 2~3개 제공될 경우: 첫 번째 종목을 메인 픽, 나머지를 보조 픽으로 처리한다.
- 메인 픽: 가장 논리가 선명하고 리서치 근거가 풍부한 종목. 더 자세히 서술한다.
- 보조 픽: 메인 픽과 다른 방식으로 테마에 연결되는 종목 또는 ETF.
- 메인/보조의 역할 차이가 글에서 명확히 드러나야 한다.

[가격 정보 정책 — 매크로몰트 v3]
- 종가·현재가·목표가는 기본적으로 출력하지 않는다.
- 오직 출처와 기준일이 명확하고 본문 논리에 꼭 필요할 때만 예외적으로 사용한다.
- 사용 시 반드시 "기준 종가 (YYYY-MM-DD)" 형식으로만 표기한다.
- 가격 정보가 없는 자리는 업황 근거, 실적 연결, 수급 변수, 반대 포인트로 채운다.
- 제공된 가격 데이터는 참고용이며, 출처·기준일 없이 본문에 직접 삽입 금지.
- {{PRICE_PLACEHOLDER}} 마커는 검증된 가격이 있을 때만 선택적으로 사용.

[작성 규칙]
1. 사실은 일반 문장, 해석은 [해석], 전망은 [전망] 태그 필수
2. 투자 권유성 표현 전면 금지 — 아래 표현 및 이와 유사한 표현 모두 금지:
   "매수", "매수하세요", "지금 사야 할", "유망", "주목해야 한다", "담아야 한다",
   "기회다", "추천한다", "매력적인 선택지", "관심 가져볼 만한", "주가 상승을 견인",
   "장기 성장 가능성을 갖춘", "긍정적으로 평가", "수혜가 기대",
   "저평가 매력", "매수 기회", "하방 경직성 제공",
   "수혜를 받을 수 있는", "실적 개선 효과를 기대할 수 있는"
   → 대신 분석/관찰/조건부 해석 중심 문장으로 서술한다.
   ✅ 예: "이러한 조건이 지속된다면 실적 개선 여부를 판단할 수 있는 시점은 X분기다"
3. 미래 연도 숫자("2026년 전망", "가이던스", "추정치")는 반드시 [전망] 태그와 함께 서술
4. 근거 부족한 내용은 "확실하지 않다"로 표기
5. 위스키/바텐더 비유: 도입부에 간결하게 테마-종목 연결 (1회, 선택)
6. 같은 사실을 표현만 바꿔 반복하지 않는다

[종목 리포트 규칙 — Phase 4.3 강화판]
각 종목 섹션은 반드시 아래 4단계 순서를 지켜 최소 6문장 이상으로 작성한다:

  문장 1 — 왜 지금 이 종목인가 [★ P6 강화 — 현재 시점 트리거 필수]
    : 단순히 "이 테마와 관련 있는 종목이기 때문"이라는 반복은 충족으로 인정하지 않는다.
    : 반드시 현재 시점의 구체적 트리거(이벤트, 수치 변화, 수급 변화 등)를 제시해야 한다.
      ✅ 충족 예: "이번 주 NVIDIA 실적 발표 후 HBM 공급사에 대한 수주 문의가 집중됐기 때문이다"
      ❌ 불충족 예: "AI 인프라 투자 확대 테마에서 수혜가 기대되는 종목이기 때문이다"
    : 현재 시점 트리거가 없으면 문장 1로 인정하지 않는다.

  문장 2 — 업황·실적·수요 근거 (숫자 필수)
    : 이번 테마와 연결되는 구체적 숫자 또는 기준 시점 반드시 포함
    : 예: 매출, 영업이익, 증감률, PER, 수주잔고, 목표주가, 발표 시점, 기준분기
    : 그 숫자가 왜 중요한지 의미를 1문장 이상 설명
    : ★ 숫자·기준시점이 없으면 문장 2로 인정하지 않는다. 반드시 포함할 것.
    : ★★ 숫자가 있더라도 실제 투자 논리(왜 지금 이 종목인지)와 연결되지 않으면 충족으로 인정하지 않는다.
        예: 단순히 "전년비 10% 성장" → 불충족
        예: "전년비 10% 성장 → AI 서버 수요 급증이 직접 원인 → 이 종목의 주수익원과 일치" → 충족
  문장 3 — 리서치 데이터 연결 (필수)
    : 제공된 리서치 또는 애널리스트 리포트에서 이 종목과 관련된 논점을 반드시 2개 이상 인용
    : ★ 리서치 자료가 1건뿐이라면 업황 데이터·수급 자료로 보완해 2개 이상의 근거를 반드시 확보할 것
    : 복수 리포트가 있으면 공통 논점 + 차이 서술
    : 리서치 데이터가 전혀 없으면 "리서치 부재" 명시 후 업황 데이터 2건으로 대체
  문장 4 — 반영 변수: 시장이 이미 반영했을 변수 또는 수급·밸류에이션 포인트 [★ P8 강화]
    : "리스크가 있다"는 일반 경고가 아니어야 한다.
    : 시장이 이미 기대감을 선반영했을 수 있는 구체적 요소를 제시해야 한다.
      ✅ 충족 예: "HBM 기대감은 이미 주가에 반영돼 PER이 역사적 평균 대비 40% 프리미엄 구간이다"
      ✅ 충족 예: "외국인 순매수가 최근 3주간 집중되며 단기 수급 쏠림이 형성된 상태다"
      ❌ 불충족 예: "글로벌 경기 둔화와 불확실성이 리스크로 존재한다"
    : 선반영 가능 요소 예시: 주가·PER·PBR 레벨 / 외국인·기관 수급 / 컨센서스 목표가 괴리율 /
      최근 주가 상승폭과 기대치 선반영 정도
    : 위 요소 중 1개 이상 없으면 문장 4로 인정하지 않는다.
  문장 5 — 반대 포인트: 가장 중요한 이번 테마 특화 리스크
    : 이번 테마에 특화된 리스크 (범용 "불확실성"·"거시 변수" 금지)
  문장 6 이상 — 논리 보강 또는 체크포인트 연결
    : 종목 섹션이 6문장 미만이 되지 않도록 분량을 확보한다

★ 최소 분량 규칙 (Phase 4.3 추가):
- 각 종목 섹션은 최소 400자 이상으로 작성한다.
- 200자 미만의 코멘트형 요약은 허용하지 않는다.
- 메인 픽은 최소 600자 이상 (근거 → 해석 → 반영 변수 → 리스크 흐름이 모두 드러나야 함).
- "왜 지금인가 / 업황·실적 근거 / 반영 변수 / 반대 포인트" 4구조가 모두 드러나지 않으면 완성으로 인정하지 않는다.

추가 규칙:
- 종목 단락을 카드형 한 줄 요약으로 끝내지 않는다.
- "직접 수혜", "긍정적 흐름", "장기 성장 기대" 같은 표현은 구체 근거 없이 사용 금지.
- 리서치 출처가 있으면 공통 논점을 요약하고, 차이가 있으면 그 차이도 서술한다.
- 가격 정보 없이도 논리만으로 설득 가능해야 한다.
- 메인 픽은 보조 픽보다 반드시 더 길고 근거가 풍부해야 한다 (최소 8문장 목표).

[포맷 규칙 — 마크다운 절대 금지]
- 마크다운 기호(#, **, *, `) 절대 사용 금지
- 코드 블록(```html 등) 절대 금지. HTML 태그로 바로 시작.
- 허용 태그 및 필수 인라인 스타일:
  * 글 제목: <h1 style="{_H1_STYLE}">제목</h1>
  * 소제목: <h3 style="{_H3_STYLE}">소제목</h3>
  * 단락: <p style="{_P_STYLE}">내용</p>
  * 구분선: <hr style="{_HR_STYLE}">
  * 종목 박스: <div style="{_PICKS_DIV_STYLE}">종목 내용</div>
  * 강조: <strong style="font-weight:700;color:#1a1a1a;">강조어</strong>

[글 구조]
1. 제목: <h1>로 작성 — "[캐시의 픽] {{메인종목명}} 외 — {{테마 핵심 키워드}}" 형식
2. 도입부: <p>로 간결하게 오늘의 테마와 종목 선정 배경 연결
3. 오늘 이 테마를 보는 이유: <h3> + <p> — 매크로 근거 설명 (숫자·기준시점 포함)
4. ⭐ 메인 픽: <div style="{_PICKS_DIV_STYLE}">로 감싸고
   - <h3>으로 "⭐ 메인 픽 — 종목명(티커)" 표시
   - 4문장 이상 리포트형 서술 (4단계 순서 준수)
5. 보조 픽 1 (있는 경우): <div style="{_PICKS_DIV_STYLE}">로 감싸고
   - <h3>으로 "보조 픽 — 종목명(티커)" 표시
   - 4문장 이상 리포트형 서술
6. 보조 픽 2 (있는 경우): 동일 형식
7. 체크포인트 3개: <h3> + <p> — 이번 픽을 모니터링할 핵심 변수 (이번 테마 특화)
8. 참고 출처 섹션: <h3>참고 출처</h3> 후 <p>로 사용된 데이터 출처만 나열

[자기검수 — 출력 전 반드시 확인]
□ 각 종목이 최소 6문장(5단계 순서)으로 작성됐는가 (메인 픽은 8문장 이상 목표)
□ 문장 1(왜지금): 단순 테마 반복이 아닌 현재 시점 트리거가 명시됐는가
□ 업황/실적 근거 문장에 반드시 숫자 또는 기준 시점이 포함됐는가
□ 리서치 데이터가 각 종목에 2개 이상 연결됐는가 (없으면 업황 데이터로 대체)
□ 문장 4(반영변수): 선반영 가능 요소(PER/수급/괴리율 등)가 구체적으로 서술됐는가
□ 가격 정보 없이도 논리 밀도가 유지되는가
□ 반대 포인트가 이번 테마에 특화됐는가 (범용이면 수정)
□ 메인 픽과 보조 픽의 역할이 명확하게 구분됐는가
□ 카드형 한 줄 요약으로 끝나는 종목 섹션이 없는가

[마지막 줄 — 필수]
<!-- PICKS: [{{"ticker":"티커","name":"종목명","market":"KR 또는 US","reason":"선정 이유 한 줄"}},...] -->
위 형식의 HTML 주석을 마지막에 반드시 포함할 것.
"""

GPT_WRITER_PICKS_USER = """
아래 정보를 바탕으로 '캐시의 픽' 종목 리포트를 HTML로 작성하라.

[오늘의 핵심 테마]
{theme}

[Gemini 분석 재료 요약]
{materials_summary}

[선정 종목 및 현재가]
{tickers_and_prices}

[참고 컨텍스트]
{context_text}
"""


# ─── Step 3: Gemini 검수 엔진 프롬프트 ──────────────────────────────────────

GEMINI_VERIFIER_SYSTEM = """
너는 매크로몰트(MacroMalt) 금융 콘텐츠 편집장이다.
생성된 금융 분석 초안을 아래 기준으로 검수하고, 반드시 JSON으로만 결과를 출력해라.
설명 텍스트나 서문 없이 JSON 객체 하나만 출력할 것.

[검수 기준 19가지 — 매크로몰트 운영 정책 Phase 4.3]

★ 필수 통과 기준 (1~5번 중 하나라도 위반 시 반드시 pass=false):
1. [시점 일관성] 다음 세 가지를 모두 확인한다:
   ① 최근 7일 중심으로 구성되었는가
   ② background_facts(7~30일) 자료가 현재 시황 근거로 쓰이지 않았는가
   ③ ★ "2026년", "연간", "가이던스", "전망", "예상", "추정", "상향 조정", "하향 조정"이 포함된 문장이
      [전망] 태그 없이 현재 확인된 사실처럼 단정 서술되지 않았는가
      ※ 예외: "2024년 매출액", "2025년 영업이익" 등 이미 발표된 과거 확정 실적·집계값은
        [전망] 대상이 아니므로 위반으로 처리하지 말 것.
   — ①②③ 중 하나라도 위반 시 pass=false. 위반 문장을 issues에 정확히 인용해 명시할 것.
   — "완화 가능"으로 처리하지 말고 반드시 수정 대상으로 표시할 것.
2. [수치 정확성] 수치·날짜·고유명사의 오류 가능성 및 기준 시점 누락 여부
3. [사실/해석 구분] [해석] 또는 [전망] 태그 없이 해석·전망이 사실처럼 서술된 문장 여부
4. [출처 단정] 출처 없는 단정 표현 여부 ("~할 것이다", "~가 확실하다" 등)
5. [투자 권유] 아래 표현 또는 이와 유사한 표현이 포함된 문장 여부:
   "매수", "유망", "주목해야 한다", "담아야 한다", "기회다", "추천",
   "매력적인 선택지", "관심 가져볼 만한", "주가 상승을 견인",
   "장기 성장 가능성을 갖춘", "긍정적으로 평가", "수혜가 기대",
   "저평가 매력", "매수 기회", "하방 경직성 제공",
   "수혜를 받을 수 있는", "실적 개선 효과를 기대할 수 있는"
   — 발견 시 pass=false. 해당 문장을 issues에 정확히 인용해 명시할 것.
   — "완화 가능"으로 처리하지 말고 반드시 수정 대상으로 표시할 것.

★ Phase 4.3 주제 집중도 기준 (6~10번: 심각하면 pass=false):
6. [단일 테마] 글이 핵심 테마 1개에 집중하는가 — 병렬적으로 2개 이상 테마가 독립 섹션으로 전개되면 실패
7. [테마 정렬] 제목·도입부·핵심 섹션 3개가 모두 같은 핵심 테마를 향하는가
8. [문단 반복] 같은 사실이나 메시지를 표현만 바꿔 2회 이상 반복한 문단이 있는가 (있으면 실패)
9. [완충 문장 과잉] "긍정적이다/영향을 줄 수 있다/수혜가 예상된다/중요한 요소다" 류 완충 문장이 구체 근거 없이 단독으로 2회 이상 쓰였는가 (있으면 실패)
10. [숫자 없는 문단 연속] 숫자 또는 기준 시점이 없는 문단이 2개 이상 연속으로 이어지는가 (있으면 실패)

★ 품질 기준 (11~19번: 경미하면 pass=true + issues 기재, 심각하면 pass=false):
11. [브랜드 톤] 바텐더/위스키 비유가 도입부 1회를 초과하는지 여부
12. [포맷] 마크다운 기호(#, ##, **, *, ```) 포함 여부
13. [문단 밀도] 핵심 섹션 문단당 사실+숫자+인과관계 4요소가 있는지
14. [숫자 연결] 숫자가 단순 삽입이 아닌 논리에 연결되어 의미가 설명되었는지
15. [종목 리포트형] 종목 섹션이 카드형 요약으로 축소되지 않았는지 (각 종목 4문장 이상, 4단계 순서 준수)
16. [메인/보조 픽 구분] 캐시의 픽에서 메인 픽과 보조 픽의 역할 차이가 명확한지
17. [반대 논리 특화] 반대 논리가 범용 문장이 아닌 이번 테마에 특화된 내용인지
18. [캐시 톤] 캐시 바텐더 톤이 과장되거나 부자연스럽지 않은지
19. [출처 대응] 본문에 인용된 내용과 참고 출처가 직접 대응하는지 (미인용 출처 포함 여부)

[출력 JSON — pass/issues만 출력, revised_content 없음]
{
  "pass": true 또는 false,
  "issues": ["[기준N] 발견된 구체적 문제 문장 또는 항목 — 모호한 평가 금지", ...]
}

pass=true이면 issues는 [] 또는 경미한 사항만.
pass=false이면 issues에 위반 기준 번호와 구체적 문장을 명시.
revised_content는 절대 출력하지 않는다 — 수정본은 별도 요청으로 처리한다.
"""

GEMINI_VERIFIER_USER = """
아래 초안을 검수하고 JSON으로 결과를 출력하라. revised_content는 출력하지 않는다.

[검수 대상 초안]
{draft}
"""

GEMINI_REVISER_SYSTEM = """
너는 매크로몰트(MacroMalt) 금융 콘텐츠 편집장이다.
너의 역할은 "축약 편집자"가 아니라 "보존형 편집장"이다.
지적된 문제만 최소한으로 수정하고, 나머지 내용은 원문 그대로 보존한다.
수정 후 결과물은 원문보다 짧아서는 안 된다.

[★ 분량 보존 원칙 — 최우선 준수]
- 수정 후 HTML 총 글자 수는 원문의 90% 이상이어야 한다.
- 문장을 삭제하지 말 것. 삭제 대신 표현만 교체하라.
  (예외: 동일 사실을 중복 서술한 문장 1개 삭제는 허용)
- 숫자, 출처, 인과관계 설명, 반대 포인트 — 이 4가지는 어떤 이유로도 삭제 금지.
- 종목 리포트(캐시의 픽) 섹션:
  · 메인 픽 섹션은 원문보다 짧아지지 않도록 할 것.
    원문이 400자 미만이면 4구조(왜지금/업황근거/반영변수/반대포인트)를 보완하여 400자 이상으로 확장.
  · 보조 픽 섹션은 원문보다 짧아지지 않도록 할 것.
    원문이 300자 미만이면 업황 근거 또는 반대 포인트를 추가하여 300자 이상으로 확장.

[수정 출력 규칙]
- JSON 래핑 절대 금지 — HTML만 출력
- 코드 블록(```html 등) 절대 금지 — HTML 태그로만 출력
- 마크다운 기호(#, **, ```) 절대 금지
- [해석] / [전망] 태그 누락된 해석·전망 문장에 태그 추가 (삭제 금지, 추가만)
- 출처 없는 단정 표현 → "~로 파악된다" / "~로 보인다" 표현으로 완화
- 투자 권유성 문장 → 중립 서술로 교체
- ★ <!-- PICKS: [...] --> 형태의 HTML 주석은 절대 삭제하지 말고 원본 그대로 마지막에 유지할 것

[수정 허용 범위 — 이 범위만 수정, 나머지 원문 유지]
1. [해석]/[전망] 태그 누락된 해석·전망 문장에 태그 추가
2. 출처 없는 단정 표현 → "~로 파악된다" / "~로 보인다" 표현으로 교체
3. ★ 미래 연도 숫자 시점 혼동 수정 — 다음 방식으로 처리:
   - "[전망] 2026년 X는 Y로 예상된다(출처 추정)" 형태로 재서술
   - 현재 사실과 미래 전망을 한 문장에 섞지 말고 분리 서술
   - 근거 없는 미래 전망은 삭제하고 확인된 현재 사실로 대체
   ❌ 수정 전: "삼성전자는 2026년 매출 300조를 기록했다"
   ✅ 수정 후: "[전망] 삼성전자의 2026년 매출은 300조 원으로 추정된다(미래에셋 리서치)"
4. ★ 투자 권유성 문장 수정 — 다음 방식으로 치환:
   - "매수", "유망", "주목해야 한다", "담아야 한다", "기회다", "추천", "매력적인 선택지",
     "저평가 매력", "매수 기회", "하방 경직성 제공",
     "수혜를 받을 수 있는", "실적 개선 효과를 기대할 수 있는"
     → 근거·조건·변수 중심의 분석형 문장으로 교체
   ❌ 수정 전: "SMH는 AI 인프라 투자 테마에 참여할 수 있는 매력적인 선택지다"
   ✅ 수정 후: "SMH는 AI 반도체 상위 종목을 분산 보유하는 구조로, 테마 노출도와 개별 종목 리스크를 함께 확인해야 한다"
5. 핵심 테마와 무관한 독립 h3 섹션 → h3 제거 후 앞 섹션 끝 배경 1문장으로 흡수
   (단, 해당 섹션의 핵심 숫자·논리는 그 1문장 안에 보존할 것)
6. 완충 문장이 구체 근거 없이 단독 등장 → 해당 문장 뒤에 근거 문장 1개 추가
   (삭제 금지 — 근거를 추가하는 방향으로 처리)
7. 동일 사실 중복 서술 → 중복 문장 1개 제거 (핵심 숫자 있는 문장을 남길 것)
8. [★ 위스키/바텐더 비유 추가 금지]
   도입부에 이미 있는 경우 새로운 비유를 보강 목적으로 삽입하지 말 것.
   위스키·바텐더·캐스크·싱글몰트 관련 표현은 "보존 대상"이지 "보강 대상"이 아님.
   수정 중 새로운 비유 문장을 추가하거나 기존 비유를 다른 위치에 재삽입하는 행위는 엄격히 금지.
9. [★ 날짜 생성·삽입 금지 — 절대 원칙]
   - 본문이나 source에 없는 절대 날짜(예: "2024년 5월 20일", "2024년 4월 15일")를 새로 생성해서 삽입하지 말 것.
   - 날짜가 불명확하면 임의 보강 금지.
   - 날짜를 확정할 수 없으면 절대 날짜를 제거하고 "현재", "최근", "이날", "당시", "해당 시점" 등 일반 시점 표현으로 바꿀 것.
   - 숫자/지수/KOSPI 수정 과정에서 날짜를 함께 발명하거나 치환하지 말 것.
   - 날짜는 source에 명시된 경우에만 유지 또는 정정할 것.
   ❌ 금지: "2024년 5월 20일 기준 KOSPI는 2,724.62pt를 기록하고 있습니다"
   ❌ 금지: "2024년 4월 15일 기준으로 전일 대비 0.48% 하락하며"
   ✅ 허용: "KOSPI는 전일 대비 하락 마감했습니다" / "당시 KOSPI는 하락 마감했습니다"
"""

GEMINI_REVISER_USER = """
아래 초안에서 다음 문제들을 수정하고, 수정된 HTML 전체를 출력하라.

[발견된 문제]
{issues}

[수정 대상 초안]
{draft}
"""


# ─── Post 2 전용: Gemini 종목 선정 프롬프트 ─────────────────────────────────

GEMINI_TICKER_V2_SYSTEM = """
너는 매크로몰트 포트폴리오 매니저다.
오늘의 매크로 분석 재료를 바탕으로 블로그 '캐시의 픽' 섹션에 소개할 종목을 선정해라.

[선정 기준]
- 오늘의 핵심 테마와 직접적으로 연결된 종목 2~3개
- 한국 주식과 미국 주식을 적절히 혼합 (가능하면 각 1개 이상)
- 분석 재료의 counter_interpretations(반대 해석)를 고려해 리스크가 극단적인 종목 제외
- 과도한 테마주·소형주 기피 (대형주 또는 ETF 우선)

[출력 규칙]
- 설명 없이 JSON 배열만 출력. 마크다운 코드 블록 금지.
- 한국 주식 티커 형식: '005930.KS' (KOSPI) 또는 '035720.KQ' (KOSDAQ)
- 미국 주식 티커 형식: 'AAPL', 'XLE' (거래소 접미사 없음)

[출력 JSON]
[
  {"ticker": "005930.KS", "name": "삼성전자", "market": "KR", "reason": "선정 이유 한 줄"},
  {"ticker": "XLE", "name": "Energy Select Sector SPDR", "market": "US", "reason": "선정 이유 한 줄"}
]
"""

GEMINI_TICKER_V2_USER = """
오늘의 핵심 테마와 분석 재료를 바탕으로 종목을 선정하라.

[오늘의 핵심 테마]
{theme}

[분석 재료 요약]
- 시장 영향 경로: {market_impact}
- 반대 해석: {counter_interpretations}
- 불확실 요소: {uncertainties}

[참고 리서치 데이터]
{research_text}
"""


# ──────────────────────────────────────────────────────────────────────────────
# SECTION F: Phase 7 — 3단계 파이프라인 내부 함수
# ──────────────────────────────────────────────────────────────────────────────

# 약한 관련성을 나타내는 키워드 (이 표현이 relevance_to_theme에 있으면 bg로 이동)
_WEAK_RELEVANCE_KEYWORDS = [
    "간접", "배경", "보조", "참고", "부수", "간접적", "배경 정보",
    "부차적", "부수적", "맥락", "일반적", "broad", "general",
]


def _filter_irrelevant_facts(materials: dict) -> dict:
    """
    Phase 4.3 — 코드 레벨 facts 필터링.

    Gemini가 출력한 facts 배열을 검사해:
      1) relevance_to_theme 필드가 없거나 비어있는 항목 → background_facts로 이동
      2) relevance_to_theme에 약한 관련성 키워드가 포함된 항목 → background_facts로 이동

    프롬프트 지시만으로 충족하지 못하는 경우를 코드에서 보정한다.
    이동 건수를 INFO 로그로 기록해 실제 동작 여부를 검증 가능하게 한다.
    """
    facts = materials.get("facts", [])
    bg_facts = list(materials.get("background_facts", []))

    kept: list = []
    moved: list = []

    for fact in facts:
        relevance = fact.get("relevance_to_theme", "").strip()
        if not relevance:
            moved.append(fact)
        elif any(kw in relevance for kw in _WEAK_RELEVANCE_KEYWORDS):
            moved.append({**fact, "tier": "extended"})
        else:
            kept.append(fact)

    if moved:
        logger.info(
            f"[facts 필터링] {len(moved)}개 항목을 background_facts로 이동 "
            f"(유지: {len(kept)}개) — 테마: '{materials.get('theme', '')[:40]}'"
        )
        for m in moved:
            logger.info(f"  → 이동: {m.get('content', '')[:60]}")

    materials["facts"] = kept
    materials["background_facts"] = bg_facts + moved
    return materials


def gemini_analyze(news_text: str, research_text: str, dart_text: str = "",
                   slot: str = "default", history_context: str = "") -> dict:
    """
    Step 1: Gemini 분석 엔진.
    뉴스·리서치 데이터를 구조화된 JSON 리포트 재료로 변환합니다.

    Args:
        dart_text:        format_dart_for_prompt() 결과물. 빈 문자열이면 프롬프트에 공백만 추가.
        slot:             발행 슬롯 ("morning"/"evening"/"us_open"/"default") — Phase 10
        history_context:  최근 발행 이력 텍스트 — Phase 10

    반환:
        {"theme", "facts", "market_impact", "counter_interpretations",
         "uncertainties", "writing_notes"}
    """
    # Phase 10: 슬롯 컨텍스트 + 이력 컨텍스트 append
    # Phase 12: 증거 밀도 규칙 append
    slot_ctx    = _SLOT_ANALYST_CONTEXTS.get(slot, _SLOT_ANALYST_CONTEXTS["default"])
    user_msg = GEMINI_ANALYST_USER.format(
        research_text=research_text,
        news_text=news_text,
        dart_text=dart_text,
    ) + slot_ctx + history_context + _P12_ANALYST_EVIDENCE_RULES + _P13_GEMINI_SPINE_HINT
    raw = _call_gemini(GEMINI_ANALYST_SYSTEM, user_msg, "Step1:분석재료생성", temperature=0.2)
    result = _parse_json_response(raw) if raw else None

    if not result or not isinstance(result, dict):
        logger.warning("Gemini 분석 재료 파싱 실패 — 기본값 사용")
        result = {
            "theme": "글로벌 경제 주요 이슈",
            "facts": [{"content": "수집된 뉴스 데이터 기반", "source": "뉴스 종합", "date": datetime.now().strftime("%Y-%m-%d"), "relevance_to_theme": "직접 관련"}],
            "market_impact": "금융 시장에 직접적인 영향",
            "counter_interpretations": [],
            "uncertainties": ["추가 데이터 확인 필요"],
            "writing_notes": "수치 인용 시 반드시 출처 명시",
        }

    # ── Phase 4.3: 코드 레벨 facts 필터링 (약한 관련성 항목 → background_facts) ──
    result = _filter_irrelevant_facts(result)

    logger.info(f"Step1 선정 테마: {result.get('theme', 'N/A')}")
    logger.info(f"Step1 사실 데이터(필터 후): {len(result.get('facts', []))}개 | bg: {len(result.get('background_facts', []))}개")
    return result


def gpt_write_analysis(materials: dict, context_text: str, slot: str = "default") -> str:
    """
    Step 2a: GPT 작성 엔진 — Post 1 심층 분석.
    Gemini 분석 재료를 HTML 형식의 심층 분석 글로 작성합니다.

    Args:
        slot: 발행 슬롯 — Phase 10 슬롯별 작성 방향 힌트 삽입

    반환: HTML 문자열 (마크다운 없음, 인라인 스타일 포함)
    """
    materials_json = json.dumps(materials, ensure_ascii=False, indent=2)
    # Phase 10: 슬롯별 작성 방향 힌트를 user 메시지 앞에 prepend
    # Phase 12: 증거 밀도 & 구조 규칙을 슬롯 힌트 앞에 prepend
    # Phase 13: 해석 지성 규칙을 P12 규칙 앞에 prepend
    # Phase 14: 생성 강제(few-shot+spine+hedge금지) + 소스 정규화를 P13 앞에 prepend
    slot_hint = _SLOT_POST1_WRITER_HINTS.get(slot, _SLOT_POST1_WRITER_HINTS["default"])

    # Phase 14 Track A: 소스 시점 정규화 블록
    run_date_str_now = datetime.now().strftime("%Y-%m-%d")
    source_norm_block = _normalize_source_for_generation(materials, run_date_str_now)

    user_msg = (
        _P14_POST1_ENFORCEMENT_BLOCK        # Phase 14: few-shot + spine + hedge 금지
        + source_norm_block                 # Phase 14 Track A: 소스 정규화
        + _P13_POST1_INTELLIGENCE_RULES     # Phase 13: 비자명성 + 헤징 + 반론 규격
        + _P12_POST1_EVIDENCE_RULES         # Phase 12: 증거 밀도 규칙
        + slot_hint                         # Phase 10: 슬롯 힌트
        + "\n"
        + GPT_WRITER_ANALYSIS_USER.format(
            materials_json=materials_json,
            context_text=context_text,
        )
    )
    draft = _call_gpt(
        GPT_WRITER_ANALYSIS_SYSTEM,
        user_msg,
        "Step2a:심층분석작성",
        temperature=0.7,
        max_tokens=5000,  # Phase 4.3: 4000 → 5000 (심층분석 밀도 복원)
    )
    return draft


def gpt_write_picks(materials: dict, tickers: list, prices: dict, context_text: str,
                    slot: str = "default", post1_spine: str = "") -> str:
    """
    Step 2b: GPT 작성 엔진 — Post 2 종목 리포트.
    분석 재료 + 종목 + 실제 가격 데이터로 종목 리포트 HTML을 작성합니다.

    Args:
        slot:        발행 슬롯 — Phase 10 슬롯별 Post2 방향 힌트 삽입
        post1_spine: Phase 14 Track B-4 — Post1 분석 뼈대/결론 (Post2 연속성 강제용)

    반환: HTML 문자열 ({PRICE_PLACEHOLDER} 포함, PICKS JSON 주석 포함)
    """
    theme = materials.get("theme", "")
    materials_summary = (
        f"시장 영향 경로: {materials.get('market_impact', '')}\n"
        f"핵심 불확실 요소: {'; '.join(materials.get('uncertainties', []))}\n"
        f"글 작성 주의사항: {materials.get('writing_notes', '')}"
    )

    # 종목별 가격 정보 텍스트
    tickers_lines = []
    for pick in tickers:
        t = pick.get("ticker", "")
        name = pick.get("name", t)
        market = pick.get("market", "")
        reason = pick.get("reason", "")
        price = prices.get(t, "{PRICE_PLACEHOLDER}")
        tickers_lines.append(
            f"- {name}({t}) [{market}] 현재가: {price}\n  선정 근거: {reason}"
        )
    tickers_and_prices = "\n".join(tickers_lines)

    # Phase 10: 슬롯별 Post2 방향 힌트를 user 메시지 앞에 prepend
    # Phase 12: 증거 밀도 & 구조 규칙을 슬롯 힌트 앞에 prepend
    # Phase 13: 해석 지성 + Post2 연속성 규칙을 P12 규칙 앞에 prepend
    # Phase 14: 연속성 강제(Post1 spine) + few-shot + hedge 금지를 P13 앞에 prepend
    slot_hint = _SLOT_POST2_WRITER_HINTS.get(slot, _SLOT_POST2_WRITER_HINTS["default"])

    # Phase 14 Track B-4: Post1 뼈대/결론 주입 (연속성 강제)
    continuation_block = ""
    if post1_spine:
        continuation_block = _P14_POST2_CONTINUATION_TEMPLATE.format(
            post1_spine=post1_spine
        )

    # Phase 14 Track A: 소스 정규화
    run_date_str_now = datetime.now().strftime("%Y-%m-%d")
    source_norm_block = _normalize_source_for_generation(materials, run_date_str_now)

    user_msg = (
        continuation_block                  # Phase 14: Post1 결론 + 연속성 강제
        + _P14_POST1_ENFORCEMENT_BLOCK      # Phase 14: few-shot + spine + hedge 금지
        + source_norm_block                 # Phase 14 Track A: 소스 정규화
        + _P13_POST2_INTELLIGENCE_RULES     # Phase 13: Post2 지성 규칙
        + _P12_POST2_EVIDENCE_RULES         # Phase 12: 증거 밀도 규칙
        + slot_hint                         # Phase 10: 슬롯 힌트
        + "\n"
        + GPT_WRITER_PICKS_USER.format(
            theme=theme,
            materials_summary=materials_summary,
            tickers_and_prices=tickers_and_prices,
            context_text=context_text,
        )
    )
    draft = _call_gpt(
        GPT_WRITER_PICKS_SYSTEM,
        user_msg,
        "Step2b:종목리포트작성",
        temperature=0.65,
        max_tokens=6000,  # Phase 4.3: 3000 → 6000 (종목 리포트 밀도 복원)
    )
    return draft


def verify_draft(draft: str) -> dict:
    """
    Step 3: Gemini 검수 엔진 (2단계 분리 방식).

    Step 3a — 검수: pass/issues만 담은 소형 JSON 반환 (HTML 미포함)
    Step 3b — 수정: pass=false일 때 별도 호출로 HTML만 직접 출력 (JSON 래핑 없음)

    반환:
        {"pass": bool, "issues": list, "revised_content": str | None}
    """
    # ── Step 3a: 검수 (pass + issues JSON만) ──────────────────────────────
    user_msg = GEMINI_VERIFIER_USER.format(draft=draft)
    raw = _call_gemini(
        GEMINI_VERIFIER_SYSTEM,
        user_msg,
        "Step3:팩트체크",
        temperature=0.1,
    )
    result = _parse_json_response(raw) if raw else None

    if not result or not isinstance(result, dict):
        logger.warning("검수 결과 파싱 실패 — 통과로 처리")
        return {"pass": True, "issues": [], "revised_content": None}

    passed = result.get("pass", True)
    issues = result.get("issues", [])
    revised = None  # Step 3b에서 별도 채움

    if passed:
        logger.info("Step3 검수 통과" + (f" | 경고 {len(issues)}건" if issues else ""))
        if issues:
            for iss in issues:
                logger.info(f"  ⚠ {iss}")
    else:
        logger.warning(f"Step3 검수 실패 ({len(issues)}건)")
        for iss in issues:
            logger.warning(f"  ✗ {iss}")

        # ── Step 3b: 수정 (HTML만 직접 출력, JSON 래핑 없음) ──────────────
        draft_len = len(draft)
        issues_text = "\n".join(f"- {iss}" for iss in issues)
        revise_msg  = GEMINI_REVISER_USER.format(issues=issues_text, draft=draft)
        revised_raw = _call_gemini(
            GEMINI_REVISER_SYSTEM,
            revise_msg,
            "Step3:수정",
            temperature=0.3,
        )
        if revised_raw and revised_raw.strip():
            revised = _strip_code_fences(revised_raw)  # Phase 4.3: 공통 헬퍼로 통일
            revised_len = len(revised)
            ratio = revised_len / draft_len * 100 if draft_len else 0
            # ── Phase 4.3 보존형 편집 검증 로그 ──────────────────────────
            logger.info(
                f"Step3 수정본 채택 | GPT초안 {draft_len}자 → Step3수정본 {revised_len}자 "
                f"({ratio:.1f}% 보존)"
            )
            if ratio < 90:
                logger.warning(
                    f"  ⚠ REVISER 과도 축소 감지: {draft_len - revised_len}자 감소 "
                    f"(90% 미만 보존) — 분량 손실 확인 필요"
                )
            # PICKS 주석 보존 여부 확인
            picks_in_draft   = "<!-- PICKS:" in draft
            picks_in_revised = "<!-- PICKS:" in revised
            if picks_in_draft and not picks_in_revised:
                logger.warning("  ⚠ PICKS 주석 소실: REVISER가 <!-- PICKS: --> 삭제함 — 원본 주석 복원 처리")
                # 원본에서 PICKS 주석을 추출해 수정본 끝에 재삽입
                picks_match = re.search(r"<!--\s*PICKS:.*?-->", draft, re.DOTALL)
                if picks_match:
                    revised = revised.rstrip() + "\n" + picks_match.group(0)
                    logger.info("  ✅ PICKS 주석 자동 복원 완료")
            elif picks_in_draft and picks_in_revised:
                logger.info("  ✅ PICKS 주석 보존 확인")
        else:
            logger.warning("Step3 수정 호출 실패 — 원본 유지")

    return {"pass": passed, "issues": issues, "revised_content": revised}


def gemini_select_tickers_v2(theme: str, materials: dict, research_text: str) -> list:
    """
    Post 2 전용: Gemini 종목 선정.
    분석 재료를 바탕으로 오늘의 픽 종목 2~3개를 선정합니다.

    반환:
        [{"ticker", "name", "market", "reason"}, ...]
    """
    user_msg = GEMINI_TICKER_V2_USER.format(
        theme=theme,
        market_impact=materials.get("market_impact", ""),
        counter_interpretations="; ".join(materials.get("counter_interpretations", [])),
        uncertainties="; ".join(materials.get("uncertainties", [])),
        research_text=research_text,
    )
    raw = _call_gemini(GEMINI_TICKER_V2_SYSTEM, user_msg, "Post2-Step1:종목선정", temperature=0.2)
    result = _parse_json_response(raw) if raw else None

    if not result or not isinstance(result, list):
        logger.warning("종목 선정 파싱 실패 — 기본 종목 사용")
        return [
            {"ticker": "SPY", "name": "S&P 500 ETF", "market": "US", "reason": "시장 대표 ETF"},
        ]

    logger.info(f"Post2 선정 종목: {[p['ticker'] for p in result]}")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# SECTION G: Phase 7 — 공개 API (main.py 연결)
# ──────────────────────────────────────────────────────────────────────────────

def generate_deep_analysis(news: list, research: list, slot: str = "default") -> dict:
    """
    Post 1 — 3단계 심층 경제 분석 생성.

    3단계 파이프라인:
        Step 1 (Gemini): 뉴스+리서치 → 구조화된 JSON 재료
        Step 2 (GPT):    JSON 재료 → HTML 심층 분석 초고
        Step 3 (Gemini): HTML 초고 → 팩트체크 + 필요 시 수정

    Args:
        slot: 발행 슬롯 ("morning"/"evening"/"us_open"/"default") — Phase 10

    반환:
        {"title", "content", "theme", "key_data", "materials", "generated_at"}
        ※ materials: Post 2에 전달하기 위한 구조화 데이터
    """
    _hk_session = _hankyung_login()
    enrich_research_with_pdf(research, session=_hk_session)
    news_text     = format_articles_for_prompt(news)
    research_text = format_research_for_prompt(research)
    context_text  = f"{research_text}\n\n{RESEARCH_NEWS_SEPARATOR}\n\n{news_text}"

    # ── Phase 10: 자료 최신성 분포 로그 ──────────────────────────────────
    _log_freshness_summary(news, research)

    # ── Step 1-DART: 전체 시장 주요사항보고서 스캔 (심층분석용, 14일) ──────
    dart_disclosures = run_dart_disclosure_scan(days=14)
    if dart_disclosures:
        dart_disclosures = enrich_dart_disclosures_with_fulltext(dart_disclosures, max_fetch=3)
    dart_text = format_dart_for_prompt(dart_disclosures) if dart_disclosures else ""
    if dart_text:
        logger.info(f"[DART] 심층분석 공시 데이터 {len(dart_disclosures)}건 → 프롬프트 주입")

    # ── Phase 10: 발행 이력 컨텍스트 생성 ────────────────────────────────
    history_ctx = _build_history_context(slot)
    logger.info(f"[Phase 10] 슬롯: {slot} | 이력 컨텍스트 길이: {len(history_ctx)}자")

    # ── Phase 12: 수치 하이라이트 블록 생성 + Gemini 입력에 주입 ───────────
    numeric_highlight = _build_numeric_highlight_block(news, research)
    if numeric_highlight:
        history_ctx = history_ctx + numeric_highlight  # 기존 이력 컨텍스트 뒤에 추가

    # ── Step 1: Gemini 분석 재료 생성 ─────────────────────────────────────
    materials = gemini_analyze(news_text, research_text, dart_text=dart_text,
                               slot=slot, history_context=history_ctx)
    theme = materials.get("theme", "글로벌 경제 주요 이슈")

    # ── Step 2: GPT 심층 분석 초고 작성 ───────────────────────────────────
    draft = gpt_write_analysis(materials, context_text, slot=slot)
    draft = _strip_code_fences(draft)  # Phase 4.3: 코드펜스/백틱 제거

    # ── Step 2.5: 후처리 밀도/반복 감지 (경고 로그만) ────────────────────
    _postprocess_density_check(draft, label="Post1")

    # ── Step 3: Gemini 팩트체크 + 수정 ────────────────────────────────────
    draft_len = len(draft)
    verify_result = verify_draft(draft)
    if not verify_result["pass"] and verify_result.get("revised_content"):
        logger.info("Step3 검수 실패 — 수정본 채택")
        final_content = verify_result["revised_content"]
    else:
        final_content = draft

    # ── Phase 5-A 후처리 ─────────────────────────────────────────────────
    final_content = _fix_double_typing(final_content)
    final_content = _format_source_section(final_content)

    # ── Phase 4.3: 보존율 요약 로그 ──────────────────────────────────────
    final_len = len(final_content)
    logger.info(
        f"Post1 분량 | GPT초안 {draft_len}자 → 최종 {final_len}자 "
        f"({final_len / draft_len * 100:.1f}% 보존)" if draft_len else "Post1 분량 | 초안 없음"
    )

    # ── Phase 12: 품질 스코어링 ────────────────────────────────────────────
    quality_scores = _score_post_quality(final_content, label="Post1")

    # ── Phase 13: 해석 품질 + 시간/수치 신뢰성 진단 ────────────────────────
    run_date_str = datetime.now().strftime("%Y-%m-%d")
    p13_interp   = _score_interpretation_quality(final_content, label="Post1")
    p13_temporal = _check_temporal_sanity(final_content, run_date_str)
    p13_numeric  = _check_numeric_sanity(final_content)
    p13_closure  = _check_verifier_closure(
        verify_result.get("issues", []), draft, final_content
    )

    # ── Phase 14 Track C (Hotfix): 약한 해석 FAIL 시 타겟 블록 교체 ────────
    weak_hits = p13_interp.get("weak_interp_hits", 0)
    # spine은 이 시점에 아직 추출 전이므로 SPINE 주석에서 직접 추출
    _pre_spine = _extract_post1_spine(final_content)
    final_content = _enforce_interpretation_rewrite(
        final_content, weak_hits, label="Post1", article_spine=_pre_spine
    )
    # 재작성 후 품질 재진단 (타겟 교체 내부에서도 re-score하지만 최종 p13_interp 갱신)
    if weak_hits >= 3:
        p13_interp = _score_interpretation_quality(final_content, label="Post1-재작성후")

    p13_scores: dict = {
        "interpretation": p13_interp,
        "temporal":       p13_temporal,
        "numeric":        p13_numeric,
        "closure":        p13_closure,
    }

    # ── Phase 14 Track B-4: Post1 분석 뼈대 추출 (Post2 연속성 강제용) ───
    post1_spine = _extract_post1_spine(final_content)
    if post1_spine:
        logger.info(f"[Phase 14] Post1 뼈대 추출: {post1_spine[:80]}…")
    else:
        logger.info("[Phase 14] Post1 뼈대 미탐지 — Post2 연속성 규칙만 적용")

    # 제목 구성 (h1 태그에서 추출, 없으면 직접 생성)
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", final_content, re.DOTALL)
    if h1_match:
        title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip()
    else:
        title = f"[심층분석] {theme}"

    # key_data: facts의 content 목록 (Post 2 전달용)
    key_data = [f.get("content", "") for f in materials.get("facts", [])[:5]]

    logger.info(f"Post1 생성 완료 | 제목: '{title}' | HTML {len(final_content)}자")

    return {
        "title":          title,
        "content":        final_content,
        "theme":          theme,
        "key_data":       key_data,
        "materials":      materials,      # Post 2에 재사용
        "post1_spine":    post1_spine,    # Phase 14: Post2 연속성 강제용
        "quality_scores": quality_scores, # Phase 12: 품질 진단 결과
        "p13_scores":     p13_scores,     # Phase 13/14: 해석 지성 + 신뢰성 진단
        "generated_at":   datetime.now().isoformat(),
    }


def generate_stock_picks_report(
    theme: str,
    key_data: list,
    post1_content: str,
    news: list,
    research: list,
    materials: Optional[dict] = None,
    slot: str = "default",
) -> dict:
    """
    Post 2 — 3단계 종목 리포트 생성.

    Post 1의 materials를 재사용하면 Gemini 분석 Step을 건너뜁니다.

    3단계 파이프라인:
        Step 1 (Gemini): materials가 없으면 재분석, 있으면 재사용
        Step 1B (Gemini): 종목 2~3개 선정
        Step 1C (가격 조회): 실시간 종가 조회
        Step 2 (GPT):    종목 + 가격 + 재료 → HTML 종목 리포트
        Step 3 (Gemini): HTML → 팩트체크 + 필요 시 수정

    Args:
        slot: 발행 슬롯 ("morning"/"evening"/"us_open"/"default") — Phase 10

    반환:
        {"title", "content", "picks", "prices", "generated_at"}
    """
    _hk_session = _hankyung_login()
    enrich_research_with_pdf(research, session=_hk_session)
    news_text     = format_articles_for_prompt(news)
    research_text = format_research_for_prompt(research)
    context_text  = f"{research_text}\n\n{RESEARCH_NEWS_SEPARATOR}\n\n{news_text}"

    # ── Step 1: 분석 재료 (재사용 or 재생성) ──────────────────────────────
    if materials is None:
        logger.info("Post2 — materials 없음, Gemini 재분석 실행")
        materials = gemini_analyze(news_text, research_text, slot=slot)
        theme = materials.get("theme", theme)
    else:
        logger.info("Post2 — Post1 materials 재사용")

    # ── Step 1B: Gemini 종목 선정 ──────────────────────────────────────────
    picks = gemini_select_tickers_v2(theme, materials, research_text)

    # ── Step 1C: 실시간 종가 조회 ─────────────────────────────────────────
    prices = {}
    for pick in picks:
        ticker = pick.get("ticker", "")
        if ticker:
            prices[ticker] = _get_price_for_ticker(ticker)
    logger.info(f"Post2 종가 조회 완료: {prices}")

    # ── Step 1D: DART 재무 수치 + 기업정보 조회 (픽 확정 KR 종목만, 좁게) ──
    # 미국 티커(알파벳)는 제외하고 6자리 숫자 종목코드(KR)만 전달
    kr_stock_codes = [
        p["ticker"].split(".")[0]
        for p in picks
        if p.get("ticker", "").split(".")[0].isdigit()
    ]
    dart_financials   = run_dart_financials(kr_stock_codes)   if kr_stock_codes else {}
    dart_company_info = run_dart_company_info(kr_stock_codes) if kr_stock_codes else {}
    picks_dart_text   = format_dart_for_prompt(
        disclosures=[],        # 픽용은 공시 이벤트 불필요 (심층분석에서 이미 처리)
        financials=dart_financials,
        company_info=dart_company_info,
    )
    if picks_dart_text:
        logger.info(f"[DART] 픽 재무 데이터 주입: {list(dart_financials.keys())}")
        context_text = context_text + "\n\n" + picks_dart_text

    # ── Step 1D-2: 사업보고서 핵심 섹션 주입 (Phase 6-B) ──────────────────
    if kr_stock_codes:
        annual_sections = run_dart_annual_report_sections(kr_stock_codes)
        if annual_sections:
            lines = ["\n[DART 사업보고서 핵심 섹션]"]
            for sc, secs in annual_sections.items():
                for header, text in secs.items():
                    lines.append(f"[{sc} — {header}]\n{text}")
            context_text = context_text + "\n\n" + "\n\n".join(lines)
            logger.info(f"[DART/annual] 사업보고서 섹션 주입: {list(annual_sections.keys())}")

    # ── Phase 14 Track B-4: Post1 뼈대 추출 (연속성 강제용) ───────────────
    post1_spine = _extract_post1_spine(post1_content)
    if post1_spine:
        logger.info(f"[Phase 14] Post2용 Post1 뼈대: {post1_spine[:80]}…")

    # ── Step 2: GPT 종목 리포트 작성 ──────────────────────────────────────
    draft = gpt_write_picks(materials, picks, prices, context_text, slot=slot,
                            post1_spine=post1_spine)  # Phase 14: 뼈대 주입
    draft = _strip_code_fences(draft)  # Phase 4.3: 코드펜스/백틱 제거

    # ── Step 2.5: 후처리 밀도/반복 감지 (경고 로그만) ────────────────────
    _postprocess_density_check(draft, label="Post2")

    # ── Step 3: Gemini 팩트체크 + 수정 ────────────────────────────────────
    post2_draft_len = len(draft)
    verify_result = verify_draft(draft)
    if not verify_result["pass"] and verify_result.get("revised_content"):
        logger.info("Post2 Step3 검수 실패 — 수정본 채택")
        raw_content = verify_result["revised_content"]
    else:
        raw_content = draft

    # ── Phase 4.3: 종목 섹션별 글자수 보고 ───────────────────────────────
    post2_final_len = len(raw_content)
    logger.info(
        f"Post2 분량 | GPT초안 {post2_draft_len}자 → Step3 후 {post2_final_len}자 "
        f"({post2_final_len / post2_draft_len * 100:.1f}% 보존)" if post2_draft_len else ""
    )
    # 종목 div 섹션별 글자수 측정 (보존형 편집 검증용)
    _log_picks_section_lengths(raw_content, picks)

    # PICKS JSON 파싱 + 가격 플레이스홀더 교체
    parsed_picks = parse_picks_from_content(raw_content)
    if not parsed_picks:
        parsed_picks = picks  # GPT 주석 누락 시 Gemini 선정 목록 사용
    final_content = assemble_final_content(raw_content, parsed_picks, prices)

    # 제목 구성
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", final_content, re.DOTALL)
    if h1_match:
        title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip()
    else:
        names = "·".join([p.get("name", p.get("ticker", "")) for p in parsed_picks[:2]])
        title = f"[캐시의 픽] {names} — {theme}"

    save_portfolio(parsed_picks, prices)

    # P10 검증용: assemble 이전 raw_content 기준으로 PICKS 주석 존재 여부 기록
    picks_comment_in_raw = bool(re.search(r"<!--\s*PICKS:", raw_content))

    # ── Phase 12: 품질 스코어링 ────────────────────────────────────────────
    quality_scores = _score_post_quality(final_content, label="Post2")

    # ── Phase 13: 해석 품질 + 시간/수치 신뢰성 + Post2 연속성 진단 ─────────
    _run_date_str  = datetime.now().strftime("%Y-%m-%d")
    p13_interp     = _score_interpretation_quality(final_content, label="Post2")
    p13_temporal   = _check_temporal_sanity(final_content, _run_date_str)
    p13_numeric    = _check_numeric_sanity(final_content)
    p13_closure    = _check_verifier_closure(
        verify_result.get("issues", []), draft, raw_content
    )
    p13_continuity = _check_post_continuity(post1_content, final_content)

    # ── Phase 14 Track C (Hotfix): 약한 해석 FAIL 시 타겟 블록 교체 ────────
    p2_weak_hits = p13_interp.get("weak_interp_hits", 0)
    final_content = _enforce_interpretation_rewrite(
        final_content, p2_weak_hits, label="Post2",
        article_spine=post1_spine,  # Post2는 Post1 뼈대를 spine으로 전달
    )
    if p2_weak_hits >= 3:
        p13_interp = _score_interpretation_quality(final_content, label="Post2-재작성후")

    p13_scores: dict = {
        "interpretation": p13_interp,
        "temporal":       p13_temporal,
        "numeric":        p13_numeric,
        "closure":        p13_closure,
        "continuity":     p13_continuity,
    }

    logger.info(f"Post2 생성 완료 | 제목: '{title}' | HTML {len(final_content)}자")

    return {
        "title":                title,
        "content":              final_content,
        "picks":                parsed_picks,
        "prices":               prices,
        "picks_comment_in_raw": picks_comment_in_raw,  # P10 검증용
        "quality_scores":       quality_scores,         # Phase 12: 품질 진단 결과
        "p13_scores":           p13_scores,             # Phase 13: 해석 지성 + 신뢰성 진단
        "generated_at":         datetime.now().isoformat(),
    }


def _log_picks_section_lengths(content: str, picks: list) -> None:
    """
    Phase 4.3 보존형 편집 검증:
    캐시의 픽 종목 div 섹션별 텍스트 글자수를 로그로 출력한다.
    메인픽 400자(600자 목표) / 보조픽 300자 미달 시 경고.
    """
    from bs4 import BeautifulSoup as _BS
    soup = _BS(content, "html.parser")
    divs = soup.find_all("div")

    pick_names = [p.get("name", p.get("ticker", f"종목{i+1}")) for i, p in enumerate(picks)]
    is_main = True  # 첫 번째 div를 메인픽으로 간주

    found = 0
    for div in divs:
        text = div.get_text(strip=True)
        if len(text) < 50:
            continue  # 짧은 wrapper div 무시
        found += 1
        label_tag = "메인픽" if found == 1 else f"보조픽{found - 1}"
        threshold = 400 if found == 1 else 300
        goal = 600 if found == 1 else 400
        status = "✅" if len(text) >= threshold else "❌"
        logger.info(
            f"  [{label_tag}] 텍스트 {len(text)}자 {status} "
            f"(기준 {threshold}자 / 목표 {goal}자)"
        )
        if len(text) < threshold:
            logger.warning(
                f"  ⚠ [{label_tag}] 분량 미달 {threshold - len(text)}자 부족 "
                f"— REVISER 보강 미작동 가능성"
            )
        if found >= len(picks) + 1:
            break


# ──────────────────────────────────────────────────────────────────────────────
# SECTION H: 자동 검증 테스트 (python generator.py 직접 실행)
# ──────────────────────────────────────────────────────────────────────────────

def _postprocess_density_check(content: str, label: str = "") -> None:
    """
    Phase 4.3 후처리 밀도/반복 감지 (경고 로그만 출력, 수정 없음).
    generate_deep_analysis / generate_stock_picks_report 에서 검수 전에 호출한다.
    """
    prefix = f"[{label}] " if label else ""

    soup = BeautifulSoup(content, "html.parser")

    # ── 1. 숫자 없는 문단 연속 탐지 (반대시각/체크포인트 섹션 제외) ─────────
    # 질적 서술이 정상인 섹션은 연속 무숫자 카운터에서 제외
    EXEMPT_H3_KEYWORDS = ["반대 시각", "체크포인트", "반대포인트", "리스크 요인", "불확실"]
    number_pattern = re.compile(r"\d[\d,]*\.?\d*[%억만달러원배럴위안엔]?")
    consecutive_no_num = 0
    max_consecutive_no_num = 0
    current_h3_text = ""
    for tag in soup.find_all(["h3", "p"]):
        if tag.name == "h3":
            current_h3_text = tag.get_text(strip=True)
            consecutive_no_num = 0  # 섹션 경계에서 카운터 리셋
        elif tag.name == "p":
            para = tag.get_text(strip=True)
            if len(para) <= 30:
                continue
            # 반대시각/체크포인트 섹션은 연속 카운터 제외
            if any(kw in current_h3_text for kw in EXEMPT_H3_KEYWORDS):
                continue
            if number_pattern.search(para):
                consecutive_no_num = 0
            else:
                consecutive_no_num += 1
                max_consecutive_no_num = max(max_consecutive_no_num, consecutive_no_num)
    if max_consecutive_no_num >= 2:
        logger.warning(f"{prefix}밀도 경고: 숫자/시점 없는 문단이 {max_consecutive_no_num}개 연속 감지 (반대시각/체크포인트 섹션 제외)")

    # 완충 문장 탐지용 전체 문단 목록 (기존 방식 유지)
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30]

    # ── 2. 완충 문장 과잉 탐지 ────────────────────────────────────────────
    buffer_phrases = [
        "긍정적이다", "영향을 줄 수 있다", "수혜가 예상된다", "중요한 요소다",
        "주목할 필요가 있다", "긍정적으로 작용", "기대된다", "주목받고 있다",
        "영향을 미칠 것으로", "중요한 변수", "기대감이 높아", "관심이 집중",
    ]
    buffer_count = 0
    for phrase in buffer_phrases:
        buffer_count += content.count(phrase)
    if buffer_count >= 4:
        logger.warning(f"{prefix}밀도 경고: 완충 문장 과잉 ({buffer_count}회 감지) — 구체 근거 없는 일반론 축소 필요")

    # ── 3. 반복 문단 탐지 (유사 도입부 2회 이상) ─────────────────────────
    # 핵심 동의어 집합을 이용해 문단 간 의미 중복 간이 측정
    repeat_keywords = re.compile(
        r"(글로벌 지정학|에너지 가격|IT 섹터|실적 상향|관세|금리 인하|반도체|수출 기업)"
    )
    intro_hits: dict[str, int] = {}
    for para in paragraphs[:4]:  # 도입부 4개 문단만 체크
        for m in repeat_keywords.finditer(para):
            key = m.group(1)
            intro_hits[key] = intro_hits.get(key, 0) + 1
    repeated = [k for k, v in intro_hits.items() if v >= 2]
    if repeated:
        logger.warning(f"{prefix}반복 경고: 도입부에서 '{repeated[0]}' 등 키워드가 반복됨 — 중복 서술 점검 필요")

    # ── 4. 주제 분산 감지 (h3 소제목이 서로 다른 테마를 가리키는지 간이 체크) ─
    h3_texts = [h.get_text(strip=True) for h in soup.find_all("h3")]
    theme_keywords = {
        "지정학": ["지정학", "전쟁", "러시아", "중동", "우크라이나"],
        "유가": ["유가", "원유", "WTI", "브렌트", "에너지"],
        "금리": ["금리", "연준", "Fed", "CPI", "인플레"],
        "무역": ["관세", "무역", "수출", "무역법"],
        "IT반도체": ["IT", "반도체", "DRAM", "MLCC", "서버", "AI"],
    }
    active_themes = set()
    for h3 in h3_texts:
        for theme_name, keywords in theme_keywords.items():
            if any(kw in h3 for kw in keywords):
                active_themes.add(theme_name)
    if len(active_themes) >= 3:
        logger.warning(
            f"{prefix}주제 분산 경고: 소제목에서 {len(active_themes)}개 테마 감지 "
            f"({', '.join(active_themes)}) — 단일 테마 집중 필요"
        )
    else:
        logger.info(f"{prefix}밀도/반복 점검 완료 | 완충 문장 {buffer_count}회 | 연속 무숫자 문단 최대 {max_consecutive_no_num}개")


def _count_whisky_metaphors(content: str) -> int:
    """위스키·바텐더 비유 횟수 카운트 (도입부 제외 여부는 위치로 판단)."""
    patterns = [r"위스키", r"바텐더", r"캐스크", r"싱글몰트", r"distill", r"dram", r"cocktail"]
    count = 0
    for pat in patterns:
        count += len(re.findall(pat, content, re.IGNORECASE))
    return count


def _verify_no_unsourced_price(content: str) -> bool:
    """
    출처 없는 가격 표현 탐지.
    '$숫자' 또는 '₩숫자' 패턴이 있을 때, 기준일(기준) 또는 출처 언급 없이 단독으로 나오는 경우를 탐지.
    {PRICE_PLACEHOLDER} 및 이미 교체된 가격(기준 포함)은 허용.
    """
    # 가격 단독 출현 패턴: $숫자 또는 ₩숫자가 '기준'이라는 단어 없이 단독 출현
    price_pattern = re.compile(r"([$₩]\d[\d,]*\.?\d*)")
    matches = price_pattern.findall(content)
    if not matches:
        return True  # 가격 없음 → 통과

    # 가격 패턴 주변에 '기준' 또는 출처 관련 단어가 있는지 확인
    suspicious_count = 0
    for match in re.finditer(r"([$₩]\d[\d,]*\.?\d*)", content):
        # 주변 80자 내에 '기준' 또는 출처 단어가 있는지 체크
        start = max(0, match.start() - 80)
        end   = min(len(content), match.end() + 80)
        context = content[start:end]
        if "기준" not in context and "출처" not in context and "기준일" not in context:
            suspicious_count += 1

    return suspicious_count == 0


if __name__ == "__main__":
    import sys

    # 로깅 설정 (테스트용)
    # scraper.py 모듈 레벨 basicConfig(INFO)가 먼저 실행되어 root handler가 등록된 상태.
    # basicConfig는 무효 → named logger 레벨을 직접 조정.
    if os.getenv("DEBUG_LLM"):
        logging.getLogger("macromalt").setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)  # root handler 레벨도 낮춤

    print("\n" + "=" * 70)
    print("macromalt Phase 4.3 (v3) 파이프라인 자동 검증 테스트")
    print("=" * 70)

    # ── 샘플 데이터 (Phase 4.3 재검증용 — Post1·Post2 모두 테스트) ──────────
    _today = datetime.now().strftime("%Y-%m-%d")

    sample_news = [
        {
            "source": "한국경제",
            "title": "삼성전자, 1분기 메모리 반도체 수요 '완판'...HBM 공급 확대",
            "summary": "삼성전자가 2026년 1분기 DRAM·NAND 제품 수량을 내년치까지 선주문 완판. HBM3E 공급 비율이 전 분기 대비 30%p 확대됐다고 밝혔다.",
            "url": "https://www.hankyung.com/article/sample1",
            "date_tier": "recent",
            "published": _today,
        },
        {
            "source": "로이터",
            "title": "NVIDIA Q4 Data Center Revenue Hits $35.6B, Up 93% YoY",
            "summary": "NVIDIA reported record Q4 FY2026 data center revenue of $35.6 billion, a 93% year-over-year increase driven by Blackwell GPU demand from hyperscalers.",
            "url": "https://www.reuters.com/technology/nvidia-sample2",
            "date_tier": "recent",
            "published": _today,
        },
        {
            "source": "매일경제",
            "title": "SK하이닉스, HBM4 양산 준비 완료...NVIDIA 공급 비중 60% 목표",
            "summary": "SK하이닉스가 HBM4 양산을 2026년 2분기 시작한다고 확인. NVIDIA향 HBM 공급 비중을 60%까지 확대해 2026년 HBM 매출 10조원 달성 목표.",
            "url": "https://www.mk.co.kr/news/sample3",
            "date_tier": "recent",
            "published": _today,
        },
        {
            "source": "블룸버그",
            "title": "AI Capex Boom: Microsoft, Google, Meta Plan $300B Investment in 2026",
            "summary": "Microsoft, Google, Meta collectively plan to invest over $300 billion in AI infrastructure in 2026, up 60% from 2025, driving continued semiconductor demand.",
            "url": "https://www.bloomberg.com/news/sample4",
            "date_tier": "recent",
            "published": _today,
        },
        {
            "source": "전자신문",
            "title": "삼성전기, 서버용 MLCC 2026년 1분기 수주 전년비 45% 증가",
            "summary": "삼성전기 서버향 MLCC 수주 잔고가 2026년 1분기 기준 전년 동기 대비 45% 증가. AI 서버 확산에 따른 수요 급증이 주요 원인으로 분석.",
            "url": "https://www.etnews.com/sample5",
            "date_tier": "recent",
            "published": _today,
        },
        {
            "source": "조선비즈",
            "title": "반도체 수출, 2026년 2월 전년비 62% 급증...역대 최대",
            "summary": "산업통상자원부에 따르면 2026년 2월 반도체 수출액이 전년 동월 대비 62% 증가한 148억 달러로 집계. AI 서버 수요가 주도.",
            "url": "https://biz.chosun.com/sample6",
            "date_tier": "recent",
            "published": _today,
        },
    ]

    sample_research = [
        {
            "source": "네이버금융 리서치",
            "title": "삼성전자(005930) — AI 인프라 수혜 핵심주, 목표주가 12만원 상향",
            "summary": "AI 데이터센터 수요 급증으로 HBM3E 완판. 2026년 반도체 부문 영업이익 35조원 전망. 목표주가 12만원(기존 10만원) 상향. 투자의견 매수 유지.",
            "broker": "NH투자증권",
            "sector": "반도체",
            "target_price": "120,000원",
            "weight": 8,
            "date_tier": "recent",
            "published": _today,
        },
        {
            "source": "한국투자증권 리서치",
            "title": "SK하이닉스(000660) — HBM4 독점 공급, PER 8배 저평가",
            "summary": "2026년 HBM 매출 10조원 달성 시 영업이익 20조원 돌파 예상. 현재 PER 8배로 글로벌 메모리 피어 대비 30% 할인. 목표주가 30만원(현재 19만원) 제시.",
            "broker": "한국투자증권",
            "sector": "반도체",
            "target_price": "300,000원",
            "weight": 7,
            "date_tier": "recent",
            "published": _today,
        },
        {
            "source": "삼성증권 리서치",
            "title": "삼성전기(009150) — 서버 MLCC 수혜, 2026년 영업이익 1.2조원 전망",
            "summary": "서버향 MLCC 수주 증가로 2026년 영업이익 1.2조원 전망(전년비 40% 증가). AI 서버당 MLCC 탑재량이 일반 서버 대비 3~5배 수준. 목표주가 55만원.",
            "broker": "삼성증권",
            "sector": "전자부품",
            "target_price": "550,000원",
            "weight": 6,
            "date_tier": "recent",
            "published": _today,
        },
        {
            "source": "미래에셋증권 리서치",
            "title": "AI 반도체 섹터 — NVIDIA·삼성·SK 3강 구도, 2026년 시장 규모 $800B 전망",
            "summary": "글로벌 AI 반도체 시장이 2026년 8,000억 달러 규모로 성장 전망. NVIDIA GPU + HBM 메모리 + MLCC 부품 공급망 전반 수혜. 한국 반도체 수출 비중 확대 예상.",
            "broker": "미래에셋증권",
            "sector": "반도체",
            "weight": 5,
            "date_tier": "recent",
            "published": _today,
        },
    ]

    print("\n[Step 1] Post 1 생성 시작...")
    try:
        post1 = generate_deep_analysis(sample_news, sample_research)
        content = post1["content"]
        materials = post1.get("materials", {})

        print(f"\n제목: {post1['title']}")
        print(f"테마: {post1['theme']}")
        print(f"HTML 길이: {len(content)}자")
        print(f"facts 수: {len(materials.get('facts', []))}개")
        print("\n--- 본문 앞 500자 ---")
        print(content[:500])
        print("...")

        # ── Phase 4.3 자동 검증 ──────────────────────────────────────────
        print("\n" + "=" * 70)
        print("Phase 4.3 검증 기준 체크 (14개)")
        print("=" * 70)

        # 공통 파싱
        h3_count    = len(re.findall(r"<h3[^>]*>", content))
        h3_texts    = re.findall(r"<h3[^>]*>(.*?)</h3>", content, re.DOTALL)
        para_texts  = re.findall(r"<p[^>]*>(.*?)</p>", content, re.DOTALL)
        number_pat  = re.compile(r"\d[\d,]*\.?\d*[%억만달러원배럴위안엔]?")
        buffer_pat  = re.compile(
            r"(긍정적이다|영향을 줄 수 있다|수혜가 예상된다|중요한 요소다|기대된다|주목받고 있다)"
        )

        # 숫자 없는 문단 연속 최대치 — 반대시각/체크포인트 섹션 제외
        _EXEMPT_SECTIONS = ["반대 시각", "체크포인트", "반대포인트", "리스크 요인", "불확실"]
        _soup_test = BeautifulSoup(content, "html.parser")
        max_consec_no_num = 0
        cur = 0
        _cur_h3 = ""
        for _tag in _soup_test.find_all(["h3", "p"]):
            if _tag.name == "h3":
                _cur_h3 = _tag.get_text(strip=True)
                cur = 0
            elif _tag.name == "p":
                _txt = _tag.get_text(strip=True)
                if len(_txt) <= 30:
                    continue
                if any(kw in _cur_h3 for kw in _EXEMPT_SECTIONS):
                    continue  # 반대시각·체크포인트 섹션 제외
                if number_pat.search(_txt):
                    cur = 0
                else:
                    cur += 1
                    max_consec_no_num = max(max_consec_no_num, cur)

        # 완충 문장 총 횟수
        buffer_count = sum(len(buffer_pat.findall(re.sub(r"<[^>]+>", "", p))) for p in para_texts)

        # h3 텍스트 다중 테마 분산 체크
        theme_kw_map = {
            "지정학": ["지정학", "전쟁", "러시아", "중동"],
            "유가": ["유가", "원유", "WTI"],
            "금리": ["금리", "연준", "Fed"],
            "무역": ["관세", "무역법"],
        }
        active_themes_in_h3 = set()
        for h3 in h3_texts:
            clean_h3 = re.sub(r"<[^>]+>", "", h3)
            for tname, kws in theme_kw_map.items():
                if any(kw in clean_h3 for kw in kws):
                    active_themes_in_h3.add(tname)

        criteria = {
            # ── v3 기존 기준 ────────────────────────────────────────────
            " 1. Gemini 결과가 구조화 JSON으로 출력됐는가?":
                isinstance(materials, dict) and "theme" in materials and "facts" in materials,

            " 2. background_facts 배열이 JSON에 포함됐는가?":
                isinstance(materials, dict) and "background_facts" in materials,

            " 3. theme_sub_axes(하위 축 3개)가 JSON에 포함됐는가?":
                isinstance(materials, dict) and len(materials.get("theme_sub_axes", [])) >= 3,

            " 4. 최종 결과물이 마크다운 없이 HTML만 사용했는가?":
                not bool(re.search(r"(?m)^#{1,6} |(?<!\[)\*\*(?!\])", content)),

            " 5. 출처 없는 가격·목표가가 임의 생성되지 않았는가?":
                _verify_no_unsourced_price(content),

            " 6. [해석]·[전망]·'확실하지 않다' 규칙이 적용됐는가?":
                "[해석]" in content or "[전망]" in content or "확실하지 않" in content,

            " 7. 참고 출처 섹션이 본문 데이터와 대응하는가?":
                bool(re.search(r"참고\s*출처|Reference", content, re.IGNORECASE)),

            " 8. 위스키·바텐더 비유가 1회를 넘지 않았는가?":
                _count_whisky_metaphors(content) <= 2,

            " 9. 글 구조가 h3 소제목 3개 이상 포함됐는가?":
                h3_count >= 3,

            # ── Phase 4.3 신규 기준 ────────────────────────────────────
            "10. [단일 테마] h3 소제목에서 테마 분산이 2개 미만인가?":
                len(active_themes_in_h3) < 2,

            "11. [문단 밀도] 숫자 없는 문단이 연속 2개 미만인가? (반대시각·체크포인트 섹션 제외)":
                max_consec_no_num < 2,

            "12. [완충 문장] 완충·일반론 문장이 4회 미만인가?":
                buffer_count < 4,

            "13. [facts 밀도] Gemini facts에 relevance_to_theme 필드가 있는가?":
                isinstance(materials, dict) and
                bool(materials.get("facts")) and
                "relevance_to_theme" in (materials.get("facts", [{}])[0] if materials.get("facts") else {}),

            "14. [aux_context] auxiliary_context 필드가 JSON에 있는가?":
                isinstance(materials, dict) and "auxiliary_context" in materials,
        }

        all_pass = True
        for criterion, passed in criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | {criterion}")
            if not passed:
                all_pass = False

        print(f"\n  📊 완충 문장 {buffer_count}회 | 연속 무숫자 문단 최대 {max_consec_no_num}개 | h3 테마 분산 {len(active_themes_in_h3)}개")
        print("\n" + "=" * 70)
        if all_pass:
            print("🎉 전체 검증 통과 — Phase 4.3 파이프라인 정상 동작")
        else:
            print("⚠️  일부 기준 미통과 — 로그를 확인하고 프롬프트를 조정하세요.")
        print("=" * 70 + "\n")

    except Exception as e:
        logger.exception(f"Post1 테스트 실패: {e}")
        sys.exit(1)

    # ══════════════════════════════════════════════════════════════════════
    print("\n[Step 2] Post 2 생성 시작 (캐시의 픽 종목 리포트)...")
    try:
        post2 = generate_stock_picks_report(
            theme=post1["theme"],
            key_data=post1["key_data"],
            post1_content=post1["content"],
            news=sample_news,
            research=sample_research,
            materials=post1["materials"],
        )
        c2 = post2["content"]

        print(f"\n제목: {post2['title']}")
        print(f"HTML 길이: {len(c2)}자")
        print(f"선정 종목: {[p['ticker'] for p in post2['picks']]}")
        print("\n--- Post2 본문 앞 600자 ---")
        print(c2[:600])
        print("...")
        print("\n--- Post2 본문 뒤 400자 ---")
        print(c2[-400:])
        print("...")

        # ── Post2 자동 검증 ──────────────────────────────────────────────
        print("\n" + "=" * 70)
        print("Post2 검증 기준 체크 (Phase 4.3 Final)")
        print("=" * 70)

        # 공통 파싱
        p2_picks_divs = re.findall(r"<div[^>]*>(.*?)</div>", c2, re.DOTALL)
        p2_paras = re.findall(r"<p[^>]*>(.*?)</p>", c2, re.DOTALL)
        number_pat2 = re.compile(r"\d[\d,.]+[%억만원달러조]?")
        has_logic_number = re.compile(
            r"\d[\d,.]+[%억만원달러조]?.{0,80}(때문|원인|이유|따라|결과|수혜|직접|연결|주도|공급|수요|이익|매출|실적)",
            re.DOTALL,
        )

        # P1. 코드펜스·따옴표·래퍼 없이 순수 HTML 시작 여부
        p2_clean_start = c2.strip().startswith("<")
        p2_no_backtick = "```" not in c2
        p2_no_wrap_quote = not (c2.strip().startswith('"') or c2.strip().startswith("'"))

        # P2. 종목 섹션별 길이 분석
        pick_sections = re.findall(
            r'<div style="[^"]*fffaf0[^"]*">(.*?)</div>', c2, re.DOTALL
        )
        section_lens = [len(re.sub(r"<[^>]+>", "", s).strip()) for s in pick_sections]

        # P3. 숫자+논리 연결 여부
        p2_has_logic_number = bool(has_logic_number.search(re.sub(r"<[^>]+>", "", c2)))

        # P4. 4구조 키워드 존재 여부
        p2_plain = re.sub(r"<[^>]+>", "", c2)
        has_why_now = bool(re.search(r"왜.{0,10}지금|지금.{0,10}이유|오늘.{0,10}테마|이 종목.{0,10}이유", p2_plain))
        has_sector = bool(re.search(r"영업이익|매출|수주|HBM|MLCC|수요|공급|실적|분기|목표주가|PER", p2_plain))
        has_reflect = bool(re.search(r"선반영|이미.{0,10}반영|밸류에이션|수급|PER|할인|프리미엄", p2_plain))
        has_risk = bool(re.search(r"리스크|반대|우려|하락|위험|한계|불확실|경쟁|압력", p2_plain))

        # P10. PICKS 주석 존재 — assemble_final_content() 이전 raw 단계 기준으로 확인
        # (assemble이 PICKS 주석을 의도적으로 제거하므로 최종 content에서는 항상 없음 → raw 단계 기록값 사용)
        has_picks_comment = post2.get("picks_comment_in_raw", False)

        p2_criteria = {
            "P1. WordPress 출력: 순수 HTML로 시작 (코드펜스·따옴표 없음)":
                p2_clean_start and p2_no_backtick and p2_no_wrap_quote,

            "P2. 종목 박스(div) 섹션이 2개 이상 존재하는가":
                len(pick_sections) >= 2,

            f"P3. 메인픽 분량이 400자 이상인가 (실측: {section_lens[0] if section_lens else 0}자)":
                section_lens[0] >= 400 if section_lens else False,

            f"P4. 보조픽 분량이 300자 이상인가 (실측: {section_lens[1] if len(section_lens)>1 else 0}자)":
                section_lens[1] >= 300 if len(section_lens) > 1 else False,

            "P5. 숫자가 실제 투자 논리(원인·수혜·실적)와 연결됐는가":
                p2_has_logic_number,

            "P6. '왜 지금인가' 구조가 드러나는가":
                has_why_now,

            "P7. 업황·실적 근거(숫자 포함)가 있는가":
                has_sector,

            "P8. 반영 변수(선반영·밸류에이션·수급) 서술이 있는가":
                has_reflect,

            "P9. 반대 포인트(리스크·우려·경쟁압력)가 있는가":
                has_risk,

            "P10. PICKS JSON 주석이 포함됐는가 (포트폴리오 추적용)":
                has_picks_comment,
        }

        p2_all_pass = True
        for criterion, passed in p2_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | {criterion}")
            if not passed:
                p2_all_pass = False

        print(f"\n  📊 종목 박스 {len(pick_sections)}개 | 박스별 글자수: {section_lens}")
        print(f"  📊 숫자+논리 연결: {'있음' if p2_has_logic_number else '없음'}")
        print(f"  📊 4구조 — 왜지금:{has_why_now} 업황:{has_sector} 반영변수:{has_reflect} 리스크:{has_risk}")
        print("\n" + "=" * 70)
        if p2_all_pass:
            print("🎉 Post2 전체 검증 통과")
        else:
            print("⚠️  Post2 일부 기준 미통과")
        print("=" * 70 + "\n")

    except Exception as e:
        logger.exception(f"Post2 테스트 실패: {e}")
        sys.exit(1)
