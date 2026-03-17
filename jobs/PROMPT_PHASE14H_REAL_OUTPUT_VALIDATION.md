# PROMPT_PHASE14H_REAL_OUTPUT_VALIDATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 14H 실출력 검증용 통합 실행 문서**입니다.

목적:
1. 신규 런 실행
2. 신규 발행 URL 확보
3. 신규 URL 본문 기준 실출력 검증
4. 요약은 채팅, 상세는 MD 파일로 제출

---

## Claude Code 실행 지시문

You are running the real-output validation for the macromalt project after the Targeted Rewrite Replacement hotfix.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14 implementation was GO but real-output was HOLD.
- A focused hotfix was then implemented to convert broad rewrite into targeted block-level rewrite replacement.
- This task exists to validate whether that hotfix materially improved the actual newly published article output.

Critical mission:
You must execute a fresh current-run validation and determine whether the targeted rewrite replacement hotfix materially improved the actual published prose.

You must not stop at code inspection.
You must validate the real newly generated and newly published article outputs.

==================================================
NON-NEGOTIABLE EXECUTION RULES
==================================================

1. You must execute a NEW generation run using the current hotfixed codebase.
2. You must publish NEW outputs to WordPress.
3. You must retrieve the NEW live URLs from the CURRENT run.
4. You must validate using ONLY those NEW URLs from the CURRENT run.
5. You must NOT use old logs, old URLs, old article text, historical samples, or previously reviewed outputs as the validation basis.
6. If fresh publishing succeeds, NEW URL-based review is mandatory.
7. If fresh generation succeeds but publishing fails, review the fresh generated full text directly and explicitly mark URL-based validation as incomplete.
8. If fresh generation itself fails, report the blockage clearly and stop.
9. Do NOT ask me which option to use if the run can be executed directly.
10. Do NOT return a plan or memo instead of performing the task.

==================================================
PRIMARY GOAL
==================================================

Determine whether the targeted rewrite replacement hotfix produced real article improvement in the newly published output.

This means validating whether the new articles are now:
- stronger in non-obvious interpretation
- less dominated by weak interpretation patterns
- visibly improved by targeted rewrite rather than broad rewrite
- more precise in fact vs forecast handling
- cleaner in hedge usage
- stronger in Post1/Post2 editorial separation and continuity
- more trustworthy numerically and temporally
- more useful to an investor reader
- less generic than the previous Phase 14 output review

==================================================
MANDATORY WORKFLOW
==================================================

Follow this exact order:

Step 1.
Execute a fresh content generation run using the current hotfixed codebase.

Step 2.
Ensure at least:
- 1 newly generated Post1
- 1 newly generated Post2

Step 3.
Publish both outputs to WordPress.

Step 4.
Collect the NEW live URLs from this CURRENT run.

Step 5.
Fetch the full published article bodies directly from those NEW URLs.

Step 6.
Review those NEW published articles as the primary source of truth.

Step 7.
Judge whether the targeted rewrite replacement hotfix actually improved real output quality.

Step 8.
Return a strict validation report with GO/HOLD judgment.

==================================================
SOURCE-OF-TRUTH POLICY
==================================================

For this task, the source of truth is:

1. NEWLY GENERATED + NEWLY PUBLISHED WordPress URLs from the CURRENT run
2. If publishing fails, NEWLY GENERATED full text from the CURRENT run only
3. Nothing historical should be treated as an acceptable substitute for final validation

Validation based on historical outputs is invalid for this task.

==================================================
WHAT YOU MUST TEST
==================================================

You must evaluate all of the following from the actual newly published output.

A. Targeted Rewrite Effectiveness
Check whether the hotfix actually improved the specific weak interpretation zones.

Fail signals:
- weak interpretation remains in the same local blocks after rewrite
- rewrite executed but the final prose still contains the same obvious causal filler
- weak patterns appear to have survived because only surrounding text changed

Pass signals:
- previously weak local blocks are materially sharper
- the final prose shows sentence/block-level correction, not just cosmetic drift
- weak interpretation density is visibly lower in the exact problem zones

B. Weak Interpretation Reduction
Check whether the final prose is materially less dominated by textbook causality.

Fail signals:
- oil up -> inflation pressure
- rates up -> valuation burden
- demand up -> company strength
- volatility/uncertainty filler presented as analysis
- headline-level facts relabeled as [해석]

Pass signals:
- more tension-resolution logic
- more investor framing shift
- more second-order implication
- more configuration-specific explanation
- fewer obvious “any day” sentences

C. Fact vs Forecast Handling
Check whether fact/forecast contamination appears reduced in the final prose.

Fail signals:
- past or completed dates still written as forecasts
- already known market facts still phrased with forecast verbs
- stale or ambiguous date phrasing still leaks into the article

Pass signals:
- completed facts are written directly
- forecasts remain clearly labeled as forecasts or scenarios
- date anchoring feels coherent
- factual statements do not sound like pending events

D. Hedge Control
Check whether hedging is better controlled.

Fail signals:
- fact statements still use “것으로 보입니다 / 파악됩니다 / 추정됩니다 / 예상됩니다”
- analytical claims are still drowned in repetitive hedge language
- outlook is vague without explicit condition

Pass signals:
- fact statements are direct
- analytical claims are readable and not over-softened
- outlook statements are clearly conditional when forward-looking

E. Counterpoint Specificity
Check whether counterpoints function as real thesis challenges.

Fail signals:
- category-risk filler only
- no condition
- no consequence
- no explicit clash with thesis

Pass signals:
- explicit condition
- explicit consequence
- direct collision with the article’s thesis
- investor-relevant failure path

F. Analytical Spine
Check whether each article now has a real argument rather than parallel fact listing.

Fail signals:
- article still reads like bundled facts
- sections do not advance a single thesis
- spine marker may exist but does not govern the prose

Pass signals:
- central argument is evident
- paragraphs support a thesis
- the reader can say what the article is arguing, not just what it lists

G. Post1 / Post2 Continuity
Check whether Post2 begins where Post1 ends.

Fail signals:
- Post2 re-explains the macro setup from Post1
- same opening logic repeated
- role separation exists only formally

Pass signals:
- Post1 frames the market/theme
- Post2 continues from that frame into names/exposure/positioning/risk
- reader feels progression rather than duplication

H. Temporal / Numeric Trustworthiness
Check whether the published article avoids trust-breaking issues.

Fail signals:
- future year or forecast written like settled fact
- stale year framing
- article date and cited data are mismatched without explanation
- clearly suspicious high-impact number remains in final prose

Pass signals:
- forecast vs actual clearly separated
- dates/periods are coherent
- high-impact numbers look plausible
- fact layer feels safe enough for publication

==================================================
REVIEW METHOD
==================================================

For each article, review in 3 layers:

Layer 1 — Editorial reading
Judge it like an editor of a premium market brief.
Ask:
- Is this actually worth reading?
- Would an informed investor learn something non-obvious?
- Does the prose sound selective, confident, and intentional?
- Or does it still sound like polished AI filler?

Layer 2 — Hotfix visibility reading
Judge whether the targeted rewrite hotfix is actually visible.
Ask:
- Did the weak local blocks get sharper?
- Did broad fluff get replaced by targeted stronger lines?
- Is the final article less generic in the places that used to fail?

Layer 3 — Trust reading
Judge whether the fact layer feels safe enough.
Ask:
- Are dates coherent?
- Are forecasts clearly forecasts?
- Are high-impact numbers plausible?
- Would a careful reader lose trust in the article?

==================================================
SCORING FRAME
==================================================

For each sample, score 1 to 5 on:

- targeted_rewrite_effectiveness
- weak_interpretation_reduction
- fact_forecast_separation
- hedge_control
- counterpoint_specificity
- analytical_spine
- post1_post2_continuity
- investor_usefulness
- premium_tone
- temporal_trustworthiness
- numeric_trustworthiness
- non_genericity

Scoring meaning:
1 = severe failure
2 = weak / mostly unsuccessful
3 = mixed / partial improvement
4 = strong / clearly improved
5 = excellent / premium-level execution

You must explain each score briefly and concretely.

==================================================
MANDATORY COMPARISON AGAINST PRIOR FAILURE MODES
==================================================

You must explicitly compare the new outputs against the previously identified failure modes:

FM1. [해석] = 교과서 인과만 전달
FM2. 팩트 문장에도 헤징 지속
FM3. 반론 = 카테고리 이름 수준
FM4. 기사 뼈대 약함 / 병렬 팩트 나열
FM5. Post2가 Post1 반복
FM6. 시간/수치 신뢰 문제
FM7. 어떤 날에도 쓸 수 있는 범용 시황문
FM8. rewrite executes but weak hits do not materially improve

For each failure mode, mark one of:
- IMPROVED
- PARTIALLY IMPROVED
- NOT IMPROVED
- REGRESSED

Do not skip this section.

==================================================
OUTPUT FORMAT
==================================================

## 0. Run Audit
State clearly:
- whether a fresh generation run was executed
- run_id if available
- whether fresh publishing succeeded
- newly generated sample count
- newly published URL list from the CURRENT run
- whether final validation was performed against NEW URLs only
- any technical blockage encountered

## 1. Sample Source Audit
For each sample, state:
- source type: fresh published URL / fresh generated text
- whether it is full or partial
- whether it came from the CURRENT run
- whether confidence is limited for any reason

## 2. Executive Judgment
Answer directly:
- Did the targeted rewrite replacement hotfix materially improve real article quality?
- Is the improvement enough to move forward?
- Or is another corrective phase still required?

## 3. Sample-by-Sample Review
For each article:
- what improved
- what still fails
- score table
- one-line editorial verdict

## 4. Failure-Mode Regression Check
For each of FM1–FM8, mark:
- IMPROVED / PARTIALLY IMPROVED / NOT IMPROVED / REGRESSED
and explain why.

## 5. Cross-Sample Diagnosis
Identify the remaining systemic bottlenecks, if any.

## 6. Gate Decision
Return one of:
- PHASE14H_OUTPUT_GO
- PHASE14H_OUTPUT_HOLD

Rule:
Use GO only if the actual newly published output is clearly and materially better, not merely structurally compliant.

## 7. Rationale for Gate Decision
Write a tight but serious explanation of why the gate is GO or HOLD.

## 8. If HOLD: Next Required Action
If the result is HOLD, specify the single most important next action.
Do NOT give a vague roadmap.
Name the next bottleneck precisely.

## 9. Final Validation JSON
Return a JSON object in this shape:

{
  "fresh_run_executed": "PASS|FAIL",
  "fresh_publish_succeeded": "PASS|FAIL",
  "new_url_based_validation": "PASS|FAIL",
  "targeted_rewrite_effectiveness": "PASS|WARN|FAIL",
  "weak_interpretation_reduction": "PASS|WARN|FAIL",
  "fact_forecast_separation": "PASS|WARN|FAIL",
  "hedge_control": "PASS|WARN|FAIL",
  "counterpoint_specificity": "PASS|WARN|FAIL",
  "analytical_spine": "PASS|WARN|FAIL",
  "post1_post2_continuity": "PASS|WARN|FAIL",
  "investor_usefulness": "PASS|WARN|FAIL",
  "premium_tone": "PASS|WARN|FAIL",
  "temporal_trustworthiness": "PASS|WARN|FAIL",
  "numeric_trustworthiness": "PASS|WARN|FAIL",
  "non_genericity": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION STANDARD
==================================================

Use this standard:

GO means:
- the improvement is visible in the actual prose
- targeted weak zones are materially stronger
- the articles are meaningfully less generic
- rewrite effectiveness is visible in the final prose
- temporal/numeric trust problems are not visibly undermining trust
- Post1 and Post2 feel sequential rather than redundant

HOLD means:
- the structure improved but the writing still does not deliver real investor value
- targeted rewrite is not visible enough in the final prose
- the article still sounds like compliant AI summary prose
- weak interpretation remains obvious, padded, or low-conviction
- trust-breaking fact issues remain visible
- continuity between Post1 and Post2 still fails materially
- rewrite still behaves like a null-op in practical terms

==================================================
IMPORTANT STYLE RULE
==================================================

Be blunt, practical, and editorially serious.
Do not give polite credit for implementation effort.
Judge only the real newly published output.
A structurally compliant article that still reads like generic AI finance content is a HOLD.

---

## Additional operator note

- Do not validate against old URLs or historical samples.
- Fresh current-run URL validation is mandatory.
- Implementation success is irrelevant if the prose still feels generic.
- Targeted rewrite must be visible in the article, not just in logs.
- If a trust-breaking temporal or numeric issue is still visible in the published article, do not award GO lightly.
- The final judgment must be based on reader-facing output quality, not internal rule coverage.

---

## Important

This task is not "did the hotfix get implemented?"
This task is "did the newly published article actually get better?"
If the answer is not clearly yes, return HOLD.

---

## 결과 제출 규칙

Claude Code must return results in **two layers**:

### 1) Chat summary
Reply briefly in chat with:
- run_id
- published URLs
- whether output gate is GO or HOLD
- one-paragraph summary of what improved
- one-paragraph summary of what still failed

### 2) Full report as Markdown file
Also create and provide a **detailed MD report file**.

Recommended filename:
`REPORT_PHASE14H_REAL_OUTPUT_VALIDATION.md`

The detailed report must include:
- run audit
- sample source audit
- sample-by-sample review
- failure-mode regression check
- cross-sample diagnosis
- final gate JSON

Use this structure in the report:

# REPORT_PHASE14H_REAL_OUTPUT_VALIDATION

## 1. Run Audit

## 2. Sample Source Audit

## 3. Executive Judgment

## 4. Sample-by-Sample Review

## 5. Failure-Mode Regression Check

## 6. Cross-Sample Diagnosis

## 7. Gate Decision

## 8. If HOLD: Next Required Action

## 9. Final Validation JSON
```json
{
  "fresh_run_executed": "PASS|FAIL",
  "fresh_publish_succeeded": "PASS|FAIL",
  "new_url_based_validation": "PASS|FAIL",
  "targeted_rewrite_effectiveness": "PASS|WARN|FAIL",
  "weak_interpretation_reduction": "PASS|WARN|FAIL",
  "fact_forecast_separation": "PASS|WARN|FAIL",
  "hedge_control": "PASS|WARN|FAIL",
  "counterpoint_specificity": "PASS|WARN|FAIL",
  "analytical_spine": "PASS|WARN|FAIL",
  "post1_post2_continuity": "PASS|WARN|FAIL",
  "investor_usefulness": "PASS|WARN|FAIL",
  "premium_tone": "PASS|WARN|FAIL",
  "temporal_trustworthiness": "PASS|WARN|FAIL",
  "numeric_trustworthiness": "PASS|WARN|FAIL",
  "non_genericity": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE14H_REAL_OUTPUT_VALIDATION.md 읽고 실행해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
