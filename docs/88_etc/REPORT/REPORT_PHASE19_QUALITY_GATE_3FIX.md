# Phase 19 — 품질 게이트 3종 수정 보고서

작성일: 2026-03-24
기준 런: 20260324_131001 (Phase 19 PARSE_FAILED 수정 후 첫 정상 런)
커버 범위: Fix1(phase15_tense) + Fix2(post1_post2_continuity) + Fix3(criteria_5_pass)

---

## 0. 배경

`run_id: 20260324_131001` 런에서 PARSE_FAILED 수정 효과가 확인됐으나
3개 품질 지표가 여전히 FAIL/False 상태:

| 지표 | 상태 | 분류 |
|------|------|------|
| `phase15_tense_correction` | FAIL | 🔴 버그 (교정 후 상태 미반영) |
| `post1_post2_continuity` | FAIL | 🟠 반복 이슈 (GPT 도입부 재사용) |
| `criteria_5_pass` | False | 🟠 오탐 (단순 매칭 과도 적용) |

---

## 1. Fix 1 — phase15_tense_correction: FAIL (quality gate 버그)

### 원인 분석

`_detect_completed_year_as_forecast()` → `status="FAIL"` 탐지 시
`_enforce_tense_correction()` 교정 적용 → 교정 후 `p15_tense_diag_after` 재진단.

하지만 `p15_tense_diag["status"]`가 원래 "FAIL"인 채로 유지되고,
교정 결과(`p15_tense_diag_after`)는 `p15_tense_diag["after_correction"]` 안에만 저장됨.

`main.py` quality gate:
```python
"phase15_tense_correction": _p13gate(p1_p13, "tense", key="status")
```
→ 교정 전 "FAIL"을 읽어 FAIL 반환 — **성공적으로 교정했음에도 FAIL 표시**.

### 수정 내용

`_enforce_tense_correction()` 호출 후 status를 교정 후 값으로 업데이트 (Post1/Post2 모두):

```python
# [Phase 19] quality gate가 교정 전 FAIL을 반환하던 버그 수정
p15_tense_diag["pre_correction_status"] = "FAIL"
p15_tense_diag["status"] = p15_tense_diag_after["status"]
```

### 기대 효과

- 교정 성공(after_correction.status=PASS) 시 → quality gate PASS 반영
- 교정 미완전(after_correction.status=FAIL) 시 → quality gate FAIL 유지 (정확한 진단)
- `pre_correction_status` 필드로 교정 전 상태 이력 보존

---

## 2. Fix 2 — post1_post2_continuity: FAIL (Post1 도입부 금지 구절 주입)

### 원인 분석

Post2 GPT 프롬프트에 다수의 "도입부 차별화" 규칙이 있으나 (Phase 16B/16D/C),
모두 **추상적 지침** ("Post1의 거시 배경을 반복하지 마세요") 수준.

GPT는 "무엇을 반복하면 안 되는지" 구체적 텍스트를 모르는 상태에서
같은 테마(반도체 Chipflation)를 다루다 보니 자연스럽게 유사한 어휘를 사용 →
n-gram 4-gram 중복 5개 → FAIL.

**핵심 결핍**: Post1의 실제 도입부 텍스트가 GPT에 전달되지 않음.

### 수정 내용

`generate_stock_picks_report()` 내 user_msg 조립 직전에 Post1 도입부 추출 + 금지 구절 블록 생성:

```python
# [Phase 19] Post1 도입부 금지 구절 블록 (동적)
_m = re.search(r"<h[23][^>]*>", post1_content, re.IGNORECASE)
_p1_body = post1_content[_m.start():] if _m else post1_content
_p1_intro_text = re.sub(r"<[^>]+>", " ", _p1_body)[:350].strip()
_p1_intro_block = (
    "\n[Phase 19 — Post1 도입부 금지 구절 ★ 필독]\n"
    "아래 텍스트는 Post1([심층분석]) 도입부입니다. "
    "Post2 도입부에서 이 텍스트와 3어절 이상 겹치는 표현을 사용하지 마세요:\n"
    f"---\n{_p1_intro_text}\n---\n\n"
)
```

user_msg에 `_P16B_POST2_ANGLE_DIVERSIFICATION` 바로 앞에 삽입.

### 기대 효과

- GPT가 Post1 실제 도입부 텍스트를 보고 구체적으로 겹치지 않게 작성
- 추상적 "차별화" 지시 → 구체적 "이 텍스트와 다르게" 지시로 강화
- `post1_post2_continuity` FAIL → PASS/WARN 개선 예상

---

## 3. Fix 3 — criteria_5_pass=False (과도한 단순 매칭 수정)

### 원인 분석

`_criteria5_banned = ["매수", "유망", "담아야", "사야", "투자 추천", "강력 추천"]`

- `"유망"` 단독 매칭이 `"CCL 유망 기업"`, `"유망한 성장 섹터"` 등 분석 문맥에서도 오탐
- `"매수"` 단독 매칭이 `"매수 물량"`, `"매수 압력"` 등 수급 분석 문맥에서도 오탐
- Gemini verifier는 문맥을 보고 criterion 5 위반 아님으로 판단 → reviser 미실행
- 하지만 code-level 체크는 단순 string 포함 여부 → False 오탐

### 수정 내용

투자 권유 맥락에 특화된 복합 패턴으로 교체:

```python
# [Phase 19] 단순 단어 매칭 → 투자 권유 맥락 패턴으로 좁힘
_criteria5_banned = [
    "담아야", "사야 할", "사야 한다",   # 직접 매수 권유
    "투자 추천", "강력 추천",            # 명시적 추천
    "유망 종목", "유망주",               # 종목 특정 권유
    "매수하세요", "지금 사야",           # 직접 권유 동사
    "매수 의견", "목표 주가",            # 증권사 의견 직접 채택형
]
```

- "유망 종목", "유망주" — 종목 특정 권유 맥락에서만 금지
- "유망한 CCL", "유망 섹터" (섹터 분석) — 미포함 (오탐 제거)
- "매수 물량", "매수 압력" (수급 기술 용어) — 미포함 (오탐 제거)

### 기대 효과

- `criteria_5_pass=False` false fail 제거 → 정상 분석 콘텐츠에서 True 반환
- 실제 투자 권유 패턴(담아야, 매수하세요 등)은 여전히 감지

---

## 4. 수정 파일 요약

| 파일 | 수정 위치 | 내용 |
|------|-----------|------|
| `generator.py` | `generate_deep_analysis()` Phase 15 시제 교정 후 | `p15_tense_diag["status"]` 업데이트 (Fix 1 Post1) |
| `generator.py` | `generate_stock_picks_report()` Phase 15 시제 교정 후 | `p15_tense_diag_p2["status"]` 업데이트 (Fix 1 Post2) |
| `generator.py` | `generate_stock_picks_report()` user_msg 조립 전 | Post1 도입부 금지 구절 블록 동적 생성 (Fix 2) |
| `generator.py` | `_calc_quality_pass_fields()` criteria_5_pass | `_criteria5_banned` 맥락 한정 패턴으로 교체 (Fix 3) |

---

## 5. 비회귀 확인 항목

| 항목 | 기대 상태 |
|------|----------|
| 교정 미발생 시 phase15_tense_correction | ✅ "PASS" 유지 (else 경로 그대로) |
| 교정 후에도 FAIL 잔존 시 | ✅ `after_correction.status = FAIL` → quality gate FAIL (정확한 진단) |
| Post1 content 없는 경우 Fix 2 | ✅ `_p1_intro_block=""` 처리 (조건부) |
| "담아야", "매수하세요" 실제 권유 감지 | ✅ 새 패턴에 포함 — 동작 유지 |
| "유망한 반도체 섹터" 분석 문맥 | ✅ 오탐 제거 (단순 "유망" 삭제) |

---

## 6. 잔여 이슈

| 이슈 | 내용 | 우선순위 |
|------|------|---------|
| `post1_post2_continuity` 효과 검증 | 다음 런에서 n-gram 중복 수 확인 | 🟡 중간 |
| `opener_pass=False` (Post1) | H3 pick-angle 패턴 없음 — Post1 opener 구조 강화 별도 검토 | 🟡 중간 |
| `verifier_revision_closure: WARN` | truly_cnt 잔존 — 다음 런에서 모니터링 | 🟡 중간 |
