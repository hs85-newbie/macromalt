# PHASE18_AXIS_A_COLLECTION_TEMPLATE.md

작성 목적: Phase 18 축 A 실행용 수집 템플릿  
범위: `verifier_revision_closure FAIL/WARN` 케이스 수집, 원인 유형 분해, 후속 조치 우선순위화  
기준: Phase 17 인계 포인트와 운영 안정화 범위에만 집중한다.

---

## 1. 배경

Phase 17 종료 보고서 기준으로, Phase 18의 첫 번째 인계 포인트는 아래와 같다.

1. `verifier_revision_closure FAIL/WARN` 잔존 케이스 정리  
2. fallback 발행 경로 정책 세분화  
3. `PARSE_FAILED` 원인별 후속 대응 규칙 보강  
4. opener 성공 상태의 반복 실행 안정성 검증

또한 최신 보고서는 아래 사실을 명시한다.

- opener 구조 전환은 5/5 달성  
- Post 187에서 verifier JSON parse 실패로 fallback 발행 경로 사용  
- `PARSE_FAILED`는 발생 시 `TYPE_D`로 분류·로그·fallback 동작이 실전에서 확인됨  
- 일부 포스트에서는 `verifier_revision_closure FAIL/WARN`이 잔존함

따라서 Phase 18 축 A의 목표는 **closure FAIL/WARN 사례를 먼저 표준 양식으로 수집하고, 반복되는 원인 유형을 분리하는 것**이다.

---

## 2. 이번 템플릿의 사용 원칙

### 해야 할 것
- 최근 발행 샘플 기준으로 `closure FAIL/WARN` 사례를 빠짐없이 수집한다.
- 각 사례를 동일한 필드 구조로 기록한다.
- 단순 건수 집계보다 **원인 유형 분해**를 우선한다.
- `fallback_used=True` 사례가 closure 문제와 연결되는지 함께 본다.
- opener 적합 여부와 closure 문제를 분리해서 기록한다.

### 하지 말 것
- opener 구조 자체를 다시 바꾸지 않는다.
- `PARSE_FAILED` 분류 체계를 다시 바꾸지 않는다.
- 단일 사례만 보고 정책 결론을 확정하지 않는다.
- FAIL/WARN을 무조건 코드 버그로 단정하지 않는다.

---

## 3. 수집 대상 범위

우선 수집 대상:
- Phase 17 샘플 발행 5건
- 추가로 Phase 18에서 새로 생성되는 샘플 발행본
- `verifier_revision_closure = FAIL` 또는 `WARN` 기록이 남은 실행
- `fallback_used=True`가 함께 발생한 실행

최소 기준:
- 최초 1차 수집은 5건 전체를 다 적재한다.
- 이후 추가 샘플이 생기면 동일 포맷으로 append 한다.

---

## 4. 축 A 사례 수집 표 — 원본 템플릿

아래 표를 복사해서 사용하라.

| run_id | Post ID | 발행 시각 | opener 적합 여부 | verifier_revision_closure | verifier 이슈 건수 | reviser 개입 여부 | fallback_used | parse_failed_type | publish_blocked | 최종 발행 여부 | 비고 |
|---|---:|---|---|---|---:|---|---|---|---|---|---|
|  |  |  | PASS / FAIL | PASS / WARN / FAIL |  | Y / N | True / False | TYPE_A~E / UNKNOWN / 없음 | True / False | Y / N |  |

작성 규칙:
- `opener 적합 여부`는 opener 구조 기준만 본다.
- `verifier_revision_closure`는 최종 closure 상태를 적는다.
- `verifier 이슈 건수`는 샘플별 verifier/reviser 로그 기준으로 적는다.
- `parse_failed_type`은 발생했을 때만 적고, 없으면 `없음`으로 쓴다.

---

## 5. 사례별 상세 기록 템플릿

각 FAIL/WARN 사례마다 아래 블록을 작성하라.

```md
### Case A-__ — Post ID ___

- run_id:
- 발행 시각:
- 최종 발행 여부:
- opener 적합 여부:
- verifier_revision_closure:
- verifier 이슈 건수:
- reviser 개입 여부:
- fallback_used:
- parse_failed_type:
- publish_blocked:

#### 1) 직접 관찰된 현상
- 
- 

#### 2) 문제 발생 위치
- verifier 항목 번호:
- 관련 섹션:
- 관련 문장/구간:

#### 3) 1차 원인 분류
- [ ] C1. verifier strictness 문제
- [ ] C2. reviser 미수렴 문제
- [ ] C3. parser/verifier 입력 문제
- [ ] C4. fallback 경로 문제
- [ ] C5. 기타 / 미확정

#### 4) 판단 근거
- 
- 

#### 5) 필요한 후속 조치
- [ ] 코드 수정 필요
- [ ] verifier 기준 완화/정교화 필요
- [ ] reviser 규칙 보강 필요
- [ ] fallback 정책 문서화 필요
- [ ] 모니터링 유지 후 재판단

#### 6) 임시 결론
- 
```

---

## 6. 원인 유형 분류표

축 A에서는 최소 아래 5개 유형으로 나눈다.

### C1. verifier strictness 문제
정의:
- 본문 품질이나 발행 결과는 수용 가능하지만, closure 조건이 너무 엄격하거나 현재 운영 목적과 안 맞아 FAIL/WARN이 나는 경우

징후:
- 발행본 품질은 양호
- opener, 금지 패턴, 출처 구조는 정상
- closure만 반복적으로 걸림

권장 후속:
- verifier 기준 세분화 검토
- hard fail / soft warn 분리 검토

### C2. reviser 미수렴 문제
정의:
- reviser가 개입했지만 closure PASS까지 수렴하지 못하는 경우

징후:
- verifier 이슈가 줄어들긴 했으나 closure는 WARN/FAIL 유지
- 유사한 문장 구조가 반복 재등장

권장 후속:
- reviser 보정 규칙 추가
- 동일 오류 재유형화

### C3. parser/verifier 입력 문제
정의:
- JSON parse 실패, 포맷 파손, 필드 누락 등으로 verifier 자체가 안정적으로 판단하지 못하는 경우

징후:
- parse 실패 메시지
- snapshot/raw-normalized 비교 필요
- 구조는 괜찮아도 verifier 입력이 깨짐

권장 후속:
- parser 입력 안정화
- 예외 처리 / 재시도 / snapshot 검증 강화

### C4. fallback 경로 문제
정의:
- verifier 정상 종료가 아니어도 fallback으로 발행은 되었고, 이 경로의 허용 조건이 아직 명확하지 않은 경우

징후:
- `fallback_used=True`
- `publish_blocked=False`
- 발행은 됐지만 closure 또는 verifier 경로는 비정상

권장 후속:
- fallback 허용 조건 명문화
- fallback 후 추가 검사 의무화 여부 검토

### C5. 기타 / 미확정
정의:
- 위 4개로 즉시 설명되지 않는 경우

권장 후속:
- 추가 샘플 확보
- 축 B/C와 연동해 재분류

---

## 7. 우선순위 판정 표

사례 수집 후 아래 표를 채운다.

| 유형 | 건수 | 대표 Post ID | 현재 영향도 | 즉시 수정 필요 여부 | 비고 |
|---|---:|---|---|---|---|
| C1 verifier strictness |  |  | Low / Mid / High | Y / N |  |
| C2 reviser 미수렴 |  |  | Low / Mid / High | Y / N |  |
| C3 parser/verifier 입력 |  |  | Low / Mid / High | Y / N |  |
| C4 fallback 경로 |  |  | Low / Mid / High | Y / N |  |
| C5 기타/미확정 |  |  | Low / Mid / High | Y / N |  |

판정 기준:
- **High**: 재발 시 발행 신뢰도 또는 gate 해석에 직접 영향
- **Mid**: 즉시 발행 차단은 아니지만 반복되면 운영 해석 충돌 가능
- **Low**: 기록은 필요하나 모니터링 중심으로 충분

---

## 8. 축 A 1차 산출물 형식

축 A 1차 종료 시 아래 4개를 제출하라.

1. `A-1` 사례 수집 표 완성본  
2. `A-2` 사례별 상세 기록 블록  
3. `A-3` 원인 유형 분포표  
4. `A-4` 즉시 수정 / 정책 문서화 / 모니터링 유지 3분류 결론

권장 결론 형식:

```md
## Axis A — 1차 결론

### 즉시 수정 필요
- 

### 정책 명문화 우선
- 

### 모니터링 유지
- 

### 축 B/C/D로 넘길 인계 포인트
- 
```

---

## 9. Post 187 기록 예시

```md
### Case A-EXAMPLE — Post ID 187

- run_id: (실제 run_id 기입)
- 발행 시각: (실제 시각 기입)
- 최종 발행 여부: Y
- opener 적합 여부: PASS
- verifier_revision_closure: WARN 또는 FAIL (실제 기록 기준 기입)
- verifier 이슈 건수: (실제 기록 기준 기입)
- reviser 개입 여부: (실제 기록 기준 기입)
- fallback_used: True
- parse_failed_type: TYPE_D
- publish_blocked: False

#### 1) 직접 관찰된 현상
- verifier JSON parse 실패가 발생했다.
- 그러나 fallback 경로로 발행은 진행되었다.
- opener 구조 자체는 유지되었다.

#### 2) 문제 발생 위치
- verifier JSON parse 단계
- closure 판정 경로

#### 3) 1차 원인 분류
- [ ] C1. verifier strictness 문제
- [ ] C2. reviser 미수렴 문제
- [x] C3. parser/verifier 입력 문제
- [x] C4. fallback 경로 문제
- [ ] C5. 기타 / 미확정

#### 4) 판단 근거
- parse_failed_type이 TYPE_D로 기록됨
- fallback_used=True, publish_blocked=False로 남아 있음

#### 5) 필요한 후속 조치
- [ ] 코드 수정 필요
- [ ] verifier 기준 완화/정교화 필요
- [ ] reviser 규칙 보강 필요
- [x] fallback 정책 문서화 필요
- [x] 모니터링 유지 후 재판단

#### 6) 임시 결론
- Post 187은 축 A와 축 B를 연결하는 대표 사례로 유지한다.
```

---

## 10. 축 A 완료 기준

축 A 1차 완료는 아래를 모두 충족할 때로 본다.

- 최근 샘플 발행본 기준 `closure FAIL/WARN` 사례가 전부 표준 양식으로 수집됨
- 각 사례가 최소 1개 원인 유형(C1~C5)으로 분류됨
- `fallback_used=True` 사례가 별도 식별됨
- Post 187 같은 예외 경로 사례가 축 B/C로 넘길 수 있게 정리됨
- opener 문제와 closure 문제를 혼동하지 않도록 분리 기록됨

---

## 11. 한 줄 운영 원칙

축 A의 목적은 FAIL/WARN 숫자를 줄이는 것이 아니라,
**어떤 FAIL/WARN이 코드 수정 대상이고, 어떤 FAIL/WARN이 정책/모니터링 대상인지 구분하는 것**이다.
