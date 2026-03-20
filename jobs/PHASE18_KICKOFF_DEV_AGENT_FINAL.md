# PHASE18_KICKOFF_DEV_AGENT_FINAL.md

작성일: 2026-03-20  
대상: 개발 에이전트 전달용 최종본  
Phase: **Phase 18 Kickoff**

---

## 0. 이번 문서의 목적

이 문서는 Phase 17 종료 후 이어지는 **Phase 18 운영 안정화 트랙**의 공식 kickoff 지시문이다.

이번 Phase 18의 목적은 새 표현 실험이나 스타일 수정이 아니다.  
핵심은 **Phase 17에서 확인된 성공 상태를 반복 실행에서도 유지**하고, 남아 있는 **closure / fallback / PARSE_FAILED 운영 안정성 이슈를 분리·기록·정교화**하는 것이다.

---

## 1. 배경 요약

Phase 17에서 아래는 달성되었다.

- Post2 opener 구조 개편 완료
- generic opener 제거 및 pick-angle opener 강제 완료
- PARSE_FAILED 분류/로그/fallback 동작의 실전 관측 가능성 확보
- 실제 발행본 5건 기준 핵심 범위 검증 완료

동시에 아래 잔여 이슈가 남았다.

- 일부 포스트에서 `verifier_revision_closure` FAIL/WARN 잔존
- Post 187에서 verifier JSON parse 실패로 fallback 발행 경로 사용
- PARSE_FAILED는 미발생이 아니라, **발생 시 분류·로그·fallback 동작이 확인된 상태**
- opener 성공 상태가 추가 실행에서도 안정 유지되는지 반복 검증이 더 필요

따라서 Phase 18은 **구조 개편 단계가 아니라 운영 안정화 단계**로 진행한다.

---

## 2. Phase 18 공식 목표

이번 Phase 18의 공식 목표는 아래 4가지다.

1. `verifier_revision_closure` FAIL/WARN 잔존 원인 분리
2. fallback 발행 경로 정책 세분화 및 재발 통제
3. PARSE_FAILED 유형별 후속 대응 규칙 보강
4. opener 성공 상태의 반복 실행 안정성 검증

---

## 3. 이번 Phase에서 반드시 유지할 것

아래는 유지 대상이며, Phase 18에서 임의 변경 금지다.

- Post2 opener의 pick-angle 구조
- generic opener 금지 규칙
- opener 첫 문장에 픽명/핵심 섹터명 직접 명시 규칙
- opener 첫 문장 macro recap 금지 규칙
- PARSE_FAILED 분류 체계(TYPE_A~TYPE_E / TYPE_UNKNOWN)
- 실제 발행본 + 공개 URL 기준 검증 원칙
- 기준1 / 기준5 검수 원칙
- 최근 7일 중심 / 최대 30일 보조 자료 원칙
- 사실 / [해석] / [전망] 구분 원칙

---

## 4. 이번 Phase에서 하지 말 것

다음은 이번 Phase 18 범위 밖이다.

- 스타일 시스템 재수정
- typography / spacing / source box 등 프론트 표현 변경
- temporal SSOT 구조 재설계
- Post2 opener 구조를 다시 새 방향으로 갈아엎는 작업
- 발행 품질과 직접 관련 없는 모델/파라미터 교체 실험
- 근거 없이 fallback을 정상 경로처럼 확대 적용하는 처리

Phase 18은 **운영 안정화**가 목적이며, 새 실험 Phase가 아니다.

---

## 5. 작업 축 A — verifier_revision_closure FAIL/WARN 원인 분리

### 목표

`verifier_revision_closure`가 FAIL/WARN으로 남는 케이스를 유형화하고, 실제로 어떤 단계에서 closure가 깨지는지 분리한다.

### 해야 할 일

- 최근 샘플 발행본 및 후속 샘플 실행에서 `verifier_revision_closure` 결과를 수집한다.
- FAIL/WARN 케이스를 아래 기준으로 분해한다.
  - verifier 응답 구조 문제
  - reviser 반영 후 재파손 문제
  - HTML/구조 보존 문제
  - source/date/number linkage 관련 점검 충돌
  - opener는 통과했지만 후속 섹션에서 closure가 깨지는 문제
- FAIL/WARN 케이스별로 **최종 발행본 품질 영향도**를 함께 기록한다.

### 산출물

- closure FAIL/WARN 사례표
- 원인 유형별 분류표
- 우선순위별 보완 대상 목록

---

## 6. 작업 축 B — fallback 발행 경로 정책 정교화

### 목표

fallback이 필요한 상황과 허용 가능한 상황을 명확히 구분한다.

### 해야 할 일

- `fallback_used=True` 사례를 별도 표로 관리한다.
- fallback 진입 조건을 명시한다.
- fallback 사용 시에도 발행이 허용되는 최소 조건을 문서화한다.
- fallback 사용 후에도 반드시 남겨야 할 로그 필드를 고정한다.
- fallback이 반복될 경우 경고 또는 차단으로 승격할 기준을 정한다.

### 최소 정책 문서화 항목

1. fallback 진입 원인
2. fallback 사용 여부
3. publish_blocked 여부
4. 공개 URL 확보 여부
5. 기준1 / 기준5 위반 여부
6. 후속 수동 점검 필요 여부

### 주의

fallback은 성공이 아니라 **예외 경로**다.  
Phase 18에서는 fallback을 “발행 가능했음”으로 끝내지 말고, **재발 통제 가능한 상태**로 바꿔야 한다.

---

## 7. 작업 축 C — PARSE_FAILED 대응 규칙 보강

### 목표

PARSE_FAILED를 단순 기록에서 끝내지 말고, **유형별 대응 규칙**까지 연결한다.

### 해야 할 일

- TYPE_A~TYPE_E / TYPE_UNKNOWN 각 유형의 정의를 점검한다.
- 실제 사례(Post 187 TYPE_D)를 기준선으로 삼아 대응 규칙을 구체화한다.
- 유형별로 아래를 정리한다.
  - 전형적 발생 위치
  - 예상 원인
  - 우선 확인 로그 필드
  - fallback 허용 여부
  - 재시도/수정/차단 중 어떤 대응이 적절한지
- TYPE_UNKNOWN이 발생할 경우 별도 관찰 대상으로 묶는다.

### 권장 대응 표 구조

| type | 전형 증상 | 우선 원인 후보 | 기본 대응 | fallback 허용 | 비고 |
|------|-----------|----------------|-----------|----------------|------|
| TYPE_A | 구조 누락/순서 불일치 | writer/reviser 구조 이탈 | 재시도 또는 구조 보정 | 조건부 |  |
| TYPE_B | 금지 opener 패턴으로 인한 불일치 | opener 규칙 회귀 | reviser 보정 우선 | 조건부 |  |
| TYPE_C | HTML 파손/중첩 오류 | 후처리/보정 단계 | 구조 보정 우선 | 제한적 |  |
| TYPE_D | source/checkpoint/report 구간 파싱 문제 | verifier JSON parse / 구간 판독 실패 | 로그 저장 + fallback 정책 적용 | 조건부 | Post 187 기준선 |
| TYPE_E | reviser 수정 후 재파손 | reviser 부작용 | reviser 규칙 점검 | 제한적 |  |
| TYPE_UNKNOWN | 분류 불가 | 신규 패턴 | 별도 보관/수동 분석 | 보수적 |  |

---

## 8. 작업 축 D — opener 반복 안정성 검증

### 목표

Phase 17에서 달성한 opener 성공 상태가 **추가 실행에서도 유지되는지** 확인한다.

### 해야 할 일

- 추가 샘플 발행을 반복 수행한다.
- 각 샘플에 대해 아래를 기록한다.
  - opener H3 문구
  - opener 첫 문장
  - 픽명/핵심 섹터명 포함 여부
  - macro recap 시작 여부
  - 핵심 변수 포함 여부
  - Post1/Post2 opener 역할 중복 여부
- 반복 샘플에서 회귀(regression)가 발생하면 즉시 원인을 분리한다.

### 최소 검증 원칙

- opener 구조 성공은 1회 성공이 아니라 **반복 실행 유지**로 본다.
- opener 회귀는 작은 문장 이슈가 아니라 구조 회귀로 취급한다.

---

## 9. 권장 실행 순서

아래 순서로 진행한다.

1. 최근 발행본/로그 기준으로 closure FAIL/WARN 사례 수집
2. fallback_used=True 사례 분리 및 조건 정리
3. PARSE_FAILED 유형별 대응 규칙 표 작성
4. 추가 샘플 발행으로 opener 반복 안정성 검증
5. 보고서에 실제 발행본 기준 증적 정리
6. 최종 판정

---

## 10. 보고서 작성 기준

Phase 18 보고서는 초안 기준이 아니라 **실제 발행본 기준**으로 작성한다.

필수 포함 항목:

1. 작업 개요
2. 사용 입력 요약
3. 실제 생성된 최종 본문 또는 핵심 검증 내용
4. 공개 URL
5. 기준1 / 기준5 판정
6. source/date 반영 여부
7. 숫자-논리 연결 여부
8. closure FAIL/WARN 사례 요약
9. fallback_used 사례 요약
10. PARSE_FAILED 유형별 관찰 결과
11. opener 반복 안정성 결과
12. 최종 판정

추가 요구:

- URL만 나열하지 말고, 보고서 자체만으로 검증 가능하도록 핵심 본문 또는 본문 전문을 포함한다.
- 샘플별 opener 문구와 opener 첫 2~3문장은 별도 발췌한다.
- fallback 사례가 있으면 그 케이스는 별도 섹션으로 분리한다.

---

## 11. 최종 판정 기준

### Phase 18 GO 후보

아래가 충족되면 GO 후보로 본다.

- opener 성공 상태가 반복 샘플에서도 안정 유지
- closure FAIL/WARN 케이스가 원인별로 충분히 분리됨
- fallback 경로가 무분별하게 반복되지 않음
- PARSE_FAILED 유형별 대응 규칙이 문서화됨
- 실제 발행본 및 공개 URL 기준으로 품질 검증 완료

### Phase 18 CONDITIONAL GO 후보

아래에 가까우면 CONDITIONAL GO로 본다.

- 핵심 발행 품질은 유지되나 fallback 또는 closure 경고가 소수 잔존
- 대응 규칙은 생겼지만 반복 실행 데이터가 더 필요
- TYPE_UNKNOWN 등 추가 관찰 항목이 남아 있음

### Phase 18 HOLD 후보

아래면 HOLD로 본다.

- opener 회귀 재발
- 기준1 / 기준5 반복 위반
- fallback 경로 남용
- 실제 발행 실패 또는 공개 URL 확보 실패
- PARSE_FAILED가 반복되는데 분류/대응이 정리되지 않음

---

## 12. 제출 산출물

반드시 제출할 것:

1. Phase 18 상세 보고서 MD
2. closure FAIL/WARN 유형표
3. fallback 정책 정리표
4. PARSE_FAILED 유형별 대응 표
5. 추가 샘플 발행 결과 요약
6. 최종 판정

---

## 13. 최종 지시

이번 Phase 18은 새 글쓰기 미감 조정이나 구조 재발명 Phase가 아니다.

핵심은 아래 두 문장으로 요약된다.

- **Phase 17이 구조 전환과 관측 가능성을 확보했다면, Phase 18은 이를 운영 안정성으로 고정하는 단계다.**
- **예외를 숨기지 말고, 예외가 발생했을 때도 분류·기록·판단 가능한 상태로 만드는 것이 목표다.**

이 기준으로 실행하고 보고하라.
