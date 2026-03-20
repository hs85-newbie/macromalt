# step04-07. QA CHECKLIST (Step04)

## 1. Automation Verification
- [ ] 현재 월에 맞는 클래스가 `<body>`에 자동으로 주입되는가?
- [ ] 주입된 클래스에 따라 배경색(`--mm-bg`)이 의도한 대로 변하는가?
- [ ] 수동 시뮬레이션 시 12개 월의 모든 변수가 정상 작동하는가?

## 2. Visual Regression Check
- [ ] **Step01**: 한글/영문 본문 가독성이 보장되는가?
- [ ] **Step02**: 홈페이지 히로 쉘의 브랜드 컬러가 계절 배경과 충돌하지 않는가?
- [ ] **Step03**: 고지 박스(Disclosure) 내부 텍스트가 모든 계절에서 100% 읽히는가?

## 4. Mandatory Deliverables
- [ ] **08F_SEASONAL_SWITCH_PROOF.md** 제출 완료:
    - [ ] `functions.php` 수동 시뮬레이션을 통한 최소 3개 월(Mar, Jul, Nov) 렌더링 증명.
    - [ ] 각 월별 변수(Accent, Badge, Background)의 시각적 차이 캡처 포함.
    - [ ] 현재 라이브 시점(Live Month)의 자동 반영 최종 확인.
