"""
macromalt 자동화 시스템 - 워드프레스 발행 모듈
=====================================================
generator.py가 생성한 마크다운 콘텐츠를
WordPress REST API를 통해 임시저장(Draft)으로 업로드합니다.
"""

import logging
import os

import requests
from dotenv import load_dotenv

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
def publish_draft(title: str, content: str, category_ids: list = None) -> dict:
    """
    마크다운 콘텐츠를 WordPress에 임시저장(Draft)으로 업로드합니다.

    Args:
        title:        포스팅 제목
        content:      마크다운 본문 전체
        category_ids: WordPress 카테고리 ID 목록 (None이면 .env의 WP_CATEGORY_DEFAULT 또는 [2] 사용)

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

    payload = {
        "title": title,
        "content": content,
        "status": "draft",       # 임시저장 (자동 발행하려면 "publish"로 변경)
        "format": "standard",
        "comment_status": "open",
        "categories": category_ids,
    }

    logger.info(f"WordPress 업로드 시작 | 제목: '{title}'")

    response = requests.post(
        config["api_url"],
        json=payload,
        headers=headers,
        auth=(config["username"], config["password"]),  # Basic Auth (앱 비밀번호)
        timeout=30,
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
