# PROMPT_PHASE15C_STEP3_TEMPORAL_CONTEXT_AND_POST2_LABEL_FIX.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15C — Step3 완료 연도 컨텍스트 주입 + Post2 내부 레이블 제거** 통합 실행 문서입니다.

목적:
1. Gemini Step3가 2024/2025 완료 연도를 현재 진행 연도로 오인하지 못하게 차단
2. 완료 연도 확정 실적 문장에 `[전망]` 태그가 붙는 문제를 방지
3. Post2 독자-facing 문장에서 `Post1`, `Post2` 같은 내부 파이프라인 용어를 제거
4. 연결 문장을 자연스러운 독자용 문장으로 교체
5. 결과는 요약은 채팅, 상세는 MD 파일로 제출

---

## Claude Code 실행 지시문

You are implementing a focused hotfix for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation was GO but real-output was HOLD.
- Phase 15A and 15B improved correction coverage, but real-output is still HOLD.
- The current HOLD is now caused by two clearly localized issues:
  1. Gemini Step3 still misclassifies completed-year results as forecast-like and injects `[전망]` framing
  2. Post2 still sometimes exposes internal pipeline terminology such as `Post1의 결론에 따르면`

Your task:
Implement **Phase 15C — Step3 Temporal Context Injection + Post2 Internal Label Fix**.

This is NOT a broad new phase.
This is a focused corrective hotfix aimed at removing two specific publication-facing failures.

==================================================
PRIMARY OBJECTIVE
==================================================

Eliminate:
1. `[전망]` misuse on completed-year actual results caused by Step3 temporal misclassification
2. internal pipeline label leakage in Post2 reader-facing prose

This hotfix succeeds only if:
- Step3 becomes less likely to misread 2024/2025 as ongoing/future years in 2026 output
- completed-year actuals are no longer wrapped in forecast-style labels by Step3
- Post2 continuity language becomes editorially natural for a subscriber
- no reader-facing `Post1` / `Post2` wording survives in final published prose

==================================================
ROOT PROBLEMS TO SOLVE
==================================================

Problem 1 — Step3 temporal misclassification:
- GPT can generate a correct completed-year factual sentence
- but Gemini Step3 can still reinterpret the year incorrectly and force `[전망]`
- this upstream correction logic can therefore re-break a sentence that was already good

Problem 2 — internal label leakage:
- Post2 can still emit wording like:
  - Post1의 결론에 따르면
  - Post1에서 도출된 결론은
  - Post2 기준으로
- this is workflow language, not publication language
- readers should see editorial transitions, not pipeline metadata

==================================================
TRACK A — GEMINI STEP3 TEMPORAL CONTEXT INJECTION
==================================================

A1. Inject explicit temporal context into Step3
Strengthen the Step3 Gemini prompt so it is explicitly grounded in the publication date context.

The prompt should clearly state the equivalent of:
- publication/run date is in 2026
- 2024 and 2025 full-year results are completed years
- do not classify completed-year annual results as open forecasts
- do not add `[전망]` tags to settled completed-year actuals unless the source explicitly requires forecast framing

A2. Distinguish allowed vs forbidden Step3 behavior
Forbidden Step3 behavior:
- treating 2024 or 2025 annual actuals as if those years are still ongoing
- forcing `[전망]` on completed-year settled results
- rewriting completed-year fact sentences into future-style outcomes

Allowed Step3 behavior:
- preserve preliminary / provisional nuance if clearly supported
- preserve consensus/guidance language if truly relevant and clearly separated
- add caution only when temporal ambiguity is real, not when the year is obviously completed

A3. Make Step3 date awareness inspectable
If feasible, expose/log that Step3 is operating with the intended year context so later debugging is easier.

==================================================
TRACK B — STEP3 LABEL MISUSE REDUCTION
==================================================

B1. Explicitly restrict `[전망]` usage
Refine Step3 instructions so `[전망]` is not used for:
- completed-year actual results
- already reported annual financial outcomes
- settled historical numbers

B2. Encourage appropriate alternatives
If a completed-year result needs interpretation, use:
- factual/analytical treatment
- result context
- interpretation
but not `[전망]` unless the statement is genuinely future-oriented

B3. Keep nuance safe
Do not flatten genuine future scenarios into historical facts.
This hotfix is about blocking misapplied forecast labeling, not deleting all forward-looking structure.

==================================================
TRACK C — POST2 INTERNAL LABEL FIX
==================================================

C1. Ban internal pipeline terminology in reader-facing prose
Post2 generation must not emit:
- Post1
- Post2
- Post1의 결론에 따르면
- Post1에서 도출된 결론은
- Post2 기준으로
- or similar internal workflow wording

C2. Provide reader-facing alternatives
Encourage or require natural alternatives such as:
- [심층분석]에서 도출된 결론은 ...
- 앞서 살펴본 흐름을 종목 관점에서 보면 ...
- 이 흐름을 개별 종목에 적용하면 ...
- 앞서 확인한 시장 구조를 종목으로 옮기면 ...
- or similarly natural editorial transitions

Important:
Do not mechanically force a single phrase.
The goal is natural subscriber-facing prose, not repeated template wording.

C3. Preserve continuity without leakage
Post2 should still continue from Post1’s analytical frame,
but it should do so in a way that makes sense to a reader who has never heard the internal term “Post1”.

==================================================
TRACK D — DETECTION / SAFETY
==================================================

D1. Detect internal label leakage
Add or strengthen checks for reader-facing pipeline terms in final output.

D2. Detect completed-year forecast-label misuse
If `[전망]` appears near completed-year settled results, treat it as a significant quality failure.

D3. Recheck after correction/revision
If a fix is applied, verify that:
- completed-year sentences no longer carry misleading forecast treatment
- pipeline label leakage is gone from published prose

==================================================
TRACK E — IMPLEMENTATION CONSTRAINTS
==================================================

1. Keep this hotfix focused.
2. Do not redesign the 3-stage pipeline.
3. Do not add new external data providers.
4. Do not remove prior Phase 11–15B rules; build on top of them.
5. Prefer additive, low-risk changes.
6. Public function signatures should remain stable unless strongly necessary.
7. Keep diagnostics inspectable.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement the Step3 temporal context injection and Post2 internal label fix.

2. Documentation
Create/update concise internal docs describing:
- why Step3 temporal context needed strengthening
- how `[전망]` misuse is reduced
- how internal pipeline label leakage is blocked
- what reader-facing transition alternatives are now preferred
- what was tested

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- Step3 temporal context injection works
- completed-year forecast-label misuse is reduced
- internal pipeline label leakage detection works
- Post2 reader-facing transition language improves
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
  "step3_temporal_context_injection": "PASS|WARN|FAIL",
  "completed_year_forecast_label_reduction": "PASS|WARN|FAIL",
  "step3_label_misuse_control": "PASS|WARN|FAIL",
  "internal_pipeline_label_block": "PASS|WARN|FAIL",
  "post2_reader_facing_transition_quality": "PASS|WARN|FAIL",
  "phase15b_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION PRINCIPLES
==================================================

When in doubt:
- prefer reader trust over automated overcorrection
- prefer natural editorial continuity over internal workflow wording
- prefer explicit year grounding over vague temporal inference
- prefer narrower safer fixes over broad rewrites

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

- The current failures are publication-facing and easy for readers to notice.
- A subscriber should never see internal wording like `Post1의 결론에 따르면`.
- A completed-year actual should never be pushed under `[전망]` by a model that forgot what year it is.
- If a tradeoff is required, prioritize reader-facing credibility over clever abstraction.

---

## Important

If Step3 still pushes completed-year actuals into `[전망]`, this hotfix failed.
If `Post1` appears in reader-facing prose, this hotfix failed.

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
`REPORT_PHASE15C_STEP3_TEMPORAL_CONTEXT_AND_POST2_LABEL_FIX.md`

The detailed report must include:
- final report
- implementation details
- verification checklist
- risks / follow-up items
- final gate JSON

Use this structure in the report:

# REPORT_PHASE15C_STEP3_TEMPORAL_CONTEXT_AND_POST2_LABEL_FIX

## 1. Changed Files

## 2. Implementation Summary

## 3. Verification Results

## 4. Risks / Follow-up

## 5. Final Gate JSON

```json
{
  "step3_temporal_context_injection": "PASS|WARN|FAIL",
  "completed_year_forecast_label_reduction": "PASS|WARN|FAIL",
  "step3_label_misuse_control": "PASS|WARN|FAIL",
  "internal_pipeline_label_block": "PASS|WARN|FAIL",
  "post2_reader_facing_transition_quality": "PASS|WARN|FAIL",
  "phase15b_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE15C_STEP3_TEMPORAL_CONTEXT_AND_POST2_LABEL_FIX.md 읽고 구현해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
