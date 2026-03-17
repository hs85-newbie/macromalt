# STYLE SEPARATION STRUCTURE DESIGN

작성일: 2026-03-17
기준 커밋: 2dd1669
작성 목적: Python 로직, HTML 템플릿, CSS 스타일 분리 — Antigravity/Codex가 스타일 레이어만 안전하게 수정할 수 있는 기반 마련

---

## 1. Current-State Audit

### 1-A. 스타일 관련 코드가 섞인 위치

#### `generator.py` — 주요 오염원 (총 inline style 사용 약 32건)

| 위치 | 구조 | 문제 |
|------|------|------|
| ~line 3561–3566 | `_format_source_section()` 내부 상수 — `BOX_STYLE`, `H_STYLE`, `CAT_STYLE`, `UL_STYLE`, `LI_STYLE` | 참고 출처 박스의 CSS를 Python 함수 내부에 문자열 상수로 선언 |
| ~line 3646–3670 | `convert_to_html()` 내부 상수 — `H1_STYLE`, `SUB_H_STYLE`, `P_STYLE`, `HR_STYLE`, `BQ_STYLE`, `UL_STYLE`, `OL_STYLE`, `LI_STYLE`, `STRONG_STYLE`, `A_STYLE`, `PICKS_DIV_STYLE` | 마크다운→HTML 변환 시 모든 태그에 `style=` 직접 주입 |
| ~line 3711–3727 | 모듈 레벨 상수 — `_H3_STYLE`, `_HR_STYLE`, `_P_STYLE`, `_H1_STYLE`, `_PICKS_DIV_STYLE` | **GPT 프롬프트 문자열 내부에 직접 삽입**됨 (`{_H1_STYLE}` f-string) |
| ~line 3891–3895 | GPT Step2a 프롬프트 내 HTML 마크업 지시문 | LLM에게 `<h1 style="...">` 형태로 직접 생성 지시 |
| ~line 4023–4037 | GPT Step2b 프롬프트 내 HTML 마크업 지시문 | 동일 문제 — `_PICKS_DIV_STYLE` 포함 |

#### `publisher.py` — 스타일 관련 코드 없음
- HTML/CSS 관심사 전혀 없음. `_strip_leading_h1()`만 존재 (구조 처리, 스타일 아님).

#### `main.py` — 스타일 관련 코드 없음
- 파이프라인 오케스트레이션만 담당. 스타일 관심사 없음.

---

### 1-B. 오염 구조 분류

**타입 A — 후처리 함수 내 CSS 상수 (`_format_source_section`, `convert_to_html`)**
- Python이 HTML 문자열을 직접 조립할 때 `style=` 속성을 하드코딩
- 스타일 변경 시 Python 함수 본문을 직접 수정해야 함

**타입 B — 모듈 레벨 CSS 상수 → LLM 프롬프트 삽입 (`_H1_STYLE` 등)**
- CSS 값이 f-string으로 LLM 지시 프롬프트 안에 들어감
- "GPT가 생성하는 HTML에 inline style을 포함시키는" 방식
- **스타일 변경 = LLM 프롬프트 변경 = 생성 로직 수정**이라는 결합이 발생

**타입 C — 참고 출처 섹션 HTML 조립 (`_rebuild` 내부)**
- Python이 `<div>`, `<h3>`, `<ul>`, `<li>` 조합을 직접 f-string으로 조립
- 구조(레이아웃)와 스타일이 같은 함수 안에서 생성됨

---

### 1-C. Python에 영구히 남아야 할 것

| 항목 | 이유 |
|------|------|
| 발행 흐름 (publish_draft 호출) | 순수 데이터/인프라 로직 |
| `_strip_leading_h1()` | WP title 중복 제거 — 구조 처리 |
| `_format_source_section()`의 분류 로직 (broker/news/others 분류) | 데이터 분류 로직 |
| 게이트 판정, 스코어 집계 | 생성 파이프라인 |
| 시제 교정, 태그 제거 후처리 | 콘텐츠 품질 로직 |

---

## 2. Target Separation Architecture

```
macromalt/
├── generator.py            ← 기존: LLM 호출, 품질 검증, 후처리 (스타일 상수 제거 후)
├── main.py                 ← 변경 없음
├── publisher.py            ← 변경 없음
├── scraper.py              ← 변경 없음
│
├── styles/                 ← 신규 (CSS 책임 담당)
│   ├── tokens.py           ← CSS 토큰 딕셔너리 (단일 진실 공급원)
│   └── article.css         ← (선택적) WordPress 테마 확장용 실제 CSS — 나중 단계
│
└── templates/              ← 신규 (HTML 마크업 책임 담당)
    ├── source_box.html     ← 참고 출처 박스 템플릿
    ├── post1_structure.txt ← Post1 GPT 지시용 HTML 구조 지시문
    └── post2_structure.txt ← Post2 GPT 지시용 HTML 구조 지시문
```

### 역할 분리 원칙

| 레이어 | 파일 | 책임 | 수정 주체 |
|--------|------|------|-----------|
| 데이터 & 흐름 | `generator.py`, `main.py`, `publisher.py` | LLM 호출, 품질 검증, 발행 결정 | Claude Code |
| CSS 토큰 | `styles/tokens.py` | 색상, 폰트, 여백 값 (단일 진실 공급원) | Antigravity / Codex |
| HTML 구조 | `templates/` | 마크업 구조, 태그 배치 | Antigravity / Codex |
| 스타일 주입 | `styles/tokens.py` → `generator.py` import | Python이 토큰을 읽어 LLM 프롬프트 또는 HTML 조립에 삽입 | 자동 |

---

## 3. Template Strategy

### 3-A. `styles/tokens.py` — CSS 토큰 딕셔너리

현재 `generator.py`에 흩어진 CSS 상수를 단일 파일로 통합.

```python
# styles/tokens.py
# macromalt 스타일 토큰 — 단일 진실 공급원
# Antigravity / Codex는 이 파일만 수정한다.

STYLE = {
    # 타이포그래피
    "h1":       "font-size:2em;font-weight:800;color:#1a1a1a;margin:0 0 30px 0;padding-bottom:14px;border-bottom:3px solid #1a1a1a;line-height:1.3;",
    "h3":       "border-left:6px solid #1a1a1a;padding:12px 18px;background-color:#f4f4f4;margin:45px 0 20px 0;color:#1a1a1a;font-size:1.4em;",
    "p":        "font-size:15px;line-height:1.9;color:#333;margin:0 0 16px 0;",
    "hr":       "border:0;border-top:1px solid #eee;margin:30px 0;",
    "blockquote": "border-left:4px solid #b36b00;margin:12px 0;padding:10px 18px;background:#fffdf5;color:#555;",
    "ul":       "margin:0.5em 0 0.8em 1.4em;padding:0;color:#333;",
    "ol":       "margin:0.5em 0 0.8em 1.4em;padding:0;color:#333;",
    "li":       "font-size:15px;line-height:1.8;margin:0.3em 0;",
    "strong":   "font-weight:700;color:#1a1a1a;",
    "a":        "color:#1a1a1a;text-decoration:underline;",

    # 컴포넌트
    "picks_div":  "padding:25px;background-color:#fffaf0;border-left:5px solid #b36b00;margin:30px 0;",
    "source_box": "background:#f9f9f9;border-left:4px solid #b36b00;padding:14px 18px;margin:30px 0 0 0;border-radius:0 4px 4px 0;",
    "source_h":   "font-size:13px;font-weight:700;color:#555;margin:0 0 8px 0;",
    "source_cat": "font-size:12px;color:#999;margin:6px 0 2px 0;",
    "source_ul":  "margin:0;padding-left:18px;",
    "source_li":  "font-size:13px;line-height:1.8;color:#555;margin:2px 0;",
}
```

**사용 방법 (generator.py에서):**
```python
from styles.tokens import STYLE

# 기존: _H1_STYLE = "font-size:2em;..."
# 신규: STYLE["h1"] 참조
```

### 3-B. `templates/source_box.html` — 참고 출처 박스

현재 `_format_source_section()` 내 `_rebuild()`가 Python f-string으로 직접 조립하는 HTML을 외부 파일로 분리.

```html
<!-- templates/source_box.html -->
<!-- 변수: {style_box}, {style_h}, {style_cat}, {style_ul}, {style_li} -->
<!-- 변수: {broker_section}, {news_section}, {others_section} -->
<div style="{style_box}">
  <h3 style="{style_h}">참고 출처</h3>
  {broker_section}
  {news_section}
  {others_section}
</div>
```

Python은 템플릿을 읽어 `.format(**STYLE_VARS, **data_vars)`로 주입.

### 3-C. `templates/post1_structure.txt` / `post2_structure.txt` — LLM 구조 지시문

현재 GPT 프롬프트 내에 `{_H1_STYLE}` f-string으로 삽입되는 HTML 마크업 지시 블록을 외부 텍스트 파일로 분리.

```
# templates/post1_structure.txt
* 글 제목: <h1 style="{h1}">제목</h1>
* 소제목: <h3 style="{h3}">소제목</h3>
* 단락: <p style="{p}">내용</p>
* 구분선: <hr style="{hr}">
* 강조: <strong style="font-weight:700;color:#1a1a1a;">강조어</strong>
```

Python은 `templates/post1_structure.txt`를 읽어 `STYLE` 토큰으로 채운 뒤 GPT 프롬프트에 삽입.

### 3-D. 변수 주입 원칙

| 구분 | 담당 레이어 | 예시 |
|------|------------|------|
| 기사 데이터 (theme, title, picks) | Python → template | `{title}`, `{picks_count}` |
| CSS 스타일 값 | `styles/tokens.py` → template | `{h1}`, `{source_box}` |
| 구조적 HTML 마크업 | template 파일 자체 | `<div>`, `<h3>` 태그 |
| 절대 하드코딩 금지 in template | 개수, 날짜, 종목명 | — |

---

## 4. CSS Strategy

### 4-A. 분리 기준

| CSS 항목 | 현재 위치 | 이동 위치 |
|----------|-----------|-----------|
| 기사 본문 타이포그래피 (h1, h3, p) | `generator.py` 모듈 상수 | `styles/tokens.py` `STYLE` dict |
| 참고 출처 박스 스타일 | `_format_source_section()` 내부 | `styles/tokens.py` `STYLE` dict |
| 종목 픽 박스 스타일 | 모듈 상수 + `convert_to_html()` 내부 | `styles/tokens.py` `STYLE` dict |
| 링크, strong, hr | `convert_to_html()` 내부 | `styles/tokens.py` `STYLE` dict |

### 4-B. 네이밍 규칙

- 키 이름은 **HTML 태그명** 또는 **컴포넌트명** 사용 (`h1`, `p`, `picks_div`, `source_box`)
- 약어 금지: `src_box` → `source_box`
- 색상 팔레트 토큰은 별도로 분리하지 않음 (현재 규모에서 과설계)

### 4-C. 향후 Antigravity / Codex 작업 영역

- `styles/tokens.py` 내 값만 수정
- `templates/*.html`, `templates/*.txt` 마크업 구조 수정
- `generator.py` 로직 미접촉 보장

### 4-D. WordPress CSS 확장 (선택적, 나중 단계)

- 현재는 모두 inline style 방식 유지 (WordPress 테마 충돌 회피)
- 향후 WordPress 테마에 custom CSS를 추가하는 방향으로 발전 가능
- 지금은 `styles/tokens.py` 단일 파일만 관리하는 것이 안전

---

## 5. Migration Plan

### Step 0 — 사전 조건 확인 (코드 읽기, 변경 없음)

- [x] 현재 상태 감사 완료 (이 문서)
- [ ] `generator.py`에서 스타일 상수 사용 위치 전수 확인
- [ ] 실출력 HTML 샘플 1건 보존 (파리티 검증 기준)

---

### Step 1 — `styles/tokens.py` 생성 및 기존 상수 이관 (추출, 행동 변경 없음)

**작업:**
1. `styles/` 디렉토리 생성
2. `styles/__init__.py` 빈 파일 생성
3. `styles/tokens.py` 작성 — 기존 6개 상수를 `STYLE` dict로 통합
   - `_H1_STYLE` → `STYLE["h1"]`
   - `_H3_STYLE` → `STYLE["h3"]`
   - `_P_STYLE` → `STYLE["p"]`
   - `_HR_STYLE` → `STYLE["hr"]`
   - `_PICKS_DIV_STYLE` → `STYLE["picks_div"]`
   - `_format_source_section` 내부 상수 5종 → `STYLE["source_*"]`
   - `convert_to_html` 내부 상수 나머지 → `STYLE["blockquote"]`, `STYLE["strong"]` 등
4. **`generator.py`는 수정하지 않음** — 이 단계는 파일 생성만

**검증:** `styles/tokens.py` import 확인 (unit test 없이 단순 import)

---

### Step 2 — `generator.py` 모듈 레벨 상수를 `tokens.py` 참조로 전환

**작업:**
1. `generator.py` 상단에 `from styles.tokens import STYLE` 추가
2. `_H1_STYLE`, `_H3_STYLE`, `_P_STYLE`, `_HR_STYLE`, `_PICKS_DIV_STYLE` 상수 삭제
3. 해당 상수를 사용하는 f-string 참조를 `STYLE["h1"]` 등으로 교체
   - GPT 프롬프트 f-string: `{_H1_STYLE}` → `{STYLE['h1']}`
   - `convert_to_html()` 내부 상수: 함수 내 로컬 변수 삭제, `STYLE[...]` 직접 참조
4. `_format_source_section()` 내부 상수 5종 삭제 → `STYLE["source_*"]` 참조

**검증:**
- `python -c "from generator import convert_to_html; print('ok')"` 성공 확인
- 기존 실출력 HTML 샘플과 현재 출력 HTML diff 비교 → 내용 동일 확인

---

### Step 3 — HTML 파리티 검증

**작업:**
- `python main.py` 실 실행 1회 (또는 기존 입력 데이터로 dry-run)
- 생성된 HTML을 Step 0에서 보존한 샘플과 비교
- inline style 값이 변경되지 않았는지 확인
- WP 발행 후 레이아웃 시각 확인

**합격 기준:**
- 생성된 HTML의 `style=` 값이 Step 0 샘플과 동일
- 레이아웃 회귀 없음

---

### Step 4 — `templates/` 디렉토리 생성 (선택적, 다음 단계)

**작업:**
1. `templates/` 디렉토리 생성
2. `templates/source_box.html` 작성 (Section 3-B 참조)
3. `_format_source_section()`의 `_rebuild()` 함수를 템플릿 로딩 방식으로 교체
4. `templates/post1_structure.txt`, `post2_structure.txt` 작성
5. GPT 프롬프트 내 마크업 지시 블록을 파일 읽기로 교체

**주의:** Step 4는 Step 3 검증 완료 후에만 진행

---

### Step 5 — 프론트엔드 안전 수정 영역 확정

**작업:**
- `styles/tokens.py`와 `templates/` 파일에 아래 주석 헤더 추가:
  ```
  # FRONT-END SAFE ZONE
  # Antigravity / Codex: 이 파일만 수정하세요.
  # generator.py, main.py, publisher.py 수정 금지.
  ```
- README 또는 `docs/STYLE_SAFE_ZONE.md`에 수정 경계 명문화

---

## 6. Risk Analysis

| 리스크 | 가능성 | 영향 | 완화 방법 |
|--------|--------|------|-----------|
| **렌더링 회귀** — 토큰 이관 중 CSS 값 오탈자 | 중 | 중 | Step 3 HTML diff 검증 의무화 |
| **LLM 출력 변화** — 프롬프트 f-string 교체 중 빈 문자열 삽입 | 중 | 높음 | Step 2 완료 후 dry-run 1회 전수 확인 |
| **GPT 스타일 지시 누락** — 템플릿 파일 로딩 실패 시 | 낮음 (Step 4) | 높음 | `templates/` 파일 읽기 실패 시 하드코딩 fallback 유지 |
| **중복 스타일 소스** — `tokens.py`와 `convert_to_html()` 내부 상수 동시 존재 (Step 1 상태) | 낮음 | 중 | Step 2에서 즉시 old 상수 삭제 |
| **template escape 이슈** — `STYLE["h1"]`에 `;` 포함 → f-string 내 포맷 충돌 | 낮음 | 낮음 | Python f-string 대신 `.replace()` 또는 `str.format_map()` 사용 |
| **`convert_to_html()` 미사용 경로** — Phase 7 이후 GPT가 HTML 직접 출력하므로 `convert_to_html`은 사실상 미사용 | 해당 없음 | 낮음 | 함수 제거 또는 `# legacy` 주석 표기로 혼동 방지 |

---

## 7. Rollback Plan

### Step 1 롤백 (tokens.py 생성 전 상태 복구)
- `styles/` 디렉토리 삭제
- `generator.py` 미수정 상태이므로 즉시 복구 완료

### Step 2 롤백 (generator.py 참조 교체 후 문제 발생 시)
- `git checkout generator.py` — 이전 커밋으로 즉시 복구
- `styles/tokens.py`는 남겨둬도 무해 (미사용 파일)

### Step 4 롤백 (templates/ 도입 후 문제 발생 시)
- `templates/` 디렉토리 삭제
- `generator.py`에서 파일 로딩 코드 제거, 이전 하드코딩 복원
- `git diff` 범위가 `generator.py` 일부 함수로 국한되므로 수동 롤백 비용 낮음

**핵심 원칙:** 각 Step은 독립 커밋. Step N 롤백이 Step N-1 이전 상태에 영향을 주지 않도록 커밋 경계 유지.

---

## 8. Next Implementation Deliverables

다음 구현 Phase(이하 "Style-Sep Step1")에서 생성해야 할 파일과 변경 사항:

### 신규 생성 파일

**`styles/__init__.py`** — 빈 파일

**`styles/tokens.py`** — CSS 토큰 딕셔너리 (Section 3-A 내용 그대로)

### `generator.py` 변경 사항 (Step 2)

| 변경 유형 | 대상 | 내용 |
|-----------|------|------|
| 삭제 | line ~3711–3727 | `_H3_STYLE`, `_HR_STYLE`, `_P_STYLE`, `_H1_STYLE`, `_PICKS_DIV_STYLE` 모듈 상수 5개 |
| 삭제 | `_format_source_section()` ~line 3561–3566 | `BOX_STYLE`, `H_STYLE`, `CAT_STYLE`, `UL_STYLE`, `LI_STYLE` 로컬 상수 5개 |
| 삭제 | `convert_to_html()` ~line 3646–3670 | 내부 로컬 상수 11개 |
| 추가 | 파일 상단 | `from styles.tokens import STYLE` |
| 교체 | GPT 프롬프트 f-string 내 `{_H1_STYLE}`, `{_H3_STYLE}` 등 6곳 | `{STYLE['h1']}`, `{STYLE['h3']}` 등으로 교체 |
| 교체 | `_format_source_section()` 내 상수 참조 | `STYLE["source_box"]` 등으로 교체 |
| 교체 | `convert_to_html()` 내 상수 참조 | `STYLE["h1"]` 등으로 교체 |

### 검증 항목 (구현 완료 조건)

- [ ] `python -c "from generator import generate_deep_analysis"` import 성공
- [ ] `python -c "from styles.tokens import STYLE; print(len(STYLE))"` → 15개 이상 출력
- [ ] 기존 HTML 샘플과 신규 출력 diff에서 `style=` 속성값 일치
- [ ] `grep -n "_H1_STYLE\|_H3_STYLE\|_P_STYLE\|_HR_STYLE\|_PICKS_DIV_STYLE" generator.py` → 0건

---

## 9. Final Recommendation

### 지금 해야 하는가?

**Yes — 단, Step 1~2만 지금 실행하고 Step 4는 나중에.**

현재 Phase 15F (시간 신뢰도 완결)가 우선순위이므로, 스타일 분리는 **병행 트랙**으로 진행한다.
Step 1~2는 `generator.py` 로직에 전혀 영향을 주지 않으며, 실 출력 변화도 없다.
이 범위에서 먼저 `styles/tokens.py`를 만들고, 기존 상수를 참조로 교체하면 안전하다.

Step 4 (`templates/` 도입)는 Phase 15F 완결 후 별도 Phase로 분리 권장.

### 안전한 구현 순서

```
1. styles/tokens.py 생성 (generator.py 미수정)            ← 무위험
2. generator.py 모듈 상수 제거 + tokens.py 참조로 교체    ← 낮은 위험, 즉시 롤백 가능
3. HTML 파리티 검증 (실 실행 1회)                         ← Step 2 직후
4. templates/ 도입 — source_box.html 먼저               ← Phase 15F 이후
5. templates/ 도입 — GPT 프롬프트 구조 지시문 분리        ← Step 4 이후
```

### Python에 영구히 남아야 할 것

| 항목 | 이유 |
|------|------|
| 브로커/뉴스/기타 분류 로직 | 데이터 분류 — 프레젠테이션 아님 |
| `_strip_leading_h1()` | WP 구조 처리 |
| STYLE 토큰 import 및 프롬프트 주입 코드 | Python이 데이터를 template에 공급하는 "접착제" 역할 |
| 모든 게이트 판정, 스코어 집계 | 콘텐츠 파이프라인 로직 |
| LLM 호출 코드 | 생성 파이프라인 핵심 |

---

**총 예상 작업량:**
- Step 1~2: ~30분, ~40라인 변경 (삭제 위주), 리스크 낮음
- Step 4~5: ~90분, ~80라인 변경, Phase 15F 이후 진행 권장
