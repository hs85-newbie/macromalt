# PHASE18_AXIS_B_POLICY_TEMPLATE

- Project: Macromalt
- Phase: 18
- Axis: B — `fallback_used=True` 정책 정교화
- Document Type: Execution Template / Policy Draft Template
- Status: Draft Template

---

## 0. 문서 목적

본 문서는 Phase 18 Axis B 실행을 위한 **fallback 정책 수립 템플릿**이다.

축 B의 목적은 다음과 같다.

1. `fallback_used=True`가 실제로 어떤 조건에서 허용 가능한지 문서화한다.
2. `PARSE_FAILED`, verifier skip, reviser 미수렴, publish 진행 여부 사이의 관계를 정리한다.
3. 발행 품질 기준을 훼손하지 않는 범위에서 **허용 가능한 예외 경로**와 **차단해야 할 경로**를 분리한다.
4. 이후 샘플 발행, 운영 모니터링, Close-out 보고서에서 동일 기준을 반복 적용할 수 있도록 정책 SSOT 후보를 만든다.

이 문서는 **새 기능 설계 문서가 아니다.**
이번 축의 목적은 구조 변경이 아니라 **운영 예외 경로의 정책 명문화**다.

---

## 1. 이번 축에서 다룰 질문

축 B는 아래 질문에 답해야 한다.

1. `fallback_used=True`는 언제 허용 가능한가?
2. 어떤 종류의 fallback은 `WARN`으로 허용 가능하고, 어떤 경우는 `FAIL` 또는 `HOLD`로 막아야 하는가?
3. `PARSE_FAILED`가 있어도 발행 가능할 조건은 무엇인가?
4. verifier skip / JSON parse 실패 / reviser 미수렴 / source 구조 이상 중 어떤 것은 fallback 허용 대상이고, 어떤 것은 발행 차단 대상인가?
5. fallback 경로를 탔더라도 **기준1 / 기준5 / opener 구조 / 출처 대응**이 유지되면 운영상 허용 가능한가?
6. 허용 시 어떤 로그와 후속 모니터링을 강제해야 하는가?

---

## 2. 불변 유지 항목

이번 축에서는 아래 항목을 변경하지 않는다.

- pick-angle opener 구조
- generic opener 금지 규칙
- `PARSE_FAILED` TYPE_A~TYPE_E / TYPE_UNKNOWN 분류 체계
- 실발행본 + 공개 URL 기준 검증 원칙
- 기준1 / 기준5 품질 기준 자체

즉, 축 B는 **fallback 허용 조건을 문서화**하는 축이지, 발행 기준 자체를 완화하는 축이 아니다.

---

## 3. 용어 정의

### 3.1 fallback_used
정상 verifier / reviser / parse 경로를 끝까지 타지 못했으나, 정의된 예외 경로를 통해 최종 발행까지 진행한 경우를 의미한다.

### 3.2 verifier skip
모델 응답 구조 파손, JSON parse 실패, 기타 입력 문제로 인해 verifier가 정상 판정을 내리지 못한 상태를 의미한다.

### 3.3 publish_blocked
해당 케이스가 정책상 발행 차단되어야 하는지를 나타내는 플래그다.

### 3.4 허용 가능한 fallback
발행 품질 기준 위반은 없고, opener 구조/출처 구조/핵심 본문 품질이 유지된 상태에서 제한적으로 허용되는 예외 경로를 의미한다.

### 3.5 금지해야 할 fallback
기준1 / 기준5 / 구조 안정성 / 출처 대응 / 파서 안정성 중 핵심 기준을 실제로 훼손했는데도 발행이 진행되는 경우를 의미한다.

---

## 4. 입력 자료

축 B 실행 시 아래 자료를 반드시 수집한다.

1. Axis A 보고서
2. fallback 발생 케이스 전체 목록
3. 각 케이스의 raw output / normalized output / verifier 결과 / reviser 결과
4. publish 결과
5. 발행 URL 또는 발행 본문 전문
6. `PARSE_FAILED` 상세 로그
7. closure 결과

권장 입력:

- 가장 대표적인 fallback 케이스 1건 이상
- fallback 미발생 정상 케이스 1~2건 비교군

---

## 5. 사례 수집 표 (B-1)

아래 표를 fallback 케이스별로 채운다.

| 항목 | 내용 |
|---|---|
| Post ID |  |
| 샘플 구분 |  |
| 발행 시각 |  |
| `fallback_used` |  |
| `publish_blocked` |  |
| `verifier_revision_closure` |  |
| `parse_failed_type` |  |
| verifier skip 여부 |  |
| reviser 개입 여부 |  |
| 최종 발행 여부 |  |
| opener 구조 유지 여부 |  |
| 기준1 PASS 여부 |  |
| 기준5 PASS 여부 |  |
| 참고 출처 구조 유지 여부 |  |
| raw output 보관 여부 |  |
| normalized output 보관 여부 |  |
| 핵심 이슈 요약 |  |

---

## 6. 원인 분류 표 (B-2)

각 fallback 케이스를 아래 분류 틀로 정리한다.

| 분류 코드 | 설명 | 해당 여부 | 비고 |
|---|---|---|---|
| F1 | verifier 입력 파손으로 정상 검수 불가 |  |  |
| F2 | `PARSE_FAILED` 발생 후 fallback 진입 |  |  |
| F3 | reviser 미수렴 상태에서 fallback 진입 |  |  |
| F4 | source box / 체크포인트 / 본문 구조 일부 손실 상태 |  |  |
| F5 | opener 구조는 유지되나 closure만 닫히지 않음 |  |  |
| F6 | 실제 품질 기준 위반 동반 |  |  |
| F7 | publish 차단이 맞지만 우회 발행됨 |  |  |

주의:
- 한 케이스에 복수 코드 태깅 가능
- 이 표는 상호배타 집계가 아니다

---

## 7. 허용 / 경고 / 차단 결정표 (B-3)

아래 결정표를 채운다.

| 상황 | 기본 판정 | 발행 허용 여부 | closure 처리 | 후속 조치 |
|---|---|---|---|---|
| verifier skip 발생, 본문 품질/구조 이상 없음 |  |  |  |  |
| `PARSE_FAILED` 발생, fallback 후 발행, 기준1/5 유지 |  |  |  |  |
| opener 구조 유지, 출처 구조 유지, closure만 WARN |  |  |  |  |
| source 구조 일부 손실 있으나 발행 진행 |  |  |  |  |
| 기준1 또는 기준5 실제 위반 |  |  |  |  |
| `TYPE_UNKNOWN` 반복 발생 |  |  |  |  |
| fallback 재발률이 임계치 초과 |  |  |  |  |

이 표의 목적은 “fallback 자체를 금지할지”가 아니라,
**어떤 fallback은 운영적으로 허용 가능하고, 어떤 fallback은 발행 차단해야 하는지**를 명확히 하는 것이다.

---

## 8. 정책 결론 초안 (B-4)

아래 형식으로 정책 결론을 작성한다.

### 8.1 허용 가능한 fallback

아래 조건을 모두 만족할 경우 `fallback_used=True`를 제한적으로 허용한다.

- opener 구조 유지
- 기준1 PASS
- 기준5 PASS
- 참고 출처 구조 유지
- raw / normalized / parse 로그 보존
- `publish_blocked=False` 사유 문서화
- closure 결과가 PASS 또는 정책상 허용 가능한 WARN

### 8.2 WARN으로 허용할 fallback

아래 조건일 경우 발행은 허용하되 `WARN` 및 후속 모니터링 대상으로 둔다.

- `PARSE_FAILED` 발생 후 fallback 발행
- verifier skip 발생
- reviser 미수렴이 남았으나 핵심 발행 품질 기준 위반은 없음
- 동일 유형 재발 여부를 추적해야 함

### 8.3 허용 불가 fallback

아래 조건 중 하나라도 충족하면 fallback 허용 불가로 둔다.

- 기준1 위반
- 기준5 위반
- opener 구조 파손
- 참고 출처 직접 대응 구조 파손
- `TYPE_UNKNOWN` 반복 누적
- source box / 체크포인트 / 종목 리포트 핵심 구조 손실
- publish 차단이 맞는 케이스가 우회 발행된 경우

---

## 9. closure 매핑 정책 (B-5)

fallback 관련 closure 매핑을 아래 형식으로 정리한다.

| 조건 | closure 권장값 | 비고 |
|---|---|---|
| 정상 경로, 이슈 없음 | PASS |  |
| fallback 발생, 품질 기준 유지, 후속 모니터링 필요 | WARN |  |
| fallback 발생 + 구조/품질 핵심 기준 불확실 | FAIL |  |
| 발행 차단이 맞는 케이스 | HOLD 또는 publish blocked |  |

권장 원칙:
- `fallback_used=True`는 자동 FAIL이 아니다.
- 그러나 fallback은 원칙적으로 **PASS보다 WARN 우선**으로 본다.
- PASS 승격은 반복 샘플에서 재현 안정성이 확인된 뒤 검토한다.

---

## 10. 로그/증적 필수 항목 (B-6)

정책 문서에는 아래 로그/증적 항목을 반드시 연결한다.

1. Post ID
2. 발행 시각
3. 발행 URL 또는 발행 본문 전문
4. `fallback_used`
5. `publish_blocked`
6. `verifier_revision_closure`
7. `parse_failed_type`
8. raw output snapshot
9. normalized output snapshot
10. verifier / reviser 로그
11. opener 구조 확인 결과
12. 기준1 / 기준5 판정 결과
13. 참고 출처 구조 확인 결과

---

## 11. 정책 판정 질문 (B-7)

최종 정책을 확정하기 전에 아래 질문에 답한다.

1. fallback 허용 조건은 충분히 좁은가?
2. fallback 허용이 발행 품질 기준 완화로 오해될 여지는 없는가?
3. Post 187류 케이스는 현재 정책상 `WARN 허용`이 맞는가?
4. 동일 유형 재발 시 `WARN → FAIL` 승격 조건이 있는가?
5. `TYPE_UNKNOWN`에 대한 상한선이 정의됐는가?
6. publish 차단이 필요한 조건이 명시됐는가?
7. 운영자가 보고서만 보고 허용/차단 판정을 재현할 수 있는가?

---

## 12. 산출물 형식

축 B 결과물은 아래 순서로 제출한다.

1. B-1 사례 수집 표
2. B-2 원인 분류 표
3. B-3 허용/경고/차단 결정표
4. B-4 정책 결론 초안
5. B-5 closure 매핑 정책
6. B-6 로그/증적 체크리스트
7. B-7 최종 판정
   - 정책 초안 확정
   - 추가 사례 필요
   - HOLD

---

## 13. 보고서 결론 문구 템플릿

아래 문구를 최종 보고서 결론에 맞게 수정하여 사용한다.

### 13.1 정책 초안 확정 시

Phase 18 Axis B 결과, `fallback_used=True`는 전면 허용 또는 전면 금지가 아니라,
**정의된 품질 기준과 구조 보존 조건을 충족할 때에 한해 제한적으로 허용**하는 것으로 정리한다.

특히 `PARSE_FAILED` 또는 verifier skip이 발생하더라도,
실발행본 기준 opener 구조, 기준1, 기준5, 참고 출처 구조가 유지되고,
raw/normalized/log 증적이 남는 경우에는 `WARN 기반 허용` 정책이 타당하다.

반대로 기준 위반 또는 구조 손실이 동반되는 fallback은 허용 대상이 아니다.

### 13.2 추가 사례 필요 시

현재 fallback 정책은 방향성은 정리되었으나,
허용/차단 경계 조건을 확정하기엔 샘플 수가 부족하다.

따라서 본 정책은 임시안으로 두고,
추가 fallback 사례 수집 후 최종 확정한다.

### 13.3 HOLD 시

현재 관측된 fallback 케이스는 품질 기준 훼손 여부가 불명확하거나,
발행 차단이 필요한 조건과 충돌할 가능성이 있어 정책 확정을 보류한다.

추가 로그 보강 또는 발행 샘플 검증 없이는 운영 정책으로 승격하지 않는다.

---

## 14. 작성 주의사항

- URL만 나열하지 말고, 보고서 자체만으로 재검토 가능해야 한다.
- 대표 fallback 케이스는 본문 전문 또는 핵심 섹션 전문을 포함한다.
- 수치 집계는 상호배타 여부를 명확히 쓴다.
- `fallback_used=True`를 성공으로 미화하지 않는다.
- 이번 축의 목적은 “예외를 합법화”하는 것이 아니라 “허용 가능한 예외 조건을 좁게 정의”하는 것이다.
- Phase 17에서 확정한 opener 구조 규칙은 건드리지 않는다.

---

## 15. 권장 시작점

가장 먼저 아래 1건을 기준 케이스로 정리한다.

- 대표 fallback 케이스 1건
- `PARSE_FAILED` 유형이 식별된 케이스 1건
- `publish_blocked=False` 사유가 남아 있는 케이스 1건

그 다음 정상 케이스 1~2건을 비교군으로 붙여,
왜 어떤 케이스는 WARN 허용이고 어떤 케이스는 정상 PASS인지 경계를 정리한다.

