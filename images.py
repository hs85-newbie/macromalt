"""
macromalt 자동화 시스템 - 이미지 처리 모듈
=====================================================
Post 1 (심층분석): Unsplash API → 테마 키워드 대표 이미지
Post 2 (캐시의 픽): yfinance 1주 데이터 → matplotlib 차트 이미지 (본문 삽입 + 대표 이미지)
공용: WordPress 미디어 라이브러리 업로드
"""

import io
import logging
import os
from typing import Optional, Tuple

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
) -> Tuple[Optional[int], Optional[str]]:
    """
    이미지 바이트를 WordPress 미디어 라이브러리에 업로드합니다.

    Returns:
        (media_id, source_url) — 성공 시
        (None, None)           — 실패 시 (파이프라인 중단 없음)
    """
    site_url = os.getenv("WORDPRESS_SITE_URL", "").strip().rstrip("/")
    username = os.getenv("WORDPRESS_USERNAME", "").strip()
    password = os.getenv("WORDPRESS_PASSWORD", "").strip()

    if not all([site_url, username, password]):
        logger.warning("⚠ [images] WordPress 환경변수 누락 — 이미지 업로드 건너뜀")
        return None, None

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
        data       = resp.json()
        media_id   = data.get("id")
        source_url = data.get("source_url", "")
        logger.info(f"✅ [images] 미디어 업로드 완료 | media_id={media_id} | {filename}")

        if alt_text and media_id:
            requests.post(
                f"{api_url}/{media_id}",
                json={"alt_text": alt_text},
                auth=(username, password),
                timeout=10,
            )

        return media_id, source_url

    except Exception as e:
        logger.warning(f"⚠ [images] 미디어 업로드 실패 (비치명): {e}")
        return None, None


# ──────────────────────────────────────────────
# 2. Post 1 — Unsplash 대표 이미지
# ──────────────────────────────────────────────

_THEME_KEYWORD_MAP = {
    "금리":       "interest rate federal reserve",
    "인플레":     "inflation economy",
    "달러":       "dollar currency exchange",
    "환율":       "currency exchange rate",
    "반도체":     "semiconductor chip technology",
    "ai":         "artificial intelligence technology",
    "에너지":     "energy oil market",
    "중동":       "middle east oil geopolitics",
    "지정학":     "geopolitics world map",
    "중국":       "china economy market",
    "무역":       "trade global economy",
    "채권":       "bonds financial market",
    "주식":       "stock market financial",
    "경기":       "economy recession growth",
    "gdp":        "economy growth gdp",
    "연준":       "federal reserve monetary policy",
    "물가":       "inflation consumer prices",
    "공급망":     "supply chain logistics",
    "테크":       "technology stock market",
    "바이오":     "biotech pharmaceutical",
    "자동차":     "automotive electric vehicle",
    "화장품":     "beauty cosmetics market",
    "미국":       "united states economy market",
    "한국":       "korea economy finance",
    "부동산":     "real estate market",
    "원자재":     "commodities raw materials",
}

_UNSPLASH_FALLBACK_QUERY = "financial market economy"


def _theme_to_query(theme: str) -> str:
    """한국어 테마 문자열 → Unsplash 영문 검색어 (항상 영문 반환)"""
    theme_lower = theme.lower()
    for kor, eng in _THEME_KEYWORD_MAP.items():
        if kor in theme_lower:
            return eng
    return _UNSPLASH_FALLBACK_QUERY


def fetch_unsplash_image(theme: str) -> Tuple[Optional[bytes], str]:
    """
    Unsplash API에서 테마 관련 이미지를 가져옵니다.
    Returns: (JPEG 바이트, 출처 문자열) 또는 (None, "")
    """
    access_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
    if not access_key:
        logger.warning("⚠ [images] UNSPLASH_ACCESS_KEY 미설정 — 대표 이미지 건너뜀")
        return None, ""

    query = _theme_to_query(theme)
    logger.info(f"  [images] Unsplash 검색: '{theme[:40]}...' → query='{query}'")

    try:
        resp = requests.get(
            "https://api.unsplash.com/photos/random",
            params={"query": query, "orientation": "landscape", "content_filter": "high"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        image_url = data.get("urls", {}).get("regular")
        if not image_url:
            logger.warning("⚠ [images] Unsplash 응답에 image URL 없음")
            return None, ""

        # 사진작가 정보 추출
        photographer = data.get("user", {}).get("name", "Unsplash")
        photo_link   = data.get("links", {}).get("html", "https://unsplash.com")
        attribution  = f'Unsplash / <a href="{photo_link}" target="_blank" rel="noopener">{photographer}</a>'

        img_resp = requests.get(image_url, timeout=20)
        img_resp.raise_for_status()
        logger.info(f"✅ [images] Unsplash 이미지 다운로드 완료 ({len(img_resp.content):,} bytes) — {photographer}")
        return img_resp.content, attribution

    except Exception as e:
        logger.warning(f"⚠ [images] Unsplash 이미지 조회 실패 (비치명): {e}")
        return None, ""


# ──────────────────────────────────────────────
# 3. Post 2 — 종목 1주 차트 이미지
# ──────────────────────────────────────────────

_KOREAN_FONT_PATHS = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",   # macOS
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",  # macOS fallback
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",      # Ubuntu
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Ubuntu fallback
]

def _setup_korean_font() -> None:
    """한글 폰트를 matplotlib에 직접 등록하고 설정합니다 (파일 경로 기반, 확실한 방법)."""
    import os as _os
    import matplotlib.font_manager as fm

    for path in _KOREAN_FONT_PATHS:
        if _os.path.exists(path):
            try:
                fm.fontManager.addfont(path)
                prop = fm.FontProperties(fname=path)
                import matplotlib
                matplotlib.rcParams["font.family"] = prop.get_name()
                matplotlib.rcParams["axes.unicode_minus"] = False
                logger.info(f"  [images] 한글 폰트 설정: {prop.get_name()} ({path})")
                return
            except Exception as e:
                logger.warning(f"  [images] 폰트 로드 실패 ({path}): {e}")

    logger.warning("  [images] 한글 폰트 없음 — 폰트 깨짐 가능")


def generate_ticker_chart(ticker: str, name: str = "") -> Optional[bytes]:
    """
    yfinance 1주 데이터 → matplotlib 라인 차트 PNG 생성.
    Returns: PNG 바이트 또는 None
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import yfinance as yf

        _setup_korean_font()

    except ImportError as e:
        logger.warning(f"⚠ [images] 차트 패키지 없음: {e}")
        return None

    try:
        logger.info(f"  [images] 차트 생성: {ticker} ({name})")
        df = yf.download(ticker, period="7d", interval="1d", progress=False, auto_adjust=True)

        if df.empty or len(df) < 2:
            logger.warning(f"⚠ [images] {ticker} 데이터 부족 ({len(df)}행)")
            return None

        close   = df["Close"].squeeze()
        dates   = close.index
        ret_pct = (close.iloc[-1] / close.iloc[0] - 1) * 100
        color   = "#C0392B" if ret_pct < 0 else "#27AE60"
        label   = name if name else ticker
        sign    = "+" if ret_pct >= 0 else ""

        fig, ax = plt.subplots(figsize=(10, 5.25))
        fig.patch.set_facecolor("#FAFAF8")
        ax.set_facecolor("#FAFAF8")

        ax.plot(dates, close, color=color, linewidth=2.5, solid_capstyle="round")
        ax.fill_between(dates, close, close.min() * 0.998, alpha=0.08, color=color)

        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.tick_params(axis="both", labelsize=9, colors="#555555")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)

        ax.set_title(
            f"{label}  |  1주 수익률  {sign}{ret_pct:.2f}%",
            fontsize=13, fontweight="bold", color="#1A1A1A", pad=14, loc="left",
        )
        ax.annotate(
            f"고: {close.max():,.0f}",
            xy=(dates[close.values.argmax()], close.max()),
            xytext=(5, 8), textcoords="offset points", fontsize=8, color="#555555",
        )
        ax.annotate(
            f"저: {close.min():,.0f}",
            xy=(dates[close.values.argmin()], close.min()),
            xytext=(5, -14), textcoords="offset points", fontsize=8, color="#555555",
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
# 4. 본문 내 차트 삽입
# ──────────────────────────────────────────────

def inject_chart_into_content(content: str, img_url: str, alt_text: str = "") -> str:
    """
    Post 2 본문에 차트 이미지를 삽입합니다.
    첫 번째 <h2> 직전에 삽입 (없으면 본문 맨 앞).
    """
    import re

    img_html = (
        f'\n<figure class="mm-chart-figure" style="margin:2em 0;text-align:center;">'
        f'<img src="{img_url}" alt="{alt_text}" style="max-width:100%;height:auto;border:1px solid #eee;" />'
        f'<figcaption style="font-size:11px;color:#888;margin-top:6px;">'
        f'{alt_text} &nbsp;|&nbsp; [출처: Yahoo Finance]'
        f'</figcaption>'
        f'</figure>\n'
    )

    # 첫 번째 </h2> 직후에 삽입 (메인 픽 제목 바로 아래)
    match = re.search(r"</h2>", content)
    if match:
        pos = match.end()
        return content[:pos] + img_html + content[pos:]

    # <h2> 없으면 본문 맨 앞
    return img_html + content


# ──────────────────────────────────────────────
# 5. 파이프라인 헬퍼
# ──────────────────────────────────────────────

def attach_post1_image(theme: str) -> Tuple[Optional[int], str]:
    """
    Post 1(심층분석): Unsplash → WP 업로드 → (media_id, attribution) 반환
    attribution: 본문 하단 출처 표기용 HTML 문자열
    """
    img_bytes, attribution = fetch_unsplash_image(theme)
    if not img_bytes:
        return None, ""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in theme)[:40]
    safe_ascii = safe.encode("ascii", errors="ignore").decode() or "theme"
    media_id, _ = upload_to_wp_media(img_bytes, f"macromalt_{safe_ascii}.jpg", alt_text=theme)
    return media_id, attribution


def attach_post2_image(picks: list) -> Tuple[Optional[int], Optional[str]]:
    """
    Post 2(캐시의 픽): 첫 번째 ticker 차트 → WP 업로드 → (media_id, img_html) 반환
    img_html은 본문 삽입용 <figure> 태그.
    실패 시 (None, None) 반환.
    """
    if not picks:
        logger.warning("⚠ [images] picks 비어있음 — 차트 건너뜀")
        return None, None

    first  = picks[0]
    ticker = first.get("ticker", "")
    name   = first.get("name", "")

    if not ticker:
        logger.warning("⚠ [images] ticker 없음 — 차트 건너뜀")
        return None, None

    chart_bytes = generate_ticker_chart(ticker, name)
    if not chart_bytes:
        return None, None

    safe_ticker = ticker.replace(".", "_")
    alt_text    = f"{name} 1주 차트"
    media_id, source_url = upload_to_wp_media(
        chart_bytes,
        f"macromalt_chart_{safe_ticker}.png",
        alt_text=alt_text,
        mime_type="image/png",
    )

    if not source_url:
        return media_id, None

    img_html = inject_chart_into_content("", source_url, alt_text).strip()
    return media_id, img_html
