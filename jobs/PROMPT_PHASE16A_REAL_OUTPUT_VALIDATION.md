# PROMPT_PHASE16A_REAL_OUTPUT_VALIDATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 16A 실출력 검증용 통합 실행 문서**입니다.

목적:
1. 신규 런 실행
2. 신규 발행 URL 확보
3. 신규 URL 본문 기준 실출력 검증
4. **Temporal SSOT가 실제 출력 prose를 지배하는지 판정**
5. 현재 연도 과거 월(예: 2026년 2월) 집계 문장이 더 이상 `[전망]` + 예측 동사로 남지 않는지 판정
6. 진짜 미래 전망 문장이 보존되는지 판정
7. `p16_ssot_run`, `p15f_strip` 진단값이 실제 출력과 부합하는지 판정
8. 결과는 요약은 채팅, 상세는 MD 파일로 제출
9. **발행 본문 전문을 MD 보고서에 반드시 포함**

---

## Claude Code 실행 지시문

You are running the real-output validation for the macromalt project after Phase 16 Temporal State Normalization implementation.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation was GO but real-output was HOLD.
- Phase 15A/15B improved compound tense correction coverage.
- Phase 15C improved Step3 temporal grounding and reader-facing transitions.
- Phase 15D stripped misapplied `[전망]` tags from settled facts.
- Phase 15E improved current-year past-month settlement handling but still relied on patch-style fixes.
- Phase 16 implementation is now GO on static verification.
- Phase 16 introduced a runtime Temporal SSOT so GPT, Gemini Step3, and post-processing should now follow one normalized temporal policy.
- This task exists to validate whether Phase 16 materially improved the actual newly published article output.

Critical mission:
You must execute a fresh current-run validation and determine whether Phase 16 materially improved temporal trustworthiness in the actual published prose by making one runtime temporal policy dominate all layers.

You must not stop at code inspection.
You must validate the real newly generated and newly published article outputs.

==================================================
NON-NEGOTIABLE EXECUTION RULES
==================================================

1. You must execute a NEW generation run using the current Phase 16 codebase.
2. You must publish NEW outputs to WordPress.
3. You must retrieve the NEW live URLs from the CURRENT run.
4. You must validate using ONLY those NEW URLs from the CURRENT run.
5. You must NOT use old logs, old URLs, old article text, historical samples, or previously reviewed outputs as the validation basis.
6. If fresh publishing succeeds, NEW URL-based review is mandatory.
7. If fresh generation succeeds but publishing fails, review the fresh generated full text directly and explicitly mark URL-based validation as incomplete.
8. If fresh generation itself fails, report the blockage clearly and stop.
9. Do NOT ask me which option to use if the run can be executed directly.
10. Do NOT return a plan or memo instead of performing the task.
11. If `p16_ssot_run` or `p15f_strip` is available in scores, logs, or metadata, you must inspect it.
12. If those diagnostics are unavailable, explicitly mark that diagnostic visibility is incomplete.

==================================================
PRIMARY GOAL
==================================================

Determine whether Phase 16 produced real article improvement in temporal trustworthiness through Temporal SSOT normalization.

This means validating whether the new articles are now:
- no longer treating already settled prior months in the current year as forecasts
- no longer using `[전망]` on clearly settled current-year past-month data
- no longer using future-style verbs for already reported current-year past-month figures
- still preserving true future monthly outlook when it is genuinely forward-looking
- showing evidence that one normalized temporal policy is driving the prose across GPT / Step3 / post-processing
- maintaining prior gains in interpretation quality, hedge control, and reader-facing language

==================================================
MANDATORY WORKFLOW
==================================================

Follow this exact order:

Step 1.
Execute a fresh content generation run using the current Phase 16 codebase.

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
Inspect available logs, scores, or metadata for `p16_ssot_run` and `p15f_strip`.

Step 8.
Judge whether Phase 16 actually improved real output quality.

Step 9.
Return a strict validation report with GO/HOLD judgment.

==================================================
SOURCE-OF-TRUTH POLICY
==================================================

For this task, the source of truth is:

1. NEWLY GENERATED + NEWLY PUBLISHED WordPress URLs from the CURRENT run
2. If publishing fails, NEWLY GENERATED full text from the CURRENT run only
3. Diagnostic logs / score metadata from the CURRENT run only
4. Nothing historical should be treated as an acceptable substitute for final validation

Validation based on historical outputs is invalid for this task.

==================================================
WHAT YOU MUST TEST
==================================================

You must evaluate all of the following from the actual newly published output.

A. Temporal SSOT Dominance
Check whether the prose now behaves as if one normalized temporal policy is controlling the article.

Fail signals:
- GPT prose, Step3 revisions, and post-processing seem to disagree about tense/state
- annual/m monthly settled facts and future outlook are still mixed inconsistently
- different sections imply different temporal interpretations for the same kind of data

Pass signals:
- the article reads as though one coherent temporal policy governs all layers
- settled facts, preliminary data, guidance, consensus, and true forecasts are separated more consistently
- there is materially less layer-to-layer contradiction

B. Current-Year Past-Month Settlement Success
Check whether already completed months within the current year are now treated as settled factual periods.

Fail signals:
- in March 2026, January/February 2026 data is still framed as future expectation
- already published monthly figures still read like pending outcomes
- current-year past-month data is not recognized as completed

Pass signals:
- prior completed months in the current year read as settled/reporting statements
- monthly reported data no longer sounds forecast-like
- temporal trust at the month level is materially improved

C. `[전망]` Misuse on Settled Monthly Data
Check whether `[전망]` has been removed where it should not appear on current-year past-month settled lines.

Fail signals:
- `[전망]` still appears immediately before settled current-year past-month data
- labels continue to make already reported monthly figures look like forecasts

Pass signals:
- no misapplied `[전망]` remains on clearly settled current-year past-month statements
- labels align with reader-facing temporal reality

D. Future-Style Verb Removal on Settled Monthly Data
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

E. True Future Monthly Forecast Preservation
Check whether genuine future monthly outlook still retains forecast framing where appropriate.

Fail signals:
- true future month or future export outlook has been flattened into settled factual wording
- the new fix overreaches into genuine forecasts

Pass signals:
- genuine future-looking monthly statements still keep appropriate forecast framing
- the fix appears selective rather than destructive

F. Diagnostic Plausibility (`p16_ssot_run`, `p15f_strip`)
If logs or score metadata are available, inspect whether diagnostics align with the article reality.

Fail signals:
- `p16_ssot_run` suggests SSOT was active but prose still clearly violates temporal policy
- `p15f_strip` suggests stripping fired on lines that are genuinely future-looking
- diagnostics imply success while output contradicts that success

Pass signals:
- diagnostics line up with obvious reader-facing corrections
- stripping events correspond to settled month misuse
- SSOT execution visibility is plausible and consistent with the prose

G. Completed-Year / Prior Fix Compatibility
Check that earlier gains are preserved:
- completed-year actual enforcement should remain intact
- misapplied `[전망]` tag stripping for settled annual results should still work

H. Internal Pipeline Language Safety
Check that `Post1`, `Post2`, `Post1의 결론에 따르면` etc. do not reappear in reader-facing prose.

I. Interpretation / Hedge Regression Guard
Check that Phase 16 did not undo prior gains:
- [해석] hedge-heavy formula should not materially return
- interpretation quality should not collapse while temporal trust improves

J. Counterpoint / Spine / Continuity Regression Guard
Check that:
- counterpoint quality has not materially degraded
- analytical spine has not materially degraded
- Post1/Post2 continuity remains natural and reader-facing

K. Overall Temporal / Numeric Trustworthiness
Check overall publication trust.

==================================================
REVIEW METHOD
==================================================

For each article, review in 4 layers:

Layer 1 — Temporal state reading
Ask:
- Are settled facts, preliminary facts, consensus, guidance, and forecasts being distinguished coherently?
- Do current-year prior-month published figures read as settled?
- Is `[전망]` still misused on those lines?
- Are future-style verbs still present where they should not be?

Layer 2 — Reader-facing reading
Ask:
- Does the article read naturally to a subscriber?
- Has temporal cleanup improved trust without introducing stiffness?
- Are internal workflow terms absent?

Layer 3 — Diagnostic reading
Ask:
- Does `p16_ssot_run` appear to reflect the output reality?
- Does `p15f_strip` appear sensible and selective?
- Is there any mismatch between diagnostic confidence and visible prose?

Layer 4 — Regression reading
Ask:
- Did Temporal SSOT cause overcorrection?
- Did prior interpretation/hedge/continuity gains regress?
- Did temporal trust actually improve, not just shift form?

==================================================
SCORING FRAME
==================================================

For each sample, score 1 to 5 on:

- temporal_ssot_dominance
- current_year_past_month_settlement_success
- settled_month_jeonmang_removal
- settled_month_future_verb_correction
- true_future_month_forecast_preservation
- diagnostic_plausibility
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
FM9. multiple layers still independently reinterpret time instead of following one policy
FM10. diagnostics say success but article prose contradicts diagnostics

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
- whether `p16_ssot_run` was visible and what it indicated
- whether `p15f_strip` was visible and what it indicated

## 1. Sample Source Audit
For each sample, state:
- source type: fresh published URL / fresh generated text
- whether it is full or partial
- whether it came from the CURRENT run
- whether confidence is limited for any reason

## 2. Executive Judgment
Answer directly:
- Did Phase 16 materially improve real article quality?
- Is the improvement enough to move forward?
- Or is another corrective phase still required?

## 3. Sample-by-Sample Review
For each article:
- what improved
- what still fails
- score table
- one-line editorial verdict

## 4. Failure-Mode Regression Check
For each of FM1–FM10, mark:
- IMPROVED / PARTIALLY IMPROVED / NOT IMPROVED / REGRESSED
and explain why.

## 5. Cross-Sample Diagnosis
Identify the remaining systemic bottlenecks, if any.

## 6. Gate Decision
Return one of:
- PHASE16A_OUTPUT_GO
- PHASE16A_OUTPUT_HOLD

Rule:
Use GO only if the actual newly published output is clearly and materially more trustworthy at the temporal-policy layer, without unacceptable regression elsewhere.

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
  "temporal_ssot_dominance": "PASS|WARN|FAIL",
  "current_year_past_month_settlement_success": "PASS|WARN|FAIL",
  "settled_month_jeonmang_removal": "PASS|WARN|FAIL",
  "settled_month_future_verb_correction": "PASS|WARN|FAIL",
  "true_future_month_forecast_preservation": "PASS|WARN|FAIL",
  "diagnostic_plausibility": "PASS|WARN|FAIL",
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
- one runtime temporal policy appears to dominate the prose
- settled current-year past-month data no longer reads like forecast
- `[전망]` misuse is gone on those lines
- future-style verbs are gone on those lines
- genuine future monthly outlook is preserved
- diagnostics broadly agree with reader-facing reality
- previous gains in tense correction, interpretation, and continuity are not meaningfully lost

HOLD means:
- multiple layers still appear to disagree about temporal state
- current-year past-month data still sounds forecast-like
- `[전망]` or future-style verbs remain on those settled lines
- the month-level fix or SSOT overreaches into true future monthly outlook
- diagnostics look successful but prose still contradicts them
- or Phase 16 improved temporal logic but caused unacceptable regression elsewhere

==================================================
IMPORTANT STYLE RULE
==================================================

Be blunt, practical, and editorially serious.
Do not give polite credit for implementation effort.
Judge only the real newly published output.
A reader-facing publication that still treats already reported prior-month data as 전망 is a HOLD.
A publication whose diagnostics claim success while prose still contradicts that claim is also a HOLD.

---

## Additional operator note

- Do not validate against old URLs or historical samples.
- Fresh current-run URL validation is mandatory.
- A major success signal is that March 2026 output no longer treats February 2026 reported data as future expectation.
- Another success signal is that genuine future monthly outlook still keeps forecast framing.
- Another success signal is that logs / scores show plausible `p16_ssot_run` and selective `p15f_strip` behavior.
- Future validation reports must include the full published body of both articles.

---

## Important

This task is not "did Phase 16 get implemented?"
This task is "did the newly published article actually obey a coherent temporal policy?"
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
- whether `p16_ssot_run` / `p15f_strip` were visible and meaningful

### 2) Full report as Markdown file
Also create and provide a **detailed MD report file**.

Recommended filename:
`REPORT_PHASE16A_REAL_OUTPUT_VALIDATION.md`

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

# REPORT_PHASE16A_REAL_OUTPUT_VALIDATION

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
  "temporal_ssot_dominance": "PASS|WARN|FAIL",
  "current_year_past_month_settlement_success": "PASS|WARN|FAIL",
  "settled_month_jeonmang_removal": "PASS|WARN|FAIL",
  "settled_month_future_verb_correction": "PASS|WARN|FAIL",
  "true_future_month_forecast_preservation": "PASS|WARN|FAIL",
  "diagnostic_plausibility": "PASS|WARN|FAIL",
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

`PROMPT_PHASE16A_REAL_OUTPUT_VALIDATION.md 읽고 실행해. 결과는 요약은 채팅, 상세는 MD로 제출해. 발행 본문 전문도 MD에 반드시 포함해.`
