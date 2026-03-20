# 05. Exact Files to Modify (Step02 v2)

Step02 구현을 위한 소스 파일 목록과 배포 아티팩트를 구분하여 정의합니다.

## 1. Source Files (To Modify / Create)

| File Path | Action | Purpose |
|-----------|:------:|---------|
| `theme/child-theme/functions.php` | **CREATE** | GP Hooks (Hero/Breadcrumb) 주입 로직 |
| `theme/child-theme/style.css` | **MODIFY** | Global shell, Header/Footer rule lines |
| `styles/wordpress/base.css` | **MODIFY** | Mobile header, Hero layouts |
| `styles/wordpress/typography.css` | **MODIFY** | Menu Mono-type typography |
| `styles/wordpress/components.css` | **MODIFY** | Archive/Category badge UI |

## 2. Child-Theme Overrides (NEW)

| File | Purpose | Impact Area | Rollback Ease |
|------|---------|-------------|---------------|
| `theme/child-theme/functions.php` | Template hooks entry point | Hero/Breadcrumb injection logic | MODERATE |

## 3. Delivery Artifacts (Output)

실행 완료 후 배포용으로 제공되는 결과물입니다.

| Artifact Path | Description |
|---------------|-------------|
| `wordpress_upload/macromalt-step02.zip` | Step02 전체 테마 패키지 (Functions + CSS) |
| `wordpress_upload/step02_verification/` | 최종 검토용 스크린샷 및 검증 보고서 |

---

## 4. Scope Safety Rules
- **Non-Style Files**: `generator.py`, `publisher.py`, `styles/tokens.py`는 수정 범위에서 엄격히 제외됩니다.
- **Dependency**: `functions.php`는 `is_front_page()` 등 테마 기본 함수만을 사용하여 코어 의존성을 최소화합니다.
