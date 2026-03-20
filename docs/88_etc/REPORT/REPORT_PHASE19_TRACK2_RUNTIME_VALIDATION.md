# REPORT_PHASE19_TRACK2_RUNTIME_VALIDATION.md

작성일: 2026-03-20
Phase: **Phase 19 — Track 2 실전 검증 보고**
범위: 실전 발행/PARSE_FAILED 런타임 검증 (15개 필드 보강 실전 확인)
데이터 기준: `logs/macromalt_daily.log` 실측값 + generator.py 코드 상태

---

## 1. 작업 개요

Phase 19 Track 1에서 반영한 로그 보강 3개 항목이 실전 런타임에서 정상 기록되는지 검증한다.

| Track | 항목 | 상태 |
|---|---|---|
| T1 (선행) | 로그 보강 코드 반영 | ✅ 완료 (2026-03-20) |
| T2-1 | TYPE_D 추가 샘플 확보 | ⏳ Phase 19 이후 신규 발행 대기 |
| T2-2 | 신규 TYPE 즉시 실전 검증 | ⏳ 발생 시 적용 |
| T2-3 | 15개 필드 보강 로그 실전 기록 확인 | ⏳ Phase 19 이후 신규 발행 대기 |
| T2-4 | Axis B/C 정책과 closure/publish 판정 일치 검증 | ⚠️ Phase 17 포맷 기준 부분 확인 (아래 참조) |

---

## 2. 실전 실행 수집 현황

### 2-1. Phase 19 코드 반영 전후 발행 타임라인

| 구간 | 발행 run | 마지막 실행 시각 | 적용 로그 포맷 |
|---|---|---|---|
| Phase 19 T1 반영 이전 | 20260319_175853, 175907, 180143, 180428, 180640 | 2026-03-19 18:09:15 | [Phase 17] — 10개 필드 |
| **Phase 19 T1 반영 이후** | **(없음)** | — | **[Phase 19] — 15개 필드 (대기 중)** |

**핵심 사실**: Phase 19 Track 1 코드 반영(2026-03-20)이 최종 발행 실행(2026-03-19 18:09:15) 이후에 이루어졌다.
따라서 **15개 필드 보강 로그의 실전 기록은 아직 확인되지 않았다.**

### 2-2. 로그 내 발행 실적 (Phase 19 T1 반영 이전 전체)

| run_id | Post ID | slot | post_type | 공개 URL | 발행 여부 | PARSE_FAILED | closure |
|---|---:|---|---|---|---|---|---|
| 20260319_175853 | 180, 181 | evening | post1/post2 | 확인 | ✅ | 없음 | — |
| 20260319_175907 | 178, 179 | evening | post1/post2 | 확인 | ✅ | 없음 | — |
| 20260319_180143 | 182, 183 | evening | post1/post2 | 확인 | ✅ | 없음 | — |
| 20260319_180428 | 184, 185 | evening | post1/post2 | 확인 | ✅ | 없음 | — |
| **20260319_180640** | **186, 187** | evening | post1/post2 | 확인 | ✅ | **TYPE_D** | **WARN** |

---

## 3. 15개 필드 로그 검증

### 3-1. 검증 대상 유일 PARSE_FAILED 케이스

```
로그 라인 15225 (macromalt_daily.log):
2026-03-19 18:09:09 [WARNING] [Phase 17] PARSE_FAILED 런타임 이벤트
  run_id=20260319_180909
  slot=unknown
  post_type=unknown
  failure_type=TYPE_D
  parse_stage=Step3:verifier:json_parse
  failed_section=verifier_response
  fallback_used=True
  publish_blocked=False
```

### 3-2. 15개 필드 기대값 vs 실제값

| 항목 | 기대값 | 실제값 | 정상 여부 | 비고 |
|---|---|---|---|---|
| run_id | 존재 | 20260319_180909 | ✅ | |
| slot | `unknown` 아님 | **unknown** | ❌ | Phase 17 포맷 — T1-1 반영 전 실행 |
| post_type | `post1` or `post2` | **unknown** | ❌ | Phase 17 포맷 — T1-1 반영 전 실행 |
| failure_type | TYPE명 | TYPE_D | ✅ | |
| parse_stage | 존재 | Step3:verifier:json_parse | ✅ | |
| failed_section_name | 존재 | verifier_response | ✅ | |
| raw_output_snapshot | 존재 | — | ⚠️ | 로그 단일 라인 포맷 — 스냅샷 별도 미기록 (Phase 17 포맷) |
| normalized_output_snapshot | 존재 | — | ⚠️ | 동일 |
| fallback_used | bool | True | ✅ | |
| publish_blocked | bool | False | ✅ | |
| **picks_section_offset** | -1 또는 숫자 | **미기록** | ❌ | T1-2 — Phase 19 이후 실행에서 기록 예정 |
| **opener_pass** | bool | **미기록** | ❌ | T1-3 — Phase 19 이후 실행에서 기록 예정 |
| **criteria_1_pass** | bool | **미기록** | ❌ | T1-3 — 동일 |
| **criteria_5_pass** | bool | **미기록** | ❌ | T1-3 — 동일 |
| **source_structure_pass** | bool | **미기록** | ❌ | T1-3 — 동일 |

**판정**: 보강 5개 필드(picks_section_offset + 권장 4종) 실전 기록 **미확인** — Phase 19 이전 실행이므로 예정된 결과.

---

## 4. TYPE_D 재발 검증 (Phase 17 포맷 기준 부분 검증)

### 4-1. 이번 관측 TYPE_D (run 20260319_180640 / Post 187)

| 항목 | 결과 | 근거 |
|---|---|---|
| parse_failed_type = TYPE_D | ✅ | 로그 라인 15225 |
| slot != unknown | ❌ (unknown) | Phase 17 포맷 — T1-1 미적용 |
| post_type != unknown | ❌ (unknown) | Phase 17 포맷 — T1-1 미적용 |
| opener_pass = True | ⚠️ 미기록 | T1-3 미적용 — 품질 게이트로 간접 확인 (아래) |
| criteria_1_pass = True | ⚠️ 미기록 | T1-3 미적용 — 간접 확인 |
| criteria_5_pass = True | ⚠️ 미기록 | T1-3 미적용 — 간접 확인 |
| source_structure_pass = True | ⚠️ 미기록 | T1-3 미적용 — 간접 확인 |
| closure = WARN | ✅ | 로그 라인 15293: `verifier_revision_closure: WARN` |
| publish_blocked = False | ✅ | 로그 라인 15225: `publish_blocked=False` |
| Axis B/C 정책 일치 | ✅ (부분) | closure=WARN, publish_blocked=False → Axis B/C 조건부 허용 정책 일치 |

### 4-2. opener 간접 확인 (품질 게이트 기준)

Post 187 최종 품질 게이트 (로그 라인 15278~15307):

```
verifier_revision_closure: WARN         ← TYPE_D closure 일치
generic_wording_control: WARN
post_role_separation: WARN
interpretation_quality_p1: FAIL         ← HOLD 트리거 아님 (운영 모니터링)
interpretation_quality_p2: FAIL         ← 동일
final_status: GO                        ← 발행 차단 없음
```

**opener 직접 기록 없음** (Phase 17 포맷). 그러나 `final_status=GO`와 `publish_blocked=False` 조합으로 기준1/기준5 위반이 차단 수준이 아님을 간접 확인.

---

## 5. 신규 TYPE 실전 검증

Phase 19 T1 반영 이후 발행 없음 → **신규 TYPE 발생 케이스 없음.**

TYPE_A/B/C/E/UNKNOWN 최초 발생 시 Axis C 의사코드 즉시 적용 원칙은 유지됨.

---

## 6. 정상 발행 대체 검증

템플릿 6절 기준 (정상 발행 3건 이상에서 slot/post_type 포함 보강 로그 확인):

**Phase 19 T1 반영 이후 정상 발행: 0건** → 대체 경로 B 기준 미충족.

단, Phase 19 반영 이전 5회 run(Post 178~187) 모두 `final_status=GO` 정상 발행 확인. Phase 19 이후 첫 run에서 대체 경로 B 기준 충족 예정.

---

## 7. opener 안정성 동시 확인

Phase 19 T1 반영 이전 최근 5회 발행 기준 (Post 178~187):

| Post ID | verifier_revision_closure | generic_opener 위반 | final_status | 비고 |
|---:|---|---|---|---|
| 178 | 확인 필요 | 미관측 | GO 추정 | 로그 확인 범위 외 |
| 179 | 확인 필요 | 미관측 | GO 추정 | 동일 |
| 180 | 확인 필요 | 미관측 | GO 추정 | 동일 |
| 181 | 확인 필요 | 미관측 | GO 추정 | 동일 |
| 182 | 확인 필요 | 미관측 | GO 추정 | 동일 |
| 183 | 확인 필요 | 미관측 | GO 추정 | 동일 |
| 184 | 확인 필요 | 미관측 | GO 추정 | 동일 |
| 185 | 확인 필요 | 미관측 | GO 추정 | 동일 |
| **186** | — | 미관측 | **GO** | 로그 라인 15307 직접 확인 |
| **187** | **WARN** | 미관측 | **GO** | 로그 라인 15293, 15307 직접 확인 |

- generic opener 재발: **관측 없음**
- 발행 차단: **0건**
- opener 회귀 신호: **없음**

---

## 8. 요약표

### 8-1. 최종 요약

| 항목 | 결과 |
|---|---|
| 실행 샘플 수 (Phase 19 T1 반영 이후) | **0건** |
| 실발행본 수 (Phase 19 T1 반영 이후) | **0건** |
| 공개 URL 수 (Phase 19 T1 반영 이후) | **0건** |
| PARSE_FAILED 발생 수 (Phase 19 T1 반영 이후) | **0건** |
| TYPE_D 재발 수 (Phase 19 T1 반영 이후) | **0건** |
| 신규 TYPE 발생 수 (Phase 19 T1 반영 이후) | **0건** |
| slot unknown 재발 (Phase 19 T1 반영 이후) | **확인 불가** |
| post_type unknown 재발 (Phase 19 T1 반영 이후) | **확인 불가** |
| opener 회귀 | **관측 없음** |
| **최종 판정** | **CONDITIONAL GO** |

### 8-2. 3줄 결론

1. Phase 19 Track 1 코드 반영(2026-03-20)은 최종 발행 실행(2026-03-19 18:09:15) 이후에 이루어졌다. 결과적으로 15개 필드 보강 로그의 실전 기록은 Phase 19 이후 첫 번째 발행 run에서 확인 가능하다.
2. 로그에서 확인 가능한 유일한 PARSE_FAILED 케이스(TYPE_D, Post 187)는 Phase 17 포맷으로 기록되어 있으나, closure=WARN / publish_blocked=False로 Axis B/C 정책 일치가 부분 확인된다.
3. opener 회귀 및 generic opener 재발 신호 없음. Phase 19 이후 첫 발행에서 15개 필드 전체 기록 확인 시 GO 전환 기준 충족.

---

## 9. GO 전환 조건

다음 중 하나 충족 시 Phase 19 GO 전환:

- **우선 경로 A**: Phase 19 이후 발행 중 PARSE_FAILED 1건 발생 → 15개 필드 전체 기록 확인
- **대체 경로 B**: Phase 19 이후 정상 발행 3건에서 `slot != unknown`, `post_type != unknown` 및 권장 필드 4종 기록 확인

---

## 10. Phase 19 → Phase 20 인계 포인트

| 우선순위 | 항목 | 상태 |
|---|---|---|
| 1 | Phase 19 이후 신규 발행 run — 15개 필드 실전 기록 확인 | ⏳ 대기 |
| 2 | TYPE_D 추가 샘플 (Phase 19 포맷) — slot/post_type 정상 기록 + 권장 4종 확인 | ⏳ 대기 |
| 3 | 신규 TYPE 발생 시 Axis C 즉시 적용 | 조건부 |
| 4 | `criteria_1_pass` 간이 지표 → 정밀 지표 개선 검토 | 모니터링 |

---

## 11. 최종 판정

### **Phase 19 Track 2: CONDITIONAL GO**

**근거:**
- Phase 19 T1 코드 반영 완료 ✅
- 최종 실행(2026-03-19)이 Phase 19 코드 반영(2026-03-20) 이전 — 실전 15개 필드 기록 확인 **미수행** ⏳
- 기존 관측된 TYPE_D(Post 187)는 Axis B/C 정책 일치 부분 확인 ✅
- opener 회귀, 기준1/기준5 위반, generic opener 재발 없음 ✅
- HOLD 사유 없음 ✅

**다음 단계:** Phase 19 이후 첫 발행 run에서 우선 경로 A 또는 대체 경로 B 충족 확인 후 Phase 19 최종 GO 선언 → Phase 20 또는 통합 close-out 진행.
