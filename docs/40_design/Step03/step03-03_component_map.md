# step03-03. Component Map (Step03)

Step03의 구성 요소를 구현 방식별로 최종 분류합니다.

## 1. Hook / Template Layer (Deterministic Injection)
- [ ] **Disclosure Box**: 오직 `single` 포스트 상단에만 `DISCLOSURE & METHODOLOGY` 박스가 정상 노출되는가?
- [ ] **Disclosure Exclusion Scope**: Home, About, Category, Archive, Search, Static Pages에서 고지 박스가 **제외**되었는지 확인했는가?
  - **Logic**: `is_single() && !is_page()` 조건부 실행.
  - **Content**: Locked Disclosure Body Copy 주입.
- **Search Header (NEW)**:
  - **Hook**: `generate_before_main_content`
  - **Logic**: `is_search()` 시에만 `SEARCHING THE MACROMALT ARCHIVE:` 레이블 노출.
- **Footer Trust Append (NEW)**:
  - **Hook**: `generate_after_footer_content`
  - **Content**: Locked Footer Copyright 문구 주입.

## 2. CSS-Only Layer (Styling Only)
- **Entry Meta**: `.entry-meta` 섹션의 글꼴을 Mono-type으로 변경.
- **Read More**: `.read-more` 링크를 `FULL ANALYSIS →` 스타일로 텍스트 치환 및 디자인.
- **Search/Archive Result Items**: 목록 간격 및 메타데이터 밀도 조정.
- **Pagination**: 워드프레스 기본 페이지네이션의 시각적 장식 제거.

## 3. Operator Configuration Layer (Initial Setup)
- **About Page Transition**: 
  - "Sample Page"의 고유 ID(Slug)를 `about`으로 변경.
  - 확정된 5단계 섹션 스켈레톤 카피 주입.
- **Widget Purge**: 사이드바의 기본 검색창 외 불필요한 위젯 삭제 가이드.

---

## 4. Implementation Method Consistency
모든 구조적 개입은 **GeneratePress Hooks**를 최우선으로 하며, 템플릿 파일(`archive.php`, `search.php` 등)의 직접적인 오버라이드는 지양합니다.
