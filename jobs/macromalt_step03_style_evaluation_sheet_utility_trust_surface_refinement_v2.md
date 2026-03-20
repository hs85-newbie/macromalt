# Macromalt Step03 Style Evaluation Sheet v2
## Utility & Trust Surface Refinement — Plan Review + Execution Gate

- Version: v2
- Scope: Step03 plan package review reflecting all review findings from the first submission
- Track Type: WordPress presentation-only style track
- Status: **REVISED EVALUATION SHEET (Plan Gate Before Execution)**

---

## 0. Operating Rule for Future Style Tracks
From this point forward, when Antigravity submits a **first plan package**, the review process must automatically produce:
1. plan review,
2. mandatory fixes,
3. priority 1/2/3,
4. updated evaluation sheet,
without requiring any additional confirmation from the user.

This rule is now considered part of the Macromalt style track operating method.

---

## 1. Step03 Objective
Step03 is not a content-generation step.
It is a **utility and trust surface refinement** step intended to improve reader confidence, discovery, disclosure clarity, archive/search usability, and editorial completeness while preserving Step01 reading quality and Step02 shell/IA improvements.

### Protected Boundaries
The following remain out of scope:
- article generation logic
- temporal SSOT / research logic
- verifier / reviser / publishing gate
- LLM prompt pipeline for article creation
- non-presentation business logic

---

## 2. Review Result on First Plan Package
### Current Gate Decision
**CONDITIONAL APPROVAL**

The first Step03 package has a strong direction and a reasonable structural strategy, but it is **not yet execution-ready**.
It must first resolve the mandatory issues below.

---

## 3. Mandatory Fixes (Must Be Corrected Before Execution)

### Fix 1 — Lock the About Page Structure and Minimum Copy
The plan currently treats the About page too loosely.
Because Step03 is the trust-surface phase, the About page cannot remain a vague operator-only task.

#### Required correction
Provide a locked final structure for the About page including:
- section order
- section titles
- minimum approved copy skeleton for each section
- whether the page is operator-editable after initial implementation

#### Minimum required sections
- What Macromalt is
- What it covers
- How it writes / verifies
- What readers should expect
- Contact / identity / closing note

**Hard rule:** no placeholder-only About strategy.

---

### Fix 2 — Lock Disclosure Box Body Copy and Scope
The plan currently locks the disclosure heading but does not fully lock:
- disclosure body copy
- display scope
- exclusion conditions

#### Required correction
Explicitly define:
- the exact disclosure box body copy
- whether it appears on all single posts or only selected posts
- pages where it must never appear (About, homepage, archive, category, static pages, search)
- insertion method and condition

**Hard rule:** no open-ended disclosure text generation during implementation.

---

### Fix 3 — Clarify Footer Trust Layer Behavior
The plan identifies footer weakness correctly, but the implementation intent is still ambiguous.
It is unclear whether Step03:
- replaces existing footer identity,
- appends a trust micro-layer,
- or mixes both.

#### Required correction
Lock one approach only:
- replace existing footer trust content, or
- append a single trust layer beneath current footer identity

Also state whether contact/disclaimer/legal line(s) are included or intentionally excluded.

**Hard rule:** avoid duplicate footer identity blocks.

---

### Fix 4 — Lock Search Header / Search Result Treatment
The search surface is identified correctly, but the current package does not fully lock:
- how the search title/header is injected
- under what condition it appears
- whether empty state and result header use the same mechanism

#### Required correction
Define:
- exact search header copy
- exact implementation condition (`is_search()` or equivalent)
- whether empty state is separate from result state
- whether hook or template logic is used

**Hard rule:** search treatment must be deterministic and documented.

---

### Fix 5 — Make Exact Files and Rollback Fully Consistent
The current package leaves ambiguity around `style.css`.
It appears in rollback language, but not clearly as a real source modification target.

#### Required correction
Normalize all documentation so that:
- if `style.css` is modified, it must appear in exact source files
- if `style.css` is not modified, rollback must not mention Step03 declarations inside it
- delivery artifacts and source files remain clearly separated

**Hard rule:** no mismatch between exact files and rollback scope.

---

## 4. Priority 1 / 2 / 3
These are the user-facing priorities and must be explicitly addressed in the revised plan.

### Priority 1
**Lock the About page final structure and minimum approved copy.**
No vague “operator will fill it later” strategy.

### Priority 2
**Lock disclosure box body copy and display scope.**
The box must be deterministic, scoped, and non-generative.

### Priority 3
**Resolve footer/search/style.css documentation ambiguity.**
Footer insertion method, search header condition, and `style.css` source/rollback status must all align.

---

## 5. Hard Fail Conditions
If any of the following remain unresolved, the revised Step03 plan automatically fails plan gate review.

1. About page remains only a loose operator note without locked structure.
2. Disclosure text or scope remains open-ended.
3. Footer behavior remains ambiguous or duplicates existing identity.
4. Search state handling remains undefined or inconsistent.
5. `style.css` source/rollback inconsistency remains.
6. Step03 scope expands into article generation, verification, or publishing logic.
7. Step03 degrades Step01 typography/reading quality or Step02 shell/IA.

---

## 6. Scoring Matrix (100 pts)

### A. Scope Safety — 20 pts
- presentation-only integrity maintained
- no generation / verifier / gate leakage

### B. Trust Surface Design Clarity — 20 pts
- About / disclosure / footer trust structure clearly defined

### C. Utility Surface Clarity — 20 pts
- search / archive meta / pagination / empty states clearly documented

### D. File & Rollback Integrity — 20 pts
- exact files, implementation plan, rollback, and delivery artifacts all align

### E. Regression Safety — 20 pts
- Step01 reading layer preserved
- Step02 masthead / navigation / shell preserved

### Interpretation
- **90–100**: APPROVE
- **75–89**: CONDITIONAL APPROVAL
- **0–74**: FAIL

---

## 7. Required Resubmission Package
Before Step03 execution begins, the revised plan package must include updated versions of:
- `step03-01_current_state_audit.md`
- `step03-02_one_direction_visual_system.md`
- `step03-03_component_map.md`
- `step03-04_implementation_plan.md`
- `step03-05_exact_files_to_modify.md`
- `step03-06_rollback_plan.md`
- `step03-07_QA_CHECKLIST.md`

And the revised package must explicitly show:
- locked About structure and copy skeleton
- locked disclosure copy and scope
- locked footer method
- locked search result / empty state behavior
- exact treatment of `style.css`

---

## 8. Execution Approval Gate
Execution may begin only when all of the following are true:
- all 5 mandatory fixes are reflected in the revised docs
- all Priority 1/2/3 points are visibly addressed
- no hard fail condition remains
- evaluation score is at least 90

If not, execution must not begin.

---

## 9. Post-Execution Reporting Standard
After implementation, the standard 5-document verification package must still be submitted under:
- `docs/40_design/Step03/`
- assets in `docs/40_design/Step03/assets/`

Required deliverables:
1. `08A_DEPLOYED_SCREENSHOT_INDEX.md`
2. `08B_MODIFIED_FILE_DIFF_SUMMARY.md`
3. `08C_ZERO_EDIT_SAFETY_PROOF.md`
4. `08D_OPERATOR_SCOPE_STATUS.md`
5. `08E_FINAL_ACCEPTANCE_READY_NOTE.md`

All final reporting must be based on true live state unless clearly labeled as pending sync.

---

## 10. Copy-Paste Review Message for Antigravity
Step03 plan package is directionally strong but not yet execution-ready.
Revise and resubmit the plan package by applying all of the following:

1. Lock the About page final section structure and minimum approved copy.
2. Lock disclosure box body copy and exact display scope.
3. Clarify whether footer trust content replaces or appends existing footer identity.
4. Lock search result header / empty state implementation method and conditions.
5. Make exact files and rollback fully consistent regarding `style.css`.

Priority 1: About page structure + copy lock.
Priority 2: Disclosure body copy + scope lock.
Priority 3: Footer/search/style.css documentation alignment.

Execution must not begin until the revised package passes this evaluation sheet.

---

## 11. Reviewer Final Note
This v2 sheet supersedes the prior Step03 v1 evaluation sheet for plan-gate review.
Future first-plan submissions in the style track should automatically trigger:
- review,
- mandatory fixes,
- priority 1/2/3,
- updated evaluation sheet,
without requiring another confirmation request from the user.
