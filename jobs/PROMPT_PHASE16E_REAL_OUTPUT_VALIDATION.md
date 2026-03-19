# PROMPT_PHASE16E_REAL_OUTPUT_VALIDATION

너는 macromalt 프로젝트의 실출력 검증 담당 QA다.

이번 검증의 목적은
“Phase 16D에서 반영된 continuity/bridge hardening이 실제 발행 출력물에서 효과를 냈는지”
실제 결과물 기준으로 판정하는 것이다.

중요:
- 초안이나 코드 diff만 보고 판단하지 말고
- 실제 최종 출력 HTML 또는 실제 공개 발행본 기준으로만 판정하라
- 가능하면 공개 URL 기준으로 검증하고,
  불가능하면 최종 저장된 HTML 본문 원문 기준으로 검증하라
- wp-admin 편집 화면이나 커밋 메시지만으로 GO 판정하지 말라

이번 검증은 특히 아래 16D 반영사항의 실효성을 확인하는 데 초점을 둔다.

## 검증 대상
1. Post2 도입부에서 Post1의 매크로 배경을 다시 길게 반복하는 현상이 줄었는가
2. Post2가 초반부터 종목/섹터/포지셔닝 각도로 빠르게 진입하는가
3. 픽 섹션 직전에 “왜 이 종목들을 한 바구니로 묶는가”에 대한 브리지 문장이 실제로 들어갔는가
4. intro overlap이 여전히 HIGH 수준으로 남는가, 아니면 낮아졌는가
5. emergency_polish / step3 guard 관측값이 실제 출력과 논리적으로 맞는가
6. continuity 개선 때문에 기존 시점 규칙, 사실/해석/전망 분리, 권유성 억제 규칙이 깨지지 않았는가

---

## 반드시 확보할 것

아래 자료를 최대한 확보하라.

### 1. Phase 16E 실제 실행 결과
- run_id
- slot
- theme
- Post1 최종 HTML
- Post2 최종 HTML
- 가능하면 공개 URL 2개
- 불가능하면 최종 발행 직전 HTML 원문

### 2. p13_scores 또는 이에 준하는 진단값
- p16b_guard.step3_status
- p16b_guard.fallback_triggered
- p16b_guard.emergency_polish
- p16b_guard.intro_overlap
- intro_overlap.thresholds
- intro_overlap.intro_chars_used

### 3. source/date 관련 실출력 정보
- 본문에 반영된 핵심 근거
- 기준 시점
- 참고 출처 섹션

---

## 핵심 검증 질문

### A. Post2 continuity 개선 검증
아래를 체크하라.

- Post2 첫 1~3문단이 또 하나의 거시 브리핑처럼 시작하는가?
- 아니면 종목/섹터/민감도/포지셔닝 관점으로 빠르게 진입하는가?
- “오늘 이 테마” 같은 매크로 재설명 블록이 2문장 이내로 억제되었는가?
- Post1과 동일한 문장 구조, 동일한 표현, 동일한 키워드 묶음이 반복되는가?

판정 기준:
- Post2 초반이 독립 종목 리포트처럼 읽히면 PASS 쪽
- Post1 요약본처럼 읽히면 FAIL 쪽

### B. bridge requirement 실효성 검증
픽 섹션 직전 또는 픽 도입부에 아래 기능이 실제로 있는지 보라.

- “왜 지금 이 종목군인가”
- “이 종목들을 함께 봐야 하는 이유”
- “공통 투자 논리 / 공통 트리거 / 공통 리스크”

단순 문장 1개가 아니라,
독자가 “왜 이 종목 묶음이 나왔는지” 이해할 수 있어야 한다.

판정 기준:
- 공통 논리 브리지 존재 + 실제 종목 단락과 연결되면 PASS
- 그냥 종목 나열로 넘어가면 FAIL

### C. intro overlap 실출력 검증
Post1/Post2의 도입부를 기준으로 중복률을 재검증하라.

기본 방식:
- intro 300 chars 기준
- char-level 4-gram overlap
- shared / max(ng1, ng2)
- status = LOW / MEDIUM / HIGH

반드시 보고할 것:
- overlap_ratio
- shared 4-gram count
- status
- 사용한 intro 길이
- 공유 표현 예시 5개 이상

판정 기준:
- HIGH면 원칙적으로 HOLD
- MEDIUM이면 문맥상 허용 가능한지 정성 검토
- LOW면 개선 성공 가능성이 높음

중요:
숫자만 보지 말고,
실제 독자가 읽을 때 “또 같은 이야기다”라고 느끼는지도 함께 적어라.

### D. step3 / emergency_polish 관측성 검증
아래를 확인하라.

- step3_status 값이 무엇인가
- emergency_polish가 routine-diagnostic / fallback-diagnostic 중 어떤 모드로 기록됐는가
- 그 값이 실제 최종 출력 결과와 논리적으로 맞는가
- fallback_triggered가 True/False일 때 실제 본문 품질과 괴리가 없는가

추가 확인:
- step3_status 명칭이 REVISED / FAILED_REVISION_ADOPTED 계열로 혼용되는지
- 운영 보고 문자열과 실제 코드/실출력 해석이 충돌하지 않는지

### E. 기존 품질 규칙 회귀 여부
Phase 16D의 continuity 개선 때문에 아래가 깨지지 않았는지 검증하라.

#### 1. 시점 혼합
- 과거 사실 + 미래 전망 혼합
- 미래 추정치를 현재 사실처럼 서술
- 본문에 없는 절대 날짜 발명

#### 2. 권유성 표현
- 매수 기회
- 저평가 매력
- 하방 경직성 제공
- 수혜를 받을 수 있는
- 직접/완곡 투자 권유 표현

#### 3. 사실 / 해석 / 전망 분리
- 사실과 해석이 섞여 있지 않은가
- 전망 문장이 조건부/명시적 구분 없이 단정되지 않았는가

#### 4. source/date 대응
- 본문 핵심 주장과 참고 출처가 실제로 대응되는가
- 기준 시점 누락이 없는가

---

## 정량 + 정성 판정 방식

아래 2축으로 판정하라.

### 1) 정량
- intro overlap ratio
- intro overlap status
- Post2 초반 3문단 내 종목/섹터 직접 진입 여부
- 브리지 문단 존재 여부
- step3 / fallback / emergency_polish 관측값

### 2) 정성
- Post2가 아직도 Post1 그림자처럼 읽히는가
- 브리지가 실제 투자 논리를 묶는가
- 종목 리포트 밀도가 살아 있는가
- 억지로 차별화하다가 오히려 글이 부자연스러워지지 않았는가

---

## 최종 판정 규칙

### GO
- intro overlap이 LOW 또는 허용 가능한 MEDIUM
- Post2 초반이 종목/섹터 각도로 명확히 분리
- 브리지 문단이 실제로 작동
- 시점/권유성/사실성 규칙 회귀 없음

### CONDITIONAL GO
- 일부 표현 중복은 남아 있으나
- Post2 구조 분리가 확실해졌고
- 브리지도 존재하며
- 운영상 추가 미세조정으로 해결 가능

### HOLD
- intro overlap이 여전히 HIGH
- Post2 초반이 사실상 Post1 재서술
- 브리지 부재 또는 형식적 존재
- 시점 혼합/권유성/사실성 회귀 존재

---

## 출력 형식

반드시 아래 순서로 보고하라.

1. 작업 개요
2. 확보한 입력물 목록
3. Post1 / Post2 실출력 요약
4. Post2 continuity 검증
5. bridge requirement 검증
6. intro overlap 정량 결과
7. shared 4-gram / 반복 표현 예시
8. step3 / emergency_polish / fallback 관측 결과
9. 시점 혼합 / 권유성 / 사실-해석 분리 회귀 여부
10. source/date 대응 여부
11. 최종 판정 (GO / CONDITIONAL GO / HOLD)
12. 남은 리스크
13. 다음 Phase 16F로 넘길 보완 포인트

---

## 절대 금지

- 커밋 메시지만 보고 성공 판정
- 초안만 보고 성공 판정
- 공개 URL 없이 “대체로 잘 됨” 식 보고
- overlap 수치 없이 “중복 줄어든 듯함” 식 추정 보고
- 권유성/시점 혼합 회귀를 무시하고 continuity만 보고 GO 판정

최종 목표는
“16D가 실제 출력 품질을 개선했는지”
실출력 기준으로 냉정하게 판정하는 것이다.
