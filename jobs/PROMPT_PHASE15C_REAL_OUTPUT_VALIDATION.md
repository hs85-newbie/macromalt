# PROMPT_PHASE15C_REAL_OUTPUT_VALIDATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15C 실출력 검증용 통합 실행 문서**입니다.

목적:
1. 신규 런 실행
2. 신규 발행 URL 확보
3. 신규 URL 본문 기준 실출력 검증
4. Gemini Step3의 완료 연도 `[전망]` 오주입이 실제 발행문에서 사라졌는지 판정
5. Post2 독자-facing 문장에서 `Post1`, `Post2` 같은 내부 파이프라인 용어가 완전히 제거됐는지 판정
6. 결과는 요약은 채팅, 상세는 MD 파일로 제출
7. **발행 본문 전문을 MD 보고서에 반드시 포함**

---

## Claude Code 실행 지시문

You are running the real-output validation for the macromalt project after Phase 15C Step3 Temporal Context Injection + Post2 Internal Label Fix.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation was GO but real-output was HOLD.
- Phase 15A and 15B improved tense correction coverage.
- Phase 15C implementation is now GO.
- This task exists to validate whether Phase 15C materially improved the actual newly published article output.

Critical mission:
You must execute a fresh current-run validation and determine whether Phase 15C materially improved publication-facing temporal trustworthiness and reader-facing language quality.

You must not stop at code inspection.
You must validate the real newly generated and newly published article outputs.

==================================================
NON-NEGOTIABLE EXECUTION RULES
==================================================

1. You must execute a NEW generation run using the current Phase 15C codebase.
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

Determine whether Phase 15C produced real article improvement in two specific areas:

1. Step3 temporal misclassification control
   - completed-year actual results should no longer be wrapped in `[전망]` or similar forecast-like framing

2. Post2 reader-facing transition quality
   - internal workflow language such as `Post1`, `Post2`, `Post1의 결론에 따르면` should no longer appear in published prose

This validation should also confirm that prior gains in interpretation quality, hedge control, and temporal correction coverage have not regressed.

==================================================
MANDATORY WORKFLOW
==================================================

Follow this exact order:

Step 1.
Execute a fresh content generation run using the current Phase 15C codebase.

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
Judge whether Phase 15C actually improved real output quality.

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

A. Completed-Year Forecast-Label Misuse
Check whether completed-year actual results are still being placed under `[전망]` or otherwise framed as forecasts.

Fail signals:
- 2024 or 2025 annual actual results appear inside `[전망]` sections without clear justification
- Step3 seems to have reintroduced forecast framing onto settled completed-year facts
- completed-year actuals are labeled in a way that weakens reader trust

Pass signals:
- completed-year actuals are treated as settled facts or analytical inputs
- `[전망]` is not misapplied to already completed annual results
- temporal framing is aligned with the publication year context

B. Step3 Temporal Grounding Visibility
Check whether the final prose suggests Step3 is now correctly grounded in the publication year context.

Fail signals:
- 2024/2025 are treated as if still ongoing in a 2026 article
- completed-year actuals are rewritten into forecast-like language
- the same category of misclassification seen before remains visible

Pass signals:
- completed years are consistently treated as completed
- temporal wording feels year-aware and stable
- no obvious Step3 temporal confusion remains

C. Internal Pipeline Label Leakage
Check whether internal labels such as:
- Post1
- Post2
- Post1의 결론에 따르면
- Post1에서 도출된 결론은
- Post2 기준으로
or similar workflow phrasing appear anywhere in the published prose.

Fail signals:
- any internal pipeline term appears in reader-facing text
- continuity language sounds like internal metadata rather than editorial writing

Pass signals:
- no internal pipeline terms appear
- continuity is expressed in natural editorial language
- transitions make sense to a subscriber who does not know the production workflow

D. Post2 Reader-Facing Transition Quality
Check whether Post2 now transitions naturally from the analytical frame.

Fail signals:
- transition language sounds mechanical or workflow-like
- continuity still depends on hidden internal labels
- the opening feels like system glue rather than editorial prose

Pass signals:
- Post2 starts naturally from the already established market/theme frame
- transitions feel like part of a premium brief
- continuity is clear without exposing internal structure

E. Completed-Year Tense Correction Residue
Check whether earlier mixed-tense residue still appears.

Fail signals:
- phrases like:
  - 기록할 것으로 집계됐습니다
  - 달성할 것으로 전망되며
  - 증가할 것으로 추정되어
  or similar hybrids remain visible

Pass signals:
- compound mixed-tense hybrids are gone
- completed-year result lines read as completed outcomes

F. Interpretation / Hedge Regression Guard
Check that Phase 15C did not undo prior gains:
- [해석] hedge-heavy formula should not reappear materially
- interpretation quality should not collapse while temporal trust is improved

G. Counterpoint / Spine / Continuity Regression Guard
Check that:
- counterpoint quality has not materially degraded
- analytical spine has not materially degraded
- Post1/Post2 continuity remains functional and natural

H. Overall Temporal / Numeric Trustworthiness
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
- Are completed years treated as completed?
- Is `[전망]` misused on settled annual results?
- Is mixed-tense residue truly gone?

Layer 2 — Reader-facing language reading
Ask:
- Would a subscriber ever see internal workflow terms?
- Does Post2 continuity sound editorially natural?
- Does the article read like a publication, not a pipeline artifact?

Layer 3 — Regression reading
Ask:
- Did fixing Step3 context and label leakage create awkwardness or regressions?
- Did prior interpretation and hedge gains survive?
- Did section structure still mislead despite improved sentence wording?

==================================================
SCORING FRAME
==================================================

For each sample, score 1 to 5 on:

- completed_year_forecast_label_control
- step3_temporal_grounding_visibility
- internal_pipeline_label_safety
- post2_reader_facing_transition_quality
- completed_year_tense_residue_control
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
FM6. interpretation quality regressed while fixing tense
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

## 1. Sample Source Audit
For each sample, state:
- source type: fresh published URL / fresh generated text
- whether it is full or partial
- whether it came from the CURRENT run
- whether confidence is limited for any reason

## 2. Executive Judgment
Answer directly:
- Did Phase 15C materially improve real article quality?
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
- PHASE15C_OUTPUT_GO
- PHASE15C_OUTPUT_HOLD

Rule:
Use GO only if the actual newly published output is clearly and materially more trustworthy at the temporal fact layer and more natural at the reader-facing language layer, without unacceptable regression elsewhere.

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
  "completed_year_forecast_label_control": "PASS|WARN|FAIL",
  "step3_temporal_grounding_visibility": "PASS|WARN|FAIL",
  "internal_pipeline_label_safety": "PASS|WARN|FAIL",
  "post2_reader_facing_transition_quality": "PASS|WARN|FAIL",
  "completed_year_tense_residue_control": "PASS|WARN|FAIL",
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
- completed-year actuals are no longer pushed under `[전망]`
- Step3 no longer visibly misreads 2024/2025 as ongoing/future years
- no internal pipeline labels appear in published prose
- Post2 continuity reads naturally to a subscriber
- previous gains in interpretation and continuity are not meaningfully lost

HOLD means:
- completed-year result phrasing is still undermined by `[전망]`
- Step3 temporal confusion still appears
- internal workflow language still leaks into reader-facing text
- continuity still sounds like production metadata
- or Phase 15C fixed one issue but caused unacceptable regression elsewhere

==================================================
IMPORTANT STYLE RULE
==================================================

Be blunt, practical, and editorially serious.
Do not give polite credit for implementation effort.
Judge only the real newly published output.
A reader-facing publication that still exposes internal workflow or temporal confusion is a HOLD.

---

## Additional operator note

- Do not validate against old URLs or historical samples.
- Fresh current-run URL validation is mandatory.
- A major success signal is that no completed-year actual result appears under `[전망]`.
- Another major success signal is that no subscriber-facing sentence contains `Post1` or similar workflow wording.
- Future validation reports must include the full published body of both articles.

---

## Important

This task is not "did Phase 15C get implemented?"
This task is "did the newly published article stop sounding temporally misleading and editor-internal?"
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
`REPORT_PHASE15C_REAL_OUTPUT_VALIDATION.md`

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

# REPORT_PHASE15C_REAL_OUTPUT_VALIDATION

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
  "completed_year_forecast_label_control": "PASS|WARN|FAIL",
  "step3_temporal_grounding_visibility": "PASS|WARN|FAIL",
  "internal_pipeline_label_safety": "PASS|WARN|FAIL",
  "post2_reader_facing_transition_quality": "PASS|WARN|FAIL",
  "completed_year_tense_residue_control": "PASS|WARN|FAIL",
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

`PROMPT_PHASE15C_REAL_OUTPUT_VALIDATION.md 읽고 실행해. 결과는 요약은 채팅, 상세는 MD로 제출해. 발행 본문 전문도 MD에 반드시 포함해.`
