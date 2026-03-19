# PROMPT_PHASE16C_REAL_OUTPUT_VALIDATION.md

이 문서는 Claude Code에 직접 전달하는 **Phase 16C 실출력 검증용 통합 실행 문서**입니다.

목적:
1. 신규 런 실행
2. 신규 발행 URL 확보
3. 신규 URL 본문 기준 실출력 검증
4. **Phase 16B에서 추가한 품질 보호 레이어가 실제 발행 품질에 반영되는지 판정**
5. Gemini Step3 실패 시에도 품질 급락이 완화되는지 판정
6. Post1/Post2 도입부 및 전개부의 continuity 중복이 실제로 줄었는지 판정
7. generic wording 감소, analytical spine 유지/개선, premium tone 회복 여부 판정
8. `p16b_guard` 진단값(`step3_status`, `intro_overlap`, `emergency_polish`)이 실제 출력과 부합하는지 판정
9. **Phase 16/16A의 Temporal SSOT 성과가 비회귀인지 판정**
10. 결과는 요약은 채팅, 상세는 MD 파일로 제출
11. **발행 본문 전문을 MD 보고서에 반드시 포함**

---

## Claude Code 실행 지시문

You are running the real-output validation for the macromalt project after Phase 16B Output Quality Hardening implementation.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 and its sub-hotfixes repeatedly addressed temporal trust failures.
- Phase 16 replaced patch-style temporal handling with a runtime Temporal SSOT.
- Phase 16A real-output validation confirmed that current-year past-month settled data is now consistently written as settled fact, with `[전망]` misuse removed and temporal diagnostics aligned with prose.
- Phase 16B implementation added an output-quality hardening layer:
  - Step3 failure status visibility
  - emergency polish diagnostics for low-quality GPT-draft publication cases
  - Post2 angle diversification guidance
  - generic wording / analytical spine / premium tone hardening rules
  - intro overlap diagnostics
  - non-regression protection for the successful temporal layer
- This task exists to validate whether Phase 16B materially improved actual newly published article quality without regressing the successful Phase 16 temporal behavior.

Critical mission:
You must execute a fresh current-run validation and determine whether Phase 16B improved publication quality in the actual newly published prose.

You must not stop at code inspection.
You must validate the real newly generated and newly published article outputs.

==================================================
NON-NEGOTIABLE EXECUTION RULES
==================================================

1. You must execute a NEW generation run using the current Phase 16B codebase.
2. You must publish NEW outputs to WordPress.
3. You must retrieve the NEW live URLs from the CURRENT run.
4. You must validate using ONLY those NEW URLs from the CURRENT run.
5. You must NOT use old logs, old URLs, old article text, historical samples, or previously reviewed outputs as the validation basis.
6. If fresh publishing succeeds, NEW URL-based review is mandatory.
7. If fresh generation succeeds but publishing fails, review the fresh generated full text directly and explicitly mark URL-based validation as incomplete.
8. If fresh generation itself fails, report the blockage clearly and stop.
9. Do NOT ask me which option to use if the run can be executed directly.
10. Do NOT return a plan or memo instead of performing the task.
11. You must inspect `p16b_guard` if available in scores, logs, metadata, or emitted diagnostics.
12. You must also inspect `p16_ssot_run` and `p15f_strip` if they remain available.
13. If any of those diagnostics are unavailable, explicitly mark diagnostic visibility as incomplete.
14. If Step3 fails for either post, you must explicitly compare the final published quality against the guard diagnostics instead of stopping at the failure event.
15. You must include the full published body text of Post1 and Post2 in the final MD report.

==================================================
PRIMARY GOAL
==================================================

Determine whether Phase 16B produced real article improvement in publication quality while preserving temporal trustworthiness.

This means validating whether the new articles are now:
- more resilient when Gemini Step3 fails or partially fails
- less repetitive across Post1/Post2 intros and early development
- less generic and more publication-ready in prose quality
- stronger in analytical spine, interpretive density, and premium editorial tone
- still fully compliant with the successful Phase 16/16A temporal-state behavior

==================================================
PHASE 16C SUCCESS DEFINITION
==================================================

Phase 16C should be judged successful only if most of the following are true in the actual newly published outputs:

1. `p16b_guard.step3_status` meaningfully reflects whether Step3 revision succeeded, failed, or was bypassed
2. if Step3 fails, the final published article does NOT collapse into clearly generic or flat GPT-draft quality
3. `p16b_guard.intro_overlap` indicates lower or acceptable overlap, and the actual intros/early paragraphs are meaningfully more distinct
4. `p16b_guard.emergency_polish` status matches the real presence/absence of generic wording markers
5. Post2 no longer feels like a near-parallel restatement of Post1 in intro rhythm or thematic opening
6. analytical spine is preserved:
   - why now
   - market impact
   - transmission path
   - uncertainty / counterpoint
7. premium tone is preserved or improved:
   - calm, high-trust, financially literate
   - not noisy, not hype-like, not flat newsroom filler
8. the successful temporal behavior from Phase 16/16A remains intact:
   - settled current-year past-month facts stay settled
   - `[전망]` is not reintroduced on settled monthly facts
   - future-looking statements remain correctly preserved only where genuinely forward-looking

==================================================
MANDATORY VALIDATION CHECKLIST
==================================================

You must inspect and explicitly report all of the following.

### A. Run / Publish Audit
- Was a fresh run executed?
- What is the run_id?
- Were Post1 and Post2 both newly published?
- What are the new live URLs?
- Was any Step3 call unsuccessful (timeout / 503 / parse failure / no revision)?
- Was quality review performed on the exact new live outputs?

### B. Diagnostic Visibility Audit
For each available diagnostic, report the raw value if possible.

Required targets:
- `p16b_guard.step3_status`
- `p16b_guard.intro_overlap`
- `p16b_guard.emergency_polish`
- `p16_ssot_run`
- `p15f_strip`

For each diagnostic:
- available or unavailable
- raw content or summary
- whether it aligns with the actual published prose

### C. Step3 Failure Resilience Audit
For each post:
- Did Step3 succeed, fail, or partially fail?
- If Step3 failed, did the final published text still maintain acceptable publication quality?
- Did the article become obviously generic, repetitive, or structurally weak?
- Is `FAILED_NO_REVISION` or equivalent status correctly surfaced if applicable?

### D. Continuity / Overlap Audit
Compare Post1 and Post2 on:
- first paragraph opening angle
- first 2~3 paragraph rhythm
- repeated phrase patterns
- thematic opening duplication
- whether Post2 enters directly through stock-specific framing rather than repeating macro framing

You must evaluate both:
1. diagnostic overlap result
2. actual reader-facing overlap impression

### E. Quality / Tone Audit
For each post, inspect:
- generic wording frequency
- analytical spine clarity
- interpretive density
- premium tone consistency
- whether the article sounds like a publication-ready Macromalt piece instead of a safe generic model summary

### F. Temporal Non-Regression Audit
Confirm whether the newly published outputs still preserve:
- no `[전망]` misuse on settled current-year past-month data
- no future verbs applied to clearly settled monthly facts
- true forward-looking statements preserved as forward-looking
- no collapse in fact/forecast separation

==================================================
FAILURE MODES TO CHECK
==================================================

You must explicitly assess the following failure modes.

- **FM1**: settled current-year past-month data is still written as `[전망]`
- **FM2**: settled current-year past-month data still uses future-style verbs
- **FM3**: `p16_ssot_run` claims success but prose contradicts it
- **FM4**: Step3 failure occurs but no explicit status visibility is surfaced
- **FM5**: Step3 failure occurs and final prose quality collapses into generic draft quality
- **FM6**: Post1/Post2 intros still feel near-duplicated despite overlap guard
- **FM7**: anti-generic rules flatten the prose unnaturally or make it stiff
- **FM8**: premium tone remains weak even though generic markers are reduced
- **FM9**: `emergency_polish` diagnostics do not match the actual generic-marker reality
- **FM10**: temporal gains regress while quality hardening is being added

For each failure mode, mark one of:
- PASS
- IMPROVED
- PARTIAL
- FAIL
- NOT OBSERVABLE

==================================================
SCORING / JUDGMENT FRAME
==================================================

Your final judgment must weigh both temporal trust and publication quality.

Use the following explicit categories:

1. `temporal_non_regression`
2. `step3_failure_resilience`
3. `diagnostic_observability`
4. `post1_post2_continuity`
5. `generic_wording_reduction`
6. `analytical_spine_preservation`
7. `premium_tone`
8. `reader_facing_distinctiveness`
9. `overall_publication_readiness`

Each category must be marked:
- PASS
- WARN
- FAIL

==================================================
GO / HOLD RULE
==================================================

Return **PHASE16C_OUTPUT_GO** only if:
- temporal_non_regression = PASS
- diagnostic_observability is at least PASS or strong WARN with meaningful usable visibility
- step3_failure_resilience is at least WARN and not FAIL
- continuity / distinctiveness shows real reader-facing improvement or acceptable separation
- overall_publication_readiness is at least WARN trending positive
- there is no new serious regression introduced by Phase 16B

Return **PHASE16C_OUTPUT_HOLD** if any of the following occur:
- temporal trust regresses
- Step3 failure still causes severe publication-quality collapse
- diagnostics are too weak to guide 16D/16E
- Post1/Post2 remain substantially repetitive in intro and thematic opening
- anti-generic hardening causes strong unnatural prose degradation

==================================================
OUTPUT FORMAT
==================================================

You must provide:

### 1. Chat reply summary
Very concise:
- gate result
- run_id
- new URLs
- 3~6 bullet conclusions
- what improved
- what still failed
- what Phase 16D should target next

### 2. Detailed MD report
Create a new markdown file with a name like:
- `REPORT_PHASE16C_REAL_OUTPUT_VALIDATION.md`

The report must include:
1. Run audit
2. Diagnostic visibility audit
3. Executive judgment
4. Post1 detailed review
5. Post2 detailed review
6. Failure mode table
7. Category score table
8. Final GO/HOLD judgment
9. Recommended next-step focus for 16D
10. **Full published body text of Post1**
11. **Full published body text of Post2**

==================================================
IMPORTANT INTERPRETATION RULE
==================================================

Do not give Phase 16B credit merely because diagnostics were added.
Give credit only if:
- diagnostics match reality
- reality shows publication-quality improvement
- temporal gains remain preserved

The standard is not “more instrumentation exists.”
The standard is “the actual newly published prose is stronger and safer.”

