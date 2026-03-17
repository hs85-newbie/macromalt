# PROMPT_PHASE15_REAL_OUTPUT_VALIDATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15 실출력 검증용 통합 실행 문서**입니다.

목적:
1. 신규 런 실행
2. 신규 발행 URL 확보
3. 신규 URL 본문 기준 실출력 검증
4. 완료 연도 실적의 시제 신뢰성이 실제 발행문에서 개선됐는지 판정
5. 결과는 요약은 채팅, 상세는 MD 파일로 제출
6. **발행 본문 전문을 MD 보고서에 반드시 포함**

---

## Claude Code 실행 지시문

You are running the real-output validation for the macromalt project after Phase 15 Temporal Tense Enforcement implementation.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation is now GO.
- This task exists to validate whether Phase 15 materially improved the actual newly published article output.

Critical mission:
You must execute a fresh current-run validation and determine whether Phase 15 materially improved temporal trustworthiness in the actual published prose.

You must not stop at code inspection.
You must validate the real newly generated and newly published article outputs.

==================================================
NON-NEGOTIABLE EXECUTION RULES
==================================================

1. You must execute a NEW generation run using the current Phase 15 codebase.
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

Determine whether Phase 15 produced real article improvement in temporal trustworthiness.

This means validating whether the new articles are now:
- correctly distinguishing completed-year actuals from forecasts
- correctly distinguishing actual / preliminary / consensus / guidance / forecast
- no longer writing completed-year results as pending outcomes
- more trustworthy to a careful investor reader at the fact layer
- still maintaining the gains from Phase 14I in interpretation quality and hedge control

==================================================
MANDATORY WORKFLOW
==================================================

Follow this exact order:

Step 1.
Execute a fresh content generation run using the current Phase 15 codebase.

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
Judge whether Phase 15 actually improved real output quality.

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

A. Completed-Year Actual Enforcement
Check whether already-completed reporting periods are written as completed facts.

Fail signals:
- 2024 or 2025 full-year results in a 2026 article are written with forecast/projection phrasing
- completed-year result is written with “예상”, “전망”, “기록할 것으로”, “달성할 것으로”, or equivalent future-style wording
- article leaves the reader unsure whether the result is actual or forecast

Pass signals:
- completed-year actuals are written directly as completed facts
- wording clearly indicates the period is already settled
- no misleading future-style treatment remains

B. Preliminary vs Actual Distinction
Check whether preliminary figures are clearly distinguished from settled actuals.

Fail signals:
- preliminary figures are flattened into definitive actuals without qualification
- actuals and preliminaries are blurred together

Pass signals:
- preliminary / provisional nature is explicitly preserved where relevant
- actual vs preliminary status is clear to a careful reader

C. Consensus / Guidance / Forecast Separation
Check whether expectation language is properly separated from factual result language.

Fail signals:
- consensus is written like actual result
- guidance is written like achieved outcome
- prior expectation is collapsed into current factual narration

Pass signals:
- actual result, consensus expectation, and company guidance are clearly separated
- the article preserves the correct evidentiary status of each number

D. Completed-Year-as-Forecast Residue
Check whether any completed-year-as-forecast phrasing still remains.

Required:
- identify exact offending lines if any remain
- explicitly state whether Phase 15 correction appears visible in final prose
- if no residue remains, say so clearly

E. Fact vs Forecast Handling More Broadly
Check whether fact/forecast contamination is reduced not just for annual results but in the broader article.

Fail signals:
- completed dates phrased as pending outcomes
- known facts written like forecasts
- ambiguous date phrasing still degrades trust

Pass signals:
- factual statements sound settled when they should
- forecasts remain forecast-like when they should
- temporal anchoring is coherent

F. Interpretation / Hedge Regression Guard
Phase 15 should not break previous gains.

Check that:
- `[해석]` lines are not backsliding into hedge-heavy formulas
- Phase 14I improvements are not lost
- article does not become temporally correct but stylistically generic again

G. Counterpoint / Spine / Continuity Guard
Also ensure Phase 15 does not degrade:
- counterpoint quality
- analytical spine
- Post1/Post2 continuity

H. Temporal / Numeric Trustworthiness
Check overall publication trust.

Fail signals:
- misleading year framing
- unresolved temporal mismatch
- suspicious high-impact numbers
- article date and cited period conflict without explanation

Pass signals:
- dates/periods are coherent
- completed/future distinctions are reliable
- number usage feels safe and publication-ready

==================================================
REVIEW METHOD
==================================================

For each article, review in 3 layers:

Layer 1 — Temporal trust reading
Ask:
- Can a careful reader clearly tell what is actual, what is preliminary, and what is forecast?
- Are completed years treated as completed?

Layer 2 — Editorial reading
Ask:
- Is this still worth reading as a premium market brief?
- Did Phase 15 preserve earlier quality gains?

Layer 3 — Regression reading
Ask:
- Did fixing tense introduce new awkwardness, flattening, or loss of clarity?
- Did prior interpretation gains regress?

==================================================
SCORING FRAME
==================================================

For each sample, score 1 to 5 on:

- completed_year_actual_enforcement
- preliminary_vs_actual_distinction
- consensus_guidance_separation
- completed_year_as_forecast_residue
- fact_forecast_separation
- interpretation_regression_guard
- counterpoint_regression_guard
- analytical_spine_regression_guard
- post1_post2_continuity_regression_guard
- investor_trustworthiness
- premium_tone
- temporal_trustworthiness
- numeric_trustworthiness

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

FM1. completed-year results written as forecasts
FM2. actual / preliminary / guidance / consensus boundaries blurred
FM3. fact statements temporally ambiguous
FM4. interpretation quality regressed while fixing tense
FM5. `[해석]` hedge-heavy formula returned
FM6. counterpoint quality regressed
FM7. Post2 continuity regressed
FM8. trust-breaking year/date mismatch remains

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
- Did Phase 15 materially improve real article quality?
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
- PHASE15_OUTPUT_GO
- PHASE15_OUTPUT_HOLD

Rule:
Use GO only if the actual newly published output is clearly and materially more trustworthy at the temporal fact layer, without unacceptable regression elsewhere.

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
  "completed_year_actual_enforcement": "PASS|WARN|FAIL",
  "preliminary_vs_actual_distinction": "PASS|WARN|FAIL",
  "consensus_guidance_separation": "PASS|WARN|FAIL",
  "completed_year_as_forecast_residue": "PASS|WARN|FAIL",
  "fact_forecast_separation": "PASS|WARN|FAIL",
  "interpretation_regression_guard": "PASS|WARN|FAIL",
  "counterpoint_regression_guard": "PASS|WARN|FAIL",
  "analytical_spine_regression_guard": "PASS|WARN|FAIL",
  "post1_post2_continuity_regression_guard": "PASS|WARN|FAIL",
  "investor_trustworthiness": "PASS|WARN|FAIL",
  "premium_tone": "PASS|WARN|FAIL",
  "temporal_trustworthiness": "PASS|WARN|FAIL",
  "numeric_trustworthiness": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION STANDARD
==================================================

Use this standard:

GO means:
- completed-year actuals are no longer written as forecasts
- actual / preliminary / guidance / consensus are clearly separated
- temporal trust is materially improved in the actual prose
- previous gains in interpretation and continuity are not meaningfully lost

HOLD means:
- completed-year result phrasing is still misleading
- temporal trust is still compromised
- corrections are inconsistent or partial in a trust-breaking way
- or Phase 15 fixed tense but caused unacceptable regression elsewhere

==================================================
IMPORTANT STYLE RULE
==================================================

Be blunt, practical, and editorially serious.
Do not give polite credit for implementation effort.
Judge only the real newly published output.
A temporally misleading article is a HOLD even if the prose sounds polished.

---

## Additional operator note

- Do not validate against old URLs or historical samples.
- Fresh current-run URL validation is mandatory.
- A major success signal is that 2024/2025 completed-year results are no longer written as projections in 2026 output.
- Future validation reports must include the full published body of both articles.

---

## Important

This task is not "did Phase 15 get implemented?"
This task is "did the newly published article become temporally trustworthy?"
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
`REPORT_PHASE15_REAL_OUTPUT_VALIDATION.md`

The detailed report must include:
- run audit
- sample source audit
- sample-by-sample review
- failure-mode regression check
- cross-sample diagnosis
- final gate JSON

AND MUST ALSO INCLUDE:

## Published Article Body Archive
### Post1 Full Body
[full published body here]

### Post2 Full Body
[full published body here]

Use this structure in the report:

# REPORT_PHASE15_REAL_OUTPUT_VALIDATION

## 1. Run Audit

## 2. Sample Source Audit

## 3. Executive Judgment

## 4. Sample-by-Sample Review

## 5. Failure-Mode Regression Check

## 6. Cross-Sample Diagnosis

## 7. Gate Decision

## 8. If HOLD: Next Required Action

## 9. Final Validation JSON

## 10. Published Article Body Archive
### Post1 Full Body

### Post2 Full Body

```json
{
  "fresh_run_executed": "PASS|FAIL",
  "fresh_publish_succeeded": "PASS|FAIL",
  "new_url_based_validation": "PASS|FAIL",
  "completed_year_actual_enforcement": "PASS|WARN|FAIL",
  "preliminary_vs_actual_distinction": "PASS|WARN|FAIL",
  "consensus_guidance_separation": "PASS|WARN|FAIL",
  "completed_year_as_forecast_residue": "PASS|WARN|FAIL",
  "fact_forecast_separation": "PASS|WARN|FAIL",
  "interpretation_regression_guard": "PASS|WARN|FAIL",
  "counterpoint_regression_guard": "PASS|WARN|FAIL",
  "analytical_spine_regression_guard": "PASS|WARN|FAIL",
  "post1_post2_continuity_regression_guard": "PASS|WARN|FAIL",
  "investor_trustworthiness": "PASS|WARN|FAIL",
  "premium_tone": "PASS|WARN|FAIL",
  "temporal_trustworthiness": "PASS|WARN|FAIL",
  "numeric_trustworthiness": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE15_REAL_OUTPUT_VALIDATION.md 읽고 실행해. 결과는 요약은 채팅, 상세는 MD로 제출해. 발행 본문 전문도 MD에 반드시 포함해.`
