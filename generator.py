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
from styles.tokens import (  # Pre-Phase 17: 스타일 토큰 중앙 관리
    _H1_STYLE, _H3_STYLE, _P_STYLE, _HR_STYLE, _PICKS_DIV_STYLE, _STRONG_STYLE,
    _CITE_STYLE,
    _FOOTNOTE_SUP_STYLE, _FOOTNOTE_SECTION_STYLE, _FOOTNOTE_TITLE_STYLE, _FOOTNOTE_ITEM_STYLE,
    BQ_STYLE, UL_STYLE, OL_STYLE, LI_STYLE, A_STYLE,
    SOURCE_BOX_STYLE, SOURCE_H_STYLE, SOURCE_CAT_STYLE, SOURCE_UL_STYLE, SOURCE_LI_STYLE,
    H1_STYLE as _conv_H1, H3_STYLE as _conv_H3, P_STYLE as _conv_P,
    HR_STYLE as _conv_HR, PICKS_DIV_STYLE as _conv_PICKS,
)
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

# ── Phase A: 거시지표 모듈 ─────────────────────────────────────────────────────
try:
    from macro_data import get_macro_snapshot, format_macro_for_prompt
    _MACRO_DATA_AVAILABLE = True
except ImportError:
    _MACRO_DATA_AVAILABLE = False

# ── Phase B: 지식베이스 모듈 ──────────────────────────────────────────────────
try:
    from knowledge_base import retrieve_context as kb_retrieve, save_article as kb_save
    _KB_AVAILABLE = True
except ImportError:
    _KB_AVAILABLE = False

# ── Phase C: 편집 철학 모듈 ───────────────────────────────────────────────────
try:
    from editorial_config import (
        DISCLAIMER_OPENING_HTML, DISCLAIMER_CLOSING_HTML,
        _PC_GEMINI_SECTOR_RULES,
        _PC_POST1_EDITORIAL_RULES,
        _PC_POST2_EDITORIAL_RULES,
    )
    _EDITORIAL_CONFIG_AVAILABLE = True
except ImportError:
    _EDITORIAL_CONFIG_AVAILABLE = False
    DISCLAIMER_OPENING_HTML = ""
    DISCLAIMER_CLOSING_HTML = ""
    _PC_GEMINI_SECTOR_RULES = ""
    _PC_POST1_EDITORIAL_RULES = ""
    _PC_POST2_EDITORIAL_RULES = ""

# ── Phase R: 거시경제 리포트 + Few-shot 예시 로더 ─────────────────────────────
try:
    from reference_loader import (
        load_reference_reports,
        format_reports_for_prompt,
        load_few_shot_examples,
        format_few_shot_for_prompt,
    )
    _REFERENCE_LOADER_AVAILABLE = True
except ImportError:
    _REFERENCE_LOADER_AVAILABLE = False

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


def _p16j_check_theme_repeat(current_theme: str) -> dict:
    """Phase 16J Track B: 동일 macro theme 연속 슬롯 여부 진단.

    최근 publish_history에서 theme_fingerprint 일치 항목 수를 확인.
    repeat 감지 시 logger.warning으로 운영자에게 알림.

    Returns:
        {
            "is_repeat":    bool   — 1건 이상 동일 theme_fp 있으면 True,
            "repeat_count": int    — 이력 내 동일 theme_fp 건수,
            "theme_fp":     str    — 현재 theme fingerprint,
            "matched_slots": list  — 최근 3건의 slot/published_at/post1_title,
        }
    """
    theme_fp = _make_theme_fingerprint(current_theme)

    if theme_fp == "기타":
        logger.info("[Phase 16J] theme_fp=기타 — 연속 감지 제외")
        return {"is_repeat": False, "repeat_count": 0,
                "theme_fp": theme_fp, "matched_slots": []}

    history = _load_publish_history()
    matched = []
    for entry in reversed(history):  # 최신 순
        e_fp = entry.get("theme_fingerprint") or _make_theme_fingerprint(
            entry.get("theme", ""))
        if e_fp == theme_fp:
            matched.append({
                "slot":         entry.get("slot", ""),
                "published_at": entry.get("published_at", ""),
                "post1_title":  entry.get("post1_title", "")[:40],
            })

    is_repeat = len(matched) >= 1

    if is_repeat:
        logger.warning(
            f"[Phase 16J] 동일 theme 연속 감지 | theme_fp={theme_fp} | "
            f"최근 {len(matched)}건 동일 theme 발행 이력 — Post2 opener 다양화 강화"
        )
        for m in matched[:3]:
            logger.warning(
                f"  ⚠ [{m['slot']}] {m['published_at'][:16]} | {m['post1_title']}"
            )
    else:
        logger.info(f"[Phase 16J] theme 연속 없음 | theme_fp={theme_fp}")

    return {
        "is_repeat":    is_repeat,
        "repeat_count": len(matched),
        "theme_fp":     theme_fp,
        "matched_slots": matched[:3],
    }


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
    # [Phase 19] 고정 구조 섹션명 제외: Post1/Post2 모두에 항상 존재하는 보일러플레이트 h3
    # "참고 출처"는 두 글 모두에 구조적으로 포함되므로 비교 대상에서 제외
    _STRUCTURAL_H3_SKIP = {"참고 출처", "참고출처"}

    def _extract_h3s(html: str) -> set:
        raw = re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.DOTALL | re.IGNORECASE)
        result = set()
        for h in raw:
            text = re.sub(r"<[^>]+>", "", h).strip()
            if text and text not in _STRUCTURAL_H3_SKIP:
                result.add(text)
        return result

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

'왜 지금 {메인 픽 또는 핵심 섹터}인가' 섹션 구조 (Phase 17 개편):
  Post1이 도출한 결론 → 메인 픽/핵심 섹터의 핵심 민감도와 트리거를 즉시 제시 → 종목 분석으로 진입
  ⚠ '오늘 이 테마를 보는 이유' 섹션명은 Phase 17부터 금지됨. 픽 각도 진입형으로 교체됨.

❌ 금지:
- "최근 X가 발생하면서..." 배경 재설명
- Post1에서 이미 나온 호르무즈/금리/환율 맥락 반복
- "최근 시장이 주목하는..." 류의 매크로 재진입

✅ 허용:
- "앞서 살펴본 흐름을 종목으로 옮기면, [X] 조건에서 직접 노출되는 종목은..."
- "오늘의 핵심 논지인 [X]를 바탕으로, 가장 직접 영향받는 종목은..."
- 종목 선정 기준과 그 기준이 이번 테마에서 갖는 특수성
- 심층분석 핵심 수치 1개 인용 후 바로 종목 분석 진입

★ Phase 15C 추가 금지: 독자 대상 문장에서 "Post1", "Post2" 등 파이프라인 내부 용어 절대 사용 금지.
  구독자는 이 용어를 알지 못합니다. 자연스러운 편집 연결 표현을 사용하십시오."""

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
    # [Phase 20] 이중 카운팅 버그 수정:
    # "것으로 보입니다" 는 "로 보입니다" 를 포함 → plain.count() 시 2번 카운트됨
    # → hedge_ratio 과장 → false FAIL 발생. 단축형 4개 제거.
    # "로 보입니다" 독립 사용 패턴은 "것이라 보입니다" 등 드문 형태이므로 long form으로 커버.
    # "로 파악됩니다", "로 보입니다", "로 추정됩니다", "로 예상됩니다",  ← REMOVED
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
    # Phase 18: 한국어 리스크 서술에서 자주 쓰이는 조건부 어미·패턴 추가
    "될 경우",      # "악화될 경우", "지속될 경우", "급락할 경우"
    "할 경우",      # "현실화할 경우", "심화할 경우"
    "강화될",       # "규제가 강화될", "경쟁이 강화될"
    "악화될",       # "업황이 악화될"
    "약화될",       # "수요가 약화될"
    "지연될",       # "회복이 지연될"
    "심화될",       # "갈등이 심화될"
    "하락할",       # "주가가 하락할"
    "급락할",       # 급격한 하락 시나리오
    # [Phase 20] 리스크·반론 섹션에서 자주 쓰이는 추가 패턴 (counterpoint_spec FAIL 오탐 억제)
    "다만",         # "다만 ~에 주의해야 한다" — 유보/단서 서술
    "하지만",       # "하지만 ~는 불확실하다" — 반론 접속
    "불확실",       # "불확실성이 존재한다" — 불확실성 명시
    "우려",         # "우려가 있다", "우려 요인" — 우려 표현
    "주의",         # "주의해야 할 포인트" — 주의 환기
    "위험성",       # "위험성이 있다" — 위험 서술
    "변동성",       # "변동성이 높다/확대될 수 있다" — 변동성 언급
    "도전",         # "도전 요인이 존재한다" — 도전 과제
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


def _inject_disclaimer(content: str) -> str:
    """Phase C: 면책 문구를 h1 태그 직후(opening) + 본문 말미(closing)에 자동 삽입."""
    if not content or not DISCLAIMER_OPENING_HTML:
        return content
    # Opening: 첫 번째 </h1> 직후 삽입
    content = re.sub(
        r'(</h1>)',
        r'\1' + DISCLAIMER_OPENING_HTML,
        content, count=1,
    )
    # Closing: 콘텐츠 맨 마지막에 추가
    content = content + DISCLAIMER_CLOSING_HTML
    return content


def _check_macro_facts(content: str, macro_snapshot: dict) -> dict:
    """Phase D: 본문 기준금리·환율 수치를 BOK/FRED 실제값과 교차 검증.

    _check_numeric_sanity()가 "범위 내인가"를 검사한다면,
    이 함수는 "실제 현재값과 일치하는가"를 검사합니다.

    허용 오차:
        기준금리(한국): ±0.15%p
        기준금리(미국): ±0.15%p
        달러/원 환율:   ±50원

    반환:
        {"status": "PASS"|"WARN"|"FAIL", "flags": list[str]}
    """
    flags = []
    plain = re.sub(r"<[^>]+>", " ", content)
    floats = macro_snapshot.get("floats", {}) if macro_snapshot else {}

    bok_rate = floats.get("bok_rate")
    fed_rate = floats.get("fed_rate")
    usdkrw   = floats.get("usdkrw")

    # 한국 기준금리 교차검증
    if bok_rate is not None:
        for m in re.finditer(r"(?:한국|국내).{0,15}기준금리.{0,20}?([\d]+\.[\d]+)\s*%", plain):
            try:
                mentioned = float(m.group(1))
                if abs(mentioned - bok_rate) > 0.15:
                    flags.append(
                        f"KR_RATE_MISMATCH: 본문 {mentioned}% vs 실제 {bok_rate}% "
                        f"(오차 {abs(mentioned - bok_rate):.2f}%p)"
                    )
            except ValueError:
                pass

    # 미국 기준금리 교차검증
    if fed_rate is not None:
        for m in re.finditer(r"(?:연준|미국|Fed).{0,15}(?:기준)?금리.{0,20}?([\d]+\.[\d]+)\s*%", plain):
            try:
                mentioned = float(m.group(1))
                if abs(mentioned - fed_rate) > 0.15:
                    flags.append(
                        f"FED_RATE_MISMATCH: 본문 {mentioned}% vs 실제 {fed_rate}% "
                        f"(오차 {abs(mentioned - fed_rate):.2f}%p)"
                    )
            except ValueError:
                pass

    # 달러/원 환율 교차검증
    if usdkrw is not None:
        candidates = (
            re.findall(r"달러당\s*([\d,]+)\s*원", plain)
            + re.findall(r"([\d,]+)\s*원[/\s]*달러", plain)
            + re.findall(r"달러[/\s]*원\s*[\=:]\s*([\d,]+)", plain)
        )
        for n_str in candidates:
            try:
                mentioned = float(n_str.replace(",", ""))
                if 900 < mentioned < 3000 and abs(mentioned - usdkrw) > 50:
                    flags.append(
                        f"USDKRW_MISMATCH: 본문 {mentioned:.0f}원 vs 실제 {usdkrw:.0f}원 "
                        f"(오차 {abs(mentioned - usdkrw):.0f}원)"
                    )
            except ValueError:
                pass

    status = "FAIL" if len(flags) >= 2 else "WARN" if flags else "PASS"
    if flags:
        logger.warning(f"[Phase D] 거시지표 불일치 {len(flags)}건 감지")
        for f in flags[:4]:
            logger.warning(f"  ⚠ {f}")
    else:
        logger.info("[Phase D] 거시지표 교차검증: 이슈 없음")

    return {"status": status, "flags": flags[:6]}


def _check_verifier_closure(issues: list, draft: str, revised: str) -> dict:
    """Phase 13 Track B: Gemini 검수 이슈가 Step3 수정 후 실제 해소되었는지 확인.

    Phase 16H Track B: 스타일/구조 품질 이슈를 'style_residual'로 분리해
    진짜 사실 미해소(truly_unresolved)와 구분한다.
    FAIL 판정은 truly_unresolved 수에만 기반 → false fail 감소.

    Returns:
        {status, total_checked, resolved_count, unresolved_count, unresolved,
         truly_unresolved_count, style_residual_count, closure_reason}
    """
    import re as _re

    if not issues or not revised:
        return {
            "status": "SKIP", "total_checked": 0,
            "resolved_count": 0, "unresolved_count": 0, "unresolved": [],
            "truly_unresolved_count": 0, "style_residual_count": 0,
            "closure_reason": "이슈 없음 또는 수정본 없음",
        }

    TEMPORAL_NUMERIC_KW = [
        "[1]", "[시점 일관성]", "[숫자", "[수치", "시점", "일관성",
        "기준 날짜", "출처 날짜", "연간", "전망치", "확정",
    ]

    # Phase 16H Track B: 스타일/구조 이슈 키워드 — 이 키워드가 포함된 미해소 이슈는
    # 사실 오류가 아닌 writing quality 문제이므로 closure FAIL 판정에서 제외.
    # [Phase 18] 해석·분석 품질 이슈 패턴 추가:
    # Gemini verifier가 [1] 카테고리로 플래그해도, 설명 텍스트에 아래 패턴이 포함된 이슈는
    # 시간/수치 사실 오류가 아닌 analytical quality 문제이므로 style_residual로 분류.
    STYLE_RESIDUAL_KW = [
        "완충 문장", "4요소", "헤징", "비유", "마크다운", "숫자가 없는 문단",
        "구체적인 근거 없이", "스타일", "문단 구조", "소제목",
        # Phase 18 신규: 해석·분석 품질 이슈 (temporal/numeric 사실 오류 아님)
        "구체적 근거가 없",      # "구체적 근거가 없습니다" — 근거 부족 지적
        "실현 가능성에 대한",    # 조건부 시나리오의 근거 없음 지적
        "조건으로 제시",         # 조건부 전제 구조 지적 (시나리오→결론 논리 문제)
        "근거 없이 단정",        # 사실 단정 없이 결론 서술 지적
        "논리적 근거",           # 논리 흐름 품질 지적
        # [Phase 20] 조건부·가능성·불확실성 분석 서술 (사실 오류 아님 — 헤징·시나리오 표현)
        # verifier [1] 카테고리로 플래그하지만 조건부/확률적 분석 서술이므로 style_residual 처리
        "가능성이",              # "~가능성이 높/큽/있습니다" — 확률적 분석 서술
        "만약",                  # 조건부 시나리오 ("만약 ~된다면")
        "수 있습니다",           # 조건부 서술 ("~초래할/위축시킬/더딜 수 있습니다")
        "수 있다",               # 조건부 서술 (종결형)
        "된다면",                # 조건 종속절 ("~표면화된다면", "~실현된다면")
        "않는다면",              # 부정 조건 ("~확인되지 않는다면")
        # [Phase 20] [기준10] writing quality: 문단 수치 없음 지적 (사실 오류 아님)
        "숫자나 기준",           # "[기준10/10] 섹션 문단에 숫자나 기준 시점이 없음"
    ]

    high_risk = [
        iss for iss in issues
        if any(kw in iss for kw in TEMPORAL_NUMERIC_KW)
    ]

    # Phase 16H Track B: (original_issue, display_str, is_style_residual) 튜플로 관리
    # → 원본 텍스트로 STYLE_RESIDUAL_KW 분류, 표시용 truncate 별도 처리
    resolved_items: list = []    # (orig, display)
    unresolved_items: list = []  # (orig, display)

    for issue in high_risk:
        quoted = _re.findall(
            r"[\u2018\u2019\u201c\u201d']([^\u2018\u2019\u201c\u201d']{10,80})[\u2018\u2019\u201c\u201d']",
            issue,
        )
        if not quoted:
            quoted_pairs = _re.findall(r"'([^']{10,60})'|\"([^\"]{10,60})\"", issue)
            quoted = [q[0] or q[1] for q in quoted_pairs if (q[0] or q[1])]

        if not quoted:
            resolved_items.append((issue, issue[:60] + "…"))
            continue

        still_present = any(phrase in revised for phrase in quoted if phrase)
        display = issue[:80] + "…"
        if still_present:
            unresolved_items.append((issue, display))
        else:
            resolved_items.append((issue, display))

    # Phase 16H Track B: 원본 텍스트로 style/truly 분류 (truncate 전 전체 텍스트 사용)
    truly_unresolved = [
        disp for orig, disp in unresolved_items
        if not any(kw in orig for kw in STYLE_RESIDUAL_KW)
    ]
    style_residual = [
        disp for orig, disp in unresolved_items
        if any(kw in orig for kw in STYLE_RESIDUAL_KW)
    ]
    # 하위호환: unresolved = display strings
    unresolved = [disp for _, disp in unresolved_items]
    resolved = [disp for _, disp in resolved_items]

    total = len(high_risk)
    un_cnt = len(unresolved)
    truly_cnt = len(truly_unresolved)

    # Phase 16H: FAIL 기준을 truly_unresolved >= 2 로 조정
    # (style_residual만 남은 경우 WARN으로 강등, false fail 억제)
    status = (
        "FAIL"  if truly_cnt >= 2
        else "WARN"  if truly_cnt >= 1 or un_cnt >= 1
        else "PASS"  if total > 0
        else "SKIP"
    )

    # closure_reason: 운영자 가독용 요약
    if un_cnt == 0:
        closure_reason = "전체 해소" if total > 0 else "해당 없음"
    elif truly_cnt == 0:
        closure_reason = f"style_residual {len(style_residual)}건만 잔존 (사실 오류 없음)"
    else:
        closure_reason = f"사실 미해소 {truly_cnt}건 + style_residual {len(style_residual)}건"

    result = {
        "status":                  status,
        "total_checked":           total,
        "resolved_count":          len(resolved),
        "unresolved_count":        un_cnt,
        "unresolved":              unresolved[:3],
        "truly_unresolved_count":  truly_cnt,          # Phase 16H 신규
        "style_residual_count":    len(style_residual), # Phase 16H 신규
        "closure_reason":          closure_reason,       # Phase 16H 신규
    }

    logger.info(
        f"[Phase 13] 검수 해소 확인 | 고위험 {total}건 | "
        f"해소 {len(resolved)} / 미해소 {un_cnt} "
        f"(사실 {truly_cnt}건 + style {len(style_residual)}건) | 상태: {status}"
    )
    if truly_unresolved:
        for u in truly_unresolved:
            logger.warning(f"  ⚠ 미해소[사실]: {u}")
    if style_residual:
        for u in style_residual:
            logger.info(f"  ℹ 미해소[style]: {u}")

    return result


def _check_post_continuity(post1_content: str, post2_content: str) -> dict:
    """Phase 13 Track A-5: Post2 도입부가 Post1 도입부를 반복하는지 진단.

    [Phase 18 신규] h1 블록(제목 + 면책문구) 스킵:
    Phase C _inject_disclaimer()가 </h1> 직후에 면책문구를 주입하면서
    두 글 모두 도입부 앞 400/600자 안에 동일한 면책문구 텍스트가 포함됨.
    이로 인해 실제 내용 중복이 없어도 n-gram 이 대량 일치(19개)하는 오탐이 발생.
    → 첫 <h2> 또는 <h3> 이후 본문부터 비교 구간으로 사용.

    Returns:
        {status, ngram_overlap_count, bg_repeat_count, sample_overlaps}
    """
    import re as _re

    def _text(html: str, limit: int = 400) -> str:
        # h1 블록(제목 + 면책문구) 건너뛰기: 첫 h2/h3 이후부터 추출
        m = _re.search(r"<h[23][^>]*>", html, _re.IGNORECASE)
        body = html[m.start():] if m else html
        return _re.sub(r"<[^>]+>", " ", body)[:limit]

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
        lines.append("\n⚠ FORECAST 데이터 — 조건부 언어 표지 필수 ('~로 예상된다' / '~할 것으로 전망된다' 형식):")
        for c, src in forecast[:5]:
            lines.append(f"  • [{src}] {c}")

    if ambiguous:
        lines.append("\n❓ AMBIGUOUS — 해석·분석 표현으로만 서술 ('~라는 분석이다' / '~로 해석된다' 형식):")
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
"지정학 단기 노이즈 처리 국면에서 이익 모멘텀 종목이 상대 우위라는 오늘의 논지에서,
가장 직접 노출되는 종목은 삼성전자다 — 이번 주 이익 추정치 변화가
이 논지를 직접 확인해준다."

★ Phase 15C 금지: ❌ "Post1 결론:", "Post1에서", "Post2에서" 등 파이프라인 용어를
  독자 대상 문장에 사용하지 말 것. 내부 용어는 편집 흐름 표현으로 대체할 것.
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

# ── Track A (Phase 14I): Interpretation Hedge Clamp ──────────────────────────
# 실출력 검증: [해석] 문장 74%가 "파악됩니다/보입니다" 어미로 끝남.
# 팩트 서술 금지(Phase 14)와 별개로, [해석] 레이블 분석 문장 전용 어미 차단.

_P14I_INTERP_HEDGE_ENDINGS: list = [
    "파악됩니다",
    "보입니다",
    "것으로 보입니다",
    "것으로 파악됩니다",
    "작용하는 것으로 보입니다",
    "시사하는 것으로 보입니다",
    "판단됩니다",
    "것으로 판단됩니다",
    "보여집니다",
    "여겨집니다",
]

_P14I_INTERP_HEDGE_CLAMP: str = """
[Phase 14I — 해석 문장 헤징 어미 강제 차단]

분석·해석 판단 문장에서 아래 어미를 기본 결말로 사용하는 것을 금지합니다:
  ❌ "파악됩니다"
  ❌ "보입니다"
  ❌ "것으로 보입니다"
  ❌ "것으로 파악됩니다"
  ❌ "작용하는 것으로 보입니다"
  ❌ "시사하는 것으로 보입니다"
  ❌ "판단됩니다"

금지 예:
  ❌ 이는 시장 불안 심리가 반영된 결과로 파악됩니다.
  ❌ 이는 투자 심리를 개선하는 요인으로 작용하는 것으로 보입니다.
  ❌ 이는 성장성 기대가 이어지는 것으로 보입니다.

허용 대안 (아래 형식 중 하나를 사용하십시오):
  ✅ "핵심은 [구체적 판단]에 있다."
  ✅ "이는 [A] 대신 [B]에 주목해야 함을 의미한다."
  ✅ "이번 흐름은 [X]가 아니라 [Y]에 가깝다."
  ✅ "이 구도는 [투자자 행동 기준]을 바꾼다."
  ✅ "[조건] 하에서, [구체 결과]가 [일반 예상]보다 빠르게 나타날 수 있다."

해석 문장은 면책 선언이 아닙니다. 분석적 판단을 직접 서술합니다.
"""

_P14_POST1_ENFORCEMENT_BLOCK: str = (
    _P14_ANALYTICAL_SPINE_ENFORCEMENT + "\n"
    + _P14_FEWSHOT_BAD_GOOD_INTERP + "\n"
    + _P14_HEDGE_DIRECT_PROHIBITION + "\n"
    + _P14I_INTERP_HEDGE_CLAMP + "\n"   # Phase 14I: [해석] 헤징 어미 차단
    # Phase 15 block injected below after constant definition
)

# ── Phase 15: Temporal Tense Enforcement ─────────────────────────────────────
# 발행일 기준 완료 연도(2024, 2025 등)의 기업 실적이 "예상/전망/추정"으로
# 서술되는 문제를 생성 단계(Track C) + 발행 전 교정(Track E) 두 단계에서 차단.

# A1/D1: 완료 연도 + 전망 어미 탐지 대상 동사·구문
_P15_COMPLETED_YEAR_FORECAST_VERBS: list = [
    "예상됩니다",
    "전망됩니다",
    "예상된다",
    "전망된다",
    "기록할 것으로",
    "달성할 것으로",
    "기록할 전망",
    "달성할 전망",
    "것으로 예상",
    "것으로 전망",
    "것으로 기대",
    "것으로 추정됩니다",
    "것으로 추정된다",
    "추정됩니다",
    "기대됩니다",
    "보일 전망",
    "늘어날 전망",
    "감소할 전망",
]

# E1: 완료 연도 전망 어미 → 확정 사실 어미 교체 맵
_P15_TENSE_CORRECTION_MAP: list = [
    # ── Phase 15B: 연결어미 패턴 최최우선 (됩니다/된다 외 되며/되고/되어) ────────
    # Phase 15A HOLD 원인: "기록할 것으로 전망되며" — 됩니다/된다만 커버되고 되며 미커버
    ("기록할 것으로 전망되며",         "기록한 것으로 집계됐으며"),
    ("기록할 것으로 전망되고",         "기록한 것으로 집계됐고"),
    ("기록할 것으로 전망되어",         "기록한 것으로 집계됐다"),
    ("달성할 것으로 전망되며",         "달성한 것으로 집계됐으며"),
    ("달성할 것으로 전망되고",         "달성한 것으로 집계됐고"),
    ("증가할 것으로 전망되며",         "증가한 것으로 집계됐으며"),
    ("감소할 것으로 전망되며",         "감소한 것으로 집계됐으며"),
    ("기록할 것으로 예상되며",         "기록한 것으로 집계됐으며"),
    ("기록할 것으로 예상되고",         "기록한 것으로 집계됐고"),
    ("달성할 것으로 예상되며",         "달성한 것으로 집계됐으며"),
    ("증가할 것으로 예상되며",         "증가한 것으로 집계됐으며"),
    ("감소할 것으로 예상되며",         "감소한 것으로 집계됐으며"),
    ("기록할 것으로 추정되며",         "기록한 것으로 집계됐으며"),
    ("달성할 것으로 추정되며",         "달성한 것으로 집계됐으며"),
    ("증가할 것으로 추정되며",         "증가한 것으로 집계됐으며"),
    ("감소할 것으로 추정되며",         "감소한 것으로 집계됐으며"),
    # ── Phase 15A: 복합 패턴 최우선 (어간+어미 동시 교체) ──────────────────────
    # 기록할 + 것으로 + [추정/예상/전망/기대] 동시 교체
    ("기록할 것으로 추정됩니다",       "기록한 것으로 집계됐습니다"),
    ("기록할 것으로 추정된다",         "기록한 것으로 집계됐다"),
    ("달성할 것으로 추정됩니다",       "달성한 것으로 집계됐습니다"),
    ("달성할 것으로 추정된다",         "달성한 것으로 집계됐다"),
    ("증가할 것으로 추정됩니다",       "증가한 것으로 집계됐습니다"),
    ("증가할 것으로 추정된다",         "증가한 것으로 집계됐다"),
    ("감소할 것으로 추정됩니다",       "감소한 것으로 집계됐습니다"),
    ("감소할 것으로 추정된다",         "감소한 것으로 집계됐다"),
    ("올릴 것으로 추정됩니다",         "올린 것으로 집계됐습니다"),
    ("올릴 것으로 추정된다",           "올린 것으로 집계됐다"),
    ("확대할 것으로 추정됩니다",       "확대한 것으로 집계됐습니다"),
    ("확대할 것으로 추정된다",         "확대한 것으로 집계됐다"),
    ("기록할 것으로 기대됩니다",       "기록한 것으로 확인됐습니다"),
    ("기록할 것으로 기대된다",         "기록한 것으로 확인됐다"),
    ("달성할 것으로 기대됩니다",       "달성한 것으로 확인됐습니다"),
    ("달성할 것으로 기대된다",         "달성한 것으로 확인됐다"),
    ("증가할 것으로 기대됩니다",       "증가한 것으로 확인됐습니다"),
    ("감소할 것으로 기대됩니다",       "감소한 것으로 확인됐습니다"),
    ("기록할 것으로 관측됩니다",       "기록한 것으로 집계됐습니다"),
    ("기록할 것으로 관측된다",         "기록한 것으로 집계됐다"),
    ("달성할 것으로 관측됩니다",       "달성한 것으로 집계됐습니다"),
    # ── Phase 15 기존 패턴 (어간+어미 일체형) ──────────────────────────────────
    # (탐지 패턴, 교체 문자열) — 순서 중요 (긴 패턴 우선)
    ("기록할 것으로 예상됩니다",      "기록했습니다"),
    ("달성할 것으로 예상됩니다",      "달성했습니다"),
    ("기록할 것으로 예상된다",        "기록했다"),
    ("달성할 것으로 예상된다",        "달성했다"),
    ("기록할 것으로 전망됩니다",      "기록했습니다"),
    ("달성할 것으로 전망됩니다",      "달성했습니다"),
    ("기록할 것으로 전망된다",        "기록했다"),
    ("달성할 것으로 전망된다",        "달성했다"),
    ("기록할 전망입니다",             "기록했습니다"),
    ("기록할 전망이다",               "기록했다"),
    ("달성할 전망입니다",             "달성했습니다"),
    ("달성할 전망이다",               "달성했다"),
    ("것으로 예상됩니다",             "것으로 집계됐습니다"),
    ("것으로 예상된다",               "것으로 집계됐다"),
    ("것으로 전망됩니다",             "것으로 나타났습니다"),
    ("것으로 전망된다",               "것으로 나타났다"),
    ("것으로 기대됩니다",             "것으로 확인됐습니다"),
    ("것으로 기대된다",               "것으로 확인됐다"),
    ("것으로 추정됩니다",             "것으로 집계됐습니다"),
    ("것으로 추정된다",               "것으로 집계됐다"),
    ("전망됩니다",                    "기록됐습니다"),
    ("전망된다",                      "기록됐다"),
    ("예상됩니다",                    "기록됐습니다"),
    ("예상된다",                      "기록됐다"),
    ("추정됩니다",                    "집계됐습니다"),
    ("추정된다",                      "집계됐다"),
    ("기대됩니다",                    "확인됐습니다"),
    ("기대된다",                      "확인됐다"),
]

# A1: 잠정치 / 컨센서스 / 가이던스 마커 (예외 처리용)
_P15_PRELIMINARY_MARKERS: list  = ["잠정", "preliminary", "속보치", "잠정치"]
_P15_CONSENSUS_MARKERS: list    = ["컨센서스", "시장 기대", "시장 예상", "consensus"]
_P15_GUIDANCE_MARKERS: list     = ["가이던스", "guidance", "목표치", "가이드"]

# ── Phase 15A: Compound Tense Regex Engine ────────────────────────────────────
# 어간 + 할 것으로 + [추정/예상/전망/기대/관측] + [됩니다/된다] 패턴을 한 번에 교체.
# 어간을 그대로 재사용하여 "기록할 것으로 추정됩니다" → "기록한 것으로 집계됐습니다"
import re as _re_p15a
_P15A_COMPOUND_RE_FORMAL: "_re_p15a.Pattern" = _re_p15a.compile(
    r"([가-힣]+)할(\s+것으로\s+)(추정|예상|전망|기대|관측)됩니다"
)
_P15A_COMPOUND_RE_INFORMAL: "_re_p15a.Pattern" = _re_p15a.compile(
    r"([가-힣]+)할(\s+것으로\s+)(추정|예상|전망|기대|관측)된다"
)
# 교정 후 잔여 미래형 어간 검사용
_P15A_FUTURE_STEM_RE: "_re_p15a.Pattern" = _re_p15a.compile(
    r"[가-힣]+할\s+것으로"
)

# ── Phase 15B: Connective Ending Coverage Extension ───────────────────────────
# Phase 15A HOLD 원인: "기록할 것으로 전망되며" — 연결어미 됩니다/된다 외 미커버.
# 됩니다|된다 외 자주 등장하는 연결어미 3종 추가 커버.
_P15B_COMPOUND_RE_CONNECTIVE: "_re_p15a.Pattern" = _re_p15a.compile(
    r"([가-힣]+)할(\s+것으로\s+)(추정|예상|전망|기대|관측)(되며|되고|되어)"
)
# 연결어미 → 과거 연결어미 매핑 (의미 보존)
_P15B_CONNECTIVE_ENDING_MAP: dict = {
    "되며": "됐으며",   # 전망되며  → 집계됐으며
    "되고": "됐고",     # 전망되고  → 집계됐고
    "되어": "됐다",     # 전망되어  → 집계됐다  (자연스러운 단문 종결)
}

# ── Phase 15C: Step3 완료 연도 컨텍스트 주입 + Post2 내부 레이블 제거 ──────────
# 근본 원인: Gemini Step3가 2024/2025를 현재 진행 중인 연도로 오인 → [전망] 강요
# Secondary: Post2 독자 문장에 "Post1의 결론에 따르면" 같은 파이프라인 용어 노출

_P15C_STEP3_TEMPORAL_GROUNDING: str = """
[Phase 15C — Step3 발행 기준 연도 컨텍스트 ★ 최우선 적용]

이 콘텐츠의 발행 기준 연도는 2026년입니다.

완료 연도 분류 (2026년 발행 기준):
  - 2024년 = 완전히 종료된 회계 연도 → 연간 실적은 확정 사실
  - 2025년 = 완전히 종료된 회계 연도 → 연간 실적은 확정 사실
  - 2026년 = 현재 진행 중인 연도 → 전망·추정 서술 허용

★ Step3 절대 금지 행동:
  ❌ 2024년 또는 2025년을 "현재 진행 중인 연도"로 판단하는 것 — 이는 틀린 판단
  ❌ 2024년/2025년 확정 실적 문장에 [전망] 태그를 추가하거나 강요하는 것
  ❌ 2024년/2025년 확정 실적 문장을 조건부·전망 어미로 재작성하는 것
  ❌ "2024년은 현재 진행 중인 연도이므로 확정 표현 불가" — 이 판단은 오류
  ❌ 과거 완료 사실 문장("기록했다", "달성했다", "집계됐다")을 단정적이라는 이유로 수정하는 것

★ Step3 명시적 허용:
  ✅ "SK하이닉스는 2024년 매출 66조원을 기록했다" — 올바른 확정 사실 서술, 수정 불필요
  ✅ "삼성전자는 2025년 영업이익 35조원을 달성했다" — 올바른 확정 사실 서술, 수정 불필요
  ✅ 2024년/2025년 연간 실적이 과거형으로 서술된 문장은 [전망] 판단 대상이 아님
  ✅ 진짜 [전망] 대상: 2026년 이후 미래 수치, 아직 발표되지 않은 전망치·가이던스

"""

# Post2 내부 파이프라인 용어 독자 노출 방지 (Track C)
_P15C_POST2_LABEL_BAN: str = """
[Phase 15C — Post2 내부 파이프라인 용어 독자 노출 금지]

★ 절대 금지 — 독자 대상 문장에서 파이프라인 내부 용어 사용 금지:
  ❌ "Post1의 결론에 따르면..."
  ❌ "Post1에서 도출된 결론은..."
  ❌ "Post1이 분석한..." / "Post1이 도출한..."
  ❌ "Post2 기준으로..." / "이 Post에서..."

★ 허용 — 자연스러운 독자용 연결 표현:
  ✅ "앞서 살펴본 매크로 흐름을 종목 관점에서 보면..."
  ✅ "[심층분석]에서 도출된 결론은..."
  ✅ "이 흐름을 개별 종목에 적용하면..."
  ✅ "앞서 확인한 시장 구조에서 가장 직접 영향받는 종목은..."
  ✅ "오늘의 핵심 논지를 종목으로 옮기면..."

구독자는 "Post1", "Post2"라는 파이프라인 용어를 알지 못합니다.
자연스러운 편집 흐름으로 연결하고, 내부 워크플로우 언어는 절대 노출하지 마십시오.
"""

# C1: 생성 단계 주입 블록 (GPT 프롬프트에 prepend)
_P15_TEMPORAL_TENSE_ENFORCEMENT: str = """
[Phase 15 — 완료 연도 기업 실적 시제 강제]

기사 발행일 기준 이미 완료된 연도(2024년, 2025년)의 기업·시장 실적 수치는
확정 사실로 서술해야 합니다. 아래 규칙을 반드시 준수하십시오.

★ 완료 연도 구분 기준 (2026년 기준):
  - 2024년 = 완전히 완료된 회계 연도 → 확정/잠정 실적으로 서술
  - 2025년 = 완전히 완료된 회계 연도 → 확정/잠정 실적으로 서술
  - 2026년 = 아직 진행 중 → 전망·추정 서술 허용

❌ 금지 — 완료 연도 + 전망 어미:
  ❌ "SK하이닉스 2024년 매출은 66조원을 기록할 것으로 예상된다."
  ❌ "삼성전자 2025년 영업이익은 35조원에 달할 전망이다."
  ❌ "2024년 연간 실적은 사상 최대를 기록할 것으로 추정됩니다."

✅ 허용 — 완료 연도 + 확정 사실 어미:
  ✅ "SK하이닉스는 2024년 매출 66조원을 기록했다."
  ✅ "삼성전자는 2025년 영업이익 35조원을 달성했다."
  ✅ "2024년 연간 실적은 사상 최대를 기록한 것으로 집계됐다."

✅ 예외 — 컨센서스·가이던스·잠정치 언급 시 명확히 구분:
  ✅ "당시 시장 컨센서스는 매출 65조원을 예상했으나, 실제로는 66조원을 달성했다."
  ✅ "잠정치 기준 영업이익은 23조원으로 집계됐다." (잠정치임을 명시)
  ✅ "회사 가이던스는 2026년 매출 70조원 달성을 목표로 한다." (미래 연도 가이던스)

시제 분류:
  COMPLETED_PERIOD_ACTUAL:              직접 과거 사실 서술 (기록했다, 달성했다)
  COMPLETED_PERIOD_PRELIMINARY:         잠정치 명시 후 사실 서술 (잠정 집계됐다)
  COMPLETED_PERIOD_CONSENSUS_REFERENCE: 사실과 기대를 분리 서술
  CURRENT_YEAR_FORECAST (2026):         전망 어미 허용
  FUTURE_YEAR_FORECAST (2027+):         전망 어미 허용
  COMPANY_GUIDANCE:                     미래 목표 서술 허용 (가이던스임을 명시)
"""

# Phase 15 주입: _P14_POST1_ENFORCEMENT_BLOCK에 추가
_P14_POST1_ENFORCEMENT_BLOCK = (
    _P14_POST1_ENFORCEMENT_BLOCK
    + _P15_TEMPORAL_TENSE_ENFORCEMENT + "\n"  # Phase 15: 완료 연도 시제 강제
)

_P14_POST2_CONTINUATION_TEMPLATE: str = """
[Phase 14 — Post2 연속성 강제]
심층분석 결론/뼈대:
{post1_spine}

Post2는 위 결론에서 즉시 출발합니다.
→ "앞서 도출된 결론인 [위 결론]을 바탕으로, 가장 직접 노출되는 종목은..."
→ 또는: "[위 결론]의 조건에서, 섹터 선별 기준의 핵심은..."

다시 매크로 배경(지정학/금리/유가 등)을 설명하는 문단을 도입부에 쓰지 마십시오.

★ Phase 15C 금지: 독자 대상 문장에서 "Post1", "Post2" 등 파이프라인 내부 용어 절대 사용 금지.
  예시 ❌: "Post1이 도출한 결론에 따르면..."
  예시 ✅: "앞서 살펴본 분석 결론을 바탕으로..." / "오늘의 핵심 논지를 종목으로 옮기면..."
"""

# ── Track C: Rewrite Enforcement Loop 프롬프트 ──────────────────────────────

GEMINI_INTERP_REWRITE_SYSTEM: str = """
너는 매크로몰트(MacroMalt) 금융 콘텐츠 품질 강화 에디터다.
입력된 HTML 기사에서 교과서 인과관계와 범용 일반론을 찾아 비자명적 해석으로 교체한다.

[재작성 원칙]
1. 교체 대상: 당연한 결론을 서술하거나 교과서 인과만 담긴 해석 문장
   ("~라는 분석이다", "~를 의미한다", "~로 해석된다" 표현이 있어도 내용이 범용이면 교체 대상)
2. 교체 기준:
   - 이 시점·이 데이터 조합에서만 나오는 함의 명시
   - 상충 신호의 우열 관계 명시 (어느 신호가 더 강한가)
   - 수치 기반 이차 효과 (직접 효과보다 간접 파급 경로)
   - 투자자 판단 기준 이동 명시 (Z 대신 W에 주목해야 하는 이유)
3. 보존 대상: 사실 서술, 숫자, 구체적 조건부 반론, 출처 표기
4. 분량 보존: 교체 후 원문보다 짧아지지 않도록 한다
5. 출력 형식: 수정된 HTML 전체를 그대로 출력 (JSON 래핑 없음, 코드블록 없음)

[절대 금지 패턴 — 발견 즉시 교체]
- "유가 상승 → 인플레이션 압력" 류 직접 인과
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
입력되는 각 HTML 블록은 약한 해석 패턴(교과서 인과, 범용 리스크 나열, 헤징 어미 과잉)이 감지된 단락이다.
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

[Phase 14I — 해석 문장 헤징 어미 차단]
해석·분석 판단 문장의 결말에서 아래 어미를 사용하지 마라:
  ❌ "파악됩니다" / "보입니다" / "것으로 보입니다" / "것으로 파악됩니다"
  ❌ "작용하는 것으로 보입니다" / "시사하는 것으로 보입니다" / "판단됩니다"
금지 예: "이는 투자 심리를 개선하는 요인으로 작용하는 것으로 보입니다."
허용 대안:
  ✅ "핵심은 [판단]에 있다."
  ✅ "이는 [A] 대신 [B]에 주목해야 함을 의미한다."
  ✅ "이번 흐름은 [X]가 아니라 [Y]에 가깝다."
  ✅ "이 구도는 [투자 기준]을 바꾼다."

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
입력되는 각 HTML 블록은 약한 해석 패턴(교과서 인과, 범용 리스크 나열, 헤징 어미 과잉)이 감지된 단락이다.
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

[Phase 14I — 해석 문장 헤징 어미 차단]
해석·분석 판단 문장의 결말에서 아래 어미를 사용하지 마라:
  ❌ "파악됩니다" / "보입니다" / "것으로 보입니다" / "것으로 파악됩니다"
  ❌ "작용하는 것으로 보입니다" / "시사하는 것으로 보입니다" / "판단됩니다"
금지 예: "이는 회사의 신사업 모멘텀이 실적으로 연결되고 있는 것으로 보입니다."
허용 대안:
  ✅ "핵심은 [판단]에 있다."
  ✅ "이는 [A] 대신 [B]에 주목해야 함을 의미한다."
  ✅ "이번 흐름은 [X]가 아니라 [Y]에 가깝다."
  ✅ "[조건] 하에서, [구체 결과]가 [일반 예상]보다 빠르게 나타날 수 있다."

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


# ── Track D (Phase 14I): Hedge Density Diagnostics ───────────────────────────

def _detect_interp_hedge_density(content: str) -> dict:
    """Phase 14I Track D: [해석] 레이블 블록에서 헤징 어미 포화도 측정.

    [해석] 태그가 포함된 문장을 추출하고, 그 중 _P14I_INTERP_HEDGE_ENDINGS 어미로
    끝나는 비율을 계산한다. 재작성 전/후 비교에 사용.

    Returns:
        {
          "interp_total":   int   — [해석] 포함 문장 수,
          "interp_hedged":  int   — 헤징 어미로 끝나는 [해석] 문장 수,
          "hedge_ratio":    float — interp_hedged / max(interp_total, 1),
          "status":         str   — "FAIL"(>0.5) | "WARN"(>0.25) | "PASS",
          "bad_lines":      list  — 헤징 어미 탐지 문장 샘플 (최대 5개),
        }
    """
    import re as _re

    plain = _re.sub(r"<[^>]+>", " ", content)
    # 문장 분리 (마침표·느낌표·물음표 기준, 줄 포함)
    raw_sentences = _re.split(r"(?<=[.!?。！？])\s+", plain)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 15]

    interp_total = 0
    interp_hedged = 0
    bad_lines: list = []

    for sent in sentences:
        if "[해석]" not in sent:
            continue
        interp_total += 1
        for ending in _P14I_INTERP_HEDGE_ENDINGS:
            if sent.rstrip().endswith(ending) or (ending + ".") in sent or (ending + "。") in sent:
                interp_hedged += 1
                if len(bad_lines) < 5:
                    bad_lines.append(sent[:120])
                break

    ratio = interp_hedged / max(interp_total, 1)
    if ratio > 0.50:
        status = "FAIL"
    elif ratio > 0.25:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "interp_total":  interp_total,
        "interp_hedged": interp_hedged,
        "hedge_ratio":   round(ratio, 3),
        "status":        status,
        "bad_lines":     bad_lines,
    }


def _extract_hedge_heavy_interp_blocks(content: str) -> list:
    """Phase 14I Track C: [해석] 레이블을 포함하고 헤징 어미로 끝나는 HTML 블록 추출.

    _extract_weak_interp_blocks과 별개로 작동. [해석] 태그가 있으면서
    _P14I_INTERP_HEDGE_ENDINGS 어미로 끝나는 블록만 추출.

    Returns:
        list of block dicts (html_block, plain_text, matched_endings, ...)
    """
    import re as _re

    block_pattern = _re.compile(
        r"(<(?:p|li|blockquote)[^>]*>)(.*?)(</(?:p|li|blockquote)>)",
        _re.DOTALL | _re.IGNORECASE,
    )
    hedge_blocks: list = []
    for m in block_pattern.finditer(content):
        open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
        plain = _re.sub(r"<[^>]+>", " ", inner).strip()
        if len(plain) < 20:
            continue
        if "[해석]" not in plain:
            continue
        matched_endings: list = []
        for ending in _P14I_INTERP_HEDGE_ENDINGS:
            if (
                plain.rstrip().endswith(ending)
                or (ending + ".") in plain
                or (ending + "。") in plain
            ):
                matched_endings.append(ending)
        if matched_endings:
            hedge_blocks.append({
                "html_block":      m.group(0),
                "open_tag":        open_tag,
                "inner":           inner,
                "close_tag":       close_tag,
                "plain_text":      plain,
                "matched_endings": matched_endings,
                "matched_patterns": [(e, "") for e in matched_endings],  # 재작성 인터페이스 호환
                "has_cooccurrence": True,  # 타겟 재작성에서 우선 처리
                "section_hint":    "[해석]",
                "start":           m.start(),
                "end":             m.end(),
            })
            if len(hedge_blocks) >= 6:
                break

    return hedge_blocks


# ── Phase 15A Track D: Mixed-Tense Residue Check ─────────────────────────────

def _has_mixed_tense_residue(sentence: str, completed_years: list) -> bool:
    """Phase 15A Track D: 교정 후 완료 연도 참조 + 미래형 어간이 공존하는지 확인.

    교정 결과가 진짜로 해결됐는지 엄격하게 판정.
    교정 후에도 "기록할 것으로" 같은 미래형 어간이 남아있으면 True 반환.

    Args:
        sentence:        교정 이후의 문장 (plain text or HTML fragment)
        completed_years: 완료 연도 int 목록, 예: [2022, 2023, 2024, 2025]

    Returns:
        True  — 잔여 혼재(mixed) 시제 발견 → 교정 미완료
        False — 잔여 없음 → 교정 완료
    """
    has_completed_year = any(str(cy) + "년" in sentence for cy in completed_years)
    if not has_completed_year:
        return False
    return bool(_P15A_FUTURE_STEM_RE.search(sentence))


# ── Phase 15 Track D: Completed-Year-as-Forecast Detection ───────────────────

def _detect_completed_year_as_forecast(content: str, run_year: int = 2026) -> dict:
    """Phase 15 Track D: 완료 연도 실적이 전망/예상 어미로 서술된 패턴 탐지.

    완료 연도(run_year - 1 이하 연도) + 전망 어미 조합을 탐지한다.
    잠정치·컨센서스·가이던스 문맥은 별도 경고(WARN)로 분류해 자동 교정에서 제외.

    A2: run_year 기준 완료 연도 판단
    D1: 탐지 패턴 — 완료 연도 + 전망 어미

    Returns:
        {
          "violations":   list — clear completed-year-as-forecast violations (FAIL level),
          "warnings":     list — ambiguous / preliminary / consensus cases (WARN),
          "violation_count": int,
          "status":       str — "FAIL" | "WARN" | "PASS",
        }
    """
    import re as _re

    plain = _re.sub(r"<[^>]+>", " ", content)
    # 문장 분리
    sentences = _re.split(r"(?<=[.!?。！？])\s+", plain)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    violations: list = []
    warnings: list   = []

    # 완료 연도 목록 (run_year - 1 이하, 최근 3년만 검사해 오탐 최소화)
    completed_years = [str(y) for y in range(run_year - 3, run_year)]

    for sent in sentences:
        # 완료 연도가 포함된 문장만 검사
        year_in_sent = None
        for cy in completed_years:
            if cy + "년" in sent:
                year_in_sent = cy
                break
        if year_in_sent is None:
            continue

        # 잠정치·컨센서스·가이던스 문맥 → WARN (자동 교정 제외)
        has_exception_marker = any(m in sent for m in
                                   _P15_PRELIMINARY_MARKERS +
                                   _P15_CONSENSUS_MARKERS +
                                   _P15_GUIDANCE_MARKERS)

        # 전망 어미 탐지
        for fv in _P15_COMPLETED_YEAR_FORECAST_VERBS:
            if fv in sent:
                record = {
                    "sentence":      sent[:150],
                    "year":          year_in_sent,
                    "forecast_verb": fv,
                    "has_exception": has_exception_marker,
                }
                if has_exception_marker:
                    # 예외 마커 있으면 경고만 (컨센서스 참조 등)
                    record["category"] = "COMPLETED_PERIOD_CONSENSUS_REFERENCE"
                    if record not in warnings:
                        warnings.append(record)
                else:
                    record["category"] = "COMPLETED_PERIOD_AS_FORECAST"
                    if record not in violations:
                        violations.append(record)
                break  # 한 문장에 복수 패턴 중복 등록 방지

    violation_count = len(violations)
    status = (
        "FAIL" if violation_count >= 1
        else "WARN" if warnings
        else "PASS"
    )

    if violations:
        logger.warning(
            f"[Phase 15] 완료 연도 전망 어미 위반 {violation_count}건 탐지"
        )
        for v in violations[:5]:
            logger.warning(f"  ⚠ [{v['year']}년] {v['forecast_verb']} → {v['sentence'][:80]}")
    elif warnings:
        logger.info(f"[Phase 15] 컨센서스/잠정 문맥 경고 {len(warnings)}건 (자동 교정 제외)")
    else:
        logger.info("[Phase 15] 완료 연도 시제 이슈 없음")

    return {
        "violations":      violations,
        "warnings":        warnings,
        "violation_count": violation_count,
        "status":          status,
    }


# ── Phase 15 Track E: Targeted Tense Correction ───────────────────────────────

def _enforce_tense_correction(
    content: str,
    run_year: int = 2026,
    label: str = "",
) -> tuple:
    """Phase 15 / 15A Track E: 완료 연도 전망 어미 문장을 확정 사실 어미로 교정.

    E1: 위반 문장 특정 + 대체
    E2: 팩트 의미 보존 (시제 레이블만 변경)
    E3: 잠정치/컨센서스/가이던스 예외 처리 (자동 교정에서 제외)

    Phase 15A 변경사항:
    - Step 0: 전체 컨텐츠에 regex 복합 교정 먼저 적용 (어간+어미 동시 교체)
      → "기록할 것으로 추정됩니다" → "기록한 것으로 집계됐습니다"
    - Step 1: 위반 문장별 리스트 기반 맵 교정 (기존 Phase 15 로직, 잔여 처리)
    - Step 2: _has_mixed_tense_residue()로 교정 후 잔여 혼재 시제 엄격 재검사
      → 잔여 발견 시 경고 로그 기록 (교정 미완으로 처리)

    전략:
    1. Phase 15A regex 복합 교정 (어간+어미 동시) — 전체 컨텐츠 스캔
    2. _detect_completed_year_as_forecast로 위반 문장 재감지
    3. 위반 문장에서 리스트 맵으로 잔여 패턴 교체 (최우선 복합 패턴 먼저)
    4. 교체 후 재탐지 + _has_mixed_tense_residue() 잔여 검사

    Returns:
        (corrected_content: str, correction_log: list)
    """
    completed_years = list(range(run_year - 3, run_year))

    # ── Phase 15A Step 0: Regex 복합 교정 (어간+어미 동시 교체) ─────────────────
    # list 기반 맵보다 먼저 적용하여 "기록할 것으로 추정됩니다" 등 완전 교체
    updated = _P15A_COMPOUND_RE_FORMAL.sub(
        lambda m: m.group(1) + "한" + m.group(2) + "집계됐습니다",
        content,
    )
    updated = _P15A_COMPOUND_RE_INFORMAL.sub(
        lambda m: m.group(1) + "한" + m.group(2) + "집계됐다",
        updated,
    )

    # ── Phase 15B Step 0b: 연결어미 커버 확장 (되며/되고/되어) ───────────────────
    # Phase 15A HOLD 원인: "기록할 것으로 전망되며" — 됩니다/된다 외 미커버
    updated = _P15B_COMPOUND_RE_CONNECTIVE.sub(
        lambda m: m.group(1) + "한" + m.group(2) + "집계" + _P15B_CONNECTIVE_ENDING_MAP[m.group(4)],
        updated,
    )

    regex_changed = updated != content
    if regex_changed:
        logger.info(
            f"[Phase 15A/15B] regex 복합 교정 적용 [{label}] — 어간+어미 동시 교체"
        )

    # ── 위반 재탐지 (regex 이후 잔여 확인) ───────────────────────────────────────
    diag = _detect_completed_year_as_forecast(updated, run_year=run_year)
    if diag["status"] == "PASS":
        if regex_changed:
            logger.info(f"[Phase 15A] regex 교정만으로 완전 해소 [{label}]")
            return updated, [{"label": label, "method": "regex_compound", "status": "resolved"}]
        logger.info(f"[Phase 15] 시제 교정 스킵 [{label}] — 위반 없음")
        return updated, []

    if not diag["violations"]:
        logger.info(f"[Phase 15] 시제 교정 스킵 [{label}] — 명확 위반 없음 (경고만 있음)")
        return updated, []

    correction_log: list = []

    # ── Phase 15 Step 1: 위반 문장별 리스트 맵 교정 ─────────────────────────────
    for v in diag["violations"]:
        original_sent = v["sentence"]
        corrected_sent = original_sent

        # 전망 어미를 확정 어미로 교체 — 복합 패턴 우선 (맵 상단 배치)
        for bad_pattern, good_replacement in _P15_TENSE_CORRECTION_MAP:
            if bad_pattern in corrected_sent:
                corrected_sent = corrected_sent.replace(bad_pattern, good_replacement, 1)

                # ── Phase 15A Step 2: 교정 후 잔여 혼재 시제 엄격 재검사 ─────────
                residue = _has_mixed_tense_residue(corrected_sent, completed_years)
                resolution = "unresolved_residue" if residue else "resolved"
                if residue:
                    logger.warning(
                        f"[Phase 15A] 잔여 혼재 시제 발견 [{label}] "
                        f"— 교정 후에도 미래형 어간 잔존: {corrected_sent[:80]}"
                    )

                correction_log.append({
                    "label":           label,
                    "year":            v["year"],
                    "original":        original_sent[:120],
                    "corrected":       corrected_sent[:120],
                    "replaced_verb":   bad_pattern,
                    "replacement":     good_replacement,
                    "residue_check":   resolution,
                })
                # 전망 어미만 교체 (좁은 범위 교체로 내용 보존, E2)
                updated = updated.replace(bad_pattern, good_replacement, 1)
                break  # 한 문장에 첫 번째 매칭만 교정

    if correction_log or regex_changed:
        logger.info(
            f"[Phase 15/15A] 시제 교정 완료 [{label}] — {len(correction_log)}건 교정"
        )
        # E3: 교정 후 재탐지 (post_correction_recheck)
        post_diag = _detect_completed_year_as_forecast(updated, run_year=run_year)
        remaining = post_diag["violation_count"]
        logger.info(
            f"[Phase 15] 교정 후 재탐지 [{label}] — 잔여 위반 {remaining}건"
        )
        unresolved = [e for e in correction_log if e.get("residue_check") == "unresolved_residue"]
        if unresolved:
            logger.warning(
                f"[Phase 15A] 혼재 시제 잔여 [{label}] — "
                f"{len(unresolved)}건 교정 미완 (교정 맵 확장 필요)"
            )
    else:
        logger.warning(
            f"[Phase 15] 시제 교정 시도했으나 매칭 없음 [{label}] — "
            f"교정 맵에 없는 패턴일 수 있음"
        )

    return updated, correction_log


# ── Phase 15C Track D: Internal Pipeline Label Leakage Detection ──────────────

# 독자 대상 문장에 노출되어서는 안 되는 내부 파이프라인 용어
_P15C_INTERNAL_LABEL_TERMS: list = [
    "Post1의 결론",
    "Post1에서 도출",
    "Post1이 도출",
    "Post1 분석에서",
    "Post1 결론",
    "Post2 기준",
    "Post1에서",
    "Post2에서",
]


def _detect_internal_label_leakage(content: str, label: str = "") -> dict:
    """Phase 15C Track D: Post2 독자 대상 콘텐츠에서 파이프라인 내부 용어 노출 탐지.

    D1: 탐지 대상 — "Post1", "Post2" 등 파이프라인 내부 용어
    D2: HTML 태그를 제거한 plain text에서 탐지
    D3: 탐지 시 FAIL, 미탐지 시 PASS

    Returns:
        {
          "violations":      list — 탐지된 용어 및 문맥,
          "violation_count": int,
          "status":          str — "FAIL" | "PASS",
        }
    """
    import re as _re_label

    plain = _re_label.sub(r"<[^>]+>", " ", content)
    sentences = _re_label.split(r"(?<=[.!?。！？])\s+", plain)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    violations: list = []
    for sent in sentences:
        for term in _P15C_INTERNAL_LABEL_TERMS:
            if term in sent:
                record = {"term": term, "sentence": sent[:150]}
                if record not in violations:
                    violations.append(record)
                break  # 한 문장 중복 등록 방지

    violation_count = len(violations)
    status = "FAIL" if violation_count >= 1 else "PASS"

    if violations:
        logger.warning(
            f"[Phase 15C] 내부 파이프라인 레이블 노출 {violation_count}건 탐지 [{label}]"
        )
        for v in violations[:3]:
            logger.warning(f"  ⚠ [{v['term']}] → {v['sentence'][:80]}")
    else:
        logger.info(f"[Phase 15C] 내부 레이블 노출 없음 [{label}]")

    return {
        "violations":      violations,
        "violation_count": violation_count,
        "status":          status,
    }


# ── Phase 15D: Misapplied [전망] Tag Strip ────────────────────────────────────
# 근본 원인: Step3 Reviser가 확정 실적/집계 데이터 앞에 [전망] 태그(텍스트 접두사)를 주입.
# Phase 15C temporal grounding 프롬프트가 REVISER를 완전히 차단하지 못함.
# 동사 어미(Phase 15A/15B)와 다르게 [전망] 태그는 별도 텍스트 요소 → 별도 교정 계층 필요.

# 확정 실적 동사 패턴 (완료 연도 + 이 어미가 함께 있으면 [전망] 제거 대상)
_P15D_CONFIRMED_VERB_MARKERS: list = [
    "집계됐습니다",
    "집계됐다",
    "집계됐으며",
    "집계됐고",
    "집계됐습",
    "기록한 것으로 집계",
    "집계된 것으로",
    "기록됐습니다",
    "기록됐다",
    "기록됐으며",
    "달성했습니다",
    "달성했다",
    "달성했으며",
    "증가한 것으로",
    "감소한 것으로",
    "상승한 것으로",
    "하락한 것으로",
]


def _strip_misapplied_jeonmang_tags(
    content: str,
    run_year: int = 2026,
    label: str = "",
) -> tuple:
    """Phase 15D (진단 전용): 확정 실적/집계 데이터 앞에 오주입된 [전망] 태그 탐지.

    [전망] 텍스트 태그가 붙은 문장을 검사하여 확정 실적인 경우 경고 로그를 기록한다.
    실제 제거는 발행 직전 일괄 제거 함수에서 처리 (진단 레이어만 유지).

    Returns:
        (content: str, detect_log: list)  # content 미변경
    """
    import re as _re_15d

    detect_log: list = []

    # 완료 연도 문자열
    completed_year_strs = [f"{y}년" for y in range(run_year - 3, run_year)]

    # 발행 기준 확정 과거 월 (run_year의 현재 월 - 1 이하)
    _now_month = datetime.now().month if run_year == datetime.now().year else 12
    confirmed_periods: list = []
    for _m in range(1, _now_month):
        confirmed_periods.append(f"{run_year}년 {_m}월")
        confirmed_periods.append(f"{run_year}년 {str(_m).zfill(2)}월")

    def _is_confirmed_sentence(following_raw: str) -> bool:
        """[전망] 다음 텍스트가 확정 실적 서술인지 판단."""
        plain = _re_15d.sub(r"<[^>]+>", " ", following_raw[:300])
        has_completed_year   = any(cy in plain for cy in completed_year_strs)
        has_confirmed_period = any(cp in plain for cp in confirmed_periods)
        has_confirmed_verb   = any(cv in plain for cv in _P15D_CONFIRMED_VERB_MARKERS)
        return (has_completed_year or has_confirmed_period) and has_confirmed_verb

    JEONMANG_TAG_RE = _re_15d.compile(r"\[전망\]\s*")
    for match in JEONMANG_TAG_RE.finditer(content):
        following = content[match.end():match.end() + 300]
        if _is_confirmed_sentence(following):
            detect_log.append({
                "removed":           match.group(0),
                "following_preview": following[:120],
            })

    detected_count = len(detect_log)
    if detected_count > 0:
        logger.warning(
            f"[Phase 15D] 확정 실적 앞 [전망] 태그 {detected_count}건 탐지 [{label}]"
        )
        for r in detect_log[:5]:
            logger.warning(f"  ⚠ 탐지 → {r['following_preview'][:80]}")
    else:
        logger.info(f"[Phase 15D] [전망] 태그 오주입 없음 [{label}]")

    return content, detect_log


# ── Phase 15E: Current-Year Past-Month Settlement Fix ─────────────────────────
# 근본 원인: Phase 15 감지는 completed_years(run_year-1 이하)만 처리.
# run_year의 이미 종료된 과거 월(예: 3월 발행 시 1월, 2월)은 감지 안 됨.
# Phase 15D는 확정 어미가 이미 교정된 경우에만 [전망] 태그 제거 가능.
# → 2026년 2월 양극재 집계가 "늘어날 것으로 전망됩니다"로 나오면 두 레이어 모두 무효.
#
# Phase 15E 해결:
#   1. 현재 연도 과거 월 + 예측 동사 조합을 새 감지 함수로 탐지
#   2. Phase 15A/15B regex + 신규 NAL 형태 regex로 동사 어미 교정
#   3. 교정 후 [전망] 태그를 현재 연도 과거 월 기준으로 제거

# Phase 15E 확장 regex: "날 것으로 X됩니다/된다/되며/되고/되어" 형태
# 대상: 늘어날, 늘어날 → 늘어난 (어간 "늘어나" + 미래 ㄹ → 과거 ㄴ)
import re as _re_p15e
_P15E_COMPOUND_RE_NAL_FORMAL: "_re_p15e.Pattern" = _re_p15e.compile(
    r"([가-힣]+)날(\s+것으로\s+)(추정|예상|전망|기대|관측)됩니다"
)
_P15E_COMPOUND_RE_NAL_INFORMAL: "_re_p15e.Pattern" = _re_p15e.compile(
    r"([가-힣]+)날(\s+것으로\s+)(추정|예상|전망|기대|관측)된다"
)
_P15E_COMPOUND_RE_NAL_CONNECTIVE: "_re_p15e.Pattern" = _re_p15e.compile(
    r"([가-힣]+)날(\s+것으로\s+)(추정|예상|전망|기대|관측)(되며|되고|되어)"
)

# 현재 연도 과거 월 탐지용 예측 동사 목록 (Phase 15와 동일 기반)
_P15E_FORECAST_VERB_MARKERS: list = [
    "것으로 전망됩니다", "것으로 전망된다", "것으로 전망되며", "것으로 전망되고",
    "것으로 추정됩니다", "것으로 추정된다", "것으로 추정되며", "것으로 추정되고",
    "것으로 예상됩니다", "것으로 예상된다", "것으로 예상되며", "것으로 예상되고",
    "것으로 기대됩니다", "것으로 기대된다", "것으로 기대되며", "것으로 기대되고",
    "것으로 관측됩니다", "것으로 관측된다",
    "전망됩니다", "전망된다", "전망되며",
    "추정됩니다", "추정된다", "추정되며",
    "늘어날 것으로", "증가할 것으로", "기록할 것으로", "달성할 것으로",
    "상승할 것으로", "하락할 것으로", "감소할 것으로",
]


def _detect_current_year_past_month_as_forecast(
    content: str,
    run_year: int = 2026,
    run_month: int = None,
) -> dict:
    """Phase 15E Track A/C: 현재 연도 과거 월 집계 데이터가 예측 어미로 서술된 문장 탐지.

    Phase 15 감지 로직의 커버리지 공백:
      - _detect_completed_year_as_forecast: completed_years(run_year-1 이하)만 처리
      - run_year의 이미 종료된 과거 월은 미처리

    탐지 기준:
      - 현재 연도 + 이미 종료된 월(run_month - 1 이하) 문자열 포함
      - 예측 동사 패턴 포함

    Returns:
        {
          "violations": list,
          "violation_count": int,
          "status": "FAIL" | "PASS",
          "settled_periods": list,
        }
    """
    import re as _re_15e

    if run_month is None:
        run_month = datetime.now().month

    if run_month <= 1:
        return {"violations": [], "violation_count": 0, "status": "PASS", "settled_periods": []}

    # 현재 연도 확정 과거 월 패턴
    settled_periods: list = []
    for _m in range(1, run_month):
        settled_periods.append(f"{run_year}년 {_m}월")
        settled_periods.append(f"{run_year}년 {str(_m).zfill(2)}월")

    plain = _re_15e.sub(r"<[^>]+>", " ", content)
    sentences = _re_15e.split(r"(?<=[.!?。！？])\s+", plain)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    violations: list = []
    for sent in sentences:
        has_settled = any(sp in sent for sp in settled_periods)
        if not has_settled:
            continue
        for fv in _P15E_FORECAST_VERB_MARKERS:
            if fv in sent:
                record = {"sentence": sent[:150], "forecast_marker": fv}
                if record not in violations:
                    violations.append(record)
                break

    violation_count = len(violations)
    status = "FAIL" if violation_count >= 1 else "PASS"

    if violations:
        logger.warning(
            f"[Phase 15E] 현재 연도 과거 월 예측 어미 위반 {violation_count}건 탐지"
        )
        for v in violations[:3]:
            logger.warning(f"  ⚠ {v['forecast_marker']} → {v['sentence'][:80]}")
    else:
        logger.info("[Phase 15E] 현재 연도 과거 월 시제 이슈 없음")

    return {
        "violations": violations,
        "violation_count": violation_count,
        "status": status,
        "settled_periods": settled_periods,
    }


def _enforce_current_year_month_settlement(
    content: str,
    run_year: int = 2026,
    run_month: int = None,
    label: str = "",
) -> tuple:
    """Phase 15E (진단 전용): 현재 연도 과거 월 예측 어미 / [전망] 태그 탐지.

    Phase 15D와의 차이:
      - Phase 15D: 완료 연도 + 확정 어미 조합 탐지
      - Phase 15E: 현재 연도 과거 월 + 예측 동사 조합 탐지

    실제 교정은 발행 직전 일괄 제거 함수에서 처리 (진단 레이어만 유지).

    Returns:
        (content: str, diag_log: list)  # content 미변경
    """
    if run_month is None:
        run_month = datetime.now().month

    diag = _detect_current_year_past_month_as_forecast(
        content, run_year=run_year, run_month=run_month
    )

    if diag["status"] == "PASS":
        logger.info(f"[Phase 15E] 교정 불필요 [{label}]")
        return content, []

    logger.warning(
        f"[Phase 15E] 현재 연도 과거 월 위반 {diag['violation_count']}건 탐지 [{label}]"
        f" (진단 전용 — 발행 직전 일괄 제거에서 처리)"
    )
    return content, [{"verb_violations": diag["violation_count"], "tag_stripped": 0}]


# ── Phase 16: Temporal State Normalization — SSOT Layer ───────────────────────
# 근본 원인: Phase 15A~15E의 패턴 패치 반복 — GPT, Gemini Step3, 후처리가 각자 시간/시제를
#   독립적으로 재해석 → 새로운 표면 형태가 나올 때마다 패치 추가 필요
# 해결: 런타임에 단일 시제 상태 SSOT를 구축하고 모든 하위 레이어(GPT 생성, Gemini Step3,
#   후처리 교정)에 주입하여 시제 상태를 중앙 집중 제어

_P16_TEMPORAL_STATES: dict = {
    "ACTUAL_SETTLED": {
        "description": "확정 완료된 실적 (완전히 종료된 회계연도 / 보고된 기간)",
        "allow_forecast_tag": False,
        "require_past_factual": True,
    },
    "ACTUAL_PRELIMINARY": {
        "description": "잠정 발표된 실적 (잠정치, provisional)",
        "allow_forecast_tag": False,
        "require_past_factual": False,
        "allow_provisional_framing": True,
    },
    "CONSENSUS_REFERENCE": {
        "description": "시장 컨센서스 / 예상치 (애널리스트 전망 참조용)",
        "allow_forecast_tag": True,
        "require_past_factual": False,
        "note": "확정 결과와 별도 레이어로 유지",
    },
    "COMPANY_GUIDANCE": {
        "description": "회사 가이던스 / 경영 목표",
        "allow_forecast_tag": True,
        "require_past_factual": False,
        "note": "달성 확정치로 재작성 금지",
    },
    "FORECAST": {
        "description": "전망 / 추정 / 미래 기간 예측",
        "allow_forecast_tag": True,
        "require_past_factual": False,
    },
    "AMBIGUOUS_TEMPORAL_STATE": {
        "description": "시제 불명확 — 맥락 추가 검토 필요",
        "allow_forecast_tag": None,
        "require_past_factual": None,
        "note": "WARN 로그 대상",
    },
}

# 잠정치 마커 (ACTUAL_PRELIMINARY 판별용)
_P16_PRELIMINARY_MARKERS: list = [
    "잠정", "잠정치", "잠정 집계", "provisional", "preliminary",
    "잠정 기준", "예비", "잠정 발표",
]

# 컨센서스 마커 (CONSENSUS_REFERENCE 판별용)
_P16_CONSENSUS_MARKERS: list = [
    "컨센서스", "시장 전망", "시장 예상", "애널리스트", "전망치",
    "예상치", "consensus", "analyst estimate", "market expectation",
    "시장이 예상", "증권사 추정", "전망 평균",
]

# 회사 가이던스 마커 (COMPANY_GUIDANCE 판별용)
_P16_GUIDANCE_MARKERS: list = [
    "가이던스", "경영 목표", "회사 목표", "guidance", "management target",
    "목표치", "연간 목표", "목표 매출", "목표 영업이익",
    "회사 측 전망", "자사 가이던스",
]

# 순수 미래 동사 — 이 동사가 있으면 [전망] 보존 (Phase 15F 예외 처리용)
_P16_PURE_FUTURE_VERBS: list = [
    "될 것", "할 것", "예상된다", "전망된다", "예상됩니다", "전망됩니다",
    "될 전망", "증가할", "확대될", "개선될", "상승할", "하락할",
    "기대된다", "기대됩니다", "예정이다", "예정입니다",
]


def _build_temporal_ssot(run_year: int, run_month: int) -> dict:
    """Phase 16: 런타임 시제 상태 SSOT를 구축한다.

    run_year, run_month 기준으로 각 시간 범위의 시제 상태를 정규화하여 반환한다.
    반환된 dict는 GPT 생성 블록, Gemini Step3 블록, 후처리 교정에서 공유 SSOT로 사용된다.

    Returns:
        {
            "run_year": int,
            "run_month": int,
            "completed_years": list[int],           완전히 종료된 연도
            "current_year": int,                    현재 진행 중인 연도
            "completed_months_this_year": list[int], 현재 연도의 완료된 월
            "open_month": int,                      현재 열려있는 월
            "year_states": dict,                    연도별 SSOT 상태
            "period_rules": dict,                   기간별 언어 규칙 요약
            "states": dict,                         상태 정의 참조
        }
    """
    completed_years = [run_year - 1, run_year - 2]
    completed_months_this_year = list(range(1, run_month))  # run_month는 아직 열린 상태

    year_states: dict = {}
    for yr in completed_years:
        year_states[yr] = "ACTUAL_SETTLED"
    year_states[run_year] = "CURRENT_OPEN"

    period_rules: dict = {
        "completed_year": {
            "status": "ACTUAL_SETTLED",
            "allow_forecast_tag": False,
            "require_past_factual": True,
            "example": f"{run_year - 1}년 연간 실적 → 확정 사실 → [전망] 금지",
        },
        "current_year_past_month": {
            "status": "ACTUAL_SETTLED",
            "allow_forecast_tag": False,
            "require_past_factual": True,
            "example": (
                f"{run_year}년 1~{run_month - 1}월 보고된 수치 → 완료 사실 → [전망] 금지"
                if run_month > 1 else f"{run_year}년 — 아직 1월 시작"
            ),
        },
        "current_month": {
            "status": "AMBIGUOUS_TEMPORAL_STATE",
            "allow_forecast_tag": None,
            "note": f"{run_year}년 {run_month}월 — 진행 중, 맥락 판단 필요",
        },
        "future_period": {
            "status": "FORECAST",
            "allow_forecast_tag": True,
            "example": "미래 분기/연도 → [전망] 허용",
        },
        "preliminary": {
            "status": "ACTUAL_PRELIMINARY",
            "allow_forecast_tag": False,
            "note": "잠정치 — 조건부 표현 허용, 미래 전망으로 재해석 금지",
        },
        "consensus": {
            "status": "CONSENSUS_REFERENCE",
            "allow_forecast_tag": True,
            "note": "시장 컨센서스 — 확정 실적과 별도 레이어 유지",
        },
        "guidance": {
            "status": "COMPANY_GUIDANCE",
            "allow_forecast_tag": True,
            "note": "가이던스 — 달성 확정치로 재작성 금지",
        },
    }

    return {
        "run_year": run_year,
        "run_month": run_month,
        "completed_years": completed_years,
        "current_year": run_year,
        "completed_months_this_year": completed_months_this_year,
        "open_month": run_month,
        "year_states": year_states,
        "period_rules": period_rules,
        "states": _P16_TEMPORAL_STATES,
    }


def _build_p16_generation_block(ssot: dict) -> str:
    """Phase 16: GPT 생성 단계에 주입할 시제 SSOT 컨텍스트 블록을 구축한다.

    context_text 앞에 prepend되어 GPT가 시간/시제를 독립 재해석하지 않도록 한다.
    """
    run_year = ssot["run_year"]
    run_month = ssot["run_month"]
    completed_years = ssot["completed_years"]
    completed_months = ssot["completed_months_this_year"]

    completed_years_str = ", ".join(f"{yr}년" for yr in sorted(completed_years, reverse=True))
    completed_months_str = (
        ", ".join(f"{m}월" for m in completed_months)
        if completed_months else "없음 (1월 기준)"
    )

    lines = [
        "[Phase 16 — 시제 상태 SSOT ★ GPT 생성 최우선 적용]",
        "",
        f"현재 발행 기준: {run_year}년 {run_month}월",
        "",
        f"■ 확정 완료 연도 (ACTUAL_SETTLED) — [전망] 절대 금지, 과거 확정 표현 필수:",
        f"  {completed_years_str} 의 연간 실적·수치는 모두 확정된 사실입니다.",
        "",
        f"■ 현재 연도({run_year}년) 완료 월 (ACTUAL_SETTLED) — [전망] 금지:",
        f"  {run_year}년 {completed_months_str} 의 보고된 수치는 완료 사실입니다.",
        "",
        f"■ 현재 진행 월 ({run_year}년 {run_month}월) — 보고된 수치는 사실, 미보고 예측은 [전망]",
        "",
        "■ 잠정치 (ACTUAL_PRELIMINARY): '잠정' 표기 수치 — 조건부 표현 허용, 미래 전망 재해석 금지",
        "■ 컨센서스 (CONSENSUS_REFERENCE): 애널리스트 예상치 — 확정 실적과 혼동 금지",
        "■ 가이던스 (COMPANY_GUIDANCE): 회사 목표/가이던스 — 달성 완료로 표현 금지",
        "■ 전망 (FORECAST): 미래 기간 수치만 [전망] 태그 허용",
        "",
        "★ 절대 금지:",
        f"  ❌ {completed_years_str} 확정 실적에 [전망] 태그 부착",
        f"  ❌ {run_year}년 {completed_months_str} 완료 월 수치에 [전망] 태그 부착",
        "  ❌ 확정 어미를 전망 어미로 변환",
        "  ❌ 잠정치를 달성 확정치로 업그레이드",
        "  ❌ 컨센서스를 직접 실적으로 표현",
        "",
    ]

    return "\n".join(lines) + "\n\n"


def _build_p16_step3_block(ssot: dict) -> str:
    """Phase 16: Gemini Step3 시스템 프롬프트에 주입할 시제 SSOT 블록을 구축한다.

    기존 _P15C_STEP3_TEMPORAL_GROUNDING (정적 하드코딩)을 대체한다.
    run_year / run_month 기반 동적 생성으로 연도 고정 문제를 해결한다.
    """
    run_year = ssot["run_year"]
    run_month = ssot["run_month"]
    completed_years = ssot["completed_years"]
    completed_months = ssot["completed_months_this_year"]

    completed_years_str = " / ".join(f"{yr}년" for yr in sorted(completed_years, reverse=True))
    completed_months_str = (
        ", ".join(f"{m}월" for m in completed_months)
        if completed_months else "없음 (1월 기준)"
    )

    lines = [
        "[Phase 16 — Step3 발행 기준 시제 SSOT ★ 최우선 적용]",
        "",
        f"이 콘텐츠의 발행 기준: {run_year}년 {run_month}월",
        "",
        f"완료 기간 분류 ({run_year}년 {run_month}월 발행 기준):",
        f"  ■ {completed_years_str} = 완전히 종료된 회계연도 → 연간 실적은 ACTUAL_SETTLED",
        f"  ■ {run_year}년 {completed_months_str} = 완료된 월 → 보고 수치는 ACTUAL_SETTLED",
        f"  ■ {run_year}년 {run_month}월 이후 기간 = 아직 열린 기간 → 전망 표현 허용",
        "",
        "SSOT 시제 상태별 Step3 행동 규칙:",
        "  ACTUAL_SETTLED      → [전망] 금지 / 확정 어미 보존 / 전망 어미 변환 금지",
        "  ACTUAL_PRELIMINARY  → 잠정 표현 허용 / 확정 표현으로 업그레이드 금지",
        "  CONSENSUS_REFERENCE → 컨센서스임을 명시 / 실적과 혼동 금지",
        "  COMPANY_GUIDANCE    → 가이던스임을 유지 / 달성 확정치로 재작성 금지",
        "  FORECAST            → [전망] 태그 및 조건부 어미 허용",
        "  AMBIGUOUS           → 현 콘텐츠 맥락 기준 판단, WARN 수준 처리",
        "",
        "★ Step3 절대 금지 행동:",
        f"  ❌ {completed_years_str} 확정 실적 문장에 [전망] 태그 추가",
        f"  ❌ {run_year}년 {completed_months_str} 완료 월 수치를 전망으로 재해석",
        "  ❌ 확정 어미(기록했다/달성했다/집계됐다/기록됐다)를 전망 어미로 변환",
        "  ❌ '단정적 표현'이라는 이유로 ACTUAL_SETTLED 문장 수정",
        "  ❌ 잠정치를 완전 확정치처럼 표현",
        "  ❌ 컨센서스를 직접 실적으로 기술",
        "",
        "★ Step3 허용 행동:",
        "  ✅ 이미 올바르게 과거형으로 서술된 ACTUAL_SETTLED 문장 원문 보존",
        "  ✅ 미래 기간 전망 문장에 [전망] 유지 / 추가",
        "  ✅ 잠정치 문장에 '잠정' 표기 유지",
        "  ✅ 가이던스 문장에 조건부 표현 유지",
        "",
    ]

    return "\n".join(lines)


def _strip_current_year_past_month_jeonmang(
    content: str, ssot: dict, label: str = "Post"
) -> tuple:
    """Phase 15F (진단 전용): 현재 연도 과거 월 + [전망] 태그 조합 탐지.

    Phase 15D/15E가 동사 마커 기반으로 탐지하는 것과 달리,
    이 함수는 '현재 연도 + 완료된 월' 기간 표현에 [전망]이 붙은 경우를
    동사형에 관계없이 탐지한다.

    단, 순수 미래형 동사(_P16_PURE_FUTURE_VERBS)가 뒤따를 경우 탐지에서 제외한다.

    실제 제거는 발행 직전 일괄 제거 함수에서 처리 (진단 레이어만 유지).

    Args:
        content: 처리할 HTML 문자열
        ssot: _build_temporal_ssot()가 반환한 SSOT dict
        label: 로그 레이블 (Post1 / Post2)

    Returns:
        (content: str, detect_log: list[dict])  # content 미변경
    """
    import re as _re

    run_year = ssot["run_year"]
    completed_months = ssot["completed_months_this_year"]

    if not completed_months:
        logger.info(f"[Phase 15F] {label}: 완료 월 없음 (1월 기준) — 처리 스킵")
        return content, []

    detect_log = []

    month_pattern_parts = "|".join(str(m) for m in completed_months)
    pattern_str = (
        r'\[전망\]'
        r'(?P<gap>[^\S\r\n]{0,5})'
        r'(?P<year_month>'
        + str(run_year) + r'년\s*(?:' + month_pattern_parts + r')월'
        + r')'
    )

    for m in _re.finditer(pattern_str, content):
        start = m.start()
        end = m.end()
        lookahead_window = content[end:end + 60]
        has_future_verb = any(fv in lookahead_window for fv in _P16_PURE_FUTURE_VERBS)
        if has_future_verb:
            logger.debug(
                f"[Phase 15F] {label}: 미래 동사 감지 → [전망] 보존 | "
                f"{content[start:end + 30][:60]}"
            )
            continue
        preview = content[max(0, start - 20):end + 40]
        detect_log.append({
            "pattern":    m.group(),
            "year_month": m.group("year_month"),
            "preview":    preview,
        })

    if detect_log:
        logger.warning(
            f"[Phase 15F] {label}: 현재 연도 과거 월 [전망] 탐지 {len(detect_log)}건"
        )
        for entry in detect_log[:3]:
            logger.warning(f"  ⚠ P15F 탐지 → {entry['preview'][:80]}")
    else:
        logger.info(f"[Phase 15F] {label}: 현재 연도 과거 월 [전망] 위반 없음")

    return content, detect_log


# ── Phase 16B: Output Quality Hardening ──────────────────────────────────────
# 목적: Phase 16A SSOT 성과를 회귀 없이 유지하면서
#   1) Step3 timeout/503 → 품질 급락 방지 (Track A)
#   2) Post1/Post2 도입부 n-gram 중복 감소 (Track B)
#   3) Generic wording·analytical spine 진단 강화 (Track C)
#   4) Premium editorial tone 복구 지침 (Track D)
#   5) Temporal SSOT 비회귀 보호 (Track E)
#   6) 이후 16C~16E 미세조정을 위한 진단 가시성 (Track F)

# ─── Track C/D: Generic Wording + Premium Tone — GPT 공통 주입 블록 ───────────
_P16B_QUALITY_HARDENING_RULES: str = (
    "[Phase 16B — 품질 하드닝 ★ GPT 생성 적용]\n\n"
    "■ Generic/Bland 문장 금지:\n"
    "  ❌ 수치·근거 없이 '주목됩니다', '기대됩니다', '기대감을 높이고 있습니다' 단독 사용\n"
    "  ❌ '이러한 흐름은', '이러한 상황에서', '이러한 변화는' 류의 무의미 연결 표현\n"
    "  ❌ 사실 나열 후 해석 없이 문단 종료\n"
    "  ❌ 'X가 Y에 긍정적인 영향을 미칠 수 있습니다' — 왜·어떻게가 빠진 빈 인과 문장\n\n"
    "■ Analytical Spine 유지:\n"
    "  ✅ 모든 핵심 주장: [사실] → [해석] → [변수] → [반론] 흐름\n"
    "  ✅ 수치는 단독 나열 금지, 반드시 시장 의미 해석과 결합\n"
    "  ✅ Why-Now 프레임: 이 사실이 지금 중요한 이유를 명시할 것\n"
    "  ✅ 인과 연결: '때문에', '결과', '영향' 대신 구체적 메커니즘 서술\n\n"
    "■ Premium Editorial Tone:\n"
    "  ✅ 고요하고 확신 있는 어조 — 과장 없이 정확하게\n"
    "  ✅ 재무 전문 언어 — Sell-side 보고서 수준 이상\n"
    "  ❌ 연극적 비유, 과도한 수사, 독자 감정 호소\n"
    "  ❌ '투자자들의 주목을 받고 있습니다' 같은 관찰 빈 문장\n\n"
)

# ─── Track B: Post2 도입부 차별화 — gpt_write_picks 전용 주입 블록 ─────────────
_P16B_POST2_ANGLE_DIVERSIFICATION: str = (
    "[Phase 16B — Post2 도입부 차별화 ★ 최우선]\n\n"
    "Post2([캐시의 픽])의 도입부는 반드시 Post1([심층분석])과 다른 각도에서 열어야 합니다.\n\n"
    "❌ 금지:\n"
    "  - Post1이 사용한 은유/비유를 그대로 반복\n"
    "  - Post1의 첫 문장 또는 첫 단락 테마를 동일하게 재서술\n"
    "  - '오늘의 테마는 X와 Y입니다' 형식의 단순 테마 나열로 시작\n"
    "  - Post1 도입부에서 사용한 3어절 이상 연속 표현 재사용\n\n"
    "✅ 권장:\n"
    "  - 투자자 관점: '왜 지금 이 종목인가?' 각도로 직접 시작\n"
    "  - 구체적 수치·가격 움직임·기술 변화로 直入\n"
    "  - Post1이 '현상'을 설명했다면 Post2는 '선택'으로 시작\n"
    "  - 도입부 첫 문장은 선정 종목과 연결되어야 함\n\n"
)

# ─── Phase 16D Track A: Post2 매크로 배경 재서술 억제 ────────────────────────────
_P16D_POST2_CONTINUITY_HARDENING: str = (
    "[Phase 16D — Post2 매크로 재서술 억제 ★]\n\n"
    "Post2([캐시의 픽])에서 '오늘 이 테마를 보는 이유' 또는 유사 섹션을 작성할 때:\n\n"
    "❌ 금지:\n"
    "  - Post1([심층분석])이 이미 서술한 거시 배경(호르무즈 해협 수치, 브렌트유 가격,\n"
    "    FOMC 결정 내용, 달러 강세 등)을 같은 분량으로 다시 설명\n"
    "  - '중동 전쟁이 X주 차에 접어들며...' / 'Y 해협 통행량이 Z% 급감...' 류의\n"
    "    사건 경위 재서술\n"
    "  - 거시 배경 단독 설명 문단이 2문장을 초과\n\n"
    "✅ 필수:\n"
    "  - 매크로 사실은 1~2문장 이내 요약으로만 참조하고,\n"
    "    즉시 '그렇다면 어떤 종목/섹터가 이 흐름에서 포지셔닝 기회를 갖는가?'로 전환\n"
    "  - 섹션 첫 문장부터 종목 바스켓 또는 투자 각도를 명시\n\n"
)

# ─── Phase 16D Track B: Post2 픽-테마 브릿지 강제 ───────────────────────────────
# Phase 16F Track A: 브릿지-픽 정합성 보강 (Phase 16E 피드백 반영)
# 16E에서 "에너지 vs 기술 섹터" 대비형 브릿지가 생성됐으나 실제 픽이 모두 에너지인 케이스 발생
# → 대비형 브릿지 조건 명시, 동일 섹터 픽 시 좁은 공통 논리 브릿지 강제
_P16D_POST2_BRIDGE_REQUIREMENT: str = (
    "[Phase 16D/16F — 픽-테마 브릿지 강제 ★ 픽 정합성 필수]\n\n"
    "종목 개별 섹션(메인 픽 / 보조 픽)을 시작하기 직전에,\n"
    "'왜 이 종목들이 오늘의 매크로 국면에서 한 바구니에 담겼는가'를\n"
    "1~2문장으로 설명하는 브릿지 문장을 반드시 포함하라.\n\n"
    "브릿지 작성 필수 원칙 (픽 정합성):\n"
    "  ★ 브릿지는 반드시 아래 메시지에 명시된 최종 선정 종목 리스트의\n"
    "    실제 공통 속성에만 기반해야 한다.\n"
    "  ★ '섹터 A vs 섹터 B' 대비형 브릿지는 실제로 양쪽 섹터에 모두 픽이 있을 때만 사용하라.\n"
    "    픽이 모두 같은 섹터에 속하면 대비형 축은 절대 쓰지 말라.\n"
    "  ★ 공통 논리가 뚜렷하지 않으면 과장하지 말고 '같은 방향의 직접 수혜'처럼\n"
    "    더 좁고 안전한 표현으로 쓰라.\n\n"
    "브릿지 유형 가이드:\n"
    "  [동일 섹터 픽] → 공통 수혜 논리 / 공통 민감도 / 헤지 구조 차이로 묶어라\n"
    "  [이종 섹터 픽] → 오늘 매크로 국면에서 두 섹터를 동시에 보는 이유를 1문장으로 연결하라\n"
    "  [단일 픽]      → 픽-테마 연결 한 문장으로 충분하다\n\n"
    "❌ 금지:\n"
    "  - 픽 바스켓에 없는 섹터를 브릿지에서 언급\n"
    "  - 'X, Y, Z를 함께 봅니다' 식의 단순 나열\n"
    "  - 픽 확정 전 가상 후보군 기준으로 브릿지를 생성하는 것\n\n"
)

# ─── Phase 17 Track A: Post2 opener pick-angle 강제 ─────────────────────────────
# Phase 17 핵심 변경: Post2 opener를 theme explainer → pick-angle opener로 전환
# "오늘 이 테마를 보는 이유" 섹션 완전 폐기 → "왜 지금 {픽/섹터}인가" 구조로 교체
_P17_POST2_OPENER_ENFORCEMENT: str = (
    "[Phase 17 — Post2 opener pick-angle 강제 ★★ 최우선]\n\n"
    "Post2([캐시의 픽])의 세 번째 섹션(H3)은 반드시 픽 각도 진입형으로 작성한다.\n\n"
    "★ H3 생성 규칙:\n"
    "  - 메인 픽명 또는 핵심 섹터명을 H3에 직접 포함한다.\n"
    "  - generic fallback H3는 절대 금지한다.\n\n"
    "❌ H3 금지 패턴:\n"
    "  - '오늘 이 테마를 보는 이유'\n"
    "  - '오늘 시장을 보는 이유'\n"
    "  - '최근 거시 환경을 먼저 보면'\n"
    "  - '글로벌 매크로 흐름을 먼저 정리하면'\n"
    "  - '이번 시장 변수는'\n"
    "  - '최근 변동성이 커지면서'\n\n"
    "✅ H3 허용 패턴:\n"
    "  - '왜 지금 {메인 픽}인가'\n"
    "  - '{메인 픽}을 먼저 봐야 하는 이유'\n"
    "  - '이번 변수에서 먼저 봐야 할 {핵심 섹터}'\n"
    "  - '지금 시장이 {메인 픽}에 묻는 질문'\n"
    "  - '오늘 테마보다 먼저 확인할 {핵심 종목}'\n\n"
    "★ opener 첫 문장 강제 규칙:\n"
    "  - 첫 문장은 메인 픽 또는 핵심 섹터명을 반드시 포함한다.\n"
    "  - 첫 문장은 거시 배경(금리/환율/유가/불확실성) 재서술로 시작하면 안 된다.\n"
    "  - 첫 문장에 수주/판가/재고/CAPEX/정책 수혜/실적 민감도/가격 전가력 중\n"
    "    핵심 변수 1개 이상을 반드시 제시해야 한다.\n"
    "  - '불확실성이 커졌다', '변동성이 확대됐다' 같은 범용 문장 단독 시작 금지.\n"
    "  - 첫 문장과 둘째 문장 안에 메인 픽/핵심 섹터명이 모두 빠지는 구성 금지.\n\n"
    "✅ 권장 첫 문장 패턴:\n"
    "  - '{메인 픽}은 이번 변수에서 {핵심 변수} 해석이 먼저 붙는 종목이다.'\n"
    "  - '이번 테마에서 먼저 봐야 할 것은 시장 전체보다 {핵심 섹터}의 {핵심 변수}다.'\n"
    "  - '{메인 픽}은 단순 테마 수혜보다 {실적/수주/가격 전가력/정책 연결}이 핵심이다.'\n\n"
    "★ Post1 역할 중복 금지:\n"
    "  - Post1이 이미 제공한 시장 컨텍스트를 Post2 opener가 길게 반복하지 않는다.\n"
    "  - 거시 배경 설명은 opener 첫 문장 이후 또는 다음 문단으로 배치한다.\n\n"
)

# ─── Phase 16J Track B: 동일 theme 연속 슬롯 시 Post2 opener 강화 ───────────────
_P16J_POST2_SAME_THEME_OPENER: str = (
    "[Phase 16J — 동일 매크로 테마 연속 실행 감지: Post2 도입부 각도 강제 ★★]\n\n"
    "이번 슬롯은 직전 슬롯(들)과 동일한 거시 테마로 진행됩니다.\n"
    "Post2([캐시의 픽])의 첫 2~3문단은 반드시 아래 세 각도 중 하나로 열어야 합니다:\n\n"
    "  ① 픽 바스켓의 공통 민감도: '이 종목들이 같은 방향에 놓인 이유'\n"
    "  ② 왜 이 종목들인가: '같은 테마 중에서도 이 바스켓을 선택한 트리거 논거'\n"
    "  ③ 어떤 트리거에 베팅하는가: '오늘 이 특정 촉매에서 수혜 포지션'\n\n"
    "❌ 절대 금지 (동일 테마 연속 시 추가 제한):\n"
    "  - 매크로 배경을 이전 글과 같은 어휘·문장 구조로 재서술\n"
    "  - '이 테마가 중요한 이유' 식의 거시 설명으로 도입부 시작\n"
    "  - Post1 도입부와 유사한 흐름으로 같은 국면 설명 반복\n\n"
    "✅ 필수: 첫 문장부터 종목 선택의 논리 또는 투자 각도를 직접 제시하라.\n\n"
)

# ─── Track A: Step3 실패 시 diagnostic용 generic 마커 목록 ─────────────────────
_P16B_GENERIC_MARKERS: list = [
    "이러한 흐름은",
    "이러한 상황에서",
    "이러한 변화는",
    "주목됩니다",
    "기대됩니다",
    "관심이 집중되고 있습니다",
    "주의가 필요합니다",
    "모니터링이 필요합니다",
    "긍정적으로 평가됩니다",
    "투자자들의 주목을 받고 있습니다",
    "시장에서 주목받고 있습니다",
    "이목이 집중되고 있습니다",
    "확인이 필요합니다",
    "필요가 있습니다",
    "영향을 미칠 수 있습니다",
]

# ─── Phase 16H Track A: Post1 hedge 절제 지침 ───────────────────────────────
# 16G 실출력 진단 결과 Post1 헤징 비율 52%(13/25문장)로 FAIL — Phase 14I의
# [해석] 블록 기반 재작성이 [해석] 태그 미노출로 0건 추출 → 효과 없음.
# 프롬프트 레벨에서 factual vs interpretive 문장 구분 지침을 직접 주입.
_P16H_POST1_HEDGE_REDUCTION: str = (
    "[Phase 16H — Post1 사실 구간 헤징 절제 ★]\n\n"
    "확정된 사실·수치 문장(factual spine)에는 유보형 어미를 쓰지 말라.\n\n"
    "판단 기준:\n"
    "  [사실 구간] 이미 발생한 사건, 확정 수치, 과거 공식 발표\n"
    "    → '~했다', '~이다', '~기록했다', '~결정했다' 등 단정형 사용\n"
    "    → ❌ '~것으로 보입니다', '~것으로 추정됩니다', '~것으로 파악됩니다' 금지\n\n"
    "  [해석/전망 구간] 인과 추론, 미래 예측, 시나리오 서술\n"
    "    → 필요한 만큼만 유보형 허용: '~로 판단된다', '~가능성이 높다'\n"
    "    → 단, 전체 문장의 절반 이상을 유보형으로 끝내면 안 된다\n\n"
    "목표: 분석 spine은 자신감 있게, 불확실성은 해석 구간에만 국소 표현.\n"
    "premium editorial tone 유지 — 과잉 확신(단정 남발)도 금지.\n\n"
)


def _p16b_emergency_polish(
    content: str, label: str = "Post", step3_status: str = "PASS"
) -> tuple:
    """Phase 16B Track A / Phase 16D Track D: generic wording diagnostic pass.

    Phase 16D: step3_status 파라미터 추가 — 항상 실행하되, 실제 Step3 fallback 상황과
    일반 품질 진단 상황을 구분해 로그에 남긴다 (applied=False 원칙 유지).

    Args:
        content:      GPT 초안 또는 Step3 수정본 HTML
        label:        로그 레이블 (Post1 / Post2)
        step3_status: 현재 Step3 처리 상태 (PASS / REVISED / FAILED_NO_REVISION / PARSE_FAILED).
                      Phase 16F/16J 표준 enum — 로그 컨텍스트로만 사용.
                      ※ 구 보고서(16B/16C)에서 "FAILED_REVISION_ADOPTED"로 표기된 것은
                        코드 기준 "REVISED"와 동일한 상태임 (Phase 16F에서 통일).
                      ※ PARSE_FAILED: Gemini 검수 응답 JSON 파싱 불가 → 검수 skip,
                        GPT 초안 원본 발행. FAILED_NO_REVISION과 달리 수정 시도 없음.

    Returns:
        (content_unchanged: str, polish_log: dict)
    """
    import re as _re

    _tag_strip = _re.compile(r"<[^>]+>")
    plain = _tag_strip.sub(" ", content)

    found_markers = []
    for marker in _P16B_GENERIC_MARKERS:
        count = plain.count(marker)
        if count > 0:
            found_markers.append({"marker": marker, "count": count})

    # Phase 16H Track C: 집계 기준 단일화
    # unique_marker_count = 서로 다른 마커 종류 수
    # total_occurrence_count = 전체 출현 횟수 (unique 마커별 count 합산)
    unique_marker_count = len(found_markers)
    total_occurrence_count = sum(m["count"] for m in found_markers)
    # 집계 기준: total_occurrence_count 기준으로 status 판정 (기존 동일)
    status = "PASS" if total_occurrence_count == 0 else ("WARN" if total_occurrence_count <= 5 else "FAIL")

    # Phase 16D Track D: 항상 관측 가능한 로그 출력 (실행/스킵 여부 + step3 컨텍스트)
    _is_fallback = step3_status == "FAILED_NO_REVISION"
    _mode = "fallback-diagnostic" if _is_fallback else "routine-diagnostic"
    if total_occurrence_count > 0:
        logger.warning(
            # Phase 16H: 로그 형식에 unique_count 및 total_count 모두 명시
            f"[Phase 16B] {label} emergency_polish: "
            f"generic 마커 {unique_marker_count}종 {total_occurrence_count}건 "
            f"| status={status} | mode={_mode} | step3={step3_status}"
        )
        for m in found_markers[:5]:
            logger.warning(f"  ⚠ '{m['marker']}' x{m['count']}")
    else:
        logger.info(
            f"[Phase 16B] {label} emergency_polish: generic 마커 없음 "
            f"| status=PASS | mode={_mode} | step3={step3_status}"
        )

    return content, {
        "applied": False,
        "mode": _mode,
        "step3_status": step3_status,
        # Phase 16H Track C: unique/total 구분 필드 명시 (하위호환: total_generic_found 유지)
        "unique_marker_count":    unique_marker_count,    # 마커 종류 수
        "total_occurrence_count": total_occurrence_count, # 총 출현 횟수
        "total_generic_found":    total_occurrence_count, # 하위호환 유지
        "markers": found_markers,
        "status": status,
        "note": (
            "diagnostic-only — 실 치환 미수행 (Phase 16D 원칙 유지). "
            "집계: unique_marker_count=종류수, total_occurrence_count=총출현수 (Phase 16H 표준)"
        ),
    }


def _p16b_compute_intro_overlap(
    post1_content: str, post2_content: str, n: int = 4, intro_chars: int = 300
) -> dict:
    """Phase 16B Track B: Post1/Post2 도입부 n-gram 중복률 계산.

    각 아티클의 앞 intro_chars자(plain text 기준)에서 n-gram을 추출하고
    겹치는 비율을 반환한다.

    Returns:
        {"overlap_ratio": float, "shared_ngrams": list[str], "status": str,
         "post1_intro": str, "post2_intro": str}
    """
    import re as _re

    _tag_strip = _re.compile(r"<[^>]+>")

    def _get_intro(html: str) -> str:
        plain = _tag_strip.sub(" ", html)
        plain = _re.sub(r"\s+", " ", plain).strip()
        return plain[:intro_chars]

    def _ngrams(text: str, size: int) -> set:
        tokens = list(text)
        if len(tokens) < size:
            return set()
        return {tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}

    p1_intro = _get_intro(post1_content)
    p2_intro = _get_intro(post2_content)
    ng1 = _ngrams(p1_intro, n)
    ng2 = _ngrams(p2_intro, n)

    if not ng1 or not ng2:
        return {
            "overlap_ratio": 0.0,
            "shared_ngrams": [],
            "status": "SKIP",
            "post1_intro": p1_intro[:80],
            "post2_intro": p2_intro[:80],
        }

    shared = ng1 & ng2
    overlap_ratio = len(shared) / max(len(ng1), len(ng2))
    shared_samples = ["".join(ng) for ng in list(shared)[:5]]

    if overlap_ratio < 0.15:
        status = "LOW"
    elif overlap_ratio < 0.30:
        status = "MEDIUM"
    else:
        status = "HIGH"

    # Phase 16D Track C: threshold 기준 명시 + 원인 n-gram 구간 로그
    _thresholds = {"LOW": "<15%", "MEDIUM": "15~30%", "HIGH": "≥30%"}
    logger.info(
        f"[Phase 16B] 도입부 {n}-gram 중복: {overlap_ratio:.1%} ({status}) "
        f"| 공유 n-gram {len(shared)}개 "
        f"| 기준: LOW<15% / MEDIUM<30% / HIGH≥30%"
    )
    if status in ("HIGH", "MEDIUM"):
        logger.warning(
            f"[Phase 16B] 도입부 {status} 중복 감지 "
            f"(임계값: {_thresholds[status]}) "
            f"— 반복 n-gram 샘플: {shared_samples[:5]}"
        )

    return {
        "overlap_ratio": round(overlap_ratio, 4),
        "shared_ngrams": shared_samples,
        "status": status,
        "thresholds": {"LOW": 0.15, "MEDIUM": 0.30, "HIGH": 0.30},
        "intro_chars_used": intro_chars,
        "post1_intro": p1_intro[:80],
        "post2_intro": p2_intro[:80],
    }


def _p16f_diagnose_bridge(content: str, picks: list) -> dict:
    """Phase 16F Track C: Post2 브릿지 타입 진단 (관측 전용, 본문 무수정).

    생성된 Post2 HTML에서 브릿지 섹션 존재 여부와 타입을 감지하고 로그로 남긴다.
    대비형 브릿지("A vs B") 감지 시 picks가 동일 섹터에 몰려 있는지 함께 기록한다.

    Args:
        content: Post2 HTML (최종 본문 적용 후)
        picks:   최종 선정 종목 리스트 (dict 목록, 'sector' 또는 'ticker' 포함)

    Returns:
        {"bridge_found": bool, "bridge_mode": str, "contrast_risk": bool, "note": str}
    """
    import re as _re

    _tag_strip = _re.compile(r"<[^>]+>")
    plain = _tag_strip.sub(" ", content)
    plain = _re.sub(r"\s+", " ", plain)

    # 브릿지 섹션 존재 여부: "오늘 이 테마" 또는 종목 바스켓 설명 패턴
    bridge_keywords = ["오늘 이 테마", "이 종목들을", "함께 담는", "한 바구니", "공통 논리", "공통 수혜"]
    bridge_found = any(kw in plain for kw in bridge_keywords)

    # 대비형 브릿지 감지: "A vs B", "A와 달리", "A 반면 B", "에너지 섹터와 기술"
    contrast_patterns = ["vs ", "와 달리", "반면", "상반된", "에너지 섹터와 기술", "기술 섹터와 에너지"]
    contrast_detected = any(pat in plain[:800] for pat in contrast_patterns)

    # picks의 섹터 다양성 체크 (단순 ticker 수 기반 — 섹터 필드 없으면 스킵)
    tickers = [p.get("ticker", "") for p in (picks or [])]
    pick_count = len(tickers)

    bridge_mode = "NONE"
    if bridge_found:
        bridge_mode = "CONTRAST" if contrast_detected else "COMMON"

    # 대비형 브릿지인데 picks가 1개 이하거나 동일 섹터일 가능성 있으면 contrast_risk=True
    contrast_risk = contrast_detected and pick_count <= 2

    note = (
        f"picks={tickers} | bridge_mode={bridge_mode} | contrast_detected={contrast_detected}"
    )

    log_level = "WARNING" if (bridge_mode == "CONTRAST" and contrast_risk) else "INFO"
    if log_level == "WARNING":
        logger.warning(
            f"[Phase 16F] Post2 브릿지 타입: {bridge_mode} — 대비형 브릿지이나 picks={tickers} "
            f"(동일 섹터 가능성 있음). 브릿지-픽 정합성 확인 필요."
        )
    else:
        logger.info(
            f"[Phase 16F] Post2 브릿지: found={bridge_found} | mode={bridge_mode} | picks={tickers}"
        )

    return {
        "bridge_found": bridge_found,
        "bridge_mode": bridge_mode,
        "contrast_risk": contrast_risk,
        "picks": tickers,
        "note": note,
    }


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
    hedge_overuse_status: str = "",
) -> str:
    """Phase 14I Track C: weak_interpretation FAIL 또는 hedge_overuse FAIL 시 타겟 교체.

    Phase 14I 변경:
    - 트리거 확장: weak_hits >= 3 OR hedge_overuse_status == "FAIL"
    - hedge_overuse FAIL 트리거 시 _extract_hedge_heavy_interp_blocks 우선 사용
    - [해석] 헤징 어미 saturated 블록 → 타겟 교체
    - 교체 후 _detect_interp_hedge_density로 헤징 해소 여부 검증

    Args:
        content:              Phase 13 진단 후 콘텐츠 (HTML)
        weak_interp_hits:     Phase 13 weak_hits 수
        label:                로그 레이블 ("Post1" | "Post2" 등)
        article_spine:        Post1 분석 뼈대 문장 (선택)
        hedge_overuse_status: Phase 13 hedge_overuse 상태 ("FAIL" | "WARN" | "PASS")

    Returns:
        교체 후 콘텐츠 (실패/스킵 시 원본 반환)
    """
    # ── Phase 14I: 트리거 판정 ────────────────────────────────────────────────
    weak_trigger  = weak_interp_hits >= 3
    hedge_trigger = hedge_overuse_status == "FAIL"

    if not weak_trigger and not hedge_trigger:
        logger.info(
            f"[Phase 14I] 재작성 패스 스킵 [{label}] — "
            f"weak_hits={weak_interp_hits} (임계값 3 미만), "
            f"hedge_overuse={hedge_overuse_status or 'N/A'} (FAIL 아님)"
        )
        return content

    reason = []
    if weak_trigger:
        reason.append(f"weak_hits={weak_interp_hits}")
    if hedge_trigger:
        reason.append(f"hedge_overuse=FAIL")
    logger.info(f"[Phase 14I] 타겟 재작성 시작 [{label}] — 트리거: {', '.join(reason)}")

    post_type = "Post1" if "Post1" in label or label.endswith("1") else "Post2"

    # ── Phase 14I: hedge_overuse 트리거 시 [해석] 헤징 블록 우선 추출 ─────────
    if hedge_trigger:
        hedge_diag_before = _detect_interp_hedge_density(content)
        logger.info(
            f"[Phase 14I] [해석] 헤징 진단 [{label}] 전 — "
            f"{hedge_diag_before['interp_hedged']}/{hedge_diag_before['interp_total']} "
            f"({hedge_diag_before['hedge_ratio']*100:.0f}%) status={hedge_diag_before['status']}"
        )
        if hedge_diag_before["bad_lines"]:
            for line in hedge_diag_before["bad_lines"][:3]:
                logger.warning(f"  ⚠ 헤징 어미 감지: {line[:80]}")

        hedge_targets = _extract_hedge_heavy_interp_blocks(content)
        logger.info(
            f"[Phase 14I] [해석] 헤징 블록 추출 [{label}]: {len(hedge_targets)}개"
        )

        if hedge_targets:
            replacements = _rewrite_weak_blocks(
                hedge_targets, article_spine, post_type, f"{label}-hedge"
            )
            if replacements:
                content = _apply_block_replacements(content, replacements, f"{label}-hedge")
                # PICKS 주석 보존
                if "<!-- PICKS:" not in content:
                    pass  # 이미 원본에서 보존됨 (content가 원본 참조)
                # 헤징 재작성 후 재진단
                hedge_diag_after = _detect_interp_hedge_density(content)
                if hedge_diag_after["hedge_ratio"] < hedge_diag_before["hedge_ratio"]:
                    logger.info(
                        f"[Phase 14I] [해석] 헤징 교체 성공 [{label}] — "
                        f"{hedge_diag_before['hedge_ratio']*100:.0f}% → "
                        f"{hedge_diag_after['hedge_ratio']*100:.0f}%"
                    )
                else:
                    logger.warning(
                        f"[Phase 14I] [해석] 헤징 교체 후 비율 불변 [{label}] — "
                        f"{hedge_diag_before['hedge_ratio']*100:.0f}% → "
                        f"{hedge_diag_after['hedge_ratio']*100:.0f}%"
                    )
            else:
                logger.warning(
                    f"[Phase 14I] [해석] 헤징 블록 재작성 결과 없음 [{label}]"
                )

    # ── 기존 weak_interp 타겟 블록 추출 ─────────────────────────────────────
    if weak_trigger:
        targets = _extract_weak_interp_blocks(content)
        logger.info(
            f"[Phase 14H] 타겟 블록 추출 [{label}]: {len(targets)}개 "
            f"(코-오커런스 {sum(1 for t in targets if t.get('has_cooccurrence'))}개)"
        )

        if targets:
            replacements = _rewrite_weak_blocks(targets, article_spine, post_type, label)

            if replacements:
                updated = _apply_block_replacements(content, replacements, label)

                # PICKS 주석 보존
                if "<!-- PICKS:" in content and "<!-- PICKS:" not in updated:
                    picks_match = re.search(r"<!--\s*PICKS:.*?-->", content, re.DOTALL)
                    if picks_match:
                        updated = updated.rstrip() + "\n" + picks_match.group(0)
                        logger.info(f"[Phase 14H] PICKS 주석 복원 [{label}]")

                # re-score 검증
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

        # ── Fallback: 전체 기사 재작성 (기존 Phase 14 방식) ──────────────────
        logger.info(f"[Phase 14] 전체 기사 재작성 폴백 [{label}]")
        pattern_lines = []
        for (kw1, kw2) in _P13_WEAK_INTERP_PATTERNS[:8]:
            import re as _re
            plain = _re.sub(r"<[^>]+>", " ", content)
            if kw1 in plain and kw2 in plain:
                pattern_lines.append(f"- '{kw1}' + '{kw2}' 조합 (교과서 인과 의심)")
        pattern_desc = (
            "\n".join(pattern_lines) if pattern_lines else "- 교과서 인과 패턴 다수 감지"
        )

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

    # hedge_trigger only 경로: 이미 content가 hedge 교체 완료
    return content


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
        # [Phase 23] prompt_tokens_details.cached_tokens — 캐시 히트 토큰 추출
        _cached = 0
        try:
            _cached = response.usage.prompt_tokens_details.cached_tokens or 0
        except AttributeError:
            pass
        cost_tracker.record_openai_usage(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            cached_tokens=_cached,
        )

    return content


def _call_gemini(system: str, user: str, label: str,
                 temperature: float = 0.3,
                 response_mime_type: Optional[str] = None) -> Optional[str]:
    """Gemini 2.5-flash 호출 + 비용 기록. 실패 시 None 반환.

    [Phase 19] response_mime_type 파라미터 추가.
    JSON 응답이 필요한 호출(verifier, planner, 종목선정 등)에
    response_mime_type="application/json" 을 전달하면 Gemini API 레벨에서
    유효한 JSON만 반환되도록 강제한다 — 프롬프트 지시만으로는 불충분한 경우 방어.
    """
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
                f"response_mime_type={response_mime_type!r} "
                f"system_len={len(system)} user_len={len(user)}"
            )

        _config_extra = (
            {"response_mime_type": response_mime_type}
            if response_mime_type else {}
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user.strip(),
            config=genai_types.GenerateContentConfig(
                system_instruction=system.strip(),
                max_output_tokens=3000,
                temperature=temperature,
                thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
                **_config_extra,
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


def _fetch_krx_price(ticker: str) -> Optional[str]:
    """
    pykrx로 한국 종목 최신 종가를 조회합니다. (API 키 불필요)
    반환: '₩84,500 (2026-03-21 기준, KRX)' 또는 None
    """
    import re as _re
    from datetime import datetime, timedelta

    code = _re.sub(r"\.(KS|KQ|KT)$", "", ticker, flags=_re.IGNORECASE)
    if not code.isdigit() or len(code) != 6:
        return None

    try:
        from pykrx import stock
        end_dt   = datetime.now()
        start_dt = end_dt - timedelta(days=7)
        df = stock.get_market_ohlcv(
            start_dt.strftime("%Y%m%d"),
            end_dt.strftime("%Y%m%d"),
            code,
        )
        if df is None or df.empty:
            return None

        close_col = "종가" if "종가" in df.columns else ("Close" if "Close" in df.columns else None)
        if not close_col:
            return None

        price      = float(df[close_col].iloc[-1])
        price_date = df.index[-1].strftime("%Y-%m-%d")
        logger.info(f"pykrx 종가 조회 성공: {ticker} = ₩{price:,.0f}")
        return f"₩{price:,.0f} ({price_date} 기준, KRX)"

    except Exception as e:
        logger.warning(f"pykrx 종가 조회 실패 ({ticker}): {e}")
        return None


def fetch_stock_prices(tickers: list) -> dict:
    """
    티커 리스트의 최신 종가를 조회합니다.
    한국 종목: yfinance → KRX Open API → 네이버금융
    해외 종목: yfinance → 네이버금융
    모두 실패 시: 'N/A' 반환
    """
    prices = {}
    for ticker_str in tickers:
        is_korean = bool(re.search(r"\.(KS|KQ|KT)$", ticker_str, re.IGNORECASE)) or \
                    (ticker_str.isdigit() and len(ticker_str) == 6)
        try:
            t = yf.Ticker(ticker_str)
            hist = t.history(period="1d")
            if not hist.empty:
                price = round(hist["Close"].iloc[-1], 2)
                price_date = hist.index[-1].strftime("%Y-%m-%d")
                prices[ticker_str] = f"₩{price:,.0f} ({price_date} 기준)" if is_korean else f"${price:,.2f} ({price_date} 기준)"
                continue
        except Exception as e:
            logger.warning(f"{ticker_str} yfinance 조회 실패: {e}")

        # 한국 종목: KRX 폴백
        if is_korean:
            logger.info(f"{ticker_str} yfinance N/A → KRX 폴백 시도")
            krx = _fetch_krx_price(ticker_str)
            if krx:
                prices[ticker_str] = krx
                continue

        # 공통 최종 폴백: 네이버금융
        logger.info(f"{ticker_str} → 네이버금융 폴백 시도")
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
    """
    종가 조회 — 다단계 폴백 체인.

    한국 종목 (6자리 숫자 코드 또는 .KS/.KQ 접미사):
      1. yfinance  코드.KS
      2. yfinance  코드.KQ
      3. pykrx (KRX 직접 조회)
      4. 네이버금융 종목 페이지 (/item/main)
      5. 네이버금융 해외주식 페이지 (글로벌 상장 종목 대비)

    미국/글로벌 종목:
      1. yfinance  (원본 티커)
      2. 네이버금융 해외주식 페이지 (.O / .N 접미사)

    모두 실패 시: 'N/A' 반환
    """
    # 한국 종목 판별: 순수 6자리 숫자 or .KS/.KQ/.KT 접미사
    _kr_suffix_re = re.compile(r"\.(KS|KQ|KT)$", re.IGNORECASE)
    raw_code = _kr_suffix_re.sub("", ticker)
    is_korean = raw_code.isdigit() and len(raw_code) == 6

    if is_korean:
        # ── 1. yfinance .KS ──────────────────────────────────────────────
        for suffix in [".KS", ".KQ"]:
            try:
                t = yf.Ticker(raw_code + suffix)
                hist = t.history(period="7d")
                if not hist.empty:
                    price = round(hist["Close"].iloc[-1], 0)
                    date_str = hist.index[-1].strftime("%Y-%m-%d")
                    logger.info(f"[가격] yfinance({suffix}) 성공: {raw_code} = ₩{int(price):,}")
                    return f"₩{int(price):,} ({date_str} 기준)"
            except Exception as e:
                logger.debug(f"[가격] yfinance({raw_code}{suffix}) 실패: {e}")

        # ── 2. pykrx (KRX 직접) ──────────────────────────────────────────
        krx = _fetch_krx_price(raw_code)
        if krx:
            return krx

        # ── 3. 네이버금융 종목 페이지 (/item/main) ────────────────────────
        try:
            url = f"https://finance.naver.com/item/main.nhn?code={raw_code}"
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
                ),
                "Referer": "https://finance.naver.com/",
            }
            resp = requests.get(url, headers=headers, timeout=8)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")
            price_elem = (
                soup.select_one(".today .blind")
                or soup.select_one("p.no_today em")
                or soup.select_one("#chart_area .rate_info .today")
            )
            if price_elem:
                raw_txt = re.sub(r"[^\d]", "", price_elem.get_text(strip=True))
                if raw_txt:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    logger.info(f"[가격] 네이버종목페이지 성공: {raw_code} = ₩{int(raw_txt):,}")
                    return f"₩{int(raw_txt):,} ({date_str} 기준, 네이버금융)"
        except Exception as e:
            logger.debug(f"[가격] 네이버종목페이지({raw_code}) 실패: {e}")

        # ── 4. 네이버금융 해외주식 폴백 (.K 접미사) ──────────────────────
        naver = _fetch_naver_price(raw_code)
        if naver:
            return naver

        logger.warning(f"[가격] {ticker} 종가 조회 모두 실패 — N/A 반환")
        return "N/A"

    else:
        # ── 미국/글로벌: yfinance → 네이버금융 해외주식 ──────────────────
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="7d")
            if not hist.empty:
                price = round(hist["Close"].iloc[-1], 2)
                date_str = hist.index[-1].strftime("%Y-%m-%d")
                logger.info(f"[가격] yfinance 성공: {ticker} = ${price:,.2f}")
                return f"${price:,.2f} ({date_str} 기준)"
        except Exception as e:
            logger.debug(f"[가격] yfinance({ticker}) 실패: {e}")

        naver = _fetch_naver_price(ticker)
        if naver:
            return naver

        logger.warning(f"[가격] {ticker} 종가 조회 모두 실패 — N/A 반환")
        return "N/A"


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

    # 스타일 토큰 → styles/tokens.py 에서 import (Pre-Phase 17)
    BOX_STYLE = SOURCE_BOX_STYLE
    H_STYLE   = SOURCE_H_STYLE
    CAT_STYLE = SOURCE_CAT_STYLE
    UL_STYLE  = SOURCE_UL_STYLE
    LI_STYLE  = SOURCE_LI_STYLE

    def _rebuild(match: re.Match) -> str:
        raw = match.group(0)
        # 블록 태그를 개행으로 치환하여 줄 경계 보존 (이슈 #1)
        raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
        raw = re.sub(r"</li>|</p>|</div>", "\n", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", "", raw)
        # 쉼표를 구분자에서 제거 → "출처명, 날짜" 한 아이템으로 유지 (이슈 #2)
        parts = re.split(r"[\n·•]+", raw)
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
    # Pre-Phase 17: 스타일 토큰을 styles/tokens.py import 이름으로 직접 참조.
    # (로컬 변수 재할당 없이 module-level import 이름을 바로 사용)
    html = md_lib.markdown(content, extensions=["tables", "fenced_code"])

    for level in [2, 4]:
        html = html.replace(f"<h{level}>", f'<h3 style="{_conv_H3}">')
        html = html.replace(f"</h{level}>", "</h3>")
    html = html.replace("<h3>", f'<h3 style="{_conv_H3}">')
    html = html.replace("<h1>", f'<h1 style="{_conv_H1}">')
    html = html.replace("<p>", f'<p style="{_conv_P}">')
    html = html.replace("<hr>", f'<hr style="{_conv_HR}">')
    html = html.replace("<hr />", f'<hr style="{_conv_HR}">')
    html = html.replace("<blockquote>", f'<blockquote style="{BQ_STYLE}">')
    html = html.replace("<ul>", f'<ul style="{UL_STYLE}">')
    html = html.replace("<ol>", f'<ol style="{OL_STYLE}">')
    html = html.replace("<li>", f'<li style="{LI_STYLE}">')
    html = html.replace("<strong>", f'<strong style="{_STRONG_STYLE}">')
    html = re.sub(r"<a ", f'<a style="{A_STYLE}" ', html)

    picks_pattern = re.compile(
        r"(<h3[^>]*>.*?캐시의\s*픽.*?</h3>)(.*?)(<h3[^>]*>.*?참고\s*출처.*?</h3>)",
        re.DOTALL,
    )

    def _wrap_picks_box(m: re.Match) -> str:
        return (
            f"{m.group(1)}"
            f'<div style="{_conv_PICKS}">'
            f"{m.group(2).strip()}"
            f"</div>\n"
            f"{m.group(3)}"
        )

    html = picks_pattern.sub(_wrap_picks_box, html)
    return html


# ──────────────────────────────────────────────────────────────────────────────
# SECTION E: Phase 7 — v2 프롬프트 상수
# ──────────────────────────────────────────────────────────────────────────────

# ─── HTML 스타일 인라인 상수 → styles/tokens.py 로 이전 (Pre-Phase 17) ──────
# _H1_STYLE, _H3_STYLE, _P_STYLE, _HR_STYLE, _PICKS_DIV_STYLE 는
# 파일 상단 `from styles.tokens import ...` 에서 공급된다.


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
      "id": "fact_1",
      "content": "확인된 사실 내용 (숫자·날짜·기관명 포함)",
      "source": "출처명 (언론사명, 기관명, 리포트명 등)",
      "date": "기준 시점 (YYYY-MM-DD 또는 'YYYY년 Q분기' 등)",
      "tier": "recent",
      "relevance_to_theme": "이 사실이 핵심 테마와 어떻게 연결되는지 한 줄 설명",
      "why_it_matters": "이 숫자/사실이 왜 중요한지 인과관계 한 줄 설명",
      "causal_path": "이 사실이 금융시장으로 전파되는 구체적 인과 경로 (A → B → C 형식)",
      "confidence": "high | medium | low"
    }
  ],
  "background_facts": [
    {
      "id": "bg_1",
      "content": "7~30일 자료 — 배경 설명용으로만 사용 가능한 사실",
      "source": "출처명",
      "date": "기준 시점",
      "tier": "extended",
      "relevance_to_theme": "배경으로서 역할 한 줄",
      "usage_rule": "background_only"
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
  "writing_notes": "ChatGPT 작성자에게 전달할 주의사항 (과장 금지 항목, 반복 금지 표현, 민감한 표현 등)",

  "why_now": {
    "claim": "왜 오늘 하필 이 테마인가 — 오늘의 specific trigger 한 문장 (범용 설명 금지)",
    "evidence_ids": ["fact_2"],
    "confidence": "high | medium | low"
  },
  "market_gap": {
    "claim": "시장이 현재 과소평가하거나 오독하고 있는 것 (사실 서술만, 투자 권유 금지)",
    "evidence_ids": ["fact_4", "fact_5"],
    "confidence": "high | medium | low"
  },
  "analyst_surprise": {
    "level": "none | mild | strong",
    "claim": "예상 외로 중요하거나 비자명한 사실 (level=none이면 claim 생략 가능)",
    "evidence_ids": ["fact_3"],
    "confidence": "high | medium | low"
  },
  "stance_type": "consensus_miss | underpriced_risk | overread | low_confidence | neutral",
  "stance_evidence_ids": ["fact_2", "fact_5"],
  "risk_of_overstatement": [
    {
      "text": "과장 위험이 있는 주장",
      "reason": "근거 부족 또는 전망 비약"
    }
  ]
}

facts는 반드시 5개 이상 10개 이하 (핵심 테마와 직접 관련된 최근 7일 자료 중심).
facts의 id는 "fact_1", "fact_2" 순서로 부여한다. background_facts의 id는 "bg_1", "bg_2" 순서로 부여한다.
background_facts는 있는 경우만 포함, 없으면 빈 배열 [].
핵심 테마와 무관한 사실은 facts에 포함하지 말고 auxiliary_context에 한 줄로 요약.

[facts 필터링 규칙 — Phase 4.3 추가]
- facts 배열에서 핵심 테마와 직접 관련이 없는 항목은 우선 제외한다.
- 예: 핵심 테마가 "AI 반도체 수요 급증"이라면 유가·지정학·금리 관련 사실은 facts에서 제외하고 auxiliary_context로 이동.
- relevance_to_theme 항목이 "간접적 영향" 또는 "배경" 수준이면 background_facts로 분류한다.
- facts에는 핵심 테마와 직접 인과관계를 가진 항목만 남긴다.

[perspective fields 규칙 — Phase 20]
- why_now.claim은 반드시 "오늘의 specific trigger"여야 한다.
  좋은 예: "3/19 FOMC 점도표가 금리인하 횟수를 3→2로 하향한 것이 오늘의 핵심 트리거"
  나쁜 예: "글로벌 금융시장의 불확실성이 높아지고 있다"
- why_now.evidence_ids는 반드시 위 facts 배열의 실제 id와 일치해야 한다. 일치하지 않으면 why_now 전체를 생략하라.
- market_gap.claim은 투자 권유가 되면 안 된다. "시장이 아직 X를 반영하지 않았다"는 사실 서술이어야 한다.
- market_gap.evidence_ids도 반드시 facts 배열의 실제 id와 일치해야 한다. 일치하지 않으면 market_gap 전체를 생략하라.
- analyst_surprise.level=none이면 claim과 evidence_ids를 생략하고 {"level": "none"}만 출력해도 된다.
- stance_type은 아래 5개 값 중 하나만 허용한다: consensus_miss | underpriced_risk | overread | low_confidence | neutral
  근거가 없으면 반드시 "neutral"로 설정한다.
- stance_evidence_ids가 비어있으면 stance_type은 강제로 "neutral"이다.
- risk_of_overstatement는 why_now 또는 market_gap이 존재할 때 반드시 1개 이상 작성한다.
  why_now와 market_gap이 모두 없으면 빈 배열 []로 출력해도 된다.
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


# ─── Step 1.5: Editorial Planner 프롬프트 (Phase 20) ──────────────────────────

GEMINI_PLANNER_POST1_SYSTEM = """
너는 매크로몰트 Post1 Editorial Planner다.
Step1 분석 재료를 받아 Post1(심층분석) 편집 계획을 JSON으로 출력한다.

Post1의 역할:
- 거시 메커니즘과 전파 경로 중심 (macro mechanism / transmission path)
- 정책·구조·글로벌 연결 논리
- 종목 픽 없음. macro 레이어만.

[section roles — Post1 전용 허용 집합]
sec_1: macro_mechanism   — 거시 변수가 왜 지금 작동하는가
sec_2: transmission_path — 한국/아시아 시장으로 전파되는 경로
sec_3: market_structure  — 구조적 배경 또는 선행 지표
sec_4: counterpoint      — 이번 thesis에 특화된 반대 해석 (필수)

[필수 결정 사항]
1. lead_angle: facts에서 evidence_ids 지정. 정확히 1개.
2. secondary_support: lead를 강화하는 전파 경로 메커니즘. 최대 2개.
3. background_or_drop: 강등 또는 제외 대상. drop_ids 최소 1개 필수.
4. stance: Step1의 stance_type 중 하나. evidence_ids 필수.
5. narrative_shape: conclusion_first | contradiction_first | question_first
6. section_plan: 4개 섹션. word_budget_ratio 합 ≤ 1.0. lead 섹션 ≥ 0.35.

[슬롯별 opener_strategy]
- morning:   어젯밤 미국장 결과가 오늘 macro 테마에 미치는 직접 결과
- afternoon: 국내장 중 나타나는 섹터 차별화 또는 예상 대비 해석
- evening:   오늘 세션 실제 결과 vs 장 시작 전 예상 경로 비교
- default:   현재 살아있는 핵심 변수 또는 시장 오독

[금지]
- facts 전체를 section_plan에 균등 분배하지 말 것.
- counterpoint를 "다양한 리스크 존재" 수준으로 처리 금지.
- 근거 없는 lead_angle 생성 금지.
- pick_trigger / stock_sensitivity / selection_logic을 section role로 사용 금지.
- word_budget_ratio lead 섹션이 0.35 미만이면 재편성.

[출력 JSON 구조]
{
  "lead_angle": {
    "claim": "이 글의 유일한 중심 논거 한 문장",
    "evidence_ids": ["fact_2", "fact_5"],
    "reason_selected": "이 각도가 다른 후보를 제치고 선택된 이유"
  },
  "secondary_support": [
    {
      "claim": "리드를 강화하는 2차 메커니즘",
      "evidence_ids": ["fact_1", "fact_4"]
    }
  ],
  "background_or_drop": {
    "background_ids": ["fact_6", "bg_1"],
    "drop_ids": ["fact_8"],
    "reason": "배경 처리 또는 제외 이유"
  },
  "stance": {
    "type": "consensus_miss | underpriced_risk | overread | low_confidence | neutral",
    "confidence": "high | medium | low",
    "evidence_ids": ["fact_2", "fact_5"]
  },
  "narrative_shape": "conclusion_first | contradiction_first | question_first",
  "opener_strategy": "슬롯 기반 opener 지침 결과 한 줄",
  "counterpoint_priority": "strong | moderate | light",
  "section_plan": [
    {
      "section_id": "sec_1",
      "role": "macro_mechanism",
      "goal": "이 섹션이 논거에서 하는 역할",
      "evidence_ids": ["fact_2", "fact_5"],
      "word_budget_ratio": 0.40,
      "must_include": ["date anchor", "mechanism sentence", "specific market relevance"],
      "must_avoid": ["generic macro filler", "equal-weight fact review"]
    },
    {
      "section_id": "sec_2",
      "role": "transmission_path",
      "goal": "리드 논거의 전파 경로",
      "evidence_ids": ["fact_1", "fact_4"],
      "word_budget_ratio": 0.25
    },
    {
      "section_id": "sec_3",
      "role": "market_structure",
      "goal": "구조적 배경으로 thesis 강화",
      "evidence_ids": ["fact_7"],
      "word_budget_ratio": 0.20
    },
    {
      "section_id": "sec_4",
      "role": "counterpoint",
      "goal": "thesis를 무력화하지 않는 최강의 반대 논거",
      "evidence_ids": ["fact_9"],
      "word_budget_ratio": 0.15
    }
  ]
}

반드시 JSON 하나만 출력. 설명 없음. 마크다운 없음.
"""

GEMINI_PLANNER_POST2_SYSTEM = """
너는 매크로몰트 Post2 Editorial Planner다.
Step1 분석 재료를 받아 Post2(캐시의 픽) 편집 계획을 JSON으로 출력한다.

Post2의 역할:
- 종목/섹터 민감도와 트리거 논리 중심 (pick trigger / stock sensitivity / selection logic)
- "왜 지금 이 종목인가" pick-angle이 opener
- 거시 배경은 pick trigger를 설명하기 위한 수단으로만 사용

[section roles — Post2 전용 허용 집합]
sec_1: pick_trigger      — 왜 지금 이 종목/섹터인가 (오늘의 specific trigger)
sec_2: stock_sensitivity — 핵심 변수가 이 종목에 미치는 민감도와 노출 경로
sec_3: selection_logic   — 다른 종목/섹터 대비 이 픽을 선택한 근거
sec_4: counterpoint      — 이번 pick thesis에 특화된 반대 해석 (필수)

[필수 결정 사항]
1. lead_angle: 메인 픽 또는 섹터의 pick trigger. evidence_ids 지정. 정확히 1개.
2. secondary_support: 민감도 또는 선택 근거 강화용. 최대 2개.
3. background_or_drop: 강등 또는 제외 대상. drop_ids 최소 1개 필수.
4. stance: Step1의 stance_type. evidence_ids 필수.
5. narrative_shape: 픽 논거에 맞는 shape 선택.
6. section_plan: 4개 섹션. lead ≥ 0.35.

[금지]
- macro_mechanism / transmission_path를 section role로 설정 금지.
- pick_trigger 없이 시장 배경 설명으로 opener 시작 금지 (Phase 17 규칙 유지).
- counterpoint를 범용 리스크 나열로 처리 금지.
- word_budget_ratio lead 섹션이 0.35 미만이면 재편성.

[출력 JSON 구조]
{
  "lead_angle": {
    "claim": "이 글의 유일한 중심 논거 — 메인 픽 또는 섹터의 핵심 trigger",
    "evidence_ids": ["fact_3", "fact_6"],
    "reason_selected": "이 각도가 다른 후보를 제치고 선택된 이유"
  },
  "secondary_support": [
    {
      "claim": "민감도 또는 선택 근거 강화",
      "evidence_ids": ["fact_1", "fact_5"]
    }
  ],
  "background_or_drop": {
    "background_ids": ["fact_7", "bg_1"],
    "drop_ids": ["fact_9"],
    "reason": "배경 처리 또는 제외 이유"
  },
  "stance": {
    "type": "consensus_miss | underpriced_risk | overread | low_confidence | neutral",
    "confidence": "high | medium | low",
    "evidence_ids": ["fact_3", "fact_6"]
  },
  "narrative_shape": "conclusion_first | contradiction_first | question_first",
  "opener_strategy": "픽 논거 기반 opener 지침 한 줄",
  "counterpoint_priority": "strong | moderate | light",
  "section_plan": [
    {
      "section_id": "sec_1",
      "role": "pick_trigger",
      "goal": "왜 지금 이 종목/섹터인가 확립",
      "evidence_ids": ["fact_3", "fact_6"],
      "word_budget_ratio": 0.40,
      "must_include": ["픽명 또는 섹터명", "오늘의 specific trigger", "핵심 변수 1개"],
      "must_avoid": ["거시 배경 설명으로 시작", "generic macro filler"]
    },
    {
      "section_id": "sec_2",
      "role": "stock_sensitivity",
      "goal": "핵심 변수가 이 종목에 미치는 민감도",
      "evidence_ids": ["fact_1", "fact_5"],
      "word_budget_ratio": 0.25
    },
    {
      "section_id": "sec_3",
      "role": "selection_logic",
      "goal": "다른 종목 대비 선택 근거",
      "evidence_ids": ["fact_2"],
      "word_budget_ratio": 0.20
    },
    {
      "section_id": "sec_4",
      "role": "counterpoint",
      "goal": "pick thesis에 특화된 반대 해석",
      "evidence_ids": ["fact_8"],
      "word_budget_ratio": 0.15
    }
  ]
}

반드시 JSON 하나만 출력. 설명 없음. 마크다운 없음.
"""

GEMINI_PLANNER_USER = """
아래 Step1 분석 재료와 슬롯 정보를 바탕으로 편집 계획을 JSON으로 출력하라.

[슬롯]
{slot}

[최근 발행 이력 제약]
{history_constraints}

[Step1 분석 재료]
{step1_json}
"""

# ─── Phase 20: Writer Contract 소비 블록 ─────────────────────────────────────
# gpt_write_analysis / gpt_write_picks의 user_msg 최상단에 prepend됨 (planner 성공 시)

_P20_POST1_CONTRACT_BLOCK = """
[Phase 20 — Editorial Planner Contract — 최우선 준수]

너는 중립적 요약자가 아니다.
planner가 선택한 lead_angle 논거를 중심으로 독자에게
"왜 오늘 이 macro 테마가 중요한가"를 설득하는 밀도 높은 분석 브리프를 작성한다.

[4-tier 사실 처리 규칙 — 절대 준수]
- lead_facts: 이 글의 중심축. sec_1(lead section)의 핵심 근거로만 사용.
  lead section 분량이 다른 모든 섹션보다 명확히 무거워야 한다.
- secondary_facts: lead 논거를 강화하는 2차 근거. lead보다 분량이 적어야 한다.
- background_facts: usage_rule=context_only. 배경 언급만 허용. 논거로 인용 절대 금지.
- disallowed_fact_ids: 이 id 목록의 사실은 본문에 절대 등장하지 않는다.

[section_plan 준수]
- 각 섹션의 role / goal / evidence_ids / word_budget_ratio를 따른다.
- 모든 섹션에 "claim → support → implication" 동형 구조를 반복하지 말 것.
  lead 이후 섹션은 다른 수사 구조를 써라.
- counterpoint 섹션은 section_plan.evidence_ids 기반으로만. 범용 리스크 나열 금지.

[stance 표명 규칙]
- stance.type에 따라 논리적 입장을 선택한다:
  * consensus_miss: "시장이 아직 반영하지 않은 X가 있다" 구조
  * underpriced_risk: "이 리스크가 현재 가격에 충분히 반영되지 않았다" 구조
  * overread: "시장 반응이 실제 변화보다 과장됐다" 구조
  * low_confidence: 조건부 서술 강화, 단정 금지
  * neutral: 기존 방식 유지
- stance 표명은 lead_facts / secondary_facts 기반 사실에서만 도출. 근거 없는 확신 금지.

[narrative_shape 준수]
- conclusion_first: lead section 첫 문단에서 핵심 결론부터
- contradiction_first: lead section 첫 문단에서 시장 예상과 실제의 간극부터
- question_first: lead section 첫 문단에서 핵심 질문부터

[출력 끝에 필수 포함 — 누락 시 오류]
<!-- macromalt:evidence_ids_used=[fact_2,fact_5,...] -->
본문 작성에 실제로 사용한 fact/bg id 목록을 기재. 형식 엄수.

[이번 글의 편집 계획 (writer_contract)]
{writer_contract_json}
"""

_P20_POST2_CONTRACT_BLOCK = """
[Phase 20 — Editorial Planner Contract — 최우선 준수]

너는 중립적 요약자가 아니다.
planner가 선택한 pick_trigger 논거를 중심으로 독자에게
"왜 지금 이 종목/섹터인가"를 설득하는 밀도 높은 종목 브리프를 작성한다.

[4-tier 사실 처리 규칙 — 절대 준수]
- lead_facts: sec_1(pick_trigger section)의 핵심 근거.
  lead section 분량이 다른 모든 섹션보다 명확히 무거워야 한다.
- secondary_facts: 민감도/선택 근거 강화용. lead보다 분량이 적어야 한다.
- background_facts: usage_rule=context_only. 배경 언급만. 픽 논거로 인용 절대 금지.
- disallowed_fact_ids: 이 id 목록의 사실은 본문에 절대 등장하지 않는다.

[section_plan 준수]
- sec_1(pick_trigger): opener는 반드시 메인 픽명 또는 핵심 섹터명으로 시작.
  거시 배경 설명으로 시작 금지 (Phase 17 규칙 유지).
- 모든 섹션에 동형 구조 반복 금지. 각 섹션은 다른 수사 구조를 써라.
- counterpoint 섹션은 section_plan.evidence_ids 기반으로만. 범용 리스크 나열 금지.

[stance 표명 규칙 — Post1과 동일]
- stance.type에 따라 논리적 입장을 선택한다.
- 근거 없는 확신 표명 금지.

[narrative_shape 준수]
- conclusion_first / contradiction_first / question_first 중 선택.
- pick_trigger 섹션의 opener 구조에 반영.

[출력 끝에 필수 포함 — 누락 시 오류]
<!-- macromalt:evidence_ids_used=[fact_3,fact_6,...] -->
본문 작성에 실제로 사용한 fact/bg id 목록을 기재. 형식 엄수.

[이번 글의 편집 계획 (writer_contract)]
{writer_contract_json}
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
  현재 확인된 사실처럼 단정 서술 금지. 반드시 조건부 언어 표지와 함께 서술한다.
  ❌ 금지 예: "삼성전자는 2026년 매출 300조 원을 기록할 것이다"
  ✅ 허용 예: "삼성전자의 2026년 매출은 300조 원으로 예상된다(미래에셋 추정)"
  ※ 예외: "2024년 매출액 X조", "2025년 영업이익 Y억" 등 이미 발표된 과거 확정 실적·집계값은
    과거 사실로 그대로 서술한다.

[작성 규칙]
1. 사실: 출처가 있는 내용은 일반 문장으로 자연스럽게 서술
   ★ [Phase 21] 각주 시스템 — 수치·통계·출처 있는 내용에 각주 번호를 순서대로 부여:
     본문: 수치 직후 <sup style="{_FOOTNOTE_SUP_STYLE}">[N]</sup> 삽입 (N은 1부터 순서대로)
     예: 영업이익 2,300억 원<sup style="{_FOOTNOTE_SUP_STYLE}">[1]</sup>
     예: 기준금리 3.5%<sup style="{_FOOTNOTE_SUP_STYLE}">[2]</sup>
     - 같은 출처 재인용 시 동일 번호 재사용 ([1] 반복)
     - 출처 불명 수치는 각주 없이 서술
     ★ 글 맨 마지막에 반드시 참고 자료 섹션을 추가:
     <div style="{_FOOTNOTE_SECTION_STYLE}">
     <p style="{_FOOTNOTE_TITLE_STYLE}">참고 자료</p>
     <p style="{_FOOTNOTE_ITEM_STYLE}">[1] 메리츠증권 리서치센터, 2026.03</p>
     <p style="{_FOOTNOTE_ITEM_STYLE}">[2] 한국은행 경제통계시스템(ECOS), 2026.02</p>
     </div>
2. 해석: [해석] 태그 없이 문장 자체에 해석 표지를 녹여 쓴다.
   ✅ "이는 ~를 의미한다" / "~라는 분석이다" / "~로 해석된다" / "핵심은 ~에 있다"
   ❌ "[해석]" 텍스트 레이블 삽입 금지
3. 전망: [전망] 태그 없이 조건부 언어 표지로 구분한다.
   ✅ "~로 예상된다" / "~할 것으로 전망된다" / "~가능성이 높다는 분석이 나온다"
   ❌ "[전망]" 텍스트 레이블 삽입 금지
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
  * 강조: <strong style="{_STRONG_STYLE}">강조어</strong>
  * 인라인 출처: <small style="{_CITE_STYLE}">(출처명, YYYY.MM)</small>

[글 구조]
0. [Phase 21] 출력 맨 첫 줄(h1 이전): <!-- SEO_TITLE: 검색 키워드 중심 제목 (40~60자) -->
   형식 가이드: "{{핵심 종목/지표}} {{핵심 동사구}} — {{독자 궁금증}}"
   예: SK하이닉스 HBM 수율 — 엔비디아 납품이 갈리는 기준
   예: 기준금리 동결 — 2026년 하반기 인하 시나리오 3가지
   규칙: [심층분석] 태그 없이, 독자가 실제 검색할 키워드 중심 (40~60자)
1. 제목: <h1>로 작성 — "[심층분석] {{테마}}" 형식 (핵심 테마 1개만 담을 것)
2. 도입부: <p>로 작성 — 위스키/바텐더 비유 1회 + 오늘의 핵심 테마 소개 (150자 내외)
3. 오늘의 시장 컨텍스트: <h3> + <p> — 최근 7일 데이터 중심 현황 정리
4. 핵심 분석 1: <h3> + <p> — theme_sub_axes[0] 에 해당하는 하위 축 (4요소 필수)
5. 핵심 분석 2: <h3> + <p> — theme_sub_axes[1] 에 해당하는 하위 축 (4요소 필수)
6. 핵심 분석 3: <h3> + <p> — theme_sub_axes[2] 에 해당하는 하위 축 (4요소 필수)
7. 반대 시각 및 체크포인트: <h3> + <p> — 이번 테마에 특화된 반론 및 불확실성
8. 참고 출처 섹션: <h3>참고 출처</h3> 다음에 <ul>/<li>로 각 출처를 한 줄씩 나열.
   형식: <li>출처명, 날짜</li> (예: <li>매일경제, 2026.04.08</li>)
   각 출처를 반드시 별도 <li> 태그에 작성할 것. 쉼표로 여러 항목을 한 줄에 나열 금지.
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
□ ★★ [Phase 20 숫자 밀도 필수 검수] 전체 글에 숫자 패턴(%, ₩, 원, 억, 만, 년+월, 분기, bps, pp 포함 숫자)이 최소 5개 이상 포함됐는가 — 5개 미만이면 즉시 구체 수치 문장 추가 후 재출력
□ ★ [Phase 21 각주 검수] 출처가 명확한 수치·통계 직후에 <sup>[N]</sup> 각주 번호가 삽입됐는가 — 본문에 최소 3개 이상, 글 말미에 참고 자료 섹션이 포함되어 있는가
□ [Phase 21 SEO_TITLE 검수] 출력 첫 줄이 <!-- SEO_TITLE: ... --> 형식 주석으로 시작하는가

[분량]
총 2,000자 이상의 HTML 출력
★ [Phase 20] 숫자 패턴(%, ₩, 원, 억, 만, 년월, 분기, bps 포함 숫자) 최소 5개 필수
  — 숫자 5개 미만이면 품질 검사 FAIL 처리 → 숫자 없는 단락에 수치 근거 추가하여 해결할 것
  — 예: "전 분기 대비 +12%" / "영업이익 2,300억 원" / "2026년 1월 기준" / "기준금리 3.5%" 등
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
1. 사실은 일반 문장, 해석·전망은 조건부 언어 표지로 구분
   ★ [Phase 21] 각주 시스템 — 수치·통계·출처 있는 내용에 각주 번호를 순서대로 부여:
     본문: 수치 직후 <sup style="{_FOOTNOTE_SUP_STYLE}">[N]</sup> 삽입 (N은 1부터 순서대로)
     예: 영업이익 2,300억 원<sup style="{_FOOTNOTE_SUP_STYLE}">[1]</sup>
     - 같은 출처 재인용 시 동일 번호 재사용 ([1] 반복)
     ★ 글 맨 마지막에 반드시 참고 자료 섹션 추가:
     <div style="{_FOOTNOTE_SECTION_STYLE}">
     <p style="{_FOOTNOTE_TITLE_STYLE}">참고 자료</p>
     <p style="{_FOOTNOTE_ITEM_STYLE}">[1] 메리츠증권 리서치센터, 2026.03</p>
     </div>
2. 투자 권유성 표현 전면 금지 — 아래 표현 및 이와 유사한 표현 모두 금지:
   "매수", "매수하세요", "지금 사야 할", "유망", "주목해야 한다", "담아야 한다",
   "기회다", "추천한다", "매력적인 선택지", "관심 가져볼 만한", "주가 상승을 견인",
   "장기 성장 가능성을 갖춘", "긍정적으로 평가", "수혜가 기대",
   "저평가 매력", "매수 기회", "하방 경직성 제공",
   "수혜를 받을 수 있는", "실적 개선 효과를 기대할 수 있는"
   → 대신 분석/관찰/조건부 해석 중심 문장으로 서술한다.
   ✅ 예: "이러한 조건이 지속된다면 실적 개선 여부를 판단할 수 있는 시점은 X분기다"
3. 미래 연도 숫자("2026년 전망", "가이던스", "추정치")는 반드시 조건부 언어 표지와 함께 서술
   ('~로 예상된다', '~할 것으로 전망된다', '~라는 분석이다' 형식)
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
  * 강조: <strong style="{_STRONG_STYLE}">강조어</strong>
  * 인라인 출처: <small style="{_CITE_STYLE}">(출처명, YYYY.MM)</small>

[글 구조]
0. [Phase 21] 출력 맨 첫 줄(h1 이전): <!-- SEO_TITLE: 검색 키워드 중심 제목 (40~60자) -->
   형식 가이드: "{{메인 픽 종목명}} {{핵심 투자 논점}} — {{독자 궁금증}}"
   예: SK하이닉스 캐시의 픽 — HBM 수율 개선이 실적 반영되는 시점
   예: 삼성바이오 캐시의 픽 — CMO 수주 잔고가 주가를 결정할 변수
   규칙: [캐시의 픽] 태그 없이, 독자가 실제 검색할 키워드 중심 (40~60자)
1. 제목: <h1>로 작성 — "[캐시의 픽] {{메인종목명}} 외 — {{테마 핵심 키워드}}" 형식
2. 도입부: <p>로 간결하게 오늘의 테마와 종목 선정 배경 연결
3. 왜 지금 {{메인 픽 또는 핵심 섹터}}인가: <h3> + <p>
   - H3에 메인 픽명 또는 핵심 섹터명을 반드시 직접 명시 (generic fallback 금지)
   - 첫 문장은 메인 픽 또는 핵심 섹터명을 반드시 포함해야 한다
   - 첫 문장은 거시 배경 재서술로 시작하면 안 된다
   - 첫 문장에 수주/판가/재고/CAPEX/정책 수혜/실적 민감도/가격 전가력 중 핵심 변수 1개 이상 제시
   - 거시 배경은 첫 문장 이후 또는 다음 문단에 배치
   ❌ H3 금지 예시: "오늘 이 테마를 보는 이유" / "오늘 시장을 보는 이유" / "최근 거시 환경을 먼저 보면" / "이번 시장 변수는"
   ✅ H3 허용 예시: "왜 지금 {{메인 픽}}인가" / "{{메인 픽}}을 먼저 봐야 하는 이유" / "이번 변수에서 먼저 봐야 할 {{핵심 섹터}}"
4. ⭐ 메인 픽: <div style="{_PICKS_DIV_STYLE}">로 감싸고
   - <h3>으로 "⭐ 메인 픽 — 종목명(티커)" 표시
   - 4문장 이상 리포트형 서술 (4단계 순서 준수)
5. 보조 픽 1 (있는 경우): <div style="{_PICKS_DIV_STYLE}">로 감싸고
   - <h3>으로 "보조 픽 — 종목명(티커)" 표시
   - 4문장 이상 리포트형 서술
6. 보조 픽 2 (있는 경우): 동일 형식
7. 체크포인트 3개: <h3> + <p> — 이번 픽을 모니터링할 핵심 변수 (이번 테마 특화)
8. 참고 출처 섹션: <h3>참고 출처</h3> 다음에 <ul>/<li>로 각 출처를 한 줄씩 나열.
   형식: <li>출처명, 날짜</li> (예: <li>매일경제, 2026.04.08</li>)
   각 출처를 반드시 별도 <li> 태그에 작성할 것. 쉼표로 여러 항목을 한 줄에 나열 금지.

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
□ ★ [Phase 21 각주 검수] 실적·수주잔고·목표가 등 구체 수치 직후에 <sup>[N]</sup> 각주 번호가 삽입됐는가 — 본문에 최소 2개 이상, 글 말미에 참고 자료 섹션이 포함되어 있는가
□ [Phase 21 SEO_TITLE 검수] 출력 첫 줄이 <!-- SEO_TITLE: ... --> 형식 주석으로 시작하는가

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
      조건부 언어 표지 없이 현재 확인된 사실처럼 단정 서술되지 않았는가
      ('~로 예상된다', '~할 것으로 전망된다', '~가능성이 높다는 분석' 등 조건부 표현이 있으면 통과)
      ※ 예외: "2024년 매출액", "2025년 영업이익" 등 이미 발표된 과거 확정 실적·집계값은
        위반으로 처리하지 말 것.
   — ①②③ 중 하나라도 위반 시 pass=false. 위반 문장을 issues에 정확히 인용해 명시할 것.
   — "완화 가능"으로 처리하지 말고 반드시 수정 대상으로 표시할 것.
2. [수치 정확성] 수치·날짜·고유명사의 오류 가능성 및 기준 시점 누락 여부
3. [사실/해석 구분] 해석·전망이 조건부 언어 표지 없이 사실처럼 단정 서술된 문장 여부
   (조건부 표현 예: '~로 예상된다', '~라는 분석이다', '~로 해석된다', '~할 것으로 전망된다')
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

★ Phase 17 opener 구조 점검 (Post2 전용, 20~25번):
20. [opener H3 generic] Post2 세 번째 섹션 H3가 "오늘 이 테마를 보는 이유" / "오늘 시장을 보는 이유" /
    "최근 거시 환경을 먼저 보면" / "글로벌 매크로 흐름" / "이번 시장 변수는" / "최근 변동성" 등
    generic theme explainer 패턴인지 (해당 시 pass=false)
21. [opener 첫 문장 픽 누락] Post2 세 번째 섹션의 첫 문장에 메인 픽명 또는 핵심 섹터명이
    포함되지 않은 경우 (해당 시 pass=false)
22. [opener macro recap 시작] Post2 세 번째 섹션의 첫 문장이 금리/환율/유가/불확실성/변동성
    등 macro 변수 설명으로만 시작하는 경우 (해당 시 pass=false)
23. [opener 핵심 변수 누락] Post2 세 번째 섹션의 첫 문장에 수주/판가/재고/CAPEX/정책 수혜/
    실적 민감도/가격 전가력/운임/밸류체인 등 핵심 변수가 1개도 없는 경우 (경미하면 issues 기재)
24. [Post1 opener 중복] Post2 세 번째 섹션이 Post1의 시장 배경 설명과 역할 중복인 경우
    (중복 문장이 뚜렷하면 pass=false)
25. [opener 픽 연결 누락] Post2 세 번째 섹션이 이후 메인 픽/보조 픽 섹션과 논리적으로
    연결되지 않는 경우 (경미하면 issues 기재)
※ 20~22번 위반 시 반드시 pass=false. 위반 문장을 issues에 정확히 인용할 것.

★ Phase 20 편집 구조 점검 (26~30번):
26. [섹션 동형 반복] 연속된 2개 이상의 h3 섹션이 "주장(1문장) → 수치 근거(1~2문장) → 시장 시사(1문장)"
    동일 3단 구조를 거의 그대로 반복하는가 — opener 표현만 다르고 수사 구조가 동형이면 해당
    (2섹션 이상 연속 동형 시 pass=false. 위반 섹션 제목을 issues에 인용할 것.)
27. [강조 분산] 전체 h3 섹션들이 분량·수사 비중 면에서 거의 균등한가 — 명확히 무거운 lead 섹션이
    없고 모든 섹션이 비슷한 역할(요약형 서술)로 처리된 경우
    (3개 이상 섹션 균등 배분 시 pass=false)
28. [리드 드리프트] 도입부 또는 첫 h3에서 제시한 핵심 논거·각도가 중반 이후 섹션에서 사라지고,
    각 섹션이 독립적인 사실 묶음으로 전개되는가 — 전반부에서 내세운 "왜 지금"이 후반부에서
    재등장하거나 강화되지 않고 방치되는 패턴
    (뚜렷한 드리프트 시 pass=false. 드리프트 지점 문장을 issues에 인용할 것.)
29. [일반 문장 과잉] 숫자·날짜·인과관계·출처·포지션 값 중 하나도 포함하지 않은 문장(일반 연결 문장 제외)이
    전체 서술 문장의 40% 이상인가 — "~에 주목할 필요가 있다", "~로 분석된다", "시장에 영향을 줄 수 있다"
    류 내용 없는 문장이 과도하게 반복되는 경우
    (40% 이상 시 pass=false)
30. [근거 없는 분석 단정] "시장이 과소평가했다", "아직 반영되지 않았다", "시장 컨센서스와 달리",
    "예상보다 강하다/약하다", "시장의 인식과 괴리" 등 consensus_miss/underpriced_risk 계열의
    분석 판단이 구체적 수치·날짜·대비 사건 없이 단독 주장으로 서술되는가
    (구체 근거 없는 단정 1회 이상 시 pass=false. 해당 문장을 issues에 정확히 인용할 것.)
※ 26~30번은 구조적 문제이므로 심각하면 pass=false. 경미하면 pass=true + issues 기재.
※ 26번(섹션 동형 반복)과 28번(리드 드리프트)은 AI 기계적 서술의 핵심 지표 — 엄격히 적용.

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
- 미래 예측 문장에 '~로 예상된다' / '~할 것으로 전망된다' 등 조건부 표지가 없으면 추가
- 출처 없는 단정 표현 → "~로 파악된다" / "~로 보인다" 표현으로 완화
- 투자 권유성 문장 → 중립 서술로 교체
- ★ <!-- PICKS: [...] --> 형태의 HTML 주석은 절대 삭제하지 말고 원본 그대로 마지막에 유지할 것

[수정 허용 범위 — 이 범위만 수정, 나머지 원문 유지]
1. 미래 예측 문장에 '~로 예상된다' / '~할 것으로 전망된다' 등 조건부 표지가 없으면 추가
2. 출처 없는 단정 표현 → "~로 파악된다" / "~로 보인다" 표현으로 교체
3. ★ 미래 연도 숫자 시점 혼동 수정 — 다음 방식으로 처리:
   - "2026년 X는 Y로 예상된다(출처 추정)" 형태로 재서술 (브래킷 태그 삽입 금지)
   - 현재 사실과 미래 전망을 한 문장에 섞지 말고 분리 서술
   - 근거 없는 미래 전망은 삭제하고 확인된 현재 사실로 대체
   ❌ 수정 전: "삼성전자는 2026년 매출 300조를 기록했다"
   ✅ 수정 후: "삼성전자의 2026년 매출은 300조 원으로 추정된다(미래에셋 리서치)"
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
9. [★ Phase 17 — opener 구조 보정 — Post2 전용]
   generic H2/H3 → pick-angle H3 교체 규칙:
   - "오늘 이 테마를 보는 이유" 등 generic opener H3 → "왜 지금 {메인 픽}인가" 형태로 교체
   - macro-first opener 첫 문장 → pick-first 문장으로 재작성 (메인 픽/섹터명 반드시 포함)
   - 메인 픽/핵심 섹터명이 첫 문장에 누락된 경우 → 첫 문장 앞에 즉시 삽입
   - Post1과 중복된 거시 배경 서술 → 시장 배경 축소 후 종목 연결 문장으로 치환
   - 보정 과정에서 새 절대 날짜를 발명하거나 삽입하지 않는다
   - [Phase 18 신규] 본문(h3 섹션 내) "오늘" 시점 표현 교체:
     "오늘 분석의 전제" → "이번 분석의 전제"
     "오늘 분석에서" → "이번 분석에서"
     "오늘 논의" → "이번 논의"
     "오늘의 핵심" → "이번의 핵심"
     ※ opener H3 교체 규칙(위)과 별개로, h3 헤딩 및 본문 모두에 적용할 것
   opener 검수 출력 형식 (issues에 포함할 것):
   - opener 구조: 적합 / 부적합
   - 문제 문장: (인용)
   - 문제 유형: generic H3 / macro recap / 픽 누락 / 역할 중복 / 핵심 변수 누락
   - 수정 이유: (한 줄)
   - 교체 문장 제안: (한 줄)
10. [★ 날짜 생성·삽입 금지 — 절대 원칙]
   - 본문이나 source에 없는 절대 날짜(예: "2024년 5월 20일", "2024년 4월 15일")를 새로 생성해서 삽입하지 말 것.
   - 날짜가 불명확하면 임의 보강 금지.
   - 날짜를 확정할 수 없으면 절대 날짜를 제거하고 "현재", "최근", "이날", "당시", "해당 시점" 등 일반 시점 표현으로 바꿀 것.
   - 숫자/지수/KOSPI 수정 과정에서 날짜를 함께 발명하거나 치환하지 말 것.
   - 날짜는 source에 명시된 경우에만 유지 또는 정정할 것.
   ❌ 금지: "2024년 5월 20일 기준 KOSPI는 2,724.62pt를 기록하고 있습니다"
   ❌ 금지: "2024년 4월 15일 기준으로 전일 대비 0.48% 하락하며"
   ✅ 허용: "KOSPI는 전일 대비 하락 마감했습니다" / "당시 KOSPI는 하락 마감했습니다"
11. [★ Phase 20 — 섹션 동형 반복 보정]
   연속된 섹션이 "주장→근거→시사" 동일 구조를 반복하는 경우 — 두 번째 반복 섹션부터 opener를 교체:
   - 평서형 opener → 역접형("그러나 ~", "반면 ~")이나 인과형("이 때문에 ~") 또는 질문형으로 교체
   - opener 표현만 교체 — 해당 섹션의 수치·논리는 반드시 원문 그대로 보존
   - 교체 후 섹션 길이가 원문보다 짧아지지 않도록 할 것
12. [★ Phase 20 — 리드 논거 약화 보정]
   도입부 또는 첫 섹션에서 제시된 핵심 각도(lead 논거)가 후반 섹션에서 재등장하지 않는 경우:
   - 마지막 핵심 분석 섹션(counterpoint 직전) 끝에 lead 논거와의 연결 문장 1개 추가
     예: "이러한 흐름은 앞서 제시한 [핵심 각도]의 연장선에서 해석할 수 있다"
   - 날짜·수치 발명 금지 — 기존 본문에 있는 사실만 참조할 것
   - 추가 문장은 1개로 제한
"""

GEMINI_REVISER_USER = """
아래 초안에서 다음 문제들을 수정하고, 수정된 HTML 전체를 출력하라.

[발견된 문제]
{issues}

[수정 대상 초안]
{draft}
"""

# ── Phase 16: Step3 시제 SSOT 블록 (모듈 로드 시 생성 → Phase 15C 정적 블록 대체) ──
# Phase 15C의 하드코딩 2026 고정 방식을 Phase 16 동적 SSOT로 교체
# _build_temporal_ssot / _build_p16_step3_block 은 위 Phase 16 섹션에 정의됨
_p16_module_ssot: dict = _build_temporal_ssot(
    run_year=int(datetime.now().strftime("%Y")),
    run_month=int(datetime.now().strftime("%m")),
)
_P16_STEP3_BLOCK: str = _build_p16_step3_block(_p16_module_ssot)

GEMINI_VERIFIER_SYSTEM = _P16_STEP3_BLOCK + GEMINI_VERIFIER_SYSTEM

# REVISER에는 추가로 완료 연도 [전망] 추가 절대 금지 규칙을 삽입 (Phase 15C 호환 유지)
_P15C_REVISER_COMPLETED_YEAR_GUARD: str = """
[Phase 15C/16 — 완료 연도 [전망] 태그 추가 절대 금지]
ACTUAL_SETTLED 상태(완전히 종료된 회계연도 및 현재 연도 완료 월)에 해당하는 실적·수치 문장에 대해:
  ❌ [전망] 태그를 새로 추가하는 것은 금지됩니다
  ❌ 확정 어미("기록했다", "달성했다", "집계됐다", "기록됐다")를 전망 어미로 변환하는 것은 금지됩니다
  ❌ "단정적 표현"이라는 이유로 ACTUAL_SETTLED 확정 실적 문장을 수정하는 것은 금지됩니다
  ✅ 이미 올바르게 과거형으로 서술된 완료 연도 실적 문장은 원문 그대로 보존하십시오

"""
GEMINI_REVISER_SYSTEM = (
    _P16_STEP3_BLOCK
    + _P15C_REVISER_COMPLETED_YEAR_GUARD
    + GEMINI_REVISER_SYSTEM
)


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


# ─── [Phase 22] 다중 테마 선정 ─────────────────────────────────────────────
_GEMINI_THEME_SELECTOR_SYSTEM = """
너는 매크로몰트(MacroMalt) 편집장이다.
오늘 수집된 뉴스·리서치 데이터를 보고 블로그에 게시할 핵심 경제 테마를 최대 {n}개 선정한다.

[선정 규칙]
- 각 테마는 서로 중복되지 않는 독립적인 주제여야 한다.
- 가장 많은 출처가 수렴하고 숫자 데이터가 풍부한 테마를 우선 선정한다.
- 최근 7일 이내 자료에 근거한 테마를 최우선으로 한다.
- 테마는 구체적이어야 한다 ("글로벌 경제" 같은 추상적 테마 금지).
- 각 테마는 한 문장으로 표현한다 (예: "SK하이닉스 HBM 수율 개선과 엔비디아 납품 확대").
- picks_priority: 1=종목 픽 가장 적합, 2=두 번째 적합, 3 이상=심층분석만

[출력 규칙]
JSON만 출력. 설명 텍스트 금지.

{{
  "themes": [
    {{"priority": 1, "theme": "테마 한 문장", "picks_priority": 1, "reason": "선정 이유 한 줄"}},
    {{"priority": 2, "theme": "테마 한 문장", "picks_priority": 2, "reason": "선정 이유 한 줄"}},
    ...
  ]
}}
"""

def gemini_select_themes(
    news_text: str,
    research_text: str,
    dart_text: str = "",
    n: int = 5,
    slot: str = "default",
    history_context: str = "",
) -> list[dict]:
    """[Phase 22] 오늘의 상위 N개 테마를 Gemini로 선정.

    Returns:
        [{"priority": 1, "theme": "...", "picks_priority": 1, "reason": "..."}, ...]
        실패 시 단일 테마 [{"priority": 1, "theme": "글로벌 경제 주요 이슈", ...}] 반환
    """
    system = _GEMINI_THEME_SELECTOR_SYSTEM.format(n=n)
    user_msg = (
        f"[뉴스 데이터]\n{news_text[:3000]}\n\n"
        f"[리서치 데이터]\n{research_text[:2000]}\n\n"
        f"[공시 데이터]\n{dart_text[:500] if dart_text else '없음'}\n\n"
        f"[발행 슬롯] {slot}\n"
        f"{history_context[:500] if history_context else ''}\n\n"
        f"위 데이터에서 오늘 다룰 핵심 테마 {n}개를 선정해줘."
    )
    raw = _call_gemini(system, user_msg, "Step0:테마선정", temperature=0.2,
                       response_mime_type="application/json")
    result = _parse_json_response(raw) if raw else None

    themes = None
    if result:
        if isinstance(result, list):                   # Gemini가 리스트 직접 반환
            themes = result
        elif isinstance(result, dict) and result.get("themes"):
            themes = result["themes"]

    if themes and isinstance(themes, list) and len(themes) > 0:
        logger.info(f"[Phase 22] 테마 {len(themes)}개 선정: {[t.get('theme','')[:30] for t in themes]}")
        return themes

    logger.warning(f"[Phase 22] 테마 선정 실패 — fallback. raw[:300]={str(raw)[:300]}")
    return [{"priority": 1, "theme": "글로벌 경제 주요 이슈", "picks_priority": 1, "reason": "fallback"}]


def gemini_analyze(news_text: str, research_text: str, dart_text: str = "",
                   slot: str = "default", history_context: str = "",
                   forced_theme: str = "") -> dict:
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
    ) + slot_ctx + history_context + _P12_ANALYST_EVIDENCE_RULES + _P13_GEMINI_SPINE_HINT + _PC_GEMINI_SECTOR_RULES
    # [Phase 22] 다중 테마 모드: forced_theme이 있으면 프롬프트에 명시
    if forced_theme:
        user_msg += (
            f"\n\n[Phase 22 — 분석 테마 지정]\n"
            f"오늘 분석할 핵심 테마는 이미 선정됐습니다: '{forced_theme}'\n"
            f"반드시 이 테마를 'theme' 필드에 그대로 사용하고, 이 테마와 관련된 사실만 facts에 포함하세요."
        )
    raw = _call_gemini(GEMINI_ANALYST_SYSTEM, user_msg, "Step1:분석재료생성", temperature=0.2,
                       response_mime_type="application/json")  # [Phase 19] JSON 강제
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


# ──────────────────────────────────────────────────────────────────────────────
# SECTION: Phase 20 — Step 1.5 Editorial Planner
# ──────────────────────────────────────────────────────────────────────────────

def _validate_planner_evidence_ids(planner: dict, step1: dict) -> dict:
    """planner의 evidence_ids가 step1 facts/bg의 실제 id와 일치하는지 검증.
    불일치 id를 제거하고, lead_angle.evidence_ids가 비면 planner를 None으로 반환."""
    valid_ids = set()
    for f in step1.get("facts", []):
        if f.get("id"):
            valid_ids.add(f["id"])
    for f in step1.get("background_facts", []):
        if f.get("id"):
            valid_ids.add(f["id"])

    def clean_ids(ids: list) -> list:
        return [i for i in (ids or []) if i in valid_ids]

    # lead_angle
    la = planner.get("lead_angle", {})
    la["evidence_ids"] = clean_ids(la.get("evidence_ids", []))
    if not la["evidence_ids"]:
        logger.warning("[Phase 20] planner lead_angle evidence_ids 검증 실패 — fallback")
        return None

    # secondary_support
    for ss in planner.get("secondary_support", []):
        ss["evidence_ids"] = clean_ids(ss.get("evidence_ids", []))

    # background_or_drop
    bod = planner.get("background_or_drop", {})
    bod["background_ids"] = clean_ids(bod.get("background_ids", []))
    bod["drop_ids"]       = clean_ids(bod.get("drop_ids", []))

    # stance
    st = planner.get("stance", {})
    st["evidence_ids"] = clean_ids(st.get("evidence_ids", []))
    if not st["evidence_ids"]:
        st["type"] = "neutral"

    # section_plan
    for sec in planner.get("section_plan", []):
        sec["evidence_ids"] = clean_ids(sec.get("evidence_ids", []))

    return planner


def _call_editorial_planner(
    step1: dict,
    post_type: str,
    slot: str,
    run_id: str,
    history_constraints: Optional[str] = None,
) -> Optional[dict]:
    """Step 1.5: Editorial Planner 호출 (Phase 20).

    Args:
        step1:               gemini_analyze() 결과
        post_type:           "post1" | "post2"
        slot:                발행 슬롯
        run_id:              로그용 run_id
        history_constraints: 최근 이력 제약 텍스트 (없으면 "없음")

    Returns:
        planner dict 또는 None (실패 시 fallback)
    """
    system_prompt = (
        GEMINI_PLANNER_POST1_SYSTEM if post_type == "post1"
        else GEMINI_PLANNER_POST2_SYSTEM
    )
    user_msg = GEMINI_PLANNER_USER.format(
        slot=slot,
        history_constraints=history_constraints or "없음",
        step1_json=json.dumps(step1, ensure_ascii=False, indent=2),
    )

    raw = _call_gemini(
        system_prompt, user_msg,
        f"Step1.5:EditorialPlanner:{post_type}",
        temperature=0.1,
        response_mime_type="application/json",  # [Phase 19] JSON 강제
    )
    planner = _parse_json_response(raw) if raw else None

    if not planner or not isinstance(planner, dict):
        logger.warning(
            f"[Phase 20] planner FAILED | run_id={run_id} | post_type={post_type} | "
            f"planner_used=False | fallback=step1_only"
        )
        return None

    # evidence_ids 검증 — 불일치 id 제거, lead 비면 None
    planner = _validate_planner_evidence_ids(planner, step1)
    if planner is None:
        logger.warning(
            f"[Phase 20] planner evidence_ids validation FAILED | run_id={run_id} | "
            f"post_type={post_type} | planner_used=False | fallback=step1_only"
        )
        return None

    # word_budget_ratio lead 섹션 최소값 보정
    section_plan = planner.get("section_plan", [])
    if section_plan:
        lead_ratio = section_plan[0].get("word_budget_ratio", 0)
        if lead_ratio < 0.35:
            logger.warning(
                f"[Phase 20] lead word_budget_ratio={lead_ratio} < 0.35 — 0.40으로 보정"
            )
            section_plan[0]["word_budget_ratio"] = 0.40

    # 로그
    bod = planner.get("background_or_drop", {})
    logger.info(
        f"[Phase 20] editorial planner OK | run_id={run_id} | slot={slot} | "
        f"post_type={post_type} | planner_used=True | "
        f"stance_type={planner.get('stance', {}).get('type', 'N/A')} | "
        f"narrative_shape={planner.get('narrative_shape', 'N/A')} | "
        f"lead_angle_evidence_ids={planner.get('lead_angle', {}).get('evidence_ids', [])} | "
        f"background_ids={bod.get('background_ids', [])} | "
        f"drop_ids={bod.get('drop_ids', [])}"
    )
    return planner


def _build_writer_contract(
    step1: dict,
    planner: dict,
    slot: str,
    history_constraints: Optional[dict] = None,
) -> dict:
    """planner 결과를 소비해 GPT writer에게 넘길 4-tier 구조 contract를 생성 (Phase 20).

    lead_facts / secondary_facts / background_facts / disallowed_fact_ids로 분리.
    GPT는 원본 step1 facts 배열을 받지 않는다 — contract만 받는다.

    Returns:
        writer_contract dict
    """
    all_facts: dict = {f["id"]: f for f in step1.get("facts", []) if f.get("id")}
    all_bg:    dict = {f["id"]: f for f in step1.get("background_facts", []) if f.get("id")}

    bod            = planner.get("background_or_drop", {})
    background_ids = set(bod.get("background_ids", []))
    drop_ids       = set(bod.get("drop_ids", []))

    # lead_fact_ids: lead_angle + secondary_support evidence_ids 합집합
    lead_ids = set(planner.get("lead_angle", {}).get("evidence_ids", []))
    secondary_ids: set = set()
    for ss in planner.get("secondary_support", []):
        secondary_ids.update(ss.get("evidence_ids", []))
    # secondary는 lead와 중복되지 않도록
    secondary_ids -= lead_ids

    def pick(id_set: set, src: dict) -> list:
        """id_set에서 src dict에 있는 항목만 추출 (순서: id 정렬)."""
        return [src[i] for i in sorted(id_set) if i in src]

    lead_facts       = pick(lead_ids, all_facts)
    secondary_facts  = pick(secondary_ids, all_facts)

    # background_facts: planner background_ids + step1 bg_facts (drop 제외)
    bg_fact_ids = background_ids & set(all_facts.keys())
    bg_bg_ids   = (set(all_bg.keys()) | (background_ids & set(all_bg.keys()))) - drop_ids
    background_facts = pick(bg_fact_ids, all_facts) + pick(bg_bg_ids, all_bg)

    # 나머지 facts (lead/secondary/background/drop 미포함) → background로 추가
    accounted = lead_ids | secondary_ids | background_ids | drop_ids
    remainder = set(all_facts.keys()) - accounted
    background_facts += pick(remainder, all_facts)

    # background_facts에 usage_rule 명시
    for f in background_facts:
        f["usage_rule"] = "context_only"

    # perspective 필드 (evidence_ids 검증된 것만)
    perspective: dict = {}
    wn = step1.get("why_now")
    if wn and isinstance(wn, dict) and wn.get("claim"):
        perspective["why_now"] = wn["claim"]
    mg = step1.get("market_gap")
    if mg and isinstance(mg, dict) and mg.get("claim"):
        perspective["market_gap"] = mg["claim"]
    asur = step1.get("analyst_surprise", {})
    perspective["analyst_surprise_level"] = asur.get("level", "none")

    contract = {
        "theme":         step1.get("theme", ""),
        "slot":          slot,
        "stance":        planner.get("stance", {"type": "neutral", "confidence": "low"}),
        "narrative_shape": planner.get("narrative_shape", "conclusion_first"),
        "opener_strategy": planner.get("opener_strategy", ""),
        "counterpoint_priority": planner.get("counterpoint_priority", "moderate"),
        "lead_facts":      lead_facts,
        "secondary_facts": secondary_facts,
        "background_facts": background_facts,
        "disallowed_fact_ids": sorted(drop_ids),
        "perspective":   perspective,
        "section_plan":  planner.get("section_plan", []),
        "recent_history_constraints": history_constraints or {},
        "html_output_rules": {
            "format":               "HTML only",
            "no_markdown":          True,
            "evidence_ids_comment": True,
        },
    }
    return contract


def _parse_writer_evidence_ids(html: str) -> list:
    """writer 출력 HTML에서 <!-- macromalt:evidence_ids_used=[...] --> 주석을 파싱.
    파싱 실패 시 [] 반환 (파이프라인 차단 없음).
    """
    import re as _re
    m = _re.search(r"<!--\s*macromalt:evidence_ids_used=\[([^\]]*)\]\s*-->", html or "")
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _check_p20_lead_metrics(
    writer_contract: dict,
    writer_used_ids: list,
    run_id: str,
    post_type: str,
) -> None:
    """Phase 20 lead quality 이중 지표 측정 (파이프라인 차단 없음).

    lead_recall: lead_ids 중 writer가 실제로 사용한 비율.
        낮으면 → planner가 지정한 핵심 근거를 writer가 누락 (lead 누락 문제).

    lead_focus: writer 전체 사용 ids 중 lead_ids의 비율.
        낮으면 → writer가 lead보다 secondary/background에 집중 (강조 희석 문제).

    WARN 임계값:
        lead_recall < 0.5  → lead 사실 절반 이상 미사용
        lead_focus  < 0.25 → 사용 사실 중 lead 비중 25% 미만 (균등 배분 회귀)
    """
    try:
        lead_ids = set()
        for f in writer_contract.get("lead_facts", []):
            if isinstance(f, dict) and f.get("id"):
                lead_ids.add(f["id"])
        if not lead_ids:
            return

        used_ids = set(writer_used_ids)
        hit       = lead_ids & used_ids
        missing   = lead_ids - used_ids

        lead_recall = len(hit) / len(lead_ids)
        lead_focus  = len(hit) / len(used_ids) if used_ids else 0.0

        logger.info(
            f"[Phase 20] lead_metrics | run_id={run_id} | post_type={post_type} | "
            f"lead_ids={sorted(lead_ids)} | writer_used_ids={sorted(used_ids)} | "
            f"missing_lead_ids={sorted(missing)} | "
            f"lead_recall={lead_recall:.2f} | lead_focus={lead_focus:.2f}"
        )

        warns = []
        if lead_recall < 0.5:
            warns.append(f"lead_recall={lead_recall:.2f} — lead_ids 절반 이상 미사용")
        if lead_focus < 0.25:
            warns.append(f"lead_focus={lead_focus:.2f} — 사용 facts 중 lead 비중 25% 미만 (강조 희석)")
        if warns:
            logger.warning(
                f"[Phase 20] WARN lead_metrics | run_id={run_id} | post_type={post_type} | "
                + " | ".join(warns)
            )
    except Exception as _e:
        logger.debug(f"[Phase 20] lead_metrics 예외 (무시) | {_e}")


# ─── [Phase 21] SEO_TITLE 추출 헬퍼 ─────────────────────────────────────────
def _extract_seo_title(html: str) -> str:
    """GPT 출력 첫 줄의 <!-- SEO_TITLE: ... --> 주석에서 제목 텍스트 추출.

    Returns:
        추출된 제목 문자열 (없으면 빈 문자열)
    """
    import re as _re
    m = _re.search(r"<!--\s*SEO_TITLE:\s*(.*?)\s*-->", html, _re.IGNORECASE)
    return m.group(1).strip() if m else ""


def gpt_write_analysis(materials: dict, context_text: str, slot: str = "default",
                       writer_contract: Optional[dict] = None,
                       run_id: str = "",
                       few_shot_suffix: str = "") -> str:
    """
    Step 2a: GPT 작성 엔진 — Post 1 심층 분석.
    Gemini 분석 재료를 HTML 형식의 심층 분석 글로 작성합니다.

    Args:
        slot:            발행 슬롯 — Phase 10 슬롯별 작성 방향 힌트 삽입
        writer_contract: Phase 20 editorial planner contract (없으면 기존 방식 fallback)
        run_id:          로그용 run_id

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

    # Phase 20: writer_contract 존재 시 contract 블록을 최우선으로 prepend
    p20_block = ""
    if writer_contract:
        p20_block = _P20_POST1_CONTRACT_BLOCK.format(
            writer_contract_json=json.dumps(writer_contract, ensure_ascii=False, indent=2)
        )

    user_msg = (
        p20_block                           # Phase 20: contract 소비 (최우선, 있을 때만)
        + _PC_POST1_EDITORIAL_RULES         # Phase C: 편집 철학 (독자·의견강도·시계·품질비율)
        + _P16H_POST1_HEDGE_REDUCTION       # Phase 16H Track A: factual spine 헤징 절제
        + _P16B_QUALITY_HARDENING_RULES     # Phase 16B: generic 금지 + spine + premium tone
        + _P14_POST1_ENFORCEMENT_BLOCK      # Phase 14: few-shot + spine + hedge 금지
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
    # Phase R: Few-shot 예시가 있으면 system 프롬프트 뒤에 append
    _pr_system = GPT_WRITER_ANALYSIS_SYSTEM + (few_shot_suffix if few_shot_suffix else "")

    draft = _call_gpt(
        _pr_system,
        user_msg,
        "Step2a:심층분석작성",
        temperature=0.7,
        max_tokens=5000,  # Phase 4.3: 4000 → 5000 (심층분석 밀도 복원)
    )

    # Phase 20: writer_used_evidence_ids 로그 + lead drift 체크
    if writer_contract and draft:
        used_ids = _parse_writer_evidence_ids(draft)
        logger.info(
            f"[Phase 20] writer evidence | run_id={run_id} | post_type=post1 | "
            f"writer_used_evidence_ids={used_ids}"
        )
        _check_p20_lead_metrics(writer_contract, used_ids, run_id, "post1")

    return draft


def gpt_write_picks(materials: dict, tickers: list, prices: dict, context_text: str,
                    slot: str = "default", post1_spine: str = "",
                    same_theme_hint: str = "",
                    writer_contract: Optional[dict] = None,
                    run_id: str = "",
                    post1_intro_text: str = "") -> str:  # [Phase 19] Post1 도입부 금지 구절
    """
    Step 2b: GPT 작성 엔진 — Post 2 종목 리포트.
    분석 재료 + 종목 + 실제 가격 데이터로 종목 리포트 HTML을 작성합니다.

    Args:
        slot:            발행 슬롯 — Phase 10 슬롯별 Post2 방향 힌트 삽입
        post1_spine:     Phase 14 Track B-4 — Post1 분석 뼈대/결론 (Post2 연속성 강제용)
        same_theme_hint: Phase 16J Track B — 동일 theme 연속 시 opener 강화 프롬프트 주입.
                         _p16j_check_theme_repeat() 결과가 is_repeat=True인 경우 주입.
                         is_repeat=False이면 빈 문자열 — 동작 변화 없음.
        writer_contract: Phase 20 editorial planner contract (없으면 기존 방식 fallback)
        run_id:          로그용 run_id

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

    # [Phase 19] Post1 도입부 금지 구절 블록 — post1_post2_continuity FAIL 방지
    # post1_intro_text 파라미터로 전달받은 Post1 실제 도입부 텍스트를 GPT에 전달
    _p1_intro_block = ""
    if post1_intro_text:
        _p1_intro_block = (
            "\n[Phase 19 — Post1 도입부 금지 구절 ★ 필독]\n"
            "아래 텍스트는 Post1([심층분석]) 도입부입니다. "
            "Post2 도입부에서 이 텍스트와 3어절 이상 겹치는 표현을 사용하지 마세요:\n"
            f"---\n{post1_intro_text}\n---\n\n"
        )

    # Phase 14 Track A: 소스 정규화
    run_date_str_now = datetime.now().strftime("%Y-%m-%d")
    source_norm_block = _normalize_source_for_generation(materials, run_date_str_now)

    # Phase 20: writer_contract 존재 시 contract 블록을 최우선으로 prepend
    p20_block = ""
    if writer_contract:
        p20_block = _P20_POST2_CONTRACT_BLOCK.format(
            writer_contract_json=json.dumps(writer_contract, ensure_ascii=False, indent=2)
        )

    user_msg = (
        p20_block                           # Phase 20: contract 소비 (최우선, 있을 때만)
        + _PC_POST2_EDITORIAL_RULES         # Phase C: 편집 철학 (독자·의견강도·시계·리스크섹션)
        + _P17_POST2_OPENER_ENFORCEMENT     # Phase 17: opener pick-angle 강제 ★★
        + _P15C_POST2_LABEL_BAN             # Phase 15C: 내부 파이프라인 레이블 차단
        + _P16D_POST2_CONTINUITY_HARDENING  # Phase 16D: Track A — 매크로 배경 재서술 억제
        + _P16D_POST2_BRIDGE_REQUIREMENT    # Phase 16D: Track B — 픽-테마 브릿지 강제
        + same_theme_hint                   # Phase 16J: 동일 theme 연속 시 opener 강화 (조건부)
        + _p1_intro_block                   # [Phase 19] Post1 도입부 금지 구절 (동적)
        + _P16B_POST2_ANGLE_DIVERSIFICATION # Phase 16B: 도입부 각도 차별화 (Track B)
        + _P16B_QUALITY_HARDENING_RULES     # Phase 16B: generic 금지 + spine + premium tone
        + continuation_block                # Phase 14: Post1 결론 + 연속성 강제
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

    # Phase 20: writer_used_evidence_ids 로그 + lead drift 체크
    if writer_contract and draft:
        used_ids = _parse_writer_evidence_ids(draft)
        logger.info(
            f"[Phase 20] writer evidence | run_id={run_id} | post_type=post2 | "
            f"writer_used_evidence_ids={used_ids}"
        )
        _check_p20_lead_metrics(writer_contract, used_ids, run_id, "post2")

    return draft


# ── Phase 17: PARSE_FAILED 런타임 분류 체계 ─────────────────────────────────────
# TYPE_A: H2/H3 구조 누락 또는 섹션 순서 불일치
# TYPE_B: 금지된 opener 패턴으로 인한 후처리 불일치
# TYPE_C: HTML 태그 파손 또는 중첩 오류
# TYPE_D: source box / 체크포인트 / 종목 구간 파싱 실패
# TYPE_E: reviser 수정 후 구조 재파손
# TYPE_UNKNOWN: 위 분류로 설명되지 않는 실패

def _classify_parse_failed(raw: str, normalized: Optional[str] = None,
                           *, is_html_context: bool = True) -> str:
    """Phase 17: PARSE_FAILED 발생 원인을 TYPE_A~TYPE_E 또는 TYPE_UNKNOWN으로 분류.

    [Phase 19] is_html_context 파라미터 추가:
    - is_html_context=True (기본): HTML 본문에서 h2/h3 부재 시 TYPE_A
    - is_html_context=False: verifier JSON 응답 컨텍스트 — h2/h3 부재는 정상이므로 TYPE_A 제외.
      JSON 파싱 자체 실패는 TYPE_UNKNOWN으로 분류해 차단하지 않음.
    """
    if raw is None:
        return "TYPE_UNKNOWN"
    # TYPE_A: H2/H3 구조 이상 — HTML 컨텍스트에서만 적용 (verifier JSON 응답에는 미적용)
    if is_html_context and re.search(r"<h[23][^>]*>", raw) is None:
        return "TYPE_A"
    # TYPE_B: opener 금지 패턴 존재 → 후처리 불일치 가능
    opener_banned = ["오늘 이 테마를 보는 이유", "오늘 시장을 보는 이유",
                     "최근 거시 환경을 먼저 보면", "글로벌 매크로 흐름",
                     "이번 시장 변수는", "최근 변동성이 커지면서"]
    if any(p in raw for p in opener_banned):
        return "TYPE_B"
    # TYPE_C: HTML 태그 파손 (닫는 태그 누락 또는 중첩 오류 의심)
    # [Phase 19] self-closing 요소(img, input, link, meta, br, hr)는 open_tag 카운트 제외
    # [Phase 22] is_html_context=False(verifier JSON 컨텍스트)에서는 TYPE_C 체크 제외.
    #   JSON 응답에 HTML 태그가 텍스트로 언급될 수 있어 카운트 오탐 발생.
    open_tags  = len(re.findall(r"<(?!/)(?!br|hr|img|input|link|meta|!)[a-zA-Z][^>]*>", raw))
    close_tags = len(re.findall(r"</[a-zA-Z]+>", raw))
    if is_html_context and abs(open_tags - close_tags) > 5:
        return "TYPE_C"
    # TYPE_D: source box / 체크포인트 / PICKS 주석 파싱 실패
    if "<!-- PICKS:" not in raw and len(raw) > 500:
        return "TYPE_D"
    # TYPE_E: reviser 수정 후 구조 재파손 — normalized가 raw보다 현저히 짧을 때
    if normalized and len(normalized) < len(raw) * 0.6:
        return "TYPE_E"
    return "TYPE_UNKNOWN"


def _calc_quality_pass_fields(content: str) -> dict:
    """Phase 19: 품질 pass 필드 4종을 계산해 dict로 반환한다.

    PARSE_FAILED 경로 / 정상 발행 경로 양쪽에서 동일 정의로 사용한다.
    bool 값과 계산 기준이 두 경로 간에 항상 일치하도록 이 함수를 단일 진실 소스로 유지한다.

    반환 키:
        opener_pass          — pick-angle H3 패턴 존재 + 금지 opener 6종 미포함
        criteria_1_pass      — 시점 혼합 금지 간이 판정 PASS (간이 지표)
        criteria_5_pass      — 권유성 표현 6종 미포함
        source_structure_pass — 참고 출처 블록 존재 여부
    """
    _raw = content or ""

    # opener_pass: pick-angle H3 패턴 존재 + 금지 opener 6종 미포함
    _opener_banned = [
        "오늘 이 테마를 보는 이유", "최근 거시 환경을 먼저 보면",
        "이번 시장 변수는", "최근 투자 환경을 보면",
        "현재 시장의 관심은", "현 시점에서 주목해야 할 것은",
    ]
    _has_pick_angle = bool(re.search(r"왜\s+지금\s+\S+인가|을\s+먼저\s+봐야\s+하는\s+이유", _raw))
    _has_banned_opener = any(p in _raw for p in _opener_banned)
    opener_pass: bool = _has_pick_angle and not _has_banned_opener

    # criteria_5_pass (권유성 표현 부재): 기준5 금지 표현 미포함 여부
    # [Phase 19] 단순 단어 매칭 → 투자 권유 맥락 패턴으로 좁힘
    # - "유망", "매수" 단독은 분석 문맥("유망한 CCL 섹터", "매수 물량")에서 오탐 발생
    # - 실제 투자 권유로 쓰이는 복합 패턴만 감지
    _criteria5_banned = [
        "담아야", "사야 할", "사야 한다",   # 직접 매수 권유
        "투자 추천", "강력 추천",            # 명시적 추천
        "유망 종목", "유망주",               # 종목 특정 권유
        "매수하세요", "지금 사야",           # 직접 권유 동사
        "매수 의견", "목표 주가",            # 증권사 의견 직접 채택형
    ]
    criteria_5_pass: bool = not any(p in _raw for p in _criteria5_banned)

    # criteria_1_pass (시점 혼합 금지 간이 판정): 30일 초과 연월 단독 언급 미포함 여부
    # 간이 지표: "지난해" / "작년" / "전년" 이 거시 배경 근거로 단독 등장하지 않으면 PASS
    # NOTE: 정밀 판정은 verifier가 담당 — 여기서는 간이 기록용
    _criteria1_risk = bool(re.search(r"지난\s*해|작년|전년\s*동기", _raw))
    criteria_1_pass: bool = not _criteria1_risk

    # source_structure_pass: 참고 출처 블록 존재 여부
    _source_markers = ["참고 출처", "📊", "증권사 리서치", "뉴스 기사"]
    source_structure_pass: bool = any(m in _raw for m in _source_markers)

    return {
        "opener_pass":           opener_pass,
        "criteria_1_pass":       criteria_1_pass,
        "criteria_5_pass":       criteria_5_pass,
        "source_structure_pass": source_structure_pass,
    }


def _log_normal_publish_event(
    *,
    run_id: str,
    slot: str,
    post_type: str,
    content: str,
    final_status: str,
    public_url: str,
) -> dict:
    """Phase 19: 정상 발행 경로 품질 필드 로그.

    PARSE_FAILED 경로(_log_parse_failed_event)와 동일한 4개 pass 필드를
    정상 발행 시에도 운영 로그에 직접 남긴다.
    필드 정의는 _calc_quality_pass_fields()로 통일된다.
    """
    qf = _calc_quality_pass_fields(content)
    log_entry = {
        "run_id":                run_id,
        "slot":                  slot,
        "post_type":             post_type,
        "final_status":          final_status,
        "public_url":            public_url,
        "opener_pass":           qf["opener_pass"],
        "criteria_1_pass":       qf["criteria_1_pass"],
        "criteria_5_pass":       qf["criteria_5_pass"],
        "source_structure_pass": qf["source_structure_pass"],
    }
    logger.info(
        f"[Phase 19] 정상발행 품질로그 | run_id={run_id} | slot={slot} | "
        f"post_type={post_type} | final_status={final_status} | "
        f"opener_pass={qf['opener_pass']} | criteria_1_pass={qf['criteria_1_pass']} | "
        f"criteria_5_pass={qf['criteria_5_pass']} | "
        f"source_structure_pass={qf['source_structure_pass']} | "
        f"public_url={public_url}"
    )
    return log_entry


def _log_parse_failed_event(
    *,
    run_id: str,
    slot: str,
    post_type: str,
    raw_output: str,
    normalized_output: Optional[str] = None,
    failed_section_name: str = "",
    parse_stage: str = "Step3:verifier",
    fallback_used: bool = True,
    publish_blocked: bool = False,
) -> dict:
    """Phase 17: PARSE_FAILED 런타임 이벤트를 구조화된 필드로 기록한다.

    Phase 19 보강:
    - picks_section_offset: PICKS 주석 구간의 문자 오프셋 (TYPE_D 정밀 분석용)
    - opener_pass / criteria_1_pass / criteria_5_pass / source_structure_pass:
      _calc_quality_pass_fields()로 계산 — 정상 발행 경로와 동일 정의 유지.

    반환: 로그 딕셔너리 (감사 / 관측 목적)
    필수 필드: run_id / slot / post_type / failure_type / parse_stage /
              failed_section_name / raw_output_snapshot / normalized_output_snapshot /
              fallback_used / publish_blocked
    권장 필드(Phase 19): picks_section_offset / opener_pass /
                         criteria_1_pass / criteria_5_pass / source_structure_pass
    """
    failure_type = _classify_parse_failed(raw_output, normalized_output)
    raw_snap   = (raw_output or "")[:500]
    norm_snap  = (normalized_output or "")[:500]

    # ── Phase 19 T1-2: PICKS 구간 offset 탐지 ────────────────────────────
    _picks_markers = ["<!-- PICKS:", "<!-- picks:", "<!-- PICKS -->",
                      "<!-- picks -->", "PICKS:", "picks:"]
    picks_section_offset: int = -1
    for _marker in _picks_markers:
        _pos = (raw_output or "").find(_marker)
        if _pos >= 0:
            picks_section_offset = _pos
            break

    # ── Phase 19 T1-3: 권장 필드 4종 — 공통 헬퍼로 계산 (정상 경로와 동일 정의) ──
    qf = _calc_quality_pass_fields(raw_output or "")
    opener_pass           = qf["opener_pass"]
    criteria_1_pass       = qf["criteria_1_pass"]
    criteria_5_pass       = qf["criteria_5_pass"]
    source_structure_pass = qf["source_structure_pass"]

    log_entry = {
        # ── 필수 10필드 (Phase 17) ──────────────────────────────────────
        "run_id":                     run_id,
        "slot":                       slot,
        "post_type":                  post_type,
        "failure_type":               failure_type,
        "parse_stage":                parse_stage,
        "failed_section_name":        failed_section_name,
        "raw_output_snapshot":        raw_snap,
        "normalized_output_snapshot": norm_snap,
        "fallback_used":              fallback_used,
        "publish_blocked":            publish_blocked,
        # ── 권장 필드 (Phase 19) ────────────────────────────────────────
        "picks_section_offset":       picks_section_offset,
        "opener_pass":                opener_pass,
        "criteria_1_pass":            criteria_1_pass,
        "criteria_5_pass":            criteria_5_pass,
        "source_structure_pass":      source_structure_pass,
    }

    logger.warning(
        f"[Phase 19] PARSE_FAILED 런타임 이벤트 | run_id={run_id} | slot={slot} | "
        f"post_type={post_type} | failure_type={failure_type} | "
        f"parse_stage={parse_stage} | failed_section={failed_section_name or '(unknown)'} | "
        f"fallback_used={fallback_used} | publish_blocked={publish_blocked} | "
        f"picks_offset={picks_section_offset} | opener_pass={opener_pass} | "
        f"criteria_1_pass={criteria_1_pass} | criteria_5_pass={criteria_5_pass} | "
        f"source_structure_pass={source_structure_pass}"
    )
    logger.debug(f"[Phase 19] raw_snapshot: {raw_snap!r}")
    if norm_snap:
        logger.debug(f"[Phase 19] normalized_snapshot: {norm_snap!r}")
    return log_entry


def verify_draft(draft: str, *, slot: str = "unknown", post_type: str = "unknown") -> dict:
    """
    Step 3: Gemini 검수 엔진 (2단계 분리 방식).

    Phase 19 T1-1: slot / post_type 파라미터 추가.
    PARSE_FAILED 발생 시 _log_parse_failed_event()에 정상 값을 전달한다.

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
        response_mime_type="application/json",  # [Phase 19] JSON 강제 — PARSE_FAILED TYPE_A 방지
    )
    result = _parse_json_response(raw) if raw else None

    if not result or not isinstance(result, dict):
        logger.warning(
            "[Phase 16J/17] Step3 검수 결과 파싱 실패 (step3_status=PARSE_FAILED) "
            "— Gemini 응답이 JSON으로 파싱 불가 → 검수 단계 skip, GPT 초안 원본 발행 경로. "
            "FAILED_NO_REVISION과 달리 수정 시도 없이 즉시 통과 처리."
        )
        # Phase 17/19: 구조화된 PARSE_FAILED 런타임 로그 기록
        # Phase 18: TYPE별 발행 차단 정책 적용
        #   TYPE_A (구조 전무) / TYPE_B (금지 패턴) / TYPE_C (HTML 파손) → 차단
        #   TYPE_D (PICKS 주석 누락) / TYPE_E (reviser 과도 축소) / TYPE_UNKNOWN → 허용
        # [Phase 19] is_html_context=False: verifier 응답은 JSON이므로 h2/h3 부재를
        #   HTML 구조 전무로 오분류(TYPE_A)하지 않음 → TYPE_UNKNOWN으로 처리(허용)
        _pf_type = _classify_parse_failed(raw or "", is_html_context=False)
        _BLOCK_TYPES = {"TYPE_A", "TYPE_B", "TYPE_C"}
        _pf_blocked = _pf_type in _BLOCK_TYPES
        _log_parse_failed_event(
            run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            slot=slot,
            post_type=post_type,
            raw_output=raw or "",
            parse_stage="Step3:verifier:json_parse",
            failed_section_name="verifier_response",
            fallback_used=True,
            publish_blocked=_pf_blocked,
        )
        if _pf_blocked:
            logger.error(
                f"[Phase 18] PARSE_FAILED {_pf_type} — 발행 차단 유형 감지 "
                f"(TYPE_A/B/C 정책: 구조 파손·금지 패턴·HTML 파손). "
                f"draft 무결성 불확실 → 발행 중단."
            )
        else:
            logger.warning(
                f"[Phase 18] PARSE_FAILED {_pf_type} — 허용 유형 "
                f"(TYPE_D/E/UNKNOWN 정책). GPT 초안 원본 발행 경로 유지."
            )
        return {"pass": True, "issues": [], "revised_content": None,
                "step3_status": "PARSE_FAILED",
                "parse_failed_type": _pf_type,        # Phase 18
                "parse_failed_blocked": _pf_blocked,  # Phase 18
                }  # Phase 16B/16J: status 추적

    passed = result.get("pass", True)
    issues = result.get("issues", [])
    revised = None  # Step 3b에서 별도 채움
    # Phase 16B/16F/16J step3_status enum (표준, Phase 16F에서 통일 / 16J에서 PARSE_FAILED 추가):
    #   "PASS"              — Step3 팩트체크 이슈 없음 (검수 통과)
    #   "REVISED"           — Step3 이슈 발견, 수정본 채택 (구 보고서 표기: "FAILED_REVISION_ADOPTED"와 동일)
    #   "FAILED_NO_REVISION"— Step3 수정 API 실패 (503/timeout 등), GPT 초안 원본 발행
    #   "PARSE_FAILED"      — [Phase 16J] Gemini 검수 응답 JSON 파싱 불가 → 검수 단계 skip.
    #                         GPT 초안 원본 발행 (FAILED_NO_REVISION과 달리 수정 시도 자체 없음).
    #                         운영 해석: verifier가 비표준 형식을 반환한 것 — 검수 실질 미실행.
    #                         발행은 정상 진행되나 Step3 품질 보호 없이 발행됨.
    step3_status = "PASS"

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
            step3_status = "REVISED"  # Phase 16B
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
            step3_status = "FAILED_NO_REVISION"  # Phase 16B: 503/timeout 케이스
            logger.warning(
                f"[Phase 16B] Step3 수정 호출 실패 (step3_status=FAILED_NO_REVISION) "
                f"— GPT 초안 원본 발행 경로"
            )

    return {"pass": passed, "issues": issues, "revised_content": revised,
            "step3_status": step3_status}  # Phase 16B: status 포함


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
    raw = _call_gemini(GEMINI_TICKER_V2_SYSTEM, user_msg, "Post2-Step1:종목선정", temperature=0.2,
                       response_mime_type="application/json")  # [Phase 19] JSON 강제
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

def generate_deep_analysis(news: list, research: list, slot: str = "default",
                           forced_theme: str = "") -> dict:
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

    # ── Phase 16: 시제 SSOT 구축 + GPT 생성 컨텍스트에 주입 ───────────────
    _p16_run_year  = int(datetime.now().strftime("%Y"))
    _p16_run_month = int(datetime.now().strftime("%m"))
    _p16_ssot      = _build_temporal_ssot(_p16_run_year, _p16_run_month)
    _p16_gen_block = _build_p16_generation_block(_p16_ssot)
    context_text   = _p16_gen_block + context_text
    logger.info(
        f"[Phase 16] Post1 시제 SSOT 주입: 완료 연도={_p16_ssot['completed_years']}, "
        f"완료 월={_p16_ssot['completed_months_this_year']}"
    )

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

    # ── Phase A: 거시지표 스냅샷 조회 + history_ctx 주입 ─────────────────
    _p21_macro_snap = {}
    if _MACRO_DATA_AVAILABLE:
        try:
            _p21_macro_snap = get_macro_snapshot()
            _p21_macro_text = format_macro_for_prompt(_p21_macro_snap)
            if _p21_macro_text:
                history_ctx = history_ctx + _p21_macro_text
                logger.info(f"[Phase A] 거시지표 스냅샷 주입 완료 ({len(_p21_macro_text)}자)")
        except Exception as _p21_e:
            logger.warning(f"[Phase A] 거시지표 조회 실패 (비치명): {_p21_e}")

    # ── Phase B: 지식베이스 — 관련 과거 글 검색 + history_ctx 주입 ────────
    if _KB_AVAILABLE:
        try:
            _kb_ctx = kb_retrieve(query_theme="", query_news_text=news_text[:500])
            if _kb_ctx:
                history_ctx = history_ctx + _kb_ctx
                logger.info(f"[Phase B] KB 컨텍스트 주입 완료 ({len(_kb_ctx)}자)")
        except Exception as _kb_e:
            logger.warning(f"[Phase B] KB 검색 실패 (비치명): {_kb_e}")

    # ── Phase R: 거시경제 리포트 컨텍스트 주입 ────────────────────────────
    _pr_few_shot_suffix = ""
    if _REFERENCE_LOADER_AVAILABLE:
        try:
            _pr_reports = load_reference_reports()
            _pr_report_ctx = format_reports_for_prompt(_pr_reports)
            if _pr_report_ctx:
                history_ctx = history_ctx + _pr_report_ctx
                logger.info(f"[Phase R] 리포트 컨텍스트 주입 완료 ({len(_pr_report_ctx)}자, {len(_pr_reports.get('reports', []))}건)")
            _pr_examples = load_few_shot_examples()
            _pr_few_shot_suffix = format_few_shot_for_prompt(_pr_examples)
            if _pr_few_shot_suffix:
                logger.info(f"[Phase R] Few-shot 예시 {len(_pr_examples)}건 로드 완료")
        except Exception as _pr_e:
            logger.warning(f"[Phase R] 리포트/Few-shot 로드 실패 (비치명): {_pr_e}")
            _pr_few_shot_suffix = ""

    # ── Step 1: Gemini 분석 재료 생성 ─────────────────────────────────────
    materials = gemini_analyze(news_text, research_text, dart_text=dart_text,
                               slot=slot, history_context=history_ctx,
                               forced_theme=forced_theme)  # [Phase 22]
    theme = materials.get("theme", "글로벌 경제 주요 이슈")

    # ── Step 1.5: Editorial Planner (Phase 20) ─────────────────────────────
    _p20_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    _p20_post1_planner = None
    _p20_post1_contract = None
    try:
        _p20_post1_planner = _call_editorial_planner(
            step1=materials,
            post_type="post1",
            slot=slot,
            run_id=_p20_run_id,
            history_constraints=history_ctx[:400] if history_ctx else None,
        )
        if _p20_post1_planner:
            _p20_post1_contract = _build_writer_contract(
                step1=materials,
                planner=_p20_post1_planner,
                slot=slot,
            )
    except Exception as _p20_e:
        logger.warning(f"[Phase 20] Post1 planner 예외 — fallback | {_p20_e}")

    # ── Step 2: GPT 심층 분석 초고 작성 ───────────────────────────────────
    draft = gpt_write_analysis(materials, context_text, slot=slot,
                               writer_contract=_p20_post1_contract,
                               run_id=_p20_run_id,
                               few_shot_suffix=_pr_few_shot_suffix)
    draft = _strip_code_fences(draft)  # Phase 4.3: 코드펜스/백틱 제거

    # ── Step 2.5: 후처리 밀도/반복 감지 (경고 로그만) ────────────────────
    _postprocess_density_check(draft, label="Post1")

    # ── Step 3: Gemini 팩트체크 + 수정 ────────────────────────────────────
    # Phase 19 T1-1: slot / post_type 전달 (PARSE_FAILED 로그 보강)
    draft_len = len(draft)
    verify_result = verify_draft(draft, slot=slot, post_type="post1")
    _p1_step3_status = verify_result.get("step3_status", "PASS")  # Phase 16B
    # Phase 18: PARSE_FAILED 차단 유형(TYPE_A/B/C) 감지 시 발행 중단
    if verify_result.get("parse_failed_blocked", False):
        _pf_t = verify_result.get("parse_failed_type", "UNKNOWN")
        raise RuntimeError(
            f"[Phase 18] PARSE_FAILED {_pf_t} — Post1 발행 차단 유형. "
            f"파이프라인을 중단합니다."
        )
    if not verify_result["pass"] and verify_result.get("revised_content"):
        logger.info("Step3 검수 실패 — 수정본 채택")
        final_content = verify_result["revised_content"]
    else:
        final_content = draft

    # ── Phase 16B/16D Track A+D: emergency quality diagnostic (항상 실행) ────
    final_content, _p16b_polish_log = _p16b_emergency_polish(
        final_content, label="Post1", step3_status=_p1_step3_status
    )

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
    # ── Phase D: 거시지표 교차검증 ────────────────────────────────────────
    p_d_macro = _check_macro_facts(final_content, _p21_macro_snap)

    # ── Phase 14I Track C: weak_interp OR hedge_overuse FAIL 시 타겟 블록 교체 ─
    weak_hits   = p13_interp.get("weak_interp_hits", 0)
    hedge_ovuse = p13_interp.get("hedge_overuse", "PASS")  # "FAIL"|"WARN"|"PASS"
    # spine은 이 시점에 아직 추출 전이므로 SPINE 주석에서 직접 추출
    _pre_spine  = _extract_post1_spine(final_content)
    final_content = _enforce_interpretation_rewrite(
        final_content,
        weak_interp_hits=weak_hits,
        label="Post1",
        article_spine=_pre_spine,
        hedge_overuse_status=hedge_ovuse,     # Phase 14I 신규
    )
    # 재작성 후 품질 재진단
    if weak_hits >= 3 or hedge_ovuse == "FAIL":
        p13_interp = _score_interpretation_quality(final_content, label="Post1-재작성후")

    # ── Phase 15: 완료 연도 시제 교정 (Track D → Track E) ─────────────────
    _run_year_int = int(datetime.now().strftime("%Y"))
    p15_tense_diag = _detect_completed_year_as_forecast(final_content, run_year=_run_year_int)
    if p15_tense_diag["status"] == "FAIL":
        final_content, _p15_log = _enforce_tense_correction(
            final_content, run_year=_run_year_int, label="Post1"
        )
        # 교정 후 temporal 재진단
        p13_temporal = _check_temporal_sanity(final_content, run_date_str)
        p15_tense_diag_after = _detect_completed_year_as_forecast(
            final_content, run_year=_run_year_int
        )
        p15_tense_diag["after_correction"] = p15_tense_diag_after
        # [Phase 19] quality gate가 교정 전 FAIL을 반환하던 버그 수정 — 교정 후 상태로 업데이트
        p15_tense_diag["pre_correction_status"] = "FAIL"
        p15_tense_diag["status"] = p15_tense_diag_after["status"]
    else:
        _p15_log = []

    # ── Phase 15D: [전망] 태그 오주입 탐지 (진단 전용) ──────────────────────────
    _, _p15d_log = _strip_misapplied_jeonmang_tags(
        final_content, run_year=_run_year_int, label="Post1"
    )

    # ── Phase 15E: 현재 연도 과거 월 시제 + [전망] 태그 탐지 (진단 전용) ─────────
    _, _p15e_log = _enforce_current_year_month_settlement(
        final_content, run_year=_run_year_int, label="Post1"
    )

    # ── Phase 15F: 현재 연도 과거 월 [전망] 동사형 독립 탐지 (진단 전용) ─────────
    _, _p15f_log = _strip_current_year_past_month_jeonmang(
        final_content, ssot=_p16_ssot, label="Post1"
    )

    p13_scores: dict = {
        "interpretation":   p13_interp,
        "temporal":         p13_temporal,
        "numeric":          p13_numeric,
        "macro_facts":      p_d_macro,         # Phase D: 거시지표 교차검증
        "closure":          p13_closure,
        "tense":            p15_tense_diag,   # Phase 15: 완료 연도 시제 진단
        "jeonmang_strip":   {"stripped_count": len(_p15d_log), "log": _p15d_log},  # Phase 15D
        "month_settlement": _p15e_log,         # Phase 15E: 현재 연도 과거 월 교정
        "p15f_strip":       {"stripped_count": len(_p15f_log), "log": _p15f_log},  # Phase 15F/16
        "p16_ssot_run":     {"run_year": _p16_ssot["run_year"], "run_month": _p16_ssot["run_month"],
                             "completed_years": _p16_ssot["completed_years"],
                             "completed_months": _p16_ssot["completed_months_this_year"]},
        "p16b_guard": {                        # Phase 16B/16J: 품질 하드닝 진단
            "step3_status":            _p1_step3_status,
            # PASS / REVISED / FAILED_NO_REVISION / PARSE_FAILED
            "fallback_triggered":      _p1_step3_status == "FAILED_NO_REVISION",
            "parse_failed":            _p1_step3_status == "PARSE_FAILED",  # [Phase 16J]
            "parse_failed_type":       verify_result.get("parse_failed_type", None),  # [Phase 18]
            "emergency_polish":        _p16b_polish_log,
            "intro_overlap":           None,   # Post1은 단독 — 비교 대상 없음
        },
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

    # [Phase 21] SEO_TITLE 추출 (WordPress slug 설정용)
    seo_title = _extract_seo_title(final_content)
    if seo_title:
        logger.info(f"[Phase 21] Post1 SEO_TITLE 추출: '{seo_title}'")

    # key_data: facts의 content 목록 (Post 2 전달용)
    key_data = [f.get("content", "") for f in materials.get("facts", [])[:5]]

    # ── Phase C: 면책 문구 자동 주입 ────────────────────────────────────────
    final_content = _inject_disclaimer(final_content)

    logger.info(f"Post1 생성 완료 | 제목: '{title}' | HTML {len(final_content)}자")

    # ── Phase B: 지식베이스 저장 ────────────────────────────────────────────
    if _KB_AVAILABLE:
        try:
            kb_save("post1", theme, title, final_content, tickers=None, slot=slot)
        except Exception as _kb_e:
            logger.warning(f"[KB] Post1 저장 실패 (무시): {_kb_e}")

    return {
        "title":          title,
        "seo_title":      seo_title,      # [Phase 21] SEO slug 소스
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

    # ── Phase 16: 시제 SSOT 구축 + GPT 생성 컨텍스트에 주입 ───────────────
    _p2_p16_run_year  = int(datetime.now().strftime("%Y"))
    _p2_p16_run_month = int(datetime.now().strftime("%m"))
    _p2_p16_ssot      = _build_temporal_ssot(_p2_p16_run_year, _p2_p16_run_month)
    _p2_p16_gen_block = _build_p16_generation_block(_p2_p16_ssot)
    context_text      = _p2_p16_gen_block + context_text
    logger.info(
        f"[Phase 16] Post2 시제 SSOT 주입: 완료 연도={_p2_p16_ssot['completed_years']}, "
        f"완료 월={_p2_p16_ssot['completed_months_this_year']}"
    )

    # ── Phase A: 거시지표 스냅샷 주입 (Post2) ─────────────────────────────
    _p21_macro_snap_p2: dict = {}
    if _MACRO_DATA_AVAILABLE:
        try:
            _p21_macro_snap_p2 = get_macro_snapshot()
            _p21_macro_text_p2 = format_macro_for_prompt(_p21_macro_snap_p2)
            if _p21_macro_text_p2:
                context_text = context_text + _p21_macro_text_p2
                logger.info("[Phase A] Post2 거시지표 스냅샷 주입 완료")
        except Exception as _macro_e2:
            logger.warning(f"[Phase A] Post2 거시지표 조회 실패 (무시): {_macro_e2}")

    # ── Phase B: 지식베이스 컨텍스트 주입 (Post2) ─────────────────────────
    if _KB_AVAILABLE:
        try:
            _kb_ctx_p2 = kb_retrieve(query_theme=theme, query_news_text=news_text[:500])
            if _kb_ctx_p2:
                context_text = context_text + _kb_ctx_p2
                logger.info("[Phase B] Post2 KB 컨텍스트 주입 완료")
        except Exception as _kb_e2:
            logger.warning(f"[Phase B] Post2 KB 검색 실패 (무시): {_kb_e2}")

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

    # [Phase 19] Post1 도입부 텍스트 추출 (post1_post2_continuity 방지용 금지 구절)
    _p19_m = re.search(r"<h[23][^>]*>", post1_content, re.IGNORECASE) if post1_content else None
    _p19_body = post1_content[_p19_m.start():] if _p19_m else (post1_content or "")
    _p19_post1_intro = re.sub(r"<[^>]+>", " ", _p19_body)[:350].strip()

    # ── Phase 16J Track B: 동일 theme 연속 진단 (opener 강화 + 경고) ──────
    _p16j_theme_diag = _p16j_check_theme_repeat(materials.get("theme", theme))
    _p16j_same_theme_hint = (
        _P16J_POST2_SAME_THEME_OPENER if _p16j_theme_diag["is_repeat"] else ""
    )

    # ── Step 1.5: Editorial Planner (Phase 20) ─────────────────────────────
    _p20_post2_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    _p20_post2_planner = None
    _p20_post2_contract = None
    try:
        _p20_post2_planner = _call_editorial_planner(
            step1=materials,
            post_type="post2",
            slot=slot,
            run_id=_p20_post2_run_id,
        )
        if _p20_post2_planner:
            _p20_post2_contract = _build_writer_contract(
                step1=materials,
                planner=_p20_post2_planner,
                slot=slot,
            )
    except Exception as _p20_e2:
        logger.warning(f"[Phase 20] Post2 planner 예외 — fallback | {_p20_e2}")

    # ── Step 2: GPT 종목 리포트 작성 ──────────────────────────────────────
    draft = gpt_write_picks(materials, picks, prices, context_text, slot=slot,
                            post1_spine=post1_spine,
                            same_theme_hint=_p16j_same_theme_hint,
                            writer_contract=_p20_post2_contract,
                            run_id=_p20_post2_run_id,
                            post1_intro_text=_p19_post1_intro)  # [Phase 19]
    draft = _strip_code_fences(draft)  # Phase 4.3: 코드펜스/백틱 제거

    # ── Step 2.5: 후처리 밀도/반복 감지 (경고 로그만) ────────────────────
    _postprocess_density_check(draft, label="Post2")

    # ── Step 3: Gemini 팩트체크 + 수정 ────────────────────────────────────
    # Phase 19 T1-1: slot / post_type 전달 (PARSE_FAILED 로그 보강)
    post2_draft_len = len(draft)
    verify_result = verify_draft(draft, slot=slot, post_type="post2")
    _p2_step3_status = verify_result.get("step3_status", "PASS")  # Phase 16B
    # Phase 18: PARSE_FAILED 차단 유형(TYPE_A/B/C) 감지 시 Post2 생성 중단
    # Post2 차단은 RuntimeError로 전파 → main.py에서 post2=None으로 처리
    if verify_result.get("parse_failed_blocked", False):
        _pf_t2 = verify_result.get("parse_failed_type", "UNKNOWN")
        raise RuntimeError(
            f"[Phase 18] PARSE_FAILED {_pf_t2} — Post2 발행 차단 유형. "
            f"Post2 생성을 중단합니다."
        )
    if not verify_result["pass"] and verify_result.get("revised_content"):
        logger.info("Post2 Step3 검수 실패 — 수정본 채택")
        raw_content = verify_result["revised_content"]
    else:
        raw_content = draft

    # ── Phase 16B/16D Track A+D: emergency quality diagnostic (항상 실행) ────
    raw_content, _p2_16b_polish_log = _p16b_emergency_polish(
        raw_content, label="Post2", step3_status=_p2_step3_status
    )

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
    p_d_macro_p2   = _check_macro_facts(final_content, _p21_macro_snap_p2)  # Phase D
    p13_closure    = _check_verifier_closure(
        verify_result.get("issues", []), draft, raw_content
    )
    p13_continuity = _check_post_continuity(post1_content, final_content)

    # ── Phase 14I Track C: weak_interp OR hedge_overuse FAIL 시 타겟 블록 교체 ─
    p2_weak_hits  = p13_interp.get("weak_interp_hits", 0)
    p2_hedge_ovuse = p13_interp.get("hedge_overuse", "PASS")
    final_content = _enforce_interpretation_rewrite(
        final_content,
        weak_interp_hits=p2_weak_hits,
        label="Post2",
        article_spine=post1_spine,
        hedge_overuse_status=p2_hedge_ovuse,   # Phase 14I 신규
    )
    if p2_weak_hits >= 3 or p2_hedge_ovuse == "FAIL":
        p13_interp = _score_interpretation_quality(final_content, label="Post2-재작성후")

    # ── Phase 15: 완료 연도 시제 교정 (Track D → Track E, Post2 엄격 적용) ─
    _p2_run_year_int = int(datetime.now().strftime("%Y"))
    p15_tense_diag_p2 = _detect_completed_year_as_forecast(
        final_content, run_year=_p2_run_year_int
    )
    if p15_tense_diag_p2["status"] == "FAIL":
        final_content, _p15_log_p2 = _enforce_tense_correction(
            final_content, run_year=_p2_run_year_int, label="Post2"
        )
        # 교정 후 temporal 재진단
        p13_temporal = _check_temporal_sanity(final_content, _run_date_str)
        p15_tense_diag_p2_after = _detect_completed_year_as_forecast(
            final_content, run_year=_p2_run_year_int
        )
        p15_tense_diag_p2["after_correction"] = p15_tense_diag_p2_after
        # [Phase 19] quality gate가 교정 전 FAIL을 반환하던 버그 수정
        p15_tense_diag_p2["pre_correction_status"] = "FAIL"
        p15_tense_diag_p2["status"] = p15_tense_diag_p2_after["status"]
    else:
        _p15_log_p2 = []

    # ── Phase 15C Track D: 내부 파이프라인 레이블 노출 탐지 ──────────────────
    p15c_label_diag = _detect_internal_label_leakage(final_content, label="Post2")

    # ── Phase 15D: [전망] 태그 오주입 탐지 (진단 전용) ──────────────────────────
    _, _p15d_log_p2 = _strip_misapplied_jeonmang_tags(
        final_content, run_year=_p2_run_year_int, label="Post2"
    )

    # ── Phase 15E: 현재 연도 과거 월 시제 + [전망] 태그 탐지 (진단 전용) ─────────
    _, _p15e_log_p2 = _enforce_current_year_month_settlement(
        final_content, run_year=_p2_run_year_int, label="Post2"
    )

    # ── Phase 15F: 현재 연도 과거 월 [전망] 동사형 독립 탐지 (진단 전용) ─────────
    _, _p15f_log_p2 = _strip_current_year_past_month_jeonmang(
        final_content, ssot=_p2_p16_ssot, label="Post2"
    )

    # ── Phase 16B Track B: 도입부 n-gram 중복 계산 ────────────────────────
    _p16b_intro_overlap = _p16b_compute_intro_overlap(
        post1_content, final_content, n=4
    )

    # ── Phase 16F Track C: 브릿지 타입 진단 (관측 전용) ─────────────────
    _p16f_bridge_diag = _p16f_diagnose_bridge(final_content, parsed_picks)

    p13_scores: dict = {
        "interpretation":   p13_interp,
        "temporal":         p13_temporal,
        "numeric":          p13_numeric,
        "macro_facts":      p_d_macro_p2,          # Phase D: 거시지표 교차검증
        "closure":          p13_closure,
        "continuity":       p13_continuity,
        "tense":            p15_tense_diag_p2,   # Phase 15: 완료 연도 시제 진단
        "label_leak":       p15c_label_diag,      # Phase 15C: 내부 레이블 노출 진단
        "jeonmang_strip":   {"stripped_count": len(_p15d_log_p2), "log": _p15d_log_p2},  # Phase 15D
        "month_settlement": _p15e_log_p2,          # Phase 15E: 현재 연도 과거 월 교정
        "p15f_strip":       {"stripped_count": len(_p15f_log_p2), "log": _p15f_log_p2},  # Phase 15F/16
        "p16_ssot_run":     {"run_year": _p2_p16_ssot["run_year"], "run_month": _p2_p16_ssot["run_month"],
                             "completed_years": _p2_p16_ssot["completed_years"],
                             "completed_months": _p2_p16_ssot["completed_months_this_year"]},
        "p16b_guard": {                            # Phase 16B/16F/16J: 품질 하드닝 진단
            "step3_status":         _p2_step3_status,  # PASS / REVISED / FAILED_NO_REVISION / PARSE_FAILED
            "fallback_triggered":   _p2_step3_status == "FAILED_NO_REVISION",
            "parse_failed":         _p2_step3_status == "PARSE_FAILED",  # [Phase 16J]
            "parse_failed_type":    verify_result.get("parse_failed_type", None),  # [Phase 18]
            "emergency_polish":     _p2_16b_polish_log,
            "intro_overlap":        _p16b_intro_overlap,
            "bridge_diag":          _p16f_bridge_diag,  # Phase 16F: 브릿지 타입 진단
            "theme_repeat_diag":    _p16j_theme_diag,   # [Phase 16J Track B]: 동일 theme 연속 진단
        },
    }

    # ── Phase C: 면책 문구 자동 주입 ────────────────────────────────────────
    final_content = _inject_disclaimer(final_content)

    # [Phase 21] SEO_TITLE 추출 (WordPress slug 설정용)
    seo_title_p2 = _extract_seo_title(final_content)
    if seo_title_p2:
        logger.info(f"[Phase 21] Post2 SEO_TITLE 추출: '{seo_title_p2}'")

    logger.info(f"Post2 생성 완료 | 제목: '{title}' | HTML {len(final_content)}자")

    # ── Phase B: 지식베이스 저장 ────────────────────────────────────────────
    if _KB_AVAILABLE:
        try:
            _p2_tickers = [p.get("ticker", "") for p in parsed_picks if p.get("ticker")]
            kb_save("post2", theme, title, final_content, tickers=_p2_tickers, slot=slot)
        except Exception as _kb_e:
            logger.warning(f"[KB] Post2 저장 실패 (무시): {_kb_e}")

    return {
        "title":                title,
        "seo_title":            seo_title_p2,           # [Phase 21] SEO slug 소스
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
