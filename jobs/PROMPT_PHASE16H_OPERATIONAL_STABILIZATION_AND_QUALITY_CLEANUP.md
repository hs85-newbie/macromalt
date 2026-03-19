# PROMPT_PHASE16H_OPERATIONAL_STABILIZATION_AND_QUALITY_CLEANUP.md

너는 macromalt 프로젝트의 Phase 16H 구현 담당 엔지니어다.

이번 Phase 16H의 목적은
**Phase 16G에서 GO가 확인된 핵심 성과를 유지한 채, 남아 있는 운영 안정화/잔여 품질 이슈만 정리하는 것**이다.

이번 페이즈는 구조 개편이 아니다.
Phase 17로 올라가기 전,
현재 16계열이 실제로 안정 수렴 가능한지 확인하기 위한 **운영 안정화 페이즈**다.

---

## 현재 전제

Phase 16G까지 아래는 이미 달성된 것으로 본다.

- temporal SSOT 정착
- 완료 월 [전망] 오주입 방지
- bridge-pick 정합성 개선
- step3_status 표준화
- intro overlap HIGH 탈출
- emergency_polish 관측성 확보

이번 16H에서는 위 성과를 절대 깨지 말고,
아래 **잔여 이슈 3개만** 다뤄라.

---

## Phase 16H 핵심 타깃

### Track A — hedge_overuse_p1 정리
Post1에서 헤징이 과도하게 남는 문제를 줄여라.

문제 유형 예시:
- “~일 수 있다”
- “~로 볼 수 있다”
- “~가능성이 있다”
- “~로 해석될 수 있다”
- 확정적으로 말해도 되는 factual spine 구간까지 과도하게 유보형으로 눕는 현상

중요:
- 무조건 단정형으로 바꾸라는 뜻이 아니다
- **사실 구간은 더 단정적으로**, 해석/전망 구간은 **필요한 만큼만 유보형**을 쓰게 정렬하라
- factual sentence와 interpretive sentence를 분리해서 판단하라

목표:
- Post1 analytical spine을 흐리는 불필요한 헤징 감소
- premium editorial tone 유지
- 과잉 확신으로 오버슈팅 금지

### Track B — verifier_revision_closure 정리
Step3 verifier → reviser → 최종 채택 흐름에서
closure 판정이 어색하게 남는 문제를 정리하라.

해야 할 일:
- verifier_revision_closure FAIL이 왜 나는지 원인 범주화
- 실제로는 충분히 수정 종료된 케이스인데 closure만 FAIL 되는 경우가 있는지 확인
- closure 판정 기준이 너무 엄격하거나 문구 중심이면 완화 또는 재정의
- 반대로 진짜 미종결 케이스는 계속 FAIL 되도록 유지

중요:
- Step3 품질 게이트를 약화시키지 말 것
- “문제 있어도 그냥 통과” 방향 금지
- 닫힘(closing) 판정이 **실제 수정 상태와 맞도록** 조정하라

목표:
- verifier_revision_closure가 형식적 false fail을 덜 내게 만들기
- 운영 리포트 해석성을 높이기
- step3_status 표준 체계와 충돌 없게 유지

### Track C — emergency_polish 집계/보고 정합성
run 로그와 보고서의 emergency_polish WARN 개수 불일치 문제를 정리하라.

예:
- 실제 로그 5건인데 보고서 2건 기재
- 집계 기준이 “unique marker 수”인지 “총 warn line 수”인지 불명확
- 보고서 작성 단계에서 필터링/요약 기준이 다름

해야 할 일:
- emergency_polish warning count의 **단일 기준** 정의
- 코드 로그 / p13_scores / 보고서가 같은 기준을 쓰게 정렬
- count 외에도 필요하면 marker list 또는 summarized categories를 함께 남겨
  운영자가 숫자만 보고 오해하지 않게 하라

목표:
- 로그 ↔ 보고서 ↔ handoff 간 숫자 일치
- 운영 관측성 향상
- 실출력 GO/FAIL 판정에 혼선 제거

---

## 절대 비침범 영역

아래는 이번 Phase 16H에서 건드리지 말아야 한다.

- temporal SSOT 로직
- [전망] / [해석] 태그 규칙
- bridge alignment 로직
- intro overlap 기본 로직
- step3_status enum 체계
- 본문 대규모 구조 개편
- 슬롯/발행 플로우 구조 변경

즉, 16H는 **운영 안정화 미세조정**이지 새 구조 설계가 아니다.

---

## 구현 원칙

1. **작게 고치고 크게 검증**
- 코드 변경은 최소화
- 진단/관측 강화는 허용
- 본문 생성 구조를 다시 설계하지 말 것

2. **문체 보정은 규칙 우선**
- hedge_overuse는 regex 남발보다
  verifier/reviser 규칙 또는 sentence-level heuristic 보정이 우선
- 다만 안전한 후처리 진단은 허용

3. **관측값은 사람이 읽히게**
- emergency_polish count, closure status는
  운영자가 보고 바로 이해할 수 있어야 한다
- 숫자만 있고 기준이 불명확하면 실패다

4. **비회귀 우선**
- 16G GO 축이 하나라도 깨지면 16H는 실패다

---

## 권장 구현 방향

### Track A 권장안
- factual sentence / interpretive sentence 분류 기준을 간단히 도입
- 확정 데이터 문장에 과도한 hedge marker가 붙으면 경고
- Post1에만 작동하는 경량 보정 또는 진단 추가
- “유보형 제거”보다 “불필요한 유보형 경고” 중심으로 접근 가능

### Track B 권장안
- verifier_revision_closure FAIL 케이스를 2~3개 범주로 분류
  - truly unresolved
  - wording-only residual
  - structurally resolved but marker mismatch
- false fail이 많다면 closure 판정 규칙을 좁혀라
- 보고서에 closure failure reason을 남겨 운영 해석 가능하게 하라

### Track C 권장안
- emergency_polish_count 정의:
  - total_warning_lines
  또는
  - unique_warning_markers
  둘 중 하나를 선택하고 전체에 통일
- 가능하면 count와 marker summary를 함께 저장
- handoff/report 템플릿에도 동일 명칭 사용

---

## 구현 후 자체 검증

아래를 스스로 점검하라.

### A. hedge_overuse_p1
- factual spine 문장이 이전보다 덜 흐려졌는가
- 해석/전망 구간의 필요한 hedge는 남아 있는가
- 글이 과하게 딱딱하거나 단정적으로 변질되지 않았는가

### B. verifier_revision_closure
- false fail이 줄었는가
- 진짜 unresolved 케이스는 여전히 잡는가
- step3_status / revision flow와 충돌이 없는가

### C. emergency_polish 정합성
- 로그 count와 보고서 count가 같은가
- 기준 정의가 문서에 명시되는가
- 운영자가 숫자 의미를 바로 이해할 수 있는가

### D. non-regression
- temporal SSOT 비회귀
- bridge-pick 정합성 유지
- intro overlap MEDIUM 이하 유지 가능 구조 유지
- step3_status 표준화 유지
- emergency_polish 관측 유지

---

## 산출물

반드시 아래 3가지를 제출하라.

### 1. 채팅 요약
- 무엇을 바꿨는지
- 왜 16G 이후 잔여 이슈에 맞는지
- 비회귀 위험은 없는지

### 2. 상세 보고서 MD
파일명 예시:
- `REPORT_PHASE16H_OPERATIONAL_STABILIZATION_AND_QUALITY_CLEANUP.md`

반드시 포함:
- 변경 파일 목록
- 변경 목적
- Track A/B/C 구현 상세
- hedge_overuse 처리 방식
- verifier_revision_closure 조정 방식
- emergency_polish 집계 기준 정의
- 비회귀 보호 설명
- 잔여 위험
- 다음 실출력 검증 포인트

### 3. handoff MD
파일명 예시:
- `handoff_phase16h.md`

---

## 최종 게이트 규칙

다음일 때만 `PHASE16H_IMPL_GO`로 판정하라.

- hedge_overuse_p1 완화 장치 또는 진단이 실제 코드에 반영됨
- verifier_revision_closure false fail 완화가 반영됨
- emergency_polish 집계 기준이 단일화됨
- 기존 16G GO 축에 회귀 없음
- syntax/runtime에 즉시 보이는 오류 없음

그 외에는 정직하게 HOLD 또는 PARTIAL로 보고하라.
