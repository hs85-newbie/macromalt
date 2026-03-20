# MACROMALT_HANDOFF_MONETIZATION_SEO_TRACK.md

작성일: 2026-03-20  
용도: **새 채팅창에서 Macromalt 수익화 / SEO 트랙을 바로 이어가기 위한 핸드오프**  
상태: 전달용 최종본

---

## 0. 현재 프로젝트 상태 요약

Macromalt는 현재 아래 기준선 위에 있다.

1. **WordPress 스타일 분리 / 표현 레이어 정리 트랙 완료**
2. **Post2 opener 구조 개편 및 PARSE_FAILED 운영 안정화 완료**
3. **Phase 19 GO 달성**
4. **하루 3회 발행 + 주 1회 Phase 20 운영 점검 자동화 구성 완료**
5. **Phase 20은 차단 게이트가 아니라 상시 운영 정교화 / 모니터링 업무로 해석**

즉, 이제 다음 채팅은 **운영 정교화 게이트를 다시 여는 것이 아니라**,  
그 위에서 **수익화 / SEO 트랙**을 설계하고 실행하는 단계로 본다.

---

## 1. 다음 채팅의 목적

다음 채팅의 목적은 아래 두 가지다.

### A. 수익화
- 광고 삽입 가능 구조 설계
- 수익화 위치 / 밀도 / 정책 설계
- 브랜드 훼손 없이 revenue layer를 얹는 방법 정리

### B. SEO
- technical SEO
- on-page SEO
- information architecture
- metadata / sitemap / indexation / schema
- 속도 / 모바일 / 검색 유입 관점 정리

중요:
이번 트랙은 **“광고를 붙이기 위해 현재 생성 파이프라인을 망가뜨리는 것”**이 아니라,  
**현재 기준선 위에 안전하게 수익화와 SEO를 얹는 것**이어야 한다.

---

## 2. 현재 기준선 (SSOT 해석)

### 2-1. 스타일 / 프론트 기준선
WordPress 스타일 트랙은 **presentation layer decoupling** 원칙 위에서 진행되었고,
아래 항목은 건드리지 않는 것이 명시돼 있다.

- article generation logic
- temporal SSOT
- factual / verification logic
- publishing gates
- slot policy
- content quality policy

또한 시각 방향은 다음을 유지한다.

- premium financial editorial
- restrained luxury
- calm, intelligent, dense but breathable
- typography-first
- mobile readable
- generic news portal 느낌 금지
- retail trading app 느낌 금지
- 과한 motion / gimmick 금지

### 2-2. 운영 기준선
Phase 19는 **GO**로 종료되었다.

핵심 완료 항목:
- `slot/post_type` 정상화
- `picks_section_offset` 기록
- PARSE_FAILED 경로 품질 필드 기록
- 정상 발행 경로 품질 필드 직접 로그화
- Route B 정상 발행 샘플 + 공개 URL 기준 충족
- Phase 19의 구조적 목표 달성

### 2-3. Phase 20 해석
Phase 20은 현재 **상시 운영 정교화 / 후속 모니터링 업무**로 해석한다.

즉:
- 다음 트랙 진입을 막는 차단 게이트가 아님
- 주 1회 운영 점검 / 리포트 성격
- 수익화 / SEO 트랙과 병행 가능한 운영 모니터링 레일

---

## 3. 현재 자동 운영 상태

현재 이 대화 기준으로 GitHub Actions 자동 운영 구성이 잡혀 있다.

### 자동 발행
- **하루 3회 발행**
- GitHub Actions schedule 사용
- KST 기준 08:17 / 14:17 / 20:17
- publish workflow + wrapper script 구조
- logs는 artifact 기반으로 남김

### 주간 운영 점검
- **주 1회 Phase 20 weekly report**
- GitHub Actions schedule 사용
- artifact 집계 기반 Markdown 리포트 생성

중요:
이 구조는 **사용자 노트북이 꺼져 있어도 GitHub-hosted runner 기준으로 운영 가능**한 방향으로 정리됨.

---

## 4. 다음 채팅에서 다룰 범위

다음 채팅에서는 아래를 우선순위로 다룬다.

### 1순위 — 수익화 구조 설계
- 광고 삽입 위치
- single post / archive / category / home / about 별 광고 정책
- 광고 밀도
- 모바일 가독성과 충돌 없는 placement
- AdSense / direct ad / sponsor / affiliate 분기
- disclosure / policy 문구 구조
- premium editorial 톤을 깨지 않는 광고 UX

### 2순위 — 기술 SEO
- title / meta description / canonical
- robots / sitemap
- category / tag / archive indexation 정책
- schema.org (Article / Breadcrumb / Organization / WebSite)
- Open Graph / Twitter Card
- internal linking 구조
- pagination / archive SEO

### 3순위 — 콘텐츠 SEO / IA
- 카테고리 구조
- 태그 정책
- pillar / cluster 가능성
- evergreen vs daily macro post 분리
- author / about / editorial identity 페이지 정리
- source / reference block의 검색 친화적 구조

### 4순위 — 수익화와 SEO의 충돌 방지
- 광고 삽입으로 Core Web Vitals 악화 금지
- intrusive layout shift 금지
- 본문 흐름 파손 금지
- source block / reference block 가독성 저하 금지
- Macromalt 브랜드 톤 저하 금지

---

## 5. 다음 채팅에서 건드리면 안 되는 범위

아래는 이번 수익화 / SEO 트랙에서 **기본적으로 비침범**으로 둔다.

1. article generation logic
2. temporal SSOT
3. verifier / reviser 핵심 구조
4. factual / verification logic
5. publishing gates
6. slot policy
7. content quality policy
8. Post2 opener 구조 규칙
9. Phase 19 정상 경로 품질 로그 구조

즉, 이번 트랙은 원칙적으로:

- **theme / child-theme / template / CSS / plugin / WP 설정 / metadata / script loading**
- **광고 / SEO / 정보구조 / 페이지 설계**

중심으로 움직인다.

---

## 6. 수익화 / SEO 트랙의 성공 기준

다음 채팅에서 정의할 성공 기준은 아래 축으로 잡는다.

### 운영 비회귀
- 하루 3회 발행 유지
- 공개 URL 발행 유지
- weekly Phase 20 report 계속 생성
- 기존 품질 로그 / fallback / parse_failed 체계 비회귀

### 수익화 적합성
- 광고 위치가 premium editorial 톤을 해치지 않음
- mobile readability 유지
- source/reference block 파손 없음
- 과도한 광고 밀도 금지
- disclosure / policy 문구 포함

### SEO 적합성
- title / meta / canonical / sitemap / robots 정비
- 구조화 데이터 적용 가능성 확보
- archive / category / single 정보구조 일관성
- internal linking / taxonomy 정리
- 검색 친화성과 편집 품질의 균형 유지

---

## 7. 다음 채팅에서 먼저 결정할 질문

새 채팅에서는 아래 질문부터 정리하면 된다.

1. **광고 모델을 무엇으로 둘 것인가**
   - AdSense 우선
   - 직접 판매
   - sponsor / partner
   - affiliate
   - 혼합형

2. **광고를 어느 레이어에 넣을 것인가**
   - single post
   - archive
   - category
   - home
   - about / static pages

3. **SEO 우선순위를 무엇부터 할 것인가**
   - technical SEO 먼저
   - taxonomy / IA 먼저
   - on-page/meta 먼저
   - schema / performance 먼저

4. **수익화와 SEO 중 어떤 것을 선행 트랙으로 둘 것인가**
   - 내 추천: technical SEO baseline → monetization placement → schema / performance → optimization

---

## 8. 권장 시작 순서

다음 채팅에서는 아래 순서로 진행하는 것을 권장한다.

### Step 1
**SEO / monetization scope declaration**
- 무엇을 이번 트랙 범위로 둘지 고정

### Step 2
**current-site revenue/SEO audit 설계**
- 어떤 페이지 타입을 볼지
- 어떤 항목을 점검할지
- 어떤 것을 우선 적용할지 정리

### Step 3
**technical SEO baseline 설계**
- metadata
- canonical
- sitemap
- robots
- schema
- taxonomy

### Step 4
**광고 삽입 아키텍처 설계**
- 어디에 광고를 넣고
- 어디에는 넣지 않을지
- 모바일/데스크톱 차이
- lazy load / CLS 방지

### Step 5
**브랜드 보존형 수익화 UX 정의**
- Macromalt 특유의 premium editorial 톤 유지
- 과한 광고형 포털 느낌 금지

---

## 9. 다음 채팅용 시작 프롬프트

아래를 새 채팅 첫 메시지로 사용하면 된다.

```text
Macromalt 프로젝트의 다음 트랙은 수익화 / SEO다.

현재 기준선:
- WordPress 스타일 분리 및 시각 정리 완료
- Phase 19 GO로 운영 정교화 게이트 종료
- Phase 20은 주 1회 운영 모니터링 성격의 상시 업무로 간주
- GitHub Actions로 하루 3회 발행 + 주 1회 Phase 20 리포트 자동 운영 중

이번 채팅의 목표:
1. 수익화 구조 설계
2. technical SEO / on-page SEO / taxonomy / schema 설계
3. 광고와 SEO를 현재 Macromalt 브랜드 톤 위에 안전하게 얹는 방법 정의

절대 건드리지 말 것:
- article generation logic
- temporal SSOT
- verifier/reviser 핵심 구조
- factual / verification logic
- publishing gates
- slot policy
- content quality policy
- Post2 opener 구조 규칙

원하는 결과:
- 구현 우선순위
- 파일/레이어별 변경 범위
- 안전한 적용 순서
- 수익화/SEO 성공 기준
- rollback-safe 실행 계획
```

---

## 10. 최종 정리

이 핸드오프의 핵심은 아래 한 줄이다.

**Macromalt는 현재 “스타일 완료 + 운영 게이트 종료 + 자동 발행/주간 점검 운영화” 상태이며, 다음 채팅은 그 위에서 수익화 / SEO를 설계하는 별도 트랙으로 시작한다.**
