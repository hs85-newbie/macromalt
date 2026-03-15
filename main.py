"""
macromalt 자동화 시스템 - 메인 파이프라인 (Phase 7 / v3 정책 반영)
=====================================================
실행 순서:
  Step 1   — 뉴스 수집 (기존 RSS/Web 소스)
  Step 1B  — 리서치 수집 (네이버금융 + 한경 컨센서스)
  Step 2A  — Post 1 생성: 심층 경제 분석
  Step 2B  — Post 2 생성: 종목 리포트
  Step 3A  — Post 1 WordPress 임시저장
  Step 3B  — Post 2 WordPress 임시저장

에러 처리:
  Post 1 실패 → Post 2도 중단 (파이프라인 전체 종료)
  Post 2 실패 → Post 1 결과는 유지 (경고 로그 후 종료)

실행 방법:
  source venv/bin/activate
  python main.py
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────
# 0. 슬롯 식별 — Phase 10
# ──────────────────────────────────────────────

def _is_us_dst(dt: datetime) -> bool:
    """미국 서머타임(EDT) 적용 여부 판단.
    규칙: 3월 두 번째 일요일 ~ 11월 첫 번째 일요일 (미국 DST 기준).
    """
    year = dt.year
    # 3월 두 번째 일요일
    mar1 = datetime(year, 3, 1)
    dst_start = mar1 + timedelta(days=(6 - mar1.weekday()) % 7 + 7)
    # 11월 첫 번째 일요일
    nov1 = datetime(year, 11, 1)
    dst_end = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)
    return dst_start.date() <= dt.date() < dst_end.date()


def detect_slot(dt: datetime = None) -> str:
    """현재 시각(KST)을 기준으로 발행 슬롯을 반환한다.

    슬롯 정의 (KST):
      morning  : 05:00 ~ 11:59  — 미국장 마감 → 한국장 개장 전
      evening  : 14:00 ~ 20:59  — 한국장 마감 리뷰
      us_open  : DST   21:30 ~ 22:29  / non-DST 22:30 ~ 23:29
                 미국장 개장 30분 전 중심 ±30분 윈도우
      default  : 그 외 시간대    — 중립 일반 브리핑
    """
    if dt is None:
        dt = datetime.now()
    hm = dt.hour * 100 + dt.minute  # 예: 21:35 → 2135

    if 500 <= hm < 1200:
        return "morning"
    if 1400 <= hm < 2100:
        return "evening"

    # us_open 윈도우: DST 여부에 따라 30분씩 이동
    if _is_us_dst(dt):
        if 2130 <= hm < 2230:
            return "us_open"
    else:
        if 2230 <= hm < 2330:
            return "us_open"

    return "default"


# ──────────────────────────────────────────────
# 1. 로거 설정 (파일 + 콘솔 동시 출력)
# ──────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "macromalt_daily.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("macromalt")


# ──────────────────────────────────────────────
# 2. 카테고리 ID 로드 헬퍼
# ──────────────────────────────────────────────
def _get_category_ids(env_key: str, default: list) -> list:
    """
    .env에서 카테고리 ID를 읽어 반환합니다.
    값이 없거나 파싱 실패 시 default를 사용합니다.
    """
    val = os.getenv(env_key, "").strip()
    if val:
        try:
            return [int(x.strip()) for x in val.split(",") if x.strip()]
        except ValueError:
            logger.warning(f"⚠ {env_key} 값 파싱 실패, 기본값 {default} 사용")
    return default


# ──────────────────────────────────────────────
# 3. 파이프라인 단계별 실행 함수
# ──────────────────────────────────────────────
def step_scrape_news() -> list[dict]:
    """Step 1: 뉴스 수집 (RSS/Web 소스)"""
    from scraper import run_all_sources

    logger.info("▶ [Step 1] 뉴스 수집 시작")
    articles = run_all_sources()

    if not articles:
        raise RuntimeError("수집된 기사가 0건입니다. sources.json 및 네트워크를 확인하세요.")

    logger.info(f"✅ [Step 1] 뉴스 수집 완료: {len(articles)}건")
    return articles


def step_scrape_research() -> list[dict]:
    """Step 1B: 리서치 수집 (네이버금융 + 한경 컨센서스)"""
    from scraper import run_research_sources

    logger.info("▶ [Step 1B] 리서치 데이터 수집 시작")
    research = run_research_sources()
    logger.info(f"✅ [Step 1B] 리서치 수집 완료: {len(research)}건")
    return research


def step_generate_analysis(news: list[dict], research: list[dict], slot: str = "default") -> dict:
    """Step 2A: Post 1 — 심층 경제 분석 생성"""
    from generator import generate_deep_analysis

    logger.info("▶ [Step 2A] Post 1 심층 경제 분석 생성 시작")
    post1 = generate_deep_analysis(news, research, slot=slot)
    logger.info(f"✅ [Step 2A] Post 1 생성 완료: '{post1['title']}'")
    logger.info(f"   핵심 주제: {post1.get('theme', 'N/A')}")
    return post1


def step_generate_picks(post1: dict, news: list[dict], research: list[dict], slot: str = "default") -> dict:
    """Step 2B: Post 2 — 종목 리포트 생성"""
    from generator import generate_stock_picks_report

    logger.info("▶ [Step 2B] Post 2 종목 리포트 생성 시작")
    post2 = generate_stock_picks_report(
        theme=post1.get("theme", ""),
        key_data=post1.get("key_data", []),
        post1_content=post1.get("content", ""),
        news=news,
        research=research,
        materials=post1.get("materials"),   # Phase 7: Post 1 분석 재사용
        slot=slot,                           # Phase 10: 슬롯 전달
    )
    logger.info(f"✅ [Step 2B] Post 2 생성 완료: '{post2['title']}'")
    picks_count = len(post2.get("picks", []))
    logger.info(f"   선정 종목: {picks_count}개")
    return post2


def step_publish(post: dict, category_ids: list, step_label: str) -> dict:
    """Step 3A/3B: WordPress Draft 업로드"""
    from publisher import publish_draft

    logger.info(f"▶ [{step_label}] WordPress 업로드 시작: '{post['title']}'")
    result = publish_draft(
        title=post["title"],
        content=post["content"],
        category_ids=category_ids,
    )
    logger.info(f"✅ [{step_label}] 업로드 완료: Post ID {result['post_id']}")
    return result


# ──────────────────────────────────────────────
# 4. 메인 실행 진입점
# ──────────────────────────────────────────────
def main() -> None:
    now    = datetime.now()
    run_id = now.strftime("%Y%m%d_%H%M%S")
    slot   = detect_slot(now)

    logger.info("=" * 60)
    logger.info(f"macromalt Phase 10 파이프라인 시작 [run_id: {run_id}]")
    logger.info(f"[Phase 10] 슬롯: {slot} | run_id: {run_id}")
    logger.info("=" * 60)

    # 카테고리 ID 로드
    cat_analysis = _get_category_ids("WP_CATEGORY_ANALYSIS", [2])
    cat_picks    = _get_category_ids("WP_CATEGORY_PICKS",    [2])
    logger.info(f"   카테고리 — 심층분석: {cat_analysis} | 종목리포트: {cat_picks}")

    post1_result = None
    post2_result = None

    try:
        # ── Step 1: 수집 ──────────────────────────────
        news     = step_scrape_news()
        research = step_scrape_research()

        # ── Step 2A: Post 1 생성 ──────────────────────
        post1 = step_generate_analysis(news, research, slot=slot)

    except RuntimeError as e:
        logger.error("=" * 60)
        logger.error(f"❌ [Step 1] 수집 실패 [run_id: {run_id}]")
        logger.error(f"   원인: {e}")
        logger.error("=" * 60)
        sys.exit(1)

    except Exception as e:
        logger.exception(f"❌ [Step 2A] Post 1 생성 실패 [run_id: {run_id}]")
        logger.error(f"   원인: {e}")
        logger.error("   Post 1 실패로 Post 2 생성을 중단합니다.")
        sys.exit(1)

    try:
        # ── Step 2B: Post 2 생성 ──────────────────────
        post2 = step_generate_picks(post1, news, research, slot=slot)

    except Exception as e:
        logger.error(f"⚠ [Step 2B] Post 2 생성 실패 — Post 1은 계속 발행합니다.")
        logger.error(f"   원인: {e}")
        post2 = None

    try:
        # ── Step 3A: Post 1 발행 ─────────────────────
        post1_result = step_publish(post1, cat_analysis, "Step 3A")

    except Exception as e:
        logger.error(f"❌ [Step 3A] Post 1 발행 실패 [run_id: {run_id}]")
        logger.error(f"   원인: {e}")
        sys.exit(1)

    if post2 is not None:
        try:
            # ── Step 3B: Post 2 발행 ─────────────────
            post2_result = step_publish(post2, cat_picks, "Step 3B")

        except Exception as e:
            logger.error(f"⚠ [Step 3B] Post 2 발행 실패")
            logger.error(f"   원인: {e}")
            logger.warning("   Post 1은 정상 발행되었습니다.")

    # ── Phase 10: 발행 이력 저장 ─────────────────────
    if post1_result:
        try:
            from generator import save_publish_history
            save_publish_history(
                slot=slot,
                post1=post1,
                post2=post2 if post2 is not None else None,
            )
        except Exception as e:
            logger.warning(f"⚠ 발행 이력 저장 실패 (비치명): {e}")

    # ── 최종 결과 요약 ────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"🎉 macromalt Phase 10 파이프라인 완료 [run_id: {run_id}] [슬롯: {slot}]")
    logger.info("-" * 60)

    if post1_result:
        logger.info("  📄 Post 1 — 심층 경제 분석")
        logger.info(f"     제목    : {post1['title']}")
        logger.info(f"     주제    : {post1.get('theme', 'N/A')}")
        logger.info(f"     Post ID : {post1_result['post_id']}")
        logger.info(f"     URL     : {post1_result['post_url']}")
        logger.info(f"     상태    : {post1_result['status']} (임시저장)")

    logger.info("-" * 60)

    if post2_result:
        logger.info("  📊 Post 2 — 종목 리포트")
        logger.info(f"     제목    : {post2['title']}")
        picks = post2.get("picks", [])
        if picks:
            ticker_names = ", ".join(
                f"{p.get('name','?')}({p.get('ticker','?')})" for p in picks
            )
            logger.info(f"     종목    : {ticker_names}")
        logger.info(f"     Post ID : {post2_result['post_id']}")
        logger.info(f"     URL     : {post2_result['post_url']}")
        logger.info(f"     상태    : {post2_result['status']} (임시저장)")
    elif post2 is None:
        logger.warning("  ⚠ Post 2 — 생성 또는 발행 실패 (Post 1은 정상)")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
