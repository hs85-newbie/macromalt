# Macromalt Step04 Style Prompt — Seasonal Layer (v1)

## 0. Role
You are working on the **Macromalt WordPress Style Track — Step04: Seasonal Layer**.

This is a **presentation-only** refinement phase that comes **after** Step01 (editorial typography), Step02 (global shell & IA), and Step03 (utility & trust surface).

Your job is **not** to redesign Macromalt.
Your job is to add a **lightweight monthly seasonal skin** on top of the already-approved institutional editorial shell.

---

## 1. Core Goal
Introduce a controlled, elegant, automatically-switching **seasonal layer** that changes the site's atmosphere **by month** while preserving the Macromalt brand.

This must feel like:
- a subtle shift in editorial climate
- a premium institutional publication with seasonal nuance
- calm, intelligent, restrained, and readable

This must **not** feel like:
- a themed campaign site
- a blog template swap
- a holiday microsite
- a weather widget product
- a colorful consumer UI

---

## 2. Non-Negotiable Brand Continuity
The following must remain structurally stable.

### LOCKED / MUST NOT CHANGE
- Georgia-led heading hierarchy
- mono-type utility system from Step03
- disclosure box structure and placement logic
- institutional footer trust layer
- homepage IA / masthead shell from Step02
- archive/list reading rhythm
- article width, paragraph rhythm, spacing logic
- menu structure and operator-owned information architecture
- verification / generation / publishing / temporal logic

### Seasonal Layer MAY Influence Only
- background tint / paper tone
- accent/rule/border tone
- badge tint nuance
- breadcrumb / pagination tonal emphasis
- subtle homepage seasonal subline (optional)
- subtle archive/category label nuance
- optional footer secondary tint

If any seasonal idea threatens readability, hierarchy, trust, or calmness, reject it.

---

## 3. Automation Principle
Use **monthly deterministic switching**, not live weather-reactive switching.

### Required Automation Rule
- The visual season must be chosen from the **current month**.
- The site should switch automatically **without manual monthly editing**.
- Prefer **body class injection + CSS custom properties** over fragile scheduled rewriting.
- Avoid external APIs, remote weather data, or anything that can fail due to network state.

### Preferred Technical Pattern
1. Add a deterministic month-based body class from `functions.php`
   - Example pattern: `macromalt-season-jan-frost`
2. Define seasonal CSS variable sets in child-theme / WordPress style layer
3. Keep the institutional base theme intact
4. Override only seasonal variables and small presentation details

### Strong Preference
- Do **not** build a complex admin UI
- Do **not** introduce a plugin unless absolutely unavoidable
- Do **not** use real-time weather integrations
- Do **not** create layout branching by season

---

## 4. Seasonal System Design Requirement
Create a **12-month seasonal token system** with locked names and tonal intent.

## 4.1 Required Monthly Preset Table (LOCKED)
Use these exact preset identifiers unless there is a compelling technical reason not to.

| Month | Preset ID | Tonal Intent |
|------|-----------|--------------|
| Jan | `jan-frost` | cold paper, disciplined contrast |
| Feb | `feb-ash` | muted late-winter restraint |
| Mar | `mar-thaw` | softened early-spring release |
| Apr | `apr-mist` | airy, pale, intelligent freshness |
| May | `may-sage` | light green-gray calm |
| Jun | `jun-haze` | warm diffuse summer paper |
| Jul | `jul-storm` | denser, moodier macro tension |
| Aug | `aug-amber` | muted dry heat, restrained warmth |
| Sep | `sep-harvest` | composed harvest gold-gray |
| Oct | `oct-oak` | deep editorial autumn restraint |
| Nov | `nov-smoke` | smoke, ash, late-year seriousness |
| Dec | `dec-velvet` | dark winter elegance |

## 4.2 Required Variable Surface
At minimum, define seasonal overrides for:
- `--mm-bg`
- `--mm-bg-alt`
- `--mm-ink`
- `--mm-ink-soft`
- `--mm-rule`
- `--mm-accent`
- `--mm-badge-bg`
- `--mm-badge-text`
- `--mm-link-hover`

You may add more variables only if necessary.

---

## 5. Scope Boundaries

### Allowed Files (Expected)
- `theme/child-theme/functions.php`
- `theme/child-theme/style.css`
- `styles/wordpress/base.css`
- `styles/wordpress/typography.css`
- `styles/wordpress/components.css`

### Untouched Reference Targets
- `generator.py`
- `styles/tokens.py`
- `publisher.py`
- any temporal SSOT or verifier layer

### If Structure Is Needed
Use minimal hook/body-class logic only.
No front-end redesign beyond seasonal presentation.

---

## 6. Required Deliverables (Plan Phase)
Produce the standard StepXX plan package.

1. `step04-01_current_state_audit.md`
2. `step04-02_one_direction_visual_system.md`
3. `step04-03_component_map.md`
4. `step04-04_implementation_plan.md`
5. `step04-05_exact_files_to_modify.md`
6. `step04-06_rollback_plan.md`
7. `step04-07_QA_CHECKLIST.md`

Additional requirement for Step04:
8. `step04-08_seasonal_token_matrix.md`
   - show all 12 monthly presets
   - exact variable values
   - intended affected UI surfaces

---

## 7. Required Deliverables (Execution / Reporting Phase)
Follow the Macromalt reporting standard.

Store reports under:
- `docs/40_design/Step04/`
- assets under `docs/40_design/Step04/assets/`

Required verification package:
1. `08A_DEPLOYED_SCREENSHOT_INDEX.md`
2. `08B_MODIFIED_FILE_DIFF_SUMMARY.md`
3. `08C_ZERO_EDIT_SAFETY_PROOF.md`
4. `08D_OPERATOR_SCOPE_STATUS.md`
5. `08E_FINAL_ACCEPTANCE_READY_NOTE.md`

Additional Step04 proof requirement:
6. `08F_SEASONAL_SWITCH_PROOF.md`
   - proof that monthly switching logic works
   - show at least 3 month states (for example Mar / Jul / Nov)
   - clarify whether proof is live-state or deterministic simulation

---

## 8. QA Expectations
You must explicitly verify:
- no regression to Step01 article readability
- no regression to Step02 masthead / IA shell
- no regression to Step03 disclosure / trust utility layer
- seasonal tint remains readable on desktop and mobile
- badge contrast remains acceptable
- archive cards remain calm and consistent
- disclosure box remains readable under all sampled seasonal presets
- no layout shift when month changes
- no manual admin action is required for monthly switching

---

## 9. Hard Fail Conditions
Your output fails automatically if any of the following occur:
- redesigning the site instead of adding a seasonal layer
- changing disclosure logic/content structure
- changing IA/menu structure
- introducing loud visual themes or heavy decorative assets
- using weather API integration for the core switching logic
- requiring manual monthly edits
- touching generation / verifier / temporal pipeline files
- creating seasonal layouts that reduce contrast or readability

---

## 10. Execution Style
You are using a Flash-class model environment.
That means:
- close all open choices
- do not leave seasonal naming, copy, or technical method ambiguous
- choose one implementation method and justify it
- prefer deterministic simplicity over novelty
- avoid brainstorming multiple alternatives unless explicitly requested

---

## 11. Final Instruction
Implement Step04 as a **quiet seasonal skin system** for Macromalt.
Do not make the site feel different every month.
Make it feel like the same institutional publication under slightly different atmospheric conditions.
