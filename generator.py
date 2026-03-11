"""
macromalt 자동화 시스템 - AI 블로그 생성 모듈
=====================================================
수집된 뉴스 데이터를 OpenAI gpt-4o에 전달해
'바텐더 캐시' 페르소나의 블로그 포스팅을 생성합니다.
"""

import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger("macromalt")

# ──────────────────────────────────────────────
# 1. 시스템 프롬프트 (바텐더 캐시 페르소나)
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """
[역할 부여]
너는 'MacroMalt(매크로몰트)'라는 경제/투자 블로그를 운영하는 '바텐더 캐시(Cash)'야.
너는 낮에는 날카로운 글로벌 매크로 투자자이고, 밤에는 단골손님들에게 위스키 한 잔과 함께
고급 경제 인사이트를 나누어주는 따뜻하고 지적인 바텐더야.

[작업 지시]
내가 매일 아침 미국, 일본, 한국의 전날 경제 뉴스 헤드라인과 주요 증시 데이터를 텍스트로
넘겨줄 거야. 너는 이 원시 데이터를 분석해서, 개인 투자자에게 실질적인 도움이 되는
1,500자 내외의 블로그 포스팅을 마크다운(Markdown) 형식으로 작성해 줘.

[어조 및 글쓰기 스타일]
1. 심야 위스키 바에서 단골손님에게 차분하고 친절하게 설명해 주는 말투를 사용해.
   (예: "~했습니다", "~하는 것이 좋겠네요", "~라는 점을 주목해 볼까요?")
2. 경제 용어는 전문성을 유지하되, 비개발자나 초보 투자자도 이해하기 쉽게 비유를 들어 설명해 줘.
3. 단순한 사실 전달(Fact)을 넘어, 그래서 우리가 어떻게 투자에 적용해야 하는지(Insight)를 반드시 포함해.

[블로그 글 구조 - 반드시 지킬 것]
1. 매력적인 제목: 클릭을 유도하면서도 핵심을 담은 제목
   (예: [오늘의 캐시픽] 나스닥의 숨고르기, 그리고 엔화의 반격... 우리가 주목할 섹터는?)
2. 오프닝: "안녕하세요, 매크로몰트의 바텐더 캐시입니다."로 시작.
   가벼운 안부나 그날의 분위기를 잡는 세련된 인사말 작성.
3. 글로벌 마켓 브리핑: 전달받은 데이터를 바탕으로 미국, 일본, 한국 시장의 핵심 이슈를
   2~3가지 소제목으로 나누어 분석. 국가 간의 연결고리(예: 미국의 금리가 한국 증시에
   미친 영향)를 강조할 것.
4. 캐시의 테이스팅 노트 (결론): 오늘의 시장 분위기를 특정 위스키의 맛이나 칵테일에
   비유하며 우아하게 마무리.
   (예: "오늘 시장은 마치 피트 향이 강한 아일라 위스키 같았습니다. 처음엔 맵고 쌉쌀하지만...")
   그리고 오늘 하루 투자자가 가져야 할 마인드셋을 한 줄로 요약.

반드시 마크다운(Markdown) 형식으로 반환해 줘.
제목은 # 으로, 소제목은 ## 으로 구분해.
"""


# ──────────────────────────────────────────────
# 2. 뉴스 데이터 → 프롬프트 텍스트 변환
# ──────────────────────────────────────────────
def format_articles_for_prompt(articles: list[dict]) -> str:
    """
    수집된 기사 리스트를 GPT에 전달할 텍스트 블록으로 변환합니다.
    소스별로 그룹핑해서 정리합니다.
    """
    today = datetime.now().strftime("%Y년 %m월 %d일")
    lines = [f"[{today} 뉴스 데이터]\n"]

    # 소스별 그룹핑
    grouped: dict[str, list[dict]] = {}
    for article in articles:
        src = article.get("source", "기타")
        grouped.setdefault(src, []).append(article)

    for source_name, items in grouped.items():
        lines.append(f"\n## {source_name} ({len(items)}건)")
        for i, item in enumerate(items, 1):
            title = item.get("title", "제목 없음")
            summary = item.get("summary", "")
            lines.append(f"{i}. **{title}**")
            if summary:
                lines.append(f"   {summary[:200]}")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 3. 제목 추출 헬퍼
# ──────────────────────────────────────────────
def extract_title(markdown_content: str) -> str:
    """
    생성된 마크다운에서 첫 번째 # 제목을 추출합니다.
    제목이 없으면 날짜 기반 기본 제목을 반환합니다.
    """
    for line in markdown_content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    today = datetime.now().strftime("%Y-%m-%d")
    return f"[오늘의 캐시픽] {today} 글로벌 마켓 브리핑"


# ──────────────────────────────────────────────
# 4. 블로그 포스팅 생성 메인 함수
# ──────────────────────────────────────────────
def generate_blog_post(articles: list[dict]) -> dict:
    """
    수집된 기사를 바탕으로 블로그 포스팅을 생성합니다.

    반환값:
        {
            "title": str,       # 마크다운에서 추출한 제목
            "content": str,     # 마크다운 전체 본문
            "generated_at": str # 생성 시각 ISO 형식
        }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY가 .env에 설정되지 않았습니다.")
        raise ValueError("OPENAI_API_KEY 없음")

    if not articles:
        logger.warning("전달된 기사가 없어 블로그 생성을 건너뜁니다.")
        raise ValueError("기사 데이터 없음")

    client = OpenAI(api_key=api_key)

    user_message = format_articles_for_prompt(articles)
    logger.info(f"GPT-4o 호출 시작 (입력 기사: {len(articles)}건)")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_message},
        ],
        max_tokens=2500,
        temperature=0.75,
    )

    content = response.choices[0].message.content or ""
    title = extract_title(content)

    logger.info(f"블로그 포스팅 생성 완료 | 제목: '{title}' | 길이: {len(content)}자")

    return {
        "title": title,
        "content": content,
        "generated_at": datetime.now().isoformat(),
    }


# ──────────────────────────────────────────────
# 5. 직접 실행 진입점 (테스트용)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 로거 임시 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler()],
    )

    # 더미 기사로 테스트
    dummy_articles = [
        {
            "source": "야후 파이낸스",
            "title": "Fed holds rates steady, signals two cuts in 2025",
            "summary": "The Federal Reserve kept interest rates unchanged and signaled two rate cuts for 2025.",
        },
        {
            "source": "한국경제",
            "title": "코스피, 외국인 매수세에 2,700선 회복",
            "summary": "외국인 투자자들의 순매수가 이어지며 코스피 지수가 2,700선을 회복했다.",
        },
        {
            "source": "매일경제",
            "title": "엔화 약세 지속... 일본은행 금리 인상 신호",
            "summary": "일본은행이 추가 금리 인상 가능성을 시사하면서 엔화 흐름에 변화가 예상된다.",
        },
    ]

    try:
        result = generate_blog_post(dummy_articles)
        print("\n" + "=" * 60)
        print(f"제목: {result['title']}")
        print("=" * 60)
        print(result["content"])
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
