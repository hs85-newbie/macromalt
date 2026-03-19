# PROMPT_PHASE16J_THEME_ROTATION_AND_PARSEFAILED_STANDARDIZATION.md

너는 macromalt 프로젝트의 Phase 16J 구현 담당 엔지니어다.

이번 Phase 16J의 목적은
**Phase 16I에서 CONDITIONAL GO로 남은 두 가지 잔여 이슈를 미세조정으로 정리하여
Phase 16 계열을 안정적으로 종료 가능한 상태로 만드는 것**이다.

이번 16J는 구조 개편이 아니다.
Phase 17로 가기 전 마지막 마감 정리 페이즈다.

---

## Phase 16I 잔여 이슈

### 이슈 1 — Post2 `step3_status = PARSE_FAILED`
- Gemini verifier JSON 파싱 실패가 실제 런에서 다시 발생
- 현재 파이프라인은 graceful 처리되지만
  운영 기준상 표준 enum 외 상태가 남아 있음
- 코드/로그/보고서/handoff에서 이 상태를 어떻게 해석할지 더 명확히 해야 함

### 이슈 2 — post1_post2_continuity FAIL
- intro_overlap 수치는 MEDIUM 수준으로 유지되고 있지만
- 실제 독자 체감상 Post2 초반부가 Post1의 매크로 배경을 다시 압축 설명하는 경향이 남아 있음
- 이건 더 이상 문장 패치보다
  **slot/theme 운영 규칙과 theme rotation 정책**으로 다뤄야 할 가능성이 높음

---

## 이번 16J의 핵심 목표

1. **PARSE_FAILED 운영 표준화**
2. **동일 theme 반복 시 Post1/Post2 연속성 누적 억제**
3. **16G/16I까지 확보한 핵심 성과 비회귀 유지**

---

## Track A — PARSE_FAILED 운영 표준화

### 목표
`PARSE_FAILED`가 실제 런타임에서 다시 발생해도
운영자가 해석에 혼선이 없도록
**코드 / 로그 / 보고서 / handoff에서 단일 기준으로 읽히게 만들 것**

### 해야 할 일
- 현재 `PARSE_FAILED`가 어떤 조건에서 발생하는지 정리
- 이 상태를 표준 enum 체계 안에서 어떻게 취급할지 명확히 규정
- 코드 주석 / 로그 메시지 / 보고서 템플릿 / handoff 표현을 정렬
- `PARSE_FAILED`가 있어도 최종 발행 경로가 어떤 의미인지 운영자가 바로 알 수 있게 설명 추가

### 선택지
아래 둘 중 하나를 택하라.

#### 옵션 A
`PARSE_FAILED`를 독립 상태로 유지
- 장점: 실제 원인 보존
- 조건: 운영 문서에서 의미를 명확히 설명해야 함

#### 옵션 B
운영 표기상 `FAILED_NO_REVISION` 계열로 통합
- 장점: 상태 단순화
- 조건: 실제 파싱 실패와 수정 실패의 차이를 별도 필드로 보존해야 함

어느 쪽을 택하든:
- 코드/로그/보고서/handoff에서 해석 충돌이 없어야 한다
- “표준 enum 외 상태가 튀어나온다”는 인상을 줄이면 안 된다

### 금지
- 의미를 숨긴 채 상태명을 단순 치환
- 런타임 의미는 다른데 문서상 같은 뜻으로 뭉개기
- 실제 실패 경로를 없애버리는 식의 위장

---

## Track B — Theme Rotation / Continuity 운영 규칙 보강

### 목표
같은 매크로 테마가 연속 슬롯에서 반복될 때
Post1과 Post2가 서로 “압축 재서술”처럼 읽히는 문제를
**생성 문장 패치가 아니라 운영 규칙/선택 규칙 수준에서 완화**하라.

### 문제 정의
지금까지는
- intro_overlap LOW/MEDIUM
- bridge COMMON
- step3_status 정리
까지는 달성했지만
동일 theme가 반복되면 Post2 초반부가 결국 Post1의 매크로 설명을 다시 요약하는 경향이 남아 있다.

이 문제는 다음 중 하나 이상으로 해결해야 한다.

### 권장 구현 방향
아래 중 1개 이상 반영하라.

#### 방향 1 — 슬롯 간 theme reuse penalty
- 최근 N회 슬롯에서 같은 macro theme가 반복되면 penalty 부여
- Post2 종목 선정/도입 구조에서 동일 설명을 다시 쓰지 않도록 유도

#### 방향 2 — Post1/Post2 role separation 강화
- Post1은 macro mechanism / market structure
- Post2는 sector sensitivity / pick rationale / basket logic
- 동일 theme일수록 Post2에서 macro recap 허용량을 더 줄임

#### 방향 3 — opening angle diversification 규칙 강화
- 동일 theme 연속 시 Post2 첫 2~3문단은
  macro summary가 아니라
  “픽 바스켓의 공통 민감도 / 왜 이 종목들인가 / 어떤 트리거에 베팅하는가”
  로 시작하도록 강제

#### 방향 4 — 동일 theme 연속성 경고 진단
- 생성 전 또는 생성 후,
  최근 slot과 theme/angle 유사도가 높으면 warning
- 운영자가 “이번 글이 또 비슷하다”는 것을 발행 전에 알 수 있게 함

### 반드시 지킬 것
- bridge alignment는 유지
- intro overlap 기존 로직은 깨지 말 것
- Post2가 억지로 낯선 주제를 만드는 식으로 품질을 떨어뜨리면 안 됨
- 같은 theme라도 angle이 다르게 읽히게 만드는 것이 목표다

---

## 비침범 영역

이번 16J에서 아래는 건드리지 말 것.

- temporal SSOT
- [전망] / [해석] 태그 규칙
- hedge_overuse_p1 로직
- verifier_revision_closure 기본 구조
- intro_overlap 계산식 자체
- bridge_diag 기본 로직
- step3_status의 기존 PASS/REVISED/FAILED_NO_REVISION 의미

즉 16J는 **표준화 + 운영 회전 규칙 보강**이다.

---

## 구현 원칙

1. **작게 고치고 운영적으로 크게 안정화**
- 구조를 뒤엎지 말고
- 운영/진단/선택 규칙을 미세조정하라

2. **문장 패치보다 선택 규칙 우선**
- continuity 잔여 이슈를 regex나 문장 치환으로 막으려 하지 말 것
- slot/theme/angle 운영 규칙에서 해결을 우선하라

3. **운영자가 읽을 수 있는 상태명**
- `PARSE_FAILED`는 기술적으로 정확하면서도
  운영자가 이해 가능한 의미 체계 안에 있어야 한다

4. **비회귀 우선**
- 16G/16I 성과 축이 하나라도 깨지면 16J는 실패다

---

## 구현 후 자체 검증

### A. PARSE_FAILED 표준화
- 코드/로그/보고서/handoff가 같은 의미 체계를 쓰는가
- 운영자가 상태를 보고 바로 이해할 수 있는가
- 실제 파싱 실패와 수정 실패가 혼동되지 않는가

### B. continuity 운영 규칙
- 동일 theme 반복 시 Post2 각도 분산 장치가 생겼는가
- Post1 매크로 재서술 억제 규칙이 강화되었는가
- slot/theme rotation 관련 경고나 penalty가 생겼는가

### C. non-regression
- bridge-pick 정합성 유지
- intro_overlap MEDIUM 이하 유지 가능 구조
- temporal SSOT 유지
- step3_status 표준화 유지
- emergency_polish 집계 정합성 유지

---

## 산출물

반드시 아래 3가지를 제출하라.

### 1. 채팅 요약
- 무엇을 바꿨는지
- 왜 16I 잔여 이슈에 맞는지
- 비회귀 위험은 없는지

### 2. 상세 보고서 MD
파일명 예시:
- `REPORT_PHASE16J_THEME_ROTATION_AND_PARSEFAILED_STANDARDIZATION.md`

반드시 포함:
- 변경 파일 목록
- Track A/B 구현 상세
- PARSE_FAILED 표준화 방안
- theme rotation / continuity 운영 규칙 설명
- 비회귀 보호 설명
- 잔여 위험
- 다음 실출력 검증 포인트

### 3. handoff MD
파일명 예시:
- `handoff_phase16j.md`

---

## 최종 게이트 규칙

다음일 때만 `PHASE16J_IMPL_GO`로 판정하라.

- PARSE_FAILED 운영 표준화가 반영됨
- continuity를 운영 규칙 측면에서 줄이는 장치가 반영됨
- 16G/16I의 핵심 GO 축에 회귀 없음
- syntax/runtime에 즉시 보이는 오류 없음

그 외에는 정직하게 HOLD 또는 PARTIAL로 보고하라.
