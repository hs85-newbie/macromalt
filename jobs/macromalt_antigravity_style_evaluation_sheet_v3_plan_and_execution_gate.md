# Macromalt Antigravity Style Evaluation Sheet v3

## Purpose
This document is the official reviewer-side evaluation sheet for the Macromalt WordPress style track.

It must be used in the following operating order:

1. Antigravity drafts the plan package
2. Reviewer validates the plan package
3. Reviewer writes review + evaluation sheet
4. Antigravity revises the plan if required
5. Antigravity performs the actual implementation work
6. Reviewer validates implementation results with the same sheet

This document is intentionally stricter than the implementation-side QA checklist.
It is a reviewer gate, not a self-check list.

---

## Fixed Review Principles

### In-scope
- WordPress presentation layer only
- `styles/wordpress/*.css`
- `theme/child-theme/style.css`
- rollback-safe presentation improvements
- typography
- spacing
- hierarchy
- source box
- analytical badge presentation
- homepage/archive/shell readability improvements
- mobile readability

### Out-of-scope / hard boundary
- article generation logic
- temporal SSOT
- verifier / reviser logic
- publishing gate / slot policy / workflow behavior
- Python quality rules
- LLM prompts outside front-end presentation instructions
- non-presentation pipeline logic

### Core tone target
- premium financial editorial
- restrained luxury
- calm and intelligent
- typography-first
- dense but breathable
- mobile readable
- not like a default WordPress blog
- not like a retail trading portal
- not like a noisy startup media site

---

# Part A. Step01 Plan Package Review Gate

Use this section before Antigravity starts actual file modification.

## A-1. Current review status
- Review 대상: `step01-*` plan package
- Review stage: pre-implementation
- Reviewer verdict options:
  - APPROVED
  - CONDITIONALLY APPROVED
  - REVISE AND RESUBMIT
  - REJECTED

Reviewer verdict: `REVISE AND RESUBMIT`

Reason summary:
The submitted plan package is directionally strong, but it is not yet closed enough for safe implementation. The plan must be tightened before code changes begin.

---

## A-2. Mandatory Fixes — all 5 must be reflected

### Mandatory Fix 1 — Add the missing exact-files deliverable
**Required action**
Create `step01-05_exact_files_to_modify.md` as a dedicated deliverable.

**Why this is mandatory**
The style-track guidance explicitly requires exact file diff targets / changed file list / least-invasive implementation path, and the current uploaded package does not provide this as a dedicated deliverable.

**Must include**
For each target file:
- exact file path
- why it is being modified
- CSS-only / template-required / WP-config-required classification
- rollback impact
- whether parent theme is untouched

**Pass condition**
A standalone `step01-05_exact_files_to_modify.md` exists and closes file-level ambiguity.

---

### Mandatory Fix 2 — Close typography to a single final stack
**Required action**
Revise `step01-02_one_direction_visual_system.md` so typography is no longer open-ended.

**Current issue**
The visual direction is chosen as one direction, but headings/body typography still contains unresolved alternatives such as serif-style *or* high-contrast sans, and body serif *or* sans options.

**Must include**
- final heading font stack
- final body font stack
- fallback stack
- whether external fonts are used or not
- if external fonts are not guaranteed, define a safe system-font fallback-first option
- exact desktop/mobile size logic for H1/H2/H3/body

**Pass condition**
There is one final typography decision only, not multiple stylistic branches.

---

### Mandatory Fix 3 — Reclassify the component map by implementation type
**Required action**
Revise `step01-03_component_map.md` into explicit implementation categories.

**Required categories**
- CSS-only
- template-required
- WordPress admin / config required
- not recommended / remove

**Why this is mandatory**
The current component plan mixes pure styling with text injection / structural / admin-type actions.

**Examples that must be reclassified**
- pseudo-element tagline insertion
- footer credit text addition
- analytical badge span wrapping
- menu/header identity issues

**Pass condition**
Every proposed UI action is classified so implementation scope is unambiguous.

---

### Mandatory Fix 4 — Separate style work from WordPress config / shell setup work
**Required action**
Update the plan package so the following are explicitly separated:
- style task
- template task
- WordPress admin/config task

**Why this is mandatory**
The audit states that the site identity/navigation problem includes missing site title/logo visibility and a menu containing only `Sample Page`. These cannot always be solved by CSS alone.

**Must include**
A short matrix like this:
- issue
- can CSS solve it fully? yes/no
- requires template touch? yes/no
- requires WP admin setting? yes/no
- owner: Antigravity or site operator

**Pass condition**
Homepage/nav/logo/menu issues are no longer treated as if they are automatically solvable through CSS only.

---

### Mandatory Fix 5 — Remove `cost_tracker.py` from this style-track plan
**Required action**
Delete the `python cost_tracker.py` verification line from `step01-04_implementation_plan.md`.

**Why this is mandatory**
This track is WordPress presentation-only. Referencing unrelated pipeline-side verification muddies the boundary and weakens separation discipline.

**Pass condition**
The implementation plan contains only presentation-layer verification appropriate to this track.

---

## A-3. Priority feedback to send back to Antigravity

These are the top 3 feedback items and must remain visible even if the full mandatory-fix section exists.

### Priority 1
Add `step01-05_exact_files_to_modify.md` as a dedicated deliverable.

### Priority 2
Close typography to one final stack and remove open-ended font alternatives.

### Priority 3
Reclassify the component map into:
- CSS-only
- template-required
- WordPress config/admin required
- remove / not recommended

---

## A-4. Suggested resend instruction to Antigravity

Use the following resend instruction:

```text
Revise the Step01 plan package before implementation.

You must fix all 5 mandatory review items below:
1. Add `step01-05_exact_files_to_modify.md` as a dedicated deliverable.
2. Close typography to one final stack; do not leave serif/sans alternatives open.
3. Reclassify `step01-03_component_map.md` into CSS-only / template-required / WordPress config-required / remove.
4. Separate style work from WordPress config/shell setup work, especially for title/logo/menu/navigation issues.
5. Remove `cost_tracker.py` from `step01-04_implementation_plan.md` because this is presentation-only work.

Also treat the following 3 items as the top priorities:
- Priority 1: exact files deliverable
- Priority 2: final typography stack
- Priority 3: component reclassification

Do not start actual implementation until the revised plan package closes these points.
Return the revised plan package in the same numbered structure.
```

---

## A-5. Step01 plan review scoring

### Hard Fail conditions
Any of the following is an automatic fail:
- touches generation logic or pipeline logic
- mixes style work and pipeline verification
- does not provide rollback-safe implementation structure
- leaves implementation scope ambiguous at file level
- treats WordPress config issues as solved purely by styling without acknowledging limits

### Scoring (100 points)

#### 1) Scope discipline — 25 pts
- clearly respects presentation-only boundary
- no pipeline contamination
- no generator/verifier/gate intrusion

Score: `__/25`

#### 2) Direction clarity — 20 pts
- one visual direction only
- no unresolved typography branches
- clear tone language

Score: `__/20`

#### 3) Implementation safety — 20 pts
- child-theme safe
- rollback-safe
- exact change surface defined

Score: `__/20`

#### 4) Component realism — 15 pts
- CSS-only vs template/config separated
- no pseudo-magic solutions hiding structural work

Score: `__/15`

#### 5) Verification quality — 10 pts
- desktop/mobile checks are relevant
- regression checks are meaningful for presentation layer

Score: `__/10`

#### 6) Documentation completeness — 10 pts
- audit
- visual system
- component map
- implementation plan
- exact files
- rollback
- QA

Score: `__/10`

### Step01 plan verdict rubric
- 90–100: APPROVED
- 75–89: CONDITIONALLY APPROVED
- 60–74: REVISE AND RESUBMIT
- below 60: REJECTED

Recommended current verdict: `REVISE AND RESUBMIT`

---

# Part B. Implementation Result Review Gate

Use this section after Antigravity performs the actual style work.

## B-1. Required result package
Antigravity must provide all of the following:

1. changed file list
2. code diff or patch summary
3. before/after screenshots
4. desktop review proof
5. mobile review proof
6. regression notes
7. rollback confirmation
8. final self-check against QA checklist

---

## B-2. Implementation hard fail conditions
Any of the following is automatic FAIL:
- `generator.py` touched
- `styles/tokens.py` touched without explicit approval
- LLM prompt / research / verification / gate logic touched
- parent theme modified without clear necessity and documentation
- visual regression on core article rendering
- horizontal overflow on mobile
- badge/source block readability regresses

---

## B-3. Implementation scoring (100 points)

### 1) Boundary safety — 20 pts
- no forbidden file touched
- no pipeline contamination

Score: `__/20`

### 2) Typography & reading experience — 20 pts
- H1/H2/H3 hierarchy improved
- body reading comfort improved
- spacing rhythm improved
- long-form readability improved

Score: `__/20`

### 3) Component quality — 15 pts
- analytical badges premium and legible
- source box institutional and readable
- callout / picks box coherent

Score: `__/15`

### 4) Site shell refinement — 15 pts
- header/footer/nav feel less default
- archive/list rhythm improves
- homepage shell feels more intentional

Score: `__/15`

### 5) Mobile readability — 15 pts
- no overflow
- headings scale correctly
- badges wrap correctly
- source box remains readable
- menu remains usable

Score: `__/15`

### 6) Rollback safety & documentation — 15 pts
- rollback instructions remain valid
- changed file list is exact
- visual impact summary is clear

Score: `__/15`

### Implementation verdict rubric
- 90–100: PASS
- 75–89: PARTIAL PASS
- 60–74: FAIL — revise and re-run
- below 60: FAIL — rollback recommended

Final score: `__/100`
Final verdict: `PASS / PARTIAL PASS / FAIL`

---

# Part C. Reviewer Notes Template

## 1. Summary
- Overall assessment:
- Brand fit:
- Safety assessment:

## 2. What improved
- 
- 
- 

## 3. What remains weak
- 
- 
- 

## 4. Must-fix before acceptance
- 
- 
- 

## 5. Optional next-pass refinements
- 
- 
- 

---

# Part D. Pairing Rule for Future Deliverables

From now on, every style-track delivery should be provided as a pair:

1. **Style Prompt MD**
   - the instruction document to Antigravity / front-end agent
2. **Evaluation Sheet MD**
   - the reviewer-side scoring / verdict / hard-fail / evidence document

And the operating flow should remain fixed as:

1. Antigravity plan drafting
2. reviewer validation
3. review + evaluation sheet writing
4. Antigravity execution
5. result review using the paired evaluation sheet

This rule should be treated as the default operating standard for the Macromalt WordPress style track.
