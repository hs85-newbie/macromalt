"""
reference_loader.py — Phase C: 거시경제 리포트 + Few-shot 예시 로더
====================================================================
1. data/macro_reports/ 폴더의 PDF를 읽어 텍스트 추출 후 캐싱
2. data/few_shot/examples.json 의 모범 글 예시를 GPT 라이터 프롬프트에 주입
3. generator.py의 history_ctx / GPT SYSTEM에 append 방식으로 연결

캐시 TTL: 24시간 (PDF는 자주 바뀌지 않으므로)
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("macromalt")

_REPORTS_DIR   = Path(__file__).parent / "data" / "macro_reports"
_FEW_SHOT_FILE = Path(__file__).parent / "data" / "few_shot" / "examples.json"
_CACHE_FILE    = Path(__file__).parent / "data" / "macro_reports" / "_cache.json"
_CACHE_TTL_H   = 24
_MAX_CHARS_PER_REPORT = 3000   # PDF 1개당 최대 추출 글자수 (토큰 절약)
_MAX_TOTAL_CHARS      = 8000   # 전체 리포트 컨텍스트 상한


# ── 캐시 유틸 ─────────────────────────────────────────────────────────────────

def _load_cache() -> Optional[dict]:
    if not _CACHE_FILE.exists():
        return None
    try:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            cached = json.load(f)
        cached_at = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=_CACHE_TTL_H):
            return cached
    except Exception:
        pass
    return None


def _save_cache(data: dict) -> None:
    data["cached_at"] = datetime.now().isoformat()
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"[reference_loader] 캐시 저장 실패: {e}")


# ── PDF 텍스트 추출 ───────────────────────────────────────────────────────────

def _extract_pdf_text(pdf_path: Path) -> str:
    """pdfplumber로 PDF 텍스트 추출. 실패 시 빈 문자열 반환."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages[:20]:   # 최대 20페이지
                t = page.extract_text()
                if t:
                    text_parts.append(t.strip())
        full_text = "\n".join(text_parts)
        return full_text[:_MAX_CHARS_PER_REPORT]
    except Exception as e:
        logger.warning(f"[reference_loader] PDF 추출 실패 ({pdf_path.name}): {e}")
        return ""


# ── 공개 PDF 자동 다운로드 ────────────────────────────────────────────────────
# 정기 발간 공공 리포트만 포함 (저작권 무관한 공식 배포 문서)

_AUTO_DOWNLOAD_SOURCES = [
    {
        "id": "imf_weo",
        "name": "IMF World Economic Outlook (최신)",
        "url": "https://www.imf.org/external/pubs/ft/weo/2025/02/weodata/WEOOct2025all.pdf",
        "filename": "imf_weo_latest.pdf",
    },
    {
        "id": "fed_beige_book",
        "name": "미 연준 Beige Book (최신)",
        "url": "https://www.federalreserve.gov/monetarypolicy/files/BeigeBook_20250115.pdf",
        "filename": "fed_beige_book_latest.pdf",
    },
]


def _try_download_auto_reports() -> None:
    """자동 다운로드 대상 리포트를 data/macro_reports/ 에 저장."""
    import requests
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for src in _AUTO_DOWNLOAD_SOURCES:
        dest = _REPORTS_DIR / src["filename"]
        if dest.exists():
            continue  # 이미 있으면 스킵
        try:
            r = requests.get(src["url"], timeout=30, headers={"User-Agent": "macromalt/1.0"})
            if r.status_code == 200 and b"%PDF" in r.content[:10]:
                dest.write_bytes(r.content)
                logger.info(f"[reference_loader] 자동 다운로드 완료: {src['name']}")
        except Exception as e:
            logger.debug(f"[reference_loader] 자동 다운로드 실패 ({src['name']}): {e}")


# ── 메인 공개 API: 리포트 컨텍스트 ──────────────────────────────────────────

def load_reference_reports(force_refresh: bool = False) -> dict:
    """
    data/macro_reports/ 폴더의 PDF를 읽고 추출 텍스트를 반환.
    24시간 캐시 적용.

    반환:
        {
          "reports": [{"name": "...", "text": "..."}],
          "cached_at": "..."
        }
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            logger.info(f"[reference_loader] 리포트 캐시 사용 ({len(cached.get('reports', []))}건)")
            return cached

    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _try_download_auto_reports()

    reports = []
    pdf_files = sorted(_REPORTS_DIR.glob("*.pdf"))

    for pdf_path in pdf_files:
        text = _extract_pdf_text(pdf_path)
        if not text.strip():
            continue
        reports.append({
            "name": pdf_path.stem.replace("_", " ").replace("-", " "),
            "filename": pdf_path.name,
            "text": text,
        })
        logger.info(f"[reference_loader] 로드 완료: {pdf_path.name} ({len(text)}자)")

    result = {"reports": reports}
    _save_cache(result)
    logger.info(f"[reference_loader] 총 {len(reports)}개 리포트 로드")
    return result


def format_reports_for_prompt(reports_data: dict) -> str:
    """
    리포트 데이터를 Gemini 애널리스트 프롬프트 주입용 텍스트로 변환.
    전체 상한 _MAX_TOTAL_CHARS 적용.
    """
    reports = reports_data.get("reports", [])
    if not reports:
        return ""

    lines = ["\n[참고 거시경제 리포트 — 분석 깊이 보강용]\n"]
    total_chars = 0

    for r in reports:
        if total_chars >= _MAX_TOTAL_CHARS:
            break
        block = f"■ {r['name']}\n{r['text']}\n"
        lines.append(block)
        total_chars += len(block)

    lines.append(
        "\n※ 위 리포트는 분석 깊이·논거 보강용 배경 자료입니다. "
        "현재 뉴스 사실과 교차 검증 후 활용하세요.\n"
    )
    return "\n".join(lines)


# ── 메인 공개 API: Few-shot 예시 ─────────────────────────────────────────────

def load_few_shot_examples() -> list:
    """
    data/few_shot/examples.json 에서 모범 글 예시를 로드.
    파일 없거나 비어있으면 빈 리스트 반환.
    """
    if not _FEW_SHOT_FILE.exists():
        return []
    try:
        with open(_FEW_SHOT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        examples = data.get("examples", [])
        logger.info(f"[reference_loader] Few-shot 예시 {len(examples)}건 로드")
        return examples
    except Exception as e:
        logger.warning(f"[reference_loader] Few-shot 로드 실패: {e}")
        return []


def format_few_shot_for_prompt(examples: list) -> str:
    """
    Few-shot 예시를 GPT 라이터 SYSTEM 프롬프트 주입용 텍스트로 변환.
    """
    if not examples:
        return ""

    lines = ["\n\n[모범 글 예시 — 아래 수준의 문체·구조·분석 깊이를 목표로 작성]\n"]
    for i, ex in enumerate(examples[:3], 1):   # 최대 3개
        title   = ex.get("title", f"예시 {i}")
        excerpt = ex.get("excerpt", "")[:1500]  # 예시당 최대 1500자
        source  = ex.get("source", "")
        lines.append(f"--- 예시 {i}: {title} ({source}) ---")
        lines.append(excerpt)
        lines.append("")

    lines.append(
        "--- 위 예시의 핵심 특징 ---\n"
        "· 수치 직후 즉시 의미 해석\n"
        "· 인과관계 3단계 연결 (사실 → 메커니즘 → 영향)\n"
        "· 단정 문장과 [해석]/[전망] 태그의 명확한 구분\n"
        "· 섹션 간 논리적 흐름 (병렬 나열 금지)\n"
    )
    return "\n".join(lines)
