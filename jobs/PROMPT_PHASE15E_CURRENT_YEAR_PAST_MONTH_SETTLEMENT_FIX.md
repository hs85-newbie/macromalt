# PROMPT_PHASE15E_CURRENT_YEAR_PAST_MONTH_SETTLEMENT_FIX.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15E — 현재 연도 과거 월 완료구간 처리 핫픽스** 통합 실행 문서입니다.

목적:
1. 현재 연도(예: 2026년) 안에서도 이미 종료된 과거 월(예: 1월, 2월)을 **완료 구간**으로 처리
2. 해당 구간의 집계 데이터에 붙은 `[전망]` 태그와 예측 동사를 동시에 교정
3. `기록할 것으로 추정됩니다`, `늘어날 것으로 전망됩니다` 같은 문장을 확정형으로 전환
4. 결과는 요약은 채팅, 상세는 MD 파일로 제출

---

## Claude Code 실행 지시문

You are implementing a focused hotfix for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation was GO but real-output was HOLD.
- Phase 15A/15B improved compound tense correction coverage.
- Phase 15C improved Step3 temporal grounding and removed internal label leakage.
- Phase 15D stripped misapplied `[전망]` tags from completed-year actuals.
- Phase 15D real-output is still HOLD because current-year past-month data is still being treated like forecast content.

Observed failure example:
- in March 2026 output, a line about **2026년 2월 집계 수출 데이터** can still appear as:
  - `[전망] ... 늘어날 것으로 전망됩니다`
  - `[전망] ... 기록할 것으로 추정됩니다`
- this is wrong because the month is already completed and the figure is already published/settled

Your task:
Implement **Phase 15E — Current-Year Past-Month Settlement Fix**.

This is NOT a broad new phase.
This is a focused corrective hotfix aimed at treating current-year past-month data as settled when appropriate.

==================================================
PRIMARY OBJECTIVE
==================================================

Ensure that already-completed months within the current year are handled as settled factual periods, not forecast periods.

This hotfix succeeds only if:
1. current-year past-month figures can be recognized as completed/settled
2. `[전망]` misuse on those lines is removed
3. future-style verbs on those lines are corrected into completed factual phrasing
4. real output has a realistic chance of moving from HOLD to GO on the temporal trust axis

==================================================
ROOT PROBLEM TO SOLVE
==================================================

Current failure mode:
- the system mostly knows how to treat completed prior years
- but it still fails on current-year past-month data
- therefore published monthly figures from January/February 2026 can still be framed as if they are pending expectations in March 2026

New design principle:
A month that has already closed and has been reported should be treated as a completed factual period, even if it belongs to the current year.

==================================================
TRACK A — CURRENT-YEAR PAST-MONTH CLASSIFICATION
==================================================

A1. Add current-year past-month settlement logic
The system must recognize that, relative to the run date:
- prior months in the same year can already be completed
- especially if the source sentence is clearly reporting a published/settled monthly figure

Examples:
- in March 2026, January 2026 and February 2026 are already completed months
- those periods should not default to forecast framing when they are described as reported/export/settled data

A2. Require both time and settlement cues when appropriate
Prefer safe handling:
- current year match
- month earlier than run month
- published/settled signal in the sentence or source framing when available

A3. Avoid overreach into still-open periods
Do not treat:
- current month
- future months
- vague undated same-year references
as automatically settled without stronger support

==================================================
TRACK B — COMBINED TAG + VERB CORRECTION
==================================================

B1. Handle label and verb together
For current-year past-month settled lines, the system should be able to:
- remove misapplied `[전망]`
AND
- convert future-style verbs into completed factual phrasing

This hotfix must not rely on tag stripping alone.

B2. Cover common monthly-stat phrasing
Expand support for patterns such as:
- 늘어날 것으로 전망됩니다
- 증가할 것으로 전망됩니다
- 기록할 것으로 추정됩니다
- 회복될 것으로 보입니다
when applied to already completed reported monthly data

B3. Keep phrasing natural
The corrected output should read like a reported/settled fact, not an awkward literal transformation.

==================================================
TRACK C — DETECTION / RECHECK
==================================================

C1. Detect current-year past-month forecast misuse
Add or strengthen logic to detect:
- current-year past-month reference
- forecast-style language
- misapplied `[전망]`
on the same settled/reporting line

C2. Recheck after correction
A correction should count as success only if:
- `[전망]` misuse is removed
- future-style verb residue is removed
- the sentence reads as a settled/reporting statement

C3. Treat partial correction as unresolved
If one part is fixed but the line still reads like a forecast, do NOT treat it as success.

==================================================
TRACK D — QUALITY GUARDRAILS
==================================================

D1. Do not flatten real future monthly expectations
If a sentence is genuinely about future months or future export outlook,
preserve forecast framing.

D2. Preserve source nuance
If a monthly figure is still provisional, preserve that nuance explicitly.

D3. Keep prior phase gains
Do not regress:
- Phase 14I interpretation hedge improvements
- Phase 15C internal label safety
- Phase 15D completed-year `[전망]` stripping

==================================================
IMPLEMENTATION CONSTRAINTS
==================================================

1. Keep this hotfix focused.
2. Do not redesign the 3-stage pipeline.
3. Do not add new external data providers.
4. Do not remove prior Phase 11–15D rules; build on top of them.
5. Prefer additive, low-risk changes.
6. Public function signatures should remain stable unless strongly necessary.
7. Keep diagnostics inspectable.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement the current-year past-month settlement fix.

2. Documentation
Create/update concise internal docs describing:
- why current-year past-month data was still failing
- how settled-month classification works
- how tag + verb correction now works together
- what safeguards prevent overreach into genuine future months
- what was tested

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- current-year past-month classification works
- `[전망]` misuse on settled monthly data is removed
- future-style verb residue on settled monthly data is removed
- combined correction is natural and readable
- genuine future monthly outlook is preserved
- Phase 15D compatibility remains intact
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
  "current_year_past_month_classification": "PASS|WARN|FAIL",
  "settled_month_jeonmang_removal": "PASS|WARN|FAIL",
  "settled_month_future_verb_correction": "PASS|WARN|FAIL",
  "combined_monthly_fix_readability": "PASS|WARN|FAIL",
  "future_month_forecast_preservation": "PASS|WARN|FAIL",
  "phase15d_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION PRINCIPLES
==================================================

When in doubt:
- prefer treating clearly reported past-month data as settled
- prefer correcting both label and verb together
- prefer safe month-aware logic over blunt same-year assumptions
- prefer narrow trustworthy corrections over broad overreach

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

- The remaining temporal trust issue is now mostly month-level, not year-level.
- A line about February 2026 that is already reported in March 2026 should not read like a forecast.
- If a tradeoff is required, prioritize temporal trust for clearly settled reported months.
- Do not accidentally flatten true future monthly outlook sentences.

---

## Important

If March 2026 output still treats February 2026 reported data as `[전망]`, this hotfix failed.
This task succeeds only if settled current-year past-month data stops sounding like future expectation.

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
`REPORT_PHASE15E_CURRENT_YEAR_PAST_MONTH_SETTLEMENT_FIX.md`

The detailed report must include:
- final report
- implementation details
- verification checklist
- risks / follow-up items
- final gate JSON

Use this structure in the report:

# REPORT_PHASE15E_CURRENT_YEAR_PAST_MONTH_SETTLEMENT_FIX

## 1. Changed Files

## 2. Implementation Summary

## 3. Verification Results

## 4. Risks / Follow-up

## 5. Final Gate JSON

```json
{
  "current_year_past_month_classification": "PASS|WARN|FAIL",
  "settled_month_jeonmang_removal": "PASS|WARN|FAIL",
  "settled_month_future_verb_correction": "PASS|WARN|FAIL",
  "combined_monthly_fix_readability": "PASS|WARN|FAIL",
  "future_month_forecast_preservation": "PASS|WARN|FAIL",
  "phase15d_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE15E_CURRENT_YEAR_PAST_MONTH_SETTLEMENT_FIX.md 읽고 구현해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
