# Phase 19 — Post2 PARSE_FAILED TYPE_A 근본 원인 수정 보고서

작성일: 2026-03-24
run_id 기준: 20260324_104903 (Type_A 차단 발생)
커버 범위: Fix A (response_mime_type) + Fix B (is_html_context) 2개 트랙

---

## 0. 이슈 요약

`run_id: 20260324_104903` 런에서 Post2 Gemini 검수(Step3:팩트체크) 응답이
JSON으로 파싱되지 않아 PARSE_FAILED → TYPE_A 차단 → Post2 생성 중단.

```
[WARNING] JSON 파싱 실패 — None 반환
[WARNING] [Phase 16J/17] Step3 검수 결과 파싱 실패 (PARSE_FAILED)
[WARNING] [Phase 19] PARSE_FAILED | failure_type=TYPE_A | publish_blocked=True
[ERROR] [Phase 18] PARSE_FAILED TYPE_A — Post2 발행 차단 유형
```

---

## 1. 원인 분석

### 1-A. JSON 응답 불안정 (근본 원인)

`_call_gemini()`는 `response_mime_type` 파라미터 없이 호출됨:
```python
raw = _call_gemini(GEMINI_VERIFIER_SYSTEM, user_msg, "Step3:팩트체크", temperature=0.1)
```

Gemini 2.5-flash(thinking_budget=0)는 30개 검수 기준이 포함된 긴 시스템 프롬프트 처리 시
프롬프트에 "반드시 JSON으로만 출력"이라고 명시해도 다음과 같이 응답할 때가 있음:

```
[Gemini가 설명 텍스트를 앞에 붙여 반환]
다음은 검수 결과입니다:
{"pass": true, "issues": [...]}
```

또는 JSON을 마크다운 코드 블록으로 감싸거나, JSON 구조 자체가 malformed인 경우.
`_parse_json_response`의 fallback regex로도 추출 불가한 경우 → PARSE_FAILED.

### 1-B. TYPE_A 오분류 (부차 원인)

`_classify_parse_failed(raw)`는 h2/h3 태그 부재 시 TYPE_A 반환:
```python
if re.search(r"<h[23][^>]*>", raw) is None:
    return "TYPE_A"
```

verifier 응답(JSON 포맷)은 HTML이 아니므로 h2/h3가 없는 것이 당연 →
JSON 파싱 실패 시 **무조건 TYPE_A**로 분류 → 차단 오발동.

TYPE_A의 원래 의미는 "HTML 본문에 h2/h3 구조 전무"이지만,
verifier 응답 컨텍스트(JSON)에 잘못 적용됨.

### 1-C. criteria_5_pass=False 연쇄 (2차 증상)

PARSE_FAILED로 reviser(Step3b)가 실행되지 않아 GPT 초안의 "유망" 등
권유성 표현이 정리되지 않은 채 발행 → `criteria_5_pass=False`.
→ verifier/reviser 체인이 정상 작동하면 자연 해소 예상.

---

## 2. 수정 내용

### Fix A: `_call_gemini()` — `response_mime_type` 파라미터 추가

```python
# 수정 전
def _call_gemini(system, user, label, temperature=0.3):
    config = GenerateContentConfig(
        system_instruction=..., max_output_tokens=3000,
        temperature=temperature, thinking_config=...,
    )

# 수정 후 [Phase 19]
def _call_gemini(system, user, label, temperature=0.3,
                 response_mime_type=None):
    _config_extra = {"response_mime_type": response_mime_type} if response_mime_type else {}
    config = GenerateContentConfig(
        system_instruction=..., max_output_tokens=3000,
        temperature=temperature, thinking_config=...,
        **_config_extra,
    )
```

**JSON 강제 적용 대상 4개 호출:**

| 호출 라벨 | 역할 | 적용 |
|-----------|------|------|
| `Step1:분석재료생성` | 분석 재료 JSON 생성 | `response_mime_type="application/json"` |
| `Step1.5:EditorialPlanner` | 편집 플래너 JSON | `response_mime_type="application/json"` |
| `Step3:팩트체크` | 검수 결과 JSON (**핵심**) | `response_mime_type="application/json"` |
| `Post2-Step1:종목선정` | 종목 리스트 JSON | `response_mime_type="application/json"` |

**기대 효과:**
- Gemini API 레벨에서 valid JSON만 반환 강제
- 프롬프트 지시("JSON으로만 출력")에 더해 API 레벨 이중 방어
- PARSE_FAILED 발생 빈도 대폭 감소 예상

### Fix B: `_classify_parse_failed()` — `is_html_context` 파라미터 추가

```python
# 수정 전
def _classify_parse_failed(raw, normalized=None):
    if re.search(r"<h[23][^>]*>", raw) is None:
        return "TYPE_A"  # verifier JSON 응답에도 오적용

# 수정 후 [Phase 19]
def _classify_parse_failed(raw, normalized=None, *, is_html_context=True):
    # TYPE_A: HTML 컨텍스트에서만 적용 (verifier JSON 응답에는 미적용)
    if is_html_context and re.search(r"<h[23][^>]*>", raw) is None:
        return "TYPE_A"
```

**`verify_draft()` 내 호출 변경:**
```python
# 수정 전
_pf_type = _classify_parse_failed(raw or "")

# 수정 후 [Phase 19]
_pf_type = _classify_parse_failed(raw or "", is_html_context=False)
# verifier 응답은 JSON이므로 h2/h3 부재 = HTML 구조 문제 아님 → TYPE_UNKNOWN(허용)
```

**기대 효과:**
- verifier JSON 응답 PARSE_FAILED 시 TYPE_UNKNOWN(허용) 처리
- Fix A가 PARSE_FAILED 자체를 막지만, 혹여 발생 시 오차단 방지

---

## 3. 수정 파일 요약

| 파일 | 수정 위치 | 내용 |
|------|-----------|------|
| `generator.py` | `_call_gemini()` | `response_mime_type` 파라미터 추가 |
| `generator.py` | `Step1:분석재료생성` 호출 | `response_mime_type="application/json"` |
| `generator.py` | `Step1.5:EditorialPlanner` 호출 | `response_mime_type="application/json"` |
| `generator.py` | `Step3:팩트체크` 호출 | `response_mime_type="application/json"` |
| `generator.py` | `Post2-Step1:종목선정` 호출 | `response_mime_type="application/json"` |
| `generator.py` | `_classify_parse_failed()` | `is_html_context` 파라미터 추가 |
| `generator.py` | `verify_draft()` PARSE_FAILED 분기 | `is_html_context=False` 전달 |

---

## 4. 비회귀 확인 항목

| 항목 | 기대 상태 |
|------|----------|
| HTML 본문 생성 호출 (GPT) | ✅ 영향 없음 (JSON 강제 적용 대상 아님) |
| Gemini reviser 호출 (HTML 직접 출력) | ✅ 영향 없음 (response_mime_type 미적용) |
| `_classify_parse_failed` 기존 HTML 컨텍스트 호출 | ✅ 비회귀 (is_html_context=True 기본값 유지) |
| PARSE_FAILED TYPE_A 차단 (HTML 본문) | ✅ 동작 유지 |

---

## 5. 잔여 이슈

| 이슈 | 내용 | 우선순위 |
|------|------|---------|
| `criteria_5_pass=False` | verifier 정상화 시 reviser 체인으로 자연 해소 예상. 다음 런에서 검증 | 🟡 중간 |
| `opener_pass=False` | Post1 opener H3 pick-angle 패턴 미충족 — GPT 프롬프트 강화 고려 | 🟡 중간 |
| `criteria_1_pass=False` | 시점 혼합 간이 판정 FAIL — 검수 체인 정상화 시 reviser가 처리 예상 | 🟡 중간 |
