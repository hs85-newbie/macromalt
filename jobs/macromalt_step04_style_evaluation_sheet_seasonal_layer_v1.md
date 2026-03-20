# Macromalt Step04 Style Evaluation Sheet — Seasonal Layer (v1)

## 0. Purpose
This evaluation sheet is for reviewing Step04 **Seasonal Layer** planning, implementation, and final acceptance.

Step04 is successful only if it adds a subtle monthly atmosphere **without damaging** the already-approved institutional shell from Step01–Step03.

---

## 1. Review Workflow (Fixed)
Use this order.

1. Antigravity submits Step04 plan package
2. Review against this evaluation sheet
3. Mandatory corrections are issued if needed
4. Execution approval is granted only after plan quality is sufficient
5. Antigravity implements Step04
6. `08A~08F` reporting package is submitted
7. Final acceptance review is performed

---

## 2. Hard Fail Conditions
If any item below is true, the package fails immediately.

- Seasonal layer changes IA, menu structure, or core shell hierarchy
- Disclosure box logic, scope, or trust wording is broken
- Seasonal styling reduces readability or contrast
- Seasonal implementation depends on live weather API for core switching
- Monthly switching still requires manual editing
- External plugin dependency is introduced without strong justification
- Non-style pipeline files are modified
- Step01, Step02, or Step03 approved surfaces regress materially

---

## 3. What Must Be Preserved
The following are protected assets from prior steps.

### Step01 Protected
- editorial typography hierarchy
- article reading width and spacing rhythm
- institutional badge and source-box legibility

### Step02 Protected
- homepage masthead shell
- primary navigation structure
- archive/category shell distinction
- mobile header compactness

### Step03 Protected
- disclosure box logic and trust tone
- mono utility system
- footer trust layer
- search/archive utility refinements

Any regression in protected assets counts heavily against approval.

---

## 4. Mandatory Fix Areas for Step04
The reviewer must explicitly check these areas.

### A. Seasonal Design Discipline
- Is the seasonal layer subtle rather than thematic/noisy?
- Does each month still feel like the same brand?
- Are there no gimmicky weather visuals or campaign-style motifs?

### B. Deterministic Automation
- Is switching based on month, not manual editing?
- Is the switching logic deterministic and simple?
- Does it work without external APIs?

### C. Token System Closure
- Are all 12 monthly presets defined?
- Are preset IDs locked and consistent?
- Are variable surfaces clear and limited?

### D. Scope Protection
- Are typography, disclosure, IA, and trust layers preserved?
- Are only allowed presentation surfaces seasonally affected?

### E. Reporting Proof Quality
- Does the final package distinguish live-state proof vs deterministic simulation?
- Does `08F_SEASONAL_SWITCH_PROOF.md` clearly prove the switching logic?

---

## 5. Plan-Phase Approval Checklist
Approve execution only if all items below are satisfied.

- [ ] `step04-01_current_state_audit.md` explains why a seasonal layer is needed and what must remain fixed
- [ ] `step04-02_one_direction_visual_system.md` locks one seasonal concept only
- [ ] `step04-03_component_map.md` separates CSS / Hook / Operator / Excluded clearly
- [ ] `step04-04_implementation_plan.md` chooses one technical method only
- [ ] `step04-05_exact_files_to_modify.md` is precise and rollback-aware
- [ ] `step04-06_rollback_plan.md` is realistic and fast
- [ ] `step04-07_QA_CHECKLIST.md` includes regression checks against Step01–03
- [ ] `step04-08_seasonal_token_matrix.md` defines all 12 preset systems explicitly

If any of the above remain open-ended, execution approval should be withheld.

---

## 6. Mandatory Correction Template (Use When Needed)
When the first plan is insufficient, corrections should be structured in this format.

### Must-Fix 1
Lock the exact monthly preset naming, variable surface, and affected UI surfaces.

### Must-Fix 2
Lock the automation method to one deterministic implementation pattern.

### Must-Fix 3
Explicitly separate protected shell surfaces from seasonally variable surfaces.

### Must-Fix 4
Provide regression-safe QA against Step01, Step02, and Step03.

### Must-Fix 5
Clarify whether any operator action is required at all, and if yes, exactly what.

---

## 7. Priority 1 / 2 / 3 Template
These should be used in review responses.

### Priority 1
Close all open seasonal design choices into one locked system.

### Priority 2
Close the automation method into one deterministic, no-API, low-maintenance method.

### Priority 3
Show explicit regression protection for typography, IA, disclosure, and trust surfaces.

---

## 8. Scoring Grid (100 Points)

### A. Brand Continuity — 25
- Preserves Macromalt institutional identity
- Seasonal layer is subtle and premium

### B. Technical Stability — 20
- Deterministic month logic
- No fragile dependencies
- Fast rollback path

### C. Seasonal Token Quality — 15
- 12-month system is coherent
- Variables are controlled and usable

### D. Regression Safety — 20
- No damage to Step01–03 surfaces
- Mobile and desktop remain stable

### E. Reporting Quality — 20
- `08A~08F` package is complete
- proof language is precise
- live vs simulated proof is clearly separated

### Suggested Interpretation
- **90–100**: Approve
- **75–89**: Conditional approval
- **0–74**: Rework required

---

## 9. Execution-Phase Acceptance Checklist
Final acceptance requires all of the following.

- [ ] Live or clearly-labeled proof for current month is provided
- [ ] At least 3 month-state comparisons are documented in `08F`
- [ ] Monthly switch logic is demonstrated clearly
- [ ] No operator-pending ambiguity remains in `08D`
- [ ] ZIP/package paths are consistent across reports
- [ ] `generator.py`, `styles/tokens.py`, `publisher.py` remain untouched
- [ ] Article readability remains premium on desktop and mobile
- [ ] Disclosure box remains readable under sampled seasonal states
- [ ] Homepage shell still looks like Macromalt, not a campaign page

---

## 10. Reporting Standard for Step04
Step04 final package must include:

- `08A_DEPLOYED_SCREENSHOT_INDEX.md`
- `08B_MODIFIED_FILE_DIFF_SUMMARY.md`
- `08C_ZERO_EDIT_SAFETY_PROOF.md`
- `08D_OPERATOR_SCOPE_STATUS.md`
- `08E_FINAL_ACCEPTANCE_READY_NOTE.md`
- `08F_SEASONAL_SWITCH_PROOF.md`

### Required Asset Expectations
- desktop home current-month state
- mobile home current-month state
- one single-post state showing disclosure readability
- one archive/category state showing badge/meta readability
- at least 3 month comparison proofs

---

## 11. Standard Reviewer Output Format
When reviewing Step04, use this output structure.

### Verdict
- APPROVE / CONDITIONAL APPROVAL / HOLD / FAIL

### Good
- 2–5 concise items

### Must Fix
- up to 5 items

### Priority 1 / 2 / 3
- short actionable instructions

### Final Instruction
- proceed to implementation / resubmit plan / resubmit final package

---

## 12. Pair Rule (Fixed)
For Macromalt style work, always keep these together:
- Step04 Style Prompt MD
- Step04 Evaluation Sheet MD

Any new plan submission should be reviewed against this paired standard automatically.
