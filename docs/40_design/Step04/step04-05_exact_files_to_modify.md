# step04-05. Exact Files to Modify (Step04 v3)

## 1. WordPress Presentation Track
- [MODIFY] `theme/child-theme/functions.php`: **WP-timezone** 기반 `mm-season-` 클래스 주입.
- [MODIFY] `theme/child-theme/style.css`: 테마 버전 1.5.0 업데이트 및 seasonal 임포트.
- [MODIFY] `styles/wordpress/base.css`: 전역 CSS 변수(:root) 기본값 정의.
- [NEW] `styles/wordpress/seasonal.css`: 12개월 프리셋 변수 집합.

## 2. Non-Style Exclusion (LOCKED)
- **NO CHANGE**: `generator.py`, `publisher.py`, `scraper.py`.
- **NO CHANGE**: 모든 백엔드 로깅 및 감사 로직.
- **NO CHANGE**: WordPress DB 스키마.
