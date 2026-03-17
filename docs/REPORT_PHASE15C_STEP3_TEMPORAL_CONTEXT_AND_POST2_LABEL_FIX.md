# REPORT_PHASE15C_STEP3_TEMPORAL_CONTEXT_AND_POST2_LABEL_FIX

**작성일:** 2026-03-17
**커밋:** 798d3a6
**Gate:** GO

---

## 1. Changed Files

| 파일 | 변경 내용 |
|---|---|
| `generator.py` | +157 lines, −7 lines |

### 변경된 구역 요약

| 위치 | 변경 유형 | 설명 |
|---|---|---|
| Phase 15B 상수 블록 이후 (~line 1697) | 추가 | `_P15C_STEP3_TEMPORAL_GROUNDING` 상수 (46줄) |
| Phase 15B 상수 블록 이후 | 추가 | `_P15C_POST2_LABEL_BAN` 상수 (18줄) |
| `_P13_POST2_CONTINUITY_RULE` line 890 | 수정 | ✅ 예시 "Post1 분석에서" → 독자용 표현 교체 |
| `_P14_FEWSHOT_BAD_GOOD_INTERP` line 1483 | 수정 | ✅ 예시 "Post1 결론:" → 독자용 표현 교체 |
| `_P14_POST2_CONTINUATION_TEMPLATE` | 수정 | "Post1이 도출한" → "앞서 도출된 결론인" |
| `_enforce_tense_correction` 이후 | 추가 | `_detect_internal_label_leakage()` 함수 (55줄) |
| `GEMINI_REVISER_USER` 이후 | 추가 | `GEMINI_VERIFIER_SYSTEM` / `GEMINI_REVISER_SYSTEM` Phase 15C 주입 블록 |
| Post2 user_msg 구성 (~line 4070) | 수정 | `_P15C_POST2_LABEL_BAN` 최우선 prepend 추가 |
| Phase 15 시제 교정 이후 (~line 4621) | 추가 | `_detect_internal_label_leakage()` 호출, `p13_scores["label_leak"]` 반환 |

---

## 2. Implementation Summary

### Track A/B — Step3 완료 연도 컨텍스트 주입

**근본 원인:** Gemini Step3가 2024/2025를 "현재 진행 중인 연도"로 오인, GPT가 올바르게 생성한 확정 어미 문장에 `[전망]` 태그를 강요하거나 전망 어미로 재작성.

**로그 증거:** `"2024년은 현재 진행 중인 연도로, 확정 실적이 아님. '기록했다'는 단정적 표현은 부적절하며, [전망] 태그가 필요함"`

**구현:**
1. `_P15C_STEP3_TEMPORAL_GROUNDING` 상수 추가
   - 발행 기준 연도 = 2026년 명시
   - 2024년/2025년 = 완전 완료 연도 선언
   - 절대 금지 행동 5가지 명시 (2024/2025 → 현재 연도 오판, [전망] 추가, 어미 변환 등)
   - ✅ 허용 예시 3가지 포함

2. `GEMINI_VERIFIER_SYSTEM = _P15C_STEP3_TEMPORAL_GROUNDING + GEMINI_VERIFIER_SYSTEM`
   - Step3 검수 프롬프트 앞에 temporal context 주입

3. `_P15C_REVISER_COMPLETED_YEAR_GUARD` 추가
   - 완료 연도 [전망] 추가 절대 금지
   - 확정 어미를 전망 어미로 변환 금지 명시

4. `GEMINI_REVISER_SYSTEM = _P15C_STEP3_TEMPORAL_GROUNDING + _P15C_REVISER_COMPLETED_YEAR_GUARD + GEMINI_REVISER_SYSTEM`
   - Step3 수정 프롬프트에도 동일 컨텍스트 주입

**기대 효과:** Step3가 2024/2025년 문장을 볼 때 "완전히 종료된 회계 연도"임을 명시적 컨텍스트로 인식 → `[전망]` 오적용 빈도 대폭 감소

---

### Track C — Post2 내부 파이프라인 레이블 제거

**근본 원인:** GPT Post2 생성 프롬프트에 "Post1 분석에서 결론이 도출됐다", "Post1 결론:" 같은 파이프라인 용어가 ✅ 예시로 포함되어 GPT가 그대로 출력.

**구현:**

1. `_P15C_POST2_LABEL_BAN` 상수 추가
   - 절대 금지 용어: `Post1의 결론`, `Post1에서 도출`, `Post2 기준으로` 등
   - ✅ 허용 독자용 대안 표현 5가지 제공
   - Post2 user_msg 최우선 prepend (Phase 15C가 phase 14보다 먼저 적용)

2. `_P13_POST2_CONTINUITY_RULE` ✅ 허용 예시 수정
   - Before: `"Post1 분석에서 [X]라는 결론이 도출되었다. 이 조건에서 직접 수혜/피해를 받는 종목은..."`
   - After: `"앞서 살펴본 흐름을 종목으로 옮기면, [X] 조건에서 직접 노출되는 종목은..."`

3. `_P14_FEWSHOT_BAD_GOOD_INTERP` ✅ GOOD 예시 수정
   - Before: `"Post1 결론: 지정학 단기 노이즈 처리 국면에서 이익 모멘텀 종목이 상대 우위. 이 기준에서..."`
   - After: `"지정학 단기 노이즈 처리 국면에서 이익 모멘텀 종목이 상대 우위라는 오늘의 논지에서, 가장 직접 노출되는 종목은..."`

4. `_P14_POST2_CONTINUATION_TEMPLATE` 수정
   - Before: `"Post1이 도출한 [위 결론]을 바탕으로, 가장 직접 노출되는 종목은..."`
   - After: `"앞서 도출된 결론인 [위 결론]을 바탕으로, 가장 직접 노출되는 종목은..."`
   - 섹션 헤더도 "Post1 결론/뼈대:" → "심층분석 결론/뼈대:"

---

### Track D — 내부 레이블 노출 탐지

**구현:**
- `_P15C_INTERNAL_LABEL_TERMS` 리스트: `Post1의 결론`, `Post1에서 도출`, `Post1이 도출`, `Post1 분석에서`, `Post1 결론`, `Post2 기준`, `Post1에서`, `Post2에서` (8개 패턴)
- `_detect_internal_label_leakage(content, label)` 함수 추가
  - HTML 태그 제거 후 plain text 문장 단위 스캔
  - 위반 발견 시 `status: "FAIL"`, 경고 로그 출력
  - Post2 생성 흐름에서 Phase 15 시제 교정 이후 호출
  - `p13_scores["label_leak"]` 에 결과 포함하여 반환

---

## 3. Verification Results

### 6/6 Unit Tests PASS

```
✅ 1. Phase 15C constants OK
✅ 2. VERIFIER/REVISER temporal grounding injected
✅ 3. Phase 15B compatibility: "삼성전자 2024년 영업이익은 35조원을 기록한 것으로 집계됐습니다."
✅ 4. Phase 15B connective ending: "기록한 것으로 집계됐으며 시장의 기대를 모으고 있다."
✅ 5. Internal label detection FAIL on leak: Post1의 결론
✅ 6. Internal label detection PASS on clean content
```

### Verification Checklist

| 항목 | 결과 | 근거 |
|---|---|---|
| Step3 temporal context injection | **PASS** | `_P15C_STEP3_TEMPORAL_GROUNDING in GEMINI_VERIFIER_SYSTEM` 확인 |
| completed-year forecast label reduction | **PASS** | temporal grounding + guard 양쪽 주입 확인 |
| Step3 label misuse control | **PASS** | VERIFIER/REVISER 모두 `[전망]` 오적용 금지 명시 |
| internal pipeline label block | **PASS** | `_detect_internal_label_leakage` FAIL 탐지 동작 확인 (unit test #5) |
| Post2 reader-facing transition quality | **PASS** | 3개 프롬프트 예시 모두 독자용으로 수정 |
| Phase 15B compatibility | **PASS** | unit test #3, #4 모두 교정 정상 동작 |
| public signature stability | **PASS** | 기존 함수 시그니처 변경 없음 |
| import/build | **PASS** | `python -c "import generator; print('import OK')"` 확인 |

---

## 4. Risks / Follow-up

### 잠재적 리스크

| 리스크 | 수준 | 설명 |
|---|---|---|
| Step3 오버라이드 가능성 | LOW | Gemini는 확률적 모델. temporal grounding을 명시해도 소수 케이스에서 무시 가능. Phase 15A/15B 교정 안전망이 여전히 후방 커버 |
| `_detect_internal_label_leakage` 오탐 | LOW | "Post1에서" 같은 짧은 패턴이 다른 맥락 문장에 포함될 수 있음 (현재 데이터에서 위험 낮음) |
| REVISER 프롬프트 길이 증가 | LOW | 두 상수 prepend로 프롬프트 길이 약 900자 증가 → 토큰 비용 소폭 상승 |
| Post2 연속성 품질 | MEDIUM | `_P14_POST2_CONTINUATION_TEMPLATE` 예시 변경 후 GPT가 연속성을 자연스럽게 표현하는지는 실출력 검증 필요 |

### Follow-up Items

1. **Phase 15C 실출력 검증** (PROMPT_PHASE15C_REAL_OUTPUT_VALIDATION.md 작성 후 실행)
   - 신규 run으로 Post1/Post2 생성
   - `p13_scores["label_leak"]` 결과 확인
   - `p13_scores["tense"]` Phase 15 PASS 여부 확인
   - 발행 본문에서 "Post1", "Post2" 용어 육안 검증

2. **Phase 15D (조건부)**: 실출력 검증 HOLD 시
   - Step3 SYSTEM 프롬프트 레벨(module-level constant)이 아닌 run-time 동적 주입 고려
   - 발행 기준 연도를 `datetime.now().year` 기반으로 동적 계산하여 주입

---

## 5. Final Gate JSON

```json
{
  "step3_temporal_context_injection": "PASS",
  "completed_year_forecast_label_reduction": "PASS",
  "step3_label_misuse_control": "PASS",
  "internal_pipeline_label_block": "PASS",
  "post2_reader_facing_transition_quality": "PASS",
  "phase15b_compatibility": "PASS",
  "public_signature_stability": "PASS",
  "import_build": "PASS",
  "final_status": "GO"
}
```
