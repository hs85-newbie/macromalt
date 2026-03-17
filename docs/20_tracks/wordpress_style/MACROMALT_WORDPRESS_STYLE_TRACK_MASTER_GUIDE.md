# MACROMALT_WORDPRESS_STYLE_TRACK_MASTER_GUIDE.md

이 문서는 **Macromalt WordPress 스타일 트랙 전용 마스터 가이드**입니다.  
목적은 다음과 같습니다.

1. **콘텐츠 품질 파이프라인**과 **WordPress 스타일/UI 작업**을 완전히 분리
2. Claude Code, Antigravity, Codex 각각에 어떤 식으로 지시해야 하는지 정리
3. WordPress 스타일 트랙에서 바로 사용할 수 있는 **실전 프롬프트 세트** 제공
4. 향후 스타일 작업을 **안정적, 롤백 가능, 프론트 전용 수정 가능 구조**로 운영

---

# 1. 분리 원칙

Macromalt 프로젝트는 앞으로 아래 두 트랙을 **명확히 분리**해서 운영한다.

## 트랙 A — 콘텐츠 품질 / 생성 파이프라인
담당:
- Claude Code
- 본문 생성/검증 파이프라인 담당 에이전트

범위:
- 기사 생성
- 해석 품질
- 시제 일관성
- `[전망]` 태그 오용 방지
- Post1/Post2 연결
- 검증/게이트 로직
- 발행 파이프라인 로직

## 트랙 B — WordPress 스타일 / 표현 레이어
담당:
- Antigravity
- Codex
- 프론트/UI 전용 에이전트

범위:
- WordPress 테마/차일드테마
- HTML 템플릿
- CSS 스타일
- 단일 포스트 페이지
- 아카이브/리스트 페이지
- 시각적 계층 구조
- 배지/콜아웃/소스 블록 스타일
- 모바일 반응형
- 독자-facing 시각적 UX

---

# 2. 워드프레스 스타일 트랙의 핵심 원칙

## 반드시 지켜야 할 것
- 스타일 작업은 **콘텐츠 생성 로직과 분리**
- Python 로직은 데이터/발행 흐름 담당
- HTML 템플릿은 구조 담당
- CSS는 스타일 담당
- Antigravity / Codex는 **HTML/CSS만 수정** 가능하게 설계

## 건드리면 안 되는 것
- 기사 생성 프롬프트
- 시제/사실성 검증 로직
- LLM 파이프라인
- 발행 게이트
- Python 품질 규칙
- 게시 로직 자체

---

# 3. 권장 구조

## Python
역할:
- 데이터 준비
- article data normalization
- 발행 흐름
- 템플릿에 값 주입

## HTML Templates
역할:
- 기사 마크업 구조
- section wrapper
- source block
- label block
- archive card structure

## CSS
역할:
- 타이포그래피
- 여백
- 색상
- 배지
- callout
- blockquote
- source/citation visual styling
- responsive layout

---

# 4. 추천 파일 구조

예시:

```text
templates/
  post_layout.html
  post_section.html
  source_block.html
  tag_badge.html
  archive_card.html

styles/
  macromalt_post.css
  macromalt_labels.css
  macromalt_archive.css
  macromalt_mobile.css
```

실제 프로젝트 구조에 맞게 경로명은 조정할 수 있으나,  
원칙은 다음과 같다.

- Python은 **HTML/CSS 문자열을 직접 많이 들고 있지 않는다**
- 마크업은 template 파일로 분리
- 스타일은 CSS 파일로 분리
- 프론트 스타일 담당 에이전트는 이 폴더만 수정해도 대부분 작업이 가능해야 한다

---

# 5. 왜 이 분리가 필요한가

현재 스타일/마크업이 `main.py`, `publisher.py` 등에 섞여 있으면:

- 스타일 수정이 곧 발행 로직 수정이 됨
- 롤백이 어려움
- 프론트 전용 작업과 콘텐츠 파이프라인 작업이 충돌
- Antigravity/Codex가 안전하게 작업하기 어려움
- CSS/HTML 실험이 매번 Python 코드 수정으로 연결됨

따라서 **스타일 작업은 CSS/HTML로 분기해서 관리**하는 것이 가장 안정적이다.

---

# 6. 디자인 목표

WordPress 스타일 트랙의 목표 미감은 다음과 같다.

- premium financial editorial
- restrained luxury
- calm and intelligent
- high readability first
- dense but breathable
- elegant, not flashy
- not a generic news portal
- not a noisy startup blog
- not a retail trading app feel
- subtle whisky-bar/private-brief mood is allowed
- typography-first
- mobile readability is mandatory

---

# 7. Antigravity / Codex에 공통으로 줄 마스터 지시문

```text
You are working on a WordPress presentation/styling track that is fully separate from the article generation pipeline.

Important separation rule:
- Do NOT modify article generation logic, LLM prompts, verification rules, or publishing pipeline behavior.
- Your scope is only WordPress presentation, rendering, layout, theme-level styling, template behavior, and reader-facing visual UX.

Project context:
- Brand: Macromalt
- Tone: premium macro/investment briefing
- Reader expectation: high-end financial editorial product, not a generic blog
- The site should feel elegant, calm, information-dense, premium, and readable on both desktop and mobile.

Your job:
Design and implement the WordPress styling layer only.
```

---

# 8. 작업 범위 고정 지시문

```text
Scope in:
- single post layout
- post typography
- headings, paragraphs, spacing
- callout blocks
- quote blocks
- source/citation styling
- tag chips such as [해석], [전망], [반론], [심층분석], [캐시의 픽]
- mobile responsiveness
- list/archive card layout
- category/series visual identity
- reusable CSS / theme overrides / child-theme modifications
- template parts if needed

Scope out:
- article text rewriting
- temporal/factual verification logic
- LLM prompts
- generation pipeline
- publishing workflow
- analytics logic unless explicitly requested
```

---

# 9. 디자인 의도 설명문

```text
Design intent:
- premium financial editorial, not flashy media
- restrained luxury, not loud luxury
- high readability first
- strong hierarchy, calm spacing, dense but breathable
- elegant contrast
- subtle whisky-bar / private-briefing mood is allowed
- avoid gimmicky animations and startup-style gradients
- avoid generic magazine clutter
- avoid “crypto-bro” or “news portal” visual language
```

---

# 10. 실전 프롬프트 템플릿

## 10.1 전체 스타일 시스템 설계용

```text
Design a WordPress styling system for Macromalt.

Goal:
Create a premium editorial visual system for:
- single article pages
- archive/list pages
- tag/series/category indicators
- reader-facing analytical labels such as [해석], [전망], [반론]

Requirements:
- desktop + mobile responsive
- typography-first design
- calm premium financial feel
- excellent readability for long-form analysis
- reusable styling rules, not page-by-page hacks
- minimize plugin dependency
- prefer child-theme safe implementation
- provide implementation in a rollback-friendly way

Deliverables:
1. visual design principles
2. component inventory
3. implementation plan
4. exact files to change
5. CSS / template strategy
6. risk notes
7. rollback plan

Important:
Do not touch content-generation logic.
Only work on WordPress rendering/presentation.
```

---

## 10.2 단일 포스트 페이지 개선용

```text
Improve the single-post reading experience for Macromalt WordPress articles.

Primary goals:
- make long-form articles feel premium and highly readable
- visually distinguish analytical labels like [해석], [전망], [반론]
- improve spacing, hierarchy, and information density
- maintain calm financial-editorial tone

Focus areas:
- article width
- font sizing and line-height
- heading hierarchy
- paragraph spacing
- blockquote / callout styling
- inline source styling
- analytical tag badge styling
- related article / next article presentation
- sticky or floating table of contents only if it improves reading

Avoid:
- noisy motion
- heavy JS
- overdecorated cards
- anything that makes the page feel like a mass news portal

Return:
- style rationale
- exact WordPress implementation steps
- code changes
- screenshots or preview instructions if available
```

---

## 10.3 `[해석]`, `[전망]`, `[반론]` 배지 스타일 전용

```text
Create a visual styling system for reader-facing analytical labels used inside Macromalt articles.

Labels include:
- [해석]
- [전망]
- [반론]
- [심층분석]
- [캐시의 픽]

Requirements:
- easy to scan
- premium and understated
- visually distinct but not childish
- should support inline usage inside paragraphs and heading-adjacent usage
- mobile-safe
- consistent with a high-end financial brief

Deliver:
- styling rules for each label
- accessibility/readability considerations
- CSS implementation
- any minimal template adjustment if necessary
```

---

## 10.4 워드프레스 실제 구현 지시용

```text
Implement the styling changes in a rollback-safe WordPress manner.

Implementation requirements:
- prefer child theme changes
- avoid editing parent theme directly unless unavoidable
- clearly separate:
  - CSS
  - template changes
  - functions.php hooks
- every change must be documented
- provide exact file diff targets
- provide rollback instructions
- keep plugin dependency minimal
- no content-generation logic changes

Before implementation:
- inspect current theme structure
- identify safe override points
- propose the least invasive implementation path

After implementation:
- provide changed file list
- provide summary of visual impact
- provide test checklist for desktop/mobile
```

---

# 11. Antigravity용 프롬프트 스타일

Antigravity는 설계 → 구현 → 운영 자동화 흐름에 강하므로 아래처럼 지시하는 것이 좋다.

```text
Act as a WordPress front-end styling engineer.

Task:
Create a premium editorial styling upgrade for Macromalt.

Constraints:
- separate from article-generation pipeline
- rollback-safe
- child-theme preferred
- minimal plugin reliance
- provide implementation in phases:
  1. audit current theme
  2. propose component styling map
  3. implement safe overrides
  4. provide QA checklist
```

권장 포맷:
- audit
- component map
- implementation plan
- changed files
- QA checklist
- rollback plan

---

# 12. Codex용 프롬프트 스타일

Codex는 파일 단위 구현에 더 직접적이므로 아래처럼 지시하는 것이 좋다.

```text
You are modifying only the WordPress presentation layer.

Do not touch:
- Python generation pipeline
- LLM prompts
- article verification logic
- publishing automation

Touch only:
- WordPress theme/child-theme files
- CSS
- template parts
- minimal PHP hooks if required for presentation

Output format:
1. audit
2. implementation plan
3. exact changed files
4. code
5. QA checklist
6. rollback notes
```

---

# 13. 반드시 함께 넣으면 좋은 추가 요구사항

## 13.1 브랜드 일관성
```text
The site should feel like:
- a private institutional market brief
- a premium whisky-bar editorial identity
- calm, intelligent, selective, disciplined
not like:
- a retail trading portal
- a flashy startup blog
- a generic WordPress magazine theme
```

## 13.2 모바일 우선성
```text
The article must remain highly readable on mobile.
Long paragraphs, analytical labels, and citation/source blocks must not collapse into clutter on narrow screens.
```

## 13.3 QA 체크 강제
```text
Include QA checks for:
- mobile readability
- tag badge consistency
- paragraph spacing
- heading hierarchy
- archive card consistency
- dark/light contrast if relevant
- regression risk against existing WordPress content
```

---

# 14. 가장 추천하는 실제 시작 프롬프트

이 프롬프트를 가장 먼저 던지는 것을 권장한다.

```text
You are working on the WordPress styling/presentation track for Macromalt, fully separate from the article generation pipeline.

Your scope is only:
- theme/child-theme styling
- template rendering
- article page layout
- archive/list page styling
- analytical label presentation
- reader-facing visual UX

Do not touch:
- article generation logic
- LLM prompts
- verification rules
- publishing pipeline
- Python code outside presentation-related integration

Design target:
Macromalt should feel like a premium financial editorial product with restrained luxury and high readability.
It should feel elegant, dense, calm, and intelligent — not flashy, noisy, or like a generic news portal.

Task:
Audit the current WordPress presentation layer and propose the safest implementation plan for a premium editorial redesign.

Deliver:
1. current-state audit
2. target visual system
3. component list
4. implementation strategy
5. exact files to modify
6. rollback strategy
7. QA checklist
```

---

# 15. 실제 운영 순서 추천

## 1단계
Claude Code:
- `PROMPT_STYLE_SEPARATION_STRUCTURE_DESIGN.md` 기반으로 구조 설계
- Python/HTML/CSS 분리 구조 확정

## 2단계
Antigravity 또는 Codex:
- 현재 테마/차일드테마 audit
- safe override point 파악
- single post / archive / labels / mobile typography 방향 확정

## 3단계
스타일 구현:
- CSS
- template parts
- minimal PHP hook (필요 시)
- rollback-safe 방식 적용

## 4단계
QA:
- desktop
- mobile
- analytical labels
- source blocks
- archive cards
- readability
- regression

---

# 16. 최종 권장안

가장 안전한 운영 방식은 다음과 같다.

- **Claude Code**
  - 스타일 분리 구조 설계
  - Python/Template/CSS 경계 설계
  - 콘텐츠 품질 파이프라인 유지

- **Antigravity / Codex**
  - WordPress 스타일/UI 구현
  - template/CSS 수정
  - theme/child-theme 반영
  - 롤백 가능한 프론트 작업

핵심 원칙:
- 콘텐츠 품질 파이프라인과 스타일 트랙을 절대 섞지 않는다
- 스타일은 CSS/HTML로 분리
- Python은 데이터와 흐름만 유지
- 프론트 에이전트는 HTML/CSS만 수정하게 만든다

---

# 17. 한 줄 결론

**Macromalt WordPress 스타일 개발은 콘텐츠 품질 파이프라인과 완전히 분리해서 운영하는 것이 맞고, HTML/CSS 분리 구조를 먼저 확정한 뒤 Antigravity/Codex가 그 레이어만 수정하게 하는 방식이 최적이다.**
