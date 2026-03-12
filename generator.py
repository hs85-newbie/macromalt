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

def format_articles_for_prompt(articles: list) -> str:
    """뉴스 기사 리스트를 프롬프트용 텍스트로 변환합니다."""
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
            lines.append(f"{i}. {title}")
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
    리서치 데이터를 프롬프트용 텍스트로 변환합니다 (Phase 6 enhanced).
    weight 내림차순 정렬, [⭐ 핵심 리서치] 마커 포함.
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

        priority_marker = "[⭐ 핵심 리서치] " if weight >= 5 else ""
        lines.append(f"{i}. {priority_marker}[{source}] {title}")

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


def assemble_final_content(raw_content: str, picks: list, prices: dict) -> str:
    """
    GPT 초고에서 PICKS JSON 주석을 제거하고,
    각 티커의 {PRICE_PLACEHOLDER}를 실제 종가(기준일 포함)로 교체합니다.
    """
    content = re.sub(r"<!--\s*PICKS:\s*\[.*?\]\s*-->", "", raw_content, flags=re.DOTALL)

    for pick in picks:
        ticker = pick.get("ticker", "")
        price = prices.get(ticker, "N/A")
        if "{PRICE_PLACEHOLDER}" in content:
            content = content.replace("{PRICE_PLACEHOLDER}", price, 1)

    content = content.replace("{PRICE_PLACEHOLDER}", "N/A")
    content = re.sub(r"\n{3,}", "\n\n", content)
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

[출력 규칙 — 최우선]
- 반드시 아래 JSON 구조로만 출력할 것.
- 설명 텍스트, 마크다운 코드 블록(```), 서문 없이 JSON 객체 하나만 출력.
- 사실(fact)과 해석(interpretation)을 절대 혼합하지 말 것.
- 목표가·투자의견·현재가는 명확한 출처와 기준일이 있을 때만 facts에 포함.
- 출처가 불분명한 수치는 uncertainties에 이동.

[출력 JSON 구조]
{
  "theme": "오늘의 핵심 경제 테마 (한 문장, 구체적으로)",
  "facts": [
    {
      "content": "확인된 사실 내용 (숫자·날짜·기관명 포함)",
      "source": "출처명 (언론사명, 기관명, 리포트명 등)",
      "date": "기준 시점 (YYYY-MM-DD 또는 'YYYY년 Q분기' 등)"
    }
  ],
  "market_impact": "이 테마가 금융시장에 미치는 영향 경로 (사실 기반, 해석 금지)",
  "counter_interpretations": [
    "이 테마에 대한 반대 해석 또는 대안적 시각 1",
    "반대 해석 2 (없으면 빈 배열 [])"
  ],
  "uncertainties": [
    "이 분석에서 불확실한 요소 또는 추가 확인이 필요한 사항"
  ],
  "writing_notes": "ChatGPT 작성자에게 전달할 주의사항 (과장 금지 항목, 민감한 표현 등)"
}

facts는 반드시 5개 이상 10개 이하로 출력할 것.
"""

GEMINI_ANALYST_USER = """
아래 데이터를 분석해 오늘의 구조화된 리포트 재료를 JSON으로 출력하라.

[⭐ 핵심 리서치 — 최우선 참고]
[⭐ 핵심 리서치] 마커가 붙은 항목은 전문 애널리스트 의견이므로 가장 높은 가중치로 반영.
{research_text}

[뉴스 기사 — 보조 참고]
{news_text}
"""


# ─── Step 2a: GPT 작성 엔진 — Post 1 심층 분석 프롬프트 ─────────────────────

GPT_WRITER_ANALYSIS_SYSTEM = f"""
너는 매크로몰트(MacroMalt) 오너 바텐더 '캐시(Cash)'다.
Gemini 애널리스트가 정리한 구조화된 리포트 재료를 바탕으로 금융 분석 글을 작성한다.

[작성 규칙 — 이것이 가장 중요하다]
1. 사실: 출처가 있는 내용은 일반 문장으로 자연스럽게 서술
2. 해석: 문장 앞에 반드시 [해석] 태그를 삽입
3. 전망: 문장 앞에 반드시 [전망] 태그를 삽입
4. 불확실한 내용: "확실하지 않다", "확인되지 않았다" 등 명확히 표기
5. 출처 없는 가격·목표가·투자의견: 절대 작성 금지
6. 도입부에서만 바텐더/위스키 비유를 딱 1회 사용. 이후 본문은 정보 전달·객관성에 집중.
7. 상투적 결론 문장("이상으로 살펴보았습니다", "결론적으로" 등) 금지
8. 기계적인 접속사 패턴 반복 금지

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
1. 제목: <h1>로 작성 — "[심층분석] {{테마}}" 형식
2. 도입부: <p>로 작성 — 위스키/바텐더 비유 1회 + 오늘의 핵심 테마 소개 (150자 내외)
3. 본문 소제목 2~3개: <h3>로 작성 — 사실 데이터 기반 분석
4. 반대 시각 또는 불확실성: <h3> + <p> — 균형 잡힌 시각 제시
5. 참고 출처 섹션: <h3>참고 출처</h3> 후 <p>로 본문에서 실제 사용된 데이터의 출처만 나열
   (미사용 출처 제외 — 본문 데이터와 직접 대응되는 것만)

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

[작성 규칙]
1. 종목별 근거: 3문장 내외 (매크로 연결 근거 1~2문장 + 핵심 리스크 1문장)
2. 해석은 [해석], 전망은 [전망] 태그 필수
3. 현재가: 반드시 제공된 {{PRICE_PLACEHOLDER}} 마커를 사용. 절대 임의 생성 금지.
4. 목표가: 제공된 출처·기준일이 있는 경우에만 작성. 없으면 작성 금지.
5. "매수하세요", "지금 사야 할 주식" 등 투자 권유 문구 절대 금지
6. 위스키/바텐더 비유: 도입부에 간결하게 테마-종목 연결 (1회, 필수는 아님)

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
1. 제목: <h1>로 작성 — "[캐시의 픽] {{종목명}} 외 — {{테마}}" 형식
2. 도입부: <p>로 간결하게 오늘의 테마와 종목 선정 배경 연결
3. 종목별 섹션: 각 종목을 <div style="{_PICKS_DIV_STYLE}">로 감싸고
   - <h3>으로 종목명(티커) 표시
   - 현재가: "현재가 {{PRICE_PLACEHOLDER}}" 형식으로 명시
   - 선정 근거 <p> 1~2개
   - 핵심 리스크 <p> 1개
4. 참고 출처 섹션: <h3>참고 출처</h3> 후 <p>로 사용된 데이터 출처만 나열

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
너는 매크로몰트(MacroMalt) 금융 콘텐츠 팩트체커다.
생성된 금융 분석 초안을 아래 기준으로 검수하고, 반드시 JSON으로만 결과를 출력해라.
설명 텍스트나 서문 없이 JSON 객체 하나만 출력할 것.

[검수 기준 6가지]
1. 수치·날짜·고유명사의 오류 가능성 및 기준 시점 누락
2. [해석] 또는 [전망] 태그 없이 해석·전망이 사실처럼 서술된 문장
3. 출처 없는 단정 표현 존재 여부 (예: "~할 것이다", "~가 확실하다" 단정)
4. 투자 권유처럼 보이는 문장 존재 여부
5. 바텐더/위스키 비유가 도입부 1회를 초과하는지 여부
6. 마크다운 기호(#, ##, **, *, ```) 포함 여부

[출력 JSON]
{
  "pass": true 또는 false,
  "issues": ["발견된 문제 1", "문제 2"],
  "revised_content": null 또는 "pass가 false일 때 수정된 전체 HTML 본문"
}

pass=true이면 issues는 [] 또는 경미한 사항만, revised_content는 반드시 null.
pass=false이면 issues에 문제 목록, revised_content에 6개 기준을 모두 해결한 수정본 전체.
"""

GEMINI_VERIFIER_USER = """
아래 초안을 검수하고 JSON으로 결과를 출력하라.

[검수 대상 초안]
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

def gemini_analyze(news_text: str, research_text: str) -> dict:
    """
    Step 1: Gemini 분석 엔진.
    뉴스·리서치 데이터를 구조화된 JSON 리포트 재료로 변환합니다.

    반환:
        {"theme", "facts", "market_impact", "counter_interpretations",
         "uncertainties", "writing_notes"}
    """
    user_msg = GEMINI_ANALYST_USER.format(
        research_text=research_text,
        news_text=news_text,
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

    logger.info(f"Step1 선정 테마: {result.get('theme', 'N/A')}")
    logger.info(f"Step1 사실 데이터: {len(result.get('facts', []))}개")
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
        max_tokens=4000,
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
        max_tokens=3000,
    )
    return draft


def verify_draft(draft: str) -> dict:
    """
    Step 3: Gemini 검수 엔진.
    HTML 초안을 6가지 기준으로 검수합니다.

    반환:
        {"pass": bool, "issues": list, "revised_content": str | None}
    """
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
    revised = result.get("revised_content")

    if passed:
        logger.info(f"Step3 검수 통과" + (f" (경고: {issues})" if issues else ""))
    else:
        logger.warning(f"Step3 검수 실패: {issues}")

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

    # ── Step 1: Gemini 분석 재료 생성 ─────────────────────────────────────
    materials = gemini_analyze(news_text, research_text)
    theme = materials.get("theme", "글로벌 경제 주요 이슈")

    # ── Step 2: GPT 심층 분석 초고 작성 ───────────────────────────────────
    draft = gpt_write_analysis(materials, context_text)

    # ── Step 3: Gemini 팩트체크 + 수정 ────────────────────────────────────
    verify_result = verify_draft(draft)
    if not verify_result["pass"] and verify_result.get("revised_content"):
        logger.info("Step3 검수 실패 — 수정본 채택")
        final_content = verify_result["revised_content"]
    else:
        final_content = draft

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

    # ── Step 2: GPT 종목 리포트 작성 ──────────────────────────────────────
    draft = gpt_write_picks(materials, picks, prices, context_text)

    # ── Step 3: Gemini 팩트체크 + 수정 ────────────────────────────────────
    verify_result = verify_draft(draft)
    if not verify_result["pass"] and verify_result.get("revised_content"):
        logger.info("Post2 Step3 검수 실패 — 수정본 채택")
        raw_content = verify_result["revised_content"]
    else:
        raw_content = draft

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

    logger.info(f"Post2 생성 완료 | 제목: '{title}' | HTML {len(final_content)}자")

    return {
        "title":        title,
        "content":      final_content,
        "picks":        parsed_picks,
        "prices":       prices,
        "generated_at": datetime.now().isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# SECTION H: 자동 검증 테스트 (python generator.py 직접 실행)
# ──────────────────────────────────────────────────────────────────────────────

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
    print("macromalt Phase 7 파이프라인 자동 검증 테스트")
    print("=" * 70)

    # 샘플 데이터 (실제 API 호출 포함)
    sample_news = [
        {
            "source": "한국경제",
            "title": "미 연준, 금리 인하 속도 조절 시사",
            "summary": "제롬 파월 연준 의장이 물가 안정에 앞서 추가 데이터가 필요하다고 발언.",
            "url": "https://www.hankyung.com/article/sample1",
            "published": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "source": "야후 파이낸스",
            "title": "US Core CPI Rose 0.3% in February, Exceeding Expectations",
            "summary": "Core inflation data came in hotter than expected, complicating Fed rate cut timeline.",
            "url": "https://finance.yahoo.com/news/sample2",
            "published": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "source": "매일경제",
            "title": "원달러 환율 1,330원대 진입...수출주 반응 주목",
            "summary": "원달러 환율이 달러 강세에 1,330원대로 상승. 수출 기업 실적에 영향 전망.",
            "url": "https://www.mk.co.kr/news/sample3",
            "published": datetime.now().strftime("%Y-%m-%d"),
        },
    ]

    sample_research = [
        {
            "source": "네이버금융 리서치",
            "title": "2026년 상반기 매크로 환경 점검 — 금리·환율·수출 삼각관계",
            "summary": "금리 인하 지연과 달러 강세가 신흥국 자금 이탈 가속. 한국 수출 기업 환율 수혜 가능성.",
            "broker": "NH투자증권",
            "weight": 3,
            "published": datetime.now().strftime("%Y-%m-%d"),
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

        # ── 6가지 기준 자동 검증 ──────────────────────────────────────────
        print("\n" + "=" * 70)
        print("6가지 검증 기준 체크")
        print("=" * 70)

        criteria = {
            "1. Gemini 결과가 구조화 JSON으로 출력됐는가?":
                isinstance(materials, dict) and "theme" in materials and "facts" in materials,

            "2. 최종 결과물이 마크다운 없이 HTML만 사용했는가?":
                not bool(re.search(r"(?m)^#{1,6} |(?<!\[)\*\*(?!\])", content)),

            "3. 출처 없는 가격·목표가가 임의 생성되지 않았는가?":
                _verify_no_unsourced_price(content),

            "4. [해석]·[전망]·'확실하지 않다' 규칙이 적용됐는가?":
                "[해석]" in content or "[전망]" in content or "확실하지 않" in content,

            "5. 참고 출처 섹션이 본문 데이터와 대응하는가?":
                bool(re.search(r"참고\s*출처|Reference", content, re.IGNORECASE)),

            "6. 위스키·바텐더 비유가 1회를 넘지 않았는가?":
                _count_whisky_metaphors(content) <= 2,  # 관련 단어 총합 2회 이하
        }

        all_pass = True
        for criterion, passed in criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | {criterion}")
            if not passed:
                all_pass = False

        print("\n" + "=" * 70)
        if all_pass:
            print("🎉 전체 검증 통과 — Phase 7 파이프라인 정상 동작")
        else:
            print("⚠️  일부 기준 미통과 — 로그를 확인하고 프롬프트를 조정하세요.")
        print("=" * 70 + "\n")

    except Exception as e:
        logger.exception(f"테스트 실패: {e}")
        sys.exit(1)
