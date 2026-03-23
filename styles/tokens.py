"""
styles/tokens.py — Macromalt WordPress 스타일 토큰 단일 진실 공급원 (SSOT)

Pre-Phase 17 스타일 분리 트랙.

이 파일이 모든 인라인 스타일 값의 단일 출처다.
- generator.py 는 이 토큰을 import 해 사용한다.
- WordPress child-theme CSS 는 동일 값을 CSS 변수/클래스로 미러링한다.
- Antigravity 는 분리 완료 후 이 파일과 styles/wordpress/*.css 만 수정한다.

변경 시 주의: generator.py 프롬프트 f-string 에 직접 주입되므로
실제 WordPress 출력 HTML 의 인라인 스타일이 바뀐다.
"""

# ─── 브랜드 색상 팔레트 ──────────────────────────────────────────────────────
COLOR_INK       = "#1a1a1a"   # 주요 텍스트 / 제목 / 테두리
COLOR_BODY      = "#333"      # 본문 텍스트
COLOR_MUTED     = "#555"      # 보조 텍스트 (출처 목록 등)
COLOR_SUBTLE    = "#999"      # 카테고리 레이블, 메타
COLOR_ACCENT    = "#b36b00"   # 브랜드 골드 (좌측 테두리 강조, 픽 박스)
COLOR_BG_LIGHT  = "#f4f4f4"   # H3 소제목 배경
COLOR_BG_WARM   = "#fffaf0"   # 픽 박스 배경 (warm cream)
COLOR_BG_QUOTE  = "#fffdf5"   # 인용구 배경
COLOR_BG_SOURCE = "#f9f9f9"   # 참고 출처 박스 배경
COLOR_RULE      = "#eee"      # <hr> 색상

# ─── 타이포그래피 ────────────────────────────────────────────────────────────
FONT_SIZE_H1    = "var(--fs-h1)"
FONT_SIZE_H3    = "var(--fs-h3)"
FONT_SIZE_BODY  = "var(--fs-body)"
FONT_SIZE_SMALL = "var(--fs-source)"
FONT_SIZE_META  = "var(--fs-meta)"

FONT_WEIGHT_BOLD   = "var(--fw-bold)"
FONT_WEIGHT_STRONG = "var(--fw-semibold)"

LINE_HEIGHT_BODY = "var(--lh-body)"
LINE_HEIGHT_LIST = "var(--lh-source)"

# ─── 스페이싱 ────────────────────────────────────────────────────────────────
MARGIN_H1_BOTTOM    = "30px"
MARGIN_H3_TOP       = "45px"
MARGIN_H3_BOTTOM    = "20px"
MARGIN_PARA_BOTTOM  = "16px"
MARGIN_HR           = "30px"
MARGIN_PICKS_V      = "30px"
MARGIN_SOURCE_TOP   = "30px"

PADDING_H3          = "12px 18px"
PADDING_PICKS       = "25px"
PADDING_BQ          = "10px 18px"
PADDING_SOURCE_BOX  = "14px 18px"
PADDING_SOURCE_UL   = "18px"   # padding-left

BORDER_H1_BOTTOM    = f"3px solid {COLOR_INK}"
BORDER_H3_LEFT      = f"6px solid {COLOR_INK}"
BORDER_PICKS_LEFT   = f"5px solid {COLOR_ACCENT}"
BORDER_BQ_LEFT      = f"4px solid {COLOR_ACCENT}"
BORDER_SOURCE_LEFT  = f"4px solid {COLOR_ACCENT}"
BORDER_SOURCE_RADIUS = "0 4px 4px 0"


# ═══════════════════════════════════════════════════════════════════════════════
# 인라인 스타일 토큰 — generator.py 프롬프트 / 후처리 함수 직접 참조
# ═══════════════════════════════════════════════════════════════════════════════

# ─── 기사 본문 요소 ──────────────────────────────────────────────────────────
H1_STYLE = (
    f"font-size:{FONT_SIZE_H1};font-weight:{FONT_WEIGHT_BOLD};color:{COLOR_INK};"
    f"margin:0 0 {MARGIN_H1_BOTTOM} 0;padding-bottom:14px;"
    f"border-bottom:{BORDER_H1_BOTTOM};line-height:1.3;"
)

H3_STYLE = (
    f"border-left:{BORDER_H3_LEFT};padding:{PADDING_H3};"
    f"background-color:{COLOR_BG_LIGHT};margin:{MARGIN_H3_TOP} 0 {MARGIN_H3_BOTTOM} 0;"
    f"color:{COLOR_INK};font-size:{FONT_SIZE_H3};"
)

P_STYLE = (
    f"font-size:{FONT_SIZE_BODY};line-height:{LINE_HEIGHT_BODY};"
    f"color:{COLOR_BODY};margin:0 0 {MARGIN_PARA_BOTTOM} 0;"
)

HR_STYLE = f"border:0;border-top:1px solid {COLOR_RULE};margin:{MARGIN_HR} 0;"

BQ_STYLE = (
    f"border-left:{BORDER_BQ_LEFT};margin:12px 0;"
    f"padding:{PADDING_BQ};background:{COLOR_BG_QUOTE};color:{COLOR_MUTED};"
)

UL_STYLE = f"margin:0.5em 0 0.8em 1.4em;padding:0;color:{COLOR_BODY};"
OL_STYLE = f"margin:0.5em 0 0.8em 1.4em;padding:0;color:{COLOR_BODY};"
LI_STYLE = f"font-size:{FONT_SIZE_BODY};line-height:{LINE_HEIGHT_LIST};margin:0.3em 0;"

STRONG_STYLE = f"font-weight:{FONT_WEIGHT_STRONG};color:{COLOR_INK};"
A_STYLE      = f"color:{COLOR_INK};text-decoration:underline;"

# ─── 픽 박스 (Post2 종목 섹션) ───────────────────────────────────────────────
PICKS_DIV_STYLE = (
    f"padding:{PADDING_PICKS};background-color:{COLOR_BG_WARM};"
    f"border-left:{BORDER_PICKS_LEFT};margin:{MARGIN_PICKS_V} 0;"
)

# ─── 참고 출처 박스 (_format_source_section) ─────────────────────────────────
SOURCE_BOX_STYLE = (
    f"background:{COLOR_BG_SOURCE};border-left:{BORDER_SOURCE_LEFT};"
    f"padding:{PADDING_SOURCE_BOX};margin:{MARGIN_SOURCE_TOP} 0 0 0;"
    f"border-radius:{BORDER_SOURCE_RADIUS};"
)
SOURCE_H_STYLE   = (
    f"font-size:{FONT_SIZE_BODY};font-weight:{FONT_WEIGHT_STRONG};"
    f"color:{COLOR_MUTED};margin:0 0 8px 0;"
)
SOURCE_CAT_STYLE = f"font-size:{FONT_SIZE_BODY};color:{COLOR_SUBTLE};margin:6px 0 2px 0;"
SOURCE_UL_STYLE  = f"margin:0;padding-left:{PADDING_SOURCE_UL};"
SOURCE_LI_STYLE  = (
    f"font-size:{FONT_SIZE_BODY};line-height:{LINE_HEIGHT_LIST};"
    f"color:{COLOR_MUTED};margin:2px 0;"
)

# ─── 하위 호환 별칭 (generator.py 기존 변수명 _XXX_STYLE 매핑) ───────────────
# generator.py 의 _H1_STYLE, _H3_STYLE 등 언더스코어 접두어 변수들을 그대로 유지해
# import 교체 후 다른 코드 변경 없이 동작하도록 한다.
_H1_STYLE        = H1_STYLE
_H3_STYLE        = H3_STYLE
_P_STYLE         = P_STYLE
_HR_STYLE        = HR_STYLE
_PICKS_DIV_STYLE = PICKS_DIV_STYLE
_STRONG_STYLE    = STRONG_STYLE
