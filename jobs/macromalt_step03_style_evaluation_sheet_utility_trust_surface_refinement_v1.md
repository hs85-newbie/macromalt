# Macromalt Step03 Style Evaluation Sheet — Utility & Trust Surface Refinement (v1)

## 0. Purpose
This evaluation sheet is the gate for **Step03**.

Step03 is not about article generation or broad product expansion.
It is a presentation-layer refinement phase focused on **utility, trust, and discovery surfaces** after:
- Step01 reading-layer refinement
- Step02 global shell & IA refinement

Use this sheet for:
1. plan-package review
2. execution approval gate
3. final acceptance review

---

## 1. Hard Fail Conditions
Immediate FAIL if any of the following occur:
- article generation logic is modified
- temporal SSOT / verifier / publishing workflow is modified
- Step01 reading quality is visibly degraded
- Step02 masthead/navigation shell is visibly degraded
- plugin-heavy expansion is introduced without strong necessity
- the work adds noisy portal/blog widgets that break brand tone
- source file list and delivery artifact list are mixed together
- rollback path is missing

---

## 2. Mandatory Fixes Required Before Execution Approval
The Step03 plan must satisfy all five items below.

### Mandatory Fix 1 — Exact Step03 Target Surfaces Must Be Closed
The plan must explicitly lock which surfaces are in Step03.
Examples:
- about page identity block
- footer utility layer
- archive/category meta rhythm
- breadcrumb consistency
- search/empty states
- pagination

Do not leave the scope as a vague basket of possibilities.

### Mandatory Fix 2 — Any New Copy/Labels Must Be Locked
If Step03 introduces any front-end copy, labels, section headings, footer identity text, or disclosure microcopy, these must be finalized as single locked choices.
No example text.
No open alternatives.

### Mandatory Fix 3 — Implementation Method Must Be Singular and Consistent
If structural work is required, the plan must pick one safe method and stick to it.
Examples:
- CSS-only
- child-theme hooks/functions
- template override

Mixed implementation approaches without a clear primary strategy are not acceptable.

### Mandatory Fix 4 — CSS / Structural / Operator Scope Must Be Reclassified Cleanly
The component map must explicitly separate:
- CSS-only
- hook/template-required
- operator-config-required
- excluded/not recommended

### Mandatory Fix 5 — Reporting Standard Must Be Pre-Bound
The plan must already commit to the 08A~08E reporting package and identify the screenshots needed for final proof.

---

## 3. Priority 1 / 2 / 3 Review Focus

### Priority 1
Lock the exact Step03 surfaces and any new microcopy/labels into one final set.

### Priority 2
Choose one structural implementation path only.

### Priority 3
Protect Step01 and Step02 from regression and explicitly show how that will be verified.

---

## 4. Plan Review Score (100)

### A. Scope Precision — 25
- 0–10: vague / over-broad
- 11–18: partially scoped
- 19–25: exact surfaces clearly locked

### B. Layer Separation — 20
- 0–8: mixed responsibilities
- 9–14: mostly separated
- 15–20: CSS / structure / operator clearly separated

### C. Brand Continuity — 20
- 0–8: risks breaking Step01/02 tone
- 9–14: generally aligned
- 15–20: tightly aligned with existing editorial system

### D. Technical Safety — 20
- 0–8: unclear rollback / risky changes
- 9–14: acceptable but loose
- 15–20: rollback-safe and implementation-consistent

### E. Reporting Readiness — 15
- 0–5: weak proof planning
- 6–10: partial reporting readiness
- 11–15: 08A~08E proof path clearly planned

---

## 5. Execution Approval Threshold
- **PASS / APPROVE**: 85+
- **PARTIAL / REVISE**: 70–84
- **FAIL**: below 70

All 5 mandatory fixes must be satisfied regardless of score.

---

## 6. Final Acceptance Review Checklist
After implementation, verify the following.

### 6A. Live Proof
- real desktop screenshots exist
- real mobile screenshots exist
- required Step03 utility/trust surfaces are visible in proof

### 6B. Report Integrity
- 08A has no placeholder or deployment-pending language
- 08B matches actual modified files
- 08C proves `generator.py` and `styles/tokens.py` remain untouched
- 08D operator status table and summary do not contradict each other
- 08E final status matches actual proof

### 6C. Visual Quality
- utility surfaces feel editorial and restrained
- archive/category/search/about/footer do not look default WordPress
- metadata density is readable and calm
- breadcrumb / pagination / utility links are visually coherent
- mobile utility layer remains readable

### 6D. Regression Safety
- Step01 reading layer remains intact
- Step02 shell/IA remains intact

---

## 7. Reviewer Output Template
Use the following structure in the review.

### Verdict
- PASS / APPROVE
- PARTIAL / REVISE
- FAIL

### Summary
- one paragraph on whether Step03 is ready

### Mandatory Fixes Status
- Fix 1:
- Fix 2:
- Fix 3:
- Fix 4:
- Fix 5:

### Priority Review
- Priority 1:
- Priority 2:
- Priority 3:

### Remaining Corrections
- list only if needed

---

## 8. Pair Rule
For Step03 and later, always provide and maintain this pair together:
- StepXX style prompt MD
- StepXX evaluation sheet MD
