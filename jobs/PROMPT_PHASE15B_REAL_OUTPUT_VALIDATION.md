# PROMPT_PHASE15B_REAL_OUTPUT_VALIDATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15B 실출력 검증용 통합 실행 문서**입니다.

목적:
1. 신규 런 실행
2. 신규 발행 URL 확보
3. 신규 URL 본문 기준 실출력 검증
4. Phase 15B의 연결어미(`되며|되고|되어`) 커버 확장이 실제 발행문에서 완전하게 작동했는지 판정
5. 내부 파이프라인 용어(`Post1`, `Post2`)가 발행문에 노출되는지 점검
6. 결과는 요약은 채팅, 상세는 MD 파일로 제출
7. **발행 본문 전문을 MD 보고서에 반드시 포함**

---

## Claude Code 실행 지시문

You are running the real-output validation for the macromalt project after the Phase 15B Verb Ending Coverage Micro-Hotfix.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation was GO but real-output was HOLD.
- Phase 15A compound tense correction hotfix was implementation GO but real-output was HOLD.
- Phase 15B verb-ending coverage micro-hotfix is now implementation GO.
- This task exists to validate whether Phase 15B materially improved the actual newly published article output.

Critical mission:
You must execute a fresh current-run validation and determine whether Phase 15B materially improved temporal trustworthiness in the actual published prose.

You must not stop at code inspection.
You must validate the real newly generated and newly published article outputs.

==================================================
NON-NEGOTIABLE EXECUTION RULES
==================================================

1. You must execute a NEW generation run using the current Phase 15B codebase.
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

Determine whether Phase 15B produced real article improvement in temporal trustworthiness.

This means validating whether the new articles are now:
- no longer leaving mixed future-style residue with connective endings
- no longer producing phrases like:
  - 기록할 것으로 전망되며
  - 달성할 것으로 예상되며
  - 증가할 것으로 추정되어
  - similar mixed-tense hybrids
- correctly distinguishing completed-year actuals from forecasts
- still maintaining prior gains in interpretation quality, hedge control, and continuity
- not leaking internal pipeline language such as `Post1` / `Post2` into reader-facing prose

==================================================
MANDATORY WORKFLOW
==================================================

Follow this exact order:

Step 1.
Execute a fresh content generation run using the current Phase 15B codebase.

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
Judge whether Phase 15B actually improved real output quality.

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

A. Connective Ending Coverage Success
Check whether mixed future-style residue with connective endings is gone.

Fail signals:
- completed-year sentences still contain phrases like:
  - 기록할 것으로 전망되며
  - 달성할 것으로 예상되며
  - 증가할 것으로 추정되어
  - similar mixed-tense connective hybrids
- correction changed only part of the phrase and left future-style residue

Pass signals:
- connective-ending hybrids are fully removed
- corrected sentences read as completed factual outcomes
- no mixed-tense residue remains in those surface forms

B. Completed-Year Actual Enforcement
Check whether already-completed reporting periods are written as completed facts.

Fail signals:
- 2024 or 2025 full-year results in a 2026 article are still written with forecast/projection phrasing
- completed-year result is written with “예상”, “전망”, “기록할 것으로”, “달성할 것으로”, or equivalent future-style wording
- article leaves the reader unsure whether the result is actual or forecast

Pass signals:
- completed-year actuals are written directly as completed facts
- wording clearly indicates the period is already settled
- no misleading future-style treatment remains

C. Preliminary vs Actual Distinction
Check whether preliminary figures are clearly distinguished from settled actuals.

D. Consensus / Guidance / Forecast Separation
Check whether expectation language is properly separated from factual result language.

E. Section Placement Sanity
Check whether completed-year actual results are still being placed under [전망] or forecast-like sections in a misleading way.

Fail signals:
- completed-year actual figures appear under [전망] structure without clear qualification
- section labeling itself makes settled facts read like open forecasts

Pass signals:
- completed-year actuals appear in an appropriate factual/analytical context
- section structure does not undermine temporal trust

F. Internal Pipeline Language Leakage
Check whether internal labels such as:
- Post1
- Post2
- "Post1에서 도출된 결론"
- "Post2 기준으로"
or similar pipeline-facing wording appear in the published prose.

Fail signals:
- any reader-facing prose exposes internal pipeline terminology
- phrasing sounds like workflow metadata rather than editorial writing

Pass signals:
- no internal pipeline labels appear in the published text
- continuity is expressed in natural reader-facing language
- examples of acceptable phrasing include:
  - "[심층분석]에서 도출된 결론은 ..."
  - "앞서 살펴본 흐름을 종목 관점에서 보면 ..."
  - "이 흐름을 개별 종목에 적용하면 ..."
  - or other natural editorial transitions

If internal terms appear, explicitly quote them and mark as failure.

G. Interpretation / Hedge Regression Guard
Phase 15B should not break previous gains.

Check that:
- [해석] lines are not backsliding into hedge-heavy formulas
- Phase 14I improvements are not lost
- article does not become temporally correct but stylistically generic again

H. Counterpoint / Spine / Continuity Guard
Also ensure Phase 15B does not degrade:
- counterpoint quality
- analytical spine
- Post1/Post2 continuity
Note: continuity should be reader-facing and natural, not dependent on raw pipeline labels.

I. Temporal / Numeric Trustworthiness
Check overall publication trust.

==================================================
REVIEW METHOD
==================================================

For each article, review in 3 layers:

Layer 1 — Temporal trust reading
Ask:
- Can a careful reader clearly tell what is actual, what is preliminary, and what is forecast?
- Are completed years treated as completed?
- Is mixed-tense residue truly gone?

Layer 2 — Editorial reading
Ask:
- Is this still worth reading as a premium market brief?
- Did Phase 15B preserve earlier quality gains?
- Does continuity sound natural to a subscriber who has no idea what "Post1" means?

Layer 3 — Regression reading
Ask:
- Did fixing connective endings introduce awkward phrasing or flattening?
- Did prior interpretation gains regress?
- Did section structure still mislead despite corrected sentence endings?
- Did internal pipeline language leak into the prose?

==================================================
SCORING FRAME
==================================================

For each sample, score 1 to 5 on:

- connective_ending_coverage_success
- completed_year_actual_enforcement
- preliminary_vs_actual_distinction
- consensus_guidance_separation
- section_placement_sanity
- internal_pipeline_language_safety
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
FM2. mixed-tense hybrid remained after correction
FM3. actual / preliminary / guidance / consensus boundaries blurred
FM4. completed-year facts placed in misleading forecast sections
FM5. interpretation quality regressed while fixing tense
FM6. [해석] hedge-heavy formula returned
FM7. Post2 continuity regressed
FM8. trust-breaking year/date mismatch remains
FM9. internal pipeline labels leaked into published prose

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
- Did Phase 15B materially improve real article quality?
- Is the improvement enough to move forward?
- Or is another corrective phase still required?

## 3. Sample-by-Sample Review
For each article:
- what improved
- what still fails
- score table
- one-line editorial verdict

## 4. Failure-Mode Regression Check
For each of FM1–FM9, mark:
- IMPROVED / PARTIALLY IMPROVED / NOT IMPROVED / REGRESSED
and explain why.

## 5. Cross-Sample Diagnosis
Identify the remaining systemic bottlenecks, if any.

## 6. Gate Decision
Return one of:
- PHASE15B_OUTPUT_GO
- PHASE15B_OUTPUT_HOLD

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
  "connective_ending_coverage_success": "PASS|WARN|FAIL",
  "completed_year_actual_enforcement": "PASS|WARN|FAIL",
  "preliminary_vs_actual_distinction": "PASS|WARN|FAIL",
  "consensus_guidance_separation": "PASS|WARN|FAIL",
  "section_placement_sanity": "PASS|WARN|FAIL",
  "internal_pipeline_language_safety": "PASS|WARN|FAIL",
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
- mixed-tense residue with connective endings is no longer visible
- completed-year actuals are no longer written as forecasts
- section structure does not undermine temporal trust
- internal pipeline labels do not appear in reader-facing prose
- previous gains in interpretation and continuity are not meaningfully lost

HOLD means:
- mixed-tense residue still appears
- completed-year result phrasing is still misleading
- section placement still makes settled facts read like forecasts
- internal workflow language leaks into published prose
- or Phase 15B fixed tense but caused unacceptable regression elsewhere

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
- A major success signal is that phrases like “기록할 것으로 전망되며” no longer appear.
- Also treat any reader-facing “Post1/Post2” wording as a quality failure.

---

## Important

This task is not "did Phase 15B get implemented?"
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
`REPORT_PHASE15B_REAL_OUTPUT_VALIDATION.md`

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

# REPORT_PHASE15B_REAL_OUTPUT_VALIDATION

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
  "connective_ending_coverage_success": "PASS|WARN|FAIL",
  "completed_year_actual_enforcement": "PASS|WARN|FAIL",
  "preliminary_vs_actual_distinction": "PASS|WARN|FAIL",
  "consensus_guidance_separation": "PASS|WARN|FAIL",
  "section_placement_sanity": "PASS|WARN|FAIL",
  "internal_pipeline_language_safety": "PASS|WARN|FAIL",
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

`PROMPT_PHASE15B_REAL_OUTPUT_VALIDATION.md 읽고 실행해. 결과는 요약은 채팅, 상세는 MD로 제출해. 발행 본문 전문도 MD에 반드시 포함해.`
