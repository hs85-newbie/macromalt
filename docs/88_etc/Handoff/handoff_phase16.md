# handoff_phase16.md

작성일: 2026-03-17
Phase: 16 — Temporal State Normalization
상태: GO (정적 검증 완료, 실출력 검증 대기)

---

## 1. Phase 목표 요약

Phase 15A~15E의 패턴 패치 방식이 반복적으로 한계에 도달함.
GPT, Gemini Step3, 후처리가 각자 시간/시제를 독립적으로 재해석하는 구조적 문제를 해결하기 위해
**단일 시제 상태 SSOT(Single Source of Truth)** 레이어를 구축했다.

---

## 2. 구현 완료 항목

### 2.1 신규 상수 / 함수 (generator.py 내 Phase 16 섹션)

| 이름 | 타입 | 역할 |
|------|------|------|
| `_P16_TEMPORAL_STATES` | dict | 6개 시제 상태 정의 |
| `_P16_PRELIMINARY_MARKERS` | list | 잠정치 마커 |
| `_P16_CONSENSUS_MARKERS` | list | 컨센서스 마커 |
| `_P16_GUIDANCE_MARKERS` | list | 가이던스 마커 |
| `_P16_PURE_FUTURE_VERBS` | list | Phase 15F 미래동사 예외 목록 |
| `_build_temporal_ssot(run_year, run_month)` | func | 런타임 SSOT dict 구축 |
| `_build_p16_generation_block(ssot)` | func | GPT context_text 주입용 블록 |
| `_build_p16_step3_block(ssot)` | func | Step3 시스템 프롬프트 블록 |
| `_strip_current_year_past_month_jeonmang(content, ssot, label)` | func | Phase 15F: 동사형 독립 [전망] 제거 |

### 2.2 파이프라인 통합

| 위치 | 변경 내용 |
|------|----------|
| `GEMINI_VERIFIER_SYSTEM` | `_P15C_STEP3_TEMPORAL_GROUNDING` → `_P16_STEP3_BLOCK` (동적) 교체 |
| `GEMINI_REVISER_SYSTEM` | 동일 교체 |
| Post1 `context_text` 직후 | SSOT 구축 + generation block prepend |
| Post1 Phase 15E 직후 | Phase 15F (`_strip_current_year_past_month_jeonmang`) 호출 |
| Post2 `context_text` 직후 | SSOT 구축 + generation block prepend |
| Post2 Phase 15E 직후 | Phase 15F 호출 |
| Post1/Post2 `p13_scores` | `p15f_strip`, `p16_ssot_run` 추가 |

---

## 3. 검증 게이트

- 정적 검증 (구문 파싱): ✅ PASS
- 실출력 검증: ⏳ Phase 16A에서 수행 예정

---

## 4. 다음 단계

1. **Phase 16A**: 실출력 1회 실행 → `p13_scores.p16_ssot_run` 및 `p15f_strip` 확인
2. 시제 위반 잔여 케이스 발생 시 → `_P16_PURE_FUTURE_VERBS` 또는 SSOT 마커 목록 보강
3. 동일 클래스 위반 3회 이상 반복 시 → Phase 17 승격 기준 적용 (MACROMALT_PHASE_EXECUTION_POLICY)

---

## 5. 파일 위치

| 파일 | 경로 |
|------|------|
| 구현 파일 | `generator.py` |
| 실출력 보고서 | `docs/88_etc/REPORT/REPORT_PHASE16_TEMPORAL_STATE_NORMALIZATION.md` |
| 본 핸드오프 | `docs/88_etc/Handoff/handoff_phase16.md` |
