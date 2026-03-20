# 03. Component Map (Step02 v2)

본 문서는 Step02의 구현 전략과 페이지별 노출 범위를 확정합니다.

## 1. Primary Structural Strategy (LOCKED)

- **Selected Method**: **GeneratePress Hooks (via `functions.php`)**
- **Rationale**: 
  - `generatepress` 테마의 공식 확장 방식을 사용하여 업데이트 안정성을 확보합니다.
  - `header.php` 전체 오버라이드보다 코드량이 적고 리스크가 낮습니다.
  - `front-page.php` 방식보다 글로벌 헤더와의 유기적 연결이 용이합니다.

### Rejected Methods & Why
- `header.php` Override: 테마 코어 구조가 변경될 경우 유지보수가 어렵고 버그 유발 가능성이 높음.
- `front-page.php` Only: 홈페이지 전용 레이아웃에는 강하나, 글로벌 헤더와의 정합성 및 다른 보조 페이지 연계가 복잡함.

---

## 2. Page-Scope Matrix (LOCKED)

각 요소가 어느 페이지 레이어에 노출되는지 정의합니다.

| Component | Global | Home Only | Archive Only | Single Only |
|-----------|:------:|:---------:|:------------:|:-----------:|
| **Navigation Menu** (Primary) | [x] | | | |
| **Site Branding (Logo)** | [x] | | | |
| **Editorial Hero (Masthead)** | | [x] | | |
| **Strategic Tagline** | | [x] | | |
| **Category Badge Header** | | | [x] | |
| **Breadcrumb Navigation** | | | [x] | [x] |
| **Footer (Editorial Version)** | [x] | | | |

---

## 3. Component Classification (Redefined)

| Component | Layer | Description |
|-----------|-------|-------------|
| **Masthead Injection** | **Template** | `generate_after_header` 훅을 이용한 히어로 섹션 삽입 |
| **IA Menu Labels** | **Operator** | `HOME`, `ANALYSIS`, `PICKS`, `ARCHIVE`, `ABOUT` 구성 |
| **Typography Shell** | **CSS** | 전역 헤더 및 메뉴에 Mono-type 적용 |
| **Compact Mobile View** | **CSS** | `generate_header_mobile_menu_logo` 등 전용 선택자 제어 |
| **Breadcrumb Layout** | **Template** | `generate_before_content` 훅을 통한 계층 구조 노출 |
