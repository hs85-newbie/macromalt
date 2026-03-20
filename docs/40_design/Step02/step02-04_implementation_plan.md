# 04. Implementation Plan (Step02 v2)

Step02의 구현은 **"GeneratePress Hooks"** 전략을 단일 추진 방식으로 확정하여 진행합니다.

## 1. Selected Method: Hooks Strategy (LOCKED)
- **Primary Hook**: `generate_after_header`를 사용하여 홈페이지 전용 마스트헤드 주입.
- **Secondary Hook**: `generate_before_content`를 사용하여 아카이브/포스트 브레드크럼 주입.

### Rejected Alternatives
- **`header.php` Override**: 테마 업데이트 시 유지 보수 리스크가 크고, 전체 레이아웃 안정성을 해칠 수 있어 배제함.
- **`front-page.php` Creation**: 정적 페이지만 제어하여 글로벌 헤더와의 정합성 유지가 어려운 구조적 한계로 배제함.

---

## 2. Phase-by-Phase Execution

### Phase 1: Structural Setup (Hooks)
1. **Child System Creation**: `theme/child-theme/functions.php` 파일을 생성하고 기본 훅 구조 선언.
2. **Masthead Injection**: `is_front_page()` 조건문을 사용하여 홈페이지 마스트헤드(Masthead) HTML 마크업 주입.
3. **Labels Application**: 확정된 `MACROMALT` 타이틀 및 `INSTITUTIONAL RESEARCH...` 태그라인 적용.

### Phase 2: Shell Refinement (Visual)
1. **Desktop IA Style**: 내비게이션 메뉴에 Mono-type 타이포그래피 및 Rule lines 적용.
2. **Mobile Layout**: 헤더 간격 축소 및 햄버거 메뉴 가독 영역 개선.
3. **Archive Layer**: 카테고리 진입 시 Identity 구분을 위한 스타일 레이어 활성화.

### Phase 3: Technical Verification
1. **Site-wide Consistency**: 홈, 아카이브, 개별 기사(Single) 간의 시각적 위계 점검.
2. **Scope Validation**: 홈페이지 전용 마스트헤드가 다른 페이지(Archive/Single)에 노출되지 않는지 Matrix 검증.
3. **Regression Proof**: Step01의 기사 읽기 품질이 100% 유지되는지 전수 검사.

---

## 3. Deployment Flow
- 모든 소스 코드는 로컬 작업 후 `wordpress_upload/macromalt-step02.zip`으로 패키징하여 관리자 페이지를 통해 배포합니다.
