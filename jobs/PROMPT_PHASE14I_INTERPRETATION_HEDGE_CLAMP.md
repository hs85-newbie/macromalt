# PROMPT_PHASE14I_INTERPRETATION_HEDGE_CLAMP.md

이 문서는 Claude Code에 직접 전달하는 **Phase 14I — Interpretation Hedge Clamp** 통합 실행 문서입니다.

목적:
1. `[해석]` 문장에 고착된 헤징 어미 공식을 강하게 차단
2. `weak_hits`뿐 아니라 `hedge_overuse`도 재작성 트리거로 승격
3. 실출력에서 해석 문장의 확신도와 비자명성을 동시에 끌어올림
4. 결과는 요약은 채팅, 상세는 MD 파일로 제출

---

## Claude Code 실행 지시문

You are implementing a focused hotfix for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14 implementation was GO but real-output was HOLD.
- Phase 14H targeted rewrite replacement hotfix was implemented.
- Phase 14H real-output validation still returned HOLD.
- A new highest-priority bottleneck is now clear:
  [해석] sentences are still dominated by hedge-heavy default endings such as
  "파악됩니다", "보입니다", "것으로 보입니다", "작용하는 것으로 보입니다".
- This pattern is now a stronger bottleneck than broad interpretation rules because it directly suppresses analytical conviction and makes the prose sound like generic AI commentary.

Your task:
Implement **Phase 14I — Interpretation Hedge Clamp**.

This is a focused hotfix, not a broad new architecture phase.

==================================================
PRIMARY OBJECTIVE
==================================================

Raise real article quality by directly suppressing hedge-saturated interpretation phrasing.

This hotfix succeeds only if it materially improves:
1. the directness of [해석] sentences
2. the editorial confidence of analytical prose
3. rewrite triggering when hedge-heavy interpretation remains
4. the likelihood that real published output sounds less generic and less evasive

==================================================
ROOT PROBLEM TO SOLVE
==================================================

Observed failure mode from real-output validation:
- Post1 [해석] sentences repeatedly use “파악됩니다 / 보입니다” endings
- hedge-heavy phrasing dominates even when facts and structure are otherwise acceptable
- targeted rewrite did not execute in some runs because `weak_hits` stayed below threshold
- therefore the system allows hedge-saturated interpretation to survive even when it clearly weakens output quality

New principle:
A sentence labeled [해석] should not sound like a liability disclaimer.
It should sound like an analytical judgment.

==================================================
TRACK A — INTERPRETATION HEDGE CLAMP
==================================================

Implement explicit suppression of hedge-heavy endings in interpretive sections.

A1. Clamp only the right zones
Focus the clamp on:
- [해석]
- analysis paragraphs
- thesis-carrying interpretive sentences
- interpretive transition lines that explain what matters

Do NOT over-apply to:
- genuine future scenarios
- explicit uncertainty disclosures
- clearly conditional outlook blocks
- citation/source notes

A2. Explicitly prohibit default hedge endings in [해석]
Add direct generation-time prohibition for patterns such as:
- 파악됩니다
- 보입니다
- 것으로 보입니다
- 것으로 파악됩니다
- 작용하는 것으로 보입니다
- 시사하는 것으로 보입니다
- 판단됩니다
when they are used as the default ending for interpretive claims

Important:
This does NOT mean zero uncertainty language everywhere.
It means [해석] must stop defaulting to repetitive hedge-ending formulas.

A3. Allow controlled alternatives
Encourage stronger alternatives such as:
- direct interpretive statements
- conditionally bounded interpretation
- explicit thesis-linked claims
- “이 구도는 …를 의미한다”
- “핵심은 …에 있다”
- “이는 …보다 …를 더 중요하게 만든다”
- “이번 흐름은 …가 아니라 …에 가깝다”

Goal:
The prose should become more editorially intentional, not merely more blunt.

==================================================
TRACK B — HEDGE-AWARE REWRITE TRIGGER
==================================================

Current problem:
Rewrite triggers are too dependent on weak interpretation count.
Some bad articles escape rewrite because `weak_hits < threshold` even though hedge saturation is clearly severe.

B1. Promote hedge_overuse to rewrite trigger
Add rewrite triggering not only when:
- weak interpretation count is high

but also when:
- hedge_overuse is FAIL
or
- interpretation-zone hedge density exceeds a defined threshold

B2. Section-sensitive triggering
Prefer triggering on hedge-heavy interpretive zones specifically, not whole-article generic counts only.

Desired behavior:
- if [해석] blocks are saturated with “보입니다 / 파악됩니다” style endings,
  targeted rewrite should run even if weak_hits are below the original threshold

B3. Combined trigger logic
Support logic like:
- weak_hits high -> rewrite
- hedge_overuse fail -> rewrite
- both high -> stronger rewrite priority

==================================================
TRACK C — TARGETED HEDGE REWRITE
==================================================

C1. Target the actual hedge-heavy lines
When hedge-driven rewrite is triggered:
- identify the exact [해석] sentences or local blocks that overuse hedge endings
- rewrite those lines specifically
- do not rely only on global article improvement

C2. Preserve meaning while changing force
The goal is not to make the sentence recklessly absolute.
The goal is to remove formulaic default hedging and replace it with stronger analytical phrasing.

Bad:
- 이는 시장 불안 심리가 반영된 결과로 파악됩니다.
- 이는 성장성 기대가 이어지는 것으로 보입니다.

Better direction:
- 핵심은 시장이 안전자산 회피보다 금리 민감도를 더 크게 반영하고 있다는 점이다.
- 이번 흐름은 단순 기대감보다 성장성 프리미엄이 다시 가격에 반영되기 시작했다는 신호에 가깝다.

C3. Post-type-aware hedge rewrite
For Post1:
- strengthen macro interpretation
- emphasize thesis clarity
- reduce vague analytical fog

For Post2:
- strengthen stock-level judgment
- avoid “technology strength / demand increase / uncertainty” filler
- force “why this name under this thesis” clarity

==================================================
TRACK D — VALIDATION / SCORING UPDATE
==================================================

D1. Strengthen hedge diagnostics
Refine diagnostics so they can distinguish:
- harmless conditional scenario wording
vs
- repetitive hedge-ending dependency in [해석] zones

D2. Visible before/after reporting
Log or expose:
- hedge-heavy interpretation lines targeted
- replacements inserted
- hedge-related score before/after
- whether rewrite actually reduced hedge saturation

D3. Treat unchanged hedge saturation as unresolved
If hedge-heavy interpretation remains essentially unchanged after rewrite,
do NOT treat the rewrite as successful.

==================================================
TRACK E — QUALITY GUARDRAILS
==================================================

E1. Do not over-correct into reckless certainty
This hotfix should improve confidence, not introduce unsupported certainty.

E2. Preserve factual correctness
Do not change factual meaning while removing hedge-heavy phrasing.

E3. Avoid ornate pseudo-confidence
Do not replace weak hedge-heavy prose with dramatic but empty editorial language.

E4. Keep investor usefulness central
Sharper language must also produce better investment interpretation, not just different style.

==================================================
IMPLEMENTATION CONSTRAINTS
==================================================

1. Do not redesign the 3-stage pipeline.
2. Do not add new external data providers.
3. Do not remove Phase 11–14H rules; build on top of them.
4. Treat this as a focused hotfix.
5. Prefer additive, low-risk changes.
6. Public function signatures should remain stable unless strongly necessary.
7. Keep logs and diagnostics inspectable.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement the Interpretation Hedge Clamp hotfix.

2. Documentation
Create/update concise internal docs describing:
- why hedge-heavy interpretation became the new bottleneck
- how hedge clamp works
- how rewrite triggering was extended
- how targeted hedge rewrite works
- how Post1/Post2 handling differs if applicable

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- interpretation hedge clamp rules are injected
- hedge-heavy [해석] lines are detected
- hedge_overuse can trigger rewrite
- targeted hedge rewrite replaces the actual lines
- hedge score is re-evaluated after rewrite
- unchanged hedge saturation is treated as unresolved
- Post2 interpretation hedge handling improves
- Phase 14H compatibility remains intact
- public signatures remain stable
- imports/build pass

4. Final report
Return:
- changed files
- implementation summary
- verification results
- risks / follow-up items
- final gate JSON

==================================================
TARGET VERIFICATION FORMAT
==================================================

Use a gate summary like this shape if possible:

{
  "interpretation_hedge_clamp": "PASS|WARN|FAIL",
  "hedge_line_detection": "PASS|WARN|FAIL",
  "hedge_trigger_extension": "PASS|WARN|FAIL",
  "targeted_hedge_rewrite": "PASS|WARN|FAIL",
  "post_rewrite_hedge_rescoring": "PASS|WARN|FAIL",
  "hedge_resolution_detection": "PASS|WARN|FAIL",
  "post2_interpretation_clamp": "PASS|WARN|FAIL",
  "phase14h_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION PRINCIPLES
==================================================

When in doubt:
- prefer fewer hedge-heavy [해석] lines over more “safe” but generic ones
- prefer targeted rewrite of the exact bad line over global rewrite drift
- prefer stronger analytical judgment over repetitive disclaimer-style phrasing
- prefer measurable hedge reduction over stylistic self-congratulation
- prefer inspectable clamp behavior over hidden magic

==================================================
OUTPUT STYLE
==================================================

Be practical and implementation-first.
Do not return a vague strategy memo only.
Actually implement the hotfix.

At the end, provide:
1. changed files
2. what was implemented
3. verification results
4. final gate JSON

---

## Additional operator note

- The current highest-priority bottleneck is not broad structure.
- It is the default hedge-ending formula inside [해석] lines.
- If a tradeoff is required, prefer direct improvement of reader-facing interpretive prose over adding more internal scoring.
- If rewrite can only be improved in one way, make hedge_overuse capable of forcing rewrite.
- The success condition is visible reduction of “보입니다 / 파악됩니다” dominance in real published output.

---

## Important

A system that still writes most [해석] sentences as “파악됩니다 / 보입니다” has not solved interpretation quality.
This hotfix succeeds only if the final prose sounds less evasive and more editorially intentional.

---

## 결과 제출 규칙

Claude Code must return results in **two layers**:

### 1) Chat summary
Reply briefly in chat with:
- commit hash
- changed files
- whether implementation gate is GO or HOLD
- one-paragraph summary of what changed
- one-paragraph summary of remaining risk

### 2) Full report as Markdown file
Also create and provide a **detailed MD report file**.

Recommended filename:
`REPORT_PHASE14I_INTERPRETATION_HEDGE_CLAMP.md`

The detailed report must include:
- final report
- implementation details
- verification checklist
- risks / follow-up items
- final gate JSON

Use this structure in the report:

# REPORT_PHASE14I_INTERPRETATION_HEDGE_CLAMP

## 1. Changed Files
- file
- change summary

## 2. Implementation Summary
- what was added
- what was changed
- how hedge clamp and rewrite triggering work

## 3. Verification Results
- checklist
- any test results
- hedge score before/after examples if available

## 4. Risks / Follow-up
- unresolved items
- tuning needs
- known limitations

## 5. Final Gate JSON
```json
{
  "interpretation_hedge_clamp": "PASS|WARN|FAIL",
  "hedge_line_detection": "PASS|WARN|FAIL",
  "hedge_trigger_extension": "PASS|WARN|FAIL",
  "targeted_hedge_rewrite": "PASS|WARN|FAIL",
  "post_rewrite_hedge_rescoring": "PASS|WARN|FAIL",
  "hedge_resolution_detection": "PASS|WARN|FAIL",
  "post2_interpretation_clamp": "PASS|WARN|FAIL",
  "phase14h_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE14I_INTERPRETATION_HEDGE_CLAMP.md 읽고 구현해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
