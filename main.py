"""
macromalt 자동화 시스템 - 메인 파이프라인
=====================================================
실행 순서:
  1. scraper.py  → 뉴스 수집
  2. generator.py → AI 블로그 포스팅 생성 (gpt-4o)
  3. publisher.py → WordPress 임시저장(Draft) 업로드

실행 방법:
  source venv/bin/activate
  python main.py
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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
# 2. 파이프라인 단계별 실행 함수
# ──────────────────────────────────────────────
def step_scrape() -> list[dict]:
    """Step 1: 뉴스 수집"""
    from scraper import run_all_sources

    logger.info("▶ [Step 1/3] 뉴스 수집 시작")
    articles = run_all_sources()

    if not articles:
        raise RuntimeError("수집된 기사가 0건입니다. sources.json 및 네트워크를 확인하세요.")

    logger.info(f"✅ [Step 1/3] 뉴스 수집 완료: {len(articles)}건")
    return articles


def step_generate(articles: list[dict]) -> dict:
    """Step 2: AI 블로그 포스팅 생성"""
    from generator import generate_blog_post

    logger.info("▶ [Step 2/3] 블로그 포스팅 생성 시작 (GPT-4o)")
    post = generate_blog_post(articles)
    logger.info(f"✅ [Step 2/3] 포스팅 생성 완료: '{post['title']}'")
    return post


def step_publish(post: dict) -> dict:
    """Step 3: WordPress Draft 업로드"""
    from publisher import publish_draft

    logger.info("▶ [Step 3/3] WordPress 업로드 시작")
    result = publish_draft(title=post["title"], content=post["content"])
    logger.info(f"✅ [Step 3/3] 업로드 완료: Post ID {result['post_id']}")
    return result


# ──────────────────────────────────────────────
# 3. 메인 실행 진입점
# ──────────────────────────────────────────────
def main() -> None:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 60)
    logger.info(f"macromalt 파이프라인 시작 [run_id: {run_id}]")
    logger.info("=" * 60)

    try:
        # Step 1: 수집
        articles = step_scrape()

        # Step 2: 생성
        post = step_generate(articles)

        # Step 3: 발행
        result = step_publish(post)

        logger.info("=" * 60)
        logger.info(f"🎉 파이프라인 성공 [run_id: {run_id}]")
        logger.info(f"   제목     : {post['title']}")
        logger.info(f"   Post ID  : {result['post_id']}")
        logger.info(f"   URL      : {result['post_url']}")
        logger.info(f"   상태     : {result['status']} (임시저장)")
        logger.info("=" * 60)

    except RuntimeError as e:
        logger.error("=" * 60)
        logger.error(f"❌ 파이프라인 실패 [run_id: {run_id}] - 수집 오류")
        logger.error(f"   원인: {e}")
        logger.error("=" * 60)
        sys.exit(1)

    except ValueError as e:
        logger.error("=" * 60)
        logger.error(f"❌ 파이프라인 실패 [run_id: {run_id}] - 설정 오류")
        logger.error(f"   원인: {e}")
        logger.error("   .env 파일의 API 키와 WordPress 정보를 확인하세요.")
        logger.error("=" * 60)
        sys.exit(1)

    except PermissionError as e:
        logger.error("=" * 60)
        logger.error(f"❌ 파이프라인 실패 [run_id: {run_id}] - 인증 오류")
        logger.error(f"   원인: {e}")
        logger.error("=" * 60)
        sys.exit(1)

    except Exception as e:
        logger.exception("=" * 60)
        logger.exception(f"❌ 파이프라인 실패 [run_id: {run_id}] - 예상치 못한 오류")
        logger.exception(f"   원인: {e}")
        logger.exception("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
