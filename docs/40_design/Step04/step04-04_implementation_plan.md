# step04-04. Implementation Plan (Step04 v3)

## 1. Style-Only Strategy: "Atmospheric Determinism"
본 단계는 **오직 WordPress 프론트엔드 스타일**에만 집중합니다. `generator.py` 등 백엔드 로직은 이번 작업 범위에서 완전히 배제됩니다.

## 2. Implementation Steps

### Phase 1: Monthly Determinism (functions.php)
서버 시간이 아닌, 워드프레스 관리자 설정의 **사이트 시간(Local Timezone)**을 기준으로 정확한 박자(Midnight)에 계절이 교체되도록 구현합니다.
- **Hook**: `body_class` 필터.
- **Logic**: `strtolower( current_time( 'M' ) )`을 사용하여 사이트 현지 시간 기준 월(jan, feb...)을 추출.
- **Class Naming**: `mm-season-[month]` (예: `mm-season-mar`).

### Phase 2: Token Foundation (base.css)
- 전역 색상 변수(`:root`)를 정의하여 Step03의 정규 상태를 기본값으로 설정합니다.

### Phase 3: Seasonal Overrides (seasonal.css)
- 12개의 월별 클래스에 대해 변수 오버라이드 세트를 정의합니다.
- **Variable Set**: `--mm-bg`, `--mm-bg-alt`, `--mm-ink-soft`, `--mm-rule`, `--mm-badge-bg`, `--mm-badge-text`, `--mm-accent`.

### Phase 4: Integration (style.css)
- `style.css`에서 `seasonal.css`를 최하단에 임포트하여 우선순위를 확보합니다.

## 3. Automation Rule (Presentation)
```php
add_filter( 'body_class', function( $classes ) {
    // WordPress 로컬 타임존 기반 월 식별 (Deterministic)
    $month = strtolower( current_time( 'M' ) ); // 'jan', 'feb' 등 3자 영문
    $classes[] = 'mm-season-' . $month;
    return $classes;
});
```

## 4. Verification & Reporting
- **08F_SEASONAL_SWITCH_PROOF.md**: `functions.php`의 로직을 일시적으로 수정(예: `jan` 강제 주입)하여 최소 3개 월(Mar, Jul, Nov)의 시각적 차이를 캡처하고 증명합니다.
- **Regression Check**: 가독성 및 Step01-03 보호 자산의 안정성을 확인하며, `--mm-accent`를 통합 사용하여 호버 및 강조 스타일을 일원화합니다.
