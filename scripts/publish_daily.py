#!/usr/bin/env python3
"""
macromalt 발행 스크립트 — GitHub Actions 래퍼
=============================================
기존 main.py를 서브프로세스로 호출하고,
실행 결과(Phase 19 품질로그)를 JSONL 형식으로
logs/publish_result.jsonl 에 저장한다.

사용법:
  python scripts/publish_daily.py

출력:
  stdout  — main.py 전체 로그 + JSONL 요약
  logs/publish_result.jsonl  — 파싱된 Phase 19 품질로그 (JSONL)
  exit code 0 = 성공, 1 = 실패
"""

import json
import os
import re
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── 경로 설정 ────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
LOG_PATH = PROJECT_ROOT / "logs" / "macromalt_daily.log"
RESULT_PATH = PROJECT_ROOT / "logs" / "publish_result.jsonl"

# ── Phase 19 로그 패턴 ────────────────────────────────────────
_P19_PATTERN = re.compile(
    r"\[Phase 19\] 정상발행 품질로그 \| "
    r"run_id=(?P<run_id>\S+) \| "
    r"slot=(?P<slot>\S+) \| "
    r"post_type=(?P<post_type>\S+) \| "
    r"final_status=(?P<final_status>\S+) \| "
    r"opener_pass=(?P<opener_pass>\S+) \| "
    r"criteria_1_pass=(?P<criteria_1_pass>\S+) \| "
    r"criteria_5_pass=(?P<criteria_5_pass>\S+) \| "
    r"source_structure_pass=(?P<source_structure_pass>\S+) \| "
    r"public_url=(?P<public_url>\S+)"
)

# ── run_id 추출 패턴 ─────────────────────────────────────────
_RUNID_PATTERN = re.compile(
    r"macromalt Phase 15E 파이프라인 시작 \[run_id: (?P<run_id>\S+)\]"
)

# ── 로그 타임스탬프 패턴 ─────────────────────────────────────
_TS_PATTERN = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")


def _run_pipeline() -> tuple[int, str]:
    """main.py를 서브프로세스로 실행하고 (exit_code, combined_output) 반환."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "main.py")],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    return result.returncode, result.stdout


def _extract_run_id_from_log(started_after: datetime) -> Optional[str]:
    """로그 파일에서 started_after 이후에 시작된 최신 run_id를 추출."""
    if not LOG_PATH.exists():
        return None

    run_id = None
    for line in LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        ts_m = _TS_PATTERN.match(line)
        if not ts_m:
            continue
        try:
            line_ts = datetime.strptime(ts_m.group("ts"), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if line_ts < started_after:
            continue
        m = _RUNID_PATTERN.search(line)
        if m:
            run_id = m.group("run_id")  # 마지막 매칭 run_id 사용

    return run_id


def _parse_phase19_entries(run_id: str) -> list[dict]:
    """로그 파일에서 해당 run_id의 Phase 19 품질로그 항목을 파싱."""
    if not LOG_PATH.exists():
        return []

    entries = []
    for line in LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _P19_PATTERN.search(line)
        if not m:
            continue
        if m.group("run_id") != run_id:
            continue

        entry = {
            "run_id":               m.group("run_id"),
            "slot":                 m.group("slot"),
            "post_type":            m.group("post_type"),
            "final_status":         m.group("final_status"),
            "opener_pass":          m.group("opener_pass") == "True",
            "criteria_1_pass":      m.group("criteria_1_pass") == "True",
            "criteria_5_pass":      m.group("criteria_5_pass") == "True",
            "source_structure_pass": m.group("source_structure_pass") == "True",
            "public_url":           m.group("public_url"),
            "logged_at":            datetime.now(timezone.utc).isoformat(),
        }
        entries.append(entry)

    return entries


def _write_jsonl(entries: list[dict]) -> None:
    """Phase 19 품질로그를 JSONL 파일로 저장 (append 모드)."""
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _print_summary(entries: list[dict]) -> None:
    """GitHub Actions 로그에서 읽기 쉽도록 요약 출력."""
    print()
    print("=" * 60)
    print("=== PHASE19_QUALITY_LOG SUMMARY ===")
    print("=" * 60)
    if not entries:
        print("[WARN] Phase 19 품질로그 항목을 찾지 못했습니다.")
        print("       main.py 실행 실패 또는 PARSE_FAILED 경로로 분기됐을 수 있습니다.")
        return

    for e in entries:
        print(f"  post_type : {e['post_type']}")
        print(f"  run_id    : {e['run_id']}")
        print(f"  slot      : {e['slot']}")
        print(f"  final_status: {e['final_status']}")
        print(f"  opener_pass         : {e['opener_pass']}")
        print(f"  criteria_1_pass     : {e['criteria_1_pass']}")
        print(f"  criteria_5_pass     : {e['criteria_5_pass']}")
        print(f"  source_structure_pass: {e['source_structure_pass']}")
        print(f"  public_url: {e['public_url']}")
        print("-" * 40)
        print(json.dumps(e, ensure_ascii=False))
        print()


def main() -> int:
    started_at = datetime.now()
    print(f"[publish_daily.py] 시작: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[publish_daily.py] PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"[publish_daily.py] LOG_PATH: {LOG_PATH}")
    print()

    # ── 1. 파이프라인 실행 ──────────────────────────────────
    print("[publish_daily.py] python main.py 실행 중...")
    exit_code, output = _run_pipeline()
    print(output)

    # ── 2. run_id 추출 ──────────────────────────────────────
    run_id = _extract_run_id_from_log(started_at)
    if run_id:
        print(f"[publish_daily.py] 감지된 run_id: {run_id}")
    else:
        print("[publish_daily.py][WARN] run_id를 로그에서 찾지 못했습니다.")

    # ── 3. Phase 19 품질로그 파싱 ───────────────────────────
    entries: list[dict] = []
    if run_id:
        entries = _parse_phase19_entries(run_id)

    # ── 4. JSONL 저장 ───────────────────────────────────────
    if entries:
        _write_jsonl(entries)
        print(f"[publish_daily.py] 품질로그 {len(entries)}건 → {RESULT_PATH}")
    else:
        print("[publish_daily.py][WARN] JSONL에 저장할 항목이 없습니다.")

    # ── 5. 요약 출력 ────────────────────────────────────────
    _print_summary(entries)

    if exit_code != 0:
        print(f"[publish_daily.py][ERROR] main.py exit code: {exit_code}")
    else:
        print(f"[publish_daily.py] 완료 (exit 0)")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
