# Macromalt Style Track Reporting Standard (v1)

After any style-related implementation, the following 5-document verification package must be provided in the corresponding `StepXX` folder within `docs/40_design/`.

## 1. Required Deliverables
1.  **08A_DEPLOYED_SCREENSHOT_INDEX.md**:
    - Must include "Live State" screenshots (Homepage, Single Post, Archive) for both Desktop and Mobile.
    - If deployment is blocked or pending, clearly label as "Pending Sync" and provide "Target Visuals" (injected/simulated) as logic evidence.
2.  **08B_MODIFIED_FILE_DIFF_SUMMARY.md**:
    - Detailed summary of every modified file.
    - Fields: Purpose, Key Changes, Impact, Rollback Ease.
    - Prefer unified diffs or clear before/after code blocks.
3.  **08C_ZERO_EDIT_SAFETY_PROOF.md**:
    - Proof that non-target files (`generator.py`, `tokens.py`) remain untouched.
    - Evidence: `git status` or `git diff [file]`.
4.  **08D_OPERATOR_SCOPE_STATUS.md**:
    - Separation of CSS work (Agent) from WP-Admin settings (Operator).
    - Status labels: `DONE`, `DONE_BY_OPERATOR`, `NOT_DONE_OPERATOR_PENDING`, `NOT_REQUIRED`, `PARTIAL`.
5.  **08E_FINAL_ACCEPTANCE_READY_NOTE.md**:
    - Executive summary and checklist of mandatory fixes from the style evaluation sheet.

## 2. Folder Structure
- Root: `docs/40_design/StepXX/`
- Assets: `docs/40_design/StepXX/assets/` (Store all .png screenshots here).

## 3. Visual Requirements
- Final proof must show **Editorial Hierarchy** (Georgia/Sans-Serif stack).
- Components (Badges, Picks Boxes) must be normalized.
- Responsive rhythm must be verified (Line-height 1.8+, Spacing).
