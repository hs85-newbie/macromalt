# Macromalt Step03 Style Prompt — Utility & Trust Surface Refinement (v1)

## 0. Role
You are working on the **Macromalt WordPress Style Track — Step03**.

This phase happens **after**:
- Step01: single-post reading layer refinement
- Step02: global shell & IA refinement

Your job in Step03 is to refine the **utility and trust-facing surfaces** of the WordPress site so that Macromalt reads less like a styled blog and more like a finished editorial research product.

---

## 1. Fixed Scope
Work only inside the **WordPress presentation layer**.

Allowed:
- `styles/wordpress/*.css`
- `theme/child-theme/*`
- minimal rollback-safe presentation-oriented PHP/hooks only when unavoidable
- archive/category/search/about/footer/breadcrumb/byline/disclosure-facing rendering

Do **NOT** modify:
- article generation logic
- temporal SSOT
- verifier/reviser logic
- publishing workflow
- slot policy
- research/content quality policy
- Python output rules unrelated to presentation
- generator pipeline behavior

This remains a **presentation-only track**.

---

## 2. Step03 Goal
Step03 should refine the parts of the site that shape **credibility, discovery, and completion feel** after the reading layer and shell are already in place.

The target result is:
- users can understand the site's structure more easily
- trust cues feel intentional and editorial, not default WordPress
- utility surfaces feel coherent with the Step01/Step02 visual system
- mobile discovery is efficient and not cluttered

---

## 3. One Direction Only
Use exactly **one** direction:

## Direction: "The Institutional Utility Layer"
The site should feel like a research publication with quiet operational maturity.

Characteristics:
- understated trust signals
- clean metadata presentation
- calm utility components
- no widget noise
- no generic portal clutter
- no aggressive CTA patterns

Do not brainstorm multiple directions.
Do not provide alternatives unless required by a hard technical constraint.

---

## 4. Primary Work Areas

### A. Trust Surfaces
Refine the surfaces that answer: “What is this site, and why should I trust it?”

Candidate targets:
- About page / site identity block
- footer editorial identity
- copyright / byline / publication context
- source methodology summary block if already present in theme layer
- disclosure / note box presentation if already present in the front-end layer

### B. Discovery Surfaces
Refine the surfaces that answer: “How do I find the right material quickly?”

Candidate targets:
- archive cards and archive meta rhythm
- category/taxonomy pages
- breadcrumb styling consistency
- search results page if available
- empty/no-result states if available
- pagination styling

### C. Editorial Utility Components
Refine utility-facing front-end details so they match the institutional system.

Candidate targets:
- date/category/byline/meta block rhythm
- category badges across list views
- read-more / continue-reading patterns
- list spacing and scanning density
- footer utility links

### D. Mobile Utility Layer
Refine mobile browsing efficiency.

Candidate targets:
- search result readability
- archive item spacing on narrow screens
- breadcrumb wrapping
- metadata overflow prevention
- footer link density

---

## 5. Explicit Non-Goals
Do not spend this phase on:
- rewriting article content
- adding motion-heavy interaction
- adding sliders/carousels
- adding generic stock-blog widgets
- adding plugin-heavy features unless absolutely unavoidable
- redesigning Step01 reading typography from scratch
- redesigning Step02 masthead/navigation from scratch

---

## 6. Required Planning Deliverables
Create the plan package in:
`docs/40_design/Step03/`

Required documents:
1. `step03-01_current_state_audit.md`
2. `step03-02_one_direction_visual_system.md`
3. `step03-03_component_map.md`
4. `step03-04_implementation_plan.md`
5. `step03-05_exact_files_to_modify.md`
6. `step03-06_rollback_plan.md`
7. `step03-07_QA_CHECKLIST.md`

---

## 7. Planning Rules
- Lock all major labels/copy if Step03 introduces them.
- Separate **CSS-only / hook-template / operator-config** clearly.
- Do not mix deployment artifacts into source file lists.
- Prefer child-theme safe implementation.
- If a utility surface does not exist in the current site, do not invent a large new product feature. Keep the work proportional.
- Every structural change must have a rollback path.

---

## 8. Required Execution Reporting Standard
After implementation, submit the 5-document verification package in:
`docs/40_design/Step03/report/`

Required:
1. `08A_DEPLOYED_SCREENSHOT_INDEX.md`
2. `08B_MODIFIED_FILE_DIFF_SUMMARY.md`
3. `08C_ZERO_EDIT_SAFETY_PROOF.md`
4. `08D_OPERATOR_SCOPE_STATUS.md`
5. `08E_FINAL_ACCEPTANCE_READY_NOTE.md`

Assets go in:
`docs/40_design/Step03/report/assets/`

---

## 9. Verification Expectations
The final proof must show:
- utility/trust surfaces align with Step01 and Step02 visual tone
- archive/category/search/about/footer surfaces no longer feel default WordPress
- desktop/mobile consistency
- no regression to Step01 reading quality
- no regression to Step02 masthead/navigation shell
- `generator.py` and `styles/tokens.py` remain untouched unless explicitly approved

---

## 10. Final Instruction
Start with the plan package only.
Do not jump directly to implementation.
Do not claim final completion until live-state proof is captured.
