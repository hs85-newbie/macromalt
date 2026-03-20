# MACROMALT_SEO_MONETIZATION_SSOT_v1

- 작성일: 2026-03-20
- 상태: SSOT / Claude Code 실행 기준 문서
- 적용 대상: Macromalt WordPress 프론트/SEO/수익화 트랙
- 우선 실행 에이전트: Claude Code
- 후속 협업 에이전트: Antigravity, Codex (필요 시)

---

## 0. 문서 목적

이 문서는 Macromalt의 **SEO / 수익화 트랙 단일 기준 문서(SSOT)** 이다.
목표는 아래 세 가지다.

1. 현재 프로젝트 기준선 위에서 **안전하게 SEO와 수익화 레이어를 얹는 것**
2. Claude Code가 **범위 / 금지 범위 / 구현 순서 / 성공 기준 / 롤백 기준**을 혼동 없이 따르게 하는 것
3. 향후 Antigravity/Codex가 참여하더라도 **같은 기준 문서 위에서 작업**하게 하는 것

이 문서는 “광고를 빨리 붙이는 문서”가 아니라,
**브랜드 훼손 없이 검색 유입과 수익화를 구조적으로 설계하는 문서**다.

---

## 1. 현재 기준선

Macromalt는 현재 아래 상태를 전제로 한다.

1. WordPress 스타일 분리 / 표현 레이어 정리 완료
2. Post2 opener 구조 개편 및 PARSE_FAILED 운영 안정화 완료
3. Phase 19 GO 달성
4. 하루 3회 발행 + 주 1회 운영 점검 자동화 구성 완료
5. Phase 20은 차단 게이트가 아니라 운영 모니터링 레일로 해석

즉, 이번 트랙은 **운영 정상화 이전 단계가 아니라**,
이미 운영 가능한 기준선 위에서 **SEO / monetization을 별도 레이어로 추가하는 단계**다.

---

## 2. 이번 트랙의 핵심 원칙

### 2-1. 절대 원칙

이번 트랙은 아래를 절대 건드리지 않는다.

- article generation logic
- temporal SSOT
- verifier / reviser 핵심 구조
- factual / verification logic
- publishing gates
- slot policy
- content quality policy
- Post2 opener 구조 규칙
- Phase 19 정상 경로 품질 로그 구조

### 2-2. 이번 트랙이 다루는 범위

이번 트랙은 아래 레이어만 다룬다.

- WordPress theme / child-theme
- template / template parts
- CSS
- metadata injection
- schema injection
- robots / sitemap / ads.txt
- script loading order
- page-level information architecture
- ad placement and disclosure UX
- internal linking / taxonomy / archive policy

### 2-3. 브랜드 방향

모든 SEO / 수익화 구현은 아래 톤을 유지해야 한다.

- premium financial editorial
- restrained luxury
- calm, intelligent, dense but breathable
- typography-first
- mobile readable
- generic news portal 느낌 금지
- retail trading app 느낌 금지
- 과한 motion / gimmick 금지

광고를 붙이더라도 **포털화**되면 실패로 간주한다.

---

## 3. 이번 트랙의 목표

### 목표 A — Technical SEO baseline 구축

최소한 아래를 구조적으로 정비한다.

- title
- meta description
- canonical
- robots
- sitemap
- Open Graph / Twitter Card
- schema.org (Article / Breadcrumb / Organization / WebSite)
- archive / category / tag indexation policy
- internal linking baseline
- author / about / editorial identity 노출

### 목표 B — 브랜드 보존형 수익화 구조 설계

최소한 아래를 구조적으로 정비한다.

- 광고 모델 1차 선택
- 페이지 타입별 광고 허용 / 금지 정책
- 모바일/데스크톱 placement 분리
- CLS/가독성 저해 없는 삽입 구조
- disclosure / 광고 정책 문구
- 제외 페이지 / 제외 영역 정의

### 목표 C — SEO와 수익화의 충돌 방지

아래 충돌을 예방한다.

- 광고 삽입으로 Core Web Vitals 악화
- 본문 흐름 파손
- source/reference block 가독성 저하
- author/about 신뢰 시그널 약화
- taxonomy 남발로 인한 indexation 품질 저하

---

## 4. 외부 정책 기준 반영

Google Search 기준상, 검색 성과의 핵심은 **사람을 위한 원본성 있는 유용한 콘텐츠**이며,
작성자 정보, 사이트 소개, 명확한 출처 등 신뢰 신호를 분명히 하는 것이 권장된다.

Google Search 기준상 canonical은 중복 또는 유사 URL 정리에 사용하며,
리디렉션, `rel="canonical"`, sitemap 포함이 canonicalization 신호로 작동한다.
또한 robots.txt는 canonicalization 용도가 아니다.

Google Search 기준상 sitemap의 `<lastmod>`는 **실제 의미 있는 수정일일 때만 정확하게** 써야 하며,
Google은 `<priority>`와 `<changefreq>`를 무시한다.

Google Search 기준상 구조화 데이터는 Article / Breadcrumb / Organization 등을 통해
페이지와 사이트를 더 잘 이해하도록 돕는다.

Google 기준상 Core Web Vitals의 권장 목표는 다음과 같다.

- LCP: 2.5초 이내
- INP: 200ms 미만
- CLS: 0.1 미만

AdSense 정책상 광고는 메뉴, 내비게이션, 다운로드 버튼 등으로 오인되게 배치하면 안 되며,
우발 클릭을 유도하는 구조를 피해야 한다.
또한 Auto ads는 excluded areas, excluded pages, ad load, in-page formats 제어가 가능하다.
Multiplex Auto ads는 인페이지 그리드형 네이티브 광고다.

---

## 5. Macromalt의 1차 전략 결정

### 5-1. 수익화 1차 선택

**1차 권장안: AdSense 중심의 보수적 시작**

이유:

- 가장 빠르게 실험 가능
- 초기 구현 난이도가 낮음
- page exclusion / excluded areas / experiment 운용 가능
- direct ad / sponsor / affiliate보다 운영 복잡도가 낮음
- 현재 Macromalt 단계에서는 과도한 상업화보다 데이터 수집이 더 중요함

### 5-2. 초기 광고 포맷 권장

초기 포맷 권장 순서:

1. Multiplex Auto ads
2. 제한적 in-page ads
3. 이후 anchor / side rail / vignette는 실측 후 검토

### 5-3. 광고 밀도 원칙

- 초기에는 **낮은 광고 밀도**를 기본값으로 둔다.
- 첫 단계에서 home / about / archive 상단을 광고화하지 않는다.
- single post 중심으로 시작한다.
- 광고는 “읽기 흐름을 끊지 않는 위치”에만 둔다.

---

## 6. 페이지 타입별 정책

### 6-1. Single Post

허용:

- 본문 중단 1개 후보
- 글 하단 1개 후보
- 관련 글 블록 하단 Multiplex 후보

금지:

- H1 직하단
- 작성자/브랜드 신뢰 정보 바로 인접 위치
- source/reference block 인접 위치
- 첫 섹션 시작 직전
- 결론/핵심 요약 직전

원칙:

- 본문 흐름 보존
- source block 보존
- CLS 최소화
- 모바일에서 문단 사이 과밀 광고 금지

### 6-2. Home

초기 정책:

- 광고 비활성 또는 매우 제한적
- hero / 주요 큐레이션 블록 상단 광고 금지

원칙:

- 브랜드 첫인상 우선
- 포털형 레이아웃 금지

### 6-3. Category / Archive

초기 정책:

- 상단 광고 금지
- 리스트 중간 광고는 후순위 검토
- taxonomy 정리 이후에만 부분 도입 검토

원칙:

- 카테고리 정보구조 우선
- 검색/탐색 UX 우선

### 6-4. About / Editorial / Author

초기 정책:

- 광고 비활성 권장

원칙:

- 신뢰 신호 페이지는 수익화보다 E-E-A-T 성격의 설명 기능 우선

### 6-5. Static Pages

- 이용약관 / 개인정보 / 광고정책 / disclosure 페이지: 광고 비활성 권장

---

## 7. SEO 설계 기준

### 7-1. Metadata

모든 인덱싱 대상 페이지에 대해 아래를 정비한다.

- 고유 `<title>`
- 고유 meta description
- canonical 1개
- OG title / description / image / url
- Twitter Card metadata

### 7-2. Canonical

원칙:

- 페이지당 canonical 1개만 사용
- canonical은 absolute URL 사용
- sitemap URL, 내부 링크 URL, canonical URL의 방향을 최대한 일치시킨다.
- robots.txt로 canonical 문제를 해결하려고 하지 않는다.

### 7-3. Robots / Indexation

원칙:

- robots.txt는 크롤링 제어용으로만 사용
- 색인 제외가 목적이면 meta robots / page-level policy를 검토
- 불필요한 tag archive / thin archive / duplicate-like archive는 indexation 정책을 보수적으로 둔다.

### 7-4. Sitemap

원칙:

- canonical 대상 URL 중심으로 sitemap 구성
- `<lastmod>`는 실제 의미 있는 수정일일 때만 기록
- WordPress 기본 sitemap 또는 SEO plugin sitemap 중 **단일 진실 소스 하나만 유지**
- Search Console 제출 기준 URL과 sitemap URL을 일치시킨다.

### 7-5. Structured Data

우선 적용 대상:

- Single Post: `Article` 또는 `BlogPosting`
- Breadcrumb path: `BreadcrumbList`
- Home/About: `Organization`
- Site-level search identity 필요 시: `WebSite`

Single Post 권장 필드:

- headline
- description
- author.name
- author.url
- datePublished
- dateModified
- image
- mainEntityOfPage
- publisher

### 7-6. Author / Editorial Identity

필수 정비:

- author page 존재
- about / editorial identity 페이지 존재
- 가능한 경우 byline과 author page 연결
- 사이트의 목적 / 작성 원칙 / 검증 원칙을 독자에게 설명

### 7-7. Internal Linking / IA

원칙:

- daily macro post와 evergreen explainers를 분리해 사고한다.
- category는 넓고 분명하게, tag는 보수적으로 운용한다.
- internal linking은 자동 남발보다 편집 기준을 우선한다.
- pillar / cluster는 후속 확장안으로 두되, 1차에서는 single / archive / category 일관성부터 맞춘다.

---

## 8. 수익화와 SEO 충돌 방지 규칙

다음 항목 중 하나라도 깨지면 배포 보류 대상이다.

1. 광고 삽입 후 LCP/INP/CLS가 의미 있게 악화
2. mobile readability가 악화
3. source/reference block이 밀리거나 잘림
4. H1~첫 2문단 사이 광고가 들어가 맥락 파악을 방해
5. 광고가 내비게이션처럼 오인될 수 있는 위치에 배치
6. 신뢰 페이지(about/author/editorial policy)가 광고로 오염
7. taxonomy를 과도하게 늘려 thin archive가 급증

---

## 9. 기술 구현 범위

### 9-1. 허용 파일 / 레이어

- child-theme CSS
- template parts
- theme functions.php 내 presentation/metadata hook
- schema injector
- robots.txt 관리 레이어
- sitemap 설정 레이어
- header / head metadata 관련 파일
- ads.txt 배포 경로
- AdSense / analytics / consent 관련 theme-level loader

### 9-2. 비허용 파일 / 레이어

- article generation core
- temporal/factual verification core
- publishing workflow core
- slot policy core
- content quality enforcement core
- LLM prompt source of truth

---

## 10. Claude Code 실행 순서

### Step 1 — Scope Lock

수행 내용:

- 현재 SEO/수익화 트랙 범위 고정
- 비침범 범위 재확인
- 실제 워드프레스/테마 구조 파악

산출물:

- scope declaration
- touched files 예상 목록
- non-goal 명시

### Step 2 — Current-State Audit

수행 내용:

- 현재 페이지 타입 인벤토리 작성
- metadata/canonical/robots/sitemap/schema 현황 점검
- author/about/editorial identity 노출 상태 점검
- 현재 광고 삽입 지점 및 스크립트 유무 점검
- Search Console / AdSense / ads.txt 준비 상태 점검

산출물:

- audit report
- risk list
- quick wins list

### Step 3 — Technical SEO Baseline

수행 내용:

- title/meta/canonical 정비
- robots/sitemap 정비
- schema baseline 적용
- OG/Twitter metadata 정비
- archive/category/tag indexation 정책 정리
- author/about/editorial identity 연결

산출물:

- changed files
- implementation notes
- QA checklist

### Step 4 — Monetization Architecture

수행 내용:

- page-type별 ad allow/deny 정책 구현
- excluded pages / excluded areas 설계
- single post 중심 배치 구현
- disclosure / ad policy 문구 연결
- script loading / lazy handling / CLS 대응

산출물:

- ad placement map
- changed files
- rollback notes

### Step 5 — Performance / CWV Guardrail

수행 내용:

- 광고/SEO 변경 후 성능 영향 점검
- LCP/INP/CLS 위험 요소 정리
- template shift / image size / font / script load 영향 검토

산출물:

- before/after measurement log
- blocker list
- safe rollout recommendation

### Step 6 — Rollout Plan

수행 내용:

- staged rollout 순서 정의
- feature flag or safe toggle 여부 검토
- revert path 정의

산출물:

- rollout order
- rollback plan
- post-deploy checklist

---

## 11. 우선 구현 목록

### 11-1. 반드시 먼저 할 것

1. `<title>` / meta description / canonical 정비
2. sitemap 단일 진실 소스 정리
3. robots.txt 검토
4. author / about / editorial identity 정비
5. Article / Breadcrumb / Organization schema 적용
6. Open Graph / Twitter Card 정비
7. category/tag indexation 정책 정리

### 11-2. 그 다음 할 것

1. single post용 AdSense placement 설계
2. excluded areas / excluded pages 설계
3. disclosure / ad policy 문구 정리
4. ads.txt 배포
5. Search Console / AdSense 운영 체크리스트 정리

### 11-3. 후순위

1. archive/list 중간 광고
2. side rail ads
3. anchor/vignette 확장
4. affiliate / sponsor / partner 페이지 확장
5. pillar/cluster 재편

---

## 12. 성공 기준

### 운영 비회귀

- 하루 3회 발행 유지
- 공개 URL 발행 유지
- 주간 운영 점검 리포트 유지
- parse_failed / fallback / quality log 체계 비회귀

### SEO 적합성

- single/category/archive/home/about 별 metadata 기준 확정
- canonical 충돌 없음
- sitemap/robots 일관성 확보
- 구조화 데이터 적용 가능성 확보
- author/about/editorial identity 노출 개선
- taxonomy/indexation 정책 명시화

### 수익화 적합성

- premium editorial 톤 유지
- mobile readability 유지
- source/reference block 보존
- 광고 밀도 과잉 없음
- 광고 오인 위험 없음
- disclosure / ad policy 문구 반영

### 성능 적합성

- LCP 2.5s 이내 목표
- INP 200ms 미만 목표
- CLS 0.1 미만 목표
- 광고 삽입 전후 레이아웃 안정성 유지

---

## 13. 롤백 기준

아래 중 하나라도 발생하면 즉시 롤백 후보로 본다.

1. canonical / robots / sitemap 충돌로 인덱싱 리스크 발생
2. H1~첫 2문단 가독성 저하
3. source block 파손
4. 광고가 메뉴/네비게이션처럼 보임
5. Core Web Vitals 급격 악화
6. mobile article readability 저하
7. about/author 신뢰 페이지 오염
8. single/category/archive 시각 톤 붕괴

---

## 14. Claude Code 산출물 형식 고정

Claude Code는 반드시 아래 형식으로 답해야 한다.

1. current-state audit
2. exact files to change
3. implementation plan
4. code changes
5. QA checklist
6. rollback plan
7. risks / open questions

코드를 제시할 때는 다음을 지킨다.

- 파일 단위로 분리
- 변경 이유 명시
- SEO/meta/schema와 ad placement를 섞지 말고 구분
- 실험적 제안과 필수 구현을 분리

---

## 15. Claude Code 실행 프롬프트

```text
You are working on the Macromalt SEO / monetization track.

This document is the SSOT for the track.
You must follow it strictly.

Primary objective:
Safely add technical SEO and a conservative monetization layer on top of the current Macromalt baseline without modifying the content-generation pipeline.

Hard boundaries — do NOT modify:
- article generation logic
- temporal SSOT
- verifier / reviser core structure
- factual / verification logic
- publishing gates
- slot policy
- content quality policy
- Post2 opener rules
- Phase 19 quality logging structure

Scope in:
- WordPress theme / child-theme
- template parts
- CSS
- metadata injection
- schema injection
- robots / sitemap / ads.txt
- script loading order
- page-level information architecture
- ad placement and disclosure UX
- internal linking / taxonomy / archive policy

Brand target:
- premium financial editorial
- restrained luxury
- calm, intelligent, dense but breathable
- typography-first
- mobile readable
- not a generic news portal
- not a retail trading app
- no gimmicky motion

Track priorities:
1. technical SEO baseline
2. conservative monetization placement
3. schema / performance guardrails
4. rollout-safe optimization

Technical SEO requirements:
- unique title / meta description / canonical per indexable page
- consistent sitemap strategy
- robots.txt review
- Article / Breadcrumb / Organization / WebSite schema where appropriate
- Open Graph / Twitter Card metadata
- author / about / editorial identity visibility
- taxonomy / archive indexation policy

Monetization requirements:
- start conservatively
- single post first
- avoid H1-adjacent placements
- avoid source/reference block adjacency
- avoid misleading navigation-like placements
- define excluded pages and excluded areas
- include disclosure / ad policy wording
- protect mobile readability and CLS

Success criteria:
- no regression to publishing operations
- no regression to quality/fallback/parse_failed systems
- premium editorial tone preserved
- metadata/canonical/sitemap/robots consistency improved
- structured data baseline added
- mobile readability preserved
- Core Web Vitals not meaningfully degraded

Required output format:
1. current-state audit
2. exact files to change
3. implementation plan
4. code changes
5. QA checklist
6. rollback plan
7. risks / open questions

When making recommendations, separate:
- required implementation
- optional follow-up improvements
- risky or deferred items

Do not drift into content rewriting or pipeline redesign.
Operate only within the allowed layers.
```

---

## 16. 후속 협업 규칙

- Claude Code가 baseline을 만든 뒤 Antigravity/Codex는 그 위에서만 후속 refinement를 수행한다.
- 후속 에이전트는 generator/pipeline 쪽으로 역침범하지 않는다.
- SEO와 광고 실험은 프론트/테마/설정 레이어에서만 반복한다.

---

## 17. 한 줄 결론

**Macromalt의 지금 단계는 “SEO / 수익화 트랙을 여는 시점”이 맞다. 다만 방식은 반드시 technical SEO baseline 선행, single-post 중심의 보수적 광고 실험 후행, 그리고 브랜드·가독성·운영 비회귀를 최우선으로 하는 SSOT 기반 실행이어야 한다.**
