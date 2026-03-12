"""
macromalt 자동화 시스템 - AI 블로그 생성 모듈 v5.1
=====================================================
교차 퇴고 파이프라인 (Generator-Evaluator):
  Step 1 — Gemini 2.5-flash  : 뉴스 → 매크로 분석 보고서 (애널리스트)
  Step 2 — GPT-4o            : 보고서 → 블로그 초고 (바텐더 캐시)
  Step 3 — Gemini 2.5-flash  : 초고 → 편집장 비평 (PASS or 수정 가이드)
  Step 4 — GPT-4o            : 비평 반영 → 재작성 (최대 2회 루프)
  yfinance / 네이버금융       : 최종본 티커 실시간 종가 + 기준일 조회
  portfolio.json             : 픽 히스토리 누적 저장
  cost_tracker               : 실제 토큰 기반 예상 비용 계산 + 예산 알림
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

# 퇴고 루프 최대 반복 횟수
MAX_RETRIES = 2


# ──────────────────────────────────────────────
# 1. Gemini Step 1 프롬프트 (수석 매크로 애널리스트)
# ──────────────────────────────────────────────
GEMINI_ANALYST_SYSTEM = """
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

GEMINI_ANALYST_USER = """
아래 뉴스 데이터를 분석해 내부 보고서를 작성해라.

{articles_text}
"""


# ──────────────────────────────────────────────
# 2. GPT-4o Step 2 프롬프트 (바텐더 캐시 — 초고 작성)
# ──────────────────────────────────────────────
GPT_WRITER_SYSTEM = """
너는 'MacroMalt(매크로몰트)'의 바텐더 캐시(Cash)다.
주 독자: 여의도·월스트리트 펀드매니저, Level 6-7 개인 투자자.

아래 매크로 분석 보고서를 바탕으로 블로그 포스팅을 작성해라.

[목표 분량]
총 2,500자 이상. 한국경제·매일경제 심층 분석 기사 수준의 밀도로 작성해라.
각 섹션을 압축하지 말고 논거를 충분히 전개해라.

[데이터 강제 인용 규칙 — 최우선]
분석 보고서에 등장하는 모든 숫자(가격·지수·퍼센트·bp·환율·수급 금액 등)를
본문 전체에서 최소 3회 이상 직접 인용해라.
- 금지: "유가가 올랐다", "달러가 강세를 보였다", "코스피가 상승했다"
- 필수: "WTI가 $76.40까지 밀렸다", "달러 인덱스 104.3으로 0.6% 반등", "코스피 2,730 돌파"
수치 없이 방향성만 서술하는 문장은 작성 금지다.

[Negative Prompt — 절대 사용 금지]
- "결론적으로", "요약하자면", "정리하면"
- "~하는 것이 중요합니다", "~할 수 있겠습니다", "~라고 볼 수 있습니다"
- "투자에 유의하시기 바랍니다", "참고하시기 바랍니다"
- "이번 분석이 도움이 되셨으면", "오늘도 좋은 하루"
- AI 전형 접속사·맺음말 일체

[글 구조 — 순서 엄수]

1. # 제목: [오늘의 캐시픽] + 핵심 키워드 조합 (시장을 관통하는 하나의 테마).
   예: [오늘의 캐시픽] WTI 80불 붕괴와 끈적한 두바이유... 한국 정제마진의 향방은?

2. 오프닝: "안녕하세요, 매크로몰트의 바텐더 캐시입니다."로 시작.
   오늘 시황 전반을 싱글몰트 위스키(피트향·셰리캐스크·숙성연도·피니시 등)에 비유해 3~4문장으로 묘사해라.
   비유는 구체적이고 감각적이어야 하며, 투자자가 오늘 시장의 온도를 직감할 수 있어야 한다.
   오프닝에도 핵심 수치 1개 이상을 자연스럽게 녹여라.

3. ## 글로벌 매크로 브리핑
   반드시 아래 두 섹션으로 나눠라.

   ### 🌐 미국 시장
   - 연준 금리·국채 수익률·달러 인덱스·S&P500·나스닥 중 해당 수치를 전부 인용해라.
   - 테마 중심 소제목 정확히 3개. 반드시 `####` 수준의 마크다운 제목으로 작성해라.
     예: #### 4.5%의 벽 — 연준이 버티는 이유
   - 각 소제목 단락 사이에는 반드시 `---` 구분선을 삽입해라.
   - 각 단락 최소 4문장. 수치 → 인과 → 파급 → 포지션 시사점 순서로 전개.
   - 수치 없는 단락은 작성 금지.

   ### 🇰🇷 국내 시장
   - 코스피·코스닥·원/달러 환율·외국인 수급 중 해당 수치를 전부 인용해라.
   - 테마 중심 소제목 정확히 3개. 반드시 `####` 수준의 마크다운 제목으로 작성해라.
     예: #### 외국인 5,200억 순매수의 진짜 의미
   - 각 소제목 단락 사이에는 반드시 `---` 구분선을 삽입해라.
   - 각 단락 최소 4문장. 글로벌 매크로(미국 시장 섹션의 수치)와의 연결고리를 반드시 서술해라.
   - 수치 없는 단락은 작성 금지.

4. ## 캐시의 테이스팅 노트
   내일 당장 포트폴리오를 손봐야 하는 섹터·전략 3가지를 제시해라.
   각 항목은 아래 형식으로 3~4문장씩 작성해라:
   - **[섹터/전략명]**: 오늘 매크로 데이터의 구체적 수치를 인용한 근거 1문장.
     그 수치가 해당 섹터에 미치는 1~2차 연쇄 효과 1~2문장 (수치 포함).
     내일 당장 취해야 할 구체적 행동(매수·매도·비중 확대·헷지) 1문장.
   "장기 투자", "분산 투자" 표현 금지. 단기 포지션 중심으로만 작성해라.

5. ### 🥃 캐시의 픽
   반드시 4번(테이스팅 노트)의 논리적 연장선에서 2~3개 티커를 선정해라.
   테이스팅 노트에서 언급하지 않은 섹터의 티커는 선정 금지.

   JSON 블록 형식 엄수 (시스템이 파싱하므로 형식 절대 변경 금지):
   <!-- PICKS: [{"ticker": "NVDA", "reason": "반도체 수요 회복 + 달러 약세 수혜"}, {"ticker": "XLE", "reason": "유가 반등 수혜 에너지 ETF"}] -->

   JSON 블록 아래에 각 티커를 다음 형식으로 작성해라:

   **[티커명]** | 현재가: {PRICE_PLACEHOLDER}
   > [추천 근거 — 최소 3문장]
   > 첫째, 오늘 분석된 구체적 매크로 수치와 이 종목의 상관관계를 설명해라. (예: 중동 리스크 고조로 WTI $80 돌파 → 정제마진 수혜 → 에너지주 단기 강세)
   > 둘째, 그 매크로 흐름이 이 종목의 실적·밸류에이션·수급에 미치는 직접적 영향을 서술해라.
   > 셋째, 단기(1~5거래일) 트레이딩 관점에서 왜 지금 이 종목인지 한 줄로 확언해라.

   (실제 주가는 시스템이 자동 삽입하므로 {PRICE_PLACEHOLDER}를 그대로 두어라)

6. ### 🔗 오늘의 참고 문헌
   본문(브리핑·테이스팅 노트)에서 실제로 인용·언급한 기사만 엄선해라.
   본문에 없는 기사를 참고문헌에 넣지 마라. 본문에서 인용했으나 참고문헌에 빠진 기사도 없어야 한다.
   형식: - [기사 제목](원본 URL) *— 출처명*
"""

GPT_WRITER_USER = """
[매크로 분석 보고서]

{gemini_report}
"""

GPT_FALLBACK_USER = """
아래 원본 뉴스 데이터를 직접 분석해 블로그 포스팅을 작성해라.

{articles_text}
"""


# ──────────────────────────────────────────────
# 3. Gemini Step 3 프롬프트 (수석 편집장 — 교차 비평)
# ──────────────────────────────────────────────
GEMINI_CRITIC_SYSTEM = """
너는 여의도 최고급 투자 블로그 'MacroMalt'의 수석 편집장이다.
숫자에 집착하는 깐깐한 완벽주의자로, 수치 없는 분석은 분석이 아니라는 철학을 가지고 있다.
ChatGPT가 쓴 글을 읽고 아래 기준으로 무자비하게 평가해라.
내용이 평이하거나 수치가 부족하면 무조건 반려(FAIL)하고 재작성을 지시해라.
웬만한 글은 FAIL이 정상이다. PASS는 진짜 완벽할 때만 허용해라.

[평가 기준 — 하나라도 미달이면 즉시 FAIL]

⓪ 형식 준수 [최우선 — 이것부터 확인]:
   브리핑 섹션의 테마 소제목이 `####` (해시 4개) 수준으로 작성됐는가?
   `###` 이하 수준의 소제목(### 또는 ##)이 브리핑 내 소제목으로 혼용됐는가? → 혼용 시 즉시 FAIL.
   각 소제목 단락 사이에 `---` 구분선이 존재하는가? 없으면 즉시 FAIL.
   본문 산문 단락 안에 `#`, `##`, `###` 같은 마크다운 제목 기호가 남아 있는가? → 있으면 즉시 FAIL.
   → 위 기준 중 하나라도 위반 시: "FAIL\n⓪ 형식 위반: [구체 위반 내용]" 형식으로 반환해라.

① 수치 밀도 (가장 중요):
   본문 전체에서 구체 수치(가격·지수·퍼센트·bp·환율·수급 금액)가 최소 8개 이상 직접 인용됐는가?
   "유가가 올랐다", "달러가 강세를 보였다"처럼 방향성만 서술하고 수치가 없는 문장이 있는가?
   → 수치 없는 방향 서술 문장을 하나씩 직접 인용하고, 어떤 숫자로 대체해야 하는지 명시해라.

② 분량·밀도:
   총 글자 수가 2,500자 이상인가?
   한국경제·매일경제 심층 기사 수준의 논거 전개인가, 아니면 개조식 나열인가?
   → 부족하면 어느 섹션을 얼마나 확장해야 하는지 명시해라.

③ 브리핑 2세션 구조 및 소제목 3개:
   '### 🌐 미국 시장'과 '### 🇰🇷 국내 시장' 두 소제목이 각각 명확히 존재하는가?
   각 세션에 해당 시장의 핵심 수치(금리·수익률·지수·환율·수급)가 빠짐없이 인용됐는가?
   미국 시장 섹션에 `####` 소제목이 정확히 3개 존재하는가? (2개 이하면 즉시 FAIL)
   국내 시장 섹션에 `####` 소제목이 정확히 3개 존재하는가? (2개 이하면 즉시 FAIL)
   각 `####` 소제목 단락 사이에 `---` 구분선이 있는가? 없으면 FAIL.
   국내 시장 섹션이 미국 시장과의 인과 연결 없이 독립적으로 서술됐는가?
   → 소제목이 부족하거나 구분선·연결이 빠졌으면 구체적으로 지적해라.

④ 참고문헌 정합성:
   본문(브리핑·테이스팅 노트)에서 언급한 모든 기사가 참고문헌에 있는가?
   반대로, 본문에서 다루지 않은 기사가 참고문헌에 끼어 있지 않은가?
   → 불일치 항목을 구체적으로 나열해라.

⑤ 테이스팅 노트 깊이:
   각 액션 포인트가 3~4문장(수치 근거→연쇄효과→단기 행동)으로 서술됐는가?
   1~2문장으로 압축된 항목이 하나라도 있으면 FAIL이다.
   → 해당 항목을 직접 인용하고 어떻게 확장해야 하는지 방향을 제시해라.

⑥ 픽 논리 연결·형식·추천 근거:
   <!-- PICKS: [...] --> JSON 블록이 정확히 존재하는가? 티커가 2~3개인가?
   각 티커 아래에 최소 3문장 추천 근거(매크로 수치→종목 상관관계→단기 확언)가 있는가?
   픽이 테이스팅 노트 논리에서 직접 파생됐는가? 뜬금없는 티커는 없는가?
   → 문제 있으면 어떤 티커가 왜 부적절한지, 추천 근거가 왜 부족한지 명시해라.

[AI 어투 점검]
"결론적으로", "요약하자면", "중요합니다", "~할 수 있겠습니다", "~라고 볼 수 있습니다" 등
뻔한 표현이 있으면 해당 문장을 직접 인용하고 구체적 대안 문장을 제시해라.

[출력 규칙 — 엄수]
- 위 6가지 기준을 단 하나의 예외도 없이 모두 통과한 경우에만 "PASS" 한 단어를 반환해라.
- 하나라도 미달이면 반드시 "FAIL\n" 뒤에 ①~⑥ 번호를 붙여 구체 수정 지시를 작성해라.
- "전반적으로 잘 썼지만..." 같은 칭찬 멘트는 절대 금지. 지적과 지시만 써라.
"""

GEMINI_CRITIC_USER = """
아래는 ChatGPT가 작성한 블로그 초고다. 수석 편집장으로서 평가해라.

[초고]
{draft}
"""


# ──────────────────────────────────────────────
# 4. GPT-4o Step 4 프롬프트 (바텐더 캐시 — 재작성)
# ──────────────────────────────────────────────
GPT_REWRITE_USER = """
수석 편집장(Gemini)이 아래 초고를 반려하고 수정 지시를 내렸다.
편집장의 모든 지적 사항을 한 줄도 빠짐없이 반영해 글을 전면 재작성해라.

[편집장 수정 지시]
{feedback}

[수정할 초고]
{draft}

[재작성 필수 체크리스트 — 전부 지켜야 한다]
□ 본문 전체에 구체 수치(가격·지수·%·bp·환율·수급)를 최소 8개 이상 직접 인용할 것.
  "유가가 올랐다" → "WTI가 $76.40으로 2.3% 하락했다" 같이 반드시 숫자로 대체.
□ 글 구조(제목→오프닝→브리핑→테이스팅노트→캐시의픽→참고문헌) 순서 유지.
□ 브리핑은 '### 🌐 미국 시장'과 '### 🇰🇷 국내 시장' 두 섹션으로 분리.
□ 미국·국내 시장 각각 소제목 정확히 3개. 소제목은 반드시 #### 수준으로 작성.
□ 각 소제목 단락 사이에 --- 구분선 삽입 필수.
□ 테이스팅 노트 각 항목은 3~4문장(수치 근거→연쇄효과→단기 행동) 필수.
□ <!-- PICKS: [...] --> JSON 블록 형식 유지. 티커 2~3개.
□ 각 픽 아래에 추천 근거 최소 3문장(매크로 수치 상관관계→실적 영향→단기 확언) 작성.
□ 참고문헌은 본문에서 실제 인용한 기사만 포함. 불일치 없을 것.
□ 총 글자 수 2,500자 이상.
□ AI 어투(결론적으로·요약하자면·중요합니다 등) 절대 사용 금지.
"""


# ──────────────────────────────────────────────
# 5. 내부 유틸: GPT-4o 공통 호출 (비용 기록 포함)
# ──────────────────────────────────────────────
def _call_gpt(system: str, user: str, label: str, temperature: float = 0.75) -> str:
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
        max_tokens=3000,
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


# ──────────────────────────────────────────────
# 6. 내부 유틸: Gemini 공통 호출 (비용 기록 포함)
# ──────────────────────────────────────────────
def _call_gemini(system: str, user: str, label: str, temperature: float = 0.3) -> Optional[str]:
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


# ──────────────────────────────────────────────
# 7. Step 1 — Gemini 매크로 분석 보고서
# ──────────────────────────────────────────────
def step1_gemini_analysis(articles_text: str) -> Optional[str]:
    user_msg = GEMINI_ANALYST_USER.format(articles_text=articles_text)
    return _call_gemini(GEMINI_ANALYST_SYSTEM, user_msg, label="Step1:매크로분석")


# ──────────────────────────────────────────────
# 8. Step 2 — GPT-4o 블로그 초고 작성
# ──────────────────────────────────────────────
def step2_gpt_draft(gemini_report: Optional[str], articles_text: str = "") -> str:
    if gemini_report:
        user_msg = GPT_WRITER_USER.format(gemini_report=gemini_report)
        label = "Step2:초고(듀얼코어)"
    else:
        user_msg = GPT_FALLBACK_USER.format(articles_text=articles_text)
        label = "Step2:초고(GPT단독폴백)"

    return _call_gpt(GPT_WRITER_SYSTEM, user_msg, label=label)


# ──────────────────────────────────────────────
# 9. Step 3 — Gemini 편집장 비평 (교차 검토)
# ──────────────────────────────────────────────
def step3_gemini_critic(draft: str) -> str:
    """
    Gemini가 GPT 초고를 평가합니다.
    반환값: "PASS" 또는 "FAIL\n{수정 가이드}"
    Gemini 호출 실패 시 "PASS"를 반환해 루프를 우회합니다.
    """
    user_msg = GEMINI_CRITIC_USER.format(draft=draft)
    result = _call_gemini(GEMINI_CRITIC_SYSTEM, user_msg, label="Step3:편집장비평", temperature=0.1)

    if result is None:
        logger.warning("Gemini 편집장 호출 실패 — 비평 없이 PASS 처리")
        return "PASS"

    return result.strip()


# ──────────────────────────────────────────────
# 10. Step 4 — GPT-4o 재작성 (편집장 피드백 반영)
# ──────────────────────────────────────────────
def step4_gpt_rewrite(draft: str, feedback: str) -> str:
    user_msg = GPT_REWRITE_USER.format(feedback=feedback, draft=draft)
    return _call_gpt(GPT_WRITER_SYSTEM, user_msg, label="Step4:재작성")


# ──────────────────────────────────────────────
# 11. 뉴스 데이터 → 텍스트 변환
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
# 12. 추천 티커 파싱
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
# 13a. 네이버 금융 해외주식 종가 폴백 조회
# ──────────────────────────────────────────────
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

            # 네이버 금융 해외주식 현재가 선택자 (여러 후보 순차 탐색)
            price_elem = (
                soup.select_one(".now")
                or soup.select_one("#rate_view .now")
                or soup.select_one(".price_now .num")
                or soup.select_one("strong.tit_sd")
            )

            if price_elem:
                raw = price_elem.get_text(strip=True).replace(",", "")
                # 숫자(소수점 허용)만 추출
                digits = re.sub(r"[^\d.]", "", raw)
                if digits:
                    price_float = float(digits)
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    logger.info(
                        f"네이버금융 종가 조회 성공: {ticker}{suffix} = ${price_float:,.2f}"
                    )
                    return f"${price_float:,.2f} ({date_str} 기준, 네이버금융)"

        except Exception as e:
            logger.debug(f"네이버금융 조회 실패 ({ticker}{suffix}): {e}")
            continue

    logger.warning(f"네이버금융에서도 {ticker} 종가를 찾지 못했습니다.")
    return None


# ──────────────────────────────────────────────
# 13b. yfinance 종가 조회 (네이버 금융 폴백 포함)
# ──────────────────────────────────────────────
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


# ──────────────────────────────────────────────
# 14. 캐시의 픽 섹션 조립 (실제 종가 삽입)
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
# 15. portfolio.json 저장
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
# 16. 제목 추출
# ──────────────────────────────────────────────
def extract_title(markdown_content: str) -> str:
    for line in markdown_content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    today = datetime.now().strftime("%Y-%m-%d")
    return f"[오늘의 캐시픽] {today} 글로벌 마켓 브리핑"


# ──────────────────────────────────────────────
# 17. 마크다운 → HTML 변환 (디렉터 지정 스타일 시스템 v2)
# ──────────────────────────────────────────────
def convert_to_html(content: str) -> str:
    """
    디렉터 지정 스타일 시스템으로 마크다운을 WordPress HTML로 변환합니다.

    스타일 규칙:
    - # (제목)       → h1 (대형 타이틀)
    - ##/###/#### (소제목) → h3 with border-left #1a1a1a (디렉터 지정)
    - ---            → <hr style="border-top: 1px solid #eee; margin: 30px 0">
    - > (인용)       → blockquote (픽 추천 근거용 amber 계열)
    - 캐시의 픽 섹션 → <div style="background:#fffaf0; border-left: 5px solid #b36b00">
    """

    # ── 스타일 상수 (디렉터 지정) ────────────────────────────────────────
    H1_STYLE = (
        "font-size:2em;font-weight:800;color:#1a1a1a;"
        "margin:0 0 30px 0;padding-bottom:14px;"
        "border-bottom:3px solid #1a1a1a;line-height:1.3;"
    )
    # 모든 소제목 (##, ###, ####) → 디렉터 지정 h3 스타일
    SUB_H_STYLE = (
        "border-left:6px solid #1a1a1a;padding:12px 18px;"
        "background-color:#f4f4f4;margin:45px 0 20px 0;"
        "color:#1a1a1a;font-size:1.4em;"
    )
    P_STYLE = (
        "font-size:15px;line-height:1.9;color:#333;margin:0 0 16px 0;"
    )
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

    # ── 1. markdown → HTML ───────────────────────────────────────────────
    html = md_lib.markdown(content, extensions=["tables", "fenced_code"])

    # ── 2. 제목 스타일 변환 ──────────────────────────────────────────────
    # h2, h4 → h3 + SUB_H_STYLE (태그명까지 통일)
    for level in [2, 4]:
        html = html.replace(f"<h{level}>", f'<h3 style="{SUB_H_STYLE}">')
        html = html.replace(f"</h{level}>", "</h3>")
    # h3 (아직 style 없는 것) → SUB_H_STYLE
    html = html.replace("<h3>", f'<h3 style="{SUB_H_STYLE}">')
    # h1 (포스팅 제목)
    html = html.replace("<h1>", f'<h1 style="{H1_STYLE}">')

    # ── 3. 본문 요소 스타일 ──────────────────────────────────────────────
    html = html.replace("<p>", f'<p style="{P_STYLE}">')
    html = html.replace("<hr>", f'<hr style="{HR_STYLE}">')
    html = html.replace("<hr />", f'<hr style="{HR_STYLE}">')
    html = html.replace("<blockquote>", f'<blockquote style="{BQ_STYLE}">')
    html = html.replace("<ul>", f'<ul style="{UL_STYLE}">')
    html = html.replace("<ol>", f'<ol style="{OL_STYLE}">')
    html = html.replace("<li>", f'<li style="{LI_STYLE}">')
    html = html.replace("<strong>", f'<strong style="{STRONG_STYLE}">')
    html = re.sub(r"<a ", f'<a style="{A_STYLE}" ', html)

    # ── 4. 캐시의 픽 섹션 → 특별 메뉴판 div 박스로 감싸기 ───────────────
    # 패턴: '캐시의 픽' h3 ~ '참고 문헌' h3 사이의 컨텐츠를 감싼다
    picks_pattern = re.compile(
        r"(<h3[^>]*>.*?캐시의\s*픽.*?</h3>)"   # 픽 소제목
        r"(.*?)"                                 # 픽 본문 (비탐욕적)
        r"(<h3[^>]*>.*?참고\s*문헌.*?</h3>)",   # 참고 문헌 소제목
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


# ──────────────────────────────────────────────
# 18. 최종 콘텐츠 조립 (PICKS 블록 제거 + 실제 종가 삽입)
# ──────────────────────────────────────────────
def assemble_final_content(raw_content: str, picks: list, prices: dict) -> str:
    """
    GPT 초고에서 PICKS JSON 주석을 제거하고,
    각 티커의 {PRICE_PLACEHOLDER}를 실제 종가(기준일 포함)로 교체합니다.
    GPT-written 상세 추천 근거를 그대로 보존합니다.
    """
    # 1. PICKS JSON 블록 제거
    content = re.sub(r"<!--\s*PICKS:\s*\[.*?\]\s*-->", "", raw_content, flags=re.DOTALL)

    # 2. 각 티커의 {PRICE_PLACEHOLDER}를 실제 종가로 순차 교체
    for pick in picks:
        ticker = pick.get("ticker", "")
        price = prices.get(ticker, "N/A")
        if "{PRICE_PLACEHOLDER}" in content:
            content = content.replace("{PRICE_PLACEHOLDER}", price, 1)

    # 3. GPT가 플레이스홀더를 누락한 경우 잔여 처리
    content = content.replace("{PRICE_PLACEHOLDER}", "N/A")

    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


# ──────────────────────────────────────────────
# 19. 메인 생성 함수 (교차 퇴고 루프 포함)
# ──────────────────────────────────────────────
def generate_blog_post(articles: list) -> dict:
    """
    교차 퇴고 파이프라인으로 블로그 포스팅을 생성합니다.

    흐름:
      Step1 Gemini 분석 → Step2 GPT 초고
      → [Step3 Gemini 비평 → Step4 GPT 재작성] × 최대 MAX_RETRIES회
      → yfinance/네이버금융 종가 조회 → 최종 조립 → HTML 변환 → portfolio 저장

    반환값:
        {"title": str, "content": str, "generated_at": str, "picks": list}
    """
    if not articles:
        raise ValueError("기사 데이터 없음")

    # ── Step 1: Gemini 매크로 분석 ──────────────
    articles_text = format_articles_for_prompt(articles)
    gemini_report = step1_gemini_analysis(articles_text)

    # ── Step 2: GPT-4o 초고 작성 ────────────────
    draft = step2_gpt_draft(gemini_report, articles_text)

    # ── Step 3-4: 교차 퇴고 루프 ────────────────
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"▶ 퇴고 루프 {attempt}/{MAX_RETRIES} — Gemini 편집장 비평 시작")
        feedback = step3_gemini_critic(draft)

        if feedback.upper().startswith("PASS"):
            logger.info(f"✅ Gemini 편집장 PASS 승인 (퇴고 {attempt}회차)")
            break

        logger.info(f"📝 Gemini 피드백 수신 ({attempt}회차) | GPT 재작성 시작")
        logger.debug(f"편집장 피드백:\n{feedback}")
        draft = step4_gpt_rewrite(draft, feedback)

        if attempt == MAX_RETRIES:
            logger.info(f"⏹ 최대 퇴고 횟수 도달 ({MAX_RETRIES}회) — 마지막 수정본으로 확정")

    # ── 최종본 기준으로 picks·종가 처리 ──────────
    picks = parse_picks_from_content(draft)
    tickers = [p.get("ticker", "") for p in picks if p.get("ticker")]
    prices = fetch_stock_prices(tickers) if tickers else {}

    if picks:
        save_portfolio(picks, prices)

    # ── 최종 조립: PICKS 블록 제거 + 실제 종가 주입 ─
    title = extract_title(draft)  # HTML 변환 전 마크다운에서 제목 추출
    final_content = assemble_final_content(draft, picks, prices)

    # ── 마크다운 → WordPress용 HTML 변환 ─────────
    final_html = convert_to_html(final_content)

    logger.info(f"블로그 포스팅 생성 완료 | 제목: '{title}' | HTML 길이: {len(final_html)}자")

    return {
        "title": title,
        "content": final_html,
        "generated_at": datetime.now().isoformat(),
        "picks": picks,
    }


# ──────────────────────────────────────────────
# 20. 직접 실행 진입점 (테스트용)
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
