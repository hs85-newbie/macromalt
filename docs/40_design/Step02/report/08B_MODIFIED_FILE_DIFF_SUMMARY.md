# 08B. Modified File Diff Summary (Step02)

Step02 (Global Shell & IA Refinement)를 위해 수정 및 생성된 파일 요약입니다.

## 1. File Modification Summary

| File | Purpose | Key Changes | Impact | Rollback |
|------|---------|-------------|--------|----------|
| `functions.php` | **[NEW]** structural hooks | `generate_after_header` 및 `generate_before_content` 훅 정의 | Hero/Breadcrumb 구조 생성 | EASY (삭제) |
| `style.css` | Global identity | 마스트헤드 레이아웃, 메뉴 모노타입, 전역 Rule line 정의 | 전체 쉘 시각 정체성 확립 | EASY (롤백) |
| `base.css` | Structural alignment | 모바일 헤더 높이 축소, 그리드 마진 조정 | 모바일 가독 환경 개선 | EASY |
| `typography.css` | IA Typography | `--font-mono` 스택 확정 및 메뉴/메타 적용 | 전문 미디어 IA 톤 조성 | EASY |
| `components.css` | Contextual UI | 카테고리 배지 및 섹션 레이블 스타일링 | 아카이브 탐색 직관성 향상 | EASY |

---

## 2. Key Differentiation Strategy
- **GP Hooks**: `header.php`를 덮어쓰지 않고 테마 훅을 사용하여 업데이트 안정성 극대화.
- **Conditional Layout**: `is_front_page()`를 통해 홈페이지 전용 히어로(Masthead)와 다른 페이지의 브레드크럼 레이어를 철저히 분리.
- **Step01 Safety**: 본문 폰트(`Georgia`) 및 픽 박스 등 Step01의 성과는 100% 보존.

---

## 3. Code Asset
- **Theme ZIP**: `wordpress_upload/macromalt-step02.zip`
