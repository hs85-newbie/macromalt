# REPORT_PHASE19_NEXT_RUN_GO_CHECK.md

작성일: 2026-03-20
Phase: **Phase 19 — 다음 generator 실행 후 GO 체크**
목적: Phase 19 Track 1 로그 보강이 실전 run에서 실제 기록되는지 확인하고, 최종 GO 전환 여부를 판단한다.

---

## 1. Run 개요

### Run 1

| 항목 | 값 |
|---|---|
| run_id | **20260320_132107** |
| 실행 시각 | 2026-03-20 13:21:07 |
| slot | **default** |
| 발행 건수 | 2건 |
| 공개 URL 수 | 2건 |
| Post ID 목록 | Post 223 (Post1), Post 224 (Post2) |
| PARSE_FAILED 발생 여부 | 없음 |
| fallback_used 발생 여부 | 없음 |
| final_status | **GO** |

- Post1 (223): https://macromalt.com/심층분석-증권업종과-게임-신작의-이익-추정치-상향/
- Post2 (224): https://macromalt.com/캐시의-픽-엔씨소프트-외-실적-모멘텀과-이익-추정/

### Run 2

| 항목 | 값 |
|---|---|
| run_id | **20260320_134131** |
| 실행 시각 | 2026-03-20 13:41:31 |
| slot | **default** |
| 발행 건수 | 2건 |
| 공개 URL 수 | 2건 |
| Post ID 목록 | Post 225 (Post1), Post 226 (Post2) |
| PARSE_FAILED 발생 여부 | 없음 |
| fallback_used 발생 여부 | 없음 |
| final_status | **GO** |

- Post1 (225): https://macromalt.com/심층분석-증권업종의-브로커리지-수익과-게임-신작/
- Post2 (226): https://macromalt.com/캐시의-픽-엔씨소프트-외-증권-및-게임-섹터의-실적/

---

## 2. Route B 우선 확인

> 본 템플릿에서는 경로 B를 **정상 발행 3건 확인** 기준으로 고정한다.
> `3회 연속 run`이 아니라 **동일 run 또는 연속 run 합산 3건의 실발행 샘플**로 판정한다.

| 확인 항목 | 결과 | 비고 |
|---|---|---|
| 정상 발행 3건 이상 확보 | ✅ | 4건 (Post 223~226) |
| 3건 모두 `slot != unknown` | ✅ | Run 1/2 모두 slot=default |
| 3건 모두 `post_type != unknown` | ✅ | T1-1 반영: post1/post2 하드코딩 확인 |
| 3건 모두 `opener_pass` 기록 | ⏳ | PARSE_FAILED 미발생 → 정상 발행 경로 로그 미기록 (구조적 제약) |
| 3건 모두 `criteria_1_pass` 기록 | ⏳ | 동일 — `_log_parse_failed_event()`에서만 기록됨 |
| 3건 모두 `criteria_5_pass` 기록 | ⏳ | 동일 |
| 3건 모두 `source_structure_pass` 기록 | ⏳ | 동일 |
| 공개 URL 3건 이상 확보 | ✅ | 4건 확보 |
| generic opener 재발 없음 | ✅ | Run 1/2 모두 재발 없음 |
| HOLD 사유 없음 | ✅ | |

**Route B 판정: 부분 충족** (발행 건수·slot·post_type·URL ✅. 4 pass 필드 로그 ⏳ 구조적 제약)

> **구조적 참고**: `opener_pass` 등 4개 권장 필드는 `_log_parse_failed_event()`에서만 기록된다.
> 정상 발행 경로에서는 필드 계산은 수행되나 로그에 별도 출력되지 않음.
> Route A(PARSE_FAILED 1건 발생) 시 즉시 GO 확정 가능.

---

## 3. Route A 보조 확인

| 확인 항목 | 결과 | 비고 |
|---|---|---|
| `PARSE_FAILED` 1건 이상 발생 | ❌ | Run 1/2 모두 발생 없음 |
| `[Phase 19]` 로그 포맷 확인 | — | 해당 없음 |
| `slot != unknown` | — | 해당 없음 |
| `post_type != unknown` | — | 해당 없음 |
| `picks_section_offset` 기록 | — | 해당 없음 |
| `opener_pass` 기록 | — | 해당 없음 |
| `criteria_1_pass` 기록 | — | 해당 없음 |
| `criteria_5_pass` 기록 | — | 해당 없음 |
| `source_structure_pass` 기록 | — | 해당 없음 |
| `closure / publish_blocked` 기록 | — | 해당 없음 |
| Axis B/C 정책 일치 | — | 해당 없음 |

**Route A 판정: 해당 없음** (Run 1/2 모두 PARSE_FAILED 미발생)

---

## 4. 대표 샘플 기록표

| Post ID | slot | post_type | opener_pass | criteria_1_pass | criteria_5_pass | source_structure_pass | 공개 URL |
|---:|---|---|---|---|---|---|---|
| 223 | default | post1 | ⏳ 미기록 | ⏳ 미기록 | ⏳ 미기록 | ⏳ 미기록 | ✅ |
| 224 | default | post2 | ⏳ 미기록 | ⏳ 미기록 | ⏳ 미기록 | ⏳ 미기록 | ✅ |
| 225 | default | post1 | ⏳ 미기록 | ⏳ 미기록 | ⏳ 미기록 | ⏳ 미기록 | ✅ |
| 226 | default | post2 | ⏳ 미기록 | ⏳ 미기록 | ⏳ 미기록 | ⏳ 미기록 | ✅ |

---

## 5. PARSE_FAILED 샘플 기록표

Run 1/2 모두 PARSE_FAILED 없음 — 해당 없음.

---

## 6. 추가 확인: Post2 제목 중복 버그 수정 실증

| 항목 | 결과 |
|---|---|
| 버그 ID | BUG-POST2-TITLE-DUP-20260320 |
| 수정 내용 | `publisher.py` `_strip_leading_h1()` regex 확장 (방안 A) |
| 수정 시점 | Run 1 이전 (2026-03-20) |
| 라이브 검증 | Post 224 페이지 확인: 제목 **1회만 출력** ✅ |
| Run 2 추가 확인 | Post 226 발행 정상 (동일 수정 적용) ✅ |

---

## 7. 최종 판정

| 판정 | 해당 여부 | 근거 |
|---|---|---|
| GO | ❌ | 4 pass 필드 로그 미확인 (구조적 제약, PARSE_FAILED 미발생) |
| **CONDITIONAL GO** | ✅ | 실발행 4건·slot/post_type 정상·공개 URL 4건·버그 수정 완료. 4 pass 필드만 미기록 |
| HOLD | ❌ | HOLD 트리거 사유 없음 |

> **Phase 19 현재 판정: CONDITIONAL GO** (진전 — GO 직전 상태)

근거:
1. Phase 19 T1 반영 후 2회 연속 실전 run(20260320_132107 / 20260320_134131) 완료. 총 4건 정상 발행, final_status=GO 2회 연속.
2. slot=default(≠unknown), post_type=post1/post2(≠unknown) 전건 확인. T1-1 로그 보강 정상 작동.
3. 4 pass 필드(opener_pass 등)는 PARSE_FAILED 미발생으로 미기록 — 구조적 제약. 다음 PARSE_FAILED 발생 시 Route A로 즉시 GO 확정 가능.

---

## 8. GO인 경우 후속 조치

- `REPORT_PHASE19_CLOSEOUT.md` 작성
- Phase 19 최종 판정 공식화
- Phase 20 kickoff 진행

## 9. CONDITIONAL GO인 경우 후속 조치

- 다음 PARSE_FAILED 발생 대기 → Route A 즉시 GO 확정
- 또는 정상 발행 로그에 4 pass 필드 추가 출력 코드 반영 → Route B 완전 충족

## 10. HOLD인 경우 후속 조치

- 기준1/기준5 / 구조 / URL / 정책 충돌 원인 우선 수정
- 재실행 전 close-out 금지
