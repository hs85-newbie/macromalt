# Macromalt Step04 — Seasonal Layer Evaluation Sheet (v3, Scope Gate)

## 0. Decision
**Status:** REJECT AS-INTEGRATED  
**Meaning:** Step04 Seasonal Layer 계획에 Phase 19 backend logging을 통합한 현재 안은 실행 승인 불가.  
**Required Next Move:** Step04는 다시 **presentation-only seasonal layer**로 되돌리고, Phase 19는 별도 개발 트랙으로 분리해야 한다.

---

## 1. Core Reason for Rejection
Step04는 WordPress 스타일 트랙의 일부이며, 기준 문서상 **presentation-only**여야 한다.  
현재 수정안은 `generator.py`, `main.py` 등 backend audit/logging 변경을 포함하여 스타일 트랙의 안전 경계를 넘었다.

This is not a minor refinement issue.  
It is a **scope violation** against the style-track SSOT.

---

## 2. Evidence of Scope Violation

### A) Step04 original safety boundary
Original Step04 exact-files plan explicitly stated:
- modify only `functions.php`, `style.css`, `styles/wordpress/*.css`, `seasonal.css`
- **NO CHANGE:** `generator.py`, `publisher.py` and backend pipeline

This means Step04 was defined as a seasonal styling layer only.

### B) Integrated plan changed Step04 into a dual-track backend+frontend task
The revised Step04 implementation plan now proposes:
- `generator.py` refactor
- `main.py` logging output changes
- success-path pass-field logging for Phase 19
- verification via run/log evidence

This is outside the WordPress presentation track.

### C) Style-track master rule forbids this
The WordPress style track master guide and pre-Phase17 separation guide both prohibit modifying:
- article generation logic
- factual/verification logic
- publishing workflow
- backend pipeline behavior

Therefore the integrated Step04+Phase19 plan cannot be accepted within Step04.

---

## 3. Mandatory Fixes (Must Fix Before Any Step04 Execution)

### 1) Remove all backend logging work from Step04
Delete all Step04 references to:
- `generator.py`
- `main.py`
- `_calculate_quality_metrics`
- `_log_parse_failed_event`
- success-path pass-field logging
- Phase 19 audit JSON output

**Pass condition**
- Step04 documents return to style-only scope
- Exact files list contains only child-theme / CSS / seasonal artifacts

---

### 2) Split Phase 19 into a separate development track
Create a separate package for Phase 19 backend logging, for example:
- `phase19-logging-01_current_state_audit.md`
- `phase19-logging-02_implementation_plan.md`
- `phase19-logging-03_exact_files_to_modify.md`
- `phase19-logging-04_rollback_plan.md`
- `phase19-logging-05_verification_checklist.md`

**Pass condition**
- Step04 and Phase 19 no longer share implementation ownership or execution flow
- Phase 19 is reviewed under dev/backend rules, not style-track rules

---

### 3) Restore Step04 deterministic month logic to a WordPress-safe standard
Even before the scope violation, Step04 still had unresolved deterministic issues:
- body class naming inconsistency
- raw `date('M')` usage instead of WordPress-timezone deterministic month resolution

**Pass condition**
- single body class naming scheme across all Step04 docs
- WP-timezone month resolution defined and documented

---

### 4) Complete the full seasonal token matrix
Step04 still needs a locked token matrix for all exposed seasonal variables, not only background/rule.

**Pass condition**
- 12-month matrix covers all exposed seasonal variables
- fallback to Step03 default is clearly defined

---

### 5) Add explicit seasonal proof requirements
Seasonal switching must have its own proof layer.

**Pass condition**
- `08F_SEASONAL_SWITCH_PROOF.md` is required in QA/reporting
- proof includes representative month simulations and live-month verification

---

## 4. Priority 1 / 2 / 3

### Priority 1
**Undo the Step04 + Phase19 merge.**  
Return Step04 to pure seasonal styling scope immediately.

### Priority 2
**Open Phase 19 as a separate backend track.**  
Do not allow generator/main logging changes inside the style workflow.

### Priority 3
**After separation, finish the original Step04 determinism fixes**  
(class naming, WP-timezone month source, full token matrix, 08F proof).

---

## 5. Hard Fail Conditions
If any of the following remains true, Step04 cannot be executed:

1. Step04 documents still mention modifying `generator.py` or `main.py`
2. Step04 exact-files list contains backend pipeline files
3. Step04 implementation sequence includes logging / run-level backend audit tasks
4. seasonal month resolution still relies on raw server date logic
5. token matrix remains incomplete
6. `08F_SEASONAL_SWITCH_PROOF.md` is not part of the reporting standard
7. Step01–03 protected assets risk regression under seasonal layer changes

---

## 6. Scoring (Step04 only, after re-separation)
- Scope purity / presentation-only compliance: 30
- Seasonal determinism: 20
- Token SSOT completeness: 15
- Regression safety (Step01–03 protection): 15
- File / rollback consistency: 10
- QA / reporting completeness incl. 08F: 10

**Pass:** 90+  
**Conditional Pass:** 75–89  
**Fail:** below 75

---

## 7. Required Resubmission Set

### Step04 resubmission
- `step04-03_component_map.md`
- `step04-04_implementation_plan.md`
- `step04-05_exact_files_to_modify.md`
- `step04-06_rollback_plan.md`
- `step04-07_QA_CHECKLIST.md`
- `step04-08_seasonal_token_matrix.md`

### Separate Phase19 package
- new Phase19 backend logging package (separate folder / separate review track)

---

## 8. Re-instruction to Antigravity
Use this exact instruction:

> The current Step04 + Phase19 integrated plan is rejected as out-of-scope for the Macromalt style track.  
> Step04 must remain a presentation-only seasonal layer and must not modify `generator.py`, `main.py`, or backend logging behavior.  
> Revert Step04 documents to style-only scope and resubmit them.  
> Open Phase 19 logging as a separate backend development package with its own implementation plan, exact files, rollback plan, and verification checklist.  
> After separation, complete the original Step04 determinism fixes: unified seasonal class naming, WordPress-timezone month resolution, full token matrix, and explicit `08F_SEASONAL_SWITCH_PROOF.md`.

---

## 9. Workflow Rule
From this point forward:

1. Step04 Seasonal Layer review continues under **style-track rules**
2. Phase 19 logging review continues under **backend/dev rules**
3. These two tracks must not be merged in the same execution approval package
