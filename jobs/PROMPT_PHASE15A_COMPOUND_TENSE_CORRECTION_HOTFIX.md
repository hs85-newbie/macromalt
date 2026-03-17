# PROMPT_PHASE15A_COMPOUND_TENSE_CORRECTION_HOTFIX.md

이 문서는 Claude Code에 직접 전달하는 **Phase 15A — 복합 패턴 시제 교정 핫픽스** 통합 실행 문서입니다.

목적:
1. 완료 연도 실적 문장에서 남아 있는 **어간+어미 혼재형 미래 시제**를 제거
2. `_P15_TENSE_CORRECTION_MAP`의 단순 어미 교체 한계를 보완
3. 탐지는 성공했지만 교정이 불완전했던 Phase 15 real-output HOLD 원인을 직접 해결
4. 결과는 요약은 채팅, 상세는 MD 파일로 제출

---

## Claude Code 실행 지시문

You are implementing a focused hotfix for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 implementation is GO but real-output is HOLD.
- The root cause of the current HOLD is now clearly identified:
  completed-year result sentences can still retain future-oriented stems even after end-phrase correction.

Observed failure example:
- "기록할 것으로 추정됩니다" was partially corrected to
  "기록할 것으로 집계됐습니다"
- this still contains a future-oriented stem ("기록할") inside a completed-year factual sentence
- detection succeeded, but correction remained incomplete

Your task:
Implement **Phase 15A — Compound Tense Correction Hotfix**.

This is NOT a broad new phase.
This is a focused corrective hotfix to make completed-year tense correction fully resolve compound future-style patterns.

==================================================
PRIMARY OBJECTIVE
==================================================

Ensure that completed-year result sentences no longer retain mixed future-style phrasing after correction.

This hotfix succeeds only if:
1. completed-year-as-forecast phrasing is corrected more completely
2. both stem and ending can be fixed when needed
3. post-correction residue is materially reduced
4. real output has a realistic chance of moving from HOLD to GO on the temporal trust axis

==================================================
ROOT PROBLEM TO SOLVE
==================================================

Current failure mode:
- detection catches completed-year-as-forecast phrasing
- correction changes only the sentence ending
- but future-oriented stems such as:
  - 기록할
  - 달성할
  - 올릴
  - 확대할
  - 감소할
  may still survive
- therefore the sentence remains temporally misleading even after “correction”

New design principle:
For completed-year factual correction, fix the whole future-style phrase, not just the tail ending.

==================================================
TRACK A — COMPOUND PATTERN PRIORITY
==================================================

A1. Add compound correction entries before simple ending replacements
The correction system should prioritize longer, more specific compound patterns above shorter generic replacements.

Examples:
- "기록할 것으로 추정됩니다" -> "기록한 것으로 집계됐습니다"
- "달성할 것으로 추정됩니다" -> "달성한 것으로 집계됐습니다"
- "증가할 것으로 예상됩니다" -> "증가한 것으로 집계됐습니다"
- "감소할 것으로 예상됩니다" -> "감소한 것으로 집계됐습니다"

The exact wording may vary if a better completed-period factual phrasing is more appropriate,
but the correction must fully remove future-oriented residue.

A2. Longest-match-first strategy
When multiple correction candidates overlap:
- prefer the longest and most specific match
- do not let a short suffix replacement fire before a better compound replacement

A3. Preserve nuance where appropriate
If the source clearly indicates:
- preliminary result
- consensus reference
- guidance framing
then preserve that nuance rather than over-flattening everything into one factual template

==================================================
TRACK B — TARGETED CORRECTION LOGIC
==================================================

B1. Correct the offending line itself
Do not rely on broad paraphrase.
Correct the exact offending sentence or phrase.

B2. Remove mixed-tense residue
A sentence should not be considered resolved if it still contains:
- completed year reference
AND
- future stem residue
AND/OR
- future-style construction

B3. Re-check after correction
After correction, run detection again and verify:
- the original violation is actually gone
- no mixed-tense residue remains in the corrected line

==================================================
TRACK C — CORRECTION MAP IMPROVEMENT
==================================================

C1. Expand the map with compound patterns
Add high-priority compound entries for the most common financial/result constructions.

Suggested targets include patterns around:
- 기록할 것으로
- 달성할 것으로
- 증가할 것으로
- 감소할 것으로
- 예상됩니다 / 전망됩니다 / 추정됩니다
- similar completed-year result phrasing

C2. Keep ordering explicit
Make it obvious in code or logic that compound patterns are applied before generic tail substitutions.

C3. Avoid regressions
Do not make the correction map so aggressive that:
- genuine future forecasts get flattened into factual past tense
- guidance language loses its source nuance
- consensus commentary is rewritten as achieved fact

==================================================
TRACK D — VALIDATION / RESOLUTION
==================================================

D1. Resolution must be stricter
A correction should count as successful only if:
- the future-style residue is gone
- the completed-year factuality is readable and trustworthy
- re-detection no longer flags the same issue

D2. Log exact before/after
Expose or log:
- offending original line
- applied correction
- recheck result
- unresolved residue if any remains

D3. Treat partial correction as unresolved
If the sentence still contains mixed-tense residue after correction,
do NOT treat it as success.

==================================================
TRACK E — QUALITY GUARDRAILS
==================================================

E1. Do not hallucinate facts
Do not change the numerical claim itself unless supported.
This hotfix is about temporal phrasing, not numeric rewriting.

E2. Preserve completed-year meaning
The corrected sentence should clearly read as a settled completed-period result when that is what the source supports.

E3. Preserve source nuance
Do not erase preliminary / consensus / guidance distinctions if they are genuinely present.

==================================================
IMPLEMENTATION CONSTRAINTS
==================================================

1. Do not redesign the 3-stage pipeline.
2. Do not add new external data providers.
3. Do not remove prior Phase 11–15 rules; build on top of them.
4. Treat this as a focused trust/quality hotfix.
5. Prefer additive, low-risk changes.
6. Public function signatures should remain stable unless strongly necessary.
7. Keep diagnostics inspectable.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement the compound tense correction hotfix.

2. Documentation
Create/update concise internal docs describing:
- why Phase 15 partial correction was insufficient
- how compound correction patterns are prioritized
- how longest-match-first behavior works
- how recheck confirms full resolution
- how false flattening is avoided

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- compound pattern correction works
- longest-match-first ordering works
- simple suffix replacement no longer preempts better compound fixes
- mixed-tense residue is detected as unresolved
- post-correction recheck works
- guidance/consensus nuance is preserved
- Phase 15 compatibility remains intact
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
  "compound_pattern_priority": "PASS|WARN|FAIL",
  "longest_match_first_ordering": "PASS|WARN|FAIL",
  "compound_tense_correction": "PASS|WARN|FAIL",
  "mixed_tense_residue_detection": "PASS|WARN|FAIL",
  "post_correction_recheck": "PASS|WARN|FAIL",
  "guidance_consensus_nuance_preservation": "PASS|WARN|FAIL",
  "phase15_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}

==================================================
DECISION PRINCIPLES
==================================================

When in doubt:
- prefer full correction of the actual offending phrase over cosmetic suffix edits
- prefer longer specific matches over shorter generic replacements
- prefer temporal trustworthiness over elegant but misleading phrasing
- prefer explicit recheck over assumed success
- prefer narrow safe correction over broad uncontrolled rewriting

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

- Phase 15 already proved that detection works.
- The remaining problem is incomplete correction, not missing diagnosis.
- If a tradeoff is required, prioritize full removal of future-style residue in completed-year sentences.
- A partial fix that still leaves "기록할" inside a completed-year factual sentence is a failure.

---

## Important

A correction that changes only the tail ending but leaves the sentence temporally misleading is not a real correction.
This hotfix succeeds only if completed-year result lines stop sounding like pending outcomes.

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
`REPORT_PHASE15A_COMPOUND_TENSE_CORRECTION_HOTFIX.md`

The detailed report must include:
- final report
- implementation details
- verification checklist
- risks / follow-up items
- final gate JSON

Use this structure in the report:

# REPORT_PHASE15A_COMPOUND_TENSE_CORRECTION_HOTFIX

## 1. Changed Files

## 2. Implementation Summary

## 3. Verification Results

## 4. Risks / Follow-up

## 5. Final Gate JSON

```json
{
  "compound_pattern_priority": "PASS|WARN|FAIL",
  "longest_match_first_ordering": "PASS|WARN|FAIL",
  "compound_tense_correction": "PASS|WARN|FAIL",
  "mixed_tense_residue_detection": "PASS|WARN|FAIL",
  "post_correction_recheck": "PASS|WARN|FAIL",
  "guidance_consensus_nuance_preservation": "PASS|WARN|FAIL",
  "phase15_compatibility": "PASS|WARN|FAIL",
  "public_signature_stability": "PASS|WARN|FAIL",
  "import_build": "PASS|WARN|FAIL",
  "final_status": "GO|HOLD"
}
```

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_PHASE15A_COMPOUND_TENSE_CORRECTION_HOTFIX.md 읽고 구현해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
