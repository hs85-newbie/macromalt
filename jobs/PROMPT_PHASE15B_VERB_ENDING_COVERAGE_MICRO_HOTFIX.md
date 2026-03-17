# PROMPT_PHASE15B_VERB_ENDING_COVERAGE_MICRO_HOTFIX.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15B — 어미 커버 확장 마이크로 핫픽스** 통합 실행 문서입니다.

목적:
1. Phase 15A에서 놓친 `되며` 계열 혼재 시제를 교정 범위에 포함
2. `기록할 것으로 전망되며` 같은 완료 연도 실적 문장을 발행 전 교정에서 확실히 제거
3. 변경 범위를 최소화해 빠르게 실출력 HOLD 원인을 해소
4. 결과는 요약은 채팅, 상세는 MD 파일로 제출

---

## Claude Code 실행 지시문

You are implementing a very narrow micro-hotfix for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation was GO but real-output was HOLD.
- Phase 15A compound tense correction hotfix is implementation GO but real-output is HOLD.
- The immediate cause of the current HOLD is now extremely specific:
  the compound tense correction logic does not cover `되며`-family endings.

Observed failure example:
- completed-year result sentence survived as:
  "기록할 것으로 전망되며"
- because regex and/or correction coverage handled `됩니다|된다` but not `되며`

Your task:
Implement **Phase 15B — Verb Ending Coverage Micro-Hotfix**.

This is NOT a broad new phase.
This is a minimal corrective hotfix aimed at closing the specific ending-coverage gap.

==================================================
PRIMARY OBJECTIVE
==================================================

Extend tense-correction coverage so mixed future-style residue with connective endings is no longer missed.

This hotfix succeeds only if:
1. `되며`-family endings are covered by correction logic
2. completed-year mixed-tense phrases using those endings are no longer missed
3. the fix stays minimal and low-risk
4. real output has a realistic chance of moving from HOLD to GO on the temporal trust axis

==================================================
ROOT PROBLEM TO SOLVE
==================================================

Current failure mode:
- detection identified a completed-year-as-forecast issue
- but correction did not fire because the surface form ended with `되며`
- current regex/correction coverage is too narrow for real generated Korean finance prose

New design principle:
If the system covers only declarative endings and misses connective/reporting endings, temporal correction is incomplete.

==================================================
TRACK A — ENDING COVERAGE EXPANSION
==================================================

A1. Expand covered endings
Extend the relevant formal compound correction regex and any associated correction logic so it covers at least:
- 됩니다
- 된다
- 되며
- 되고
- 되어
- 됐으며
- 됐다

If there are closely related endings already present in code, ensure coverage is coherent and not fragmented.

A2. Keep the change minimal
Do not redesign the whole correction system.
Do not widen scope beyond what is needed for the current failure.

A3. Ensure coverage applies to compound tense correction patterns
This hotfix is about phrases like:
- 기록할 것으로 전망되며
- 달성할 것으로 예상되며
- 증가할 것으로 추정되며
- similar completed-year result constructions

==================================================
TRACK B — REPLACEMENT / LAMBDA ADJUSTMENT
==================================================

B1. Update replacement handling accordingly
If the correction lambda or replacement logic currently assumes only `됩니다|된다`,
extend it so new ending coverage still produces natural corrected past/completed phrasing.

B2. Preserve completed-year factuality
The corrected result must read as a completed-period factual statement when that is what the source supports.

B3. Avoid false flattening
Do not break genuine future forecast language for periods that are not completed.

==================================================
TRACK C — VALIDATION
==================================================

C1. Add narrow tests
Include targeted tests for the exact family of failures now in scope.

Suggested examples:
- 기록할 것으로 전망되며
- 달성할 것으로 예상되며
- 증가할 것으로 추정되며
- 감소할 것으로 전망되며

C2. Recheck after correction
Ensure the corrected sentence no longer contains mixed future-style residue.

C3. Keep compatibility
Do not regress:
- Phase 15 detection
- Phase 15A compound correction logic
- prior phase interpretation/hedge gains

==================================================
IMPLEMENTATION CONSTRAINTS
==================================================

1. Keep this hotfix extremely narrow.
2. Do not redesign the 3-stage pipeline.
3. Do not add new external data providers.
4. Do not remove prior Phase 11–15A rules; build on top of them.
5. Prefer additive, low-risk changes.
6. Public function signatures should remain stable unless strongly necessary.
7. Keep diagnostics inspectable.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement the verb-ending coverage micro-hotfix.

2. Documentation
Create/update concise internal docs describing:
- what exact ending gap caused the HOLD
- what endings were added
- how correction behavior remains safe
- what was tested

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- `되며` coverage works
- extended ending family coverage works
- replacement logic remains natural
- mixed-tense residue is removed after correction
- Phase 15A compatibility remains intact
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
  "ending_coverage_expansion": "PASS|WARN|FAIL",
  "doemyeo_family_support": "PASS|WARN|FAIL",
  "replacement_logic_update": "PASS|WARN|FAIL",
  "mixed_tense_residue_removal": "PASS|WARN|FAIL",
  "phase15a_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION PRINCIPLES
==================================================

When in doubt:
- prefer a smaller safer hotfix over a broad rewrite
- prefer complete ending-family coverage over partial declarative-only coverage
- prefer direct removal of the current failure mode over speculative improvements
- prefer explicit recheck over assumed resolution

==================================================
OUTPUT STYLE
==================================================

Be practical and implementation-first.
Do not return a vague strategy memo only.
Actually implement the micro-hotfix.

At the end, provide:
1. changed files
2. what was implemented
3. verification results
4. final gate JSON

---

## Additional operator note

- The current failure is highly localized.
- Do not broaden scope unnecessarily.
- The immediate job is to make sure `되며`-family endings no longer slip through the completed-year tense correction layer.
- If a tradeoff is required, prioritize safer coverage expansion over clever refactoring.

---

## Important

If `기록할 것으로 전망되며` can still survive after this hotfix, the hotfix failed.
This task is successful only if the exact uncovered ending family is now handled.

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
`REPORT_PHASE15B_VERB_ENDING_COVERAGE_MICRO_HOTFIX.md`

The detailed report must include:
- final report
- implementation details
- verification checklist
- risks / follow-up items
- final gate JSON

Use this structure in the report:

# REPORT_PHASE15B_VERB_ENDING_COVERAGE_MICRO_HOTFIX

## 1. Changed Files

## 2. Implementation Summary

## 3. Verification Results

## 4. Risks / Follow-up

## 5. Final Gate JSON

```json
{
  "ending_coverage_expansion": "PASS|WARN|FAIL",
  "doemyeo_family_support": "PASS|WARN|FAIL",
  "replacement_logic_update": "PASS|WARN|FAIL",
  "mixed_tense_residue_removal": "PASS|WARN|FAIL",
  "phase15a_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE15B_VERB_ENDING_COVERAGE_MICRO_HOTFIX.md 읽고 구현해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
