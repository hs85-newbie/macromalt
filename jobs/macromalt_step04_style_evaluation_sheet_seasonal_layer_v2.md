# Macromalt Step04 — Seasonal Layer Evaluation Sheet (v2)

## 0. Decision
**Status:** CONDITIONAL APPROVAL  
**Meaning:** 방향성은 적절하나, 자동 전환/토큰 시스템은 문서 정합성과 결정론 보강 후 실행해야 한다.

---

## 1. Why this is not yet execution-ready
Step04는 단순 색상 변경이 아니라 **월별 자동 클래스 주입 + CSS 변수 레이어**를 함께 다루므로,  
명명 규칙·시간 기준·토큰 정의가 조금만 어긋나도 실제 구현 시 런타임 혼선이나 검증 실패로 이어질 수 있다.

---

## 2. Mandatory Fixes (Must Fix Before Execution)

### 1) Seasonal body class naming must be unified
현재 계획 문서들 사이에 body class 체계가 일치하지 않는다.
- `step04-03_component_map.md`: `mm-season-jan`, `mm-season-feb` 등 월 단순 클래스
- `step04-04_implementation_plan.md`: 예시 `mm-season-apr-mist`
- 같은 문서의 PHP 예시 코드는 `mm-season-jan-frost` 형태를 생성

이 3개는 서로 다른 규칙이므로, **하나의 최종 규칙**으로 잠가야 한다.  
권장: `mm-season-jan-frost`처럼 **month + preset id**를 포함하는 단일 규칙.

**Pass condition**
- Component Map / Implementation Plan / QA / CSS selector가 동일한 class naming을 사용
- 예시 코드와 실제 selector naming이 동일

---

### 2) Month source must be WordPress-timezone deterministic
현재 구현 예시는 PHP `date('M')`를 사용한다.  
이 방식은 서버 timezone 기준이 될 수 있어, WordPress 설정 timezone과 어긋날 가능성이 있다.

**Required change**
- `date('M')` 대신 WordPress timezone 기반 함수로 고정  
  예: `wp_date('M', current_time('timestamp'))` 또는 동등한 WP-timezone deterministic 접근
- “월 전환 기준 시각”을 문서에 명시

**Pass condition**
- 계획 문서에 WordPress timezone 기준 전환 규칙 명시
- QA에 월 경계(월말/월초) deterministic check 추가

---

### 3) Full token matrix must be locked for every exposed variable
현재 Component Map은 다음 seasonal surface를 노출한다.
- `--mm-bg`
- `--mm-bg-alt`
- `--mm-ink-soft`
- `--mm-rule`
- `--mm-badge-bg`
- `--mm-badge-text`

하지만 `step04-08_seasonal_token_matrix.md`는 현재 `--mm-bg`, `--mm-rule`만 잠겨 있다.  
즉, 실제 오버라이드 대상과 SSOT 토큰 매트릭스가 불일치한다.

**Required change**
- 12개월 모두에 대해 위 6개 변수 전체를 잠금
- 필요 시 hover/accent 관련 변수까지 포함
- 기본 Step03 fallback 값도 함께 명시

**Pass condition**
- Seasonal Token Matrix가 실제 component surface 전체를 커버
- 어떤 변수도 “구현 시 임의 결정” 상태로 남지 않음

---

### 4) Import path / default fallback / rollback chain must be consistent
현재 exact files는 `[NEW] styles/wordpress/seasonal.css`를 말하지만,  
rollback은 `style.css`에서 `@import url("styles/seasonal.css");` 제거를 적고 있다.  
실제 import path와 파일 구조를 명확히 맞춰야 한다.

또 seasonal layer는 Step03 institutional default를 훼손하면 안 되므로,  
`:root` 기본값이 **Step03 final default**와 정확히 같아야 한다.

**Required change**
- `seasonal.css` 실제 import path를 정확히 1개로 고정
- `:root` default token = Step03 institutional default 명시
- rollback 시 “body class 제거 + seasonal import 제거 = Step03로 즉시 복귀”가 문서상 완전히 성립해야 함

**Pass condition**
- Exact Files / Implementation / Rollback이 같은 경로와 같은 복귀 논리를 사용
- seasonal layer 제거 시 Step03 default가 정확히 복원됨

---

### 5) QA and reporting must explicitly include seasonal proof
현재 QA는 자동 클래스, 배경색 변화, 12개월 시뮬레이션, Step01~03 회귀만 적고 있다.  
그러나 Step04는 자동 월간 전환이 핵심이므로, **월별 증빙 문서**가 추가로 필요하다.

**Required change**
- Final reporting standard에 `08F_SEASONAL_SWITCH_PROOF.md` 포함
- 최소 대표 월(예: Jan / Apr / Jul / Oct) 또는 12개월 전체 시뮬레이션 캡처 기준 명시
- QA에 “Disclosure / Masthead / Readability / Badge contrast / Footer trust layer”의 계절별 회귀 체크 추가

**Pass condition**
- 계획 문서와 QA에 08F seasonal proof 요구 반영
- 최종 acceptance가 라이브 월 + 시뮬레이션 월 모두를 기준으로 가능

---

## 3. Priority 1 / 2 / 3

### Priority 1
**Class naming + month source**를 잠가라.  
즉,
- body class 최종 규칙 1개
- WordPress timezone 기준 월 판정 1개  
이 두 개를 먼저 닫아라.

### Priority 2
**Full token matrix**를 잠가라.  
노출 변수 전체(`bg`, `bg-alt`, `ink-soft`, `rule`, `badge-bg`, `badge-text`)를 12개월 기준으로 문서화하라.

### Priority 3
**Import path / rollback / reporting proof**를 정합성 있게 맞춰라.  
특히 `seasonal.css` 경로, Step03 fallback, `08F_SEASONAL_SWITCH_PROOF.md`를 함께 닫아라.

---

## 4. Hard Fail Conditions
아래 중 하나라도 해당하면 실행 승인 불가.

1. body class naming이 문서끼리 다름
2. 월 판정이 서버 timezone 의존 상태로 남음
3. token matrix가 실제 노출 변수 전체를 커버하지 않음
4. seasonal.css 경로/rollback 문서가 서로 다름
5. 08F seasonal proof 기준이 계획/QA에 반영되지 않음
6. Step01~03 핵심 자산(Disclosure, Masthead, Reading Rhythm, Footer Trust)이 seasonal layer로 흔들릴 위험이 남아 있음

---

## 5. Scoring (100)
- Seasonal automation determinism: 25
- Token SSOT completeness: 20
- Regression safety (Step01~03 protection): 20
- File / rollback consistency: 15
- QA / reporting completeness: 10
- Brand restraint & institutional tone preservation: 10

**Pass:** 90+  
**Conditional Pass:** 75–89  
**Fail:** below 75

---

## 6. Required Resubmission Set
재제출 시 아래 문서가 반드시 업데이트되어야 한다.

- `step04-03_component_map.md`
- `step04-04_implementation_plan.md`
- `step04-05_exact_files_to_modify.md`
- `step04-06_rollback_plan.md`
- `step04-07_QA_CHECKLIST.md`
- `step04-08_seasonal_token_matrix.md`

---

## 7. Re-instruction to Antigravity
Use this exact instruction:

> Step04 plan package is directionally strong, but it is not yet execution-approved.  
> Revise and resubmit with the following mandatory fixes:
> 1) unify the seasonal body class naming scheme across all documents and CSS selectors,  
> 2) replace raw server-date month logic with WordPress-timezone deterministic month resolution,  
> 3) lock the full 12-month token matrix for every exposed seasonal variable,  
> 4) align seasonal.css import path, default Step03 fallback, and rollback logic,  
> 5) add explicit seasonal proof requirements including 08F_SEASONAL_SWITCH_PROOF.md.  
> After these corrections, Step04 may proceed to implementation.

---

## 8. Workflow Rule
Step04 must follow the same review chain as prior style steps:

1. Plan package submission  
2. Review  
3. Evaluation sheet update  
4. Resubmission  
5. Execution approval  
6. Implementation  
7. `08A~08F` verification package  
8. Final acceptance

