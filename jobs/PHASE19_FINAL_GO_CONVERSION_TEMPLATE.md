# PHASE19_FINAL_GO_CONVERSION_TEMPLATE

작성일: YYYY-MM-DD  
Phase: **Phase 19 — 최종 GO 전환 확인 템플릿**  
범위: Phase 19 Track 2 이후 첫 실발행 run 기준 최종 GO 전환 여부 확인

---

## 1. 목적

본 문서는 Phase 19 Track 1에서 반영한 로그 보강 3개 항목과 Track 2 런타임 검증 결과를
**실제 Phase 19 이후 발행 run** 기준으로 최종 확인하기 위한 템플릿이다.

이번 확인의 핵심은 아래 두 경로 중 하나 충족 여부다.

- **우선 경로 A**: Phase 19 이후 발행 중 `PARSE_FAILED` 1건 이상 발생 → 15개 필드 전체 기록 확인
- **대체 경로 B**: Phase 19 이후 정상 발행 3건 이상에서 `slot/post_type` 정상 기록 + 권장 4종 기록 확인

---

## 2. 선행 조건

| 항목 | 상태 | 비고 |
|---|---|---|
| Phase 19 Track 1 코드 반영 완료 | [ ] | T1-1 / T1-2 / T1-3 |
| Phase 19 Track 2 조건부 보고 완료 | [ ] | `REPORT_PHASE19_TRACK2_RUNTIME_VALIDATION.md` |
| 실제 Phase 19 이후 신규 발행 run 존재 | [ ] | run_id 기입 필요 |
| 실발행본 / 공개 URL 확보 | [ ] | 운영 정책 필수 |
| opener 회귀 없음 | [ ] | generic opener 금지 유지 |

---

## 3. 신규 발행 run 개요

| 항목 | 값 |
|---|---|
| run_id |  |
| 실행 시각 |  |
| slot |  |
| 발행 건수 |  |
| 공개 URL 수 |  |
| Post ID 목록 |  |
| Post1 / Post2 구분 |  |
| PARSE_FAILED 발생 여부 |  |
| fallback_used 발생 여부 |  |

---

## 4. 경로 판정 (A / B)

### 4-1. 우선 경로 A — PARSE_FAILED 기반 확인

| 조건 | 결과 | 비고 |
|---|---|---|
| Phase 19 이후 PARSE_FAILED 1건 이상 발생 | [ ] | |
| `slot != unknown` | [ ] | |
| `post_type != unknown` | [ ] | |
| `picks_section_offset` 기록 | [ ] | 숫자 또는 -1 |
| `opener_pass` 기록 | [ ] | |
| `criteria_1_pass` 기록 | [ ] | |
| `criteria_5_pass` 기록 | [ ] | |
| `source_structure_pass` 기록 | [ ] | |
| `closure / publish_blocked` 기록 | [ ] | |
| Axis B/C 정책 일치 | [ ] | TYPE별 허용/차단 일치 |

**경로 A 충족 여부:** [GO / 미충족 / 해당 없음]

---

### 4-2. 대체 경로 B — 정상 발행 3건 기반 확인

| 조건 | 결과 | 비고 |
|---|---|---|
| Phase 19 이후 정상 발행 3건 이상 확보 | [ ] | |
| 3건 모두 `slot != unknown` | [ ] | |
| 3건 모두 `post_type != unknown` | [ ] | |
| 3건 모두 `opener_pass` 기록 | [ ] | |
| 3건 모두 `criteria_1_pass` 기록 | [ ] | |
| 3건 모두 `criteria_5_pass` 기록 | [ ] | |
| 3건 모두 `source_structure_pass` 기록 | [ ] | |
| 공개 URL 3건 이상 확보 | [ ] | |
| opener 회귀 / generic opener 재발 없음 | [ ] | |

**경로 B 충족 여부:** [GO / 미충족 / 해당 없음]

---

## 5. 15개 필드 실전 기록 점검표

### 5-1. PARSE_FAILED 로그 또는 대표 발행 로그 1건

| 필드 | 기대값 | 실제값 | 정상 여부 | 비고 |
|---|---|---|---|---|
| run_id | 존재 |  |  | |
| slot | `unknown` 아님 |  |  | |
| post_type | `post1` or `post2` |  |  | |
| failure_type | TYPE명 or 없음 |  |  | |
| parse_stage | 존재 |  |  | |
| failed_section_name | 존재 |  |  | |
| raw_output_snapshot | 존재 |  |  | |
| normalized_output_snapshot | 존재 |  |  | |
| fallback_used | bool |  |  | |
| publish_blocked | bool |  |  | |
| picks_section_offset | 숫자 또는 -1 |  |  | |
| opener_pass | bool |  |  | |
| criteria_1_pass | bool |  |  | |
| criteria_5_pass | bool |  |  | |
| source_structure_pass | bool |  |  | |

### 5-2. 대표 샘플 3건 요약

| Post ID | slot | post_type | opener_pass | criteria_1_pass | criteria_5_pass | source_structure_pass | 공개 URL |
|---:|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |

---

## 6. TYPE / fallback 정책 일치 확인

| 항목 | 결과 | 비고 |
|---|---|---|
| TYPE_D 발생 시 closure=WARN 상한 유지 | [ ] | |
| TYPE_D 발생 시 publish_blocked=False 조건부 허용 | [ ] | |
| TYPE_UNKNOWN 2건 이상 아님 | [ ] | |
| fallback 30일 누적 3건 미만 / 또는 정책 일치 | [ ] | |
| 차단되어야 할 케이스 우회 발행 없음 | [ ] | |
| opener PASS와 fallback 정책 충돌 없음 | [ ] | |

---

## 7. 운영 정책 대조

| 판정 기준 | 결과 | 근거 |
|---|---|---|
| 실제 발행본 기준 검증 | [ ] | |
| 공개 URL 확보 | [ ] | |
| 기준1 위반 없음 | [ ] | |
| 기준5 위반 없음 | [ ] | |
| 반복 실행에서 품질 유지 | [ ] | |
| HOLD 사유 없음 | [ ] | |

---

## 8. 최종 판정

### 8-1. 판정 표

| 판정 | 해당 여부 | 근거 |
|---|---|---|
| GO | [ ] | 경로 A 또는 B 충족 + 운영 정책 GO 기준 충족 |
| CONDITIONAL GO | [ ] | 일부 보강은 됐으나 경로 A/B 미충족 또는 샘플 부족 |
| HOLD | [ ] | 기준1/기준5 위반, URL 누락, 구조 문제, 우회 발행 등 |

### 8-2. 최종 판정 문구

> **Phase 19 최종 판정: [GO / CONDITIONAL GO / HOLD]**

근거:
1.  
2.  
3.  

---

## 9. GO 전환 시 후속 조치

### GO인 경우
- Phase 19 close-out 보고 확정
- Phase 20 kickoff 또는 통합 handoff 문서 생성
- Track 1 / Track 2 미완 항목이 남아 있으면 모니터링 항목으로만 이관

### CONDITIONAL GO인 경우
- 다음 신규 발행 run 추가 확보
- 경로 A 또는 경로 B 충족 전까지 Phase 19 유지
- 보강 로그 누락 필드 또는 TYPE 샘플 부족 계속 추적

### HOLD인 경우
- 발행 차단 원인 우선 해결
- 기준1/기준5 / URL / 구조 문제 우선 수정
- 재실행 전 close-out 금지

---

## 10. 산출물 체크리스트

- [ ] 신규 발행 run_id
- [ ] 실제 발행본 본문 또는 핵심 검증 내용
- [ ] 공개 URL
- [ ] 15개 필드 기록 증거
- [ ] opener / 기준1 / 기준5 판정
- [ ] TYPE / fallback 정책 일치 여부
- [ ] 최종 판정
