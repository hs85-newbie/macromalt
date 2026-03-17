# PROMPT_PHASE15_TEMPORAL_TENSE_ENFORCEMENT.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15 — 과거 완료 연도 실적의 시제 구분 강제** 통합 실행 문서입니다.

목적:
1. 이미 완료된 연도(예: 2024년, 2025년) 실적을 `예상/전망`처럼 쓰지 못하게 강제
2. 확정 실적 / 잠정 실적 / 컨센서스 / 가이던스 / 미래 전망을 명확히 분리
3. Post1/Post2 모두에서 시제 신뢰성을 높여 독자 신뢰를 끌어올림
4. 결과는 요약은 채팅, 상세는 MD 파일로 제출
5. **발행 본문 전문을 MD 보고서에 반드시 포함**

---

## Claude Code 실행 지시문

You are implementing the next quality-improvement phase for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14 implementation was GO but real-output was HOLD.
- Phase 14H targeted rewrite replacement hotfix was implemented.
- Phase 14I Interpretation Hedge Clamp reached real-output GO for its target scope.
- The next highest-priority bottleneck is now clear:
  completed-year company results are still sometimes written as forecasts/projections in published articles.
- This directly damages reader trust at the fact layer.

Your task:
Implement **Phase 15 — Temporal Tense Enforcement for Completed-Year Results**.

This is a focused quality phase aimed at temporal trustworthiness in financial writing.

==================================================
PRIMARY OBJECTIVE
==================================================

Prevent already-completed reporting periods from being written as forecasts.

This phase succeeds only if the system becomes materially better at:
1. distinguishing completed-year actuals from future-year forecasts
2. separating actual / provisional / consensus / guidance / forecast language
3. preventing stale-year results from being phrased as pending outcomes
4. making final published prose temporally trustworthy for a careful investor reader

==================================================
ROOT PROBLEM TO SOLVE
==================================================

Observed failure mode:
- articles published in 2026 still described 2024 company results as projections or expected outcomes
- this is not merely a style issue; it is a trust and factuality issue
- readers should never have to guess whether a completed year is settled fact or still a projection

New principle:
If a reporting period is already complete relative to the run date, the default stance must be factual past-tense treatment unless the source explicitly indicates otherwise.

==================================================
TRACK A — TEMPORAL CLASSIFICATION
==================================================

Implement a stronger classification layer for company-result statements.

A1. Distinguish at least these categories:
- COMPLETED_PERIOD_ACTUAL
- COMPLETED_PERIOD_PRELIMINARY
- COMPLETED_PERIOD_CONSENSUS_REFERENCE
- CURRENT_YEAR_FORECAST
- FUTURE_YEAR_FORECAST
- COMPANY_GUIDANCE
- AMBIGUOUS_TEMPORAL_RESULT

A2. Use run date awareness
The system must interpret a result relative to the actual run date.
Examples:
- In March 2026, full-year 2024 is completed.
- In March 2026, full-year 2025 is also completed.
- In March 2026, full-year 2026 is not completed.

A3. If a statement refers to a completed year, it must not default to future-oriented phrasing unless the source clearly frames it as forecast/consensus commentary.

==================================================
TRACK B — TENSE ENFORCEMENT RULES
==================================================

B1. Completed-year actuals
If the period is already complete and the figure is presented as actual/settled:
- write as direct fact
- use past/completed framing
- do NOT use “예상”, “전망”, “기록할 것으로”, “달성할 것으로”, etc.

B2. Completed-year preliminary figures
If the result is preliminary:
- preserve that nuance explicitly
- still do not phrase it as open-ended future expectation
- use wording like provisional / preliminary / 잠정 / preliminary result if appropriate

B3. Consensus references on completed years
If discussing what the market had expected for a completed year:
- distinguish clearly between actual result and prior expectation
- do not collapse expectation into the article’s present factual layer

B4. Current/future forecasts
If the year is not complete or the figure is truly forecast/guidance:
- keep forecast framing
- keep explicit conditionality or source attribution where appropriate

==================================================
TRACK C — GENERATION ENFORCEMENT
==================================================

C1. Prompt-level tense enforcement
Strengthen generation prompts so the model is explicitly told:
- completed years must be treated as completed unless clearly marked otherwise
- do not write closed periods as pending outcomes
- actual vs forecast language is a trust-critical distinction

C2. Contrastive examples
Include GOOD vs BAD examples directly in the prompt.

Bad:
- 2024년 SK하이닉스 매출은 66조원을 기록할 것으로 예상된다.
- 2025년 삼성전자 영업이익은 23조원을 달성할 전망이다.

Good:
- SK하이닉스는 2024년 매출 66조원을 기록했다.
- 삼성전자는 2025년 영업이익 23조원을 기록했다.
- 다만 당시 시장 컨센서스는 이를 상회할 것으로 기대했다.  ← expectation kept separate

C3. Post-specific application
For Post1:
- apply temporal discipline when citing sector/company supporting facts

For Post2:
- apply especially strict temporal discipline for stock-level numbers, because these are most likely to influence reader judgment directly

==================================================
TRACK D — DETECTION / GATING
==================================================

D1. Detect completed-year-as-forecast phrasing
Add or strengthen detection for patterns such as:
- completed year + “예상”
- completed year + “전망”
- completed year + “기록할 것으로”
- completed year + “달성할 것으로”
- completed year + similar future-style verbs

D2. Severity
Treat this as publication-risk quality failure, not cosmetic wording.

Suggested severity:
- clear completed-year-as-forecast = FAIL or HOLD-level issue
- ambiguous case = WARN, requiring explicit clarification

D3. Re-check after rewrite or revision
If a temporal tense issue is detected, ensure the final prose actually changed.
Do not count superficial rephrasing as resolution if the year/result relationship remains misleading.

==================================================
TRACK E — TARGETED FIX / REWRITE
==================================================

E1. Target the exact offending lines
When tense enforcement fails:
- identify the exact sentences
- rewrite only those lines if possible
- replace them with temporally correct wording

E2. Preserve fact meaning
Do not invent a stronger factual claim than the source supports.
Only correct temporal framing.

E3. Keep source nuance
If the source really is consensus/guidance/preview language about a completed year, preserve that nuance instead of flattening everything into direct fact.

==================================================
TRACK F — REPORTING / VALIDATION
==================================================

F1. Inspectability
Log or expose:
- which lines were flagged
- what temporal class they were assigned
- what replacement or correction occurred
- whether the issue was resolved before publication

F2. Real-output validation ready
This phase must support later real-output validation directly.

IMPORTANT:
Future validation/reporting for this project must include the **full published article body** inside the Markdown report.

This is mandatory.
Do not submit only a summary.
The detailed MD report must contain:
- the full published body of Post1
- the full published body of Post2
for the current validation run

==================================================
IMPLEMENTATION CONSTRAINTS
==================================================

1. Do not redesign the 3-stage pipeline.
2. Do not add new external data providers.
3. Do not remove prior Phase 11–14I rules; build on top of them.
4. Treat this as a focused trust/quality phase.
5. Prefer additive, low-risk changes.
6. Public function signatures should remain stable unless strongly necessary.
7. Keep diagnostics inspectable.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement the temporal tense enforcement phase.

2. Documentation
Create/update concise internal docs describing:
- why completed-year tense treatment is now a priority
- how temporal result classification works
- how actual / preliminary / consensus / guidance / forecast are separated
- how generation prompts were strengthened
- how detection/gating works
- how targeted tense correction works

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- completed-year actual classification works
- completed-year preliminary classification works
- consensus/guidance separation works
- completed-year-as-forecast detection works
- targeted tense correction works
- final prose is re-checked after correction
- Post2 stock-level tense discipline improves
- prior phase compatibility remains intact
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
  "temporal_result_classification": "PASS|WARN|FAIL",
  "completed_year_actual_enforcement": "PASS|WARN|FAIL",
  "preliminary_vs_actual_distinction": "PASS|WARN|FAIL",
  "consensus_guidance_separation": "PASS|WARN|FAIL",
  "completed_year_as_forecast_detection": "PASS|WARN|FAIL",
  "targeted_tense_correction": "PASS|WARN|FAIL",
  "post_correction_recheck": "PASS|WARN|FAIL",
  "post2_stock_level_tense_discipline": "PASS|WARN|FAIL",
  "phase14i_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION PRINCIPLES
==================================================

When in doubt:
- prefer temporal trustworthiness over elegant phrasing
- prefer explicit distinction over compressed ambiguity
- prefer narrow sentence correction over broad drift
- prefer actual reader trust over cosmetic style gains
- prefer inspectable temporal logic over hidden heuristics

==================================================
OUTPUT STYLE
==================================================

Be practical and implementation-first.
Do not return a vague strategy memo only.
Actually implement the phase.

At the end, provide:
1. changed files
2. what was implemented
3. verification results
4. final gate JSON

---

## Additional operator note

- Completed-year results written as forecasts are publication-risk issues.
- If a tradeoff is required, prioritize factual temporal trust over stylistic smoothness.
- Post2 stock-level numeric prose is especially sensitive and should receive stricter enforcement.
- Future validation reports must include the full published article body in the MD report, not just summaries.

---

## Important

A polished article that misstates the temporal status of company results is still a failure.
This phase succeeds only if completed-year results stop being phrased as pending outcomes.

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
`REPORT_PHASE15_TEMPORAL_TENSE_ENFORCEMENT.md`

The detailed report must include:
- final report
- implementation details
- verification checklist
- risks / follow-up items
- final gate JSON

AND MUST ALSO INCLUDE:

## Published Article Body Archive
### Post1 Full Body
[full published body here]

### Post2 Full Body
[full published body here]

This requirement is mandatory for future validation comparability.

Use this structure in the report:

# REPORT_PHASE15_TEMPORAL_TENSE_ENFORCEMENT

## 1. Changed Files

## 2. Implementation Summary

## 3. Verification Results

## 4. Risks / Follow-up

## 5. Final Gate JSON

## 6. Published Article Body Archive
### Post1 Full Body

### Post2 Full Body

```json
{
  "temporal_result_classification": "PASS|WARN|FAIL",
  "completed_year_actual_enforcement": "PASS|WARN|FAIL",
  "preliminary_vs_actual_distinction": "PASS|WARN|FAIL",
  "consensus_guidance_separation": "PASS|WARN|FAIL",
  "completed_year_as_forecast_detection": "PASS|WARN|FAIL",
  "targeted_tense_correction": "PASS|WARN|FAIL",
  "post_correction_recheck": "PASS|WARN|FAIL",
  "post2_stock_level_tense_discipline": "PASS|WARN|FAIL",
  "phase14i_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE15_TEMPORAL_TENSE_ENFORCEMENT.md 읽고 구현해. 결과는 요약은 채팅, 상세는 MD로 제출해. 발행 본문 전문도 MD에 반드시 포함해.`
