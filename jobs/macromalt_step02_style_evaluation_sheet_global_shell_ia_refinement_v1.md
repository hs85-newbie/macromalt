# Macromalt Step02 Style Evaluation Sheet — Global Shell & IA Refinement (v1)

## 0. Purpose
This document is the official review and gate sheet for **Macromalt Step02**.

Step02 is not a content phase.
Step02 is not a pipeline phase.
Step02 is a **presentation-layer refinement phase** focused on:
- homepage shell
- global navigation
- archive/category identity
- mobile browsing shell
- site-level editorial coherence

This evaluation sheet must be used in the following sequence:

1. **Antigravity plans the work**
2. **Plan package is verified**
3. **Review + evaluation sheet decision is written**
4. **Only then Antigravity executes the real implementation**
5. **Final 08A~08E verification package is reviewed**

---

## 1. Fixed Separation Rules
### Hard boundary
The following must remain untouched:
- article generation logic
- temporal SSOT logic
- verifier / reviser logic
- publishing gates / workflow behavior
- research/content quality logic
- `generator.py`
- `styles/tokens.py` unless explicitly approved and justified

### Step02 allowed scope
- homepage shell presentation
- site identity presentation
- global nav / menu shell
- archive/category/list-page visual UX
- mobile browsing shell
- child-theme safe CSS / template changes

---

## 2. Review Tracks
This evaluation sheet has **two gates**.

### Gate A — Plan Review Gate
Used before implementation.

### Gate B — Execution / Acceptance Gate
Used after implementation and after the 08A~08E package is submitted.

---

# Gate A — Step02 Plan Review

## A1. Mandatory Review Items
The plan package is acceptable only if all of the following exist:

- `step02-01_current_state_audit.md`
- `step02-02_one_direction_visual_system.md`
- `step02-03_component_map.md`
- `step02-04_implementation_plan.md`
- `step02-05_exact_files_to_modify.md`
- `step02-06_rollback_plan.md`
- `step02-07_QA_CHECKLIST.md`

If any required file is missing, Gate A cannot pass.

---

## A2. Must-Fix Review Points
These are the **minimum must-fix requirements** for Step02 plan approval.

### Must-Fix 1 — Exact file map must exist
A dedicated `step02-05_exact_files_to_modify.md` must exist.
It must not be buried only inside the implementation plan.

### Must-Fix 2 — One-direction system must be closed
The visual/IA direction must be one-direction only.
No unresolved multi-option homepage/nav/archive direction.

### Must-Fix 3 — CSS / template / operator tasks must be separated
`step02-03_component_map.md` must classify each item into:
- CSS-only
- template-required
- WordPress Admin / Operator required
- not recommended / remove

### Must-Fix 4 — Site-shell problems must be addressed directly
The audit and plan must explicitly cover:
- homepage shell identity
- navigation usefulness
- archive/category distinction
- mobile shell readability

### Must-Fix 5 — Non-style verification noise must be removed
Plan/verification text must not introduce unrelated pipeline checks or irrelevant tooling that blurs presentation-only scope.

---

## A3. Priority Feedback Block
These are the first three priority checks reviewers should usually emphasize.

### Priority 1
`step02-05_exact_files_to_modify.md` must be complete and explicit.

### Priority 2
`step02-02_one_direction_visual_system.md` must commit to one final direction.

### Priority 3
`step02-03_component_map.md` must separate CSS-only vs template-required vs operator-required work clearly.

---

## A4. Plan Scoring (100 points)
### 1. Scope discipline — 20
- stays in presentation layer
- no pipeline contamination

### 2. Audit quality — 15
- identifies real shell/IA weaknesses
- not generic

### 3. One-direction clarity — 15
- one clear direction only
- no unresolved alternatives

### 4. File-map precision — 15
- exact files and impact areas are explicit

### 5. CSS/template/operator separation — 15
- roles and boundaries are clean

### 6. Rollback safety — 10
- rollback is realistic and fast

### 7. QA quality — 10
- desktop/mobile/home/archive/category/regression checks present

### Gate A Decision Bands
- **90–100**: APPROVE
- **75–89**: CONDITIONAL APPROVE
- **0–74**: REVISE BEFORE IMPLEMENTATION

---

## A5. Gate A Hard Fail Conditions
Immediate fail if any of the following occurs:
- required Step02 plan files missing
- generator/pipeline logic touched
- multiple unresolved visual systems left open
- no exact file map
- no CSS/template/operator separation
- no rollback plan

---

## A6. Gate A Review Template
Use this block when reviewing the Step02 plan package.

```text
Step02 plan review decision:
[APPROVE / CONDITIONAL APPROVE / REVISE BEFORE IMPLEMENTATION]

Reason:
- 
- 
- 

Mandatory fixes required before implementation:
1. 
2. 
3. 
4. 
5. 

Priority feedback:
1. 
2. 
3. 
```

---

# Gate B — Step02 Execution / Final Acceptance

## B1. Required Completion Package
Final execution review requires all of the following inside `docs/40_design/Step02/`:

1. `08A_DEPLOYED_SCREENSHOT_INDEX.md`
2. `08B_MODIFIED_FILE_DIFF_SUMMARY.md`
3. `08C_ZERO_EDIT_SAFETY_PROOF.md`
4. `08D_OPERATOR_SCOPE_STATUS.md`
5. `08E_FINAL_ACCEPTANCE_READY_NOTE.md`
6. screenshot assets in `docs/40_design/Step02/assets/`

---

## B2. Reporting Standard (Fixed)
### 08A
Must include live desktop/mobile screenshots for:
- homepage
- archive/category
- any single-post view needed for regression proof

If deployment is blocked, it must be labeled clearly as `Pending Sync`, and target visuals must be separated from live proof.

### 08B
Must summarize every modified file with:
- Purpose
- Key Changes
- Impact
- Rollback Ease

Unified diffs or clear before/after blocks are preferred.

### 08C
Must prove zero-edit safety for:
- `generator.py`
- `styles/tokens.py`

Preferred evidence:
- `git status`
- `git diff [file]`

### 08D
Must distinguish agent work from operator work.
Allowed status labels only:
- `DONE`
- `DONE_BY_OPERATOR`
- `NOT_DONE_OPERATOR_PENDING`
- `NOT_REQUIRED`
- `PARTIAL`

### 08E
Must summarize:
- whether mandatory fixes were completed
- whether final acceptance is ready
- which operator items remain, if any

---

## B3. Final Acceptance Criteria
Final acceptance should confirm all of the following:

### 1. Homepage shell quality
- homepage no longer feels like a default blog index
- identity feels deliberate and editorial
- hero/intro/section structure is calm and useful

### 2. Global navigation quality
- navigation is meaningfully clearer than before
- desktop menu feels intentional
- mobile menu is readable and usable

### 3. Archive/category identity
- archive/category are visually distinct enough from homepage
- scanning for titles/meta is easier
- browsing feels editorial, not generic

### 4. Mobile shell quality
- no clutter collapse
- no obvious spacing breakdown
- useful menu shell
- stable title wrapping and readable rhythm

### 5. Step01 preservation
- Step01 editorial reading quality remains intact
- single-post tone has not regressed
- badge/source/picks styling has not degraded if touched

### 6. Scope discipline
- no pipeline logic touched
- no false live deployment claims
- operator tasks are separated clearly

---

## B4. Step02 Visual Requirements
Final proof should show:
- editorial hierarchy across the shell
- coherent institutional tone
- normalized nav rhythm
- improved archive/category browsing
- preserved long-form readability
- responsive rhythm and spacing

Where long-form text is involved, strong reading rhythm should remain, typically line-height 1.8+ where applicable.

---

## B5. Execution Hard Fail Conditions
Immediate fail if any of the following occurs:
- live deployment is claimed without live proof
- Step01 quality regresses visibly
- generator/pipeline logic touched
- CSS work and operator work are falsely merged
- homepage/nav/archive/mobile improvements are too minor to resolve the audited shell problems
- 08D table and summary contradict each other materially

---

## B6. Final Scoring (100 points)
### 1. Homepage shell upgrade — 20
### 2. Navigation clarity — 15
### 3. Archive/category identity — 15
### 4. Mobile usability — 15
### 5. Step01 regression control — 15
### 6. Scope and safety discipline — 10
### 7. Reporting package quality — 10

### Gate B Decision Bands
- **90–100**: PASS
- **75–89**: PARTIAL PASS / follow-up correction required
- **0–74**: FAIL / rework required

---

## B7. Final Acceptance Review Template
```text
Step02 final acceptance decision:
[PASS / PARTIAL PASS / FAIL]

Summary:
- 
- 
- 

What passed:
1. 
2. 
3. 

What still needs correction:
1. 
2. 
3. 

Operator follow-up items:
1. 
2. 
```

---

## 3. Recommended Reviewer Comments for Step02
Use these when the plan or result is weak.

### If the plan is too vague
> The Step02 package does not yet define a sufficiently closed one-direction shell/IA system. Refine the homepage/navigation/archive direction and resubmit before implementation.

### If CSS and operator tasks are mixed
> Separate CSS/template work from operator/admin work more clearly. The current package blends implementation claims with dashboard/config tasks.

### If live proof is weak
> Final acceptance cannot pass because the package does not prove deployed live state clearly enough. Submit live desktop/mobile screenshots and corrected operator-scope status.

### If Step01 quality regresses
> Step02 may not pass by solving shell issues at the cost of Step01 editorial reading quality. Preserve single-post readability and re-submit proof.

---

## 4. Pair Rule (Permanent)
For future style-track work, deliver documents as a pair:

1. **Style Prompt MD**
2. **Evaluation Sheet MD**

This pair must be created **before** Antigravity implementation work begins.

---

## 5. One-Line Conclusion
Step02 passes only when Macromalt evolves from a merely styled article site into a more coherent **editorial publication shell**, without touching the content-generation pipeline and without regressing Step01 reading quality.
