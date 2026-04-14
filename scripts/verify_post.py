#!/usr/bin/env python3
"""
macromalt 발행 게시글 후처리 검증 스크립트
==========================================
WordPress REST API로 실제 발행된 게시글을 조회하고
발행 후 상태 이상을 감지한다.

사용법:
  # 특정 post ID 검증
  python scripts/verify_post.py --post-id 123 456

  # logs/publish_result.jsonl에서 자동으로 post ID 추출
  python scripts/verify_post.py

  # 최근 N건만 검증 (기본 10)
  python scripts/verify_post.py --limit 5

출력:
  stdout  — 검증 결과 요약
  exit code 0 = 전체 PASS, 1 = 1건 이상 FAIL
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
RESULT_PATH = PROJECT_ROOT / "logs" / "publish_result.jsonl"

load_dotenv(PROJECT_ROOT / ".env")

# ── 검증 기준 상수 ────────────────────────────────────────────
_MIN_CONTENT_LEN = 8_000
_MARKDOWN_PATTERN = re.compile(r"(?:^|\s)(#{1,3} |```|\*\*|\*[^*])")
_INVEST_RECOMMEND_PATTERN = re.compile(
    r"매수|유망|담아야|사야|투자 추천|강력 추천"
)


# ── WordPress 연결 ────────────────────────────────────────────

def _get_wp_base_url() -> str:
    site_url = os.getenv("WORDPRESS_SITE_URL", "").strip().rstrip("/")
    if not site_url:
        raise ValueError("WORDPRESS_SITE_URL 환경변수가 설정되지 않았습니다.")
    if not site_url.startswith("http"):
        site_url = f"http://{site_url}"
    return site_url


def _get_wp_auth() -> tuple[str, str]:
    username = os.getenv("WORDPRESS_USERNAME", "").strip()
    password = os.getenv("WORDPRESS_PASSWORD", "").strip()
    if not username or not password:
        raise ValueError("WORDPRESS_USERNAME 또는 WORDPRESS_PASSWORD 환경변수 누락")
    return username, password


def fetch_post(post_id: int) -> dict:
    """WordPress REST API로 게시글 조회."""
    base_url = _get_wp_base_url()
    auth = _get_wp_auth()
    resp = requests.get(
        f"{base_url}/wp-json/wp/v2/posts/{post_id}",
        auth=auth,
        timeout=15,
    )
    if resp.status_code == 404:
        raise LookupError(f"post_id={post_id} 를 찾을 수 없습니다 (404).")
    resp.raise_for_status()
    return resp.json()


# ── 검증 항목 ─────────────────────────────────────────────────

def _check_status(post: dict) -> tuple[bool, str]:
    """발행 상태가 publish 또는 future인지 확인."""
    status = post.get("status", "")
    ok = status in ("publish", "future")
    return ok, f"status={status!r}"


def _check_title(post: dict) -> tuple[bool, str]:
    """제목이 비어있지 않은지 확인."""
    rendered = post.get("title", {}).get("rendered", "").strip()
    ok = bool(rendered)
    return ok, f"title={'있음' if ok else '없음(공백)'}"


def _check_content_length(post: dict) -> tuple[bool, str]:
    """본문 길이 최소 기준 확인."""
    rendered = post.get("content", {}).get("rendered", "")
    length = len(rendered)
    ok = length >= _MIN_CONTENT_LEN
    return ok, f"content_len={length} (최소 {_MIN_CONTENT_LEN})"


def _check_no_markdown(post: dict) -> tuple[bool, str]:
    """본문에 마크다운 기호가 남아있지 않은지 확인."""
    rendered = post.get("content", {}).get("rendered", "")
    match = _MARKDOWN_PATTERN.search(rendered)
    ok = match is None
    return ok, f"마크다운={'없음' if ok else f'발견({match.group().strip()!r})'}"


def _check_no_duplicate_h1(post: dict) -> tuple[bool, str]:
    """본문에 <h1> 태그가 남아있지 않은지 확인 (발행 전 제거 대상)."""
    rendered = post.get("content", {}).get("rendered", "")
    count = len(re.findall(r"<h1[^>]*>", rendered, re.IGNORECASE))
    ok = count == 0
    return ok, f"h1_count={count}"


def _check_categories(post: dict) -> tuple[bool, str]:
    """카테고리가 1개 이상 설정됐는지 확인."""
    categories = post.get("categories", [])
    ok = len(categories) >= 1
    return ok, f"categories={categories}"


def _check_slug(post: dict) -> tuple[bool, str]:
    """슬러그가 숫자만으로 이뤄지지 않고 의미 있는 값인지 확인."""
    slug = post.get("slug", "").strip()
    ok = bool(slug) and not slug.isdigit()
    return ok, f"slug={slug!r}"


def _check_no_invest_recommend(post: dict) -> tuple[bool, str]:
    """투자 권유 금지어 포함 여부 확인 (기준 5)."""
    rendered = post.get("content", {}).get("rendered", "")
    match = _INVEST_RECOMMEND_PATTERN.search(rendered)
    ok = match is None
    return ok, f"투자권유={'없음' if ok else f'발견({match.group()!r})'}"


def _check_risk_section(post: dict) -> tuple[bool, str]:
    """리스크 섹션 존재 여부 확인."""
    rendered = post.get("content", {}).get("rendered", "")
    ok = "리스크" in rendered or "⚠" in rendered
    return ok, f"리스크섹션={'있음' if ok else '없음'}"


def _check_time_horizon(post: dict) -> tuple[bool, str]:
    """투자 시계(단기/중기) 기재 여부 확인."""
    rendered = post.get("content", {}).get("rendered", "")
    has_short = "단기" in rendered
    has_mid = "중기" in rendered
    ok = has_short and has_mid
    parts = []
    if not has_short:
        parts.append("단기 누락")
    if not has_mid:
        parts.append("중기 누락")
    return ok, "시계=OK" if ok else f"시계={'|'.join(parts)}"


_CHECKS = [
    ("status_ok",           _check_status),
    ("title_ok",            _check_title),
    ("content_length_ok",   _check_content_length),
    ("no_markdown",         _check_no_markdown),
    ("no_duplicate_h1",     _check_no_duplicate_h1),
    ("categories_ok",       _check_categories),
    ("slug_ok",             _check_slug),
    ("no_invest_recommend", _check_no_invest_recommend),
    ("risk_section_ok",     _check_risk_section),
    ("time_horizon_ok",     _check_time_horizon),
]


# ── 단일 게시글 검증 ──────────────────────────────────────────

def verify_post(post_id: int) -> dict:
    """
    post_id에 해당하는 게시글을 WordPress에서 조회해 검증한다.

    반환:
        {
            "post_id": int,
            "title":   str,
            "link":    str,
            "all_pass": bool,
            "checks":   {check_name: {"pass": bool, "detail": str}, ...},
            "verified_at": str,  # ISO 8601 UTC
        }
    """
    post = fetch_post(post_id)
    results = {}
    for name, fn in _CHECKS:
        passed, detail = fn(post)
        results[name] = {"pass": passed, "detail": detail}

    all_pass = all(v["pass"] for v in results.values())
    return {
        "post_id": post_id,
        "title": post.get("title", {}).get("rendered", ""),
        "link": post.get("link", ""),
        "all_pass": all_pass,
        "checks": results,
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


# ── publish_result.jsonl에서 post_id 추출 ─────────────────────

def _load_post_ids_from_jsonl(limit: int) -> list[int]:
    """publish_result.jsonl에 기록된 최근 게시글의 post_id 목록을 반환."""
    if not RESULT_PATH.exists():
        return []

    post_ids: list[int] = []
    seen: set[int] = set()
    lines = RESULT_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        pid = entry.get("post_id")
        if pid and isinstance(pid, int) and pid not in seen:
            post_ids.append(pid)
            seen.add(pid)
            if len(post_ids) >= limit:
                break

    return post_ids


# ── 출력 ──────────────────────────────────────────────────────

def _print_result(result: dict) -> None:
    status_icon = "PASS" if result["all_pass"] else "FAIL"
    print(f"\n[{status_icon}] post_id={result['post_id']}  {result['title']}")
    print(f"  link : {result['link']}")
    for name, info in result["checks"].items():
        icon = "✔" if info["pass"] else "✘"
        print(f"  {icon} {name:<24} {info['detail']}")


# ── 진입점 ────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="발행 게시글 후처리 검증")
    parser.add_argument(
        "--post-id", type=int, nargs="+", metavar="ID",
        help="검증할 WordPress post ID (복수 지정 가능)",
    )
    parser.add_argument(
        "--limit", type=int, default=10,
        help="publish_result.jsonl에서 읽을 최근 게시글 수 (기본 10)",
    )
    args = parser.parse_args()

    if args.post_id:
        post_ids = args.post_id
    else:
        post_ids = _load_post_ids_from_jsonl(args.limit)
        if not post_ids:
            print("[ERROR] 검증할 post_id가 없습니다.")
            print("       --post-id 옵션으로 직접 지정하거나,")
            print(f"       {RESULT_PATH} 파일이 존재해야 합니다.")
            return 1

    print(f"[verify_post.py] 검증 대상: {len(post_ids)}건  {post_ids}")

    any_fail = False
    for pid in post_ids:
        try:
            result = verify_post(pid)
        except LookupError as e:
            print(f"\n[SKIP] post_id={pid}: {e}")
            continue
        except Exception as e:
            print(f"\n[ERROR] post_id={pid}: {e}")
            any_fail = True
            continue

        _print_result(result)
        if not result["all_pass"]:
            any_fail = True

    print()
    if any_fail:
        print("[verify_post.py] 결과: FAIL (1건 이상 검증 미통과)")
        return 1

    print("[verify_post.py] 결과: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
