You are working on the Macromalt content-quality architecture track.

This is not a cosmetic rewrite task.
Do NOT approach this as:
- cliché removal
- synonym replacement
- “make it sound human”
- stylistic noise injection
- detector gaming

This is a structural editorial-design problem inside a fully automated finance-content pipeline.

==================================================
0. PROJECT CONTEXT YOU MUST RESPECT
==================================================

Macromalt is a branded research engine, not a casual blog.
Its content must feel like a premium financial editorial product:
- dense
- selective
- evidence-backed
- readable
- disciplined
- non-gimmicky

Current pipeline shape:
1. news/research collection
2. Gemini Step1 analysis material generation
3. OpenAI Post1 draft
4. OpenAI Post2 draft
5. Gemini fact-check
6. Gemini revise
7. WordPress publish

Current operating principles:
- prompt/rule correction comes before parameter tuning
- do not treat temperature tuning as the main fix
- validation should be based on actual published output quality
- one article should center one theme
- facts and background_facts should remain separated
- freshness/date discipline is mandatory
- fact / interpretation / forecast boundaries must remain visible
- no recommendation-like investment language

Freshness policy:
- primary support: recent 7 days
- secondary support: up to 30 days
- beyond 30 days: background only, not current market basis

Dedup/repetition context:
- same theme may still be allowed if slot differs and question structure differs
- same theme + same sub-axes + same stock bucket should trigger stronger rotation
- publish history, slot, theme fingerprint, and sub_axes fingerprint should be used as structural constraints

Important:
Your job is NOT to humanize prose cosmetically.
Your job is to redesign the pipeline so the machine performs editorial prioritization before writing.

==================================================
1. THE REAL PROBLEM
==================================================

Why the output often feels AI-like:

The issue is not mainly vocabulary.
The issue is the pipeline’s current cognition pattern:

data collection -> structure -> uniform narration

That tends to produce:
- equal treatment of unequal facts
- weak hierarchy of importance
- “what happened” without strong “why this matters now”
- minimal analytical stance
- repeated paragraph rhythm
- low structural asymmetry
- safe but flat report texture

The writer is currently too close to a serializer:
it receives structured facts and turns them into polished HTML.

As long as the writer receives an almost flat fact bundle,
it will tend to produce an almost flat article.

Therefore:
surface-level expression cleanup is insufficient.

==================================================
2. TARGET STATE
==================================================

Move the architecture from:

structured facts -> writer draft -> verify/revise

to:

structured facts -> editorial plan -> writer draft -> verify/revise enforcement

The key change:
Before writing begins, the system must decide:
- what matters most
- what becomes background
- what is omitted
- what stance is justified
- what narrative shape fits this slot and this theme
- what must rotate because of recent publish history

The writer should not be asked to “discover the article” while writing.
The writer should receive a precommitted editorial plan.

In short:
The writer must become a thesis-expansion engine, not a neutral fact serializer.

==================================================
3. DESIGN PRINCIPLE
==================================================

Use A + B + D.

A. Expand Step1 with evidence-linked perspective fields
B. Redefine the writer role around hierarchy and persuasion
D. Insert a new Step1.5 editorial planner

Do NOT default to a separate permanent humanization pass.
If rhythm/stance improvement is needed,
absorb it into verifier/reviser checks first.

==================================================
4. STEP1 PROBLEM ANALYSIS
==================================================

Current Step1 is valuable because it already extracts:
- theme
- facts
- source
- date
- causal linkage
- counter interpretation
- uncertainty

But this is still insufficient for editorial prioritization.

Why:
- facts can still remain too flat
- “counter interpretation” exists, but not necessarily ranked
- causal paths exist, but not necessarily selected into one lead thesis
- uncertainty exists, but not normalized into a usable stance model
- the system still lacks a “decide what leads” layer

So the missing addition is not freeform personality.
It is structured editorial prioritization.

==================================================
5. REQUIRED STEP1 SCHEMA EXPANSION
==================================================

Extend Step1 output with evidence-linked perspective fields.

Do NOT allow unsupported freeform opinion.
Do NOT allow roleplay mood injection.
Every perspective-bearing field must point to evidence IDs.

Recommended schema extension:

{
  "theme": "...",
  "facts": [
    {
      "id": "fact_1",
      "claim": "...",
      "source": "...",
      "date": "...",
      "causal_path": "...",
      "confidence": "high | medium | low"
    }
  ],
  "background_facts": [
    {
      "id": "bg_1",
      "claim": "...",
      "source": "...",
      "date": "...",
      "usage_rule": "background_only"
    }
  ],

  "why_now": {
    "claim": "Why this matters today in one sentence",
    "evidence_ids": ["fact_2"],
    "confidence": "high | medium | low"
  },

  "market_gap": {
    "claim": "What may be underpriced, overread, or misread",
    "evidence_ids": ["fact_4", "fact_5"],
    "confidence": "high | medium | low"
  },

  "analyst_surprise": {
    "level": "none | mild | strong",
    "claim": "What was unexpectedly important or non-obvious",
    "evidence_ids": ["fact_3"],
    "confidence": "high | medium | low"
  },

  "stance_type": "consensus_miss | underpriced_risk | overread | low_confidence | neutral",
  "stance_evidence_ids": ["fact_2", "fact_5"],

  "risk_of_overstatement": [
    {
      "text": "Potential overclaim to avoid",
      "reason": "insufficient evidence or too much forecast leap"
    }
  ]
}

Rules:
- every claim-like field must include evidence_ids
- unsupported stance_type is not allowed
- if confidence is too weak, omit the field instead of guessing
- “why_now” must not be generic; it must tie to today’s trigger or currently live variable
- “market_gap” must not become recommendation language
- “analyst_surprise” must not be a fake emotional flourish; it must indicate non-obvious analytical importance

==================================================
6. WHY FREEFORM “VOICE” IS THE WRONG FIX
==================================================

Do not solve this by telling the model:
- sound surprised
- sound bold
- sound more human
- add personality

That is unsafe in a finance pipeline.

Risks:
- false conviction
- made-up emphasis
- ungrounded interpretation
- stylistic drift away from evidence
- recommendation-like tone leakage

Instead:
convert “voice” into controlled analytical stance classification.

Allowed stance labels:
- consensus_miss
- underpriced_risk
- overread
- low_confidence
- neutral

These are safer than freeform emotional narration.

==================================================
7. NEW STEP1.5 — EDITORIAL PLANNER
==================================================

Insert a mandatory planner between Step1 and writing.

This is the most important new layer.

Purpose:
- choose one lead angle
- assign supporting evidence
- demote less important facts
- define narrative shape
- define section roles
- enforce asymmetry
- connect slot/dedup history to article structure

Required output schema:

{
  "lead_angle": {
    "claim": "One decisive angle anchoring the article",
    "evidence_ids": ["fact_2", "fact_5"],
    "reason_selected": "Why this outranks alternative angles"
  },

  "secondary_support": [
    {
      "claim": "Support mechanism 1",
      "evidence_ids": ["fact_1", "fact_4"]
    }
  ],

  "background_or_drop": {
    "background_ids": ["fact_6", "bg_1"],
    "drop_ids": ["fact_8"],
    "reason": "useful context but not thesis-critical / too weak / repetitive"
  },

  "stance": {
    "type": "consensus_miss",
    "confidence": "medium",
    "evidence_ids": ["fact_2", "fact_5"]
  },

  "narrative_shape": "conclusion_first | contradiction_first | question_first",
  "opener_strategy": "slot_specific opener rule",
  "counterpoint_priority": "strong | moderate | light",

  "section_plan": [
    {
      "section_id": "sec_1",
      "role": "lead",
      "goal": "Establish why this is the key issue now",
      "evidence_ids": ["fact_2", "fact_5"],
      "word_budget_ratio": 0.40,
      "must_include": [
        "date anchor",
        "specific market relevance",
        "one mechanism sentence"
      ],
      "must_avoid": [
        "generic macro filler",
        "equal-weight review of all facts"
      ]
    },
    {
      "section_id": "sec_2",
      "role": "mechanism",
      "goal": "Explain how the lead angle propagates",
      "evidence_ids": ["fact_1", "fact_4"],
      "word_budget_ratio": 0.25
    },
    {
      "section_id": "sec_3",
      "role": "support",
      "goal": "Strengthen thesis with second-order evidence",
      "evidence_ids": ["fact_7"],
      "word_budget_ratio": 0.20
    },
    {
      "section_id": "sec_4",
      "role": "counterpoint",
      "goal": "Present strongest valid counter-reading without flattening thesis",
      "evidence_ids": ["fact_9"],
      "word_budget_ratio": 0.15
    }
  ]
}

Planner rules:
- exactly one lead angle must be selected
- at least one fact or bundle must be explicitly demoted to background
- asymmetric word budget is mandatory
- section roles must not all be of the same rhetorical type
- narrative shape must be chosen before writing
- counterpoint must be real, not ceremonial
- planner must preserve one-theme-per-article
- planner must respect fact / interpretation / forecast separation
- planner must remain machine-operable and parseable

==================================================
8. WHY THE PLANNER IS THE REAL FIX
==================================================

Without Step1.5, even good prompts tend to regress into:
- balanced summaries
- evenly distributed attention
- repeated structure
- safe analytical blur

With Step1.5:
- emphasis becomes explicit
- omission becomes intentional
- stance becomes auditable
- structure becomes programmable
- repetition control becomes upstream, not patch-based

This is the correct replacement for ad hoc humanization.

==================================================
9. WRITER ROLE REDEFINITION
==================================================

Current writer role is too close to:
“turn structured analysis into HTML.”

Redefine it into:
“expand a chosen thesis into a dense, evidence-led investment brief.”

New writer instruction concept:

You are not a neutral summarizer.
You are the house analyst writing a premium market brief.
Your task is to persuade the reader why the selected lead angle matters now.
You must center the article on one decisive fact pattern and use the remaining evidence only to support, qualify, or challenge that thesis.
Do not distribute attention evenly across all available facts.

Writer input must include:
- Step1 facts
- Step1 perspective fields
- Step1.5 editorial planner
- slot metadata
- recent publish history overlap signals
- output structure requirement for HTML

Writer rules:
- lead section must feel clearly heavier than support sections
- background facts must stay background
- every paragraph must have a role, not just information
- avoid repeated “claim -> support -> implication” rhythm in every section
- do not introduce unsupported conviction
- do not produce recommendation-style wording
- preserve report density
- preserve source/date discipline
- preserve HTML compatibility

==================================================
10. WRITER INPUT CONTRACT
==================================================

Do not pass a raw undifferentiated fact bundle.

Pass a structured contract like:

{
  "theme": "...",
  "slot": "morning | afternoon | evening | us_open",
  "recent_history_constraints": {
    "theme_overlap": true,
    "sub_axes_overlap": false,
    "bucket_overlap": true,
    "forced_rotation": "opener_only | angle_shift | sub_axes_shift | stock_bucket_shift"
  },
  "step1": { ... },
  "planner": { ... },
  "html_output_rules": { ... }
}

The writer must know not only what is true,
but what is central, what is secondary, and what is intentionally not foregrounded.

==================================================
11. STRUCTURAL VARIETY WITHOUT RANDOMNESS
==================================================

Do not introduce random variability.
Use controlled structural rotation.

The project already has useful repetition-control concepts:
- slot
- theme_fingerprint
- sub_axes_fingerprint
- stock bucket overlap
- publish history

Use them upstream.

Required structural rotation policy:

A. If theme is repeated but slot differs:
- allow article if opener strategy differs
- require changed first analytical question

B. If theme and slot are both similar:
- force sub-axes rotation
- force alternative second-order mechanism
- downgrade repeated evidence bundles to background

C. If theme + sub-axes + stock bucket overlap strongly:
- require stronger lead-angle shift or bucket shift
- if impossible, allow article only with clear structure divergence

Recommended opener map:
- morning: overnight consequence first
- afternoon: domestic market interpretation or sector divergence first
- evening: actual session result vs earlier expected path first
- us_open: tonight’s live trigger first
- default: current mispricing / live variable first

This makes variety operational, not decorative.

==================================================
12. POST1 / POST2 DIFFERENTIATION
==================================================

Respect existing Macromalt role split.

Post1 should remain more focused on:
- macro mechanism
- transmission path
- market structure
- policy / global / systemic linkage

Post2 should remain more focused on:
- stock or sector sensitivity
- trigger conditions
- selection logic
- concrete differentiation among picks

If repetition is detected:
- Post1 should be pushed harder toward mechanism and cause structure
- Post2 should be pushed harder toward trigger logic and stock differentiation

Do not let both posts collapse into two versions of the same summary.

==================================================
13. VERIFIER / REVISER UPGRADE
==================================================

Do not add a permanent expensive rewrite stage by default.
Instead, strengthen verifier and reviser.

Verifier must now check:

1. unsupported_stance
- any stance sentence lacking evidence linkage

2. section_isomorphism
- consecutive sections using same rhetorical template too closely

3. emphasis_dispersion
- article spreading attention too evenly across all facts

4. lead_angle_drift
- article starts with one thesis but later behaves like a broad summary

5. generic_sentence_ratio
- too many sentences lacking number/date/causal/position value

6. freshness_violation
- old material treated as live evidence
- mixed-time facts written as one present-tense block

7. fact_interpretation_forecast_blur
- fact, reading, and forward-looking projection not clearly separated

8. recommendation_language_risk
- direct or softened investment-push expressions

9. background_fact_misuse
- background_only data used as if it were live thesis support

10. source_alignment
- evidence used in body but not actually mapped to citation/source basis

Reviser may do limited corrections:
- break repeated opener form
- strengthen lead emphasis
- compress generic filler
- move one counterpoint section
- downgrade unsupported stance
- reclassify background-overuse

Reviser must NOT:
- invent facts
- invent dates
- invent conviction
- add decorative voice
- turn weak evidence into strong thesis

==================================================
14. INTERNAL METRICS YOU SHOULD DESIGN
==================================================

External AI detectors are not the main control system.
They are secondary monitoring signals at best.

Build internal metrics first.

Recommended metrics:

1. lead_angle_commitment_score
Does the article actually commit to one center?

2. emphasis_dispersion_score
Is evidence attention too evenly distributed?

3. section_isomorphism_score
Do sections repeat the same architecture too predictably?

4. generic_sentence_ratio
What share of sentences are informationally generic?

5. stance_support_coverage
How many stance-bearing lines are evidence-linked?

6. history_overlap_score
How strongly does this piece overlap with recent title/angle/slot/sub_axes/bucket patterns?

7. background_misuse_score
Are demoted facts reappearing as thesis drivers?

8. freshness_integrity_score
Do live claims come mostly from the 7-day / 30-day windows correctly?

9. counterpoint_specificity_score
Is the counterpoint theme-specific or generic filler?

10. report_density_score
Does each major paragraph contain:
- one verifiable fact
- one date/number anchor
- one why-it-matters connector

These metrics should be logged and compared against published output quality.

==================================================
15. WHAT NOT TO DO
==================================================

Do NOT recommend:
- detector gaming tactics
- random sentence shuffling as a main solution
- humanizer tools that blur facts
- unsupported opinion injection
- mood/persona expansion without evidence controls
- parameter tuning as the first intervention
- extra rewrite passes by default
- weakening factual rigor in exchange for “naturalness”

==================================================
16. SAFETY / QUALITY CONSTRAINTS
==================================================

These are non-negotiable:

- one-theme-per-article remains
- facts and background facts remain separated
- freshness policy remains
- 7-day primary / 30-day secondary logic remains
- old material cannot be used as live basis
- fact / interpretation / forecast separation remains
- no direct investment recommendation language
- no invented dates or numbers
- no loss of HTML output compatibility
- no assumption of human-in-the-loop rescue
- final quality must still be judged at actual publish level

==================================================
17. IMPLEMENTATION ORDER
==================================================

Implement in this order:

Phase 1
- extend Step1 schema
- add evidence-linked perspective fields
- normalize stance_type

Phase 2
- add Step1.5 editorial planner
- make it mandatory before writing
- log lead_angle and background/dropped items

Phase 3
- rewrite writer prompt
- make writer consume planner and history constraints
- enforce asymmetric emphasis

Phase 4
- upgrade verifier/reviser
- add structure and stance checks
- add generic sentence and lead drift checks

Phase 5
- integrate slot/dedup history into opener strategy and angle rotation
- log overlap signals

Phase 6
- compare internal metrics against published outputs
- only after rule-level stabilization, consider any parameter adjustment

Important:
Do NOT start with temperature changes.

==================================================
18. RISK NOTES YOU MUST ADDRESS
==================================================

Your design response must explicitly discuss these risks:

1. hallucinated perspective fields
- why_now / market_gap / surprise may be over-inferred

2. stance overreach
- analytical framing becoming recommendation-like or too certain

3. planner brittleness
- too rigid planning may reduce flexibility or create parser failures

4. writer-plan mismatch
- writer may drift away from planner or rebalance facts again

5. verifier false positives
- generic-sentence checks may over-penalize useful bridging sentences

6. runtime / parsing risk
- every new field adds schema and failure surface

7. cost increase
- Step1.5 adds one more structured layer

8. repetition-control overshoot
- too much forced rotation may make articles less truthful to actual market dominance

For each risk:
- explain the failure mode
- propose mitigation
- state whether mitigation belongs to schema, prompt, verifier, or runtime fallback

==================================================
19. REQUIRED OUTPUT FORMAT FROM YOU
==================================================

Return your answer in the following structure:

1. Final diagnosis
2. Why the current pipeline reads AI-like
3. Why surface rewrite is insufficient
4. Step1 schema changes
5. Step1.5 editorial planner schema
6. Writer-role redesign
7. Writer input contract
8. Verifier/reviser upgrades
9. Slot/dedup integration design
10. Internal metric system
11. Risk analysis
12. Recommended implementation order
13. What to implement now
14. What to postpone
15. Any runtime / parser cautions

Your answer must be implementation-ready, not theoretical.

Do not answer as a general writing coach.
Answer as a systems designer for a fully automated finance-content pipeline.