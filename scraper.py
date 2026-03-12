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
import re
from datetime import datetime, timedelta
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
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
# 6. 날짜 필터 유틸
# ──────────────────────────────────────────────
def _filter_by_date(items: list[dict], days: int = 7) -> list[dict]:
    """
    published 필드 기준, 최근 N일 이내 항목만 반환합니다.
    날짜 파싱 실패 시 해당 항목을 포함(안전 기본값)합니다.
    """
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []
    for item in items:
        pub_str = item.get("published", "")
        if not pub_str:
            filtered.append(item)  # 날짜 없으면 포함
            continue
        try:
            pub_dt = dateutil_parser.parse(pub_str, ignoretz=True)
            if pub_dt >= cutoff:
                filtered.append(item)
        except Exception:
            filtered.append(item)  # 파싱 실패 시 포함
    return filtered


# ──────────────────────────────────────────────
# 7. 네이버금융 리서치 수집 (공개 접근, 인증 불필요)
# ──────────────────────────────────────────────
_NAVER_RESEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://finance.naver.com/",
}

def fetch_naver_research(days: int = 7) -> list[dict]:
    """
    네이버금융 리서치 시황 페이지에서 애널리스트 리포트를 수집합니다.
    - 로그인 불필요 (공개 페이지)
    - 최근 N일 이내 데이터만 반환
    - data_type='research' 필드 포함
    """
    results = []
    # 시황 리포트 목록
    target_pages = [
        ("https://finance.naver.com/research/market_info_list.naver", "시황"),
        ("https://finance.naver.com/research/debenture_list.naver", "채권"),
    ]

    for page_url, category in target_pages:
        try:
            resp = requests.get(
                page_url,
                headers=_NAVER_RESEARCH_HEADERS,
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning(f"[네이버리서치:{category}] HTTP {resp.status_code}")
                continue

            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            # 리포트 테이블 행 파싱
            rows = soup.select("table.type_1 tr") or soup.select("table tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                # 제목 + URL
                title_el = row.select_one("td.file a") or row.select_one("td a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://finance.naver.com" + href

                # 날짜 (보통 마지막 또는 두번째 컬럼)
                date_text = ""
                for col in reversed(cols):
                    text = col.get_text(strip=True)
                    if re.match(r"\d{4}\.\d{2}\.\d{2}", text):
                        date_text = text
                        break

                # 증권사 (두 번째 컬럼 등)
                broker = cols[1].get_text(strip=True) if len(cols) > 1 else ""

                results.append({
                    "source": "네이버금융 리서치",
                    "type": "RESEARCH_WEB",
                    "data_type": "research",
                    "category": category,
                    "title": title,
                    "summary": f"[{broker}] {category} 리포트",
                    "url": href,
                    "broker": broker,
                    "published": date_text,
                    "collected_at": datetime.now().isoformat(),
                })

        except Exception as e:
            logger.warning(f"[네이버리서치:{category}] 수집 실패: {e}")

    # 날짜 필터 적용
    before_count = len(results)
    results = _filter_by_date(results, days=days)
    logger.info(
        f"[네이버금융 리서치] 수집: {before_count}건 → "
        f"최근 {days}일 필터 후 {len(results)}건"
    )
    return results


# ──────────────────────────────────────────────
# 8. 한경 컨센서스 수집 (인증 필요)
# ──────────────────────────────────────────────
_HANKYUNG_BASE = "https://consensus.hankyung.com"
_HANKYUNG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": _HANKYUNG_BASE + "/",
}

def _hankyung_login():
    """
    한경 컨센서스 로그인 세션을 반환합니다.
    HANKYUNG_ID / HANKYUNG_PW 환경 변수가 없거나 로그인 실패 시 None 반환.
    """
    user_id = os.getenv("HANKYUNG_ID", "").strip()
    user_pw = os.getenv("HANKYUNG_PW", "").strip()

    if not user_id or not user_pw:
        logger.warning("[한경컨센서스] HANKYUNG_ID/PW 미설정 — 수집 건너뜀")
        return None

    session = requests.Session()
    session.headers.update(_HANKYUNG_HEADERS)

    try:
        # 1. 로그인 페이지 접근 (CSRF 토큰 수집)
        login_page_url = _HANKYUNG_BASE + "/apps.login/login.form"
        resp = session.get(login_page_url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # hidden input 필드 수집 (CSRF 등)
        hidden_inputs = {}
        for inp in soup.select("input[type=hidden]"):
            name = inp.get("name")
            value = inp.get("value", "")
            if name:
                hidden_inputs[name] = value

        # 2. 로그인 POST
        login_url = _HANKYUNG_BASE + "/apps.login/login.process"
        payload = {
            **hidden_inputs,
            "user_id": user_id,
            "user_password": user_pw,
        }
        resp = session.post(login_url, data=payload, timeout=10)

        # 로그인 성공 여부 확인 (리다이렉트 또는 쿠키로 판단)
        if resp.status_code in (200, 302) and session.cookies:
            logger.info("[한경컨센서스] 로그인 성공")
            return session
        else:
            logger.warning(f"[한경컨센서스] 로그인 실패 (HTTP {resp.status_code})")
            return None

    except Exception as e:
        logger.warning(f"[한경컨센서스] 로그인 오류: {e}")
        return None


def fetch_hankyung_consensus(days: int = 30) -> list[dict]:
    """
    한경 컨센서스에서 애널리스트 리포트 목록을 수집합니다.
    - 로그인 성공 시에만 수집 (실패 시 빈 리스트 반환)
    - 최근 N일 이내 데이터만 반환
    - data_type='consensus' 필드 포함
    """
    session = _hankyung_login()
    if session is None:
        return []

    results = []
    try:
        list_url = _HANKYUNG_BASE + "/apps.analysis/analysis.list"
        params = {"pageSize": 30, "pageIndex": 1}
        resp = session.get(list_url, params=params, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"[한경컨센서스] 리포트 목록 HTTP {resp.status_code}")
            return []

        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 리포트 목록 행 파싱
        rows = soup.select("table tbody tr") or soup.select(".report_list li")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            title_el = row.select_one("a.report_title") or row.select_one("td a")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            if href and not href.startswith("http"):
                href = _HANKYUNG_BASE + href

            # 증권사, 목표가, 날짜 추출
            broker = cols[1].get_text(strip=True) if len(cols) > 1 else ""
            target_price = ""
            date_text = ""
            for col in cols:
                text = col.get_text(strip=True)
                if re.match(r"\d{4}[.\-]\d{2}[.\-]\d{2}", text):
                    date_text = text
                elif re.match(r"[\d,]+원?$", text) and not date_text:
                    target_price = text

            results.append({
                "source": "한경 컨센서스",
                "type": "RESEARCH_AUTH",
                "data_type": "consensus",
                "title": title,
                "summary": f"[{broker}] 목표가: {target_price}" if target_price else f"[{broker}] 애널리스트 리포트",
                "url": href,
                "broker": broker,
                "target_price": target_price,
                "published": date_text,
                "collected_at": datetime.now().isoformat(),
            })

    except Exception as e:
        logger.warning(f"[한경컨센서스] 리포트 수집 실패: {e}")
        return []

    # 날짜 필터 적용
    before_count = len(results)
    results = _filter_by_date(results, days=days)
    logger.info(
        f"[한경 컨센서스] 수집: {before_count}건 → "
        f"최근 {days}일 필터 후 {len(results)}건"
    )
    return results


# ──────────────────────────────────────────────
# 9. 리서치 통합 수집 함수
# ──────────────────────────────────────────────
def run_research_sources() -> list[dict]:
    """
    네이버금융 리서치 + 한경 컨센서스를 통합 수집합니다.
    기존 run_all_sources()와 독립적으로 동작합니다.

    반환값:
        data_type='research' 또는 'consensus' 필드를 포함한 리포트 리스트
    """
    logger.info("=" * 60)
    logger.info("macromalt 리서치 데이터 수집 시작")
    logger.info("=" * 60)

    research = fetch_naver_research(days=7)
    consensus = fetch_hankyung_consensus(days=30)
    combined = research + consensus

    logger.info("=" * 60)
    logger.info(
        f"리서치 수집 완료: 총 {len(combined)}건 "
        f"(네이버리서치 {len(research)}건 / 한경컨센서스 {len(consensus)}건)"
    )
    logger.info("=" * 60)
    return combined


# ──────────────────────────────────────────────
# 10. 결과 출력 헬퍼 (디버깅용)
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
