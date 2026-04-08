"""
macromalt 자동화 시스템 - 워드프레스 발행 모듈
=====================================================
generator.py가 생성한 마크다운 콘텐츠를
WordPress REST API를 통해 임시저장(Draft)으로 업로드합니다.
"""

import json as _json
import logging
import os
import os as _os
import re

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logger = logging.getLogger("macromalt")


# ──────────────────────────────────────────────
# 1. WordPress 연결 설정 로드
# ──────────────────────────────────────────────
def _get_wp_config() -> dict:
    """
    .env에서 WordPress 접속 정보를 읽어 반환합니다.
    필수 값이 없으면 ValueError를 발생시킵니다.
    """
    site_url = os.getenv("WORDPRESS_SITE_URL", "").strip().rstrip("/")
    username = os.getenv("WORDPRESS_USERNAME", "").strip()
    password = os.getenv("WORDPRESS_PASSWORD", "").strip()

    missing = [k for k, v in {
        "WORDPRESS_SITE_URL": site_url,
        "WORDPRESS_USERNAME": username,
        "WORDPRESS_PASSWORD": password,
    }.items() if not v]

    if missing:
        raise ValueError(f"다음 환경 변수가 .env에 설정되지 않았습니다: {', '.join(missing)}")

    # URL 스킴 보정 (macromalt.com → http://macromalt.com)
    # 주의: macOS LibreSSL이 일부 서버의 TLS 설정과 충돌할 경우 http:// 사용
    if not site_url.startswith("http"):
        site_url = f"http://{site_url}"

    return {
        "api_url": f"{site_url}/wp-json/wp/v2/posts",
        "username": username,
        "password": password,
    }


# ──────────────────────────────────────────────
# 2. 마크다운 → WordPress 발행 함수
# ──────────────────────────────────────────────

_CATEGORY_CACHE_PATH = _os.path.join(_os.path.dirname(__file__), "category_cache.json")


def _load_category_cache() -> dict:
    """로컬 카테고리 캐시 로드."""
    if _os.path.exists(_CATEGORY_CACHE_PATH):
        try:
            with open(_CATEGORY_CACHE_PATH, "r", encoding="utf-8") as f:
                return _json.load(f)
        except Exception:
            pass
    return {}


def _save_category_cache(cache: dict) -> None:
    with open(_CATEGORY_CACHE_PATH, "w", encoding="utf-8") as f:
        _json.dump(cache, f, ensure_ascii=False, indent=2)


def get_or_create_wp_category(theme_name: str, parent_id: int) -> int:
    """[Phase 22] 테마명으로 WordPress 카테고리 ID를 반환. 없으면 생성.

    Args:
        theme_name: 테마명 (카테고리 이름으로 사용)
        parent_id:  부모 카테고리 ID (ANALYSIS=2, PICKS=3)

    Returns:
        WordPress 카테고리 ID
    """
    import requests as _req
    cache_key = f"{parent_id}:{theme_name}"

    # 캐시 확인
    cache = _load_category_cache()
    if cache_key in cache:
        logger.debug(f"[Phase 22] 카테고리 캐시 히트: '{theme_name}' → ID {cache[cache_key]}")
        return cache[cache_key]

    config = _get_wp_config()
    # api_url은 .../wp-json/wp/v2/posts 형태 — base URL 추출
    base_url = config["api_url"].replace("/wp-json/wp/v2/posts", "")
    headers = {"Content-Type": "application/json"}

    # 기존 카테고리 검색
    try:
        resp = _req.get(
            f"{base_url}/wp-json/wp/v2/categories",
            params={"search": theme_name, "parent": parent_id, "per_page": 5},
            auth=(config["username"], config["password"]),
            timeout=10,
        )
        if resp.status_code == 200:
            for cat in resp.json():
                if cat.get("name", "").strip() == theme_name.strip():
                    cat_id = cat["id"]
                    cache[cache_key] = cat_id
                    _save_category_cache(cache)
                    logger.info(f"[Phase 22] 기존 카테고리 발견: '{theme_name}' → ID {cat_id}")
                    return cat_id
    except Exception as e:
        logger.warning(f"[Phase 22] 카테고리 검색 실패: {e}")

    # 새 카테고리 생성
    try:
        resp = _req.post(
            f"{base_url}/wp-json/wp/v2/categories",
            headers=headers,
            json={"name": theme_name, "parent": parent_id},
            auth=(config["username"], config["password"]),
            timeout=10,
        )
        if resp.status_code in (200, 201):
            cat_id = resp.json()["id"]
            cache[cache_key] = cat_id
            _save_category_cache(cache)
            logger.info(f"[Phase 22] 카테고리 신규 생성: '{theme_name}' → ID {cat_id}")
            return cat_id
        else:
            logger.warning(f"[Phase 22] 카테고리 생성 실패 ({resp.status_code}) — 부모 ID {parent_id} 사용")
    except Exception as e:
        logger.warning(f"[Phase 22] 카테고리 생성 예외: {e} — 부모 ID {parent_id} 사용")

    return parent_id  # fallback: 부모 카테고리 사용


def _strip_leading_h1(content: str) -> str:
    """
    WordPress 발행 전 content에서 맨 앞 <h1> 태그를 제거합니다.
    WordPress가 title 필드를 별도로 렌더링하므로 content에 h1이 있으면
    제목이 페이지에 두 번 출력됩니다. 발행 단계에서만 제거합니다.

    Phase 19 BUG-POST2-TITLE-DUP-20260320 수정:
    _P14_ANALYTICAL_SPINE_ENFORCEMENT 프롬프트로 인해 GPT가 <h1> 앞에
    <!-- SPINE: ... --> HTML 주석을 삽입한다. 기존 regex(^\s*<h1...)는 이
    주석 선행 시 매칭 실패 → <h1> 미제거 → 제목 2회 출력 버그 발생.
    regex를 확장해 선행 HTML 주석 0개 이상을 건너뛰고 <h1>을 탐지한다.
    """
    return re.sub(
        r"^\s*(<!--.*?-->\s*)*<h1[^>]*>.*?</h1>\s*",
        "",
        content,
        count=1,
        flags=re.DOTALL,
    )


def _quality_gate(content: str) -> list[str]:
    """발행 전 콘텐츠 구조 검사. 문제 항목 목록을 반환한다."""
    issues = []
    if len(content) < 8000:
        issues.append(f"본문 길이 미달: {len(content)}자 (최소 8,000자)")
    if "⚠" not in content and "리스크" not in content:
        issues.append("리스크 섹션 누락")
    if "단기(1~3개월)" not in content and "단기" not in content:
        issues.append("투자 시계 단기 미기재")
    if "중기(3~12개월)" not in content and "중기" not in content:
        issues.append("투자 시계 중기 미기재")
    return issues


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _wp_post(api_url: str, payload: dict, headers: dict, auth: tuple) -> requests.Response:
    """WordPress REST API POST 요청 (tenacity 재시도 래퍼)."""
    return requests.post(api_url, json=payload, headers=headers, auth=auth, timeout=30)


def publish_draft(
    title: str,
    content: str,
    category_ids: list = None,
    featured_media_id: int = None,
    seo_title: str = "",
    scheduled_at: str = "",
) -> dict:
    """
    마크다운 콘텐츠를 WordPress에 임시저장(Draft)으로 업로드합니다.

    Args:
        title:             포스팅 제목
        content:           마크다운 본문 전체
        category_ids:      WordPress 카테고리 ID 목록 (None이면 .env의 WP_CATEGORY_DEFAULT 또는 [2] 사용)
        featured_media_id: WordPress 미디어 ID (None이면 대표 이미지 미설정)
        seo_title:         [Phase 21] SEO 최적화 슬러그 소스 (비어있으면 slug 미설정)
        scheduled_at:      [Phase 22] 예약 발행 시각 ISO 8601 KST (예: "2026-04-01T07:00:00"). 비어있으면 즉시 발행.

    반환값:
        {
            "post_id": int,   # 생성된 포스팅 ID
            "post_url": str,  # 편집 링크
            "status": str,    # "draft"
        }
    """
    import os as _os
    config = _get_wp_config()

    headers = {
        "Content-Type": "application/json",
    }

    # 카테고리 ID 결정 우선순위:
    # 1. 호출 시 직접 전달한 category_ids
    # 2. .env의 WP_CATEGORY_DEFAULT (쉼표 구분 숫자)
    # 3. 하드코딩 기본값 [2]
    if category_ids is None:
        env_val = _os.getenv("WP_CATEGORY_DEFAULT", "").strip()
        if env_val:
            try:
                category_ids = [int(x.strip()) for x in env_val.split(",") if x.strip()]
            except ValueError:
                category_ids = [2]
        else:
            category_ids = [2]

    # 발행 전 content에서 중복 h1 제거 (WordPress가 title을 별도 렌더링하므로)
    content = _strip_leading_h1(content)

    _status = "future" if scheduled_at else "publish"
    payload = {
        "title": title,
        "content": content,
        "status": _status,
        "format": "standard",
        "comment_status": "open",
        "categories": category_ids,
    }
    if scheduled_at:
        payload["date"] = scheduled_at
        logger.info(f"   예약 발행 설정: {scheduled_at}")

    if featured_media_id:
        payload["featured_media"] = featured_media_id
        logger.info(f"   대표 이미지 설정: media_id={featured_media_id}")

    # [Phase 21] SEO slug: GPT가 생성한 SEO_TITLE을 slug로 변환
    if seo_title:
        import unicodedata as _ud, re as _re
        _slug = _ud.normalize("NFC", seo_title.strip())
        _slug = _slug.replace("—", "-").replace("–", "-")  # em/en dash → hyphen
        _slug = _re.sub(r"[^\w\s-]", "", _slug)            # 특수문자 제거 (한글·영문·숫자·하이픈 유지)
        _slug = _re.sub(r"[\s_]+", "-", _slug)             # 공백/언더스코어 → 하이픈
        _slug = _re.sub(r"-{2,}", "-", _slug).strip("-").lower()
        if _slug:
            payload["slug"] = _slug
            logger.info(f"   SEO slug 설정: '{_slug}'")

    # 발행 전 콘텐츠 품질 게이트
    gate_issues = _quality_gate(content)
    if gate_issues:
        logger.warning(f"[품질 게이트] '{title}' 발행 경고: {gate_issues}")

    logger.info(f"WordPress 업로드 시작 | 제목: '{title}'")

    response = _wp_post(
        config["api_url"],
        payload,
        headers,
        (config["username"], config["password"]),
    )

    if response.status_code == 401:
        raise PermissionError(
            "WordPress 인증 실패. WORDPRESS_USERNAME / WORDPRESS_PASSWORD를 확인하세요. "
            "앱 비밀번호(Application Password)를 사용해야 합니다."
        )

    response.raise_for_status()

    data = response.json()
    post_id = data.get("id")
    edit_link = data.get("link", "")

    # [Phase 19] WordPress 응답에 post_id가 없는 경우 명시적 오류
    if post_id is None:
        raise RuntimeError(
            f"[Phase 19] WordPress 응답에 post_id(id) 필드 없음. "
            f"HTTP {response.status_code} | 응답 키: {list(data.keys())}"
        )

    logger.info(f"WordPress 업로드 성공 | Post ID: {post_id} | URL: {edit_link}")

    return {
        "post_id": post_id,
        "post_url": edit_link,
        "status": data.get("status", "draft"),
    }


# ──────────────────────────────────────────────
# 3. 직접 실행 진입점 (연결 테스트용)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler()],
    )

    test_title = "[테스트] 바텐더 캐시의 연결 확인 포스팅"
    test_content = "# 연결 테스트\n\n이 포스팅은 macromalt 자동화 시스템의 WordPress 연결 테스트용입니다."

    try:
        result = publish_draft(test_title, test_content)
        print(f"\n✅ 업로드 성공!")
        print(f"   Post ID : {result['post_id']}")
        print(f"   URL     : {result['post_url']}")
        print(f"   상태    : {result['status']}")
    except Exception as e:
        print(f"❌ 업로드 실패: {e}", file=sys.stderr)
        sys.exit(1)
