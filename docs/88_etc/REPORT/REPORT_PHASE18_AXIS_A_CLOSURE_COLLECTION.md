# REPORT_PHASE18_AXIS_A_CLOSURE_COLLECTION.md

작성일: 2026-03-20
Phase: **Phase 18 — Axis A 1차 실행**
범위: `verifier_revision_closure FAIL/WARN` 사례 수집 · 원인 유형 분해 · 우선순위 결론
데이터 기준: Phase 17 샘플 발행 5건 (Post 177 / 179 / 183 / 185 / 187)

---

## A-1. 사례 수집 표 — 완성본

| run_id | Post ID | 발행 시각 | opener 적합 여부 | verifier_revision_closure | verifier 이슈 건수 | reviser 개입 여부 | fallback_used | parse_failed_type | publish_blocked | 최종 발행 여부 | 비고 |
|---|---:|---|---|---|---:|---|---|---|---|---|---|
| 20260319_173621 | 177 | 2026-03-19 17:36:21 | PASS | **FAIL** | 26건 | Y | False | 없음 | False | Y | 미해소 1건 |
| 20260319_180138 | 179 | 2026-03-19 18:01:38 | PASS | **PASS** | 12건 | Y | False | 없음 | False | Y | 기준선(정상) |
| 20260319_180355 | 183 | 2026-03-19 18:03:55 | PASS | **WARN** | (고위험 5건) | Y | False | 없음 | False | Y | 미해소 1건 |
| 20260319_180619 | 185 | 2026-03-19 18:06:19 | PASS | **FAIL** | 14건 | Y | False | 없음 | False | Y | 미해소 3건 |
| 20260319_180909 | 187 | 2026-03-19 18:09:15 | PASS | **WARN** | — | skip | True | TYPE_D | False | Y | PARSE_FAILED fallback 발행 |

**요약**: FAIL 2건(Post 177, 185) / WARN 2건(Post 183, 187) / PASS 1건(Post 179)
→ FAIL/WARN 발생률: 4/5 (80%)

---

## A-2. 사례별 상세 기록

---

### Case A-01 — Post ID 177

- run_id: 20260319_173621
- 발행 시각: 2026-03-19 17:36:21
- 최종 발행 여부: Y
- opener 적합 여부: PASS ("왜 지금 삼성전자인가")
- verifier_revision_closure: **FAIL**
- verifier 이슈 건수: 26건
- reviser 개입 여부: Y
- fallback_used: False
- parse_failed_type: 없음
- publish_blocked: False

#### 1) 직접 관찰된 현상

- verifier가 26건의 이슈를 발견했다.
- reviser가 개입하여 수정본을 생성했다 (GPT 초안 3,314자 → Step3 수정본 3,237자, 97.7% 보존).
- 고위험 12건 중 11건이 해소되었으나, 1건이 미해소 상태로 남았다.
- closure 판정: FAIL (미해소 1건 기준).
- 발행본 품질은 기준1/기준5 기준 위반 없음.

#### 2) 문제 발생 위치

- verifier 항목: 고위험 미해소 1건 (구체적 항목 번호 로그 미기재 — 추가 로그 강화 필요)
- 관련 섹션: 미특정 (verifier 26건 중 마지막 미해소 항목)
- 관련 문장/구간: 현재 로그에서 세부 구간 식별 불가

#### 3) 1차 원인 분류

- [ ] C1. verifier strictness 문제 — 일부 가능성 존재 (26건 중 25건 해소는 reviser 수렴 성공에 가까움)
- [x] C2. reviser 미수렴 문제 — **주요 원인**: 다수 이슈 해소 후 마지막 1건 미수렴
- [ ] C3. parser/verifier 입력 문제
- [ ] C4. fallback 경로 문제
- [ ] C5. 기타 / 미확정

#### 4) 판단 근거

- 26건 중 25건(96.2%)을 해소했음에도 closure FAIL → reviser는 정상 동작하고 있으나, 마지막 1건 유형이 reviser 보정 규칙에 부재한 패턴일 가능성.
- 발행본 품질이 수용 가능한 수준임에도 closure FAIL → C1(strictness) 복합 가능성도 배제할 수 없음.
- 이슈 수 26건은 Phase 17 샘플 중 최다 — 초고 생성 품질 자체가 낮았을 수 있음.

#### 5) 필요한 후속 조치

- [ ] 코드 수정 필요
- [ ] verifier 기준 완화/정교화 필요
- [x] reviser 규칙 보강 필요 — 미해소 1건 유형 로그 세부 기록 강화 후 재판단
- [ ] fallback 정책 문서화 필요
- [x] 모니터링 유지 후 재판단 — 미해소 이슈 유형 추가 로그 확보 시 재분류

#### 6) 임시 결론

- C2(reviser 미수렴)로 1차 분류하나, 미해소 항목 세부 로그 부재로 C1 복합 가능성 유지.
- 즉시 코드 수정 대상이 아니라, **reviser 미해소 이슈 유형 세분화 로그 강화 → 재분류** 경로가 적절.
- 발행 품질 영향도: Low — 발행본 기준1/기준5 위반 없음.

---

### Case A-02 — Post ID 183

- run_id: 20260319_180355
- 발행 시각: 2026-03-19 18:03:55
- 최종 발행 여부: Y
- opener 적합 여부: PASS ("왜 지금 SK이노베이션인가")
- verifier_revision_closure: **WARN**
- verifier 이슈 건수: 고위험 5건 (전체 건수 로그 미기재)
- reviser 개입 여부: Y
- fallback_used: False
- parse_failed_type: 없음
- publish_blocked: False

#### 1) 직접 관찰된 현상

- verifier가 이슈를 발견하고 reviser가 개입했다 (GPT 초안 3,556자 → Step3 수정본 3,722자, 104.7% 보존 — 수정본이 오히려 분량 증가).
- 고위험 5건 중 4건 해소 / 1건 미해소 → WARN 판정.
- 발행본 품질은 기준1/기준5 기준 위반 없음.
- 수정본 분량이 초고보다 증가(+4.7%)한 점이 이례적.

#### 2) 문제 발생 위치

- verifier 항목: 고위험 미해소 1건 (구체적 항목 번호 로그 미기재)
- 관련 섹션: 미특정
- 관련 문장/구간: 현재 로그에서 세부 구간 식별 불가

#### 3) 1차 원인 분류

- [ ] C1. verifier strictness 문제
- [x] C2. reviser 미수렴 문제 — **주요 원인**: 고위험 5건 중 1건 미해소
- [ ] C3. parser/verifier 입력 문제
- [ ] C4. fallback 경로 문제
- [ ] C5. 기타 / 미확정

#### 4) 판단 근거

- Case A-01과 동일한 패턴 — reviser 개입 후 다수 해소이나 마지막 1건 미수렴.
- 수정본 분량이 104.7%로 초고보다 증가한 점은 reviser가 추가 내용을 삽입하며 수정을 시도했음을 시사 — 그럼에도 미해소 1건이 남은 것은 reviser가 해당 이슈 유형에 대한 보정 전략이 부재함을 의미.
- WARN(FAIL보다 경미) → 발행 품질 영향도 Low.

#### 5) 필요한 후속 조치

- [ ] 코드 수정 필요
- [ ] verifier 기준 완화/정교화 필요
- [x] reviser 규칙 보강 필요 — 미해소 이슈 유형 세분화 로그 강화 후 재판단
- [ ] fallback 정책 문서화 필요
- [x] 모니터링 유지 후 재판단

#### 6) 임시 결론

- C2(reviser 미수렴)로 분류. A-01과 동일 유형.
- WARN 수준이므로 즉시 수정 대상이 아닌 모니터링 + 로그 강화 경로.
- 발행 품질 영향도: Low.

---

### Case A-03 — Post ID 185

- run_id: 20260319_180619
- 발행 시각: 2026-03-19 18:06:19
- 최종 발행 여부: Y
- opener 적합 여부: PASS ("왜 지금 S-Oil인가")
- verifier_revision_closure: **FAIL**
- verifier 이슈 건수: 14건 (고위험 3건 포함)
- reviser 개입 여부: Y
- fallback_used: False
- parse_failed_type: 없음
- publish_blocked: False

#### 1) 직접 관찰된 현상

- verifier 14건 발견 → reviser REVISED (GPT 초안 2,874자 → Step3 수정본 2,835자, 98.6% 보존).
- 고위험 3건 중 2건 해소 / 1건 미해소 → FAIL 판정.
- 발행본 품질은 기준1/기준5 기준 위반 없음.
- 보고서에 "Post2 기준 별도 FAIL — 14건 발생"이라고 기재된 점이 이례적 → FAIL 분류 판정이 Post2 전용 로직과 관련될 수 있음.

#### 2) 문제 발생 위치

- verifier 항목: 고위험 미해소 1건 (Post2 전용 closure 판정 로직 관련 가능성)
- 관련 섹션: 미특정
- 관련 문장/구간: 현재 로그에서 세부 구간 식별 불가

#### 3) 1차 원인 분류

- [x] C1. verifier strictness 문제 — **부분 가능성**: "Post2 기준 별도 FAIL" 기재가 Post2 전용 closure 기준이 상대적으로 엄격할 수 있음을 시사
- [x] C2. reviser 미수렴 문제 — **주요 원인**: 고위험 1건 미해소
- [ ] C3. parser/verifier 입력 문제
- [ ] C4. fallback 경로 문제
- [ ] C5. 기타 / 미확정

#### 4) 판단 근거

- A-01, A-02와 동일하게 고위험 마지막 1건 미해소 패턴.
- "Post2 기준 별도 FAIL" 표현이 보고서에 명시된 점 → Post2용 closure 판정 기준이 별도로 존재하거나, 이슈 건수(14건)가 Post2 기준 임계값을 초과한 것으로 해석 가능 → C1(strictness) 복합 가능성.
- 이 케이스가 C1+C2 복합인지, 순수 C2인지는 verifier closure 판정 로직 세부 코드 확인 필요.

#### 5) 필요한 후속 조치

- [ ] 코드 수정 필요
- [x] verifier 기준 완화/정교화 필요 — "Post2 기준 별도 FAIL" 로직 확인 및 false fail 여부 검토
- [x] reviser 규칙 보강 필요 — 미해소 이슈 유형 세분화
- [ ] fallback 정책 문서화 필요
- [x] 모니터링 유지 후 재판단

#### 6) 임시 결론

- C2 기본 + C1 복합 가능성으로 분류.
- A-01, A-02보다 우선순위 한 단계 높음 — "Post2 기준 별도 FAIL" 로직 세부 확인 필요.
- 발행 품질 영향도: Mid (FAIL이나 발행본 품질 자체는 수용 가능).

---

### Case A-04 — Post ID 187

- run_id: 20260319_180909
- 발행 시각: 2026-03-19 18:09:15
- 최종 발행 여부: Y
- opener 적합 여부: PASS ("왜 지금 S-Oil인가")
- verifier_revision_closure: **WARN**
- verifier 이슈 건수: — (PARSE_FAILED로 verifier 판정 미진행)
- reviser 개입 여부: skip (PARSE_FAILED로 reviser 미진행)
- fallback_used: **True**
- parse_failed_type: **TYPE_D**
- publish_blocked: False

#### 1) 직접 관찰된 현상

- Gemini verifier 응답 JSON 파싱 불가 → PARSE_FAILED.
- Phase 17 신규 분류: TYPE_D (PICKS 주석 누락 기준).
- reviser 단계가 skip되고 GPT 초안 원본 발행 경로 사용 (3,888자, 100.0% 보존).
- publish_blocked=False → 정상 발행 완료.
- 발행 후 verifier_revision_closure: WARN (verifier 결과가 없으므로 closure 판정 미완 상태로 WARN 적용된 것으로 추정).

#### 2) 문제 발생 위치

- verifier 항목: Step3:verifier:json_parse 단계
- 관련 섹션: verifier_response (PICKS 주석 구간 — TYPE_D 분류 기준)
- 관련 문장/구간: Gemini verifier 응답 자체가 JSON 비정형 반환

#### 3) 1차 원인 분류

- [ ] C1. verifier strictness 문제
- [ ] C2. reviser 미수렴 문제
- [x] C3. parser/verifier 입력 문제 — **주요 원인**: verifier JSON parse 자체 실패 (TYPE_D)
- [x] C4. fallback 경로 문제 — **복합 원인**: fallback_used=True이나 fallback 허용 조건/정책이 미문서화
- [ ] C5. 기타 / 미확정

#### 4) 판단 근거

- parse_failed_type=TYPE_D: PICKS 주석 구간 판독 실패 → verifier가 PICKS 주석 구조를 인식하지 못한 채 JSON 비정형 응답을 반환.
- fallback_used=True + publish_blocked=False → 현재는 TYPE_D 발생 시 일괄 발행 허용 정책이나, 이 허용 기준이 명문화되지 않은 상태.
- WARN이 PARSE_FAILED 시 자동 부여되는지 closure 로직에서 명시적으로 처리하는지 불명확.

#### 5) 필요한 후속 조치

- [ ] 코드 수정 필요
- [ ] verifier 기준 완화/정교화 필요
- [ ] reviser 규칙 보강 필요
- [x] fallback 정책 문서화 필요 — **최우선**: TYPE_D 발행 허용 조건, PARSE_FAILED 시 closure 자동 WARN 처리 로직 명문화
- [x] 모니터링 유지 후 재판단 — TYPE_D 재발 여부 + 타 TYPE 발생 여부 관찰

#### 6) 임시 결론

- C3+C4 복합으로 분류. **축 B(fallback 정책 정교화)와 축 C(PARSE_FAILED 대응 규칙)로 인계하는 대표 사례.**
- 즉시 코드 수정 대상이 아닌 정책 문서화 우선 대상.
- 발행 품질 영향도: Mid (발행본 기준1/기준5 위반 없음, 단 verifier 검수 경로 미완).

---

## A-3. 원인 유형 분포표

| 유형 | 건수 | 대표 Post ID | 현재 영향도 | 즉시 수정 필요 여부 | 비고 |
|---|---:|---|---|---|---|
| C1 verifier strictness | 1 (복합) | 185 | Mid | N | "Post2 기준 별도 FAIL" 로직 확인 필요. C2 복합. |
| C2 reviser 미수렴 | 3 | 177, 183, 185 | Mid | N | 반복 패턴. 미해소 이슈 유형 로그 세분화 후 재판단. |
| C3 parser/verifier 입력 | 1 | 187 | Mid | N | TYPE_D. fallback 발행 허용 정책 연계. |
| C4 fallback 경로 | 1 | 187 | Mid | N | 정책 미문서화. 축 B로 이관. |
| C5 기타/미확정 | 0 | — | — | — | — |

**핵심 패턴 요약**

1. **C2(reviser 미수렴)가 3건으로 최다** — 공통 패턴: 고위험 이슈 마지막 1건이 반복적으로 미해소.
2. **C3+C4 복합(Post 187)** — PARSE_FAILED 시 closure 경로가 정상 비활성화됨에도 WARN이 부여됨 → fallback 시 closure 처리 로직 명문화 필요.
3. **C1(verifier strictness)**은 아직 독립 확정 불가 — C2 복합 가능성으로 유지.
4. **opener와 closure 문제는 완전 분리 확인** — 5건 모두 opener PASS, closure FAIL/WARN은 opener와 무관.

---

## A-4. 3분류 결론

```md
## Axis A — 1차 결론

### 즉시 수정 필요
- 없음 (현재 발행 품질 기준1/기준5 위반 없음, 발행 차단 없음)
- 단, 추가 샘플에서 고위험 미해소 건이 발행 품질에 직접 영향을 미칠 경우 즉시 재판단

### 정책 명문화 우선
- C4: PARSE_FAILED(TYPE_D) 발생 시 fallback 발행 허용 조건 명문화 (축 B 이관)
- C3+C4: PARSE_FAILED 시 verifier_revision_closure WARN 자동 부여 여부 명시 (축 C 이관)
- C1 복합: "Post2 기준 별도 FAIL" 판정 로직 세부 확인 후 false fail 여부 기준 문서화

### 모니터링 유지
- C2: reviser 미수렴 패턴 — 미해소 이슈 유형 로그 세분화 후 반복 시 reviser 규칙 보강
- C1: verifier strictness — 추가 샘플에서 고위험 0건이지만 closure FAIL 사례 발생 시 독립 분류

### 축 B/C/D로 넘길 인계 포인트
- 축 B: Post 187 (C4) — fallback_used=True 케이스 정책 정교화
- 축 C: Post 187 (C3) — PARSE_FAILED TYPE_D 대응 규칙 + PICKS 주석 구간 판독 안정화
- 축 D: opener 반복 안정성 — 5건 모두 PASS이나 추가 샘플 확보 필요
- 공통 인계: reviser 미해소 이슈 유형 세분화 로그 — 축 A 2차 분석에서 C1/C2 재분류 기반
```

---

## 참고: PASS 기준선 (Post 179)

| 항목 | 값 |
|------|-----|
| step3_status | REVISED |
| verifier 이슈 건수 | 12건 |
| reviser 개입 | Y |
| 보존율 | 99.6% |
| verifier_revision_closure | **PASS** |
| fallback_used | False |

**Post 179가 PASS를 달성한 차별점 분석:**

- 이슈 12건은 Post 177(26건), Post 185(14건)보다 적음 → 이슈 건수 자체가 적을수록 reviser 수렴 성공률 높음.
- 고위험 이슈 세부 기록이 부재하여 "이슈 유형의 차이"가 결정적 요인인지는 불명확.
- 기준선으로 삼아 C2 분석 시 이슈 건수 임계값(약 12건 이하 → PASS 가능성 높음) 가설 수립 가능.

---

## Axis A 완료 기준 체크

- [x] 최근 샘플 발행본 기준 `closure FAIL/WARN` 사례가 전부 표준 양식으로 수집됨 (4건)
- [x] 각 사례가 최소 1개 원인 유형(C1~C5)으로 분류됨
- [x] `fallback_used=True` 사례가 별도 식별됨 (Post 187 — 축 B 이관)
- [x] Post 187 예외 경로 사례가 축 B/C로 넘길 수 있게 정리됨
- [x] opener 문제와 closure 문제가 혼동 없이 분리 기록됨
