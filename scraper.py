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

import io
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

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

        skipped_old = 0
        for entry in feed.entries:
            if len(results) >= limit:
                break

            published = entry.get("published", "")
            date_tier = _classify_date_tier(published)
            if date_tier == "old":
                skipped_old += 1
                continue  # v3 정책: 30일 초과 기사 제외

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
                    "published": published,
                    "date_tier": date_tier,
                    "collected_at": datetime.now().isoformat(),
                }
            )

        if skipped_old:
            logger.info(f"[{name}] 30일 초과 항목 {skipped_old}건 제외 (v3 정책)")
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


def _classify_date_tier(date_str: str) -> str:
    """
    날짜 문자열을 기준으로 자료 시점 등급을 반환합니다 (v3 정책).

    - "recent"   : 최근 7일 이내 (최우선 근거)
    - "extended" : 8~30일 이내 (보조 근거 — background_facts로 분리)
    - "old"      : 30일 초과 (수집 제외 대상 — 즉시 Drop)
    - "unknown"  : 날짜 파싱 불가 (우선순위 낮춤, 포함은 허용)
    """
    if not date_str or not date_str.strip():
        return "unknown"
    try:
        parsed = dateutil_parser.parse(date_str, ignoretz=True)
        days_ago = (datetime.now() - parsed).days
        if days_ago <= 7:
            return "recent"
        elif days_ago <= 30:
            return "extended"
        else:
            return "old"
    except Exception:
        return "unknown"


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

_HANKYUNG_BASE       = "https://consensus.hankyung.com"   # 컨센서스 데이터 도메인
_HANKYUNG_LOGIN_BASE = "https://id.hankyung.com"           # SSO 로그인 도메인 (v3 — 2026-03)
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
    한경 컨센서스 폼 기반 로그인 세션을 반환합니다.
    HANKYUNG_USERNAME / HANKYUNG_PASSWORD 환경 변수가 없거나 로그인 실패 시 None 반환.

    ⚠ Google/Naver/Kakao 소셜 로그인 전용 계정은 이 방식으로 인증이 불가합니다.
      소셜 로그인 계정은 브라우저 쿠키 세션 방식이 필요하며, 현재 지원되지 않습니다.
      자동화 실행 시 한경 컨센서스 소스는 조용히 건너뜁니다.

    로그인 엔드포인트 (v3 — 2026-03):
      GET  https://id.hankyung.com/login/login.do          (로그인 페이지, 세션 초기화)
      POST https://id.hankyung.com/login/ajaxActionLogin.do (AJAX 인증)
      필드: userId, userPass
    """
    user_id = os.getenv("HANKYUNG_USERNAME", "").strip()
    user_pw = os.getenv("HANKYUNG_PASSWORD", "").strip()

    if not user_id or not user_pw:
        logger.warning("[한경컨센서스] HANKYUNG_USERNAME/PASSWORD 미설정 — 수집 건너뜀")
        return None

    session = requests.Session()
    session.headers.update(_HANKYUNG_HEADERS)

    try:
        # 1. 로그인 페이지 접근 (세션 쿠키 초기화)
        login_page_url = _HANKYUNG_LOGIN_BASE + "/login/login.do"
        resp = session.get(login_page_url, timeout=10,
                           headers={"Referer": _HANKYUNG_BASE + "/"})
        soup = BeautifulSoup(resp.text, "html.parser")

        # hidden input 필드 수집 (CSRF 토큰 등)
        hidden_inputs = {}
        for inp in soup.select("input[type=hidden]"):
            name = inp.get("name")
            value = inp.get("value", "")
            if name:
                hidden_inputs[name] = value

        # 2. AJAX 로그인 POST
        ajax_url = _HANKYUNG_LOGIN_BASE + "/login/ajaxActionLogin.do"
        payload = {
            **hidden_inputs,
            "userId":   user_id,
            "userPass": user_pw,
        }
        resp = session.post(
            ajax_url,
            data=payload,
            timeout=10,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": login_page_url,
            },
        )

        # 로그인 성공 여부 확인 (JSON 응답)
        if resp.status_code != 200:
            logger.warning(f"[한경컨센서스] 로그인 실패 (HTTP {resp.status_code})")
            return None

        try:
            result = resp.json()
        except Exception:
            logger.warning("[한경컨센서스] 로그인 응답 JSON 파싱 실패")
            return None

        # resultCode '0000' = 성공 (한경 SSO 표준 코드)
        if result.get("resultCode") != "0000":
            logger.warning(f"[한경컨센서스] 로그인 실패 (resultCode={result.get('resultCode')})")
            return None

        # 3. SSO 콜백 처리 — callbackUrl + key + token 으로 실제 세션 쿠키 발급
        callback_url = result.get("callbackUrl", "")
        sso_key      = result.get("key", "")
        sso_token    = result.get("token", "")

        if callback_url and sso_token:
            try:
                cb_resp = session.get(
                    callback_url,
                    params={"key": sso_key, "token": sso_token},
                    timeout=10,
                    headers={"Referer": login_page_url},
                )
                logger.debug(f"[한경컨센서스] SSO 콜백 HTTP {cb_resp.status_code}")
            except Exception as cb_err:
                logger.warning(f"[한경컨센서스] SSO 콜백 오류 (무시): {cb_err}")

        logger.info("[한경컨센서스] 로그인 성공")
        return session

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

                # 날짜 시점 분류 — 30일 초과 항목 즉시 제외 (v3 정책)
                date_tier = _classify_date_tier(date_text)
                if date_tier == "old":
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
                    "date_tier":    date_tier,
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

            # 날짜 시점 분류 — 30일 초과 항목 즉시 제외 (v3 정책)
            date_tier = _classify_date_tier(date_text)
            if date_tier == "old":
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
                "date_tier":    date_tier,
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
# 13. OpenDART API — Phase 5-A
# ──────────────────────────────────────────────

# ── 상수: API 기본 URL ─────────────────────────────────────────────────────
DART_API_BASE = "https://opendart.fss.or.kr/api"

# ── 상수: corp_code 캐시 파일 경로 ────────────────────────────────────────
DART_CORP_CODE_CACHE = Path(__file__).parent / "dart_corp_codes.json"
# 캐시 유효기간: 1일 (86400초). 당일 이미 다운로드했으면 재사용
DART_CORP_CODE_CACHE_TTL = 86400

# ── 상수: 공시 이벤트 키워드 → 이벤트 타입 매핑 (확장 가능)
# 보고서명에 키워드가 포함될 경우 해당 event_type으로 분류됩니다.
# 새 이벤트 유형 추가 시 이 딕셔너리만 수정하세요.
DART_DISCLOSURE_EVENT_MAP: dict = {
    "단일판매":     "수주계약",
    "공급계약":     "수주계약",
    "자기주식 취득": "자사주취득",
    "자기주식취득":  "자사주취득",
    "유상증자":     "유상증자",
    "전환사채":     "CB발행",
    "신주인수권부사채": "BW발행",
    "합병":         "합병",
    "분할":         "분할",
    "소송":         "소송",
    "영업양수":     "자산양수도",
    "영업양도":     "자산양수도",
    "주식매수선택권": "스톡옵션",
}

# ── 상수: 재무 수치 수집 대상 계정명 (확장 가능)
# fnlttSinglAcnt 응답의 account_nm과 일치해야 합니다.
DART_TARGET_ACCOUNTS: list = [
    "매출액",
    "영업이익",
    "당기순이익",
    "자산총계",
    "부채총계",
    "자본총계",
    # 현금흐름표 — DART account_nm 표기 두 가지 모두 포함
    "영업활동현금흐름",
    "영업활동으로인한현금흐름",
]


def _get_dart_api_key() -> str:
    """DART_API_KEY를 .env에서 로드합니다. 미설정 시 ValueError 발생."""
    key = os.getenv("DART_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "DART_API_KEY가 .env에 설정되지 않았습니다. "
            "https://opendart.fss.or.kr/ 에서 무료 발급 후 설정하세요."
        )
    return key


def _load_corp_code_map() -> dict:
    """
    stock_code(6자리) → corp_code(8자리) 매핑 딕셔너리를 반환합니다.

    OpenDART corpCode.xml(ZIP)을 다운로드해 파싱하고,
    DART_CORP_CODE_CACHE 경로에 JSON으로 캐싱합니다.
    캐시가 TTL 이내이면 파일에서 로드해 재사용합니다.

    반환값:
        {"005930": "00126380", "000660": "00164779", ...}
        실패 시 빈 딕셔너리 반환 (파이프라인 중단 없음).
    """
    # ── 캐시 히트 확인 ────────────────────────────────────────────────────
    if DART_CORP_CODE_CACHE.exists():
        age = datetime.now().timestamp() - DART_CORP_CODE_CACHE.stat().st_mtime
        if age < DART_CORP_CODE_CACHE_TTL:
            try:
                with open(DART_CORP_CODE_CACHE, encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"[DART] corp_code 캐시 로드: {len(data)}건 (갱신일 기준 {int(age/3600)}h 경과)")
                return data
            except (json.JSONDecodeError, OSError):
                pass  # 캐시 손상 시 재다운로드

    # ── corpCode.xml 다운로드 ─────────────────────────────────────────────
    try:
        key = _get_dart_api_key()
    except ValueError as e:
        logger.warning(f"[DART] corp_code 맵 로드 실패: {e}")
        return {}

    url = f"{DART_API_BASE}/corpCode.xml"
    try:
        resp = requests.get(url, params={"crtfc_key": key}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"[DART] corpCode.xml 다운로드 실패: {e}")
        return {}

    # ── ZIP → XML 파싱 ────────────────────────────────────────────────────
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            xml_name = next(n for n in zf.namelist() if n.upper().endswith(".XML"))
            xml_bytes = zf.read(xml_name)
    except (zipfile.BadZipFile, StopIteration) as e:
        logger.warning(f"[DART] corpCode.xml ZIP 파싱 실패: {e}")
        return {}

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        logger.warning(f"[DART] corpCode.xml XML 파싱 실패: {e}")
        return {}

    # ── stock_code → corp_code 매핑 구축 ─────────────────────────────────
    corp_map: dict = {}
    for item in root.findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        corp_code  = (item.findtext("corp_code")  or "").strip()
        if stock_code and corp_code:
            corp_map[stock_code] = corp_code

    # ── 캐시 저장 ─────────────────────────────────────────────────────────
    try:
        with open(DART_CORP_CODE_CACHE, "w", encoding="utf-8") as f:
            json.dump(corp_map, f, ensure_ascii=False)
        logger.info(f"[DART] corp_code 캐시 저장 완료: {len(corp_map)}건 → {DART_CORP_CODE_CACHE.name}")
    except OSError as e:
        logger.warning(f"[DART] corp_code 캐시 저장 실패: {e}")

    return corp_map


def _dart_get(endpoint: str, params: dict, label: str = "") -> Optional[dict]:
    """
    OpenDART API 공통 GET 요청 헬퍼.
    - API 키 미설정 → None 반환 (파이프라인 계속 진행)
    - 네트워크 오류 또는 API 오류 → None 반환 (경고 로그)
    - status != "000" → None 반환
    """
    try:
        key = _get_dart_api_key()
    except ValueError as e:
        logger.warning(f"[DART{label}] {e}")
        return None

    try:
        params = {**params, "crtfc_key": key}
        url = f"{DART_API_BASE}/{endpoint}"
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "")
        if status != "000":
            msg = data.get("message", "")
            logger.warning(f"[DART{label}] API 오류 status={status} message={msg}")
            return None
        return data
    except requests.RequestException as e:
        logger.warning(f"[DART{label}] 요청 실패: {e}")
        return None


def run_dart_disclosure_scan(days: int = 14) -> list:
    """
    Step 1C — 심층분석용 전체 시장 주요사항보고서 스캔 (넓게).

    최근 {days}일 이내 전체 시장 대상 주요사항보고서(B001)를 수집하고,
    DART_DISCLOSURE_EVENT_MAP 키워드로 이벤트 타입을 자동 분류합니다.

    DART_API_KEY 미설정 시 빈 리스트를 반환하고 파이프라인은 계속 진행합니다.

    반환값:
        [
            {
                "corp_name":  str,   # 회사명
                "stock_code": str,   # 종목코드 6자리
                "report_nm":  str,   # 보고서명
                "rcept_dt":   str,   # 접수일 YYYYMMDD
                "event_type": str,   # 분류된 이벤트 타입 (예: "수주계약")
                "rcept_no":   str,   # 접수번호 (원문 조회 예비용)
                "source":     str,   # "DART 주요사항보고서 (회사명)"
                "date":       str,   # "YYYY-MM-DD" — facts.date 필드용
            },
            ...
        ]
    """
    end_dt   = datetime.now()
    start_dt = end_dt - timedelta(days=days)

    params = {
        "bgn_de":           start_dt.strftime("%Y%m%d"),
        "end_de":           end_dt.strftime("%Y%m%d"),
        "pblntf_ty":        "B",       # 주요사항보고서 대분류
        "pblntf_detail_ty": "B001",    # 주요사항보고서 세부
        "page_count":       "100",
    }

    data = _dart_get("list.json", params, label="/list B001")
    if data is None:
        return []

    items   = data.get("list", [])
    results = []

    for item in items:
        report_nm = item.get("report_nm", "")
        corp_name = item.get("corp_name", "")
        rcept_dt  = item.get("rcept_dt", "")

        # 날짜 형식 변환 (YYYYMMDD → YYYY-MM-DD)
        date_str = (
            f"{rcept_dt[:4]}-{rcept_dt[4:6]}-{rcept_dt[6:]}"
            if len(rcept_dt) == 8 else rcept_dt
        )

        # 이벤트 타입 분류 (첫 번째 매칭 키워드 사용)
        event_type = "기타"
        for keyword, etype in DART_DISCLOSURE_EVENT_MAP.items():
            if keyword in report_nm:
                event_type = etype
                break

        results.append({
            "corp_name":  corp_name,
            "stock_code": item.get("stock_code", ""),
            "report_nm":  report_nm,
            "rcept_dt":   rcept_dt,
            "event_type": event_type,
            "rcept_no":   item.get("rcept_no", ""),
            "source":     f"DART 주요사항보고서 ({corp_name})",
            "date":       date_str,
        })

    logger.info(f"[DART] 주요사항보고서 스캔 완료: {len(results)}건 (최근 {days}일)")

    # 이벤트 타입별 요약 로그
    by_type: dict = {}
    for r in results:
        by_type[r["event_type"]] = by_type.get(r["event_type"], 0) + 1
    for etype, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        logger.info(f"  [{etype}] {cnt}건")

    return results


def _stock_code_to_corp_code(stock_code: str) -> Optional[str]:
    """
    종목코드(6자리) → DART 고유번호(8자리) 변환.
    corpCode.xml 캐시(_load_corp_code_map)를 사용합니다.
    """
    corp_map = _load_corp_code_map()
    return corp_map.get(stock_code) or None


def run_dart_financials(stock_codes: list, bsns_year: Optional[str] = None) -> dict:
    """
    캐시의 픽 종목 재무 수치 조회 (좁게 — 픽 확정 종목만).

    연결재무제표(CFS) 우선, 없으면 개별재무제표(OFS)로 fallback.
    매출액·영업이익·당기순이익을 당기/전기 비교 형태로 반환.
    부채비율은 (부채총계 / 자본총계 × 100) 계산값으로 포함.

    Args:
        stock_codes: 6자리 종목코드 리스트 (예: ["005930", "000660"])
                     KR 종목만 전달하세요. 미국 주식은 조회하지 않습니다.
        bsns_year:   사업연도 4자리 (None이면 전년도 자동 사용)

    반환값:
        {
            "005930": {
                "corp_name": "삼성전자",
                "bsns_year": "2024",
                "fs_div":    "CFS",          # 연결/개별 구분
                "accounts": {
                    "매출액":     {"thstrm": 300151643, "frmtrm": 258935494, "unit": "백만원"},
                    "영업이익":   {"thstrm":  32726530, "frmtrm":   6566976, "unit": "백만원"},
                    "당기순이익": {"thstrm":  34459883, "frmtrm":  15487100, "unit": "백만원"},
                    "부채비율":   {"thstrm": 42.1,      "frmtrm": 38.7,      "unit": "%"},
                }
            },
            ...
        }
    """
    # auto_mode: bsns_year 미지정 → 전년도 시도 후 2년 전으로 fallback
    auto_mode = bsns_year is None
    if auto_mode:
        cur = datetime.now().year
        candidate_years = [str(cur - 1), str(cur - 2)]
    else:
        candidate_years = [bsns_year]

    result: dict = {}

    for stock_code in stock_codes:
        corp_code = _stock_code_to_corp_code(stock_code)
        if not corp_code:
            logger.warning(f"[DART] {stock_code} → corp_code 조회 실패, 재무 수집 스킵")
            continue

        # CFS(연결) 우선, 없으면 OFS(개별) — 연도 fallback 포함
        fin_data  = None
        used_div  = None
        used_year = None
        for year in candidate_years:
            for fs_div in ("CFS", "OFS"):
                params = {
                    "corp_code":  corp_code,
                    "bsns_year":  year,
                    "reprt_code": "11011",   # 사업보고서
                    "fs_div":     fs_div,
                }
                fin_data = _dart_get("fnlttSinglAcnt.json", params,
                                     label=f"/fnltt {stock_code} {fs_div}")
                if fin_data and fin_data.get("list"):
                    used_div  = fs_div
                    used_year = year
                    if auto_mode and year != candidate_years[0]:
                        logger.info(
                            f"[DART] {stock_code} fallback 적용 "
                            f"({candidate_years[0]} 미공시 → {year})"
                        )
                    logger.info(f"[DART] {stock_code} 재무 조회 성공 ({fs_div}, {year})")
                    break
            if fin_data and fin_data.get("list"):
                break

        if not fin_data or not fin_data.get("list"):
            tried = ", ".join(candidate_years)
            logger.warning(f"[DART] {stock_code} 재무 데이터 없음 (시도 연도: {tried})")
            continue

        # 수치 파싱 헬퍼
        def _parse_amount(val: str) -> Optional[int]:
            try:
                return int(str(val).replace(",", "").replace(" ", ""))
            except (ValueError, TypeError, AttributeError):
                return None

        raw: dict = {}   # 부채비율 계산용 원시 데이터
        accounts: dict = {}

        for item in fin_data["list"]:
            acct_nm = item.get("account_nm", "")
            if acct_nm not in DART_TARGET_ACCOUNTS:
                continue
            thstrm = _parse_amount(item.get("thstrm_amount", ""))
            frmtrm = _parse_amount(item.get("frmtrm_amount", ""))
            raw[acct_nm] = {"thstrm": thstrm, "frmtrm": frmtrm}

            _INCOME_ACCOUNTS = ("매출액", "영업이익", "당기순이익")
            _CF_ACCOUNTS = ("영업활동현금흐름", "영업활동으로인한현금흐름")
            if acct_nm in _INCOME_ACCOUNTS:
                accounts[acct_nm] = {
                    "thstrm": thstrm,
                    "frmtrm": frmtrm,
                    "unit":   "백만원",
                }
            elif acct_nm in _CF_ACCOUNTS:
                # 두 표기 모두 "영업활동현금흐름"으로 통일
                accounts["영업활동현금흐름"] = {
                    "thstrm": thstrm,
                    "frmtrm": frmtrm,
                    "unit":   "백만원",
                }

        # 부채비율 계산 (부채총계 / 자본총계 × 100)
        debt   = raw.get("부채총계", {})
        equity = raw.get("자본총계", {})
        if debt.get("thstrm") and equity.get("thstrm") and equity["thstrm"] != 0:
            frmtrm_ratio = None
            if (debt.get("frmtrm") and equity.get("frmtrm") and equity["frmtrm"] != 0):
                frmtrm_ratio = round(debt["frmtrm"] / equity["frmtrm"] * 100, 1)
            accounts["부채비율"] = {
                "thstrm": round(debt["thstrm"] / equity["thstrm"] * 100, 1),
                "frmtrm": frmtrm_ratio,
                "unit":   "%",
            }

        corp_name_val = (fin_data["list"][0].get("corp_name", stock_code)
                         if fin_data["list"] else stock_code)
        did_fallback = auto_mode and used_year != candidate_years[0]
        result[stock_code] = {
            "corp_name":          corp_name_val,
            "bsns_year":          used_year,          # 하위 호환 유지
            "resolved_bsns_year": used_year,
            "used_fallback":      did_fallback,
            "fs_div":             used_div,
            "accounts":           accounts,
        }

    logger.info(f"[DART] 재무 수치 조회 완료: {len(result)}개 종목")
    return result


def run_dart_company_info(stock_codes: list) -> dict:
    """
    캐시의 픽 종목 기본정보 조회 (좁게 — 픽 확정 종목만).

    Args:
        stock_codes: 6자리 종목코드 리스트

    반환값:
        {
            "005930": {
                "corp_name": "삼성전자",
                "ind_tp":    "전자부품, 컴퓨터, 영상, 음향 및 통신장비 제조업",
                "acc_mt":    "12",     # 결산월
                "corp_code": "00126380",
            },
            ...
        }
    """
    corp_map = _load_corp_code_map()
    result: dict = {}
    for stock_code in stock_codes:
        corp_code = corp_map.get(stock_code)
        if not corp_code:
            logger.warning(f"[DART] {stock_code} → corp_code 매핑 없음, 기업정보 스킵")
            continue
        data = _dart_get("company.json", {"corp_code": corp_code},
                         label=f"/company_info {stock_code}")
        if data is None:
            continue
        result[stock_code] = {
            "corp_name": data.get("corp_name", ""),
            "ind_tp":    data.get("ind_tp",    ""),
            "acc_mt":    data.get("acc_mt",    ""),
            "corp_code": corp_code,
        }

    logger.info(f"[DART] 기본정보 조회 완료: {len(result)}개 종목")
    return result


def format_dart_for_prompt(
    disclosures: list,
    financials: Optional[dict] = None,
    company_info: Optional[dict] = None,
) -> str:
    """
    DART 데이터를 Gemini/GPT 프롬프트 삽입용 텍스트로 변환합니다.

    Args:
        disclosures:  run_dart_disclosure_scan() 반환값
        financials:   run_dart_financials() 반환값 (None 가능)
        company_info: run_dart_company_info() 반환값 (None 가능)

    반환값:
        프롬프트에 직접 삽입 가능한 텍스트 문자열.
        데이터가 없으면 빈 문자열 반환.
    """
    lines: list = []

    # ── 공시 이벤트 (심층분석용) ────────────────────────────────────────────
    if disclosures:
        lines.append("[DART 주요사항보고서 — 최근 14일 공시 이벤트]")
        lines.append("출처: 금융감독원 전자공시시스템(DART), 공식 공시 데이터")
        # 이벤트 타입 "기타" 후순위, 접수일 최신순 정렬
        sorted_disc = sorted(
            disclosures,
            key=lambda x: (x["event_type"] == "기타", "-" + x["rcept_dt"])
        )
        for d in sorted_disc[:20]:   # 최대 20건
            lines.append(
                f"- [{d['event_type']}] {d['corp_name']} | {d['report_nm']} | {d['date']}"
            )

    # ── 재무 수치 (픽 종목 전용) ─────────────────────────────────────────────
    if financials:
        lines.append("\n[DART 재무 수치 — 픽 종목 최근 사업연도 / 출처: DART 사업보고서]")
        for stock_code, info in financials.items():
            corp_name = info.get("corp_name", stock_code)
            bsns_year = info.get("bsns_year", "")
            fs_div    = info.get("fs_div", "")
            year_str      = info.get("resolved_bsns_year") or bsns_year
            fallback_note = " (fallback 적용)" if info.get("used_fallback") else ""
            lines.append(f"\n▶ {corp_name} ({stock_code}) — DART 재무 기준연도: {year_str}{fallback_note} / {fs_div}")
            for acct_nm, values in info.get("accounts", {}).items():
                thstrm = values.get("thstrm")
                frmtrm = values.get("frmtrm")
                unit   = values.get("unit", "")
                if thstrm is None:
                    continue
                # 포맷팅: 정수면 천 단위 구분, 실수(부채비율)면 소수점 1자리
                def _fmt(v):
                    if v is None:
                        return "N/A"
                    return f"{v:.1f}" if isinstance(v, float) else f"{v:,}"

                yoy_str = ""
                if frmtrm and frmtrm != 0:
                    change = (thstrm - frmtrm) / abs(frmtrm) * 100
                    yoy_str = f" (YoY {change:+.1f}%)"
                lines.append(
                    f"  · {acct_nm}: {_fmt(thstrm)} {unit}{yoy_str}"
                    f" | 전기: {_fmt(frmtrm)} {unit}"
                )

    # ── 기업 기본정보 (픽 종목 전용) ─────────────────────────────────────────
    if company_info:
        lines.append("\n[DART 기업 기본정보]")
        for stock_code, info in company_info.items():
            lines.append(
                f"- {info.get('corp_name','')} ({stock_code}): "
                f"업종 = {info.get('ind_tp','미상')} | "
                f"결산월 = {info.get('acc_mt','미상')}월"
            )

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 14. 결과 출력 헬퍼 (디버깅용)
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
