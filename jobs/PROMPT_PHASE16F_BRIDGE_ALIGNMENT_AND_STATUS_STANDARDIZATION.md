# PROMPT_PHASE16F_BRIDGE_ALIGNMENT_AND_STATUS_STANDARDIZATION.md

너는 macromalt 프로젝트의 Phase 16F 구현 담당 엔지니어다.

이번 페이즈의 목적은
Phase 16E에서 CONDITIONAL GO로 남은 두 가지 잔존 이슈를 미세조정으로 해결하는 것이다.

## Phase 16E 잔존 이슈
1. 브릿지 문장이 실제 픽 바스켓과 논리적으로 불일치하는 케이스 발생
2. `step3_status` 코드값 / 로그 / 보고서 표현이 서로 불일치하여 운영 해석 혼선 발생

이번 16F는 새로운 구조 개편 페이즈가 아니다.
Phase 16~16E에서 확보한 아래 성과를 절대 깨지 않는 범위에서 미세조정만 수행하라.

- temporal SSOT 비회귀
- 완료 월 [전망] 오주입 방지 유지
- intro overlap HIGH 탈출 성과 유지
- emergency_polish 상시 관측성 유지

---

## 절대 원칙

### 1. 브릿지-픽 정합성 우선
브릿지 문장은 “그럴듯한 문장”이 아니라
**실제 최종 선택된 픽 집합과 모순되지 않는 문장**이어야 한다.

금지:
- 픽 바스켓에 기술주가 없는데 “에너지 vs 기술” 같은 대비 축 사용
- 실제 종목군에 없는 공통점/대비점 발명
- 브릿지 문장이 픽 선정 후가 아니라 가상의 후보군 기준으로 생성되는 구조

필수:
- 브릿지 문장은 반드시 **최종 픽 리스트 확정 이후** 생성 또는 검증되어야 한다
- 브릿지는 최종 픽들의 실제 공통 논리 / 공통 민감도 / 공통 트리거 / 공통 리스크에만 기반해야 한다
- 공통 축이 약하면 브릿지를 과장하지 말고 더 좁고 안전한 설명으로 축소하라

### 2. step3_status 단일 표준화
`step3_status`는 코드 / 로그 / 보고서 / handoff에서 **동일 enum 체계**를 사용해야 한다.

해야 할 일:
- 현재 사용 중인 step3_status 관련 코드값 조사
- 실제 런타임 상태를 가장 잘 설명하는 최소 enum 세트로 정리
- generator.py, 로그 문자열, 보고서 템플릿, handoff 표현이 같은 명칭 체계를 쓰도록 정렬

권장:
- `REVISED`
- `FAILED_NO_REVISION`
- `FAILED_REVISION_ADOPTED`

위 체계가 이미 코드와 가장 가깝다면 그대로 통일하고,
다른 체계를 쓰려면 이유를 문서에 명시하라.

### 3. 기존 성과 비회귀
아래는 절대 깨지면 안 된다.
- temporal SSOT
- [전망]/[해석] 태그 규칙
- 시점 혼합 금지
- 권유성 표현 금지
- intro overlap 개선 추세
- emergency_polish INFO/WARNING 관측성

---

## 구현 목표

### Track A — Bridge Alignment Guard
아래 중 하나 이상의 방식으로 구현하라.

가능한 구현 방향:
- 브릿지 생성 전에 최종 픽 리스트를 인자로 넘겨 브릿지 문장 생성
- 브릿지 생성 후, 최종 픽 리스트와 의미적 불일치가 있으면 약화/재생성
- 공통 논리가 없으면 “같은 방향의 직접 수혜주”처럼 좁고 안전한 표현으로 다운그레이드
- 대비형 브릿지(예: 에너지 vs 기술)는 실제 양측 픽이 모두 있을 때만 허용

최종 목표:
- 브릿지가 실제 픽 바스켓과 모순되지 않음
- 형식적 브릿지가 아니라 실제 묶음 논리를 설명함

### Track B — step3_status Standardization
아래를 구현하라.

- 현재 step3_status 생성 지점 확인
- 로그 출력 지점 확인
- 보고서/핸드오프 생성 지점 확인
- enum 명칭을 하나로 통일
- 과거 보고서와 다른 명칭이 남아 있으면 매핑 코멘트 추가

최종 목표:
- 같은 상태를 두고 다른 이름이 나오지 않음
- 실출력 검증 보고서에서 해석 혼선이 없음

### Track C — Observability 유지
아래를 유지 또는 개선하라.

- `p16b_guard` 또는 후속 guard 구조에서
  - `step3_status`
  - `intro_overlap`
  - `emergency_polish`
  - threshold 정보
  가 계속 노출되어야 한다
- bridge 관련 진단이 가능하면 최소한의 로그를 추가하라
  - 예: bridge mode / bridge basis / basket theme summary

단, 로그 추가가 본문 생성 품질을 해치면 최소 수준만 넣어라.

---

## 구현 제한

- 대규모 구조개편 금지
- prompt/token 증가 과도화 금지
- regex 패치 남발 금지
- 브릿지 문장 하드코딩 금지
- 픽과 맞지 않는 예시문 상수화 금지

이번 페이즈는 16E CONDITIONAL GO를
실질적 GO에 가깝게 밀어주는 미세조정이어야 한다.

---

## 검증 기준

구현 후 아래를 자체 점검하라.

### A. Bridge alignment
- 브릿지 문장이 실제 최종 픽 바스켓과 모순되지 않는가
- 공통 논리가 없는 경우 과장 표현을 자동 축소하는가
- 대비형 문구가 허위 축을 만들지 않는가

### B. step3_status consistency
- 코드값과 로그값이 같은가
- 보고서/핸드오프 명칭도 같은가
- 과거 표현과 충돌 시 매핑 설명이 있는가

### C. Non-regression
- temporal SSOT 성과 유지
- [전망] 오주입 회귀 없음
- intro overlap 개선 구조 유지
- emergency_polish 관측 유지

---

## 산출물

반드시 아래 3가지를 제출하라.

1. 채팅 요약
- 무엇을 바꿨는지 10줄 내외
- 왜 16E 잔존 이슈에 맞는지
- 회귀 위험은 없는지

2. 상세 보고서 MD
파일명 예시:
- `REPORT_PHASE16F_BRIDGE_ALIGNMENT_AND_STATUS_STANDARDIZATION.md`

반드시 포함:
- 변경 파일 목록
- 변경 목적
- 구현 상세
- step3_status 표준안
- bridge alignment 로직 설명
- 비회귀 보호 설명
- 잔여 위험
- 다음 실출력 검증 포인트

3. handoff MD
파일명 예시:
- `handoff_phase16f.md`

---

## 최종 게이트 규칙

다음일 때만 `PHASE16F_IMPL_GO`로 판정하라.

- 브릿지-픽 정합성 보호 로직이 실제 코드에 반영됨
- step3_status 표준화가 코드/로그/문서 수준에서 정리됨
- 기존 temporal SSOT 성과에 회귀 없음
- syntax/runtime에 즉시 보이는 오류 없음

그 외에는 정직하게 HOLD 또는 PARTIAL로 보고하라.
