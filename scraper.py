"""
macromalt 자동화 시스템 - 뉴스 수집 모듈
=====================================================
실행 방법:
  1. 가상환경 활성화: source venv/bin/activate
  2. 라이브러리 설치: pip install -r requirements.txt
  3. 실행: python scraper.py
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# 0. 환경 변수 로드
# ──────────────────────────────────────────────
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
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("macromalt")


# ──────────────────────────────────────────────
# 2. 소스 설정 로드
# ──────────────────────────────────────────────
def load_sources(path: str = "sources.json") -> list[dict]:
    """sources.json을 읽어 활성화된 소스 목록을 반환합니다."""
    sources_path = Path(__file__).parent / path
    try:
        with open(sources_path, encoding="utf-8") as f:
            data = json.load(f)
        enabled = [s for s in data["sources"] if s.get("enabled", True)]
        logger.info(f"소스 설정 로드 완료: {len(enabled)}개 활성 소스")
        return enabled
    except FileNotFoundError:
        logger.error(f"sources.json 파일을 찾을 수 없습니다: {sources_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"sources.json 파싱 오류: {e}")
        return []


# ──────────────────────────────────────────────
# 3. RSS 수집 함수
# ──────────────────────────────────────────────
def fetch_rss(source: dict) -> list[dict]:
    """
    RSS 피드에서 최신 기사 제목과 요약을 수집합니다.

    반환값 예시:
        [{"source": "한국경제", "title": "...", "summary": "...", "url": "..."}]
    """
    results = []
    name = source["name"]
    url = source["url"]
    limit = source.get("fetch_limit", 10)

    try:
        feed = feedparser.parse(url)

        if feed.bozo and feed.bozo_exception:
            raise ValueError(f"RSS 파싱 경고: {feed.bozo_exception}")

        entries = feed.entries[:limit]
        for entry in entries:
            title = entry.get("title", "제목 없음").strip()
            summary = entry.get("summary", "")
            # HTML 태그 제거
            summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ").strip()
            summary = summary[:300] + "..." if len(summary) > 300 else summary

            results.append(
                {
                    "source": name,
                    "type": "RSS",
                    "title": title,
                    "summary": summary,
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "collected_at": datetime.now().isoformat(),
                }
            )

        logger.info(f"[{name}] RSS 수집 성공: {len(results)}건")

    except Exception as e:
        logger.error(f"[{name}] RSS 수집 실패: {e}")

    return results


# ──────────────────────────────────────────────
# 4. 웹 크롤링 수집 함수
# ──────────────────────────────────────────────
def fetch_web(source: dict) -> list[dict]:
    """
    일반 웹 페이지에서 기사 제목과 요약을 수집합니다.
    sources.json의 selectors 설정을 기반으로 파싱합니다.

    반환값 예시:
        [{"source": "인베스팅 닷컴", "title": "...", "summary": "...", "url": "..."}]
    """
    results = []
    name = source["name"]
    url = source["url"]
    limit = source.get("fetch_limit", 10)
    selectors = source.get("selectors", {})

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    try:
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        article_selector = selectors.get("article_list", "article")
        title_selector = selectors.get("title", "h2")
        summary_selector = selectors.get("summary", "p")

        articles = soup.select(article_selector)[:limit]

        for article in articles:
            title_el = article.select_one(title_selector)
            summary_el = article.select_one(summary_selector)
            link_el = article.select_one(selectors.get("link", "a"))

            title = title_el.get_text(strip=True) if title_el else "제목 없음"
            summary = summary_el.get_text(strip=True) if summary_el else ""
            summary = summary[:300] + "..." if len(summary) > 300 else summary
            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                href = url.rstrip("/") + "/" + href.lstrip("/")

            results.append(
                {
                    "source": name,
                    "type": "Web",
                    "title": title,
                    "summary": summary,
                    "url": href,
                    "published": "",
                    "collected_at": datetime.now().isoformat(),
                }
            )

        logger.info(f"[{name}] 웹 크롤링 성공: {len(results)}건")

    except requests.exceptions.Timeout:
        logger.error(f"[{name}] 웹 크롤링 실패: 요청 시간 초과 (15초)")
    except requests.exceptions.HTTPError as e:
        logger.error(f"[{name}] 웹 크롤링 실패: HTTP 오류 {e.response.status_code}")
    except Exception as e:
        logger.error(f"[{name}] 웹 크롤링 실패: {e}")

    return results


# ──────────────────────────────────────────────
# 5. 통합 수집 실행 함수
# ──────────────────────────────────────────────
def run_all_sources() -> list[dict]:
    """
    모든 활성 소스에서 기사를 수집하고 통합 결과를 반환합니다.

    반환값:
        수집된 전체 기사 딕셔너리 리스트
    """
    logger.info("=" * 60)
    logger.info("macromalt 뉴스 수집 시작")
    logger.info("=" * 60)

    sources = load_sources()
    if not sources:
        logger.warning("활성화된 소스가 없습니다. sources.json을 확인하세요.")
        return []

    all_articles = []

    for source in sources:
        collect_type = source.get("type", "RSS").upper()
        if collect_type == "RSS":
            articles = fetch_rss(source)
        elif collect_type == "WEB":
            articles = fetch_web(source)
        else:
            logger.warning(f"[{source['name']}] 알 수 없는 수집 타입: {collect_type}")
            articles = []

        all_articles.extend(articles)

    logger.info("=" * 60)
    logger.info(f"수집 완료: 총 {len(all_articles)}건")
    logger.info("=" * 60)

    return all_articles


# ──────────────────────────────────────────────
# 6. 결과 출력 헬퍼 (디버깅용)
# ──────────────────────────────────────────────
def print_articles(articles: list[dict]) -> None:
    """수집된 기사를 콘솔에 보기 좋게 출력합니다."""
    if not articles:
        print("\n수집된 기사가 없습니다.")
        return

    print(f"\n{'='*60}")
    print(f"총 {len(articles)}건 수집됨")
    print(f"{'='*60}")

    for i, article in enumerate(articles, 1):
        print(f"\n[{i}] [{article['source']}]")
        print(f"  제목  : {article['title']}")
        print(f"  요약  : {article['summary'][:100]}..." if len(article.get('summary', '')) > 100 else f"  요약  : {article.get('summary', '')}")
        print(f"  URL   : {article['url']}")
        print(f"  수집일: {article['collected_at'][:19]}")


# ──────────────────────────────────────────────
# 7. 직접 실행 진입점
# ──────────────────────────────────────────────
if __name__ == "__main__":
    articles = run_all_sources()
    print_articles(articles)
