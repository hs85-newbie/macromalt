# Phase 18 Axis C — PARSE_FAILED 대응 규칙 템플릿

- 문서명: `PHASE18_AXIS_C_RESPONSE_RULES_TEMPLATE.md`
- 목적: `PARSE_FAILED` 발생 시 유형별 대응 규칙, closure 매핑, 로그 보강 규칙, 허용/차단 기준을 문서화한다.
- 범위: Phase 18 Axis C
- 전제: 본 문서는 구조 개편 문서가 아니라 운영 안정화 문서다.

---

## 0. 작성 원칙

이번 Axis C의 목적은 `PARSE_FAILED`를 “없애는 것”이 아니라, 발생 시 아래 4가지를 안정적으로 수행할 수 있도록 규칙을 고정하는 데 있다.

1. 유형 분류 가능
2. 로그 보존 가능
3. closure 판정 일관화
4. publish 허용/차단 기준 일관화

이번 문서에서는 아래 항목을 변경하지 않는다.

- pick-angle opener 구조
- generic opener 금지 규칙
- Phase 17에서 확정한 `TYPE_A ~ TYPE_E / TYPE_UNKNOWN` 분류 체계
- 실발행본 + 공개 URL 기준 검증 원칙

---

## 1. 수집 범위

이번 Axis C에서 다루는 케이스 범위:

- `parse_failed_type`가 실제 기록된 케이스
- `verifier JSON parse 실패` 또는 `verifier skip` 케이스
- `fallback_used=True`로 이어진 케이스
- `slot/post_type unknown` 등 로그 불완전 케이스
- 동일 유형 반복 여부를 확인할 수 있는 비교군

수집 대상 예시:

- 대표 케이스: Post 187
- 비교군: fallback 미사용 정상 발행 케이스 1~2건
- 필요 시 동일 기간 WARN/FAIL 케이스 추가

---

## 2. 케이스 인벤토리 표 (C-1)

| Post ID | Published | parse_failed_type | verifier 상태 | fallback_used | closure | publish_blocked | opener PASS | 기준1/5 PASS | source 구조 유지 | 로그 완전성 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 예시 | Y | TYPE_D | JSON parse fail / skip | True | WARN | False | Y | Y | Y | 부분보완 필요 | 대표 케이스 |

작성 규칙:
- `verifier 상태`에는 `정상`, `JSON parse fail`, `skip`, `partial` 중 하나를 적는다.
- `로그 완전성`은 `완전`, `보완 필요`, `불충분` 중 하나로 적는다.
- `source 구조 유지`는 source box / 참고 출처 / 대응 링크 구조 기준으로 적는다.

---

## 3. 유형별 원인 정의 표 (C-2)

아래 표를 실제 관측 결과에 맞게 채운다.

| TYPE | 정의 | 대표 징후 | 주요 원인 후보 | 발행 영향도 | 기본 closure | 기본 publish 판정 | 즉시 수정 필요 여부 | 축 연계 |
|---|---|---|---|---|---|---|---|---|
| TYPE_A | H2/H3 구조 누락 또는 섹션 순서 불일치 | 섹션 누락, 순서 역전 | writer/reviser 출력 구조 이탈 | High | FAIL | 차단 우선 | 예 | A/D |
| TYPE_B | 금지 opener 패턴으로 인한 후처리 불일치 | generic opener, macro recap 시작 | opener 규칙 미준수 | Mid~High | FAIL 또는 WARN | 조건부 차단 | 예 | D |
| TYPE_C | HTML 태그 파손 또는 중첩 오류 | 태그 미닫힘, block 깨짐 | serializer / formatter 이슈 | High | FAIL | 차단 우선 | 예 | A |
| TYPE_D | source box / 체크포인트 / PICKS 구간 파싱 실패 | verifier JSON parse 불가, 구간 인식 실패 | parser/verifier 입력 파손 | Mid | WARN 기본 | 조건부 허용 | 아니오(정책 우선) | B |
| TYPE_E | reviser 수정 후 구조 재파손 | reviser 이후 parse 실패 | reviser 미수렴 / post-edit 파손 | Mid~High | FAIL 또는 WARN | 조건부 차단 | 상황별 | A |
| TYPE_UNKNOWN | 기존 유형으로 분류 불가 | 패턴 불명확 | 신규 실패 패턴 | High | FAIL 검토 | 차단 검토 | 예 | A/B |

작성 규칙:
- Axis B에서 이미 확정한 fallback 허용 조건과 충돌하지 않도록 쓴다.
- `TYPE_UNKNOWN`은 보수적으로 적는다.

---

## 4. 유형별 대응 규칙 본문 (C-3)

각 유형에 대해 아래 형식으로 기술한다.

### TYPE_A 대응 규칙
- 탐지 조건:
- 허용 가능 여부:
- closure 기본값:
- publish 허용 조건:
- publish 차단 조건:
- 로그 필수 항목:
- 후속 조치:
- 재발 시 승격 규칙:

### TYPE_B 대응 규칙
- 탐지 조건:
- 허용 가능 여부:
- closure 기본값:
- publish 허용 조건:
- publish 차단 조건:
- 로그 필수 항목:
- 후속 조치:
- 재발 시 승격 규칙:

### TYPE_C 대응 규칙
- 탐지 조건:
- 허용 가능 여부:
- closure 기본값:
- publish 허용 조건:
- publish 차단 조건:
- 로그 필수 항목:
- 후속 조치:
- 재발 시 승격 규칙:

### TYPE_D 대응 규칙
- 탐지 조건:
- 허용 가능 여부:
- closure 기본값:
- publish 허용 조건:
- publish 차단 조건:
- 로그 필수 항목:
- 후속 조치:
- 재발 시 승격 규칙:

### TYPE_E 대응 규칙
- 탐지 조건:
- 허용 가능 여부:
- closure 기본값:
- publish 허용 조건:
- publish 차단 조건:
- 로그 필수 항목:
- 후속 조치:
- 재발 시 승격 규칙:

### TYPE_UNKNOWN 대응 규칙
- 탐지 조건:
- 허용 가능 여부:
- closure 기본값:
- publish 허용 조건:
- publish 차단 조건:
- 로그 필수 항목:
- 후속 조치:
- 재발 시 승격 규칙:

---

## 5. closure 자동 부여 매핑표 (C-4)

이 표는 `parse_failed_type`이 발생했을 때 `verifier_revision_closure`를 어떤 기준으로 줄지 정리한다.

| 유형 | 기본 closure | opener PASS 필수 여부 | 기준1 PASS 필수 여부 | 기준5 PASS 필수 여부 | source 구조 유지 필수 여부 | fallback_used 허용 여부 | PASS 승격 가능 여부 | 비고 |
|---|---|---|---|---|---|---|---|---|
| TYPE_A | FAIL | 예 | 예 | 예 | 예 | 아니오 우선 | 원칙적 불가 | 구조 이탈 |
| TYPE_B | FAIL/WARN | 예 | 예 | 예 | 예 | 제한적 | 조건부 | opener 규칙 위반 정도에 따름 |
| TYPE_C | FAIL | 예 | 예 | 예 | 예 | 아니오 우선 | 불가 | HTML/구조 파손 |
| TYPE_D | WARN | 예 | 예 | 예 | 예 | 예 | 불가(초기 정책) | Post 187 기준선 |
| TYPE_E | FAIL/WARN | 예 | 예 | 예 | 예 | 제한적 | 조건부 | reviser 재파손 |
| TYPE_UNKNOWN | FAIL 검토 | 예 | 예 | 예 | 예 | 보수적 제한 | 불가 | 반복 시 차단 강화 |

필수 명시 항목:
- `PARSE_FAILED 발생 = 자동 FAIL`인지 여부
- `fallback_used=True`가 closure를 어떻게 제한하는지
- `WARN → PASS 승격` 금지 또는 허용 조건

---

## 6. publish 허용 / 차단 결정표 (C-5)

| 상황 | 예시 | 판정 | 이유 | 조치 |
|---|---|---|---|---|
| TYPE_D + opener PASS + 기준1/5 PASS + source 구조 유지 | Post 187 유사 | WARN 허용 | 품질 기준 유지 + 로그 보존 가능 | 발행 허용 + 추적 |
| TYPE_D + source 구조 손실 | source box 누락 | FAIL/차단 | 출처 구조 손실 | 발행 차단 |
| TYPE_A 또는 TYPE_C + 구조 손실 | 섹션 누락 / 태그 파손 | FAIL/차단 | 발행 품질 직접 저하 | 발행 차단 |
| TYPE_UNKNOWN 1회 단발 | 원인 불명 | WARN 또는 FAIL 검토 | 샘플 부족 | 보수적 처리 |
| TYPE_UNKNOWN 2회 이상 반복 | 원인 불명 반복 | 차단 검토 | 신규 위험 패턴 | 원인 분석 우선 |
| 동일 유형 30일 내 반복 임계치 초과 | 재발 누적 | WARN→FAIL 승격 검토 | 운영 안정성 저하 | 정책 승격 |

작성 시 주의:
- Axis B 정책과 문구가 충돌하지 않게 유지한다.
- “허용”은 unrestricted PASS가 아니라 `WARN 기반 제한 허용`일 수 있음을 명시한다.

---

## 7. 로그 보강 체크리스트 (C-6)

`PARSE_FAILED` 케이스마다 아래 항목이 남는지 점검한다.

| 항목 | 필수 여부 | 기록 상태 | 보완 필요 | 비고 |
|---|---|---|---|---|
| run_id | 필수 |  |  |  |
| slot | 필수 |  |  |  |
| post_type | 필수 |  |  |  |
| parse_stage | 필수 |  |  |  |
| parse_failed_type | 필수 |  |  |  |
| failed_section_name | 필수 |  |  |  |
| raw_output_snapshot | 필수 |  |  |  |
| normalized_output_snapshot | 필수 |  |  |  |
| fallback_used | 필수 |  |  |  |
| publish_blocked | 필수 |  |  |  |
| opener_pass | 권장 |  |  |  |
| 기준1_pass | 권장 |  |  |  |
| 기준5_pass | 권장 |  |  |  |
| source_structure_pass | 권장 |  |  |  |
| PICKS 구간 offset / section locator | 권장 |  |  |  |

이번 Axis C에서 반드시 판정할 것:
- `slot=unknown` / `post_type=unknown` 허용 여부
- `failed_section_name`의 최소 분해 단위
- PICKS 구간 세부 위치 로그 추가 필요 여부

---

## 8. 자동 규칙 / 의사코드 정리 (C-7)

필요 시 아래 형식으로 규칙을 요약한다.

```text
IF parse_failed_type == TYPE_D
AND opener_pass == true
AND criteria_1_pass == true
AND criteria_5_pass == true
AND source_structure_pass == true
THEN verifier_revision_closure = WARN
AND publish_blocked = false
AND fallback_used may be true
AND event must be logged with full evidence.
```

```text
IF parse_failed_type in [TYPE_A, TYPE_C]
OR source_structure_pass == false
OR criteria_1_pass == false
OR criteria_5_pass == false
THEN verifier_revision_closure = FAIL
AND publish_blocked = true.
```

```text
IF parse_failed_type == TYPE_UNKNOWN
AND repeat_count >= 2
THEN escalate_to_block_review = true.
```

작성 목적:
- 정책 문장을 코드/검수 규칙으로 옮기기 쉬운 상태로 만든다.

---

## 9. 정책 결론 3줄 요약 (C-8)

아래 형식으로 최종 결론을 적는다.

1. `TYPE_D` 등 일부 유형은 품질 기준과 출처 구조가 유지될 때에만 `WARN 기반 제한 허용` 가능.
2. `TYPE_A / TYPE_C / 반복 TYPE_UNKNOWN`은 발행 차단 우선.
3. `PARSE_FAILED`는 발생 여부보다 `유형 분류 + 로그 보존 + closure 일관성`이 더 중요하며, 반복 임계치 도달 시 승격 규칙을 적용한다.

---

## 10. 축 인계 포인트 (C-9)

다음 축으로 넘길 항목을 정리한다.

### 축 D 인계
- opener 반복 안정성 추가 샘플 검증
- TYPE_D 재발 시 opener 유지 여부 동시 확인
- WARN 허용 케이스 반복 시 승격 조건 재검토

### 상위 보고 / Close-out 인계
- Axis C 정책 초안 확정 여부
- 코드 반영 필요 항목
- 로그 스키마 보강 필요 항목
- 운영 모니터링 유지 항목

---

## 11. 최종 판정

아래 중 하나로 마무리한다.

- GO
- CONDITIONAL GO
- HOLD

판정 예시 기준:
- **GO**: 유형별 대응 규칙, closure 매핑, 차단/허용 기준, 로그 보강 항목이 모두 문서화되고 대표 케이스에 적용 가능함
- **CONDITIONAL GO**: 정책 방향은 확정 가능하나 반복 샘플 또는 로그 스키마 보강이 더 필요함
- **HOLD**: 유형 정의가 불안정하거나 허용/차단 경계가 아직 충돌함

---

## 12. 제출물

이번 Axis C 결과 제출물:

1. `REPORT_PHASE18_AXIS_C_PARSE_FAILED_RESPONSE_RULES.md`
2. 유형별 대응 규칙 표
3. closure 자동 부여 매핑표
4. publish 허용 / 차단 결정표
5. 로그 보강 체크리스트 결과
6. 대표 케이스 적용 결과
7. 최종 판정

