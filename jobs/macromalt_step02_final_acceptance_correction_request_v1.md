# Macromalt Step02 — Final Acceptance Correction Request v1

## Purpose
This request is **not** asking for a new implementation.
The Step02 implementation appears substantially complete, but the **final acceptance package is not yet internally consistent**.
Please correct the final reporting package so that it can be accepted without ambiguity.

This correction request follows the Step02 QA requirements for:
- locked branding copy,
- homepage-only masthead scope,
- archive identity,
- mobile compact header,
- operator final-state verification,
- and final deliverables `08A~08E`. fileciteturn46file7

It also follows the WordPress style-track operating principle that final QA must verify desktop/mobile behavior, archive distinction, badge consistency, readability, and regression safety before closure. fileciteturn46file8

---

## Current Review Result
**Implementation:** PASS  
**Live-shell activation likelihood:** HIGH  
**Final acceptance package:** HOLD  
**Required action:** Repackage and correct the final Step02 proof documents.

---

## Mandatory Corrections

### 1) Fix 08A internal contradiction
`08A_DEPLOYED_SCREENSHOT_INDEX.md` currently contains two conflicting verification states.
Only **one** final state may remain.

#### Required correction
- Remove the outdated verification block that says implementation is merely ready for upload.
- Keep only the final live-deployed status block.
- Ensure the document states one unambiguous status only.

#### Final expectation
`08A` must describe the package as **live-deployed and verified**, or **not yet deployed** — never both.

---

### 2) Replace the false/invalid mobile proof in 08A
The current Step02 “mobile” proof is not acceptable as final mobile evidence.
It must be replaced with a **true live mobile screenshot**.

#### Required correction
- Capture a real live mobile screenshot at actual mobile viewport conditions.
- Replace the current Step02 mobile proof image in `08A`.
- Ensure the screenshot visibly demonstrates the compact header and mobile shell behavior required by Step02. fileciteturn46file7

#### Final expectation
The final package must contain:
- live desktop homepage proof,
- live mobile homepage proof,
- live archive/category proof.

---

### 3) Normalize the final menu tree everywhere
The final menu structure is currently inconsistent across the package.
The final accepted package must use **one single authoritative menu tree**.

#### Required correction
- Lock the final menu labels to the **actual live site state**.
- Remove all outdated references to alternate menu versions.
- If `Archive` has been removed by the user, **no Step02 final document may still reference `Archive` as part of the final menu tree**.
- Update all relevant documents and notes to match the actual live navigation.

#### Final expectation
The same final menu tree must match across:
- `08A_DEPLOYED_SCREENSHOT_INDEX.md`
- `08D_OPERATOR_SCOPE_STATUS.md`
- `08E_FINAL_ACCEPTANCE_READY_NOTE.md`
- any related captions or summary text.

---

### 4) Fix 08D internal contradiction
`08D_OPERATOR_SCOPE_STATUS.md` currently mixes “DONE” table entries with language that still reads like operator work is pending.

#### Required correction
- If operator tasks are complete, rewrite the checklist/summary accordingly.
- Remove outdated instructions that still say menu/tagline updates are required.
- Keep the document aligned with the actual live completion state.

#### Final expectation
If Step02 is truly complete, then `08D` must clearly say:
- operator tasks completed,
- final live state aligned,
- remaining operator tasks: none.

If something still remains, then the table must also reflect that.

---

### 5) Fix 08E final acceptance contradiction
`08E_FINAL_ACCEPTANCE_READY_NOTE.md` currently declares live deployment complete while still retaining an `Operator Action Required` section.
That is not acceptable in a final acceptance note.

#### Required correction
- Remove the outdated operator-action block if all operator work is done.
- Or, if operator work remains, downgrade the final status accordingly.
- The executive summary, final status, and action section must all match.

#### Final expectation
`08E` must end in one of two valid ways only:
1. **Final acceptance complete; no remaining operator tasks**, or
2. **Acceptance on hold; remaining operator tasks clearly listed**.

Never both.

---

## What Must Be Resubmitted
Please resubmit the corrected final Step02 package with the following files updated as needed:

1. `08A_DEPLOYED_SCREENSHOT_INDEX.md`
2. `08D_OPERATOR_SCOPE_STATUS.md`
3. `08E_FINAL_ACCEPTANCE_READY_NOTE.md`
4. corrected mobile live screenshot asset
5. any updated screenshot index captions needed for consistency

---

## Acceptance Criteria for Closure
Step02 can be finally accepted only when all of the following are true:

- `08A` has a single final deployment state.
- real mobile live proof is present.
- the final menu tree is identical across all final documents.
- `08D` table and summary no longer conflict.
- `08E` no longer declares completion while also requesting operator action.
- the package remains consistent with Step02 QA expectations for homepage branding, archive identity, mobile compact shell, and operator final-state verification. fileciteturn46file7

---

## Copy-Paste Request to Antigravity
Step02 implementation itself appears substantially complete, but the final acceptance package is not yet acceptable due to internal document contradictions and missing valid mobile live proof.

Revise and resubmit the final package with the following mandatory corrections:
1. remove the conflicting duplicate deployment state in `08A`
2. replace the current Step02 mobile proof with a true live mobile screenshot
3. normalize the final menu tree across `08A`, `08D`, and `08E`
4. rewrite `08D` so the table and summary reflect the same final operator state
5. rewrite `08E` so the final status and operator-action section no longer conflict

Do not re-implement the feature set.
This is a **final proof package correction request**, not a redesign request.
