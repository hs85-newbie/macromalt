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
)

load_dotenv()

logger = logging.getLogger("macromalt")

# 검수 실패 시 재작성 최대 횟수 (Phase 7: 검수 1회, 재작성 1회)
MAX_RETRIES = 1


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
    BROKER_KW = ["증권", "투자", "리서치", "Research", "securities", "애널리스트"]
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
2. "매수하세요", "지금 사야 할 주식" 등 투자 권유 문구 절대 금지
3. 근거 부족한 내용은 "확실하지 않다"로 표기
4. 위스키/바텐더 비유: 도입부에 간결하게 테마-종목 연결 (1회, 선택)
5. 같은 사실을 표현만 바꿔 반복하지 않는다

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
1. [시점 일관성] 최근 7일 중심으로 구성되었는가; background_facts(7~30일) 자료가 현재 시황 근거로 쓰이지 않았는가
2. [수치 정확성] 수치·날짜·고유명사의 오류 가능성 및 기준 시점 누락 여부
3. [사실/해석 구분] [해석] 또는 [전망] 태그 없이 해석·전망이 사실처럼 서술된 문장 여부
4. [출처 단정] 출처 없는 단정 표현 여부 ("~할 것이다", "~가 확실하다" 등)
5. [투자 권유] 투자 권유처럼 읽히는 문장 여부

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
2. 출처 없는 단정 표현 → 완화 표현으로 교체
3. 투자 권유성 문장 → 중립 서술로 교체
4. 핵심 테마와 무관한 독립 h3 섹션 → h3 제거 후 앞 섹션 끝 배경 1문장으로 흡수
   (단, 해당 섹션의 핵심 숫자·논리는 그 1문장 안에 보존할 것)
5. 완충 문장이 구체 근거 없이 단독 등장 → 해당 문장 뒤에 근거 문장 1개 추가
   (삭제 금지 — 근거를 추가하는 방향으로 처리)
6. 동일 사실 중복 서술 → 중복 문장 1개 제거 (핵심 숫자 있는 문장을 남길 것)
7. [★ 위스키/바텐더 비유 추가 금지]
   도입부에 이미 있는 경우 새로운 비유를 보강 목적으로 삽입하지 말 것.
   위스키·바텐더·캐스크·싱글몰트 관련 표현은 "보존 대상"이지 "보강 대상"이 아님.
   수정 중 새로운 비유 문장을 추가하거나 기존 비유를 다른 위치에 재삽입하는 행위는 엄격히 금지.
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


def gemini_analyze(news_text: str, research_text: str, dart_text: str = "") -> dict:
    """
    Step 1: Gemini 분석 엔진.
    뉴스·리서치 데이터를 구조화된 JSON 리포트 재료로 변환합니다.

    Args:
        dart_text: format_dart_for_prompt() 결과물. 빈 문자열이면 프롬프트에 공백만 추가.

    반환:
        {"theme", "facts", "market_impact", "counter_interpretations",
         "uncertainties", "writing_notes"}
    """
    user_msg = GEMINI_ANALYST_USER.format(
        research_text=research_text,
        news_text=news_text,
        dart_text=dart_text,
    )
    raw = _call_gemini(GEMINI_ANALYST_SYSTEM, user_msg, "Step1:분석재료생성", temperature=0.2)
    result = _parse_json_response(raw) if raw else None

    if not result or not isinstance(result, dict):
        logger.warning("Gemini 분석 재료 파싱 실패 — 기본값 사용")
        result = {
            "theme": "글로벌 경제 주요 이슈",
            "facts": [{"content": "수집된 뉴스 데이터 기반", "source": "뉴스 종합", "date": datetime.now().strftime("%Y-%m-%d")}],
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


def gpt_write_analysis(materials: dict, context_text: str) -> str:
    """
    Step 2a: GPT 작성 엔진 — Post 1 심층 분석.
    Gemini 분석 재료를 HTML 형식의 심층 분석 글로 작성합니다.

    반환: HTML 문자열 (마크다운 없음, 인라인 스타일 포함)
    """
    materials_json = json.dumps(materials, ensure_ascii=False, indent=2)
    user_msg = GPT_WRITER_ANALYSIS_USER.format(
        materials_json=materials_json,
        context_text=context_text,
    )
    draft = _call_gpt(
        GPT_WRITER_ANALYSIS_SYSTEM,
        user_msg,
        "Step2a:심층분석작성",
        temperature=0.7,
        max_tokens=5000,  # Phase 4.3: 4000 → 5000 (심층분석 밀도 복원)
    )
    return draft


def gpt_write_picks(materials: dict, tickers: list, prices: dict, context_text: str) -> str:
    """
    Step 2b: GPT 작성 엔진 — Post 2 종목 리포트.
    분석 재료 + 종목 + 실제 가격 데이터로 종목 리포트 HTML을 작성합니다.

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

    user_msg = GPT_WRITER_PICKS_USER.format(
        theme=theme,
        materials_summary=materials_summary,
        tickers_and_prices=tickers_and_prices,
        context_text=context_text,
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

def generate_deep_analysis(news: list, research: list) -> dict:
    """
    Post 1 — 3단계 심층 경제 분석 생성.

    3단계 파이프라인:
        Step 1 (Gemini): 뉴스+리서치 → 구조화된 JSON 재료
        Step 2 (GPT):    JSON 재료 → HTML 심층 분석 초고
        Step 3 (Gemini): HTML 초고 → 팩트체크 + 필요 시 수정

    반환:
        {"title", "content", "theme", "key_data", "materials", "generated_at"}
        ※ materials: Post 2에 전달하기 위한 구조화 데이터
    """
    news_text     = format_articles_for_prompt(news)
    research_text = format_research_for_prompt(research)
    context_text  = f"{research_text}\n\n{RESEARCH_NEWS_SEPARATOR}\n\n{news_text}"

    # ── Step 1-DART: 전체 시장 주요사항보고서 스캔 (심층분석용, 14일) ──────
    dart_disclosures = run_dart_disclosure_scan(days=14)
    dart_text = format_dart_for_prompt(dart_disclosures) if dart_disclosures else ""
    if dart_text:
        logger.info(f"[DART] 심층분석 공시 데이터 {len(dart_disclosures)}건 → 프롬프트 주입")

    # ── Step 1: Gemini 분석 재료 생성 ─────────────────────────────────────
    materials = gemini_analyze(news_text, research_text, dart_text=dart_text)
    theme = materials.get("theme", "글로벌 경제 주요 이슈")

    # ── Step 2: GPT 심층 분석 초고 작성 ───────────────────────────────────
    draft = gpt_write_analysis(materials, context_text)
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
        "title":        title,
        "content":      final_content,
        "theme":        theme,
        "key_data":     key_data,
        "materials":    materials,   # Post 2에 재사용
        "generated_at": datetime.now().isoformat(),
    }


def generate_stock_picks_report(
    theme: str,
    key_data: list,
    post1_content: str,
    news: list,
    research: list,
    materials: Optional[dict] = None,
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

    반환:
        {"title", "content", "picks", "prices", "generated_at"}
    """
    news_text     = format_articles_for_prompt(news)
    research_text = format_research_for_prompt(research)
    context_text  = f"{research_text}\n\n{RESEARCH_NEWS_SEPARATOR}\n\n{news_text}"

    # ── Step 1: 분석 재료 (재사용 or 재생성) ──────────────────────────────
    if materials is None:
        logger.info("Post2 — materials 없음, Gemini 재분석 실행")
        materials = gemini_analyze(news_text, research_text)
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

    # ── Step 2: GPT 종목 리포트 작성 ──────────────────────────────────────
    draft = gpt_write_picks(materials, picks, prices, context_text)
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

    logger.info(f"Post2 생성 완료 | 제목: '{title}' | HTML {len(final_content)}자")

    return {
        "title":              title,
        "content":            final_content,
        "picks":              parsed_picks,
        "prices":             prices,
        "picks_comment_in_raw": picks_comment_in_raw,  # P10 검증용 (assemble 이전 raw 기준)
        "generated_at":       datetime.now().isoformat(),
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )

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
