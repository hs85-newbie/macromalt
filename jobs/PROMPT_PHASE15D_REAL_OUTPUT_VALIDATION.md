# PROMPT_PHASE15D_REAL_OUTPUT_VALIDATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15D 실출력 검증용 통합 실행 문서**입니다.

목적:
1. 신규 런 실행
2. 신규 발행 URL 확보
3. 신규 URL 본문 기준 실출력 검증
4. 확정 실적/확정 과거 월 문장 앞 `[전망]` 오주입이 실제 발행문에서 제거됐는지 판정
5. 결과는 요약은 채팅, 상세는 MD 파일로 제출
6. **발행 본문 전문을 MD 보고서에 반드시 포함**

---

## Claude Code 실행 지시문

You are running the real-output validation for the macromalt project after Phase 15D Jeonmang Tag Strip implementation.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation was GO but real-output was HOLD.
- Phase 15A/15B improved compound tense correction coverage.
- Phase 15C addressed Step3 temporal context and internal label leakage.
- Phase 15D implementation is now GO.
- This task exists to validate whether Phase 15D materially improved the actual newly published article output.

Critical mission:
You must execute a fresh current-run validation and determine whether Phase 15D materially improved publication-facing temporal trustworthiness by stripping misapplied `[전망]` tags from settled factual statements.

You must not stop at code inspection.
You must validate the real newly generated and newly published article outputs.

==================================================
NON-NEGOTIABLE EXECUTION RULES
==================================================

1. You must execute a NEW generation run using the current Phase 15D codebase.
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

Determine whether Phase 15D produced real article improvement in publication-facing temporal trustworthiness.

This means validating whether the new articles are now:
- no longer displaying `[전망]` in front of completed-year actual results
- no longer displaying `[전망]` in front of clearly settled past-month figures
- still preserving true forward-looking `[전망]` statements
- maintaining prior gains in tense correction, interpretation quality, hedge control, and reader-facing transitions

==================================================
MANDATORY WORKFLOW
==================================================

Follow this exact order:

Step 1.
Execute a fresh content generation run using the current Phase 15D codebase.

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
Judge whether Phase 15D actually improved real output quality.

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

A. Misapplied [전망] Tag Removal
Check whether `[전망]` has been removed where it should not appear.

Fail signals:
- `[전망]` still appears immediately before completed-year actual results
- `[전망]` still appears before clearly settled past-month figures
- reader-facing prose still frames settled facts as open forecasts because of leftover `[전망]`

Pass signals:
- no misapplied `[전망]` remains on settled factual statements
- completed-year and settled past-month facts read as facts, not forecasts
- reader trust is no longer undermined by label misuse

B. True Forecast Preservation
Check whether genuine forward-looking content still keeps appropriate forecast labeling.

Fail signals:
- legitimate future scenario or forward-looking statements have lost `[전망]` incorrectly
- true forecasts were flattened into factual/settled statements

Pass signals:
- future-oriented statements still retain appropriate forecast framing
- stripping logic appears selective, not destructive

C. Completed-Year Actual Enforcement
Check whether already-completed reporting periods are written as completed facts.

Fail signals:
- 2024 or 2025 full-year results in a 2026 article are still written with forecast/projection phrasing
- completed-year result is written with misleading future-style treatment
- article leaves the reader unsure whether the result is actual or forecast

Pass signals:
- completed-year actuals are written directly as completed facts
- wording clearly indicates the period is already settled
- no misleading future-style treatment remains

D. Past-Month Settlement Sanity
Check whether clearly settled prior-month figures are also treated as settled facts.

Fail signals:
- clearly completed monthly or near-term published figures are still labeled or framed as forecasts
- article weakens trust by making finished periods sound pending

Pass signals:
- settled monthly figures sound settled
- month-level temporal trust is preserved

E. Jeonmang Strip Log Plausibility
If logs or score metadata are available, inspect whether `p13_scores["jeonmang_strip"]["log"]` appears sensible.

Fail signals:
- removed items look like genuine forward-looking sentences that should have been preserved
- log suggests over-stripping

Pass signals:
- removed items correspond to clear misapplied `[전망]` cases
- no obvious overreach appears

F. Internal Pipeline Language Regression Guard
Check that internal labels such as `Post1`, `Post2`, `Post1의 결론에 따르면` do not reappear.

G. Interpretation / Hedge Regression Guard
Check that Phase 15D did not undo prior gains:
- [해석] hedge-heavy formula should not materially return
- interpretation quality should not collapse while temporal labels improve

H. Counterpoint / Spine / Continuity Regression Guard
Check that:
- counterpoint quality has not materially degraded
- analytical spine has not materially degraded
- Post1/Post2 continuity remains natural and reader-facing

I. Overall Temporal / Numeric Trustworthiness
Check overall publication trust.

==================================================
REVIEW METHOD
==================================================

For each article, review in 3 layers:

Layer 1 — Label trust reading
Ask:
- Does `[전망]` still appear where it obviously should not?
- Are settled facts clearly readable as settled facts?
- Are true forecasts still preserved?

Layer 2 — Reader-facing reading
Ask:
- Does the article read naturally to a subscriber?
- Has label cleanup improved trust without introducing awkwardness?
- Are internal workflow terms absent?

Layer 3 — Regression reading
Ask:
- Did `[전망]` stripping cause overcorrection?
- Did prior interpretation/hedge/continuity gains regress?
- Did temporal trust actually improve, not just shift form?

==================================================
SCORING FRAME
==================================================

For each sample, score 1 to 5 on:

- jeonmang_tag_misuse_removal
- true_forecast_preservation
- completed_year_actual_enforcement
- past_month_settlement_sanity
- jeonmang_strip_log_plausibility
- internal_pipeline_label_safety
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

FM1. completed-year actuals pushed under `[전망]`
FM2. Step3 treated 2024/2025 like ongoing years
FM3. mixed-tense residue remained after correction
FM4. internal pipeline labels leaked into published prose
FM5. Post2 continuity sounded like workflow metadata
FM6. [해석] hedge-heavy formula returned
FM7. trust-breaking year/date mismatch remains
FM8. `[전망]` stripping overreached and removed genuine forecast labeling

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
- whether `jeonmang_strip` fired or not, if visible

## 1. Sample Source Audit
For each sample, state:
- source type: fresh published URL / fresh generated text
- whether it is full or partial
- whether it came from the CURRENT run
- whether confidence is limited for any reason

## 2. Executive Judgment
Answer directly:
- Did Phase 15D materially improve real article quality?
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
- PHASE15D_OUTPUT_GO
- PHASE15D_OUTPUT_HOLD

Rule:
Use GO only if the actual newly published output is clearly and materially more trustworthy at the label/temporal fact layer, without unacceptable regression elsewhere.

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
  "jeonmang_tag_misuse_removal": "PASS|WARN|FAIL",
  "true_forecast_preservation": "PASS|WARN|FAIL",
  "completed_year_actual_enforcement": "PASS|WARN|FAIL",
  "past_month_settlement_sanity": "PASS|WARN|FAIL",
  "jeonmang_strip_log_plausibility": "PASS|WARN|FAIL",
  "internal_pipeline_label_safety": "PASS|WARN|FAIL",
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
- misapplied `[전망]` tags are no longer visible on settled facts
- true forecast labeling is preserved where it should be
- completed-year and settled past-month facts read as facts
- internal pipeline labels do not appear in published prose
- previous gains in interpretation and continuity are not meaningfully lost

HOLD means:
- settled facts are still weakened by `[전망]` misuse
- `[전망]` stripping overreaches into genuine future content
- internal workflow language leaks into reader-facing text
- or Phase 15D fixed labels but caused unacceptable regression elsewhere

==================================================
IMPORTANT STYLE RULE
==================================================

Be blunt, practical, and editorially serious.
Do not give polite credit for implementation effort.
Judge only the real newly published output.
A reader-facing publication that still mislabels settled facts as 전망 is a HOLD.

---

## Additional operator note

- Do not validate against old URLs or historical samples.
- Fresh current-run URL validation is mandatory.
- A major success signal is that no settled factual line still carries `[전망]`.
- Another major success signal is that genuine future-looking lines still keep forecast framing.
- Future validation reports must include the full published body of both articles.

---

## Important

This task is not "did Phase 15D get implemented?"
This task is "did the newly published article stop mislabeling settled facts as `[전망]`?"
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
`REPORT_PHASE15D_REAL_OUTPUT_VALIDATION.md`

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

# REPORT_PHASE15D_REAL_OUTPUT_VALIDATION

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
  "jeonmang_tag_misuse_removal": "PASS|WARN|FAIL",
  "true_forecast_preservation": "PASS|WARN|FAIL",
  "completed_year_actual_enforcement": "PASS|WARN|FAIL",
  "past_month_settlement_sanity": "PASS|WARN|FAIL",
  "jeonmang_strip_log_plausibility": "PASS|WARN|FAIL",
  "internal_pipeline_label_safety": "PASS|WARN|FAIL",
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

`PROMPT_PHASE15D_REAL_OUTPUT_VALIDATION.md 읽고 실행해. 결과는 요약은 채팅, 상세는 MD로 제출해. 발행 본문 전문도 MD에 반드시 포함해.`
