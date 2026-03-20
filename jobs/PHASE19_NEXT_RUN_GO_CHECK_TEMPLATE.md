# PHASE19_NEXT_RUN_GO_CHECK_TEMPLATE

작성일: YYYY-MM-DD  
Phase: **Phase 19 — 다음 generator 실행 후 GO 체크 템플릿**  
목적: Phase 19 Track 1 로그 보강이 **실전 run**에서 실제 기록되는지 확인하고, 최종 GO 전환 여부를 판단한다.

---

## 1. 사용 시점

이 문서는 **Phase 19 이후 첫 신규 generator 실행 직후** 사용한다.

전제:
- Track 1 코드 반영 완료
- 최종 GO 전환 확인 보고에서 아직 **신규 run 부재**로 `CONDITIONAL GO` 상태
- 이번 문서는 그 빈칸을 채우는 **실전 확인용**이다

---

## 2. 이번 run 개요

| 항목 | 값 |
|---|---|
| run_id |  |
| 실행 시각 |  |
| slot |  |
| 발행 건수 |  |
| 공개 URL 수 |  |
| Post ID 목록 |  |
| PARSE_FAILED 발생 여부 |  |
| fallback_used 발생 여부 |  |
| final_status |  |

---

## 3. Route B 우선 확인

> 본 템플릿에서는 경로 B를 **정상 발행 3건 확인** 기준으로 고정한다.  
> `3회 연속 run`이 아니라 **동일 run 또는 연속 run 합산 3건의 실발행 샘플**로 판정한다.

| 확인 항목 | 결과 | 비고 |
|---|---|---|
| 정상 발행 3건 이상 확보 | [ ] | |
| 3건 모두 `slot != unknown` | [ ] | |
| 3건 모두 `post_type != unknown` | [ ] | |
| 3건 모두 `opener_pass` 기록 | [ ] | |
| 3건 모두 `criteria_1_pass` 기록 | [ ] | |
| 3건 모두 `criteria_5_pass` 기록 | [ ] | |
| 3건 모두 `source_structure_pass` 기록 | [ ] | |
| 공개 URL 3건 이상 확보 | [ ] | |
| generic opener 재발 없음 | [ ] | |
| HOLD 사유 없음 | [ ] | |

**Route B 판정:** [GO / 미충족]

---

## 4. Route A 보조 확인

> 이번 run에서 `PARSE_FAILED`가 발생했다면 Route A도 함께 확인한다.

| 확인 항목 | 결과 | 비고 |
|---|---|---|
| `PARSE_FAILED` 1건 이상 발생 | [ ] | |
| `[Phase 19]` 로그 포맷 확인 | [ ] | |
| `slot != unknown` | [ ] | |
| `post_type != unknown` | [ ] | |
| `picks_section_offset` 기록 | [ ] | |
| `opener_pass` 기록 | [ ] | |
| `criteria_1_pass` 기록 | [ ] | |
| `criteria_5_pass` 기록 | [ ] | |
| `source_structure_pass` 기록 | [ ] | |
| `closure / publish_blocked` 기록 | [ ] | |
| Axis B/C 정책 일치 | [ ] | |

**Route A 판정:** [GO / 미충족 / 해당 없음]

---

## 5. 대표 샘플 3건 기록표

| Post ID | slot | post_type | opener_pass | criteria_1_pass | criteria_5_pass | source_structure_pass | 공개 URL |
|---:|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |

---

## 6. PARSE_FAILED 샘플 기록표 (있을 때만)

| 필드 | 실제값 | 정상 여부 | 비고 |
|---|---|---|---|
| run_id |  |  | |
| slot |  |  | |
| post_type |  |  | |
| failure_type |  |  | |
| parse_stage |  |  | |
| failed_section_name |  |  | |
| raw_output_snapshot |  |  | |
| normalized_output_snapshot |  |  | |
| fallback_used |  |  | |
| publish_blocked |  |  | |
| picks_section_offset |  |  | |
| opener_pass |  |  | |
| criteria_1_pass |  |  | |
| criteria_5_pass |  |  | |
| source_structure_pass |  |  | |

---

## 7. 최종 판정

| 판정 | 해당 여부 | 근거 |
|---|---|---|
| GO | [ ] | Route A 또는 Route B 충족 |
| CONDITIONAL GO | [ ] | 실발행은 있었으나 GO 조건 일부 미충족 |
| HOLD | [ ] | 기준 위반, 구조 문제, URL 미확보, 정책 불일치 |

> **Phase 19 현재 판정: [GO / CONDITIONAL GO / HOLD]**

근거:
1.  
2.  
3.  

---

## 8. GO인 경우 후속 조치

- `REPORT_PHASE19_CLOSEOUT.md` 작성
- Phase 19 최종 판정 공식화
- Phase 20 kickoff 진행

## 9. CONDITIONAL GO인 경우 후속 조치

- 부족한 run / 샘플 추가 확보
- Route A 또는 B 재확인
- 미충족 필드 재기록

## 10. HOLD인 경우 후속 조치

- 기준1/기준5 / 구조 / URL / 정책 충돌 원인 우선 수정
- 재실행 전 close-out 금지
