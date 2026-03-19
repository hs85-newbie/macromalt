# PROMPT — Phase 16D Continuity and Bridge Hardening

## 0. Role
너는 **Macromalt Phase 16D 구현 담당 엔지니어**다.
이번 페이즈의 목적은 **Phase 16/16A에서 확보한 temporal SSOT 성과를 절대 훼손하지 않으면서**, Phase 16C에서 HOLD를 발생시킨 **Post1/Post2 continuity 중복**, **Post2 픽-테마 분산**, **`emergency_polish` 관측성 부족**을 해결하는 것이다.

이번 작업은 **대규모 구조 개편이 아니라, 16B/16C 결과를 바탕으로 한 정밀 보강 페이즈**다.

---

## 1. 반드시 먼저 읽을 문서
아래 문서를 먼저 읽고, 그 기준에 맞춰 구현하라.

1. `PROMPT_PHASE16_TEMPORAL_STATE_NORMALIZATION.md`
2. `REPORT_PHASE16_TEMPORAL_STATE_NORMALIZATION.md`
3. `REPORT_PHASE16A_REAL_OUTPUT_VALIDATION.md`
4. `REPORT_PHASE16B_OUTPUT_QUALITY_HARDENING.md` 가 있으면 읽고, 없으면 관련 handoff/summary를 참고
5. `REPORT_PHASE16C_REAL_OUTPUT_VALIDATION.md`
6. `handoff_phase16.md`
7. Macromalt PRD / Writing & Verification Rules / Dedup 관련 SSOT 문서

문서 간 충돌 시 우선순위는 아래와 같다.

1. 최신 실출력 검증 보고서
2. 최신 handoff
3. Phase 16 temporal SSOT 설계 문서
4. Macromalt 상위 PRD / style / writing rules

---

## 2. Phase 16C에서 확인된 사실
이번 16D는 아래 사실을 전제로 한다.

### 2.1 유지된 성과
- `FAILED_REVISION_ADOPTED` 경로가 정상 로깅되었고, Step3 수정본 채택 경로가 실제 런에서 작동했다.
- temporal SSOT는 비회귀 상태다.
- Phase 15D 계층이 2025 실적 `[전망]` 오표기를 자동 교정했다.
- `p16b_guard.intro_overlap`는 실제 산문 중복을 HIGH로 감지했다.

### 2.2 HOLD 원인
- Post1/Post2 도입부 및 초기 전개에서 **34.7% HIGH 중복**이 발생했다.
- Post2가 **Post1의 매크로 배경을 재서술**하는 경향이 남아 있다.
- Post2의 종목 선택 축이 분산되며, **픽-테마 브릿지 문장**이 약하거나 누락된다.
- `emergency_polish` 로그가 실제 런에서 보이지 않아, fallback/diagnostic 관측성이 불완전하다.

즉, 16D는 **시제 수정 페이즈가 아니라, Post2의 진입 각도와 종목 선정 논리를 분리·정렬하고, 관측성을 보강하는 페이즈**다.

---

## 3. 이번 페이즈의 한 줄 목표
**Post2가 Post1의 매크로 서론을 반복하지 않고 종목/픽 관점에서 즉시 진입하도록 고정하며, 선택 종목의 공통 투자 논리를 짧고 명료한 브릿지 문장으로 연결하고, p16b_guard 및 emergency_polish 관측성을 완성한다.**

---

## 4. 구현 목표

### Track A — Post2 continuity 중복 억제 강화
Post2 시스템 프롬프트 또는 생성 블록에 아래 원칙을 명시적으로 추가하라.

- Post2는 **Post1의 매크로 배경을 다시 길게 설명하지 않는다.**
- 호르무즈 해협, 브렌트유, FOMC, 달러, 지정학 리스크 등 거시 키워드를 반복하더라도 **배경 요약 1~2문장 이하**로 제한한다.
- Post2는 반드시 **종목/섹터/포지셔닝 관점에서 즉시 진입**해야 한다.
- “오늘 이 테마를 보는 이유” 같은 섹션이 있더라도, **Post1과 동일한 매크로 서술을 복제하지 않게** 강하게 제한하라.
- 가능하면 Post2 첫 단락은 “거시 현상 설명”이 아니라 “이 거시 변화가 왜 이 종목 바스켓에 연결되는가”로 시작하게 하라.

구현은 프롬프트 레벨, 생성 블록 레벨, 혹은 후속 품질 가드 레벨 중 가장 안전한 방식으로 하되, **temporal SSOT와 충돌하지 않는 방향**이어야 한다.

### Track B — Post2 픽-테마 브릿지 강제
Post2에서 종목들이 단순 나열되지 않도록, 아래 조건을 강제하라.

- 종목 리스트 진입 전에 **공통 테마를 요약하는 1~2문장 브릿지**가 반드시 존재해야 한다.
- 브릿지는 “왜 이 종목들이 한 바구니에 담겼는가”를 설명해야 한다.
- 서로 다른 성격의 종목이 함께 들어갈 경우, 반드시 **묶는 기준**을 먼저 제시해야 한다.
- 브릿지가 없으면 Step3 또는 품질 진단 단계에서 명시적으로 감점/탐지 가능해야 한다.

예시 방향:
- 고유가 수혜 바스켓
- 유가 민감도 + 실적 레버리지 바스켓
- AI/반도체를 같이 넣어야 한다면, 왜 지금 이 매크로 국면에서 그 축을 함께 보는지 연결 논리를 먼저 제시

단, 예시는 설명용일 뿐이며 하드코딩 문구로 박지 마라.

### Track C — intro overlap 진단 보강
현행 `intro_overlap` 진단을 보강하라.

필수 요구:
- 현재 overlap 수치뿐 아니라 **threshold / status / 비교 기준**이 함께 보이게 하라.
- 가능하면 **어느 구간이 중복 원인인지**를 짧게 식별할 수 있는 보조 정보도 남겨라.
- 단, 과도한 로그로 운영 노이즈가 커지지 않도록 핵심만 남겨라.

핵심은 16C에서 나온 `34.7% HIGH`가 단순 숫자가 아니라, **왜 HIGH인지 재현 가능하게 만드는 것**이다.

### Track D — `emergency_polish` 관측성 완성
`emergency_polish`는 치환이 아니라 진단 전용 계층이므로, 이번 16D에서도 **본문 수정은 금지**한다.

하지만 아래는 반드시 만족시켜라.

- 실행 여부
- skip 여부
- skip 이유
- generic marker 탐지 수
- 상태(status)

위 최소 정보는 실제 런 로그 또는 `p13_scores` 계열 진단에 남아야 한다.

중요:
- `emergency_polish.applied=False` 원칙은 유지하라.
- 이 계층이 **시제/숫자/서술 내용을 수정해서는 안 된다.**
- 이번 페이즈는 **관측성 보강**이지 **자동 문장 교정 확장**이 아니다.

### Track E — Temporal SSOT 비회귀 보호
이번 16D는 continuity/tone/bridge 페이즈지만, 아래는 절대 깨지면 안 된다.

- 완료 월 `[전망]` 오주입 0건
- `p16_ssot_run` 정상 기록
- `p15f_strip` 진단 일치
- settled month future verb 제거 유지
- Step3 / fallback / post-process가 시간을 독립적으로 재해석하지 않음

16D 구현 중 temporal 관련 로직에 손대야 한다면, 그 이유와 범위를 최소화하고 명시하라.

---

## 5. 구현 원칙

1. **대규모 재작성 금지**
   - 이번 페이즈는 16C HOLD 원인 3개를 좁혀 잡는 미세 수정이다.

2. **Post2 우선 수정**
   - continuity와 브릿지 문제의 중심은 Post2다.
   - Post1까지 불필요하게 건드리지 마라.

3. **진단 우선, 자동 치환 최소화**
   - 관측성을 먼저 완성하라.
   - 실제 문장 치환/재작성은 다음 단계에서 필요할 때만 판단한다.

4. **Macromalt premium tone 유지**
   - 싸구려 카피처럼 보이는 강한 금지문 남발 금지.
   - 품질 강화 규칙은 “세련된 투자 편집물” 방향을 유지해야 한다.

5. **실출력 기준으로 설명 가능해야 함**
   - 구현 후 “왜 overlap이 줄었는지”, “왜 브릿지가 생겼는지”, “왜 emergency_polish가 보이게 됐는지”를 설명할 수 있어야 한다.

---

## 6. 금지 사항
- 16/16A의 temporal SSOT 성과를 깨는 수정
- `emergency_polish`에서 실제 prose 자동 치환 활성화
- Post2 중복 문제를 해결한다는 이유로 Post2를 과도하게 짧고 밋밋하게 만드는 수정
- 브릿지 강제를 하드코딩 문구 반복으로 해결하는 방식
- 특정 기사/테마 전용 예외 패치 남발

---

## 7. 구현 후 자체 점검 체크리스트
아래를 스스로 점검하고 결과에 포함하라.

1. Step3 성공/실패와 무관하게 `step3_status`가 분명히 남는가?
2. `p16b_guard.intro_overlap`에 수치 + 상태 + 기준 정보가 남는가?
3. `emergency_polish`의 실행/스킵 여부와 이유가 보이는가?
4. Post2 시작부가 Post1 매크로 서론을 거의 재서술하지 않도록 유도되는가?
5. Post2 종목 바스켓 앞에 브릿지 논리가 필수화됐는가?
6. temporal SSOT 비회귀가 보장되는가?
7. syntax check / compile / 최소 런타임 점검이 통과하는가?

---

## 8. 제출 형식
결과는 **채팅 요약 + 상세 MD 보고서**로 제출하라.

### 8.1 채팅 요약
아래 형식으로 아주 간결히 제출하라.

- 게이트: `PHASE16D_IMPL_GO` 또는 `PHASE16D_IMPL_HOLD`
- 커밋 해시
- 변경 파일 목록
- 구현 포인트 3~6줄
- 잔여 위험 1~3개

### 8.2 상세 MD 보고서
파일명 예시:
- `REPORT_PHASE16D_CONTINUITY_AND_BRIDGE_HARDENING.md`
- `handoff_phase16d.md`

상세 보고서에는 아래를 반드시 포함하라.

1. 배경
2. 16C HOLD 원인 재정리
3. 구현 변경점
4. continuity 억제 장치 설명
5. 브릿지 강제 장치 설명
6. emergency_polish 관측성 변경 설명
7. temporal SSOT 비회귀 보호 설명
8. 정적 검증 결과
9. 잔여 위험
10. 다음 Phase 16E 실출력 검증 포인트

---

## 9. 최종 기준
이번 16D는 아래가 만족되면 구현 GO다.

- Post2 중복 억제 장치가 실제 코드/프롬프트 레벨에 들어감
- Post2 픽-테마 브릿지 강제가 구현됨
- `emergency_polish` 진단 가시성이 확보됨
- intro overlap 진단이 더 해석 가능해짐
- temporal SSOT 성과 비회귀가 보장됨
- syntax / 기본 정적 검증이 통과함

실출력 품질의 최종 판단은 **Phase 16E real output validation**에서 한다.
