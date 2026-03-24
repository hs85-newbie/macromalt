"""
knowledge_base.py — Phase B: 발행 이력 지식베이스 (경량 RAG)
=============================================================
SQLite 기반 아티클 저장소.
글 생성 전 관련 과거 글을 검색하여 논지 반복·수치 모순·테마 중복을 방지합니다.

사용 패턴:
    # 글 생성 전: 관련 과거 글 검색 → history_ctx에 추가
    ctx = retrieve_context(theme, news_text)

    # 글 생성 후: KB 저장
    save_article(post_type, theme, title, content, tickers, slot)
"""

import json
import logging
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("macromalt")

_DB_PATH             = Path(__file__).parent / "data" / "knowledge_base.db"
_SIMILARITY_MIN      = 0.12   # Jaccard 최소 유사도
_CONTEXT_MAX         = 3      # 반환할 최대 과거 글 수
_LOOKBACK_DAYS       = 30     # 검색 범위 (일)
_KEY_SENTENCES_MAX   = 5      # 저장할 핵심 문장 수


# ── DB 초기화 ─────────────────────────────────────────────────────────────────

def _init_db() -> None:
    """DB 테이블 초기화 (없을 경우에만 생성)."""
    _DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            published_at   TEXT,
            post_type      TEXT,
            theme          TEXT,
            title          TEXT,
            key_sentences  TEXT,
            tickers        TEXT,
            slot           TEXT
        )
    """)
    conn.commit()
    conn.close()


# ── 유틸 함수 ─────────────────────────────────────────────────────────────────

def _extract_key_sentences(html_content: str) -> list:
    """HTML에서 핵심 문장을 추출합니다 (h3 제목 + 첫 단락 우선)."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        sentences = []
        for tag in soup.find_all(["h1", "h3"])[:3]:
            t = tag.get_text(strip=True)
            if t and len(t) > 5:
                sentences.append(t[:100])
        for p in soup.find_all("p")[:8]:
            t = p.get_text(strip=True)
            if t and len(t) > 20:
                sentences.append(t[:120])
            if len(sentences) >= _KEY_SENTENCES_MAX:
                break
        return sentences[:_KEY_SENTENCES_MAX]
    except Exception:
        return []


def _jaccard(text_a: str, text_b: str) -> float:
    """한국어·영문 단어 기반 Jaccard 유사도 계산."""
    tok_a = set(re.findall(r"[가-힣A-Za-z]{2,}", text_a))
    tok_b = set(re.findall(r"[가-힣A-Za-z]{2,}", text_b))
    if not tok_a or not tok_b:
        return 0.0
    return len(tok_a & tok_b) / len(tok_a | tok_b)


# ── 저장 ──────────────────────────────────────────────────────────────────────

def save_article(
    post_type: str,
    theme: str,
    title: str,
    content: str,
    tickers: Optional[list] = None,
    slot: str = "default",
) -> None:
    """
    생성된 글을 지식베이스에 저장합니다.

    Args:
        post_type: "post1" 또는 "post2"
        theme:     Gemini Step1이 선정한 테마 문자열
        title:     발행 제목
        content:   최종 HTML 본문
        tickers:   종목 코드 리스트 (Post2)
        slot:      발행 슬롯
    """
    _init_db()
    key_sentences = _extract_key_sentences(content)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        """INSERT INTO articles
               (published_at, post_type, theme, title, key_sentences, tickers, slot)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().isoformat(),
            post_type,
            theme,
            title,
            json.dumps(key_sentences, ensure_ascii=False),
            json.dumps(tickers or [], ensure_ascii=False),
            slot,
        ),
    )
    conn.commit()
    conn.close()
    logger.info(f"[KB] 저장: [{post_type}] {title[:50]}")


# ── 검색 ──────────────────────────────────────────────────────────────────────

def retrieve_context(
    query_theme: str = "",
    query_news_text: str = "",
    limit: int = _CONTEXT_MAX,
) -> str:
    """
    테마·뉴스 키워드 기반으로 관련 과거 글을 검색하고
    프롬프트 주입용 컨텍스트 문자열을 반환합니다.

    유사도 내림차순 정렬 → 상위 N건 반환.
    유사한 글이 없으면 빈 문자열 반환.

    반환 예시:
        [지식베이스 — 관련 과거 글 (논지 반복·수치 모순 방지)]
        ▸ 2일 전 [post1] 미중 무역긴장 | 제목: 반도체 수출 둔화...
          핵심: 미국 관세 25% 발효로 한국 반도체 수출 월 3조원 타격
          종목: 삼성전자·SK하이닉스
        [위 글들과 동일 논지·수치·종목을 반복하지 마십시오]
    """
    _init_db()
    cutoff = (datetime.now() - timedelta(days=_LOOKBACK_DAYS)).isoformat()
    conn = sqlite3.connect(_DB_PATH)
    rows = conn.execute(
        """SELECT published_at, post_type, theme, title, key_sentences, tickers
           FROM articles
           WHERE published_at >= ?
           ORDER BY published_at DESC
           LIMIT 50""",
        (cutoff,),
    ).fetchall()
    conn.close()

    if not rows:
        return ""

    combined_query = f"{query_theme} {query_news_text[:300]}"
    scored = []
    for row in rows:
        pub_at, post_type, theme, title, key_json, tickers_json = row
        try:
            keys = json.loads(key_json or "[]")
        except Exception:
            keys = []
        try:
            tickers = json.loads(tickers_json or "[]")
        except Exception:
            tickers = []

        row_text = f"{theme} {title} {' '.join(keys)}"
        score    = _jaccard(combined_query, row_text)

        try:
            age_days = (datetime.now() - datetime.fromisoformat(pub_at)).days
        except Exception:
            age_days = 99

        scored.append({
            "score": score, "age_days": age_days,
            "pub_at": pub_at, "post_type": post_type,
            "theme": theme, "title": title,
            "keys": keys, "tickers": tickers,
        })

    relevant = sorted(
        [s for s in scored if s["score"] >= _SIMILARITY_MIN],
        key=lambda x: (-x["score"], x["age_days"]),
    )[:limit]

    if not relevant:
        return ""

    lines = ["\n[지식베이스 — 관련 과거 글 (논지 반복·수치 모순 방지)]"]
    for item in relevant:
        age_label   = f"{item['age_days']}일 전" if item["age_days"] > 0 else "오늘"
        tickers_str = "·".join(item["tickers"][:3]) if item["tickers"] else ""
        lines.append(
            f"▸ {age_label} [{item['post_type']}] "
            f"테마: {item['theme'][:40]} | 제목: {item['title'][:45]}"
        )
        if item["keys"]:
            lines.append(f"  핵심: {item['keys'][0][:90]}")
        if tickers_str:
            lines.append(f"  종목: {tickers_str}")

    lines.append("[위 글들과 동일 논지·수치·종목을 그대로 반복하지 마십시오]")
    result = "\n".join(lines)
    logger.info(f"[KB] 관련 과거 글 {len(relevant)}건 검색 완료 (쿼리: '{query_theme[:30]}')")
    return result


# ── 통계 조회 (선택) ──────────────────────────────────────────────────────────

def get_stats() -> dict:
    """지식베이스 통계 (총 글 수, 최근 발행일 등)."""
    _init_db()
    conn = sqlite3.connect(_DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    latest = conn.execute(
        "SELECT published_at FROM articles ORDER BY published_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return {
        "total_articles": total,
        "latest_published_at": latest[0] if latest else None,
    }
