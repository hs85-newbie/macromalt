# PROMPT_PHASE16G_REAL_OUTPUT_VALIDATION.md

너는 macromalt 프로젝트의 실출력 검증 담당 QA다.

이번 검증의 목적은
**Phase 16F에서 반영된 bridge alignment / step3_status standardization / bridge diagnostics가 실제 발행 출력물에서 효과를 냈는지**
실제 결과물 기준으로 판정하는 것이다.

이번 검증은 초안, 커밋 메시지, 구현 요약이 아니라
**실제 발행본 / 최종 HTML / 실제 진단 로그**를 기준으로만 판단해야 한다.

---

## 이번 Phase 16G의 핵심 검증축

1. **브릿지-픽 정합성**
   - 브릿지 문장이 실제 최종 픽 바스켓과 논리적으로 맞는가
   - 대비형 브릿지가 실제 양쪽 섹터 픽이 있을 때만 등장하는가
   - 동일 섹터 픽이면 공통 수혜/민감도/트리거 축으로 안전하게 정리되는가

2. **step3_status 표준화**
   - 코드/로그/보고서/핸드오프에서 step3_status가 동일 체계로 쓰이는가
   - `REVISED`, `FAILED_NO_REVISION`, `PASS` 등 상태명이 섞이지 않고 일관되게 해석되는가
   - 구 표기(`FAILED_REVISION_ADOPTED`) 잔재가 있으면 매핑 설명과 함께 처리되는가

3. **bridge_diag 실효성**
   - `bridge_diag.bridge_mode`
   - `bridge_diag.contrast_risk`
   - 관련 guard 값이 실제 발행 품질과 논리적으로 맞는가
   - 나쁜 브릿지 케이스를 진짜로 잡아내는가

4. **기존 성과 비회귀**
   - temporal SSOT 비회귀
   - 완료 월 [전망] 오주입 없음
   - 시점 혼합 없음
   - intro_overlap MEDIUM 이하 유지
   - emergency_polish 관측성 유지

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
- `p16b_guard.intro_overlap`
- `p16b_guard.emergency_polish`
- `p16b_guard.bridge_diag`
- `intro_overlap.thresholds`
- `intro_overlap.intro_chars_used`

### 3) 운영 보고/핸드오프 자료
- REPORT_PHASE16G_* 또는 동급 보고서
- handoff_phase16g.md 또는 동급 문서
- step3_status 표기 예시
- bridge_diag 표기 예시

---

## 핵심 검증 질문

### A. 브릿지-픽 정합성 검증
아래를 확인하라.

- 브릿지 문장이 실제 최종 픽 구성과 모순되지 않는가
- “에너지 vs 기술” 같은 대비형 표현이 나왔다면 실제로 양쪽 픽이 존재하는가
- 픽이 동일 섹터/동일 민감도 바스켓이면 브릿지가 공통 축으로 설명되는가
- 브릿지가 형식적 장식이 아니라 실제 바스켓 논리를 설명하는가

판정 기준:
- 실제 픽 바스켓 논리를 정확히 설명하면 PASS
- 그럴듯하지만 바스켓과 안 맞으면 FAIL
- 부분적으로 맞지만 과장/불필요한 대비가 남아 있으면 CONDITIONAL

### B. step3_status 표준화 검증
아래를 체크하라.

- 실제 로그에서 상태명이 무엇으로 찍히는가
- 보고서에서 동일 상태를 같은 이름으로 부르는가
- handoff 문서도 동일한 체계를 따르는가
- 과거 표기와 혼용되면 명시적 매핑이 있는가

반드시 보고할 것:
- 코드/로그/보고서/핸드오프의 상태명 표본
- 동일 상태에 서로 다른 이름이 쓰였는지 여부
- 혼용이 있으면 실제 운영 해석에 혼선이 있는지

판정 기준:
- 단일 enum 체계면 PASS
- 혼용되지만 매핑 설명이 있으면 CONDITIONAL
- 혼용되고 해석 혼선이 있으면 FAIL

### C. bridge_diag 실효성 검증
아래를 확인하라.

- `bridge_diag.bridge_mode` 값
- `bridge_diag.contrast_risk` 값
- 위 값이 실제 산문 품질과 일치하는가
- 문제가 있는 브릿지에서 실제로 WARNING/진단이 남는가
- 좋은 브릿지에서 과도한 false positive는 없는가

판정 기준:
- 진단과 실제 산문이 대체로 일치하면 PASS
- 일부 어긋나도 운영상 해석 가능하면 CONDITIONAL
- 진단과 실제가 자주 엇갈리면 FAIL

### D. continuity / overlap 유지 검증
16E 성과가 유지되는지 확인하라.

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

판정 기준:
- MEDIUM 이하 유지면 PASS 쪽
- HIGH 재상승이면 HOLD/FAIL 쪽

### E. temporal / quality non-regression
아래 회귀가 없는지 보라.

1. 완료 월 수치에 [전망] 오주입
2. 과거 사실 + 미래 전망 혼합
3. 미래 추정치를 현재 사실처럼 서술
4. 권유성 표현
5. 사실 / 해석 / 전망 경계 훼손
6. emergency_polish 관측 누락

---

## 정량 + 정성 판정 방식

### 1) 정량
- intro overlap ratio / status
- bridge_mode
- contrast_risk
- step3_status 일관성 여부
- emergency_polish 관측 여부

### 2) 정성
- Post2가 실제로 독립적인 종목 리포트처럼 읽히는가
- 브릿지가 종목 바스켓을 설득력 있게 묶는가
- status/diag 체계가 운영적으로 읽기 쉬운가
- 품질 보강 때문에 오히려 문장이 어색해지지 않았는가

---

## 최종 판정 규칙

### GO
- 브릿지-픽 정합성 문제 없음
- step3_status 체계 일관
- bridge_diag가 실제 품질과 잘 맞음
- intro_overlap MEDIUM 이하 유지
- temporal / quality 비회귀

### CONDITIONAL GO
- 핵심은 개선됐으나
- 일부 문구/표기/진단 해석에 경미한 보완 필요
- 운영상 다음 미세조정으로 충분히 해결 가능

### HOLD
- 브릿지가 여전히 픽 바스켓과 모순
- step3_status 혼용으로 운영 혼선 지속
- bridge_diag가 실출력과 잘 안 맞음
- overlap HIGH 재상승 또는 temporal 회귀 발생

---

## 출력 형식

반드시 아래 순서로 보고하라.

1. 작업 개요
2. 확보한 입력물 목록
3. Post1 / Post2 실출력 요약
4. 브릿지-픽 정합성 검증
5. step3_status 표준화 검증
6. bridge_diag 검증
7. intro overlap 정량 결과
8. shared 4-gram / 반복 표현 예시
9. emergency_polish / guard 관측 결과
10. temporal / quality 비회귀 여부
11. 최종 판정 (GO / CONDITIONAL GO / HOLD)
12. 남은 리스크
13. 필요 시 Phase 17 또는 후속 미세조정 제안

---

## 절대 금지

- 구현 요약만 보고 성공 판정
- 브릿지 문구가 있다고 해서 정합성 검증 생략
- step3_status 명칭을 대충 같은 뜻으로 간주
- overlap 수치 없이 “비슷하게 좋아짐” 식 추정
- temporal 비회귀를 확인하지 않고 continuity만 보고 GO 판정

최종 목표는
**“Phase 16F가 16E의 잔존 이슈를 실제 출력에서 해결했는지”**
실출력 기준으로 냉정하게 판정하는 것이다.
