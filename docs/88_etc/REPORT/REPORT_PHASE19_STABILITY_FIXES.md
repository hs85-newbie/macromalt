# Phase 19 — 런타임 안정성 수정 보고서

작성일: 2026-03-24
기준: Phase 18 테스트 런(run_id: 20260324_103959) 결과 분석 후 수정
커버 범위: 3개 수정 트랙 (Critical 1 + High 2)

---

## 0. 배경

Phase 18 수정 효과 검증 런(run_id: 20260324_103959) 분석 중
신규 false fail 1건 + 코드 구조 분석으로 잠재 버그 2건 발견.

| 항목 | 분류 | 상태 |
|------|------|------|
| `post_role_separation` FAIL — "참고 출처" h3 오탐 | 🔴 High | 수정 완료 |
| `publisher.py` post_id=None 미검증 | 🔴 Critical | 수정 완료 |
| TYPE_C self-closing 태그 open_tag 오탐 | 🟠 High | 수정 완료 |

---

## 1. Track A — post_role_separation "참고 출처" false fail 수정

### 원인 분석

`_check_post_separation()` 내부 `_extract_h3s()`가 모든 `<h3>` 헤딩을 추출해 Post1/Post2 교집합을 계산함.

Phase 19에서 "참고 출처" h3 헤딩이 Post1/Post2 양쪽에 구조적으로 항상 존재:
```html
<h3>참고 출처</h3>
```

→ 두 글에서 동일 헤딩으로 감지 → overlap=1 → total_overlap=1 → WARN
→ 단락 중복이 추가될 경우 total_overlap>2 → **FAIL 오탐**

실제 콘텐츠 중복이 아닌 **보일러플레이트 구조 헤딩 오탐**.

### 수정 내용

`_check_post_separation()` 내부에 `_STRUCTURAL_H3_SKIP` 세트 추가:

```python
# [Phase 19] 고정 구조 섹션명 제외
_STRUCTURAL_H3_SKIP = {"참고 출처", "참고출처"}

def _extract_h3s(html: str) -> set:
    raw = re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.DOTALL | re.IGNORECASE)
    result = set()
    for h in raw:
        text = re.sub(r"<[^>]+>", "", h).strip()
        if text and text not in _STRUCTURAL_H3_SKIP:
            result.add(text)
    return result
```

### 기대 효과

- "참고 출처" h3 헤딩이 비교 대상에서 제외 → false fail 제거
- `post_role_separation` FAIL → PASS/WARN 정상화

---

## 2. Track B — publisher.py post_id=None 명시적 오류 처리

### 원인 분석

`publish_draft()` 함수에서:
```python
data = response.json()
post_id = data.get("id")    # 응답에 "id" 없으면 None
edit_link = data.get("link", "")
logger.info(f"... Post ID: {post_id} ...")
return {"post_id": post_id, ...}  # None이 그대로 반환
```

WordPress API가 비정상 응답(200 OK지만 "id" 필드 없음)을 반환하는 경우:
- `post_id=None`이 상위 코드로 그대로 전달
- `main.py`에서 `post_id is None` 체크 없으면 `None`으로 발행 이력 기록
- 이후 로직에서 `post_id + 1` 같은 산술 시 TypeError

### 수정 내용

`data.get("id")` 이후 None 체크 추가:

```python
if post_id is None:
    raise RuntimeError(
        f"[Phase 19] WordPress 응답에 post_id(id) 필드 없음. "
        f"HTTP {response.status_code} | 응답 키: {list(data.keys())}"
    )
```

### 기대 효과

- post_id=None이 상위로 전파되지 않음
- 비정상 WordPress 응답 즉시 명시적 오류로 노출 → 디버그 용이

---

## 3. Track C — TYPE_C 판정 self-closing 태그 오탐 수정

### 원인 분석

`_classify_parse_failed()` TYPE_C 판정:
```python
open_tags  = len(re.findall(r"<(?!/)(?!br|hr|!)[a-zA-Z][^>]*>", raw))
close_tags = len(re.findall(r"</[a-zA-Z]+>", raw))
if abs(open_tags - close_tags) > 5:
    return "TYPE_C"
```

`<img>`, `<input>`, `<link>`, `<meta>` 는 HTML self-closing 요소로 닫는 태그가 없음.
기존 제외 목록(`br|hr`)에 포함되지 않아:

- `<img src="...">` → open_tag +1, close_tag +0
- 이미지 포함 콘텐츠에서 open-close 불균형이 실제 파손이 아닌데도 TYPE_C 오분류 가능

### 수정 내용

negative lookahead에 `img|input|link|meta` 추가:

```python
# Phase 19: self-closing 요소 제외 확장
open_tags  = len(re.findall(r"<(?!/)(?!br|hr|img|input|link|meta|!)[a-zA-Z][^>]*>", raw))
```

### 기대 효과

- `<img>` 등 self-closing 태그가 포함된 정상 출력이 TYPE_C로 오분류되지 않음
- TYPE_C 차단(RuntimeError) 오발동 방지

---

## 4. 수정 파일 요약

| 파일 | 수정 위치 | 내용 |
|------|-----------|------|
| `generator.py` | `_check_post_separation()` | `_STRUCTURAL_H3_SKIP` 추가 (Track A) |
| `publisher.py` | `publish_draft()` | post_id=None RuntimeError (Track B) |
| `generator.py` | `_classify_parse_failed()` TYPE_C | self-closing 태그 제외 확장 (Track C) |

---

## 5. 비회귀 확인 항목

| 항목 | 기대 상태 |
|------|----------|
| Phase 18 4개 트랙 수정 효과 | ✅ 비회귀 |
| _STRUCTURAL_H3_SKIP 이외 h3 헤딩 중복 감지 | ✅ 동작 유지 |
| TYPE_C 실제 파손 감지 (닫는 태그 불균형 6개 이상) | ✅ 동작 유지 |
| publisher 정상 응답(post_id 존재) 경로 | ✅ 영향 없음 |

---

## 6. Phase 19 잔여 이슈 (다음 트랙 이관)

| 이슈 | 내용 | 우선순위 |
|------|------|---------|
| `numeric_density` / `time_anchor` FAIL | Post1 분량 저하 (2,636자, 수치 0개) — GPT 최소 분량 프롬프트 강화 필요 | 🟠 높음 |
| `criteria_5_pass: False` | Post1/Post2 모두 권유성 표현 잔존 — 패턴 강화 또는 프롬프트 수정 | 🟠 높음 |
| `post1_post2_continuity` WARN 잔존 | n-gram 2개 — PASS 미달. 추가 정밀화 검토 | 🟡 중간 |
| `issues` 타입 검증 부재 | verify_draft() issues가 str 목록인지 확인 로직 없음 | 🟡 중간 |
| `cost_tracker.py` 파일 잠금 | 동시성 대비 원자적 쓰기 필요 | 🟡 중간 |
