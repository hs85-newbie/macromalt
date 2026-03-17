# PROMPT_PHASE15E_REAL_OUTPUT_VALIDATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15E 실출력 검증용 통합 실행 문서**입니다.

목적:
1. 신규 런 실행
2. 신규 발행 URL 확보
3. 신규 URL 본문 기준 실출력 검증
4. 현재 연도 과거 월(예: 2026년 2월) 집계 문장이 더 이상 `[전망]` + 예측 동사로 남지 않는지 판정
5. 결과는 요약은 채팅, 상세는 MD 파일로 제출
6. **발행 본문 전문을 MD 보고서에 반드시 포함**

---

## Claude Code 실행 지시문

You are running the real-output validation for the macromalt project after Phase 15E Current-Year Past-Month Settlement Fix implementation.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation was GO but real-output was HOLD.
- Phase 15A/15B improved compound tense correction coverage.
- Phase 15C improved Step3 temporal grounding and reader-facing transitions.
- Phase 15D stripped misapplied `[전망]` tags from settled facts.
- Phase 15E implementation is now GO.
- This task exists to validate whether Phase 15E materially improved the actual newly published article output.

Critical mission:
You must execute a fresh current-run validation and determine whether Phase 15E materially improved temporal trustworthiness for current-year past-month settled data in the actual published prose.

You must not stop at code inspection.
You must validate the real newly generated and newly published article outputs.

==================================================
NON-NEGOTIABLE EXECUTION RULES
==================================================

1. You must execute a NEW generation run using the current Phase 15E codebase.
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

Determine whether Phase 15E produced real article improvement in temporal trustworthiness for current-year past-month data.

This means validating whether the new articles are now:
- no longer treating already settled prior months in the current year as forecasts
- no longer using `[전망]` on clearly settled current-year past-month data
- no longer using future-style verbs for already reported current-year past-month figures
- still preserving true future monthly outlook when it is genuinely forward-looking
- maintaining prior gains in interpretation quality, hedge control, and reader-facing language

==================================================
MANDATORY WORKFLOW
==================================================

Follow this exact order:

Step 1.
Execute a fresh content generation run using the current Phase 15E codebase.

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
Judge whether Phase 15E actually improved real output quality.

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

A. Current-Year Past-Month Settlement Success
Check whether already completed months within the current year are now treated as settled factual periods.

Fail signals:
- in March 2026, January/February 2026 data is still framed as future expectation
- already published monthly figures still read like pending outcomes
- current-year past-month data is not recognized as completed

Pass signals:
- prior completed months in the current year read as settled/reporting statements
- monthly reported data no longer sounds forecast-like
- temporal trust at the month level is materially improved

B. `[전망]` Misuse on Settled Monthly Data
Check whether `[전망]` has been removed where it should not appear on current-year past-month settled lines.

Fail signals:
- `[전망]` still appears immediately before settled current-year past-month data
- labels continue to make already reported monthly figures look like forecasts

Pass signals:
- no misapplied `[전망]` remains on clearly settled current-year past-month statements
- labels align with reader-facing temporal reality

C. Future-Style Verb Removal on Settled Monthly Data
Check whether future-style verb residue is gone from those same lines.

Fail signals:
- settled monthly lines still use phrases like:
  - 늘어날 것으로 전망됩니다
  - 기록할 것으로 추정됩니다
  - 증가할 것으로 예상됩니다
  - similar forecast-style constructions
- tag may be fixed, but the verb still sounds like future expectation

Pass signals:
- future-style verbs are removed or converted
- the sentence reads as a settled reported fact
- tag + verb now work together rather than contradicting each other

D. True Future Monthly Forecast Preservation
Check whether genuine future monthly outlook still retains forecast framing where appropriate.

Fail signals:
- true future month or future export outlook has been flattened into settled factual wording
- the new fix overreaches into genuine forecasts

Pass signals:
- genuine future-looking monthly statements still keep appropriate forecast framing
- the fix appears selective rather than destructive

E. Current-Year Past-Month Log Plausibility
If logs or score metadata are available, inspect whether the current-year month settlement fix appears sensible.

Fail signals:
- logs suggest over-triggering on non-settled lines
- logs suggest correction was applied to clearly future-oriented monthly outlook

Pass signals:
- triggered lines correspond to obvious settled month misuse
- no obvious overreach appears

F. Completed-Year / Prior Fix Compatibility
Check that earlier gains are preserved:
- completed-year actual enforcement should remain intact
- misapplied `[전망]` tag stripping for settled annual results should still work

G. Internal Pipeline Language Safety
Check that `Post1`, `Post2`, `Post1의 결론에 따르면` etc. do not reappear in reader-facing prose.

H. Interpretation / Hedge Regression Guard
Check that Phase 15E did not undo prior gains:
- [해석] hedge-heavy formula should not materially return
- interpretation quality should not collapse while monthly temporal trust improves

I. Counterpoint / Spine / Continuity Regression Guard
Check that:
- counterpoint quality has not materially degraded
- analytical spine has not materially degraded
- Post1/Post2 continuity remains natural and reader-facing

J. Overall Temporal / Numeric Trustworthiness
Check overall publication trust.

==================================================
REVIEW METHOD
==================================================

For each article, review in 3 layers:

Layer 1 — Month-level temporal trust reading
Ask:
- Are current-year prior-month published figures treated as settled?
- Is `[전망]` still misused on those lines?
- Are future-style verbs still present where they should not be?

Layer 2 — Reader-facing reading
Ask:
- Does the article read naturally to a subscriber?
- Has monthly temporal cleanup improved trust without introducing awkwardness?
- Are internal workflow terms absent?

Layer 3 — Regression reading
Ask:
- Did monthly settlement correction cause overcorrection?
- Did prior interpretation/hedge/continuity gains regress?
- Did temporal trust actually improve, not just shift form?

==================================================
SCORING FRAME
==================================================

For each sample, score 1 to 5 on:

- current_year_past_month_settlement_success
- settled_month_jeonmang_removal
- settled_month_future_verb_correction
- true_future_month_forecast_preservation
- month_fix_log_plausibility
- completed_year_compatibility
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

FM1. current-year past-month data framed as forecast
FM2. `[전망]` remained on settled monthly data
FM3. future-style verb residue remained on settled monthly data
FM4. `[전망]` stripping overreached into genuine future monthly outlook
FM5. completed-year fixes regressed
FM6. internal pipeline labels leaked into published prose
FM7. [해석] hedge-heavy formula returned
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
- whether the current-year past-month settlement fix fired or not, if visible

## 1. Sample Source Audit
For each sample, state:
- source type: fresh published URL / fresh generated text
- whether it is full or partial
- whether it came from the CURRENT run
- whether confidence is limited for any reason

## 2. Executive Judgment
Answer directly:
- Did Phase 15E materially improve real article quality?
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
- PHASE15E_OUTPUT_GO
- PHASE15E_OUTPUT_HOLD

Rule:
Use GO only if the actual newly published output is clearly and materially more trustworthy at the current-year past-month temporal layer, without unacceptable regression elsewhere.

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
  "current_year_past_month_settlement_success": "PASS|WARN|FAIL",
  "settled_month_jeonmang_removal": "PASS|WARN|FAIL",
  "settled_month_future_verb_correction": "PASS|WARN|FAIL",
  "true_future_month_forecast_preservation": "PASS|WARN|FAIL",
  "month_fix_log_plausibility": "PASS|WARN|FAIL",
  "completed_year_compatibility": "PASS|WARN|FAIL",
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
- settled current-year past-month data no longer reads like forecast
- `[전망]` misuse is gone on those lines
- future-style verbs are gone on those lines
- genuine future monthly outlook is preserved
- previous gains in tense correction, interpretation, and continuity are not meaningfully lost

HOLD means:
- current-year past-month data still sounds forecast-like
- `[전망]` or future-style verbs remain on those settled lines
- the monthly fix overreaches into true future monthly outlook
- or Phase 15E fixed month-level issues but caused unacceptable regression elsewhere

==================================================
IMPORTANT STYLE RULE
==================================================

Be blunt, practical, and editorially serious.
Do not give polite credit for implementation effort.
Judge only the real newly published output.
A reader-facing publication that still treats already reported prior-month data as 전망 is a HOLD.

---

## Additional operator note

- Do not validate against old URLs or historical samples.
- Fresh current-run URL validation is mandatory.
- A major success signal is that March 2026 output no longer treats February 2026 reported data as future expectation.
- Another success signal is that genuine future monthly outlook still keeps forecast framing.
- Future validation reports must include the full published body of both articles.

---

## Important

This task is not "did Phase 15E get implemented?"
This task is "did the newly published article stop treating settled prior-month data as forecast?"
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
`REPORT_PHASE15E_REAL_OUTPUT_VALIDATION.md`

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

# REPORT_PHASE15E_REAL_OUTPUT_VALIDATION

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
  "current_year_past_month_settlement_success": "PASS|WARN|FAIL",
  "settled_month_jeonmang_removal": "PASS|WARN|FAIL",
  "settled_month_future_verb_correction": "PASS|WARN|FAIL",
  "true_future_month_forecast_preservation": "PASS|WARN|FAIL",
  "month_fix_log_plausibility": "PASS|WARN|FAIL",
  "completed_year_compatibility": "PASS|WARN|FAIL",
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

`PROMPT_PHASE15E_REAL_OUTPUT_VALIDATION.md 읽고 실행해. 결과는 요약은 채팅, 상세는 MD로 제출해. 발행 본문 전문도 MD에 반드시 포함해.`
