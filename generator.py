"""
macromalt 자동화 시스템 - AI 블로그 생성 모듈 v4.0
=====================================================
듀얼 코어 파이프라인:
  Step 1 — Google Gemini (gemini-1.5-pro): 원본 뉴스 → 매크로 분석 보고서
  Step 2 — OpenAI GPT-4o: Gemini 보고서 → 블로그 본문 + 추천 티커
  yfinance: 추천 티커 실시간 종가 조회
  portfolio.json: 픽 히스토리 누적 저장
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

import yfinance as yf
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types as genai_types

load_dotenv()

logger = logging.getLogger("macromalt")


# ──────────────────────────────────────────────
# 1. Gemini Step 1 프롬프트 (수석 매크로 애널리스트)
# ──────────────────────────────────────────────
GEMINI_SYSTEM_PROMPT = """
너는 여의도 탑티어 운용사 출신 수석 매크로 애널리스트다.
주어진 뉴스 목록을 분석해 기관 투자자용 내부 보고서를 작성해라.

[필터링 — 최우선]
아래 카테고리 기사는 즉시 제외하고 분석 대상에서 삭제:
- 운세·날씨·연예·스포츠·정치 단신·부동산 매물
- 광고성 콘텐츠·생활 정보·AI 기업 신제품 소개
- 매크로 경제·금융 투자와 무관한 모든 기사

[분석 대상]
금리·환율·증시·원자재·채권·CDS·스프레드·글로벌 자본 흐름 관련 기사만 사용.

[출력 형식 — 불릿 포인트 보고서]
## 핵심 매크로 팩트 (수치 포함)
- (각 기사에서 추출한 핵심 수치/사실. 형용사 금지. 예: "미 10Y 국채 4.52%, 전일 대비 +8bp")

## 크로스에셋 연쇄 분석
- FX·Yield·Commodity·Equity 간 2~3차 연쇄 효과. 1차 해석 수준 금지.
- 미·일·한 자본 흐름을 하나의 흐름으로 연결.

## 주목할 섹터/자산
- 향후 1~5거래일 내 변동성이 예상되는 섹터나 자산 클래스와 근거.

## 미국 주식 추천 티커 (2~3개)
- 티커 심볼: (이유를 1줄로. 반드시 매크로 근거 포함)
- 출력 형식 예: "NVDA: 반도체 수요 회복 + 달러 약세 수혜"
- 반드시 실존하는 NYSE/NASDAQ 티커만 사용할 것.
"""

GEMINI_USER_TEMPLATE = """
아래 뉴스 데이터를 분석해 내부 보고서를 작성해라.

{articles_text}
"""


# ──────────────────────────────────────────────
# 2. GPT-4o Step 2 프롬프트 (바텐더 캐시)
# ──────────────────────────────────────────────
GPT_SYSTEM_PROMPT = """
너는 'MacroMalt(매크로몰트)'의 바텐더 캐시(Cash)다.
주 독자: 여의도·월스트리트 펀드매니저, Level 6-7 개인 투자자.

아래 매크로 분석 보고서를 바탕으로 블로그 포스팅을 작성해라.
보고서에 등장한 수치와 티커를 그대로 사용해라.

[Negative Prompt — 절대 사용 금지]
- "결론적으로", "요약하자면", "정리하면"
- "~하는 것이 중요합니다", "~할 수 있겠습니다", "~라고 볼 수 있습니다"
- "투자에 유의하시기 바랍니다", "참고하시기 바랍니다"
- "이번 분석이 도움이 되셨으면", "오늘도 좋은 하루"
- AI 전형 접속사·맺음말 일체

[글 구조 — 순서 엄수, 총 1,500자 이상]
1. # 제목: [오늘의 캐시픽] + 핵심 키워드 조합.
   예: [오늘의 캐시픽] WTI 80불 붕괴와 끈적한 두바이유... 한국 정제마진의 향방은?

2. 오프닝: "안녕하세요, 매크로몰트의 바텐더 캐시입니다."로 시작.
   오늘 시황을 싱글몰트 위스키(피트향·셰리캐스크·숙성연도 등)에 비유해 2~3문장 요약.

3. ## 글로벌 매크로 브리핑 (소제목 2~3개):
   국가 나열 금지. 테마 중심. 예: '미-일 금리차와 엔화 방어선'
   구체적 수치 반드시 인용. 단문, 확신, 단호하게.

4. ## 캐시의 테이스팅 노트:
   내일 당장 포트폴리오 비중 조절할 섹터·헷징 전략. "장기 투자" 금지.
   최소 3개 구체 액션 포인트.

5. ### 🥃 캐시의 픽:
   분석 보고서의 추천 티커를 JSON 블록으로 출력해라. 형식 엄수:
   <!-- PICKS: [{"ticker": "NVDA", "reason": "반도체 수요 회복 + 달러 약세 수혜"}, {"ticker": "XLE", "reason": "유가 반등 수혜 에너지 ETF"}] -->
   JSON 블록 바로 아래에는 각 티커를 마크다운 리스트로도 작성해라:
   - **NVDA** — 반도체 수요 회복 + 달러 약세 수혜 | 현재가: {PRICE_PLACEHOLDER}
   (실제 주가는 시스템이 자동 삽입하므로 {PRICE_PLACEHOLDER}를 그대로 두어라)

6. ### 🔗 오늘의 참고 문헌:
   본문에서 실제로 인용한 핵심 기사만 5~7개 엄선.
   형식: - [기사 제목](원본 URL) *— 출처명*
"""

GPT_USER_TEMPLATE = """
[매크로 분석 보고서]

{gemini_report}
"""

# Gemini 폴백: GPT가 직접 원본 뉴스를 분석해 블로그 작성
GPT_FALLBACK_USER_TEMPLATE = """
아래 원본 뉴스 데이터를 직접 분석해 블로그 포스팅을 작성해라.

{articles_text}
"""


# ──────────────────────────────────────────────
# 3. 뉴스 데이터 → 텍스트 변환
# ──────────────────────────────────────────────
def format_articles_for_prompt(articles: list) -> str:
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
            lines.append(f"{i}. **{title}**")
            if url:
                lines.append(f"   URL: {url}")
            if summary:
                lines.append(f"   요약: {summary[:200]}")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 4. Step 1 — Gemini 매크로 분석 보고서
# ──────────────────────────────────────────────
def step1_gemini_analysis(articles_text: str) -> Optional[str]:
    """
    Gemini로 매크로 분석 보고서를 생성합니다.
    API 키가 없거나 할당량 초과 시 None을 반환해 GPT 폴백을 유도합니다.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY 없음 — GPT-4o 단독 모드로 폴백")
        return None

    try:
        client = genai.Client(api_key=api_key)
        user_message = GEMINI_USER_TEMPLATE.format(articles_text=articles_text)
        logger.info("Gemini gemini-2.5-flash 호출 시작 (Step 1: 매크로 분석)")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=genai_types.GenerateContentConfig(
                system_instruction=GEMINI_SYSTEM_PROMPT.strip(),
                max_output_tokens=8000,  # 2.5-flash는 thinking 토큰 포함이라 여유있게
                temperature=0.3,
            ),
        )

        report = response.text or ""
        logger.info(f"Gemini 분석 완료 | 보고서 길이: {len(report)}자")
        return report

    except Exception as e:
        logger.warning(f"Gemini 호출 실패 ({e}) — GPT-4o 단독 모드로 폴백")
        return None


# ──────────────────────────────────────────────
# 5. Step 2 — GPT-4o 블로그 본문 생성
# ──────────────────────────────────────────────
def step2_gpt_blog(gemini_report: Optional[str], articles_text: str = "") -> str:
    """
    gemini_report가 있으면 듀얼 코어 모드, None이면 GPT 단독 폴백 모드.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env에 설정되지 않았습니다.")

    client = OpenAI(api_key=api_key)

    if gemini_report:
        user_message = GPT_USER_TEMPLATE.format(gemini_report=gemini_report)
        logger.info("GPT-4o 호출 시작 (Step 2: 듀얼 코어 모드)")
    else:
        user_message = GPT_FALLBACK_USER_TEMPLATE.format(articles_text=articles_text)
        logger.info("GPT-4o 호출 시작 (Step 2: 단독 폴백 모드 — Gemini 미사용)")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": GPT_SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_message},
        ],
        max_tokens=3000,
        temperature=0.75,
    )

    content = response.choices[0].message.content or ""
    logger.info(f"GPT-4o 생성 완료 | 본문 길이: {len(content)}자")
    return content


# ──────────────────────────────────────────────
# 6. 추천 티커 파싱
# ──────────────────────────────────────────────
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


# ──────────────────────────────────────────────
# 7. yfinance 종가 조회
# ──────────────────────────────────────────────
def fetch_stock_prices(tickers: list) -> dict:
    """티커 리스트의 최신 종가를 조회합니다. 실패 시 'N/A' 반환."""
    prices = {}
    for ticker_str in tickers:
        try:
            t = yf.Ticker(ticker_str)
            hist = t.history(period="1d")
            if not hist.empty:
                price = round(hist["Close"].iloc[-1], 2)
                prices[ticker_str] = f"${price:,.2f}"
            else:
                prices[ticker_str] = "N/A"
        except Exception as e:
            logger.warning(f"{ticker_str} 종가 조회 실패: {e}")
            prices[ticker_str] = "N/A"
    logger.info(f"yfinance 종가 조회 완료: {prices}")
    return prices


# ──────────────────────────────────────────────
# 8. 캐시의 픽 섹션 조립 (실제 종가 삽입)
# ──────────────────────────────────────────────
def build_picks_section(picks: list, prices: dict) -> str:
    """실제 종가를 포함한 '캐시의 픽' 마크다운 섹션을 생성합니다."""
    if not picks:
        return ""

    lines = ["### 🥃 캐시의 픽\n"]
    for pick in picks:
        ticker = pick.get("ticker", "")
        reason = pick.get("reason", "")
        price = prices.get(ticker, "N/A")
        lines.append(f"- **{ticker}** — {reason} | 현재가: {price}")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 9. portfolio.json 저장
# ──────────────────────────────────────────────
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


# ──────────────────────────────────────────────
# 10. 제목 추출
# ──────────────────────────────────────────────
def extract_title(markdown_content: str) -> str:
    for line in markdown_content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    today = datetime.now().strftime("%Y-%m-%d")
    return f"[오늘의 캐시픽] {today} 글로벌 마켓 브리핑"


# ──────────────────────────────────────────────
# 11. 최종 콘텐츠 조립
# ──────────────────────────────────────────────
def assemble_final_content(raw_content: str, picks_section: str) -> str:
    """
    GPT 출력에서:
      - <!-- PICKS: [...] --> 블록 제거
      - {PRICE_PLACEHOLDER} → 실제 종가로 대체된 picks_section으로 교체
    최종 순서: 제목→오프닝→브리핑→테이스팅노트→캐시의픽→참고문헌
    """
    # PICKS JSON 블록 제거
    content = re.sub(r"<!--\s*PICKS:\s*\[.*?\]\s*-->", "", raw_content, flags=re.DOTALL)

    # 기존 ### 🥃 캐시의 픽 섹션 교체 (GPT가 {PRICE_PLACEHOLDER} 포함해서 썼을 경우)
    if picks_section:
        picks_pattern = re.compile(
            r"(###\s*🥃\s*캐시의\s*픽.*?)(?=###\s*🔗|$)", re.DOTALL
        )
        if picks_pattern.search(content):
            content = picks_pattern.sub(picks_section + "\n\n", content)
        else:
            # 참고문헌 앞에 삽입
            ref_pattern = re.compile(r"(###\s*🔗\s*오늘의\s*참고\s*문헌)", re.DOTALL)
            if ref_pattern.search(content):
                content = ref_pattern.sub(picks_section + "\n\n" + r"\1", content)
            else:
                content = content.strip() + "\n\n" + picks_section

    # 연속 빈 줄 정리
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


# ──────────────────────────────────────────────
# 12. 메인 생성 함수
# ──────────────────────────────────────────────
def generate_blog_post(articles: list) -> dict:
    """
    수집된 기사를 바탕으로 듀얼 코어 AI로 블로그 포스팅을 생성합니다.

    반환값:
        {
            "title": str,
            "content": str,
            "generated_at": str,
            "picks": list,
        }
    """
    if not articles:
        raise ValueError("기사 데이터 없음")

    # Step 1: Gemini 분석 (실패 시 None 반환)
    articles_text = format_articles_for_prompt(articles)
    gemini_report = step1_gemini_analysis(articles_text)

    # Step 2: GPT-4o 블로그 생성 (gemini_report=None이면 폴백 모드)
    raw_content = step2_gpt_blog(gemini_report, articles_text)

    # 티커 파싱 + 종가 조회
    picks = parse_picks_from_content(raw_content)
    tickers = [p.get("ticker", "") for p in picks if p.get("ticker")]
    prices = fetch_stock_prices(tickers) if tickers else {}

    # 캐시의 픽 섹션 조립
    picks_section = build_picks_section(picks, prices)

    # portfolio.json 저장
    if picks:
        save_portfolio(picks, prices)

    # 최종 콘텐츠 조립
    final_content = assemble_final_content(raw_content, picks_section)
    title = extract_title(final_content)

    logger.info(f"블로그 포스팅 생성 완료 | 제목: '{title}' | 길이: {len(final_content)}자")

    return {
        "title": title,
        "content": final_content,
        "generated_at": datetime.now().isoformat(),
        "picks": picks,
    }


# ──────────────────────────────────────────────
# 13. 직접 실행 진입점 (테스트용)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler()],
    )

    dummy_articles = [
        {
            "source": "야후 파이낸스",
            "title": "Fed holds rates steady at 4.25%-4.50%, signals two cuts in 2025",
            "summary": "The Federal Reserve kept interest rates unchanged as inflation remains above target.",
            "url": "https://finance.yahoo.com/news/fed-holds-rates-steady",
        },
        {
            "source": "한국경제",
            "title": "코스피, 외국인 5,200억 순매수에 2,730선 돌파",
            "summary": "외국인 투자자들의 대규모 순매수가 이어지며 코스피가 2,730선을 돌파했다.",
            "url": "https://www.hankyung.com/finance/article/test",
        },
        {
            "source": "매일경제",
            "title": "엔/달러 149.8엔... 일본은행 금리 인상 가능성 시사",
            "summary": "일본은행 우에다 총재가 추가 금리 인상 가능성을 시사하며 엔화가 강세로 반응했다.",
            "url": "https://stock.mk.co.kr/news/test",
        },
        {
            "source": "야후 파이낸스",
            "title": "WTI crude drops 2.3% to $76.40 on demand concerns",
            "summary": "Oil prices fell sharply as weak Chinese manufacturing data raised demand concerns.",
            "url": "https://finance.yahoo.com/news/wti-crude-drops",
        },
    ]

    try:
        result = generate_blog_post(dummy_articles)
        print("\n" + "=" * 60)
        print(f"제목: {result['title']}")
        print(f"길이: {len(result['content'])}자")
        print(f"픽: {result['picks']}")
        print("=" * 60)
        print(result["content"])
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
