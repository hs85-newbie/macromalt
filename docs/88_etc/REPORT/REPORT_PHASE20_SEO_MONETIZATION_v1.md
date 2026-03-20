# REPORT_PHASE20_SEO_MONETIZATION_v1

- 작성일: 2026-03-20
- Phase: 20 — Technical SEO Baseline + Monetization Architecture
- 상태: IMPLEMENTED (Section 5 완전 구현 / Section 6 Scaffold)
- SSOT: `docs/50_SEO/MACROMALT_SEO_MONETIZATION_SSOT_v1.md`

---

## 1. Current-State Audit 결과

### 변경 전 상태

| 항목 | 상태 |
|------|------|
| meta description | ✗ 없음 |
| canonical | ✗ 없음 |
| Open Graph | ✗ 없음 |
| Twitter Card | ✗ 없음 |
| Schema (Article/Org/Breadcrumb) | ✗ 없음 |
| robots noindex (thin pages) | ✗ 없음 |
| sitemap tag 제외 | ✗ 없음 |
| robots.txt sitemap 포인터 | ✗ 없음 |
| AdSense 코드 | ✗ 없음 |
| Ad container CSS | ✗ 없음 |

### 파악된 구조

- **Parent theme**: GeneratePress
- **Child theme**: macromalt-child (Step04 기준)
- **CSS 모듈 구조**: base / typography / components / seasonal (→ seo-ads 추가됨)
- **SEO 플러그인**: 없음 — 전부 theme-level hooks로 처리
- **Template override 없음**: GeneratePress 기본 템플릿 사용 + functions.php hook 방식

---

## 2. 변경된 파일 목록

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `theme/child-theme/functions.php` | 수정 | Section 5 (SEO) + Section 6 (Ad scaffold) 추가 |
| `theme/child-theme/style.css` | 수정 | `@import url("styles/seo-ads.css")` 추가 |
| `styles/wordpress/seo-ads.css` | 신규 생성 | Ad container CSS (CLS 보호 포함) |
| `wordpress_upload/macromalt-child/functions.php` | 수정 | 동일한 SEO + Ad scaffold 추가 |
| `wordpress_upload/macromalt-child/style.css` | 수정 | `@import url("styles/seo-ads.css")` 추가 |
| `wordpress_upload/macromalt-child/styles/seo-ads.css` | 신규 생성 | 배포 패키지용 동일 CSS |

---

## 3. 구현 상세

### Section 5: Technical SEO Baseline

#### 5.1 robots meta (noindex for thin pages)
- `wp_head` priority 1에서 실행
- `is_search()`, `is_date()`, `is_tag()` → `noindex, follow` 주입
- 카테고리, 싱글 포스트, 홈: 기본값(index) 유지

#### 5.2 Canonical URL 주입
- 싱글 포스트: `get_permalink()`
- 카테고리: `get_category_link()`
- 홈: `home_url('/')`
- 페이지네이션: `get_pagenum_link()`
- absolute URL 사용 (SSOT 7-2 기준 준수)

#### 5.3 Meta description 주입
- 우선순위: post excerpt → content excerpt (25단어) → 페이지타입별 기본문
- 최대 160자로 절단 (`mb_substr`)
- 홈 고정 설명: 한국어 브랜드 설명 + 기관 리서치 방향
- 카테고리: category_description() 또는 카테고리명 + Macromalt 서픽스

#### 5.4 Open Graph + Twitter Card
- `og:site_name`, `og:type`, `og:title`, `og:url`, `og:description`, `og:image`
- Twitter Card: 이미지 있으면 `summary_large_image`, 없으면 `summary`
- article 타입: 싱글 포스트에만 적용
- 이미지: `has_post_thumbnail()` 조건부 주입

#### 5.5 Schema.org JSON-LD
- **Organization**: 전 페이지 공통 (name, url, description)
- **WebSite**: 홈 페이지에만 추가
- **Article**: 싱글 포스트 (headline, description, datePublished, dateModified, author, publisher, mainEntityOfPage, image 조건부)
- **BreadcrumbList**: 싱글 포스트 (Home → Category → Post 3단계, 카테고리 없으면 2단계)
- `JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES` 플래그로 한국어 인코딩 보존

#### 5.6 Sitemap 정책
- `wp_sitemaps_taxonomies` 필터로 `post_tag` 제외
- WordPress 네이티브 sitemap (`/wp-sitemap.xml`) 유지

#### 5.7 robots.txt 추가
- `robots_txt` 필터로 아래 항목 추가:
  - `Disallow: /?s=` (검색 페이지 크롤 차단)
  - `Disallow: /search/`
  - `Sitemap:` URL 포인터 (`/wp-sitemap.xml`)

---

### Section 6: Monetization Architecture (Scaffold / INACTIVE)

#### 상태
- `MACROMALT_ADSENSE_ACTIVE = false` — 코드는 전부 설치되어 있으나 **실행 비활성**
- `true`로 전환하면 즉시 작동하는 구조

#### 6.1 AdSense 스크립트 로더
- `MACROMALT_ADSENSE_ACTIVE` + `MACROMALT_ADSENSE_PUBLISHER_ID` 두 조건 모두 충족 시 로드
- **자동 제외 페이지**: about, privacy-policy, terms, advertising-policy, disclosure, 저자 아카이브
- 홈 / 카테고리 / 아카이브는 스크립트 로드 허용 (표시 여부는 별도 슬롯으로 제어)

#### 6.2 Mid-article 슬롯
- `the_content` 필터, priority 20
- 단락 수 > 6인 경우만 삽입 (짧은 글 보호)
- 삽입 위치: 4번째 `</p>` 이후 (H1 + 첫 2~3문단 보호)
- CSS class: `mm-ad-slot mm-ad-mid`
- `aria-label="Advertisement"` 접근성 속성

#### 6.3 End-of-article 슬롯
- `generate_after_entry_content` 훅, priority 10
- 본문 종료 직후, 관련 글 블록 이전
- CSS class: `mm-ad-slot mm-ad-end`

#### 6.4 ads.txt 안내
- **서버 루트에 직접 배포 필요** (테마 파일이 아님)
- 템플릿: `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`
- 배포 경로: `/public_html/ads.txt` (또는 WordPress 루트)

---

### seo-ads.css 구조

| 클래스 | 역할 | CLS min-height |
|--------|------|----------------|
| `.mm-ad-slot` | 기본 컨테이너 (공통) | 90px |
| `.mm-ad-mid` | 본문 중단 슬롯 | 100px |
| `.mm-ad-end` | 글 하단 슬롯 | 90px |
| `.mm-ad-label` | "ADVERTISEMENT" 표시 레이블 | — |

- 모바일(≤768px): min-height 60px으로 축소
- disclosure box 인접 금지 CSS guard 포함

---

## 4. QA 체크리스트

### 즉시 검증 가능 (테마 업로드 후)

- [ ] 싱글 포스트 `<head>` → `<meta name="description">` 존재 확인
- [ ] 싱글 포스트 `<head>` → `<link rel="canonical">` absolute URL 확인
- [ ] 싱글 포스트 `<head>` → `og:title`, `og:type=article` 확인
- [ ] 싱글 포스트 `<head>` → `<script type="application/ld+json">` Article 스키마 확인
- [ ] 홈 `<head>` → Organization + WebSite 스키마 확인
- [ ] 검색 페이지 `<head>` → `<meta name="robots" content="noindex, follow">` 확인
- [ ] 날짜 아카이브 `<head>` → noindex 확인
- [ ] 태그 아카이브 `<head>` → noindex 확인
- [ ] `/robots.txt` → `Disallow: /?s=`, `Sitemap:` 포인터 확인
- [ ] `/wp-sitemap.xml` → post_tag taxonomy 제외 확인

### Google Search Console / Rich Results Test (배포 후)

- [ ] Search Console → URL 검사 → Article 구조화 데이터 인식
- [ ] Rich Results Test → BreadcrumbList 인식
- [ ] Coverage report → noindex 페이지 excluded 분류 확인

### AdSense 활성화 전 체크리스트

- [ ] AdSense 계정 생성 및 사이트 제출
- [ ] 사이트 승인 후 `pub-XXXXXXXX` ID 확보
- [ ] `functions.php` → `MACROMALT_ADSENSE_PUBLISHER_ID` 상수 설정
- [ ] `MACROMALT_ADSENSE_ACTIVE` → `true` 전환
- [ ] ads.txt 서버 루트 배포
- [ ] 모바일/데스크톱에서 ad slot CLS 측정 (PageSpeed Insights)
- [ ] 광고가 navigation처럼 오인될 위치 없는지 수동 확인

---

## 5. 롤백 계획

### 즉시 롤백 기준 (SSOT §13 기준)

1. canonical/robots/sitemap 충돌로 인덱싱 리스크
2. H1 ~ 첫 2문단 가독성 저하
3. source block 파손
4. 광고가 메뉴/네비처럼 보임
5. Core Web Vitals 급격 악화
6. mobile readability 저하

### 롤백 방법

**SEO 레이어 전체 비활성화:**
```php
// functions.php Section 5 전체를 아래로 래핑
if ( defined( 'MACROMALT_SEO_ACTIVE' ) && MACROMALT_SEO_ACTIVE ) {
    // ... Section 5 코드 전체
}
// 비활성화: define( 'MACROMALT_SEO_ACTIVE', false );
```

**Ad 레이어 즉시 비활성화:**
```php
// 이미 MACROMALT_ADSENSE_ACTIVE = false로 설정됨
// 롤백 필요 없음 — 기본값이 비활성
```

**CSS 롤백:**
- `style.css`에서 `@import url("styles/seo-ads.css")` 라인 삭제

---

## 6. 리스크 및 미해결 항목

### 즉시 주의

| 항목 | 설명 | 대응 |
|------|------|------|
| GeneratePress 중복 canonical | GP가 canonical을 이미 출력하는 경우 중복 가능 | Search Console에서 `<link rel=canonical>` 복수 여부 확인 |
| GeneratePress 중복 meta description | GP 설정에 description 필드가 있으면 중복 가능 | 확인 후 GP 측 비활성화 또는 WordPress SEO 기본 메타 비활성화 |
| excerpt 없는 포스트 description 품질 | LLM 생성 포스트는 excerpt 없을 수 있음 → content 앞부분 25단어 | 발행 파이프라인에서 excerpt 자동 설정 권장 |

### 후속 구현 (Phase 20 2차)

1. **about/editorial identity 페이지 정비** — author page, editorial policy 페이지 생성 (WordPress Admin에서 직접)
2. **ads.txt 서버 루트 배포** — AdSense 신청과 함께 진행
3. **category/tag taxonomy 정책 정리** — 현재 운용 중인 카테고리/태그 감사 후 thin archive 제거
4. **AdSense 계정 신청 및 승인 대기**
5. **Search Console 사이트 등록 및 sitemap 제출**

### SSOT 비침범 확인

- [x] article generation logic — 변경 없음
- [x] temporal SSOT — 변경 없음
- [x] verifier/reviser core — 변경 없음
- [x] publishing gates — 변경 없음
- [x] slot policy — 변경 없음
- [x] content quality policy — 변경 없음
- [x] Phase 19 quality logging — 변경 없음

---

## 7. 다음 Phase 20 액션 (우선순위 순)

1. WordPress에 업데이트된 child theme 업로드 (`wordpress_upload/macromalt-child/`)
2. Search Console 사이트 등록 → sitemap 제출 (`/wp-sitemap.xml`)
3. Rich Results Test로 Article / BreadcrumbList 스키마 검증
4. About 페이지 / Author 페이지 WordPress Admin에서 정비
5. AdSense 사이트 신청
6. ads.txt 서버 배포 (AdSense 승인 후)
7. `MACROMALT_ADSENSE_ACTIVE = true` 전환 + CWV 측정

---

*Phase 19 비회귀 확인: 발행 파이프라인(generator.py, main.py, publisher.py) 변경 없음.*
*GitHub Actions 스케줄 유지.*
