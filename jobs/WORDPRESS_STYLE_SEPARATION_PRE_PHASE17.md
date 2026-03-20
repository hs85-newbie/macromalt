# WORDPRESS_STYLE_SEPARATION_PRE_PHASE17.md

# WordPress 스타일 분리 선행 트랙 — Pre-Phase 17

## 목적

Phase 17로 바로 진입하기 전에,  
**WordPress 스타일/표현 레이어를 콘텐츠 생성 파이프라인과 분리**하는 선행 작업을 먼저 수행한다.

이번 트랙의 핵심 목표는 다음과 같다.

1. **스타일 수정이 곧 생성 로직 수정이 되지 않도록 분리**
2. **프론트 표현 작업을 Claude Code / Antigravity가 안전하게 나눠서 수행할 수 있게 기반 확보**
3. **Phase 17의 콘텐츠 구조 개편 전, 표현 레이어를 먼저 안정화**

---

## 작업 순서 원칙

이번 작업은 아래 순서로 진행한다.

### 1단계 — Claude Code
**CSS / 스타일 분리 작업 선행**

Claude Code가 먼저 아래를 수행한다.

- 기존 WordPress 출력물의 스타일 오염 지점 식별
- generator.py 또는 관련 출력 코드에 섞여 있는 스타일 책임 분리
- styles/ 구조 설계
- style token 분리
- child-theme 기준 CSS 구조 정리
- HTML parity 유지
- rollback-safe 구조 확보

즉, **표현 레이어를 코드상에서 분리하는 작업은 Claude Code가 담당**한다.

### 2단계 — Antigravity
**분리 이후 프론트 운영/적용/정리 작업 수행**

Antigravity는 Claude Code가 스타일 분리를 끝낸 뒤에만 들어간다.

Antigravity의 역할은 다음과 같다.

- 분리된 스타일 구조 위에서 WordPress 표현 개선
- typography / spacing / hierarchy / component look 정리
- post view / archive view / source block / badge block 등의 시각 정돈
- 실제 운영 화면 기준 점검
- 시각적 일관성 개선

즉, **스타일 분리 전에는 Antigravity가 직접 건드리지 않는다.**

이 순서가 더 안전한 이유는,
Antigravity가 먼저 들어가면 스타일과 구조가 섞인 상태에서 표현 수정이 누적될 수 있고,
나중에 Claude Code가 분리 작업을 할 때 충돌 가능성이 커지기 때문이다.

---

## 역할 분리

## Claude Code 담당 범위
- CSS / 스타일 책임 분리
- styles/ 폴더 도입
- style token 구조 정리
- generator.py 내 스타일 상수 분리
- HTML templates 분리 가능성 검토
- WordPress child-theme 연동 구조 정리
- rollback-safe 구현
- 구현 후 parity 검증

## Antigravity 담당 범위
- 분리된 스타일 기반 위에서 UI/가독성 개선
- typography hierarchy 조정
- section spacing / block rhythm 정리
- label / badge / source box 디자인 정리
- single post / archive / mobile view 시각적 개선
- 운영 화면 기준 튜닝

## 절대 혼동 금지
- Claude Code = 구조 분리
- Antigravity = 분리 이후 표현 적용/운영

---

## 절대 비침범 영역

이번 스타일 분리 트랙에서는 아래를 건드리지 않는다.

- article generation logic
- temporal SSOT logic
- [전망] / [해석] 태그 규칙
- verifier / reviser logic
- publishing gate
- slot policy
- research policy
- content quality logic
- Phase 17 opener 구조 개편 로직

즉, 이번 트랙은 **표현 레이어 전용 트랙**이다.

---

## 권장 구조

아래 구조를 목표로 한다.

```text
styles/
  tokens.py
  wordpress/
    base.css
    typography.css
    layout.css
    components.css
templates/
  post/
  blocks/
theme/
  child-theme/
```

역할은 다음과 같이 나눈다.

- **Python** = 데이터 준비 / 발행 / 값 주입
- **HTML templates** = 마크업 구조
- **CSS** = 타이포 / 간격 / 색상 / 배지 / source block / responsive layout

---

## Claude Code 선행 작업 목표

Claude Code는 우선 아래 4단계를 수행한다.

### Step 1
- `styles/` 생성
- `styles/tokens.py` 생성
- 기존 스타일 상수 추출
- 아직 런타임 동작은 바꾸지 않음

### Step 2
- `generator.py` 등에서 스타일 상수를 token 참조로 교체
- HTML parity 유지
- article logic 비변경

### Step 3
- 현재 출력 HTML과 분리 후 HTML의 parity 검증
- 생성 결과/검증 결과/발행 결과 비회귀 확인

### Step 4
- 안전한 범위에서 templates 분리 제안 또는 일부 도입
- post layout / source block / label block / archive card 등을 별도 구조로 준비

---

## Antigravity 후속 작업 목표

Claude Code가 위 작업을 끝낸 뒤,
Antigravity는 아래를 수행한다.

### 시각 개선
- single post typography 개선
- 제목/부제/섹션/본문 hierarchy 조정
- section spacing 정리
- source/reference block 가독성 개선
- 체크포인트/배지/분석 라벨 시각 정리

### 운영 화면 정돈
- desktop/mobile 동시 점검
- archive / category / single post 간 톤 일치
- Macromalt 브랜드 톤에 맞춘 restrained luxury 방향 유지
- 과한 장식, 과한 컬러, noisy한 카드형 UI 지양

### 주의
Antigravity는 **분리된 구조 위에서만 작업**한다.  
분리되지 않은 generator 스타일 코드에 다시 손대지 않는다.

---

## 브랜드 시각 방향

WordPress 스타일은 아래 방향을 따른다.

- premium financial editorial
- restrained luxury
- calm, intelligent, dense but breathable
- typography-first
- mobile readable
- generic news portal 느낌 금지
- retail trading app 느낌 금지
- 과한 motion / gimmick 금지

---

## 실행용 프롬프트 — Claude Code용

아래 프롬프트를 Claude Code에 먼저 전달한다.

```text
You are working on the Macromalt WordPress style-separation track.

This work must happen BEFORE Antigravity visual refinement.

Your role in this phase is strictly:
- CSS/style separation
- style token extraction
- rollback-safe structural cleanup
- WordPress presentation layer decoupling

Do NOT modify:
- article generation logic
- temporal SSOT
- factual/verification logic
- publishing gates
- slot policy
- content quality policy
- Phase 17 content structure rules

Primary objective:
Create a safe style-separation foundation so that Antigravity can later work only on presentation.

Required work:
1. Audit current style contamination
2. Extract style responsibilities from generator/output layer
3. Create safe structure for:
   - styles/
   - styles/tokens.py
   - WordPress child-theme CSS
4. Keep HTML parity
5. Ensure rollback-safe implementation
6. Prepare templates/ separation only if safe

Safe implementation order:
- Step 1: create styles/ and tokens.py
- Step 2: replace inline/style constants with token references
- Step 3: validate parity
- Step 4: propose or safely add template separation

Deliverables:
1. current-state audit
2. exact files changed
3. implementation plan
4. code changes
5. rollback plan
6. desktop/mobile verification checklist

Important:
Antigravity will work AFTER your separation is complete.
Do not do visual polishing beyond what is necessary for clean separation.
```

---

## 실행용 프롬프트 — Antigravity용

아래 프롬프트는 **Claude Code 분리 완료 후에만** 사용한다.

```text
You are working on the Macromalt WordPress visual refinement track.

Prerequisite:
Claude Code has already completed CSS/style separation.
You must work ONLY on top of the separated style structure.

Do NOT modify:
- article generation logic
- temporal SSOT
- verifier/reviser logic
- publishing workflow
- style token architecture itself unless absolutely necessary

Your job:
- refine WordPress presentation
- improve typography hierarchy
- improve spacing rhythm
- improve readability of single posts
- improve source/reference blocks
- improve labels such as:
  [심층분석], [캐시의 픽], [전망], [해석], [반론]
- keep brand direction: restrained luxury, premium editorial, calm and intelligent

Avoid:
- generic portal design
- noisy cards
- startup blog aesthetics
- retail trading app feel
- over-decoration

Deliverables:
1. visual refinement summary
2. exact CSS / template files changed
3. before/after explanation
4. mobile/desktop verification
5. rollback plan
```

---

## 최종 권장 흐름

1. **Claude Code**
   - 스타일 분리
   - CSS/token 구조 정리
   - parity 검증
   - rollback-safe 구조 확보

2. **Antigravity**
   - 시각 개선
   - WordPress 프론트 운영 정리
   - single/archive/mobile 최종 튜닝

3. **그 다음**
   - Phase 17 진입
   - Post2 opener 구조 개편 / continuity 구조 개편

---

## 결론

이번에는 바로 Phase 17로 가지 않고,
**WordPress 스타일 분리 트랙을 Claude Code가 먼저 수행**한 뒤,
그 다음 **Antigravity가 그 분리된 기반 위에서 표현 작업을 수행**하는 것이 가장 안전하다.

이 순서를 지켜야
- 스타일과 생성 로직 충돌을 줄일 수 있고
- rollback이 쉬우며
- Phase 17 구조 개편 시 프론트 레이어가 발목을 잡지 않는다.
