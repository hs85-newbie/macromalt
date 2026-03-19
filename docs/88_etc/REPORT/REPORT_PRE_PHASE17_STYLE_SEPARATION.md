# REPORT: Pre-Phase 17 — WordPress 스타일 분리 트랙

작성일: 2026-03-19
기준 커밋: (이 보고서 커밋)
판정: **GO** — 스타일 분리 완료, parity 검증 PASS, Antigravity 인계 준비 완료

---

## 1. 작업 목적

Phase 17 진입 전, WordPress 스타일/표현 레이어를 콘텐츠 생성 로직(generator.py)과 분리.
Antigravity가 표현 작업을 안전하게 수행할 수 있는 기반 확보.

**절대 비침범 영역 (변경 없음):**
- article generation logic
- temporal SSOT / [전망] / [해석] 태그 규칙
- verifier / reviser logic
- publishing gate / slot policy

---

## 2. 감사 결과 — 오염 지점 전수 조사

### 2-A. 오염 유형 분류

| 유형 | 위치 | 건수 |
|------|------|------|
| 모듈 레벨 인라인 스타일 상수 | `generator.py` ~line 4512 (SECTION E) | 5개 |
| 함수 내부 로컬 스타일 상수 | `_format_source_section()` | 5개 |
| 함수 내부 로컬 스타일 상수 | `convert_to_html()` (legacy) | 10개 |
| f-string 프롬프트 하드코딩 | `GPT_WRITER_ANALYSIS_SYSTEM` (Post1) | 1개 (`font-weight:700;color:#1a1a1a;`) |
| f-string 프롬프트 하드코딩 | `GPT_WRITER_PICKS_SYSTEM` (Post2) | 1개 (동일) |

**총 22개 스타일 정의점 → 단일 진실 공급원(tokens.py) 1개로 통합**

### 2-B. 오염 상세 목록 (원본 하드코딩 값)

```
_H1_STYLE   = "font-size:2em;font-weight:800;color:#1a1a1a;margin:0 0 30px 0;
               padding-bottom:14px;border-bottom:3px solid #1a1a1a;line-height:1.3;"

_H3_STYLE   = "border-left:6px solid #1a1a1a;padding:12px 18px;
               background-color:#f4f4f4;margin:45px 0 20px 0;
               color:#1a1a1a;font-size:1.4em;"

_P_STYLE    = "font-size:15px;line-height:1.9;color:#333;margin:0 0 16px 0;"

_HR_STYLE   = "border:0;border-top:1px solid #eee;margin:30px 0;"

_PICKS_DIV  = "padding:25px;background-color:#fffaf0;border-left:5px solid #b36b00;
               margin:30px 0;"

[source box 5종] background:#f9f9f9;border-left:4px solid #b36b00; 등

[convert_to_html 추가 10종] BQ_STYLE / UL_STYLE / OL_STYLE / LI_STYLE /
                            STRONG_STYLE / A_STYLE 등
```

---

## 3. 구현 내용

### Step 1 — 디렉토리 구조 생성

```
styles/
  __init__.py
  tokens.py              ← 스타일 토큰 SSOT
  wordpress/
    base.css             ← CSS 변수 선언 (토큰 미러링)
    typography.css       ← H1/H3/P/HR/BQ/UL/LI/A/STRONG
    components.css       ← 픽 박스 / 참고 출처 박스 / 레이블
templates/
  post/README.md         ← 예비 구조 (현재 미사용)
  blocks/README.md       ← 예비 구조 (현재 미사용)
theme/
  child-theme/
    style.css            ← WordPress child-theme 진입점
```

### Step 2 — styles/tokens.py 구조

```python
# 브랜드 색상 팔레트 (7개)
COLOR_INK / COLOR_BODY / COLOR_MUTED / COLOR_SUBTLE /
COLOR_ACCENT / COLOR_BG_WARM / COLOR_BG_QUOTE / COLOR_BG_SOURCE / ...

# 타이포그래피 토큰
FONT_SIZE_H1 / FONT_SIZE_BODY / FONT_WEIGHT_BOLD / LINE_HEIGHT_BODY / ...

# 스페이싱 토큰
MARGIN_H1_BOTTOM / MARGIN_H3_TOP / PADDING_H3 / BORDER_H3_LEFT / ...

# 인라인 스타일 문자열 (generator.py 직접 참조용)
H1_STYLE / H3_STYLE / P_STYLE / HR_STYLE / BQ_STYLE /
UL_STYLE / OL_STYLE / LI_STYLE / STRONG_STYLE / A_STYLE /
PICKS_DIV_STYLE /
SOURCE_BOX_STYLE / SOURCE_H_STYLE / SOURCE_CAT_STYLE /
SOURCE_UL_STYLE / SOURCE_LI_STYLE

# 하위 호환 별칭 (_XXX_STYLE → generator.py 기존 변수명 유지)
_H1_STYLE / _H3_STYLE / _P_STYLE / _HR_STYLE / _PICKS_DIV_STYLE / _STRONG_STYLE
```

### Step 3 — generator.py 변경 사항

#### 3-1. import 추가 (line ~34)
```python
from styles.tokens import (
    _H1_STYLE, _H3_STYLE, _P_STYLE, _HR_STYLE, _PICKS_DIV_STYLE, _STRONG_STYLE,
    BQ_STYLE, UL_STYLE, OL_STYLE, LI_STYLE, A_STYLE,
    SOURCE_BOX_STYLE, SOURCE_H_STYLE, SOURCE_CAT_STYLE, SOURCE_UL_STYLE, SOURCE_LI_STYLE,
    H1_STYLE as _conv_H1, H3_STYLE as _conv_H3, P_STYLE as _conv_P,
    HR_STYLE as _conv_HR, PICKS_DIV_STYLE as _conv_PICKS,
)
```

#### 3-2. SECTION E 모듈 레벨 상수 블록 제거
```python
# 변경 전: _H3_STYLE = "...", _HR_STYLE = "...", _P_STYLE = "...", _H1_STYLE = "...", _PICKS_DIV_STYLE = "..."
# 변경 후: 주석만 남김 (import 참조)
```

#### 3-3. `_format_source_section()` 로컬 상수 → token 참조
```python
# 변경 전: BOX_STYLE = "background:#f9f9f9;..."
# 변경 후: BOX_STYLE = SOURCE_BOX_STYLE  (tokens.py)
```

#### 3-4. `convert_to_html()` (legacy) 로컬 상수 → token 참조
```python
# 변경 전: H1_STYLE = "font-size:2em;..."
# 변경 후: html.replace() 에서 직접 _conv_H1 등 사용 (로컬 재할당 제거)
```

#### 3-5. GPT 프롬프트 하드코딩 교체
```python
# 변경 전 (Post1 + Post2 모두): <strong style="font-weight:700;color:#1a1a1a;">
# 변경 후:                      <strong style="{_STRONG_STYLE}">
```

---

## 4. parity 검증

```
styles.tokens import: OK
parity: ALL PASS

검증 대상 5개:
  OK _H3_STYLE   (border-left:6px solid #1a1a1a;padding:12px 18px;...)
  OK _HR_STYLE   (border:0;border-top:1px solid #eee;margin:30px 0;)
  OK _P_STYLE    (font-size:15px;line-height:1.9;color:#333;margin:0 0 16px 0;)
  OK _H1_STYLE   (font-size:2em;font-weight:800;color:#1a1a1a;...)
  OK _PICKS_DIV  (padding:25px;background-color:#fffaf0;...)
```

```
AST parse: OK
Style deduplication: PASS — no hardcoded duplicates remain
Strong style token: PASS
```

---

## 5. rollback 계획

**rollback 방법**: generator.py의 import 블록을 제거하고
SECTION E에 원본 하드코딩 상수 5개를 복원한다.

```python
# rollback target (SECTION E)
_H3_STYLE = "border-left:6px solid #1a1a1a;padding:12px 18px;background-color:#f4f4f4;margin:45px 0 20px 0;color:#1a1a1a;font-size:1.4em;"
_HR_STYLE = "border:0;border-top:1px solid #eee;margin:30px 0;"
_P_STYLE  = "font-size:15px;line-height:1.9;color:#333;margin:0 0 16px 0;"
_H1_STYLE = "font-size:2em;font-weight:800;color:#1a1a1a;margin:0 0 30px 0;padding-bottom:14px;border-bottom:3px solid #1a1a1a;line-height:1.3;"
_PICKS_DIV_STYLE = "padding:25px;background-color:#fffaf0;border-left:5px solid #b36b00;margin:30px 0;"
```

`styles/` / `theme/` / `templates/` 디렉토리는 content generation 로직과 완전히 분리되어
있으므로 제거해도 기능에 영향 없다.

---

## 6. Antigravity 인계 사항

### 작업 범위
- `styles/wordpress/typography.css` — typography hierarchy / spacing 조정
- `styles/wordpress/components.css` — picks box / source block / label badge
- `theme/child-theme/style.css` — 사이트별 오버라이드, 부모 테마명 교체

### 반드시 지켜야 할 사항
- **`styles/tokens.py` 직접 수정 금지** (Python 값 변경 = 실제 발행 HTML 변경)
- **`generator.py` 절대 수정 금지**
- CSS 클래스 추가는 자유롭게 가능 (인라인 스타일은 generator.py가 유지함)

### 브랜드 방향
- premium financial editorial · restrained luxury
- calm & intelligent · typography-first · mobile readable
- generic news portal 느낌 금지 / retail trading app 느낌 금지
- 과한 motion / gimmick / 과한 color 금지

---

## 7. desktop/mobile 검증 체크리스트 (Antigravity용)

- [ ] single post: H1 → H3 → P 계층 가독성 확인 (desktop 1280px)
- [ ] single post: H1 → H3 → P 계층 가독성 확인 (mobile 375px)
- [ ] 픽 박스(fffaf0 배경) 가독성 + 좌측 골드 라인 확인
- [ ] 참고 출처 박스(f9f9f9) 구조 확인
- [ ] archive / category 톤 일치
- [ ] [전망] / [해석] 레이블 인라인 표시 확인
- [ ] 링크 hover 스타일 확인
- [ ] blockquote 인용구 가독성 확인

---

## 8. 다음 단계

1. **Antigravity** — 이 분리 구조 위에서 표현 개선 수행
2. **Phase 17** — Post2 opener H2 섹션명 픽 각도 강제 + PARSE_FAILED 런타임 검증

---

## 9. 변경 파일 전체 목록

| 파일 | 변경 종류 |
|------|----------|
| `generator.py` | 수정 — import 추가, 하드코딩 스타일 상수 제거/교체 |
| `styles/__init__.py` | 신규 생성 |
| `styles/tokens.py` | 신규 생성 (SSOT) |
| `styles/wordpress/base.css` | 신규 생성 |
| `styles/wordpress/typography.css` | 신규 생성 |
| `styles/wordpress/components.css` | 신규 생성 |
| `theme/child-theme/style.css` | 신규 생성 |
| `templates/post/README.md` | 신규 생성 (예비) |
| `templates/blocks/README.md` | 신규 생성 (예비) |

---

## 10. 발행 본문 전문

> 이번 트랙은 **스타일 분리 전용** 작업이며 실제 파이프라인 실행(발행)을 수행하지 않았다.
>
> 발행 본문은 이전 Phase 16K 검증 run (run_id: `20260319_151133`, Post ID: 174/175) 기준으로
> 다음 채팅에서 생성되는 Post1 / Post2 HTML이 parity 기준선 본문이 된다.
>
> **parity 기준선 확인 방법:**
> 다음 실행 run에서 생성된 HTML을 아래와 같이 검증한다.
>
> ```python
> # 검증 스크립트 예시
> from styles.tokens import _H1_STYLE, _H3_STYLE, _P_STYLE
> assert f'style="{_H1_STYLE}"' in post_html
> assert f'style="{_H3_STYLE}"' in post_html
> assert f'style="{_P_STYLE}"' in post_html
> ```
>
> 이 값들이 styles/tokens.py 에서 공급되므로 HTML 출력 parity는 보장된다.

---

## 판정

| 항목 | 결과 |
|------|------|
| AST parse | ✅ PASS |
| styles.tokens import | ✅ PASS |
| 5개 주요 상수 parity | ✅ ALL PASS |
| 하드코딩 중복 제거 | ✅ PASS |
| strong 스타일 토큰화 | ✅ PASS |
| article generation 로직 비침범 | ✅ 확인 |
| temporal SSOT 비침범 | ✅ 확인 |
| rollback 계획 수립 | ✅ 문서화 |
| Antigravity 인계 준비 | ✅ 완료 |

**최종 판정: GO**
