# PROMPT_PHASE16_TEMPORAL_STATE_NORMALIZATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 16 — Temporal State Normalization** 통합 실행 문서입니다.

목적:
1. 시간/시제 문제를 개별 표현 패턴이 아니라 **상태(state)** 기준으로 제어
2. 완료 연도, 현재 연도 과거 월, 잠정치, 컨센서스, 가이던스, 전망을 하나의 정규화 레이어에서 SSOT로 고정
3. GPT 생성, Gemini Step3 검수, 후처리 교정이 각자 시간을 재해석하지 못하게 구조를 정리
4. 이후 3~5회 실출력 검증 기반 미세수정이 가능한 안정된 기반을 마련
5. 결과는 요약은 채팅, 상세는 MD 파일로 제출

---

## Claude Code 실행 지시문

You are implementing a structural quality phase for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 and its sub-hotfixes (15A–15E) have repeatedly addressed temporal trust issues at the pattern level.
- Those hotfixes improved many cases, but the same class of temporal symptoms keeps reappearing in new surface forms.
- The project now needs a higher-level temporal SSOT layer rather than endless expression-specific patching.

Your task:
Implement **Phase 16 — Temporal State Normalization**.

This is a structural phase, not a tiny hotfix.
However, it should still be implemented safely and incrementally enough that follow-up micro-adjustments can happen quickly over the next 3–5 validation cycles.

==================================================
PRIMARY OBJECTIVE
==================================================

Create a single normalized temporal-status layer that becomes the source of truth for temporal interpretation across the pipeline.

Phase 16 succeeds only if:
1. article generation and verification stop re-inferring time state independently
2. completed periods, provisional figures, consensus, guidance, and forecasts are explicitly distinguished
3. tags like `[전망]` are derived from normalized temporal state rather than loose text heuristics
4. repeated temporal failures become easier to diagnose and fix in small follow-up iterations

==================================================
WHY THIS PHASE EXISTS
==================================================

The current temporal pipeline is too pattern-reactive.

Current symptom pattern:
- one form of forecast-like phrasing is fixed
- a slightly different surface form appears
- Step3 reinterprets time differently from GPT
- post-processing fixes tags in one case but not another
- the same logical failure reappears in new language forms

This means the real problem is not only wording.
The deeper problem is that temporal state is not yet treated as a stable shared object.

New principle:
Temporal status must be normalized once, then reused consistently by generation, verification, and cleanup.

==================================================
PHASE 16 DESIGN PRINCIPLE
==================================================

Do not let GPT, Gemini Step3, and post-processing each decide separately whether something is actual, preliminary, consensus, guidance, or forecast.

Instead:
- normalize temporal state first
- inject that normalized state into downstream generation/verification
- make downstream layers respect it
- use post-processing mainly as a safety net, not as the primary temporal reasoner

==================================================
TRACK A — TEMPORAL STATE MODEL
==================================================

Implement a normalized temporal-state model for fact/result items.

At minimum, distinguish these statuses:

- ACTUAL_SETTLED
- ACTUAL_PRELIMINARY
- CONSENSUS_REFERENCE
- COMPANY_GUIDANCE
- FORECAST
- AMBIGUOUS_TEMPORAL_STATE

You may expand slightly if needed, but avoid unnecessary complexity.

Each relevant item should be capable of carrying at least:
- period / time reference
- run date reference
- status
- whether forecast-like labeling is allowed
- whether completed factual phrasing is required

==================================================
TRACK B — NORMALIZATION RULES
==================================================

Create normalization logic that can classify at least these cases correctly:

B1. Completed prior years
Examples:
- in 2026 output, FY2024 and FY2025 are completed periods

B2. Current-year past months
Examples:
- in March 2026 output, January 2026 and February 2026 are completed months if the line is clearly reported/published data

B3. Current/future periods
Examples:
- current month still open
- future month / future quarter / future year forecast

B4. Preliminary / provisional cases
Examples:
- 잠정
- provisional
- preliminary result
These should remain distinct from fully settled actuals.

B5. Consensus / market expectation references
Examples:
- the market had expected
- consensus estimate
- analysts projected
These should not be collapsed into the article's direct factual layer.

B6. Company guidance
Examples:
- company guidance for upcoming period
- management target
These should not be rewritten as achieved actuals.

==================================================
TRACK C — PIPELINE INTEGRATION
==================================================

Integrate the normalized temporal state into the pipeline so it becomes reusable SSOT.

C1. Generation integration
Before GPT writing, provide normalized temporal-state information in a form the writer can use directly.

C2. Step3 integration
Gemini Step3 must not freely reinterpret normalized states.
It may inspect, but should not overturn clearly normalized temporal status without strong reason.

C3. Post-processing integration
Post-processing should mainly act as a consistency enforcer against the normalized temporal state, not as a fully independent temporal reasoner.

C4. Tag derivation
Where feasible, tags like `[전망]` should be derived from normalized state rather than guessed from local phrasing.

==================================================
TRACK D — STATE-TO-LANGUAGE RULES
==================================================

Define language rules by state, not by raw phrase pattern alone.

Examples:

For ACTUAL_SETTLED:
- no `[전망]`
- no future-style verbs
- completed factual phrasing required

For ACTUAL_PRELIMINARY:
- allow provisional framing
- still do not present as open future forecast

For CONSENSUS_REFERENCE:
- clearly separate expectation from achieved result

For COMPANY_GUIDANCE / FORECAST:
- forecast framing allowed
- conditional/forward-looking language allowed where appropriate

==================================================
TRACK E — INSPECTABILITY / DEBUGGABILITY
==================================================

Phase 16 must make debugging easier, not harder.

Expose or log enough structure that later micro-adjustments can diagnose failures quickly.

At minimum, make it possible to inspect:
- which lines/items received which temporal status
- where a state was used by generation
- whether Step3 respected the normalized state
- where post-processing had to intervene because prose violated the state

This is important because the project intends to run 3–5 quick validation/fix loops after this phase.

==================================================
TRACK F — SAFETY / SCOPE DISCIPLINE
==================================================

F1. Do not over-design
This is a structural phase, but it should remain practical.
Do not create a giant ontology or abstract framework that slows future iteration.

F2. Preserve prior gains
Do not regress:
- hedge clamp gains
- interpretation quality gains
- internal pipeline label safety
- natural Post1/Post2 continuity

F3. Keep follow-up micro-fixes easy
Implementation should support fast later adjustments rather than locking the project into a brittle heavy structure.

==================================================
IMPLEMENTATION CONSTRAINTS
==================================================

1. Do not redesign the whole product architecture beyond what is needed for temporal SSOT.
2. Do not add new external data providers.
3. Do not remove prior Phase 11–15E rules; absorb or organize them under the normalized-state framework where practical.
4. Prefer additive, inspectable, low-risk structure over hidden magic.
5. Public function signatures should remain stable unless strongly necessary.
6. Keep the implementation compatible with repeated real-output validation cycles.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement Phase 16 Temporal State Normalization.

2. Documentation
Create/update concise internal docs describing:
- why pattern-level temporal patching was no longer enough
- what temporal states now exist
- how normalization works
- how downstream layers use normalized temporal state
- how future micro-fixes should be applied after Phase 16
- what remains intentionally out of scope

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- temporal state model exists and is inspectable
- completed prior years classify correctly
- current-year past months classify correctly
- preliminary vs actual is distinguishable
- consensus/guidance/forecast separation works
- generation can consume normalized state
- Step3 respects normalized state
- post-processing enforces normalized state
- `[전망]` derivation/control is improved via state
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
  "temporal_state_model": "PASS|WARN|FAIL",
  "completed_year_classification": "PASS|WARN|FAIL",
  "current_year_past_month_classification": "PASS|WARN|FAIL",
  "preliminary_actual_distinction": "PASS|WARN|FAIL",
  "consensus_guidance_forecast_separation": "PASS|WARN|FAIL",
  "generation_state_integration": "PASS|WARN|FAIL",
  "step3_state_respect": "PASS|WARN|FAIL",
  "postprocessing_state_enforcement": "PASS|WARN|FAIL",
  "jeonmang_state_control": "PASS|WARN|FAIL",
  "phase15e_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION PRINCIPLES
==================================================

When in doubt:
- prefer stable temporal-state reasoning over expression-by-expression patching
- prefer inspectable structure over clever hidden heuristics
- prefer a practical SSOT over a theoretically perfect but unusable framework
- prefer making future micro-fixes easier over solving every edge case immediately

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

- The purpose of Phase 16 is not to magically solve every temporal edge case in one shot.
- The purpose is to move temporal reasoning to a higher and more stable layer so the next 3–5 validation/fix iterations converge faster.
- Do not optimize for elegance alone; optimize for repeated real-output correction cycles.
- This phase should reduce repeated symptom churn, not create a fragile abstraction burden.

---

## Important

If GPT, Gemini Step3, and post-processing can still freely disagree on temporal status after this phase, the phase failed.
Phase 16 succeeds only if temporal status becomes meaningfully more centralized and reusable.

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
`REPORT_PHASE16_TEMPORAL_STATE_NORMALIZATION.md`

The detailed report must include:
- final report
- implementation details
- verification checklist
- risks / follow-up items
- final gate JSON

Use this structure in the report:

# REPORT_PHASE16_TEMPORAL_STATE_NORMALIZATION

## 1. Changed Files

## 2. Implementation Summary

## 3. Verification Results

## 4. Risks / Follow-up

## 5. Final Gate JSON

```json
{
  "temporal_state_model": "PASS|WARN|FAIL",
  "completed_year_classification": "PASS|WARN|FAIL",
  "current_year_past_month_classification": "PASS|WARN|FAIL",
  "preliminary_actual_distinction": "PASS|WARN|FAIL",
  "consensus_guidance_forecast_separation": "PASS|WARN|FAIL",
  "generation_state_integration": "PASS|WARN|FAIL",
  "step3_state_respect": "PASS|WARN|FAIL",
  "postprocessing_state_enforcement": "PASS|WARN|FAIL",
  "jeonmang_state_control": "PASS|WARN|FAIL",
  "phase15e_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE16_TEMPORAL_STATE_NORMALIZATION.md 읽고 구현해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
