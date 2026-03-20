# 07. QA CHECKLIST (Step02 v2)

Step02 최종 승인을 위한 검증 체크리스트입니다.

## 1. Editorial Branding & Copy (LOCKED)
- [ ] **Hero Title**: `MACROMALT`가 홈페이지 최상단에 정확히 위치하는가?
- [ ] **Hero Tagline**: `INSTITUTIONAL RESEARCH FOR THE GLOBAL MACRO`가 누락 없이 적용되었는가?
- [ ] **Section Headings**: `STRATEGIC BRIEFINGS`, `MARKET INTELLIGENCE`, `MALT PICKS` 섹션명이 일치하는가?
- [ ] **Mono Font Stack**: 내비게이션 및 메타데이터에 지정된 `SFMono / ui-monospace` 계열이 사용되는가?

## 2. Structural & IA Matrix
- [ ] **Homepage-Only**: 마스트헤드 히어로가 홈페이지에서만 노출되고 다른 페이지(Single/Archive)에서는 숨겨지는가?
- [ ] **Archive Identity**: 카테고리 페이지 상단에 `CATEGORY: [Name]` 배지가 정상 노출되는가?
- [ ] **Navigation Utility**: 데스크탑 메뉴가 가로 1열로 정렬되어 있는가?
- [ ] **Mobile Compact**: 모바일 헤더 높이가 축소되어 콘텐츠 가시 영역이 늘어났는가?

## 3. Operator Final-State Verification
- [ ] **Menu Tree**: [Home / Analysis / Picks / Archive / About] 순서로 메뉴가 구성되었는가?
- [ ] **Tagline Context**: WP-Admin > 설정 > 일반의 태그라인과 히어로 태그라인이 정합성을 이루는가?
- [ ] **Favicon Status**: Step01에서 제공된 아이콘이 최종 반영되어 있는가?
- [ ] **Breadcrumb Activation**: 카테고리/포스트 상단에 경로(Breadcrumb)가 활성화되어 있는가?

## 4. Safety & Regression
- [ ] **Step01 Safety**: 단일 포스트의 글꼴(Georgia), 행간, 배경색이 변함없는가?
- [ ] **Pipe Safety**: `generator.py` 및 `styles/tokens.py` 파일이 수정되지 않았음을 `git status`로 확인했는가?
- [ ] **Rollback Ready**: 문제가 발생할 경우 `functions.php` 삭제만으로 즉시 복구가 가능한가?
