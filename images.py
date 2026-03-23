"""
macromalt 자동화 시스템 - 이미지 처리 모듈
=====================================================
Post 1 (심층분석): Unsplash API → 테마 키워드 대표 이미지
Post 2 (캐시의 픽): yfinance 1주 데이터 → matplotlib 차트 이미지
공용: WordPress 미디어 라이브러리 업로드 → media_id 반환
"""

import io
import logging
import os
import tempfile
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("macromalt")


# ──────────────────────────────────────────────
# 1. WordPress 미디어 업로드
# ──────────────────────────────────────────────

def upload_to_wp_media(
    image_bytes: bytes,
    filename: str,
    alt_text: str = "",
    mime_type: str = "image/jpeg",
) -> Optional[int]:
    """
    이미지 바이트를 WordPress 미디어 라이브러리에 업로드합니다.

    Returns:
        media_id (int) — 성공 시 WordPress media ID
        None           — 실패 시 (파이프라인 중단 없이 경고만)
    """
    site_url  = os.getenv("WORDPRESS_SITE_URL", "").strip().rstrip("/")
    username  = os.getenv("WORDPRESS_USERNAME", "").strip()
    password  = os.getenv("WORDPRESS_PASSWORD", "").strip()

    if not all([site_url, username, password]):
        logger.warning("⚠ [images] WordPress 환경변수 누락 — 이미지 업로드 건너뜀")
        return None

    if not site_url.startswith("http"):
        site_url = f"http://{site_url}"

    api_url = f"{site_url}/wp-json/wp/v2/media"

    try:
        resp = requests.post(
            api_url,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": mime_type,
            },
            data=image_bytes,
            auth=(username, password),
            timeout=30,
        )
        resp.raise_for_status()
        media_id = resp.json().get("id")
        logger.info(f"✅ [images] 미디어 업로드 완료 | media_id={media_id} | {filename}")

        # alt_text 설정
        if alt_text and media_id:
            requests.post(
                f"{api_url}/{media_id}",
                json={"alt_text": alt_text},
                auth=(username, password),
                timeout=10,
            )

        return media_id

    except Exception as e:
        logger.warning(f"⚠ [images] 미디어 업로드 실패 (비치명): {e}")
        return None


# ──────────────────────────────────────────────
# 2. Post 1 — Unsplash 대표 이미지
# ──────────────────────────────────────────────

# 매크로 테마 키워드 → Unsplash 영문 검색어 매핑
_THEME_KEYWORD_MAP = {
    "금리":         "interest rate federal reserve",
    "인플레":       "inflation economy",
    "인플레이션":   "inflation economy",
    "달러":         "dollar currency exchange",
    "환율":         "currency exchange rate",
    "반도체":       "semiconductor chip technology",
    "ai":           "artificial intelligence technology",
    "에너지":       "energy oil market",
    "중국":         "china economy market",
    "무역":         "trade global economy",
    "채권":         "bonds financial market",
    "주식":         "stock market financial",
    "경기":         "economy recession growth",
    "gdp":          "economy growth gdp",
    "연준":         "federal reserve monetary policy",
    "물가":         "inflation consumer prices",
    "공급망":       "supply chain logistics",
    "테크":         "technology stock market",
    "바이오":       "biotech pharmaceutical",
    "자동차":       "automotive electric vehicle",
}

_UNSPLASH_FALLBACK_QUERY = "financial market economy"


def _theme_to_query(theme: str) -> str:
    """한국어 테마 문자열 → Unsplash 검색 키워드"""
    theme_lower = theme.lower()
    for kor, eng in _THEME_KEYWORD_MAP.items():
        if kor in theme_lower:
            return eng
    # 매핑 없으면 테마 원문 그대로 (영문 테마에 대응)
    return theme if theme else _UNSPLASH_FALLBACK_QUERY


def fetch_unsplash_image(theme: str) -> Optional[bytes]:
    """
    Unsplash API에서 테마 관련 이미지를 가져옵니다.

    Args:
        theme: Post 1의 theme 문자열 (한국어 또는 영문)

    Returns:
        JPEG 바이트 또는 None (실패 시)
    """
    access_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
    if not access_key:
        logger.warning("⚠ [images] UNSPLASH_ACCESS_KEY 미설정 — 대표 이미지 건너뜀")
        return None

    query = _theme_to_query(theme)
    logger.info(f"  [images] Unsplash 검색: theme='{theme}' → query='{query}'")

    try:
        resp = requests.get(
            "https://api.unsplash.com/photos/random",
            params={
                "query":       query,
                "orientation": "landscape",
                "content_filter": "high",
            },
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # regular 사이즈 (1080px) 다운로드
        image_url = data.get("urls", {}).get("regular")
        if not image_url:
            logger.warning("⚠ [images] Unsplash 응답에 image URL 없음")
            return None

        img_resp = requests.get(image_url, timeout=20)
        img_resp.raise_for_status()
        logger.info(f"✅ [images] Unsplash 이미지 다운로드 완료 ({len(img_resp.content):,} bytes)")
        return img_resp.content

    except Exception as e:
        logger.warning(f"⚠ [images] Unsplash 이미지 조회 실패 (비치명): {e}")
        return None


# ──────────────────────────────────────────────
# 3. Post 2 — 종목 1주 차트 이미지
# ──────────────────────────────────────────────

def generate_ticker_chart(ticker: str, name: str = "") -> Optional[bytes]:
    """
    yfinance로 1주(7일) OHLCV 데이터를 받아 matplotlib 차트를 생성합니다.

    Args:
        ticker: Yahoo Finance 형식 (예: "005930.KS", "AAPL")
        name:   종목명 (차트 제목용)

    Returns:
        PNG 바이트 또는 None (실패 시)
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # 헤드리스 환경 대응
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import yfinance as yf

    except ImportError as e:
        logger.warning(f"⚠ [images] 차트 패키지 없음: {e} — pip install matplotlib yfinance")
        return None

    try:
        logger.info(f"  [images] 차트 생성: {ticker} ({name})")
        df = yf.download(ticker, period="7d", interval="1d", progress=False, auto_adjust=True)

        if df.empty or len(df) < 2:
            logger.warning(f"⚠ [images] {ticker} 데이터 부족 ({len(df)}행) — 차트 건너뜀")
            return None

        close = df["Close"].squeeze()
        dates = close.index

        # 수익률 계산
        ret_pct = (close.iloc[-1] / close.iloc[0] - 1) * 100
        color   = "#C0392B" if ret_pct < 0 else "#27AE60"

        # ── 차트 스타일 (Macromalt 에디토리얼 팔레트) ──
        fig, ax = plt.subplots(figsize=(10, 5.25))  # 1200×630 비율
        fig.patch.set_facecolor("#FAFAF8")
        ax.set_facecolor("#FAFAF8")

        ax.plot(dates, close, color=color, linewidth=2.5, solid_capstyle="round")
        ax.fill_between(dates, close, close.min() * 0.998, alpha=0.08, color=color)

        # 축 스타일
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.tick_params(axis="both", labelsize=9, colors="#555555")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{x:,.0f}")
        )
        ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)

        # 제목
        label = name if name else ticker
        sign  = "+" if ret_pct >= 0 else ""
        ax.set_title(
            f"{label}  |  1주 수익률  {sign}{ret_pct:.2f}%",
            fontsize=13, fontweight="bold", color="#1A1A1A",
            pad=14, loc="left",
        )

        # 최고/최저 마커
        ax.annotate(
            f"고: {close.max():,.0f}",
            xy=(dates[close.values.argmax()], close.max()),
            xytext=(5, 8), textcoords="offset points",
            fontsize=8, color="#555555",
        )
        ax.annotate(
            f"저: {close.min():,.0f}",
            xy=(dates[close.values.argmin()], close.min()),
            xytext=(5, -14), textcoords="offset points",
            fontsize=8, color="#555555",
        )

        fig.tight_layout(pad=1.5)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        chart_bytes = buf.read()

        logger.info(f"✅ [images] 차트 생성 완료: {ticker} ({len(chart_bytes):,} bytes)")
        return chart_bytes

    except Exception as e:
        logger.warning(f"⚠ [images] 차트 생성 실패 (비치명): {e}")
        return None


# ──────────────────────────────────────────────
# 4. 파이프라인 헬퍼
# ──────────────────────────────────────────────

def attach_post1_image(theme: str) -> Optional[int]:
    """
    Post 1(심층분석)용: Unsplash 이미지 다운로드 → WP 미디어 업로드 → media_id 반환
    실패해도 None을 반환하며 파이프라인을 중단하지 않음.
    """
    img_bytes = fetch_unsplash_image(theme)
    if not img_bytes:
        return None
    safe_theme = "".join(c if c.isalnum() or c in "-_" else "_" for c in theme)[:40]
    return upload_to_wp_media(img_bytes, f"macromalt_{safe_theme}.jpg", alt_text=theme)


def attach_post2_image(picks: list) -> Optional[int]:
    """
    Post 2(캐시의 픽)용: 첫 번째 ticker 차트 생성 → WP 미디어 업로드 → media_id 반환
    실패해도 None을 반환하며 파이프라인을 중단하지 않음.
    """
    if not picks:
        logger.warning("⚠ [images] picks 비어있음 — 차트 건너뜀")
        return None

    first = picks[0]
    ticker = first.get("ticker", "")
    name   = first.get("name", "")

    if not ticker:
        logger.warning("⚠ [images] ticker 없음 — 차트 건너뜀")
        return None

    chart_bytes = generate_ticker_chart(ticker, name)
    if not chart_bytes:
        return None

    safe_ticker = ticker.replace(".", "_")
    return upload_to_wp_media(
        chart_bytes,
        f"macromalt_chart_{safe_ticker}.png",
        alt_text=f"{name} 1주 차트",
        mime_type="image/png",
    )
