#!/usr/bin/env python3
"""
macromalt Phase 20 주간 운영 정교화 리포트 생성기
=================================================
GitHub Actions artifact에서 지난 7일간의
publish_result.jsonl 을 수집·집계하여
reports/REPORT_PHASE20_WEEKLY.md 를 생성한다.

사용법:
  python scripts/phase20_weekly_report.py

환경 변수 (GitHub Actions에서 자동 주입):
  GITHUB_TOKEN      — artifact 다운로드 권한
  GITHUB_REPOSITORY — "owner/repo" 형식

출력:
  reports/REPORT_PHASE20_WEEKLY.md
"""

import io
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("[ERROR] 'requests' 패키지가 필요합니다: pip install requests", file=sys.stderr)
    sys.exit(1)

# ── 경로 설정 ────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
REPORT_PATH  = PROJECT_ROOT / "reports" / "REPORT_PHASE20_WEEKLY.md"

# ── GitHub API 설정 ──────────────────────────────────────────
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_API_BASE   = "https://api.github.com"
ARTIFACT_NAME_PREFIX = "publish-log-"
LOOKBACK_DAYS = 7

# ── 분석 상수 ────────────────────────────────────────────────
GENERIC_OPENER_PATTERNS = [
    r"최근\s+시장은",
    r"글로벌\s+금융시장",
    r"경제\s+불확실성",
    r"시장의\s+변동성",
]
PICK_ANGLE_PATTERNS = [
    r"왜\s+지금\s+\S+인가",
    r"을\s+먼저\s+봐야\s+하는\s+이유",
]


# ═══════════════════════════════════════════════════════════
# 1. GitHub API 헬퍼
# ═══════════════════════════════════════════════════════════

def _gh_headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def _list_artifacts(repo: str, created_after: datetime) -> list[dict]:
    """지정 날짜 이후 생성된 publish-log 계열 artifact 목록 반환."""
    url = f"{GITHUB_API_BASE}/repos/{repo}/actions/artifacts"
    params = {"per_page": 100, "name": ""}  # name 필터는 API에서 prefix 미지원 → 전체 조회 후 필터
    artifacts = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, headers=_gh_headers(), params=params, timeout=30)
        if resp.status_code != 200:
            print(f"[WARN] artifact 목록 조회 실패: {resp.status_code} {resp.text[:200]}")
            break
        data = resp.json()
        items = data.get("artifacts", [])
        if not items:
            break
        for item in items:
            if not item["name"].startswith(ARTIFACT_NAME_PREFIX):
                continue
            created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            if created_at < created_after:
                continue
            if item.get("expired"):
                continue
            artifacts.append(item)
        if len(items) < 100:
            break
        page += 1
    return artifacts


def _download_jsonl(repo: str, artifact_id: int) -> list[dict]:
    """artifact zip에서 publish_result.jsonl 을 다운로드해 파싱."""
    url = f"{GITHUB_API_BASE}/repos/{repo}/actions/artifacts/{artifact_id}/zip"
    resp = requests.get(url, headers=_gh_headers(), timeout=60, allow_redirects=True)
    if resp.status_code != 200:
        print(f"[WARN] artifact {artifact_id} 다운로드 실패: {resp.status_code}")
        return []

    entries = []
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                if not name.endswith("publish_result.jsonl"):
                    continue
                with zf.open(name) as f:
                    for raw_line in f:
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if not line:
                            continue
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    except zipfile.BadZipFile:
        print(f"[WARN] artifact {artifact_id} — BadZipFile")

    return entries


# ═══════════════════════════════════════════════════════════
# 2. 로컬 fallback
# ═══════════════════════════════════════════════════════════

def _load_local_jsonl() -> list[dict]:
    """GitHub API 없이 로컬 logs/publish_result.jsonl 에서 로드 (로컬 실행 fallback)."""
    local = PROJECT_ROOT / "logs" / "publish_result.jsonl"
    if not local.exists():
        return []
    entries = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    for line in local.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        logged_at_str = e.get("logged_at", "")
        if logged_at_str:
            try:
                logged_at = datetime.fromisoformat(logged_at_str)
                if logged_at.tzinfo is None:
                    logged_at = logged_at.replace(tzinfo=timezone.utc)
                if logged_at < cutoff:
                    continue
            except ValueError:
                pass
        entries.append(e)
    return entries


# ═══════════════════════════════════════════════════════════
# 3. 데이터 집계
# ═══════════════════════════════════════════════════════════

def _analyze(entries: list[dict]) -> dict:
    total_publish = len(entries)
    post1_entries = [e for e in entries if e.get("post_type") == "post1"]
    post2_entries = [e for e in entries if e.get("post_type") == "post2"]
    go_count  = sum(1 for e in entries if e.get("final_status") == "GO")
    hold_count = total_publish - go_count

    run_ids = list({e["run_id"] for e in entries if "run_id" in e})
    total_runs = len(run_ids)

    public_urls = [e["public_url"] for e in entries if e.get("public_url")]

    # opener 분석 (post2 기준)
    opener_pass_count = sum(1 for e in post2_entries if e.get("opener_pass"))
    opener_fail_count = len(post2_entries) - opener_pass_count
    opener_regression = opener_fail_count > 0

    # criteria 분석
    c1_fail = sum(1 for e in entries if not e.get("criteria_1_pass"))
    c5_fail = sum(1 for e in entries if not e.get("criteria_5_pass"))
    source_fail = sum(1 for e in entries if not e.get("source_structure_pass"))

    # slot 분포
    slot_dist: dict[str, int] = {}
    for e in entries:
        s = e.get("slot", "unknown")
        slot_dist[s] = slot_dist.get(s, 0) + 1

    return {
        "total_runs":        total_runs,
        "total_publish":     total_publish,
        "post1_count":       len(post1_entries),
        "post2_count":       len(post2_entries),
        "go_count":          go_count,
        "hold_count":        hold_count,
        "public_url_count":  len(public_urls),
        "public_urls":       public_urls,
        "opener_pass_count": opener_pass_count,
        "opener_fail_count": opener_fail_count,
        "opener_regression": opener_regression,
        "c1_fail":           c1_fail,
        "c5_fail":           c5_fail,
        "source_fail":       source_fail,
        "slot_dist":         slot_dist,
    }


def _final_verdict(stats: dict) -> str:
    """HOLD / CONDITIONAL GO / GO 판정."""
    if stats["hold_count"] > 0:
        return "HOLD"
    if stats["opener_regression"]:
        return "CONDITIONAL GO"
    if stats["c1_fail"] > 0 or stats["c5_fail"] > 0 or stats["source_fail"] > 0:
        return "CONDITIONAL GO"
    if stats["total_publish"] == 0:
        return "CONDITIONAL GO"
    return "GO"


# ═══════════════════════════════════════════════════════════
# 4. 리포트 생성
# ═══════════════════════════════════════════════════════════

def _render_report(
    stats: dict,
    period_start: datetime,
    period_end: datetime,
    data_source: str,
) -> str:
    verdict = _final_verdict(stats)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []

    lines += [
        f"# REPORT_PHASE20_WEEKLY.md",
        f"",
        f"생성일시: {now_str}",
        f"데이터 소스: {data_source}",
        f"최종 판정: **{verdict}**",
        f"",
        f"---",
        f"",
        f"## 1. 분석 기간",
        f"",
        f"| 항목 | 값 |",
        f"|------|---|",
        f"| 시작 | {period_start.strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| 종료 | {period_end.strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| 기간 | {LOOKBACK_DAYS}일 |",
        f"",
        f"---",
        f"",
        f"## 2. 발행 실적 요약",
        f"",
        f"| 항목 | 수 |",
        f"|------|---|",
        f"| 총 발행 run 수 | {stats['total_runs']} |",
        f"| 총 실발행 수 (Post1 + Post2) | {stats['total_publish']} |",
        f"| — Post1 (심층분석) | {stats['post1_count']} |",
        f"| — Post2 (캐시의 픽) | {stats['post2_count']} |",
        f"| 공개 URL 수 | {stats['public_url_count']} |",
        f"",
        f"",
        f"### final_status 분포",
        f"",
        f"| 판정 | 수 |",
        f"|------|---|",
        f"| GO   | {stats['go_count']} |",
        f"| HOLD | {stats['hold_count']} |",
        f"",
        f"---",
        f"",
        f"## 3. 슬롯 분포",
        f"",
        f"| 슬롯 | 수 |",
        f"|------|---|",
    ]
    for slot, cnt in sorted(stats["slot_dist"].items(), key=lambda x: -x[1]):
        lines.append(f"| {slot} | {cnt} |")

    lines += [
        f"",
        f"---",
        f"",
        f"## 4. opener 회귀 여부 (Post2 기준)",
        f"",
        f"| 항목 | 값 |",
        f"|------|---|",
        f"| opener_pass (pass 수) | {stats['opener_pass_count']} |",
        f"| opener_pass (fail 수) | {stats['opener_fail_count']} |",
        f"| opener 회귀 감지 | {'⚠️ 예' if stats['opener_regression'] else '✅ 없음'} |",
        f"| generic opener 재발 | {'⚠️ 수동 확인 필요' if stats['opener_regression'] else '✅ 없음'} |",
        f"",
        f"---",
        f"",
        f"## 5. 품질 기준 통과율",
        f"",
        f"| 기준 | FAIL 수 | 상태 |",
        f"|------|---------|------|",
        f"| criteria_1_pass | {stats['c1_fail']} | {'⚠️' if stats['c1_fail'] > 0 else '✅'} |",
        f"| criteria_5_pass | {stats['c5_fail']} | {'⚠️' if stats['c5_fail'] > 0 else '✅'} |",
        f"| source_structure_pass | {stats['source_fail']} | {'⚠️' if stats['source_fail'] > 0 else '✅'} |",
        f"",
        f"---",
        f"",
        f"## 6. 수동 확인 필요 항목",
        f"",
    ]

    manual_items = []
    if stats["opener_regression"]:
        manual_items.append("- [ ] Post2 opener 회귀 감지됨 → pick-angle 구조 확인 필요")
    if stats["c1_fail"] > 0:
        manual_items.append(f"- [ ] criteria_1_pass FAIL {stats['c1_fail']}건 → 기준1 판정 확인 필요")
    if stats["c5_fail"] > 0:
        manual_items.append(f"- [ ] criteria_5_pass FAIL {stats['c5_fail']}건 → 기준5 판정 확인 필요")
    if stats["source_fail"] > 0:
        manual_items.append(f"- [ ] source_structure_pass FAIL {stats['source_fail']}건 → 소스 구조 확인 필요")
    if stats["hold_count"] > 0:
        manual_items.append(f"- [ ] final_status=HOLD {stats['hold_count']}건 → 발행 중단 run 확인 필요")
    if stats["total_publish"] == 0:
        manual_items.append("- [ ] 발행 실적 없음 → 파이프라인 실행 여부 확인 필요")

    if manual_items:
        lines += manual_items
    else:
        lines.append("없음 — 모든 기준 정상")

    lines += [
        f"",
        f"---",
        f"",
        f"## 7. PARSE_FAILED 현황",
        f"",
        f"이 리포트는 Phase 19 정상발행 품질로그(post_type 구분)만 분석합니다.",
        f"PARSE_FAILED (WARNING 레벨 로그)는 `macromalt_daily.log` artifact를",
        f"직접 확인하거나 별도 PARSE_FAILED 집계 스크립트를 사용하십시오.",
        f"",
        f"---",
        f"",
        f"## 8. title duplication 회귀 여부",
        f"",
        f"BUG-POST2-TITLE-DUP-20260320 수정 이후 회귀 여부는",
        f"공개 URL을 직접 방문하여 제목 2회 반복 여부를 확인하십시오.",
        f"자동 감지는 이번 리포트 범위 외입니다.",
        f"",
        f"---",
        f"",
        f"## 9. 발행 URL 목록",
        f"",
    ]

    if stats["public_urls"]:
        for url in stats["public_urls"]:
            lines.append(f"- {url}")
    else:
        lines.append("기간 내 공개 URL 없음")

    lines += [
        f"",
        f"---",
        f"",
        f"## 10. 최종 판정",
        f"",
        f"**{verdict}**",
        f"",
    ]

    verdict_notes = {
        "GO":              "모든 기준 정상. 자동 운영 계속.",
        "CONDITIONAL GO":  "일부 기준 요주의. 수동 확인 후 계속.",
        "HOLD":            "HOLD 발생. 파이프라인 이상 여부 수동 점검 필요.",
    }
    lines.append(verdict_notes.get(verdict, ""))
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# 5. 메인
# ═══════════════════════════════════════════════════════════

def main() -> int:
    period_end   = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=LOOKBACK_DAYS)

    print(f"[phase20_weekly_report.py] 기간: {period_start.date()} ~ {period_end.date()}")

    entries: list[dict] = []
    data_source = "unknown"

    # ── A. GitHub API 경로 (Actions 환경) ──────────────────
    if GITHUB_TOKEN and GITHUB_REPOSITORY:
        print(f"[phase20_weekly_report.py] GitHub API 사용: {GITHUB_REPOSITORY}")
        artifacts = _list_artifacts(GITHUB_REPOSITORY, period_start)
        print(f"[phase20_weekly_report.py] artifact {len(artifacts)}건 발견")
        for art in artifacts:
            batch = _download_jsonl(GITHUB_REPOSITORY, art["id"])
            print(f"  artifact {art['id']} ({art['name']}): {len(batch)}건")
            entries.extend(batch)
        data_source = f"GitHub API artifacts ({len(artifacts)}건)"

    # ── B. 로컬 fallback ────────────────────────────────────
    else:
        print("[phase20_weekly_report.py] GitHub Token 없음 → 로컬 JSONL fallback")
        entries = _load_local_jsonl()
        data_source = f"로컬 logs/publish_result.jsonl ({len(entries)}건)"

    print(f"[phase20_weekly_report.py] 총 집계 항목: {len(entries)}건")

    # ── 집계 ────────────────────────────────────────────────
    stats = _analyze(entries)

    # ── 리포트 생성 ─────────────────────────────────────────
    report_md = _render_report(stats, period_start, period_end, data_source)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_md, encoding="utf-8")
    print(f"[phase20_weekly_report.py] 리포트 저장: {REPORT_PATH}")
    print(f"[phase20_weekly_report.py] 최종 판정: {_final_verdict(stats)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
