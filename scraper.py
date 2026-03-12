"""
macromalt 자동화 시스템 - 뉴스 수집 모듈 (Phase 6)
=====================================================
실행 방법:
  1. 가상환경 활성화: source venv/bin/activate
  2. 라이브러리 설치: pip install -r requirements.txt
  3. 실행: python scraper.py

Phase 6 변경:
  - sources.json 기반 범용 리서치 수집 엔진 (_fetch_research_web / _fetch_research_auth)
  - AUTH_PROVIDERS 레지스트리로 인증 소스 확장성 확보
  - validate_date() 유틸로 항목별 날짜 검증
  - run_research_sources()가 sources.json을 자동 순회 (하드코딩 제거)
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
def load_sources(path: str = "sources.json") -> list:
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
def fetch_rss(source: dict) -> list:
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
def fetch_web(source: dict) -> list:
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
# 5. 통합 수집 실행 함수 (뉴스 전용)
# ──────────────────────────────────────────────
def run_all_sources() -> list:
    """
    모든 활성 뉴스 소스(RSS/Web)에서 기사를 수집하고 통합 결과를 반환합니다.
    RESEARCH_* 타입은 run_research_sources()에서 별도 처리합니다.

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
        elif collect_type.startswith("RESEARCH_"):
            # RESEARCH 타입은 run_research_sources()에서 처리 — 조용히 스킵
            continue
        else:
            logger.warning(f"[{source['name']}] 알 수 없는 수집 타입: {collect_type}")
            articles = []

        all_articles.extend(articles)

    logger.info("=" * 60)
    logger.info(f"수집 완료: 총 {len(all_articles)}건")
    logger.info("=" * 60)

    return all_articles


# ──────────────────────────────────────────────
# 6. 날짜 검증 유틸
# ──────────────────────────────────────────────
def validate_date(date_str: str, max_days: int) -> bool:
    """
    단일 항목의 날짜 문자열이 최근 max_days일 이내인지 검증합니다.

    반환 규칙:
    - date_str이 비어있으면 True (날짜 없는 항목은 포함 — 안전 기본값)
    - 파싱 실패 시 True (안전 기본값)
    - parse(date_str) >= now - max_days 이면 True

    지원 형식: "2024.03.12", "2024-03-12", RFC 2822, ISO datetime 등
    """
    if not date_str or not date_str.strip():
        return True
    try:
        cutoff = datetime.now() - timedelta(days=max_days)
        parsed = dateutil_parser.parse(date_str, ignoretz=True)
        return parsed >= cutoff
    except Exception:
        return True  # 파싱 실패 시 포함


def _filter_by_date(items: list, days: int = 7) -> list:
    """
    published 필드 기준, 최근 N일 이내 항목만 반환합니다.
    (내부적으로 validate_date()를 사용합니다)
    """
    return [item for item in items if validate_date(item.get("published", ""), days)]


# ──────────────────────────────────────────────
# 7. 공통 HTTP 헤더 상수
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


# ──────────────────────────────────────────────
# 8. 한경 컨센서스 로그인 핸들러
# ──────────────────────────────────────────────
def _hankyung_login():
    """
    한경 컨센서스 로그인 세션을 반환합니다.
    HANKYUNG_USERNAME / HANKYUNG_PASSWORD 환경 변수가 없거나 로그인 실패 시 None 반환.
    """
    user_id = os.getenv("HANKYUNG_USERNAME", "").strip()
    user_pw = os.getenv("HANKYUNG_PASSWORD", "").strip()

    if not user_id or not user_pw:
        logger.warning("[한경컨센서스] HANKYUNG_USERNAME/PASSWORD 미설정 — 수집 건너뜀")
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


# ──────────────────────────────────────────────
# 8-B. AUTH 프로바이더 레지스트리
# ──────────────────────────────────────────────
# 새 인증 소스 추가 시:
#   1. 로그인 함수를 정의하고
#   2. 이 딕셔너리에 {"키이름": 로그인함수} 한 줄 추가
#   3. sources.json의 해당 소스에 "auth_provider": "키이름" 설정
AUTH_PROVIDERS = {
    "hankyung": _hankyung_login,
}


# ──────────────────────────────────────────────
# 9. 범용 리서치 수집 엔진 — RESEARCH_WEB
# ──────────────────────────────────────────────
def _fetch_research_web(source: dict) -> list:
    """
    RESEARCH_WEB 타입 소스를 sources.json 설정으로 수집하는 범용 엔진.

    sources.json에서 읽는 필드:
      pages       [{path, label}] — 멀티페이지 순회 (없으면 url 단일 페이지)
      base_url    상대 href를 절대 URL로 변환할 기준
      selectors   row / row_fallback / title / link / broker / sector / target_price / date
      extract     {broker: bool, sector: bool, target_price: bool}
      days_filter 날짜 필터 기준일 (기본 7)
      fetch_limit 최대 수집 건수 (기본 10)
      weight      항목 우선순위 (기본 3)

    반환 스키마:
      {source, type, data_type, category, title, summary, url,
       broker, sector, target_price, published, weight, collected_at}
    """
    results = []
    name        = source["name"]
    base_url    = source.get("base_url", "").rstrip("/")
    selectors   = source.get("selectors", {})
    extract_cfg = source.get("extract", {})
    days_filter = source.get("days_filter", 7)
    fetch_limit = source.get("fetch_limit", 10)
    weight      = source.get("weight", 3)

    # 페이지 목록 결정
    pages_cfg = source.get("pages")
    if pages_cfg:
        page_targets = []
        for p in pages_cfg:
            path = p.get("path", "")
            if path.startswith("http"):
                page_url = path
            else:
                page_url = base_url + path if base_url else path
            page_targets.append((page_url, p.get("label", "")))
    else:
        page_targets = [(source["url"], "")]

    row_selector          = selectors.get("row", "table tr")
    row_fallback_selector = selectors.get("row_fallback", "")
    title_selector        = selectors.get("title", "a")
    link_selector         = selectors.get("link", "a")
    broker_selector       = selectors.get("broker", "")
    sector_selector       = selectors.get("sector", "")

    for page_url, category_label in page_targets:
        try:
            resp = requests.get(page_url, headers=_NAVER_RESEARCH_HEADERS, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"[{name}:{category_label}] HTTP {resp.status_code}")
                continue
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            rows = soup.select(row_selector)
            if not rows and row_fallback_selector:
                rows = soup.select(row_fallback_selector)

            count = 0
            for row in rows:
                if count >= fetch_limit:
                    break

                cols = row.find_all("td")

                # 제목 + 링크
                title_el = row.select_one(title_selector)
                if not title_el:
                    title_el = row.select_one(link_selector)
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue

                href = title_el.get("href", "")
                if href and not href.startswith("http"):
                    href = base_url + "/" + href.lstrip("/") if base_url else href

                # 브로커 (선택자 → CSS 우선, 없으면 td[1] 텍스트)
                broker = ""
                if extract_cfg.get("broker"):
                    if broker_selector:
                        broker_el = row.select_one(broker_selector)
                        broker = broker_el.get_text(strip=True) if broker_el else ""
                    if not broker and len(cols) > 1:
                        candidate = cols[1].get_text(strip=True)
                        # 날짜 패턴이 아닌 경우에만 broker로 사용
                        if candidate and not re.match(r"\d{4}[.\-]\d{2}", candidate):
                            broker = candidate

                # 섹터 (선택자 → CSS 우선, 없으면 td[2] 텍스트)
                sector = ""
                if extract_cfg.get("sector"):
                    if sector_selector:
                        sector_el = row.select_one(sector_selector)
                        sector = sector_el.get_text(strip=True) if sector_el else ""
                    if not sector and len(cols) > 2:
                        candidate = cols[2].get_text(strip=True)
                        if candidate and not re.match(r"\d{4}[.\-]\d{2}", candidate):
                            sector = candidate

                # 날짜 — 선택자가 비어있으면 td 역순 순회로 정규식 탐지
                date_selector = selectors.get("date", "")
                date_text = ""
                if date_selector:
                    date_el = row.select_one(date_selector)
                    date_text = date_el.get_text(strip=True) if date_el else ""
                else:
                    for col in reversed(cols):
                        text = col.get_text(strip=True)
                        if re.match(r"\d{4}[.\-]\d{2}[.\-]\d{2}", text):
                            date_text = text
                            break

                # 목표가 — 정규식 자동 탐지 (extract.target_price=true 시)
                target_price = ""
                if extract_cfg.get("target_price"):
                    tp_selector = selectors.get("target_price", "")
                    if tp_selector:
                        tp_el = row.select_one(tp_selector)
                        target_price = tp_el.get_text(strip=True) if tp_el else ""
                    if not target_price:
                        for col in cols:
                            text = col.get_text(strip=True)
                            if (re.match(r"[\d,]+원?$", text)
                                    and text not in (date_text, broker, sector)
                                    and text):
                                target_price = text
                                break

                # 날짜 필터 — 항목 수준에서 즉시 적용
                if not validate_date(date_text, days_filter):
                    continue

                # 구조화된 요약 생성
                meta_parts = []
                if broker:
                    meta_parts.append(broker)
                if sector:
                    meta_parts.append(sector)
                summary = f"[{'·'.join(meta_parts)}] {category_label} 리포트" if meta_parts else f"{category_label} 리포트"

                results.append({
                    "source":       name,
                    "type":         "RESEARCH_WEB",
                    "data_type":    "research",
                    "category":     category_label,
                    "title":        title,
                    "summary":      summary,
                    "url":          href,
                    "broker":       broker,
                    "sector":       sector,
                    "target_price": target_price,
                    "published":    date_text,
                    "weight":       weight,
                    "collected_at": datetime.now().isoformat(),
                })
                count += 1

            logger.info(f"[{name}:{category_label}] 수집: {count}건")

        except Exception as e:
            logger.warning(f"[{name}:{category_label}] 수집 실패: {e}")

    logger.info(f"[{name}] RESEARCH_WEB 총 수집: {len(results)}건")
    return results


# ──────────────────────────────────────────────
# 10. 범용 리서치 수집 엔진 — RESEARCH_AUTH
# ──────────────────────────────────────────────
def _fetch_research_auth(source: dict) -> list:
    """
    RESEARCH_AUTH 타입 소스를 sources.json 설정 + AUTH_PROVIDERS로 수집하는 범용 엔진.

    sources.json에서 읽는 필드:
      auth_provider  AUTH_PROVIDERS 딕셔너리 키 (예: "hankyung")
      base_url       상대 href를 절대 URL로 변환할 기준
      api_path       목록 엔드포인트 경로
      api_params     API 쿼리 파라미터 dict
      selectors      RESEARCH_WEB와 동일
      extract        {broker, sector, target_price: bool}
      days_filter    날짜 필터 기준일 (기본 30)
      fetch_limit    최대 수집 건수 (기본 30)
      weight         항목 우선순위 (기본 5)

    반환 스키마:
      {source, type, data_type, title, summary, url,
       broker, sector, target_price, published, weight, collected_at}
    """
    name        = source["name"]
    base_url    = source.get("base_url", source.get("url", "").rstrip("/"))
    selectors   = source.get("selectors", {})
    extract_cfg = source.get("extract", {})
    days_filter = source.get("days_filter", 30)
    fetch_limit = source.get("fetch_limit", 30)
    weight      = source.get("weight", 5)
    auth_key    = source.get("auth_provider", "")
    api_path    = source.get("api_path", "")
    api_params  = source.get("api_params", {})

    # 1. auth provider 조회 및 로그인
    login_fn = AUTH_PROVIDERS.get(auth_key)
    if not login_fn:
        logger.warning(f"[{name}] 알 수 없는 auth_provider: '{auth_key}' — 건너뜀")
        return []

    session = login_fn()
    if session is None:
        return []

    results = []
    try:
        # 2. API 목록 엔드포인트 호출
        list_url = base_url + api_path
        resp = session.get(list_url, params=api_params, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"[{name}] 목록 HTTP {resp.status_code}")
            return []
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 3. 행 파싱
        row_selector  = selectors.get("row", "table tbody tr")
        title_selector = selectors.get("title", "a")
        link_selector  = selectors.get("link", "a")
        broker_selector = selectors.get("broker", "")
        sector_selector = selectors.get("sector", "")

        rows = soup.select(row_selector)
        count = 0

        for row in rows:
            if count >= fetch_limit:
                break

            cols = row.find_all("td")

            # 제목 + 링크
            title_el = row.select_one(title_selector)
            if not title_el:
                title_el = row.select_one(link_selector)
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            href = title_el.get("href", "")
            if href and not href.startswith("http"):
                href = base_url + href

            # 브로커
            broker = ""
            if extract_cfg.get("broker"):
                if broker_selector:
                    broker_el = row.select_one(broker_selector)
                    broker = broker_el.get_text(strip=True) if broker_el else ""
                if not broker and len(cols) > 1:
                    candidate = cols[1].get_text(strip=True)
                    if candidate and not re.match(r"\d{4}[.\-]\d{2}", candidate):
                        broker = candidate

            # 섹터
            sector = ""
            if extract_cfg.get("sector"):
                if sector_selector:
                    sector_el = row.select_one(sector_selector)
                    sector = sector_el.get_text(strip=True) if sector_el else ""
                if not sector and len(cols) > 2:
                    candidate = cols[2].get_text(strip=True)
                    if candidate and not re.match(r"\d{4}[.\-]\d{2}", candidate):
                        sector = candidate

            # 날짜 + 목표가 — 정규식 자동 탐지
            date_text    = ""
            target_price = ""
            for col in cols:
                text = col.get_text(strip=True)
                if not date_text and re.match(r"\d{4}[.\-]\d{2}[.\-]\d{2}", text):
                    date_text = text
                elif (extract_cfg.get("target_price")
                      and not target_price
                      and re.match(r"[\d,]+원?$", text)
                      and text not in (broker, sector, date_text)
                      and text):
                    target_price = text

            # 날짜 필터 — 항목 수준
            if not validate_date(date_text, days_filter):
                continue

            # 구조화된 요약 생성
            if target_price:
                summary = f"[{broker}] 목표가: {target_price}" if broker else f"목표가: {target_price}"
            elif broker:
                summary = f"[{broker}] 애널리스트 리포트"
                if sector:
                    summary += f" ({sector})"
            else:
                summary = "애널리스트 리포트"

            results.append({
                "source":       name,
                "type":         "RESEARCH_AUTH",
                "data_type":    "consensus",
                "title":        title,
                "summary":      summary,
                "url":          href,
                "broker":       broker,
                "sector":       sector,
                "target_price": target_price,
                "published":    date_text,
                "weight":       weight,
                "collected_at": datetime.now().isoformat(),
            })
            count += 1

        logger.info(f"[{name}] RESEARCH_AUTH 수집: {count}건 (최근 {days_filter}일 필터)")

    except Exception as e:
        logger.warning(f"[{name}] RESEARCH_AUTH 수집 실패: {e}")

    return results


# ──────────────────────────────────────────────
# 11. 리서치 통합 수집 함수 (범용 엔진 기반)
# ──────────────────────────────────────────────
def run_research_sources() -> list:
    """
    sources.json의 RESEARCH_* 타입 소스를 자동 순회하여 수집합니다.
    새 리서치 소스 추가 = sources.json에 항목 추가만으로 완료 (Python 수정 불필요).

    디스패치:
      RESEARCH_WEB  → _fetch_research_web(source)
      RESEARCH_AUTH → _fetch_research_auth(source)

    반환값:
      weight 내림차순 정렬된 통합 리서치 리스트
    """
    logger.info("=" * 60)
    logger.info("macromalt 리서치 데이터 수집 시작")
    logger.info("=" * 60)

    sources = load_sources()
    research_sources = [
        s for s in sources
        if s.get("type", "").upper().startswith("RESEARCH_")
    ]

    if not research_sources:
        logger.warning("활성화된 RESEARCH 소스가 없습니다.")
        return []

    combined = []
    for source in research_sources:
        collect_type = source.get("type", "").upper()
        name = source.get("name", "알 수 없음")

        if collect_type == "RESEARCH_WEB":
            items = _fetch_research_web(source)
        elif collect_type == "RESEARCH_AUTH":
            items = _fetch_research_auth(source)
        else:
            logger.warning(f"[{name}] 지원되지 않는 RESEARCH 타입: {collect_type}")
            items = []

        combined.extend(items)

    # weight 내림차순 정렬 (높은 가중치 소스가 generator에 먼저 전달)
    combined.sort(key=lambda x: x.get("weight", 1), reverse=True)

    # 소스별 수집 건수 요약 로그
    logger.info("=" * 60)
    logger.info(f"리서치 수집 완료: 총 {len(combined)}건")
    by_source = {}
    for item in combined:
        by_source.setdefault(item["source"], 0)
        by_source[item["source"]] += 1
    for src, cnt in sorted(by_source.items(), key=lambda x: -x[1]):
        logger.info(f"  - {src}: {cnt}건")
    logger.info("=" * 60)

    return combined


# ──────────────────────────────────────────────
# 12. Deprecated 래퍼 함수 (하위 호환)
# ──────────────────────────────────────────────
def fetch_naver_research(days: int = 7) -> list:
    """
    [Deprecated — Phase 6] _fetch_research_web()으로 이전됨.
    하위 호환성을 위해 유지합니다. run_research_sources() 사용을 권장합니다.
    """
    logger.warning(
        "fetch_naver_research()는 deprecated입니다. "
        "run_research_sources()를 사용하세요."
    )
    # sources.json에서 naver_research 소스를 찾아 직접 호출
    sources_path = Path(__file__).parent / "sources.json"
    try:
        with open(sources_path, encoding="utf-8") as f:
            all_sources = json.load(f)["sources"]
    except Exception:
        all_sources = []
    naver_src = next((s for s in all_sources if s.get("id") == "naver_research"), None)
    if naver_src is None:
        logger.warning("sources.json에서 naver_research 소스를 찾을 수 없습니다.")
        return []
    overridden = {**naver_src, "days_filter": days}
    return _fetch_research_web(overridden)


def fetch_hankyung_consensus(days: int = 30) -> list:
    """
    [Deprecated — Phase 6] _fetch_research_auth()으로 이전됨.
    하위 호환성을 위해 유지합니다. run_research_sources() 사용을 권장합니다.
    """
    logger.warning(
        "fetch_hankyung_consensus()는 deprecated입니다. "
        "run_research_sources()를 사용하세요."
    )
    sources_path = Path(__file__).parent / "sources.json"
    try:
        with open(sources_path, encoding="utf-8") as f:
            all_sources = json.load(f)["sources"]
    except Exception:
        all_sources = []
    hk_src = next((s for s in all_sources if s.get("id") == "hankyung_consensus"), None)
    if hk_src is None:
        logger.warning("sources.json에서 hankyung_consensus 소스를 찾을 수 없습니다.")
        return []
    overridden = {**hk_src, "days_filter": days}
    return _fetch_research_auth(overridden)


# ──────────────────────────────────────────────
# 13. 결과 출력 헬퍼 (디버깅용)
# ──────────────────────────────────────────────
def print_articles(articles: list) -> None:
    """수집된 기사를 콘솔에 보기 좋게 출력합니다."""
    if not articles:
        print("\n수집된 기사가 없습니다.")
        return

    print(f"\n{'='*60}")
    print(f"총 {len(articles)}건 수집됨")
    print(f"{'='*60}")

    for i, article in enumerate(articles, 1):
        print(f"\n[{i}] [{article['source']}] (weight={article.get('weight', 1)})")
        print(f"  제목  : {article['title']}")
        summary = article.get("summary", "")
        print(f"  요약  : {summary[:100]}..." if len(summary) > 100 else f"  요약  : {summary}")
        print(f"  URL   : {article['url']}")
        print(f"  수집일: {article['collected_at'][:19]}")


# ──────────────────────────────────────────────
# 14. 직접 실행 진입점
# ──────────────────────────────────────────────
if __name__ == "__main__":
    articles = run_all_sources()
    print_articles(articles)
