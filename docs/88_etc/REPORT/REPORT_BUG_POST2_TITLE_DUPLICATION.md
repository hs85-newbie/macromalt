# REPORT_BUG_POST2_TITLE_DUPLICATION.md

작성일: 2026-03-20
분류: **런타임 버그 — 발행 품질 직접 영향**
심각도: **즉시 수정 필요** (모든 Post2 캐시의 픽 포스트 제목 2회 노출)
발견 경위: Phase 19 NEXT_RUN_GO_CHECK 수행 중 사용자 제보 → 실증 검증

---

## 1. 현상

**macromalt.com 라이브 페이지 확인 (Post 187 기준)**

```
URL: https://macromalt.com/캐시의-픽-s-oil-외-중동-리스크와-에너지-섹터/
```

페이지 렌더링:
```
[WordPress 테마 → post_title 렌더링]
[캐시의 픽] S-Oil 외 — 중동 리스크와 에너지 섹터   ← 1회 (테마)

[content HTML → <h1> 렌더링]
[캐시의 픽] S-Oil 외 — 중동 리스크와 에너지 섹터   ← 2회 (본문 내 <h1>)
```

스크린샷 확인: 2026-03-20 실증. WordPress 테마 제목 + 본문 `<h1>` 이중 출력.

---

## 2. 원인 체인 (완전 규명)

### Step 1 — GPT 프롬프트가 SPINE 주석을 HTML 최상단에 삽입 지시

`generator.py` line 1613–1622:
```python
_P14_ANALYTICAL_SPINE_ENFORCEMENT: str = """
[Phase 14 — 분석 뼈대 강제]
기사 작성 시작 전, HTML 첫 줄에 다음 형식의 뼈대 주석을 반드시 삽입하십시오:
<!-- SPINE: [팩트 X]와 [팩트 Y] 동시 발생 → ... -->
"""
```

### Step 2 — 이 블록이 Post2 프롬프트에도 포함됨

`generator.py` line 5324 (Post2 `user_msg` 조합):
```python
+ _P14_POST1_ENFORCEMENT_BLOCK      # Phase 14: few-shot + spine + hedge 금지
```

`_P14_POST1_ENFORCEMENT_BLOCK` (line 1682)은 `_P14_ANALYTICAL_SPINE_ENFORCEMENT`를 포함.
→ Post2 GPT 프롬프트에 SPINE 주석 삽입 지시가 전달됨.

### Step 3 — GPT가 SPINE 주석을 `<h1>` 앞에 출력

GPT 생성 Post2 HTML 구조 (Post 187 에디터 직접 확인):
```html
<!-- SPINE: 중동 지정학적 리스크와 고유가 압력이 강화되는 가운데 연준의 금리 인하 지연 가능성이 높아지며, 투자자는 에너지 섹터에 주목해야 한다. -->

<h1 style="font-size:2em;font-weight:800;...">
  [캐시의 픽] S-Oil 외 — 중동 리스크와 에너지 섹터
</h1>

<p style="...">중동 지정학적 리스크와 고유가 압력 속에서...</p>
...
```

### Step 4 — `_strip_leading_h1()` regex 매칭 실패

`publisher.py` line 62:
```python
def _strip_leading_h1(content: str) -> str:
    return re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*", "", content, count=1, flags=re.DOTALL)
```

- 패턴: `^\s*<h1...` — 문자열 시작 바로 뒤(선택적 공백 포함)에 `<h1>`이 있어야 함
- 실제 content: `<!-- SPINE: ... -->\n<h1 ...>`
- `<!-- SPINE: -->` 주석이 `<h1>` 앞에 있으므로 `^\s*<h1` 패턴 매칭 실패
- 결과: `<h1>` 제거되지 않은 채 WordPress에 업로드됨

### Step 5 — WordPress 이중 렌더링

```
WordPress REST API payload:
  title:   "[캐시의 픽] S-Oil 외 ..."  ← post_title
  content: "<!-- SPINE:... --><h1>제목</h1><p>본문...</p>"  ← <h1> 미제거

WordPress 테마 렌더링:
  1. post_title → 페이지 상단에 제목 출력 (1회)
  2. content의 <h1> → 본문에서 제목 한 번 더 출력 (2회)
```

---

## 3. 영향 범위

| 항목 | 상태 |
|---|---|
| 영향받는 Post 유형 | **Post2 (캐시의 픽) 전건** |
| Post1 (심층분석) 영향 | ⚠️ 동일 가능성 — `_P14_POST1_ENFORCEMENT_BLOCK` Post1에도 포함 여부 별도 확인 필요 |
| 최초 발생 추정 | `_P14_ANALYTICAL_SPINE_ENFORCEMENT` 도입 시점 (Phase 14) 이후 전체 Post2 |
| 확인 포스트 | Post 187 (`[캐시의 픽] S-Oil 외 — 중동 리스크와 에너지 섹터`) |

---

## 4. 수정 방향 (코드 변경 전 사용자 승인 필요)

### 방안 A — `_strip_leading_h1()` regex 확장 (권장)

```python
# Before
def _strip_leading_h1(content: str) -> str:
    return re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*", "", content, count=1, flags=re.DOTALL)

# After (방안 A): HTML 주석 0개 이상을 건너뛰고 <h1> 탐지
def _strip_leading_h1(content: str) -> str:
    return re.sub(
        r"^\s*(<!--.*?-->\s*)*<h1[^>]*>.*?</h1>\s*",
        "",
        content,
        count=1,
        flags=re.DOTALL,
    )
```

**영향 범위**: `publisher.py` 1행 수정. Post1/Post2 모두 적용.

### 방안 B — SPINE 주석을 `<h1>` 이후로 이동 (프롬프트 수정)

`_P14_ANALYTICAL_SPINE_ENFORCEMENT` 지시 변경:
```
Before: "HTML 첫 줄에 다음 형식의 뼈대 주석을 반드시 삽입하십시오"
After:  "제목 <h1> 바로 다음 줄에 다음 형식의 뼈대 주석을 반드시 삽입하십시오"
```

**영향 범위**: prompt 1행 수정. GPT 출력 재현성 의존(불안정).

### 권장: 방안 A 우선

- regex 수정이 더 확실하고 GPT 출력 변동에 무관
- SPINE 주석은 내부 분석 도구로 HTML 어디에 있어도 무관
- `re.DOTALL` 유지로 멀티라인 SPINE 주석도 처리 가능

---

## 5. 즉시 조치 항목

| 항목 | 우선순위 | 담당 |
|---|---|---|
| `publisher.py` `_strip_leading_h1()` regex 수정 (방안 A) | **최우선** | 개발 에이전트 |
| Post1 (심층분석) 동일 현상 여부 확인 | 높음 | 발행 후 라이브 확인 |
| 기존 발행 Post2 (Post 187 이전) 제목 중복 여부 점검 | 중간 | 운영 |
| 수정 후 Phase 19 Route B 실전 확인 | Phase 19 GO 전환 조건 | 개발 에이전트 |

---

## 6. 버그 분류

| 항목 | 값 |
|---|---|
| 버그 ID | BUG-POST2-TITLE-DUP-20260320 |
| 발생 단계 | 발행(publish) 단계 — `_strip_leading_h1()` regex 미매칭 |
| 발생 조건 | `_P14_ANALYTICAL_SPINE_ENFORCEMENT` 포함 Post2 GPT 출력 (SPINE 주석 선행) |
| 결과 | 라이브 페이지에서 제목 2회 반복 출력 |
| HOLD 트리거 여부 | HOLD 아님 — **즉시 수정 항목** |
| 수정 난이도 | 낮음 (1행 regex 수정) |
