# step04-03. Component Map (Step04 v3)

## 1. Class-to-Month Mapping (WP Timezone Source)
`functions.php`에서 생성되는 결정론적 클래스 명세입니다.

| Source (`current_time('M')`) | Body Class | Logic Provider |
|------------------------------|------------|----------------|
| Jan | `mm-season-jan` | WordPress Local Time |
| Feb | `mm-season-feb` | WordPress Local Time |
| ... | ... | ... |
| Dec | `mm-season-dec` | WordPress Local Time |

## 2. Refinement Targets
계절 변수가 주입되는 구체적인 컴포넌트 라이브러리입니다.

- **Backgrounds**: `body`, `.site-content`, `.inside-article`.
- **Containers**: `.article-card`, `.sidebar-box`.
- **Rules/Lines**: `hr`, `.entry-footer`, `.entry-meta`.
- **Interactive**: `a:hover`, `.read-more` 등의 강조 요소 (`--mm-accent`).
- **Trust Elements**: `.mm-disclosure-box` (내부 가독성 보호 필수).

## 3. Excluded Elements (Locked Shell)
- **Primary Branding**: 로고 이미지 및 타이포그래피 웨이트.
- **Core Reading Area**: 본문 글자색 및 기본 행간.
- **Footer Structure**: 신뢰 푸터의 물리적 레이아웃.
