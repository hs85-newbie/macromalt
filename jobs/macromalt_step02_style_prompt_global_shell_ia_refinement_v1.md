# Macromalt Step02 Style Prompt — Global Shell & IA Refinement (v1)

## 0. Mission
You are working on **Macromalt Step02** of the WordPress style/presentation track.

**Step01 is already complete and live.**
Step02 is a **new front-end refinement track** focused on the **global shell, homepage structure, navigation clarity, archive/category identity, and mobile browsing readability**.

This is **not** a content-generation phase.
This is **not** a pipeline phase.
This is **not** a verifier/gate phase.

---

## 1. Fixed Separation Rules
This work must remain fully separated from the article-generation pipeline.

### Do NOT modify
- article generation logic
- temporal SSOT logic
- verifier / reviser logic
- publishing workflow or slot policy
- LLM prompts for article generation
- research policy / content quality logic
- `generator.py`
- `styles/tokens.py` unless a change is absolutely unavoidable and explicitly justified

### Scope in
- homepage shell / front-page presentation
- site identity presentation
- global header / navigation / menu shell
- archive / category / list-page visual identity
- mobile navigation and shell readability
- child-theme safe CSS / template overrides
- reader-facing visual UX only

### Scope out
- article rewriting
- factual/temporal validation logic
- publishing automation
- backend content structures not required for presentation
- plugin-based redesign unless absolutely necessary and justified

---

## 2. Why Step02 Exists
Step01 improved the editorial reading layer, but the remaining site-level issues were already identified:

- homepage identity was weak
- header/nav felt sparse
- only “Sample Page” style navigation existed
- archive/category pages felt too similar to homepage
- mobile navigation had low utility
- the site still needed a stronger “brand entrance” and IA feel

Step02 exists to solve those remaining **site shell and browsing structure** issues.

---

## 3. Brand Direction
Macromalt must feel like:
- a premium financial editorial product
- a restrained luxury briefing environment
- calm, intelligent, selective, readable
- dense but breathable
- typography-first
- mobile-readable

Macromalt must **not** feel like:
- a generic WordPress blog
- a noisy news portal
- a startup landing page
- a retail trading app
- a crypto-style media site

Allowed mood:
- subtle institutional brief
- subtle private-briefing / whisky-bar restraint
- elegant, understated authority

---

## 4. Step02 Primary Goal
Create a **site-level presentation system** that makes Macromalt feel like a coherent editorial publication, not just a collection of styled articles.

The highest-priority outcomes are:
1. a stronger homepage shell
2. clearer navigation structure
3. distinct archive/category browsing identity
4. better mobile browsing experience
5. tighter site-wide brand consistency

---

## 5. Fixed Step02 Workstreams
You must work in the following order.
Do **not** skip directly to implementation.

### Phase A — Plan Package First
Create the Step02 plan package before touching implementation.

Required plan deliverables inside:
`docs/40_design/Step02/`

1. `step02-01_current_state_audit.md`
2. `step02-02_one_direction_visual_system.md`
3. `step02-03_component_map.md`
4. `step02-04_implementation_plan.md`
5. `step02-05_exact_files_to_modify.md`
6. `step02-06_rollback_plan.md`
7. `step02-07_QA_CHECKLIST.md`

### Phase B — Wait for Review Gate
After the plan package is complete, stop.
Do not implement until the plan is reviewed and approved.

### Phase C — Execute Approved Implementation
Only after approval, implement the Step02 work.

### Phase D — Submit Final Verification Package
After implementation, submit the 5-document verification package.

---

## 6. One-Direction Rule
Because this track may be executed with a fast model, you must avoid open-ended brainstorming.

### Required
- choose **one** direction only
- choose **one** homepage shell direction only
- choose **one** navigation tone only
- choose **one** archive/category identity direction only
- choose **one** mobile shell direction only

### Forbidden
- presenting 3 competing visual systems
- leaving typography or IA decisions open-ended
- proposing vague “optional directions” without final selection

You may mention alternatives briefly in notes, but the plan must commit to **one final direction**.

---

## 7. Step02 Design Scope in Detail

### 7.1 Homepage Shell
Improve the homepage as a **brand entrance**, not a default post list.

Focus on:
- hero / intro region
- brand tagline or brief editorial intro
- curated section structure
- separation between homepage shell and raw article feed
- visual calm and hierarchy

Do not turn it into a flashy landing page.

### 7.2 Global Header / Navigation
Improve:
- site identity visibility
- nav spacing and clarity
- menu usefulness
- mobile hamburger readability
- search visibility only if it improves actual UX

The navigation should feel deliberate and editorial.

### 7.3 Archive / Category Identity
Improve:
- distinction from homepage
- list rhythm
- metadata density
- scanability
- category / series / briefing identity

Archive pages should feel like curated browsing surfaces, not generic duplicates of home.

### 7.4 Mobile Shell
Improve:
- header compactness
- nav clarity
- title wrapping
- spacing rhythm
- touch comfort
- archive readability

Mobile should remain highly readable without clutter.

### 7.5 Brand Identity Surface
If safe and presentation-only:
- refine title/byline/descriptor display
- improve institutional/editorial tone
- normalize identity language

Do not rewrite article content.

---

## 8. Safe Override Preference
Prefer the least invasive path.

### Preferred
- `theme/child-theme/style.css`
- child-theme safe template overrides
- existing separated WordPress CSS layers
- minimal markup changes only if clearly required for presentation

### Avoid unless necessary
- parent theme edits
- plugin dependency
- JS-heavy solutions
- fragile one-off hacks

---

## 9. Exact Step02 Questions You Must Answer in the Audit
Your audit must explicitly answer all of these:

1. Does the homepage now feel like a brand entrance or still like a blog index?
2. Is the site identity visible and credible?
3. Is the top navigation meaningful on desktop?
4. Is the mobile navigation actually useful?
5. Are homepage, archive, and category pages sufficiently distinct?
6. Is archive scanning easy enough for recurring readers?
7. Does the current shell support “briefing / deep dive / series” style browsing?
8. Which issues are CSS-only?
9. Which issues require template changes?
10. Which issues require WordPress admin/operator actions?

---

## 10. Required Deliverable Quality Standard
Each Step02 plan file must be concrete.

### `step02-01_current_state_audit.md`
Must identify real homepage/nav/archive/mobile weaknesses.
No generic praise.

### `step02-02_one_direction_visual_system.md`
Must define one direction only.
Must include:
- homepage shell tone
- navigation tone
- archive/category tone
- mobile shell tone
- typography stance if touched
- background / contrast stance if touched

### `step02-03_component_map.md`
Must classify all proposed work into:
- CSS-only
- template-required
- WordPress Admin / Operator required
- not recommended / remove

### `step02-04_implementation_plan.md`
Must separate implementation order clearly.
Must identify risk level and rollback points.

### `step02-05_exact_files_to_modify.md`
Must list every target file with:
- purpose
- reason
- impact area
- rollback ease
- whether it is CSS / template / admin-config related

### `step02-06_rollback_plan.md`
Must provide a realistic rollback path.

### `step02-07_QA_CHECKLIST.md`
Must include desktop/mobile/home/archive/category/nav checks.
Must also include zero-edit safety checks for `generator.py` and `styles/tokens.py`.

---

## 11. Execution Constraints
When implementation starts:

### Must do
- maintain Step01 gains
- preserve premium editorial tone
- avoid breaking single-post readability
- keep archive/category/home visually related but not identical
- keep rollback easy
- document every changed file

### Must not do
- regress Step01 typography quality
- create flashy landing-page hero blocks
- use loud gradients or startup-style cards
- bloat the site with unnecessary plugins
- mix operator/admin tasks into CSS claims

---

## 12. Required Final Verification Package
After implementation, provide the following 5-document verification package inside:
`docs/40_design/Step02/`

### 1. `08A_DEPLOYED_SCREENSHOT_INDEX.md`
Must include:
- Homepage desktop/mobile live screenshots
- Single post desktop/mobile live screenshots if affected by regression risk
- Archive/category desktop/mobile live screenshots
- If deployment is blocked, label clearly as `Pending Sync` and provide target visuals separately

### 2. `08B_MODIFIED_FILE_DIFF_SUMMARY.md`
Must include every modified file with:
- Purpose
- Key Changes
- Impact
- Rollback Ease
- Prefer unified diff or clear before/after blocks

### 3. `08C_ZERO_EDIT_SAFETY_PROOF.md`
Must prove:
- `generator.py` untouched
- `styles/tokens.py` untouched
- using `git status` or `git diff [file]`

### 4. `08D_OPERATOR_SCOPE_STATUS.md`
Must clearly separate:
- agent CSS/template work
- operator WP-admin settings

Use status labels:
- `DONE`
- `DONE_BY_OPERATOR`
- `NOT_DONE_OPERATOR_PENDING`
- `NOT_REQUIRED`
- `PARTIAL`

### 5. `08E_FINAL_ACCEPTANCE_READY_NOTE.md`
Must summarize:
- mandatory fixes completion
- acceptance readiness
- remaining operator actions if any

### Assets folder
Store screenshots in:
`docs/40_design/Step02/assets/`

---

## 13. Visual Requirements for Final Acceptance
Final proof must show:
- homepage with clear editorial hierarchy
- distinct shell identity versus generic blog index
- normalized navigation rhythm
- improved archive/category scanability
- mobile-readable shell
- preserved Step01 editorial typography quality
- normalized badges / picks / source box if touched by regression checks
- comfortable reading rhythm (target long-form line-height remains strong, typically 1.8+ where applicable)

---

## 14. Hard Fail Conditions
Any of the following is an immediate fail:
- touching article generation logic
- touching verifier / gate / temporal logic
- touching `generator.py` without explicit approval
- touching `styles/tokens.py` without explicit approval and justification
- proposing multiple unresolved directions instead of one
- confusing CSS work with operator/admin work
- claiming live deployment without deployed proof
- breaking Step01 single-post editorial quality

---

## 15. Implementation Strategy Preference
Preferred strategy for Step02:
1. audit current live shell
2. choose one direction
3. classify CSS/template/operator tasks
4. create exact file map
5. wait for review
6. implement safe overrides
7. submit verification package

---

## 16. Final Command
Act as a **senior WordPress front-end styling engineer** working on a premium editorial site.

Your job in Step02 is to make Macromalt feel like a more coherent **editorial publication shell** through homepage, navigation, archive/category, and mobile shell refinement.

Stay inside presentation scope only.
Work in a rollback-safe way.
Do plan package first.
Stop for review.
Then execute only after approval.
