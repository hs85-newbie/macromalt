"""
macromalt 비용 추적 모듈
========================
API 호출 토큰 수를 기반으로 예상 비용을 계산하고,
월간 예산 한도 접근 시 macOS 알림을 전송합니다.

예산:
  - OpenAI GPT-4o : $10.00 / 월
  - Gemini 2.5-flash : ₩15,000 / 월
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Optional

logger = logging.getLogger("macromalt")

# ──────────────────────────────────────────────
# 요금표 (2026년 기준)
# ──────────────────────────────────────────────
# OpenAI GPT-4o
OPENAI_INPUT_PRICE_PER_M = 2.50    # USD / 1M input tokens
OPENAI_OUTPUT_PRICE_PER_M = 10.00  # USD / 1M output tokens
OPENAI_LIMIT_USD = 10.00           # 월 상한선

# Gemini 2.5-flash (thinking OFF, ≤200K context)
GEMINI_INPUT_PRICE_PER_M = 0.075   # USD / 1M input tokens
GEMINI_OUTPUT_PRICE_PER_M = 0.30   # USD / 1M output tokens
GEMINI_LIMIT_KRW = 15_000          # 월 상한선 (원)
USD_TO_KRW = 1_380                 # 환율 (수동 관리, 월 1회 업데이트 권장)

# 알림 임계값
THRESHOLDS = [50, 80, 95]  # 예산 대비 % — 각 단계에서 알림 1회

COST_LOG_PATH = os.path.join(os.path.dirname(__file__), "cost_log.json")


# ──────────────────────────────────────────────
# 1. macOS 알림 전송
# ──────────────────────────────────────────────
def _send_mac_notification(title: str, message: str, subtitle: str = "") -> None:
    """macOS 시스템 알림을 전송합니다."""
    try:
        script = (
            f'display notification "{message}" '
            f'with title "{title}" '
            f'subtitle "{subtitle}" '
            f'sound name "Glass"'
        )
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        logger.info(f"알림 전송 완료: [{title}] {message}")
    except Exception as e:
        logger.warning(f"macOS 알림 전송 실패: {e}")


# ──────────────────────────────────────────────
# 2. cost_log.json 로드 / 저장
# ──────────────────────────────────────────────
def _load_log() -> dict:
    if os.path.exists(COST_LOG_PATH):
        try:
            with open(COST_LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_log(log: dict) -> None:
    with open(COST_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def _month_key() -> str:
    """현재 월 키 반환. 예: '2026-03'"""
    return datetime.now().strftime("%Y-%m")


def _init_month(log: dict, month: str) -> None:
    """월별 데이터가 없으면 초기화합니다."""
    if month not in log:
        log[month] = {
            "openai": {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "limit_usd": OPENAI_LIMIT_USD,
                "notified_thresholds": [],
            },
            "gemini": {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "cost_krw": 0,
                "limit_krw": GEMINI_LIMIT_KRW,
                "notified_thresholds": [],
            },
            "updated_at": "",
        }


# ──────────────────────────────────────────────
# 3. 알림 판단 및 전송
# ──────────────────────────────────────────────
def _check_and_notify_openai(month_data: dict, pct: float) -> None:
    notified = month_data["openai"]["notified_thresholds"]
    cost_usd = month_data["openai"]["cost_usd"]
    limit = OPENAI_LIMIT_USD

    for threshold in THRESHOLDS:
        if pct >= threshold and threshold not in notified:
            notified.append(threshold)
            if threshold >= 95:
                title = "🚨 OpenAI 예산 위험"
                msg = f"이번 달 ${cost_usd:.2f} / ${limit:.2f} 사용 ({pct:.1f}%)"
            elif threshold >= 80:
                title = "⚠️ OpenAI 예산 경고"
                msg = f"이번 달 ${cost_usd:.2f} / ${limit:.2f} 사용 ({pct:.1f}%)"
            else:
                title = "ℹ️ OpenAI 예산 알림"
                msg = f"이번 달 ${cost_usd:.2f} / ${limit:.2f} 사용 ({pct:.1f}%)"
            _send_mac_notification(title, msg, subtitle="macromalt 자동화")


def _check_and_notify_gemini(month_data: dict, pct: float) -> None:
    notified = month_data["gemini"]["notified_thresholds"]
    cost_krw = month_data["gemini"]["cost_krw"]
    limit = GEMINI_LIMIT_KRW

    for threshold in THRESHOLDS:
        if pct >= threshold and threshold not in notified:
            notified.append(threshold)
            if threshold >= 95:
                title = "🚨 Gemini 예산 위험"
                msg = f"이번 달 ₩{cost_krw:,} / ₩{limit:,} 사용 ({pct:.1f}%)"
            elif threshold >= 80:
                title = "⚠️ Gemini 예산 경고"
                msg = f"이번 달 ₩{cost_krw:,} / ₩{limit:,} 사용 ({pct:.1f}%)"
            else:
                title = "ℹ️ Gemini 예산 알림"
                msg = f"이번 달 ₩{cost_krw:,} / ₩{limit:,} 사용 ({pct:.1f}%)"
            _send_mac_notification(title, msg, subtitle="macromalt 자동화")


# ──────────────────────────────────────────────
# 4. 공개 API: 비용 기록
# ──────────────────────────────────────────────
def record_openai_usage(
    input_tokens: int,
    output_tokens: int,
) -> dict:
    """
    GPT-4o 호출 결과의 토큰 수를 기록하고 누적 비용을 반환합니다.

    반환값:
        {
            "call_cost_usd": float,
            "month_cost_usd": float,
            "month_pct": float,
            "limit_usd": float,
        }
    """
    call_cost = (
        input_tokens * OPENAI_INPUT_PRICE_PER_M / 1_000_000
        + output_tokens * OPENAI_OUTPUT_PRICE_PER_M / 1_000_000
    )

    log = _load_log()
    month = _month_key()
    _init_month(log, month)

    d = log[month]["openai"]
    d["calls"] += 1
    d["input_tokens"] += input_tokens
    d["output_tokens"] += output_tokens
    d["cost_usd"] = round(d["cost_usd"] + call_cost, 6)
    log[month]["updated_at"] = datetime.now().isoformat()

    pct = (d["cost_usd"] / OPENAI_LIMIT_USD) * 100
    _check_and_notify_openai(log[month], pct)
    _save_log(log)

    logger.info(
        f"[비용] GPT-4o | 이번 호출: ${call_cost:.4f} | "
        f"이번 달 누적: ${d['cost_usd']:.4f} / ${OPENAI_LIMIT_USD} ({pct:.1f}%)"
    )
    return {
        "call_cost_usd": call_cost,
        "month_cost_usd": d["cost_usd"],
        "month_pct": pct,
        "limit_usd": OPENAI_LIMIT_USD,
    }


def record_gemini_usage(
    input_tokens: int,
    output_tokens: int,
) -> dict:
    """
    Gemini 호출 결과의 토큰 수를 기록하고 누적 비용을 반환합니다.

    반환값:
        {
            "call_cost_usd": float,
            "call_cost_krw": int,
            "month_cost_krw": int,
            "month_pct": float,
            "limit_krw": int,
        }
    """
    call_cost_usd = (
        input_tokens * GEMINI_INPUT_PRICE_PER_M / 1_000_000
        + output_tokens * GEMINI_OUTPUT_PRICE_PER_M / 1_000_000
    )
    call_cost_krw = round(call_cost_usd * USD_TO_KRW)

    log = _load_log()
    month = _month_key()
    _init_month(log, month)

    d = log[month]["gemini"]
    d["calls"] += 1
    d["input_tokens"] += input_tokens
    d["output_tokens"] += output_tokens
    d["cost_usd"] = round(d["cost_usd"] + call_cost_usd, 6)
    d["cost_krw"] = round(d["cost_usd"] * USD_TO_KRW)
    log[month]["updated_at"] = datetime.now().isoformat()

    pct = (d["cost_krw"] / GEMINI_LIMIT_KRW) * 100
    _check_and_notify_gemini(log[month], pct)
    _save_log(log)

    logger.info(
        f"[비용] Gemini | 이번 호출: ₩{call_cost_krw} | "
        f"이번 달 누적: ₩{d['cost_krw']:,} / ₩{GEMINI_LIMIT_KRW:,} ({pct:.1f}%)"
    )
    return {
        "call_cost_usd": call_cost_usd,
        "call_cost_krw": call_cost_krw,
        "month_cost_krw": d["cost_krw"],
        "month_pct": pct,
        "limit_krw": GEMINI_LIMIT_KRW,
    }


# ──────────────────────────────────────────────
# 5. 런 단위 토큰 추적 (이번 실행 합산)
# ──────────────────────────────────────────────
import copy as _copy

_run_start_snapshot: dict = {}


def record_run_start() -> None:
    """파이프라인 시작 시 현재 누적 상태를 스냅샷으로 저장."""
    global _run_start_snapshot
    log = _load_log()
    month = _month_key()
    _run_start_snapshot = _copy.deepcopy(log.get(month, {}))


def get_run_summary() -> dict:
    """이번 런에서 발생한 토큰·비용 델타를 반환합니다.

    반환 예시:
        {
          "gpt":    {"calls": 2, "input": 12000, "output": 8000, "cost_usd": 0.0980},
          "gemini": {"calls": 3, "input": 40000, "output": 6000, "cost_krw": 18},
          "total_krw": 153,
          "total_usd": 0.1111,
        }
    """
    log = _load_log()
    month = _month_key()
    if month not in log:
        return {}

    cur = log[month]
    st  = _run_start_snapshot

    def _d(model: str, key: str) -> int:
        return cur.get(model, {}).get(key, 0) - st.get(model, {}).get(key, 0)

    gpt_in   = _d("openai", "input_tokens")
    gpt_out  = _d("openai", "output_tokens")
    gpt_call = _d("openai", "calls")
    gem_in   = _d("gemini", "input_tokens")
    gem_out  = _d("gemini", "output_tokens")
    gem_call = _d("gemini", "calls")

    gpt_usd = (gpt_in  * OPENAI_INPUT_PRICE_PER_M  / 1_000_000
             + gpt_out * OPENAI_OUTPUT_PRICE_PER_M / 1_000_000)
    gem_usd = (gem_in  * GEMINI_INPUT_PRICE_PER_M  / 1_000_000
             + gem_out * GEMINI_OUTPUT_PRICE_PER_M / 1_000_000)
    total_usd = gpt_usd + gem_usd

    return {
        "gpt": {
            "calls":    gpt_call,
            "input":    gpt_in,
            "output":   gpt_out,
            "cost_usd": round(gpt_usd, 4),
            "cost_krw": round(gpt_usd * USD_TO_KRW),
        },
        "gemini": {
            "calls":    gem_call,
            "input":    gem_in,
            "output":   gem_out,
            "cost_usd": round(gem_usd, 6),
            "cost_krw": round(gem_usd * USD_TO_KRW),
        },
        "total_usd": round(total_usd, 4),
        "total_krw": round(total_usd * USD_TO_KRW),
    }


# ──────────────────────────────────────────────
# 6. 공개 API: 현황 요약 출력
# ──────────────────────────────────────────────
def print_monthly_summary(month: Optional[str] = None) -> None:
    """이번 달 또는 지정 월의 비용 현황을 출력합니다."""
    log = _load_log()
    month = month or _month_key()

    if month not in log:
        print(f"[{month}] 기록 없음")
        return

    data = log[month]
    oa = data["openai"]
    gm = data["gemini"]
    oa_pct = (oa["cost_usd"] / OPENAI_LIMIT_USD) * 100
    gm_pct = (gm["cost_krw"] / GEMINI_LIMIT_KRW) * 100

    print(f"\n{'='*50}")
    print(f"📊 macromalt API 비용 현황 [{month}]")
    print(f"{'='*50}")
    print(f"🤖 OpenAI GPT-4o")
    print(f"   호출 수   : {oa['calls']:,}회")
    print(f"   입력 토큰 : {oa['input_tokens']:,}")
    print(f"   출력 토큰 : {oa['output_tokens']:,}")
    print(f"   누적 비용 : ${oa['cost_usd']:.4f} / ${OPENAI_LIMIT_USD:.2f} ({oa_pct:.1f}%)")
    print(f"   잔여 예산 : ${OPENAI_LIMIT_USD - oa['cost_usd']:.4f}")
    print()
    print(f"🔵 Gemini 2.5-flash")
    print(f"   호출 수   : {gm['calls']:,}회")
    print(f"   입력 토큰 : {gm['input_tokens']:,}")
    print(f"   출력 토큰 : {gm['output_tokens']:,}")
    print(f"   누적 비용 : ₩{gm['cost_krw']:,} / ₩{GEMINI_LIMIT_KRW:,} ({gm_pct:.1f}%)")
    print(f"   잔여 예산 : ₩{GEMINI_LIMIT_KRW - gm['cost_krw']:,}")
    print(f"{'='*50}")
    print(f"  마지막 업데이트: {data.get('updated_at', 'N/A')}")
    print(f"{'='*50}\n")


# ──────────────────────────────────────────────
# 6. 직접 실행 시 현황 출력
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print_monthly_summary()
