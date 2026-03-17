# PROMPT_PHASE14_TARGETED_REWRITE_HOTFIX_FULL

이 문서는 Claude Code에 직접 전달하는 **통합 실행 문서**입니다.  
목적은 다음 3가지를 한 파일에 묶는 것입니다.

1. Targeted Rewrite Replacement 핫픽스 구현
2. 결과 제출 형식 고정
3. 요약은 채팅, 상세는 MD 파일로 제출하도록 지시

---

## Claude Code 실행 지시문

You are implementing a focused hotfix for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14 implementation is GO but real-output is still HOLD.
- The most important remaining bottleneck is now clearly identified:
  the rewrite loop executes, but it does not actually reduce weak interpretation patterns in the final published prose.

Observed failure:
- weak interpretation was detected
- rewrite loop executed
- but weak_interp_hits remained unchanged
- therefore the current rewrite mechanism is too broad and too non-targeted
- whole-article rewrite is not reliably correcting the specific weak sentences that triggered the failure

Your task:
Implement a hotfix that converts the current broad rewrite flow into a **targeted sentence-level rewrite replacement system**.

This is NOT a broad new phase.
This is a focused corrective hotfix to make the existing rewrite enforcement actually work.

==================================================
PRIMARY OBJECTIVE
==================================================

Change the rewrite mechanism so that weak interpretation sentences are:
1. explicitly identified
2. individually rewritten
3. replaced in the article
4. re-scored after replacement

Success means:
- weak interpretation hits should have a realistic chance of decreasing after rewrite
- rewrite should target the actual failing sentences
- the system should stop treating whole-article rewrite as sufficient correction

==================================================
ROOT PROBLEM TO SOLVE
==================================================

Current failure mode:
- the system sends too much article content into rewrite
- the model is asked to “improve” the article globally
- but it is not forced to replace the exact weak interpretation lines
- therefore the final article may look slightly different while the same weak patterns remain detectable

New design principle:
Do not rewrite the whole article when the actual problem is a small set of weak sentences.

==================================================
TRACK A — TARGET EXTRACTION
==================================================

Implement a concrete extraction layer for weak interpretation rewrite targets.

A1. Detect weak interpretation sentences
Use the existing weak interpretation detection logic/patterns as the basis.
Identify the exact sentence-level spans that triggered weak interpretation failure.

Targets may include:
- textbook causality statements
- obvious headline-level interpretation
- category-risk filler in interpretive sections
- weak counterpoint sentences that fail to collide with the thesis

A2. Extract only the failing lines
When rewrite is triggered, build a list of the exact sentence candidates that need replacement.
Do not pass the full article as the primary rewrite target if only 2–5 sentences are the problem.

A3. Preserve context minimally
For each weak sentence, pass only the minimum context needed for rewrite:
- article type (Post1 or Post2)
- local section role ([해석], [전망], [반론], etc.)
- article spine / main thesis if available
- nearby sentence context if necessary
- why the sentence is weak

==================================================
TRACK B — TARGETED REWRITE GENERATION
==================================================

B1. Rewrite sentence-by-sentence
Generate replacement candidates for the weak sentences themselves, not a vague rewrite of the whole article.

Each replacement must aim to:
- remove textbook causality
- become more non-obvious
- become more thesis-relevant
- become more investor-useful
- preserve factual correctness
- remain stylistically compatible with the surrounding paragraph

B2. Make the rewrite instruction explicit
Do not ask the model to “improve quality” in vague terms.
For each sentence, specify:
- original weak sentence
- why it is weak
- what kind of improvement is required
- what is forbidden in the replacement

Examples of forbidden replacement patterns:
- oil up -> inflation pressure
- rates up -> valuation burden
- earnings estimate up -> investor attention
- volatility remains a risk
- uncertainty remains elevated

Examples of desired replacement patterns:
- resolve tension between signals
- explain why current configuration matters now
- identify investor framing shift
- show second-order implication
- connect the thesis to portfolio consequence or selection consequence

B3. Post-type-aware rewrite
Handle Post1 and Post2 differently.

For Post1:
- prioritize macro/theme interpretation
- strengthen analytical spine support
- improve conflict/tension resolution
- avoid generic macro commentary

For Post2:
- prioritize stock-level implication
- strengthen “why this name under this thesis” logic
- improve thesis collision in counterpoints
- avoid generic “technology strength / demand increase / uncertainty risk” filler

==================================================
TRACK C — REPLACEMENT INTEGRATION
==================================================

C1. Replace the original weak sentences in the article
After generating stronger replacements, insert them back into the original article in place of the weak lines.

Do NOT rely on returning a separate improved article draft only.
The system must actually replace the target sentences in the working article body.

C2. Preserve formatting and structure
Preserve:
- HTML structure
- section headings
- article flow
- comment markers if any
- special tags or metadata blocks that must remain intact

C3. Avoid destructive rewrite drift
Do not allow the hotfix to:
- rewrite unrelated parts of the article
- delete major sections
- break HTML structure
- collapse article length too aggressively
- remove source/context framing that the article still needs

==================================================
TRACK D — POST-REWRITE VERIFICATION
==================================================

D1. Re-score after replacement
After targeted replacement, run the interpretation quality scoring again.

Required check:
- weak_interp_hits before rewrite
- weak_interp_hits after rewrite

D2. Treat unchanged hits as unresolved
If weak interpretation hits do not materially improve after targeted rewrite,
do NOT treat the rewrite as success.

D3. Resolution visibility
Log or expose:
- which sentences were targeted
- what replacement was inserted
- weak hit count before/after
- whether the rewrite resolved the targeted issue

==================================================
TRACK E — SAFETY / QUALITY GUARDRAILS
==================================================

E1. Do not hallucinate facts
Replacement sentences must not invent unsupported numbers, dates, or claims.

E2. Preserve fact layer integrity
This hotfix is for interpretation quality, not for silently changing core facts.

E3. Avoid over-stylization
Do not replace weak sentences with ornate but empty prose.
The goal is stronger analysis, not prettier fluff.

E4. Avoid downgrade in clarity
Replacement should be sharper, not more convoluted.

==================================================
IMPLEMENTATION CONSTRAINTS
==================================================

1. Do not redesign the 3-stage pipeline.
2. Do not introduce new external data providers.
3. Do not remove Phase 11–14 rules.
4. Treat this as a focused hotfix, not a broad architecture rewrite.
5. Prefer additive, low-risk changes.
6. Public function signatures should remain stable unless strongly necessary.
7. Keep logs and diagnostics inspectable.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement the targeted sentence-level rewrite replacement hotfix.

2. Documentation
Create/update concise internal docs describing:
- why the previous rewrite loop failed
- how target extraction works
- how sentence-level replacement works
- how post-rewrite verification works
- how Post1/Post2 rewrite behavior differs if applicable

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- weak interpretation sentence extraction works
- sentence-level rewrite generation works
- original weak sentence is actually replaced
- HTML/structure remains intact
- post-rewrite weak hit count is re-scored
- unchanged weak hit count is treated as unresolved
- Post2 stock-level weak interpretation handling improves
- Phase 14 compatibility remains intact
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
  "weak_sentence_extraction": "PASS|WARN|FAIL",
  "targeted_rewrite_generation": "PASS|WARN|FAIL",
  "sentence_replacement_integration": "PASS|WARN|FAIL",
  "html_structure_preservation": "PASS|WARN|FAIL",
  "post_rewrite_rescoring": "PASS|WARN|FAIL",
  "rewrite_resolution_detection": "PASS|WARN|FAIL",
  "post2_stock_interpretation_hotfix": "PASS|WARN|FAIL",
  "phase14_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION PRINCIPLES
==================================================

When in doubt:
- prefer rewriting the exact bad sentence over rewriting everything
- prefer visible correction over vague improvement attempts
- prefer sharper investor-useful interpretation over generic safe commentary
- prefer narrow factual integrity over broad stylistic churn
- prefer measurable reduction in weak_interp_hits over cosmetic changes
- prefer inspectable replacement logs over hidden rewrite behavior

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

- The problem is not that rewrite exists.
- The problem is that rewrite is too broad to fix the exact sentences that failed.
- This hotfix should make rewrite measurable and sentence-specific.
- If a tradeoff is required, prefer narrower but real correction over broader but unverifiable rewrite.
- The most important proof of success is reduction in weak interpretation hits after replacement.

---

## Important

A rewrite that executes but does not reduce weak interpretation is a failure.
Whole-article rewrite is not sufficient if the weak sentences remain.
This hotfix succeeds only if the actual failing lines are replaced and improved.

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
`REPORT_PHASE14_TARGETED_REWRITE_HOTFIX.md`

The detailed report must include:
- final report
- implementation details
- verification checklist
- risks / follow-up items
- final gate JSON

Use this structure in the report:

# REPORT_PHASE14_TARGETED_REWRITE_HOTFIX

## 1. Changed Files
- file
- change summary

## 2. Implementation Summary
- what was added
- what was changed
- how sentence-level replacement works

## 3. Verification Results
- checklist
- any test results
- weak hit count before/after examples if available

## 4. Risks / Follow-up
- unresolved items
- tuning needs
- known limitations

## 5. Final Gate JSON
```json
{
  "weak_sentence_extraction": "PASS|WARN|FAIL",
  "targeted_rewrite_generation": "PASS|WARN|FAIL",
  "sentence_replacement_integration": "PASS|WARN|FAIL",
  "html_structure_preservation": "PASS|WARN|FAIL",
  "post_rewrite_rescoring": "PASS|WARN|FAIL",
  "rewrite_resolution_detection": "PASS|WARN|FAIL",
  "post2_stock_interpretation_hotfix": "PASS|WARN|FAIL",
  "phase14_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE14_TARGETED_REWRITE_HOTFIX_FULL.md 읽고 구현해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
