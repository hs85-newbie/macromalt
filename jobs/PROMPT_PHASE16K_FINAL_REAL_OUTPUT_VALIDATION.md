# PROMPT_PHASE16K_FINAL_REAL_OUTPUT_VALIDATION.md

너는 macromalt 프로젝트의 실출력 검증 담당 QA다.

이번 검증의 목적은
**Phase 16J에서 반영된 PARSE_FAILED 운영 표준화 + same-theme opener diversification 규칙이 실제 발행 출력물에서 효과를 냈는지**
실제 결과물 기준으로 최종 판정하는 것이다.

이번 Phase 16K는 **Phase 16 계열 종료 판정용 최종 실출력 검증**이다.
따라서 구현 요약, 커밋 메시지, 코드 diff가 아니라
반드시 **실제 최종 발행본 / 공개 URL / 최종 HTML / 실제 진단 로그 / 운영 보고서**를 기준으로만 판정하라.

---

## 이번 Phase 16K의 핵심 검증축

1. **PARSE_FAILED 운영 표준화 실효성**
   - `PARSE_FAILED`가 실제 런에서 발생해도 운영자가 혼선 없이 읽을 수 있는가
   - 코드 / 로그 / 보고서 / handoff / p16b_guard가 같은 의미 체계를 쓰는가
   - “검수 단계 skip, 수정 시도 없음”이 실제로 일관되게 전달되는가

2. **same-theme opener diversification 실효성**
   - 동일 theme 반복 감지 시 Post2 opener가 실제로 픽 논리 각도로 시작하는가
   - Post2 초반부가 Post1 매크로 배경의 압축 재서술처럼 읽히지 않는가
   - same_theme_hint / theme_repeat_diag가 실제 산문 변화와 논리적으로 맞는가

3. **continuity 체감 개선**
   - intro_overlap 수치뿐 아니라 실제 독자 체감상 “또 같은 이야기다” 느낌이 줄었는가
   - 동일 theme 연속 슬롯에서도 Post1/Post2 역할 분리가 유지되는가

4. **기존 성과 비회귀**
   - temporal SSOT 비회귀
   - 완료 월 [전망] 오주입 없음
   - bridge-pick 정합성 유지
   - step3_status 표준화 유지
   - emergency_polish 집계 정합성 유지
   - intro_overlap MEDIUM 이하 유지

---

## 반드시 확보할 것

### 1) 실제 실행 결과
- run_id
- slot
- theme
- Post1 최종 HTML
- Post2 최종 HTML
- 가능하면 공개 URL 2개
- 불가능하면 최종 발행 HTML 원문

### 2) 진단 / guard 데이터
- `p16b_guard.step3_status`
- `p16b_guard.parse_failed`
- `p16b_guard.intro_overlap`
- `p16b_guard.emergency_polish`
- `p16b_guard.bridge_diag`
- `p16b_guard.theme_repeat_diag`
- `unique_marker_count`
- `total_occurrence_count`

### 3) 운영 보고 자료
- REPORT_PHASE16K_* 또는 동급 보고서
- handoff_phase16k.md 또는 동급 문서
- PARSE_FAILED 표기 예시
- theme_repeat_diag 표기 예시

---

## 핵심 검증 질문

### A. PARSE_FAILED 운영 표준화 검증
아래를 확인하라.

- 실제 런에서 `PARSE_FAILED`가 나왔는가
- 나왔다면 코드 / 로그 / 보고서 / handoff에서 동일한 의미로 설명되는가
- “검수 단계 skip, 수정 시도 없음”이 누락되거나 다른 말로 왜곡되지 않는가
- `FAILED_NO_REVISION`과 혼동되지 않는가

반드시 보고할 것:
- 상태명 표본
- 로그 문구
- 보고서 문구
- handoff 문구
- p16b_guard 내 관련 필드

판정 기준:
- 같은 상태를 모두 같은 의미로 읽을 수 있으면 PASS
- 표현 차이는 있지만 매핑이 명확하면 CONDITIONAL
- 상태 해석이 흔들리거나 혼용되면 FAIL

### B. same-theme opener diversification 검증
아래를 체크하라.

- 동일 theme 반복이 감지되었는가
- 감지되었다면 Post2 opener가 실제로 픽 논리 / 바스켓 논리 / 종목 민감도로 시작하는가
- Post1의 매크로 메커니즘 설명을 다시 압축 반복하지 않는가
- “오늘 이 테마를 보는 이유”가 길게 재서술되지 않는가

반드시 보고할 것:
- Post2 첫 1~3문단 요약
- same_theme_hint / theme_repeat_diag 값
- opener가 달라졌다고 볼 근거 문장
- 여전히 반복된다고 느껴지는 문장

판정 기준:
- Post2 초반이 독립적인 픽 리포트처럼 읽히면 PASS
- 일부 개선되었으나 반복감이 남으면 CONDITIONAL
- 여전히 Post1 압축판처럼 읽히면 FAIL/HOLD

### C. continuity 체감 검증
아래를 확인하라.

- intro_overlap 수치는 얼마인가
- 실제 독자 체감상 비슷한 글로 읽히는가
- 동일 테마라도 Post1은 macro mechanism, Post2는 pick rationale로 역할 분리되는가

기본 방식:
- intro 300 chars 기준
- char-level 4-gram overlap
- shared / max(ng1, ng2)
- status = LOW / MEDIUM / HIGH

반드시 보고할 것:
- overlap_ratio
- status
- shared 4-gram count
- intro 길이
- 반복 표현 예시 5개 이상
- 체감상 중복도 평가

판정 기준:
- MEDIUM 이하 + 체감 반복 감소면 PASS
- MEDIUM이지만 체감상 여전히 유사하면 CONDITIONAL
- HIGH 재상승 또는 체감 반복 심하면 FAIL

### D. non-regression 검증
아래를 확인하라.

1. temporal SSOT 비회귀
2. [전망]/[해석] 태그 규칙 유지
3. bridge-pick 정합성 유지
4. step3_status 표준화 유지
5. emergency_polish 집계 정합성 유지
6. intro_overlap MEDIUM 이하 유지

---

## 정량 + 정성 판정 방식

### 1) 정량
- intro overlap ratio / status
- step3_status / parse_failed 여부
- theme_repeat_diag 값
- emergency_polish unique / total count
- bridge_diag 값

### 2) 정성
- Post2 opener가 실제로 달라졌는가
- PARSE_FAILED 상태가 운영적으로 읽기 쉬운가
- Post1/Post2 역할 분리가 독자 체감상 살아 있는가
- 16G~16I에서 확보한 안정성이 유지되는가

---

## 최종 판정 규칙

### GO
- PARSE_FAILED 운영 표준화가 실제로 잘 작동
- same-theme opener diversification이 실제 글에서 체감됨
- continuity 체감 개선 확인
- 16G/16I 핵심 성과 비회귀
- 운영적으로 Phase 16 종료 가능

### CONDITIONAL GO
- 핵심은 개선됐으나
- 일부 경계 케이스 또는 theme 반복 체감 이슈가 남음
- 매우 작은 후속 조정 1회면 해결 가능

### HOLD
- PARSE_FAILED 해석 혼선 지속
- same-theme opener가 실제 글에 반영되지 않음
- continuity FAIL이 계속 체감됨
- 기존 핵심 성과 중 하나라도 회귀

---

## 출력 형식

반드시 아래 순서로 보고하라.

1. 작업 개요
2. 확보한 입력물 목록
3. Post1 / Post2 실출력 요약
4. PARSE_FAILED 운영 표준화 검증
5. same-theme opener diversification 검증
6. continuity 체감 검증
7. intro overlap 정량 결과
8. shared 4-gram / 반복 표현 예시
9. bridge / step3_status / temporal / emergency_polish 비회귀 여부
10. 최종 판정 (GO / CONDITIONAL GO / HOLD)
11. 남은 리스크
12. 필요 시 Phase 16L 또는 Phase 17 제안

---

## 절대 금지

- 구현 요약만 보고 성공 판정
- same_theme_hint 존재만 보고 opener 개선 판정
- PARSE_FAILED를 이름만 같다고 표준화 성공으로 간주
- overlap 수치 없이 체감만으로 continuity 평가
- 비회귀 검증 없이 종료 판정

최종 목표는
**“Phase 16J가 Phase 16 계열을 종료 가능한 수준까지 안정화했는지”**
실출력 기준으로 냉정하게 판정하는 것이다.
