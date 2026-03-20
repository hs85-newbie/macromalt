# REPORT_PHASE18_AXIS_B_FALLBACK_POLICY.md

작성일: 2026-03-20
Phase: **Phase 18 — Axis B 1차 실행**
범위: `fallback_used=True` 사례 수집 · 원인 분류 · 허용/차단 결정 · 정책 결론
데이터 기준: Phase 17 샘플 발행 5건 / Axis A 보고서 연계
참조 문서: REPORT_PHASE18_AXIS_A_CLOSURE_COLLECTION.md

---

## B-1. 사례 수집 표 — fallback 발생 케이스

### 대표 fallback 케이스: Post ID 187

| 항목 | 내용 |
|---|---|
| Post ID | 187 |
| 샘플 구분 | Phase 17 샘플 5번 (default 슬롯) |
| 발행 시각 | 2026-03-19 18:09:15 |
| `fallback_used` | **True** |
| `publish_blocked` | False |
| `verifier_revision_closure` | WARN |
| `parse_failed_type` | **TYPE_D** (PICKS 주석 누락 기준 — 500자 이상 본문에서 PICKS 주석 구조 판독 실패) |
| verifier skip 여부 | **Y** — Gemini verifier 응답 JSON 파싱 불가로 verifier 판정 미진행 |
| reviser 개입 여부 | **skip** — PARSE_FAILED 발생으로 reviser 단계 미진입 |
| 최종 발행 여부 | Y |
| opener 구조 유지 여부 | **PASS** — "왜 지금 S-Oil인가" (pick-angle 구조 유지) |
| 기준1 PASS 여부 | **PASS** — 최근 7일 기준 자료 중심 구성, 30일 초과 근거 사용 없음 |
| 기준5 PASS 여부 | **PASS** — "매수", "유망", "담아야 한다" 등 권유성 표현 없음 |
| 참고 출처 구조 유지 여부 | **PASS** — 상상인증권 / 한경 컨센서스 / 한국경제 / 매일경제 / 야후 파이낸스 / DART 정상 포함 |
| raw output 보관 여부 | Y — 3,888자, GPT 초안 원본 100.0% 보존 |
| normalized output 보관 여부 | Y — snapshot 필드 포함 (10필드 구조화 로그) |
| 핵심 이슈 요약 | Step3:verifier:json_parse 단계에서 Gemini 응답 JSON 파싱 불가 → TYPE_D 분류 → GPT 초안 원본 fallback 발행 → verifier/reviser 검수 경로 미완 상태로 정상 발행 |

#### PARSE_FAILED 런타임 로그 (Phase 17 실제 출력)

```
run_id=20260319_180909
slot=unknown
post_type=unknown
failure_type=TYPE_D
parse_stage=Step3:verifier:json_parse
failed_section=verifier_response
fallback_used=True
publish_blocked=False
```

#### 발행 URL

https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-s-oil-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ec%97%90%eb%84%88%ec%a7%80-%ec%84%b9%ed%84%b0/

---

### 비교군 A — 정상 PASS 케이스: Post ID 179

| 항목 | 내용 |
|---|---|
| Post ID | 179 |
| `fallback_used` | False |
| `publish_blocked` | False |
| `verifier_revision_closure` | **PASS** |
| `parse_failed_type` | 없음 |
| verifier skip 여부 | N (정상 판정) |
| reviser 개입 여부 | Y (정상 수렴) |
| opener 구조 유지 여부 | PASS |
| 기준1 / 기준5 | PASS / PASS |
| 참고 출처 구조 | PASS |
| 비고 | verifier 12건 → REVISED → PASS. 기준선 정상 케이스. |

### 비교군 B — fallback 없음 / closure FAIL 케이스: Post ID 177

| 항목 | 내용 |
|---|---|
| Post ID | 177 |
| `fallback_used` | False |
| `publish_blocked` | False |
| `verifier_revision_closure` | **FAIL** |
| `parse_failed_type` | 없음 |
| verifier skip 여부 | N (정상 판정) |
| reviser 개입 여부 | Y (미수렴 1건) |
| opener 구조 유지 여부 | PASS |
| 기준1 / 기준5 | PASS / PASS |
| 비고 | fallback 없이 정상 경로를 탔지만 closure FAIL → fallback과 closure FAIL은 별개 문제임을 확인 |

---

## B-2. 원인 분류 표

Post 187 기준:

| 분류 코드 | 설명 | 해당 여부 | 비고 |
|---|---|---|---|
| F1 | verifier 입력 파손으로 정상 검수 불가 | **Y** | TYPE_D: PICKS 주석 구간 판독 실패 → JSON parse 불가. verifier가 구조를 인식하지 못한 채 비정형 응답 반환. |
| F2 | `PARSE_FAILED` 발생 후 fallback 진입 | **Y** | step3_status=PARSE_FAILED → GPT 초안 원본 발행 경로. Phase 17 표준 처리 흐름. |
| F3 | reviser 미수렴 상태에서 fallback 진입 | N | reviser 단계 자체가 skip됨. 미수렴이 아니라 진입 전 종료. |
| F4 | source box / 체크포인트 / 본문 구조 일부 손실 상태 | N | 발행본 확인 기준 체크포인트 3개, 참고 출처 블록 정상 포함. |
| F5 | opener 구조는 유지되나 closure만 닫히지 않음 | **Y** | opener PASS + closure WARN. verifier 판정 경로 미완 → WARN 자동 적용 추정. |
| F6 | 실제 품질 기준 위반 동반 | N | 기준1 / 기준5 모두 PASS. 발행본 품질 기준 위반 없음. |
| F7 | publish 차단이 맞지만 우회 발행됨 | N | 현재 TYPE_D 정책상 publish_blocked=False가 적절. 차단 기준 해당 없음. |

**복합 태깅**: F1 + F2 + F5 (3개 동시 해당)

**해당 없는 코드**: F3 / F4 / F6 / F7

---

## B-3. 허용 / 경고 / 차단 결정표

| 상황 | 기본 판정 | 발행 허용 여부 | closure 처리 | 후속 조치 |
|---|---|---|---|---|
| verifier skip 발생, 본문 품질/구조 이상 없음 | WARN 허용 | ✅ 허용 | WARN | 10필드 로그 보존 의무 / 재발 시 TYPE 재분류 |
| `PARSE_FAILED` 발생, fallback 후 발행, 기준1/5 유지 | WARN 허용 | ✅ 허용 | WARN | raw/normalized/log 전체 보존 필수. TYPE 기록 의무. 재발 추적. |
| opener 구조 유지, 출처 구조 유지, closure만 WARN | WARN 허용 | ✅ 허용 | WARN | 모니터링 유지. 동일 패턴 반복 시 원인 분류 재수행. |
| source 구조 일부 손실 있으나 발행 진행 | FAIL | ❌ 차단 권고 | FAIL | publish_blocked=True 검토. 수동 점검 후 재발행. |
| 기준1 또는 기준5 실제 위반 | HOLD | ❌ 차단 | publish_blocked=True | 즉시 차단. 수동 개입 필수. |
| `TYPE_UNKNOWN` 반복 발생 (2건 이상) | FAIL | ❌ 차단 권고 | FAIL | 별도 관찰 버킷으로 이동. 원인 불명 누적 시 파이프라인 점검. |
| fallback 재발률이 임계치 초과 (30일 내 3건+) | WARN → FAIL 승격 | ❌ 차단 검토 | FAIL | 재발 통제 조치 의무화. 파이프라인 구조 점검 착수. |

**현재 기준 (Phase 17 데이터 기준)**

- fallback 발생: 1건 / 5건 (20%)
- TYPE_D 1건: 기준1/5 유지 → WARN 허용 판정 적용 중
- TYPE_UNKNOWN: 0건 — 임계치 미달

---

## B-4. 정책 결론 초안

### 8.1 허용 가능한 fallback (조건 정의)

아래 조건을 **모두** 만족할 경우 `fallback_used=True`를 제한적으로 허용한다.

| 조건 | 확인 방법 |
|---|---|
| opener 구조 유지 | 발행본 H3 구조 직접 확인 — pick-angle 패턴 여부 |
| 기준1 PASS | 최근 7일 중심 자료 구성 여부 / 30일 초과 근거 단독 사용 없음 |
| 기준5 PASS | 발행본 권유성 표현 없음 |
| 참고 출처 구조 유지 | 출처 블록(증권사 리서치 / 뉴스 / 기타) 정상 포함 |
| raw/normalized/log 보존 | 10필드 `_log_parse_failed_event()` 출력 확인 |
| `publish_blocked=False` 사유 기재 | PARSE_FAILED 유형별 사유 로그에 명시 |
| closure 결과 PASS 또는 정책상 허용 WARN | WARN 자동 부여 조건 명시 (아래 B-5 참조) |

### 8.2 WARN으로 허용할 fallback (현재 적용 기준)

아래 조건일 경우 발행은 허용하되 `WARN` 및 후속 모니터링 대상으로 둔다.

- `PARSE_FAILED` 발생 후 fallback 발행 (TYPE_A~TYPE_E 분류 완료된 경우)
- verifier skip 발생 (JSON parse 실패, 비정형 응답 반환 등)
- reviser skip 발생 (PARSE_FAILED 선행으로 reviser 미진입)
- 핵심 발행 품질 기준(기준1/5/opener/출처) 위반 없음
- 동일 유형 재발 여부 추적 필요

**현재 Post 187은 이 조건에 해당 → WARN 기반 허용 정책 적용 중**

### 8.3 허용 불가 fallback (발행 차단 조건)

아래 조건 중 하나라도 충족하면 fallback 허용 불가, publish_blocked=True 적용:

- 기준1 위반 (시점 혼합 / 30일 초과 근거 단독 사용)
- 기준5 위반 (권유성 표현 포함)
- opener 구조 파손 (generic opener 재등장 / pick-angle 미충족)
- 참고 출처 직접 대응 구조 손실 (출처 블록 전체 누락)
- `TYPE_UNKNOWN` 2건 이상 반복 누적
- source box / 체크포인트 / 종목 리포트 핵심 구조 손실
- publish 차단이 맞는 케이스가 우회 발행된 경우

---

## B-5. closure 매핑 정책

| 조건 | closure 권장값 | 비고 |
|---|---|---|
| 정상 경로, verifier/reviser 정상 완료, 이슈 없음 | PASS | 기준선. Post 179 패턴. |
| 정상 경로, verifier FAIL → reviser REVISED → 이슈 전체 해소 | PASS | verifier 이슈가 많아도 전부 해소 시 PASS. |
| 정상 경로, verifier FAIL → reviser REVISED → 고위험 1건 미해소 | WARN | Post 183 패턴. 발행 허용, 후속 모니터링. |
| 정상 경로, verifier FAIL → reviser REVISED → 고위험 2건+ 미해소 | FAIL | Post 177, 185 패턴. 발행은 진행되나 closure FAIL 기록. |
| PARSE_FAILED 발생, fallback 발행, 기준1/5/opener/출처 유지 | **WARN** | Post 187 패턴. verifier 경로 미완이므로 PASS 승격 불가. |
| PARSE_FAILED 발생, fallback 발행, 기준 위반 동반 | FAIL | 발행 차단 검토 필요. |
| 발행 차단이 맞는 케이스 | HOLD / publish_blocked=True | 수동 개입 필수. |

**운영 원칙**

1. `fallback_used=True`는 자동 FAIL이 아니다.
2. fallback은 원칙적으로 **PASS보다 WARN 우선**으로 본다.
3. WARN → PASS 승격은 **동일 슬롯/유형에서 3회 이상 재현 안정성 확인 후** 검토한다.
4. FAIL 발생 케이스는 발행 허용 여부와 별개로 반드시 원인 분류 후 후속 조치를 명기한다.

---

## B-6. 로그/증적 체크리스트 — Post 187 대조

| # | 필수 항목 | Post 187 확인 결과 |
|---|---|---|
| 1 | Post ID | ✅ 187 |
| 2 | 발행 시각 | ✅ 2026-03-19 18:09:15 |
| 3 | 발행 URL | ✅ 공개 URL 확보 |
| 4 | `fallback_used` | ✅ True |
| 5 | `publish_blocked` | ✅ False |
| 6 | `verifier_revision_closure` | ✅ WARN |
| 7 | `parse_failed_type` | ✅ TYPE_D |
| 8 | raw output snapshot | ✅ 3,888자 보존 (100.0%) |
| 9 | normalized output snapshot | ✅ 10필드 로그 포함 |
| 10 | verifier / reviser 로그 | ✅ PARSE_FAILED 로그 출력 확인 (step3:verifier:json_parse) |
| 11 | opener 구조 확인 결과 | ✅ PASS — "왜 지금 S-Oil인가" pick-angle 확인 |
| 12 | 기준1 / 기준5 판정 결과 | ✅ PASS / PASS |
| 13 | 참고 출처 구조 확인 결과 | ✅ PASS — 6종 출처 블록 정상 포함 |

**결론**: Post 187 기준 13개 필수 항목 **전항목 충족** ✅

**잔여 보완 항목**:
- `run_id`에서 `slot=unknown`, `post_type=unknown`이 기록됨 → PARSE_FAILED 시점에 슬롯 정보가 정상 주입되지 않는 현상. 로그 강화 대상.
- 로그에 `failed_section_name` 필드는 기록됐으나, PICKS 주석 구간의 구체적 위치(line 번호 또는 구간 offset)는 미기재. 세분화 권장.

---

## B-7. 최종 판정

### 정책 판정 질문 검토

| # | 질문 | 답변 |
|---|---|---|
| 1 | fallback 허용 조건은 충분히 좁은가? | **충분히 좁음** — 기준1/5/opener/출처 전체 PASS + 로그 보존 의무의 AND 조건. |
| 2 | fallback 허용이 발행 품질 기준 완화로 오해될 여지는 없는가? | **없음** — 허용 조건이 기준1/5/opener를 명시적으로 유지해야 함. fallback ≠ 기준 완화. |
| 3 | Post 187류 케이스는 현재 정책상 `WARN 허용`이 맞는가? | **맞음** — F1+F2+F5 복합, F6/F7 해당 없음. 발행 품질 위반 없음. WARN 기반 허용 적절. |
| 4 | 동일 유형 재발 시 `WARN → FAIL` 승격 조건이 있는가? | **있음 (B-3 명시)** — 30일 내 TYPE_D 3건 이상 재발 시 FAIL 승격 및 파이프라인 점검 착수. |
| 5 | `TYPE_UNKNOWN`에 대한 상한선이 정의됐는가? | **있음 (B-3 명시)** — 2건 이상 반복 누적 시 발행 차단 검토. |
| 6 | publish 차단이 필요한 조건이 명시됐는가? | **있음 (B-4 §8.3 명시)** — 7개 조건 열거. |
| 7 | 운영자가 보고서만 보고 허용/차단 판정을 재현할 수 있는가? | **가능** — B-1~B-6이 단독 판정 가능한 체계를 갖춤. |

### 판정

**정책 초안 확정 (방향성 확정 / 샘플 보강 권장)**

Phase 18 Axis B 결과, `fallback_used=True`는 전면 허용 또는 전면 금지가 아니라,
**정의된 품질 기준과 구조 보존 조건을 충족할 때에 한해 제한적으로 허용**하는 것으로 정리한다.

특히 `PARSE_FAILED` TYPE_D 또는 verifier skip이 발생하더라도,
실발행본 기준 opener 구조 · 기준1 · 기준5 · 참고 출처 구조가 유지되고,
raw/normalized/log 증적이 남는 경우에는 `WARN 기반 허용` 정책이 타당하다.

반대로 기준 위반 또는 구조 손실이 동반되는 fallback은 허용 대상이 아니며,
TYPE_UNKNOWN 반복 또는 재발률 임계치 초과 시 FAIL 승격 및 차단 조치를 적용한다.

**단, 현재 fallback 케이스가 Post 187 1건에 불과하므로:**

- WARN 허용 경계 조건은 추가 샘플 발행에서 재확인 필요
- TYPE_D 외 TYPE 발생 시 이 정책표에 추가 행 append 필요
- WARN → PASS 승격 조건은 추가 3건 이상 안정 재현 후 검토

---

## 축 B → 축 C/D 인계 포인트

| 인계 대상 | 내용 | 이관 축 |
|---|---|---|
| TYPE_D 대응 규칙 상세화 | PICKS 주석 구간 판독 실패 → 예방 가능한지 / 재시도 가능한지 검토 | 축 C |
| PARSE_FAILED 시 closure 자동 WARN 부여 로직 | 현재 PARSE_FAILED → closure WARN 경로가 명시적으로 코딩됐는지 확인 | 축 C |
| slot/post_type unknown 기록 문제 | PARSE_FAILED 시 슬롯 정보 미주입 현상 → 로그 보강 | 축 C |
| WARN 허용 반복 안정성 | 추가 샘플에서 TYPE_D 재발 여부 / opener 유지 여부 동시 확인 | 축 D |
