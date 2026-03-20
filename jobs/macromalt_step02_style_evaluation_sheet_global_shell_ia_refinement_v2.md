# Macromalt Step02 Style Evaluation Sheet v2
## Global Shell & IA Refinement — Plan Review Gate

Version: v2  
Scope: Step02 plan-package review (pre-implementation)  
Stage Position: **Plan Review / Gate Before Execution**

---

## 0. Purpose

This evaluation sheet is the **review gate document** for Step02.
It exists to determine whether the Antigravity Step02 plan package is safe and concrete enough to enter real implementation.

This document reflects:
- the Step02 prompt scope,
- the uploaded Step02 plan package,
- the senior review findings,
- the required reporting discipline established in the Macromalt style track.

This gate is stricter than Step01 because Step02 moves beyond CSS-only refinement and introduces **site shell / IA / template / minimal PHP integration**.

---

## 1. Gate Result for Current Step02 Package

**Current Decision: CONDITIONAL APPROVAL**

Interpretation:
- Problem definition is appropriate.
- Direction is appropriate.
- Layer separation is better than before.
- However, the package is **not yet execution-ready** because critical structural and copy decisions remain open.

Implementation must **not begin yet**.
Antigravity must revise and resubmit the Step02 plan package first.

---

## 2. What Is Good in the Current Package

The following are accepted as valid strengths of the current Step02 package:

1. Step02 correctly identifies the remaining site-level problems:
   - homepage lacks brand entrance clarity,
   - navigation utility is weak,
   - archive/category identity is not strong enough,
   - mobile shell needs refinement.

2. The chosen direction, **"The Editorial Masthead"**, is aligned with Step02 goals.

3. The package separates CSS / Template / Operator responsibilities better than Step01.

4. The rollback concept is present and structurally aware of template-level risk.

These strengths are preserved.

---

## 3. Mandatory Fixes Before Execution

The following **five fixes are mandatory**.
Antigravity must address **all five** before implementation approval can be granted.

### Mandatory Fix 1 — Close all brand copy and IA labels as final decisions
The current package still leaves major brand/IA decisions in example form.
This is not acceptable for Step02.

Antigravity must finalize exactly one version of all of the following:
- homepage hero title,
- homepage hero tagline,
- homepage section title(s),
- primary navigation labels,
- mono font stack.

Rules:
- No example wording.
- No “such as / like / 등 / or” wording.
- No alternative menu sets.
- No open typography options.

### Mandatory Fix 2 — Choose exactly one structural implementation method
The current package mixes multiple structural methods:
- `header.php` override,
- `front-page.php`,
- theme hook / `functions.php` injection.

Antigravity must choose **one** primary implementation method for the homepage shell and explain why it is the safest.

Rules:
- Do not mix implementation approaches in the final plan.
- Clearly state the selected method.
- Clearly state which methods were rejected and why.

### Mandatory Fix 3 — Define homepage-only scope vs global-header scope
Step02 is about making the homepage a brand entrance.
The package currently risks leaking homepage masthead behavior into archive/single contexts.

Antigravity must explicitly define:
- what appears on homepage only,
- what appears on all pages globally,
- what appears on archive/category pages only,
- what appears on single posts only.

A scope matrix is required.

### Mandatory Fix 4 — Remove delivery artifact from the “exact files to modify” source list
`wordpress_upload/macromalt-step02.zip` is a deployment artifact, not a source file.
It must be separated from the exact source modification list.

Antigravity must split the file documentation into:
- **source files to modify/create**, and
- **delivery/deployment artifacts**.

### Mandatory Fix 5 — Make operator scope concrete and final-state oriented
The current operator scope is still too abstract for a shell/IA stage.

Antigravity must specify operator-owned items concretely, including:
- final menu tree,
- site description / tagline text,
- breadcrumb activation status,
- favicon status,
- any WP-Admin settings still required after implementation.

Operator scope must not remain at the “menu setup needed” level.

---

## 4. Priority Feedback (Highest Order)

The following are the **priority 1 / 2 / 3** items that must be treated as the first revision targets.

### Priority 1
Finalize the following as one locked final system:
- hero copy,
- tagline,
- homepage section headings,
- primary menu labels,
- mono font stack.

### Priority 2
Choose **one and only one** structural implementation strategy from the following:
- `header.php` override,
- `front-page.php`,
- GeneratePress hook strategy.

The final plan must name one chosen strategy and justify it.

### Priority 3
Separate homepage-only masthead behavior from global header behavior with a page-scope matrix.

---

## 5. Hard-Fail Conditions

If any of the following remain true after resubmission, the Step02 plan must be marked **FAIL** and implementation must not begin.

1. Final hero/menu/tagline language is still example-based.
2. Multiple structural approaches remain mixed in the plan.
3. Homepage-only and global shell scope remain ambiguous.
4. Source modification list still includes deployment archive as a source file.
5. Operator scope remains vague or incomplete.
6. Any plan touches article-generation logic, temporal SSOT, verifier/gate, or unrelated Python pipeline code.
7. Step01 readability or single-post editorial quality is not explicitly protected.

---

## 6. Plan Review Scorecard (100 Points)

### A. Scope Discipline — 20 pts
- Presentation-only scope is preserved: /20
- No pipeline contamination risk: /10
- Step01 preservation explicitly protected: /10

### B. Brand & IA Decision Completeness — 20 pts
- Hero/tagline finalized: /5
- Menu labels finalized: /5
- Homepage section labels finalized: /5
- Font stack finalized: /5

### C. Structural Safety — 25 pts
- Single implementation strategy chosen: /10
- Page-scope matrix completed: /10
- Risk explanation / rejection rationale included: /5

### D. File/Artifact Clarity — 15 pts
- Exact source files list is clean: /5
- Delivery artifacts separated: /5
- Rollback mapping remains valid: /5

### E. Operator Scope Clarity — 10 pts
- Menu tree finalized: /3
- Site description / tagline ownership clear: /2
- Breadcrumb status clear: /2
- Favicon / WP-Admin items clear: /3

### F. QA & Reporting Readiness — 10 pts
- Step02 QA is specific enough: /5
- 08A~08E reporting standard is intact: /5

### Result Bands
- **90–100**: APPROVE
- **75–89**: CONDITIONAL APPROVAL
- **0–74**: FAIL

Execution is only allowed at **APPROVE**.

---

## 7. Required Resubmission Package (Step02 Revision)

Antigravity must resubmit the following revised documents:

1. `step02-02_one_direction_visual_system.md`
   - with final locked copy / labels / font decisions.

2. `step02-03_component_map.md`
   - with one structural strategy only,
   - with a scope matrix for homepage/global/archive/single.

3. `step02-04_implementation_plan.md`
   - with one chosen structure method,
   - with rejected alternatives explicitly named.

4. `step02-05_exact_files_to_modify.md`
   - with deployment ZIP removed from source list,
   - with delivery artifact separated into its own section.

5. `step02-07_QA_CHECKLIST.md`
   - with concrete operator-state checks added where necessary.

---

## 8. Copy-Paste Review Message for Antigravity

Use the following message as-is when returning the review result.

```text
Step02 plan package is directionally strong but not yet execution-ready.
Current decision: CONDITIONAL APPROVAL.
Do not begin implementation yet.

You must revise and resubmit the package.

Mandatory fixes:
1) Finalize hero copy, tagline, homepage section labels, primary menu labels, and mono font stack as one locked final system. Example wording is not allowed.
2) Choose exactly one structural implementation method for the homepage shell / IA layer. Do not mix header.php override, front-page.php, and GeneratePress hook approaches.
3) Provide a page-scope matrix that separates homepage-only masthead behavior from global header behavior, archive/category behavior, and single-post behavior.
4) Remove wordpress_upload/macromalt-step02.zip from the exact source file list and separate it as a delivery/deployment artifact.
5) Make operator scope concrete and final-state oriented, including final menu tree, site description/tagline ownership, breadcrumb status, favicon status, and any WP-Admin items still required.

Priority order:
Priority 1) Lock final copy/IA/font decisions.
Priority 2) Lock one structural method.
Priority 3) Lock page-scope separation.

Resubmit the revised Step02 package after these changes.
```

---

## 9. Acceptance Gate After Resubmission

After Antigravity resubmits, use this simple gate:

### APPROVE
- All 5 mandatory fixes resolved.
- Priority 1/2/3 fully reflected.
- No hard-fail conditions remain.
- Score is 90+.

### CONDITIONAL APPROVAL
- Some improvements made, but one or more mandatory items still partially open.

### FAIL
- Structural ambiguity remains,
- scope contamination appears,
- or execution risk remains too high.

---

## 10. Operating Rule Going Forward

For all future Step02-and-later style work, the review sequence must remain:

1. Antigravity plan package submission
2. Review + evaluation sheet update
3. Revision if needed
4. Execution approval
5. Real implementation
6. 08A–08E verification package
7. Final acceptance review

This order is mandatory.

