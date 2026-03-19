# PROMPT_PHASE16B_OUTPUT_QUALITY_HARDENING.md

이 문서는 Claude Code에 직접 전달하는 **Phase 16B — Output Quality Hardening** 통합 실행 문서입니다.

목적:
1. Phase 16/16A에서 확보한 **Temporal SSOT 성과를 절대 회귀 없이 유지**
2. Gemini Step3 실패/timeout/503 시에도 발행 품질이 급락하지 않도록 **품질 완충 레이어**를 추가
3. Post1/Post2의 도입부·전개부 **continuity 중복과 n-gram 중복**을 줄여 연속 발행 완성도를 높임
4. 시제는 맞지만 평면적이거나 generic해지는 문장을 줄이고 **analytical spine / premium tone**을 복구
5. 이후 16C~16E에서 빠르게 미세조정할 수 있도록 **저위험·가시적·진단 가능한 구조**로 구현
6. 결과는 요약은 채팅, 상세는 MD 파일로 제출

---

## Claude Code 실행 지시문

You are implementing a structural hardening phase for the macromalt project.

Project state:
- Phase 11 is complete and verified as GO.
- Phase 12 is complete and verified as GO.
- Phase 13 implementation was GO but real-output was HOLD.
- Phase 14I reached real-output GO for its target scope.
- Phase 15 and its sub-hotfixes repeatedly addressed temporal trust failures.
- Phase 16 replaced patch-style temporal handling with a runtime Temporal SSOT.
- Phase 16A real-output validation confirmed that current-year past-month settled data is now consistently written as settled fact, with `[전망]` misuse removed and temporal diagnostics aligned with prose.
- However, Phase 16A also revealed remaining quality risks outside the core temporal fix:
  - Gemini Step3 can fail with timeout/503, causing the article to publish in a lower-quality GPT-draft state
  - Post1/Post2 continuity still shows repeated intro rhythm / n-gram overlap
  - some passages remain too generic or flattened even when temporal trust is correct
  - premium editorial tone and analytical spine are not yet fully stabilized

Your task:
Implement **Phase 16B — Output Quality Hardening**.

This is not a broad redesign.
This phase must preserve the successful Phase 16 temporal layer while adding targeted guards that prevent quality collapse and improve reader-facing distinction between consecutive published articles.

==================================================
PRIMARY OBJECTIVE
==================================================

Make the pipeline more resilient and more publication-ready without regressing the Phase 16 temporal gains.

Phase 16B succeeds only if:
1. Step3 failure no longer causes severe quality degradation in the final article
2. Post1/Post2 continuity becomes more distinct and less repetitive
3. interpretation density, analytical spine, and premium tone improve or at least stop regressing
4. Temporal SSOT behavior remains intact and continues to dominate tense/state handling
5. later micro-adjustments remain easy and inspectable

==================================================
WHY THIS PHASE EXISTS
==================================================

Phase 16 solved the core temporal-state problem.
That was the correct structural move.

But Phase 16A proved that temporal correctness alone is not enough for publication quality.
The next bottleneck is output hardening.

Current symptom pattern after 16A:
- temporal trust improved materially
- but if Step3 fails, GPT draft quality may publish too directly
- article pair continuity can still feel too similar in intro cadence or framing
- generic wording can survive even when factual tense is correct
- premium editorial polish is not yet reliably protected

This means the next phase must focus on quality resilience rather than temporal reinterpretation.

==================================================
NON-NEGOTIABLE PHASE RULE
==================================================

Phase 16B must not weaken or bypass Temporal SSOT.

Do not re-open the old pattern of letting quality fixes silently reintroduce temporal ambiguity.
Any new quality guard must sit on top of the Phase 16 temporal foundation, not compete with it.

==================================================
TRACK A — STEP3 FAILURE DEGRADATION GUARD
==================================================

Implement a guard so that Step3 timeout / 503 / verifier failure does not cause unacceptable final-output quality collapse.

Goal:
If Step3 succeeds, use it normally.
If Step3 fails, the article should still pass a stronger baseline quality floor than the current raw GPT-draft state.

Possible implementation directions (choose the lightest practical combination):
- pre-Step3 self-check / local cleanup pass for generic wording, structure, and reader-facing tone
- fallback revision pass using already available internal logic/prompts when Gemini Step3 is unavailable
- narrower emergency polish pass that improves intro distinctness, spine clarity, and generic phrasing before publication
- publish gating or retry policy only if it remains low-risk and operationally practical

Requirements:
- keep implementation inspectable
- expose whether Step3 succeeded, failed, retried, or fell back
- do not create a brittle heavy sub-pipeline
- do not depend on new external vendors or new services

==================================================
TRACK B — POST1/POST2 CONTINUITY DE-DUP
==================================================

Reduce reader-facing similarity between Post1 and Post2 within the same run.

Target symptoms:
- duplicated intro rhythm
- repeated framing template
- overlapping n-grams in opening paragraphs
- same conclusion restated with only light paraphrase
- article pair feeling like “same thesis, two wrappers”

Requirements:
- Post1 and Post2 should still feel connected as part of one publication set
- but they must clearly differ in angle, opening move, and reader-facing narrative lane
- avoid internal pipeline wording
- avoid robotic anti-overlap tricks that make prose awkward

You may use light structural controls such as:
- intro-angle diversification
- opening-question diversification
- thesis-lane separation
- anti-overlap checks on first paragraphs / first section leads
- narrow rewrite triggers when near-duplicate phrasing is detected

==================================================
TRACK C — GENERIC WORDING / ANALYTICAL SPINE HARDENING
==================================================

Reduce publication of generic, flat, analyst-summary-like wording.

Strengthen:
- why-now framing
- causal linkage from data to implication
- explicit market relevance
- analytical spine from fact → interpretation → variable → counterpoint
- sentence-level precision without bloat

Do not solve this by making prose longer for its own sake.
Do not solve this by adding excessive ornament.

Target effect:
- less “safe but bland” language
- more specific reasoning and editorial confidence
- stronger separation between factual reporting and analytical claim

==================================================
TRACK D — PREMIUM TONE RECOVERY
==================================================

Recover the brand-appropriate premium editorial tone without becoming theatrical or purple.

Desired qualities:
- calm, controlled, high-conviction
- financially literate and selective
- elegant but not flowery
- sharper than generic sell-side note style
- clearly above plain summary writing

Do not:
- over-stylize
- introduce exaggerated metaphor load
- damage trustworthiness or numerical clarity
- weaken hedge discipline where caution is appropriate

==================================================
TRACK E — TEMPORAL NON-REGRESSION SAFETY
==================================================

Add explicit protection so 16B quality changes do not regress the 16/16A temporal wins.

At minimum, preserve:
- settled current-year past-month prose correctness
- no misapplied `[전망]` on settled monthly facts
- no future-style verbs on settled monthly facts
- `p16_ssot_run` plausibility
- `p15f_strip` plausibility where available
- compatibility with completed-year actual enforcement

If needed, add focused regression checks or score visibility to ensure quality hardening cannot silently undo temporal normalization.

==================================================
TRACK F — INSPECTABILITY / DIAGNOSTIC VISIBILITY
==================================================

Phase 16B should be easy to verify in 16C~16E.

Expose enough information that later validation can answer:
- Did Step3 succeed, fail, retry, or fall back?
- If it failed, which fallback or hardening path ran?
- Was continuity anti-overlap triggered?
- Which parts of Post1/Post2 were diversified?
- Did any quality hardening path touch temporal-sensitive lines?
- Did any new guard improve generic wording or spine density measurably?

Prefer small, readable diagnostic fields over giant debug dumps.

==================================================
TRACK G — SCOPE DISCIPLINE
==================================================

G1. Do not redesign the full architecture.
This is a hardening phase, not a new platform rewrite.

G2. Do not add new external APIs or providers.
Use the existing pipeline and available model stack only.

G3. Do not undo prior gains.
Preserve:
- Temporal SSOT integrity
- hedge clamp gains
- internal pipeline language safety
- reader-facing continuity naturalness

G4. Keep implementation incremental.
16C~16E should still be able to make narrow adjustments quickly.

==================================================
IMPLEMENTATION CONSTRAINTS
==================================================

1. Public function signatures should remain stable unless strongly necessary.
2. Prefer additive guards, scoring, or fallback layers over invasive rewrites.
3. Any fallback must be transparent enough to inspect later.
4. Avoid prompt bloat that materially harms generation efficiency without clear quality benefit.
5. Keep WordPress publication flow operationally simple.
6. Do not silently trade away temporal trust for style gains.

==================================================
REQUIRED DELIVERABLES
==================================================

You must produce all of the following:

1. Code implementation
Implement Phase 16B Output Quality Hardening.

2. Documentation
Create/update concise internal docs describing:
- why Phase 16A GO did not end the quality hardening work
- what 16B changes were added
- how Step3 failure degradation is now handled
- how Post1/Post2 continuity separation is improved
- how generic wording / analytical spine / premium tone were protected
- how temporal non-regression is enforced
- what remains intentionally out of scope for 16C+

3. Verification checklist
Provide a verification section suitable for manual or automated review.

Suggested categories:
- Step3 failure no longer causes unacceptable quality collapse
- fallback / retry / hardening path is visible
- Post1/Post2 intro overlap is reduced
- continuity remains natural while angle separation improves
- generic wording is reduced
- analytical spine is preserved or improved
- premium tone is preserved or improved
- temporal SSOT remains intact
- completed-month / completed-year temporal non-regression holds
- public signatures remain stable
- imports/build pass

==================================================
SUCCESS CRITERIA
==================================================

Phase 16B should be judged successful if the implementation makes the pipeline materially more publication-safe under Step3 instability, while preserving the now-working temporal SSOT foundation and reducing pairwise article sameness.

The intended result is not perfection in one phase.
The intended result is a stronger publication floor and a cleaner base for 16C~16E micro-adjustments.

==================================================
OUTPUT FORMAT
==================================================

Return:
1. concise chat summary
2. detailed Markdown report file
3. changed-file list
4. verification result with explicit GO / HOLD judgment
5. known residual risks

Do not stop at a plan.
Implement the phase.
