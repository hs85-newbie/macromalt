# REPORT_PHASE20_PHASE4_VERIFIER_UPGRADE.md

작성일: 2026-03-23
범위: Phase 20 — Phase 4: Verifier/Reviser 구조 검사 추가
최종 판정: **구현 완료 — 실전 run 대기**

---

## 1. 작업 배경

Phase 1~3 실전 run에서 `planner_used=True` 확인 후 다음 관찰이 제기됨:

- **Post1 lead drift**: `lead_angle_evidence_ids=['fact_2']` 1개였으나 `writer_used_evidence_ids=['fact_1','fact_2','fact_3','fact_4','fact_5']` 5개 사용 → lead coverage 20%
- Verifier가 이 구조적 문제(동형 섹션 반복, 강조 분산, 리드 드리프트)를 검출하지 못하고 있음
- Phase 4 목표: Verifier에 편집 구조 기준 추가 + Python-level lead drift 정량 모니터링

---

## 2. 구현 범위

| 항목 | 내용 | 상태 |
|------|------|------|
| Verifier 기준 26~30 추가 | 편집 구조 점검 5개 기준 | ✅ 완료 |
| Reviser 허용 범위 11~12번 추가 | 섹션 동형 보정 + 리드 약화 보정 | ✅ 완료 |
| `_check_p20_lead_drift()` 신규 함수 | lead coverage 정량 계산 + WARN 로그 | ✅ 완료 |
| `gpt_write_analysis/picks` 내 호출 | 작성 완료 후 drift check 자동 실행 | ✅ 완료 |

---

## 3. 변경 내용

### `GEMINI_VERIFIER_SYSTEM` — 기준 26~30 신규 (Phase 20 편집 구조 점검)

| 기준 | 검사 항목 | 위반 시 |
|------|----------|---------|
| 26. [섹션 동형 반복] | 연속 2개+ 섹션이 "주장→수치→시사" 3단 구조 반복 | pass=false |
| 27. [강조 분산] | 3개+ 섹션 균등 배분, 명확한 lead 섹션 부재 | pass=false |
| 28. [리드 드리프트] | 도입부 핵심 각도가 중반 이후 사라짐 | pass=false (뚜렷한 경우) |
| 29. [일반 문장 과잉] | 숫자·날짜·인과·출처 없는 문장 40%+ | pass=false |
| 30. [근거 없는 분석 단정] | consensus_miss/underpriced_risk 계열 단정 근거 없이 서술 | pass=false |

**적용 우선순위:** 26번(섹션 동형 반복)과 28번(리드 드리프트)은 AI 기계적 서술의 핵심 지표 — 엄격 적용.

### `GEMINI_REVISER_SYSTEM` — 허용 범위 11~12번 신규

```
11. 섹션 동형 반복 → 반복 섹션의 opener를 역접형/인과형/질문형으로 교체
    (수치·논리는 원문 보존, 섹션 길이 유지)
12. 리드 논거 약화 → counterpoint 직전 섹션 끝에 lead 연결 문장 1개 추가
    (날짜·수치 발명 금지, 기존 사실만 참조, 추가 문장 1개 제한)
```

### `_check_p20_lead_metrics()` — 신규 Python 함수 (이중 지표)

| 지표 | 정의 | 감지 실패 모드 |
|------|------|---------------|
| `lead_recall` | `len(lead_ids ∩ used_ids) / len(lead_ids)` | planner 지정 핵심 근거를 writer가 누락 |
| `lead_focus` | `len(lead_ids ∩ used_ids) / len(used_ids)` | writer가 secondary/background에 집중 → 강조 희석 |

**두 지표가 다른 실패 패턴을 잡는다:**
- `low recall + high focus`: lead_ids 중 일부만 썼지만 그나마 비중은 높음 → lead 누락
- `high recall + low focus`: lead_ids 전부 썼지만 그 외 사실도 대량 사용 → 균등 배분 회귀 (오늘 run Post1 패턴)
- `low recall + low focus`: 두 문제 동시

**로그 출력 (항상):**
```
[Phase 20] lead_metrics | run_id=... | post_type=... |
lead_ids=[...] | writer_used_ids=[...] | missing_lead_ids=[...] |
lead_recall=0.xx | lead_focus=0.xx
```

**WARN 조건:**
```
[Phase 20] WARN lead_metrics | run_id=... | post_type=... |
lead_recall=0.xx — lead_ids 절반 이상 미사용        ← recall < 0.5
lead_focus=0.xx  — 사용 facts 중 lead 비중 25% 미만 ← focus < 0.25
```

**오늘 run 기준 예측:**
- Post1: lead_recall=1.00 (fact_2 사용됨), lead_focus=0.20 (5개 중 1개) → focus WARN 발생
- Post2: lead_recall=1.00 (fact_1,2,3 모두), lead_focus=0.75 (4개 중 3개) → WARN 없음

**호출 위치:**
- `gpt_write_analysis()` 반환 직전 (post1)
- `gpt_write_picks()` 반환 직전 (post2)

---

## 4. Fallback 구조

- 모든 Phase 4 변경은 Verifier/Reviser 프롬프트 + WARN 로그 수준 — 파이프라인 차단 없음
- `_check_p20_lead_drift()` 내부 예외 → `logger.debug` 후 무시
- Verifier 기준 26~30 위반 → `pass=false` → 기존 Reviser 경로로 진행 (Phase 20 이전 동일)

---

## 5. 로그 필드 추가 (Phase 4)

| 필드 | 함수 | 설명 |
|------|------|------|
| `lead_recall` | `_check_p20_lead_metrics()` | lead_ids 중 writer 사용 비율 (누락 감지) |
| `lead_focus` | `_check_p20_lead_metrics()` | writer 사용 전체 중 lead 비중 (희석 감지) |
| `missing_lead_ids` | `_check_p20_lead_metrics()` | writer가 미사용한 lead fact id 목록 |
| `WARN lead_metrics` | `_check_p20_lead_metrics()` | recall < 0.5 또는 focus < 0.25 시 경고 |

---

## 6. 불변 원칙 (변경 금지)

| 원칙 | 이유 |
|------|------|
| 기준 26~30은 구조적 문제 — 삭제 금지 | AI 기계적 서술 핵심 지표 |
| lead_coverage 임계값 0.5 | 실전 runs 누적 전까지 유지 |
| Reviser 11~12는 추가 전용 (삭제/발명 금지) | 분량 보존 원칙 유지 |

---

## 7. 다음 단계 (Phase 5)

| 항목 | 우선순위 |
|------|---------|
| Slot/dedup → opener_strategy 연결 강화 | 중간 |
| lead_coverage 실전 데이터 누적 후 임계값 조정 | 높음 |
| opener_pass Post1/Post2 기준 분리 | 중간 |
| 기준 26~30 위반 빈도 주간 집계 추가 | 낮음 |

---

## 8. 최종 판정

**구현 완료 — 실전 run으로 기준 26~30 작동 확인 필요**

- 문법 검증 완료 (`ast.parse` 통과)
- Verifier 기준 26~30 추가 (편집 구조 점검)
- Reviser 허용 범위 11~12번 추가 (동형 보정 + 리드 보정)
- `_check_p20_lead_drift()` 신규 — lead coverage 정량 로깅 시작
- 실전 run에서 `lead_coverage`, `missing_lead_ids` 확인 후 Phase 5 진행
