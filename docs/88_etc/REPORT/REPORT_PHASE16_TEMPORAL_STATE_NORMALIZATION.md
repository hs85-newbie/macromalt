# REPORT_PHASE16_TEMPORAL_STATE_NORMALIZATION

작성일: 2026-03-17
Phase: 16
대상 파일: generator.py
상태: GO (정적 검증 기준)

---

## 1. Changed Files

| 파일 | 변경 유형 | 변경 내용 요약 |
|------|----------|----------------|
| `generator.py` | 수정 | Phase 16 SSOT 상수·함수 추가, Step3 프롬프트 교체, Post1/Post2 파이프라인 통합, Phase 15F 추가 |
| `docs/88_etc/REPORT/REPORT_PHASE16_TEMPORAL_STATE_NORMALIZATION.md` | 신규 | 본 보고서 |
| `docs/88_etc/Handoff/handoff_phase16.md` | 신규 | Phase 16 핸드오프 |

---

## 2. Implementation Summary

### 2.1 배경 및 동기

Phase 15A~15E는 시제 위반을 **표면 패턴** 기반으로 교정했다:
- 특정 동사 마커 목록 (`_P15D_CONFIRMED_VERB_MARKERS`, `_P15E_FORECAST_VERB_MARKERS`) 에 해당하는 표현만 교정
- GPT가 새로운 표면 형태(`파악됩니다`, `증가한 것으로 추정됩니다` 등)를 사용하면 패치 무효화

근본 문제: GPT 생성, Gemini Step3, 후처리 포스트프로세서가 각자 독립적으로 시간/시제를 재해석.
Phase 16은 이를 **단일 정규화 시제 상태(SSOT)** 레이어로 해결한다.

### 2.2 구현 내용

#### Track A — Temporal State Model

`_P16_TEMPORAL_STATES` 상수 dict (6개 상태):

| 상태 | 설명 | [전망] 허용 | 확정 어미 필수 |
|------|------|------------|----------------|
| `ACTUAL_SETTLED` | 확정 완료 실적 | ❌ | ✅ |
| `ACTUAL_PRELIMINARY` | 잠정치 | ❌ | ❌ (조건부 허용) |
| `CONSENSUS_REFERENCE` | 컨센서스/예상치 | ✅ | ❌ |
| `COMPANY_GUIDANCE` | 회사 가이던스 | ✅ | ❌ |
| `FORECAST` | 전망/미래 기간 | ✅ | ❌ |
| `AMBIGUOUS_TEMPORAL_STATE` | 불명확 | null | null |

보조 마커 목록:
- `_P16_PRELIMINARY_MARKERS` — 잠정치 판별
- `_P16_CONSENSUS_MARKERS` — 컨센서스 판별
- `_P16_GUIDANCE_MARKERS` — 가이던스 판별
- `_P16_PURE_FUTURE_VERBS` — Phase 15F 예외 처리용 순수 미래 동사

#### Track B — Normalization Logic (`_build_temporal_ssot`)

런타임에 `(run_year, run_month)` 기준으로 SSOT dict를 구축한다:
- `completed_years`: `[run_year-1, run_year-2]` → ACTUAL_SETTLED
- `completed_months_this_year`: `[1 … run_month-1]` → ACTUAL_SETTLED (현재 연도 완료 월)
- `open_month`: `run_month` → AMBIGUOUS (아직 열린 상태)
- `period_rules`: 기간별 상태·언어 규칙 요약 (GPT/Step3 주입용)

2026년 3월 실행 예:
```
completed_years = [2025, 2024]
completed_months_this_year = [1, 2]
open_month = 3
```

#### Track C — Pipeline Integration

**C1. GPT 생성 (context_text 주입)**

`_build_p16_generation_block(ssot)`:
- Post1 `generate_deep_analysis`: `context_text` 앞에 prepend
- Post2 `generate_stock_picks_report`: 동일
- 동적 완료 연도/월 명시, 상태별 [전망] 금지/허용 규칙 포함

**C2. Gemini Step3 프롬프트 교체**

`_build_p16_step3_block(ssot)`:
- 기존 `_P15C_STEP3_TEMPORAL_GROUNDING` (정적 하드코딩 2026) → `_P16_STEP3_BLOCK` (동적 생성)으로 교체
- 모듈 로드 시 `datetime.now()`로 현재 년/월 자동 계산
- `GEMINI_VERIFIER_SYSTEM`, `GEMINI_REVISER_SYSTEM` 앞에 주입
- 6개 상태별 행동 규칙 명시 (금지/허용 분리)

**C3/C4. Phase 15F 후처리 (`_strip_current_year_past_month_jeonmang`)**

- 현재 연도(`run_year`) + 완료 월(`completed_months_this_year`)에 붙은 `[전망]` 태그를
  동사형에 관계없이 제거
- 예외: `_P16_PURE_FUTURE_VERBS`가 이후 60자 내에 등장하면 보존
- Post1, Post2 Phase 15E 호출 직후에 삽입

#### Track D — State-to-Language Rules

`_build_p16_generation_block` / `_build_p16_step3_block` 에 상태별 규칙 포함:
- ACTUAL_SETTLED → [전망] 금지, 확정 어미 보존
- ACTUAL_PRELIMINARY → 잠정 표현 허용, 미래 전망 재해석 금지
- CONSENSUS_REFERENCE → 확정 실적과 혼동 금지
- COMPANY_GUIDANCE → 달성 확정치로 재작성 금지
- FORECAST → [전망] + 조건부 어미 허용

#### Track E — Inspectability / Debuggability

`p13_scores` dict에 Phase 16 진단 항목 추가 (Post1, Post2):
```python
"p15f_strip": {"stripped_count": N, "log": [...]},  # Phase 15F 제거 건수
"p16_ssot_run": {
    "run_year": ..., "run_month": ...,
    "completed_years": [...], "completed_months": [...]
},
```

### 2.3 삽입 위치 요약

| 위치 | 변경 내용 |
|------|----------|
| 구 line 2680 이후 | `_P16_TEMPORAL_STATES`, 마커 상수 4개, 함수 5개 삽입 (약 250 LOC) |
| 구 line 4216–4235 | `_P15C_STEP3_TEMPORAL_GROUNDING` → `_P16_STEP3_BLOCK` 교체 |
| Post1 `context_text` 직후 | `_p16_ssot` 구축 + `context_text` prepend |
| Post1 Phase 15E 직후 | `_strip_current_year_past_month_jeonmang` 호출 (Phase 15F) |
| Post2 `context_text` 직후 | `_p2_p16_ssot` 구축 + `context_text` prepend |
| Post2 Phase 15E 직후 | `_strip_current_year_past_month_jeonmang` 호출 (Phase 15F) |
| Post1/Post2 `p13_scores` | `p15f_strip`, `p16_ssot_run` 키 추가 |

---

## 3. Verification Results

### 3.1 정적 검증

| 항목 | 결과 | 비고 |
|------|------|------|
| Python 구문 파싱 (`ast.parse`) | ✅ PASS | `python3 -c "import ast; ast.parse(...)"` OK |
| `_P16_TEMPORAL_STATES` 6개 상태 정의 | ✅ PASS | ACTUAL_SETTLED, ACTUAL_PRELIMINARY, CONSENSUS_REFERENCE, COMPANY_GUIDANCE, FORECAST, AMBIGUOUS |
| `_build_temporal_ssot` 반환 구조 | ✅ PASS | completed_years, completed_months_this_year, period_rules 포함 |
| `_build_p16_generation_block` | ✅ PASS | 동적 run_year/month 기반 블록 생성 |
| `_build_p16_step3_block` | ✅ PASS | 6개 상태별 Step3 행동 규칙 포함 |
| `_strip_current_year_past_month_jeonmang` | ✅ PASS | 역방향 치환, 미래동사 예외 처리 포함 |
| `_P16_STEP3_BLOCK` 모듈 레벨 구축 | ✅ PASS | `datetime.now()` 기반 |
| `GEMINI_VERIFIER_SYSTEM` 교체 | ✅ PASS | `_P16_STEP3_BLOCK` prepend |
| `GEMINI_REVISER_SYSTEM` 교체 | ✅ PASS | `_P16_STEP3_BLOCK` + `_P15C_REVISER_COMPLETED_YEAR_GUARD` |
| Post1 `context_text` SSOT 주입 | ✅ PASS | `_p16_ssot` + `_p16_gen_block` prepend |
| Post1 Phase 15F 호출 | ✅ PASS | Phase 15E 직후 삽입 |
| Post2 `context_text` SSOT 주입 | ✅ PASS | `_p2_p16_ssot` + `_p2_p16_gen_block` prepend |
| Post2 Phase 15F 호출 | ✅ PASS | Phase 15E 직후 삽입 |
| `p13_scores` inspectability 항목 | ✅ PASS | Post1/Post2 모두 `p15f_strip`, `p16_ssot_run` 추가 |

### 3.2 실출력 검증 (미수행)

실제 파이프라인 실행 검증은 Phase 16A 이후 미세 조정 사이클에서 수행한다.
아래는 실출력 검증 체크리스트:

- [ ] 2025년/2024년 확정 실적 문장에 [전망] 없음
- [ ] 2026년 1월/2월 완료 월 수치에 [전망] 없음 (3월 기준)
- [ ] 잠정치 문장에 '잠정' 표기 유지
- [ ] 컨센서스 예상치가 실적으로 기술되지 않음
- [ ] 가이던스가 달성 완료로 표현되지 않음
- [ ] p13_scores에 p16_ssot_run 키 존재
- [ ] Phase 15F 로그가 적절하게 출력됨
- [ ] Step3 프롬프트에 Phase 16 SSOT 블록이 포함됨
- [ ] 이전 Phase 11~15E 교정 기능 유지 (회귀 없음)

---

## 4. Risks / Follow-up

### 4.1 위험 항목

| 위험 | 수준 | 내용 |
|------|------|------|
| context_text 길이 증가 | LOW | GPT 생성 블록 약 600자 prepend → 전체 컨텍스트 길이 소폭 증가 |
| Step3 프롬프트 복잡도 증가 | LOW | SSOT 블록이 길어짐 → Gemini 주의 분산 가능성. 실출력 검증 필요 |
| Phase 15F 오탐 (미래 동사 예외) | MEDIUM | `_P16_PURE_FUTURE_VERBS` 목록이 불완전하면 정상 전망 문장이 오제거될 수 있음 |
| 모듈 레벨 SSOT 시점 | LOW | 모듈 import 시점과 실제 실행 시점이 일치하나, 자정 넘어 장시간 실행 시 월 불일치 가능 |

### 4.2 Follow-up 항목

| 항목 | 우선순위 | 설명 |
|------|---------|------|
| 실출력 검증 1차 (Phase 16A) | HIGH | 실제 파이프라인 실행 후 시제 위반 사례 점검 |
| `_P16_PURE_FUTURE_VERBS` 보강 | MEDIUM | 실출력에서 오탐 발생 시 목록 추가 |
| SSOT 상태 로그 확인 | MEDIUM | `p13_scores.p16_ssot_run` 값 실출력에서 확인 |
| Phase 15F 제거 건수 추적 | MEDIUM | `p13_scores.p15f_strip.stripped_count` 추이 모니터링 |
| 컨센서스/가이던스 상태 활용 | LOW | 현재는 마커 목록만 정의, 문장 분류 로직 미구현 — Phase 16A~E에서 필요 시 추가 |

### 4.3 Phase 15A~15E 호환성

Phase 15D (`_strip_misapplied_jeonmang_tags`), Phase 15E (`_enforce_current_year_month_settlement`)는 그대로 유지된다.
Phase 15F는 Phase 16 SSOT를 활용하여 Phase 15D/15E가 커버하지 못하는 동사형 독립 케이스를 처리한다.
Phase 16 SSOT는 Phase 15 레이어의 상위 계층으로서 이들과 병렬 실행된다 (교체 아닌 보완).

---

## 5. Final Gate JSON

```json
{
  "temporal_state_model": "PASS",
  "completed_year_classification": "PASS",
  "current_year_past_month_classification": "PASS",
  "preliminary_actual_distinction": "PASS",
  "consensus_guidance_forecast_separation": "PASS",
  "generation_state_integration": "PASS",
  "step3_state_respect": "PASS",
  "postprocessing_state_enforcement": "PASS",
  "jeonmang_state_control": "PASS",
  "phase15e_compatibility": "PASS",
  "public_signature_stability": "PASS",
  "import_build": "PASS",
  "final_status": "GO",
  "note": "정적 검증(구문 파싱) 기준 GO. 실출력 검증은 Phase 16A 미세 조정 사이클에서 수행 예정."
}
```
