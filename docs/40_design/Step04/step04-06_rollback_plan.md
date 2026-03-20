# step04-06. Rollback Plan (Step04)

## 1. Technical Reversion
계절 레이어에 문제가 발생할 경우 다음을 수행합니다.

### Step 1: Logic Removal
`functions.php`에서 `add_filter( 'body_class', ... )` 관련 블록을 삭제하거나 주석 처리합니다.
- **Effect**: `<body>`에 계절 클래스가 붙지 않게 되어 모든 스타일이 Default로 복구됨.

### Step 2: CSS Import Removal
`style.css`에서 `@import url("styles/seasonal.css");`를 제거합니다.

## 2. Recovery Time Objective (RTO)
- **Time**: 2분 이내.
- **Impact**: Step03의 최종 상태(Default Institutional Style)로 즉시 복구됩니다.
