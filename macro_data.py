"""
macro_data.py — Phase A: 거시지표 실시간 조회 모듈
=====================================================
BOK ECOS + FRED API를 통해 한국·미국 핵심 거시지표를 수집하고
생성 파이프라인에 주입할 프롬프트 텍스트를 반환합니다.

캐시: 1시간 TTL (JSON 파일, data/macro_cache.json)
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("macromalt")

BOK_KEY  = os.getenv("BOK_API_KEY", "")
FRED_KEY = os.getenv("FRED_API_KEY", "")
BOK_BASE  = "https://ecos.bok.or.kr/api"
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

_CACHE_FILE      = Path(__file__).parent / "data" / "macro_cache.json"
_CACHE_TTL_HOURS = 1

# ── BOK 통계 코드 정의 ──────────────────────────────────────────────────────
# (통계코드, 항목코드, 주기, 레이블)
_BOK_SERIES: dict = {
    "base_rate": ("722Y001", "0101000", "M", "한국 기준금리(%)"),
    "usd_krw":   ("731Y001", "0000001", "D", "달러/원 환율(원)"),
    "cpi":       ("901Y009", "0",       "M", "소비자물가지수"),
    "m2":        ("101Y004", "BBHA00",  "M", "M2 광의통화"),
}

# ── FRED 시리즈 정의 ─────────────────────────────────────────────────────────
_FRED_SERIES: dict = {
    "fed_rate":     ("FEDFUNDS", "연준 기준금리(%)"),
    "us_10y":       ("DGS10",    "미국 10년 국채수익률(%)"),
    "us_2y":        ("DGS2",     "미국 2년 국채수익률(%)"),
    "unemployment": ("UNRATE",   "미국 실업률(%)"),
    "dxy":          ("DTWEXBGS", "달러인덱스(DXY)"),
    "vix":          ("VIXCLS",   "VIX 변동성지수"),
}


# ── 캐시 유틸 ────────────────────────────────────────────────────────────────

def _load_cache() -> Optional[dict]:
    """캐시 파일 로드. TTL 초과 또는 없으면 None 반환."""
    if not _CACHE_FILE.exists():
        return None
    try:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            cached = json.load(f)
        cached_at = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=_CACHE_TTL_HOURS):
            return cached
    except Exception:
        pass
    return None


def _save_cache(data: dict) -> None:
    """거시지표 데이터를 캐시 파일로 저장."""
    _CACHE_FILE.parent.mkdir(exist_ok=True)
    data["cached_at"] = datetime.now().isoformat()
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"[macro_data] 캐시 저장 실패: {e}")


# ── BOK 조회 ─────────────────────────────────────────────────────────────────

def _fetch_bok_value(stat_code: str, item_code: str, cycle: str) -> Optional[str]:
    """BOK ECOS API에서 최신값 1건 조회. 실패 시 None 반환."""
    if not BOK_KEY:
        return None
    now = datetime.now()
    if cycle == "D":
        start = (now - timedelta(days=14)).strftime("%Y%m%d")
        end   = now.strftime("%Y%m%d")
    else:  # M
        start = (now - timedelta(days=90)).strftime("%Y%m")[:6]
        end   = now.strftime("%Y%m")[:6]

    url = (
        f"{BOK_BASE}/StatisticSearch/{BOK_KEY}/json/kr/1/5/"
        f"{stat_code}/{cycle}/{start}/{end}/{item_code}"
    )
    try:
        r = requests.get(url, timeout=10)
        rows = r.json().get("StatisticSearch", {}).get("row", [])
        if rows:
            latest = rows[-1]
            return f"{latest['DATA_VALUE']} ({latest['TIME']})"
    except Exception as e:
        logger.warning(f"[macro_data] BOK 조회 실패 ({stat_code}): {e}")
    return None


# ── FRED 조회 ────────────────────────────────────────────────────────────────

def _fetch_fred_value(series_id: str) -> Optional[str]:
    """FRED API에서 최신값 1건 조회. 실패 시 None 반환."""
    if not FRED_KEY:
        return None
    try:
        params = {
            "series_id":        series_id,
            "api_key":          FRED_KEY,
            "file_type":        "json",
            "sort_order":       "desc",
            "limit":            1,
            "observation_start": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        }
        r = requests.get(FRED_BASE, params=params, timeout=10)
        obs = r.json().get("observations", [])
        if obs and obs[0]["value"] != ".":
            o = obs[0]
            return f"{float(o['value']):.2f} ({o['date']})"
    except Exception as e:
        logger.warning(f"[macro_data] FRED 조회 실패 ({series_id}): {e}")
    return None


# ── 숫자 추출 헬퍼 ────────────────────────────────────────────────────────────

def _extract_float(value_str: Optional[str]) -> Optional[float]:
    """'3.50 (202403)' 형태 문자열에서 숫자만 추출."""
    if not value_str:
        return None
    try:
        return float(value_str.split()[0].replace(",", ""))
    except Exception:
        return None


# ── 메인 공개 API ─────────────────────────────────────────────────────────────

def get_macro_snapshot(force_refresh: bool = False) -> dict:
    """
    한국·미국 핵심 거시지표 스냅샷을 반환합니다.
    1시간 TTL 캐시를 사용합니다. force_refresh=True 시 캐시 무시.

    반환값:
        {
          "korea": {
            "base_rate": "3.50 (202403)",   # str
            "usd_krw":   "1456 (20250306)", # str
            "cpi":       "113.95 (202403)", # str
            "m2":        "..."              # str
          },
          "us": {
            "fed_rate":     "3.64 (2026-02-01)",
            "us_10y":       "4.39 (2026-03-20)",
            "us_2y":        "4.21 (2026-03-20)",
            "unemployment": "4.40 (2026-02-01)",
            "dxy":          "120.28 (2026-03-20)",
            "vix":          "18.50 (2026-03-20)"
          },
          "floats": {                         # 교차검증용 숫자값
            "bok_rate": 3.50,
            "usdkrw":   1456.0,
            "fed_rate": 3.64,
            "us_10y":   4.39,
            "us_2y":    4.21
          },
          "cached_at": "2026-03-23T..."
        }
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            logger.info("[macro_data] 캐시 사용 (TTL 이내)")
            return cached

    logger.info("[macro_data] 거시지표 신규 조회 시작")
    result: dict = {"korea": {}, "us": {}, "floats": {}}

    # BOK 조회
    for key, (stat, item, cycle, label) in _BOK_SERIES.items():
        val = _fetch_bok_value(stat, item, cycle)
        result["korea"][key] = val or "조회 불가"
        if val:
            logger.info(f"[macro_data] BOK {label}: {val}")

    # FRED 조회
    for key, (series_id, label) in _FRED_SERIES.items():
        val = _fetch_fred_value(series_id)
        result["us"][key] = val or "조회 불가"
        if val:
            logger.info(f"[macro_data] FRED {label}: {val}")

    # 교차검증용 float 값 추출
    result["floats"] = {
        "bok_rate": _extract_float(result["korea"].get("base_rate")),
        "usdkrw":   _extract_float(result["korea"].get("usd_krw")),
        "fed_rate": _extract_float(result["us"].get("fed_rate")),
        "us_10y":   _extract_float(result["us"].get("us_10y")),
        "us_2y":    _extract_float(result["us"].get("us_2y")),
    }

    _save_cache(result)
    logger.info(f"[macro_data] 거시지표 조회 완료: KR금리={result['floats']['bok_rate']}%, USD/KRW={result['floats']['usdkrw']}")
    return result


def format_macro_for_prompt(snapshot: dict) -> str:
    """
    거시지표 스냅샷을 Gemini/GPT 프롬프트 주입용 텍스트로 변환합니다.

    출력 예시:
        [거시지표 스냅샷 — 2026-03-23 기준 (BOK·FRED 실시간)]
        ■ 한국
          기준금리: 3.50% (202403) | 달러/원: 1,456원 (20250306) | CPI: 113.95pt
        ■ 미국
          연준금리: 3.64% | 10년물: 4.39% | 2년물: 4.21% | 실업률: 4.4%
          달러인덱스(DXY): 120.28 | VIX: 18.50
          장단기 스프레드(10Y-2Y): +0.18%p (정상)
    """
    if not snapshot or (
        not snapshot.get("korea") and not snapshot.get("us")
    ):
        return ""

    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"\n[거시지표 스냅샷 — {today} 기준 (BOK·FRED 실시간)]\n"]

    kr = snapshot.get("korea", {})
    lines.append("■ 한국 거시지표")
    lines.append(f"  기준금리:   {kr.get('base_rate', 'N/A')}")
    lines.append(f"  달러/원:    {kr.get('usd_krw', 'N/A')}")
    lines.append(f"  소비자물가: {kr.get('cpi', 'N/A')}")
    lines.append(f"  M2 통화량:  {kr.get('m2', 'N/A')}")

    us = snapshot.get("us", {})
    lines.append("\n■ 미국 거시지표")
    lines.append(f"  연준금리:   {us.get('fed_rate', 'N/A')}")
    lines.append(f"  10년 국채:  {us.get('us_10y', 'N/A')}")
    lines.append(f"  2년 국채:   {us.get('us_2y', 'N/A')}")
    lines.append(f"  실업률:     {us.get('unemployment', 'N/A')}")
    lines.append(f"  달러인덱스: {us.get('dxy', 'N/A')}")
    lines.append(f"  VIX:        {us.get('vix', 'N/A')}")

    # 장단기 스프레드 자동 계산
    floats = snapshot.get("floats", {})
    y10 = floats.get("us_10y")
    y2  = floats.get("us_2y")
    if y10 is not None and y2 is not None:
        spread    = y10 - y2
        direction = "정상" if spread >= 0 else "역전 ⚠"
        lines.append(f"  장단기스프레드(10Y-2Y): {spread:+.2f}%p ({direction})")

    lines.append(
        "\n※ 위 수치를 글에서 인용 시 출처 표기: "
        "BOK(한국은행 경제통계시스템) 또는 FRED(미국 연준)"
    )
    return "\n".join(lines)
