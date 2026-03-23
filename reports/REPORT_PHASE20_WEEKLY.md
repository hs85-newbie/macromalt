# REPORT_PHASE20_WEEKLY.md

생성일시: 2026-03-20 07:36 UTC
데이터 소스: 로컬 logs/publish_result.jsonl (0건)
최종 판정: **CONDITIONAL GO**

---

## 1. 분석 기간

| 항목 | 값 |
|------|---|
| 시작 | 2026-03-13 07:36 UTC |
| 종료 | 2026-03-20 07:36 UTC |
| 기간 | 7일 |

---

## 2. 발행 실적 요약

| 항목 | 수 |
|------|---|
| 총 발행 run 수 | 0 |
| 총 실발행 수 (Post1 + Post2) | 0 |
| — Post1 (심층분석) | 0 |
| — Post2 (캐시의 픽) | 0 |
| 공개 URL 수 | 0 |


### final_status 분포

| 판정 | 수 |
|------|---|
| GO   | 0 |
| HOLD | 0 |

---

## 3. 슬롯 분포

| 슬롯 | 수 |
|------|---|

---

## 4. opener 회귀 여부 (Post2 기준)

| 항목 | 값 |
|------|---|
| opener_pass (pass 수) | 0 |
| opener_pass (fail 수) | 0 |
| opener 회귀 감지 | ✅ 없음 |
| generic opener 재발 | ✅ 없음 |

---

## 5. 품질 기준 통과율

| 기준 | FAIL 수 | 상태 |
|------|---------|------|
| criteria_1_pass | 0 | ✅ |
| criteria_5_pass | 0 | ✅ |
| source_structure_pass | 0 | ✅ |

---

## 6. 수동 확인 필요 항목

- [ ] 발행 실적 없음 → 파이프라인 실행 여부 확인 필요

---

## 7. PARSE_FAILED 현황

이 리포트는 Phase 19 정상발행 품질로그(post_type 구분)만 분석합니다.
PARSE_FAILED (WARNING 레벨 로그)는 `macromalt_daily.log` artifact를
직접 확인하거나 별도 PARSE_FAILED 집계 스크립트를 사용하십시오.

---

## 8. title duplication 회귀 여부

BUG-POST2-TITLE-DUP-20260320 수정 이후 회귀 여부는
공개 URL을 직접 방문하여 제목 2회 반복 여부를 확인하십시오.
자동 감지는 이번 리포트 범위 외입니다.

---

## 9. 발행 URL 목록

기간 내 공개 URL 없음

---

## 10. 최종 판정

**CONDITIONAL GO**

일부 기준 요주의. 수동 확인 후 계속.
