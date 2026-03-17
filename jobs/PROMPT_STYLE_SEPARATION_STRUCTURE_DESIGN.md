# PROMPT_STYLE_SEPARATION_STRUCTURE_DESIGN.md

이 문서는 Claude Code에 직접 전달하는 **스타일 분리용 구조 설계 프롬프트**입니다.

목적:
1. `main.py`, `publisher.py` 등에 섞여 있는 스타일/마크업 관련 구문을 분리 가능한 구조로 재설계
2. Python 로직, HTML 템플릿, CSS 스타일을 명확히 분리
3. 이후 Antigravity / Codex가 **HTML/CSS만 안전하게 수정**할 수 있는 기반 마련
4. 본문 생성/검증 파이프라인과 프론트 스타일 트랙을 완전히 분리

---

## Claude Code 실행 지시문

You are designing a structural refactor plan for the Macromalt project.

Important:
This task is about **presentation-layer separation only**.
Do NOT redesign article generation logic, LLM prompts, verification rules, or publishing decision logic.

The goal is to separate style/presentation concerns from Python publishing logic so that front-end styling can later be handled safely by Antigravity or Codex.

==================================================
PRIMARY OBJECTIVE
==================================================

Design a safe structure that separates:

- Python logic
- HTML markup/templates
- CSS styling

The desired future state is:

- Python handles data preparation and publishing flow
- HTML templates handle markup structure
- CSS files handle presentation/styling
- front-end/style agents can modify HTML/CSS without touching generation/verification logic

==================================================
WHY THIS REFACTOR IS NEEDED
==================================================

Currently, style-related strings and markup may be embedded inside Python code such as `main.py` and `publisher.py`.

That creates several problems:
- style changes require touching publishing logic
- rollback is harder
- front-end work and content-pipeline work collide
- non-Python style agents cannot safely operate
- HTML/CSS experimentation becomes risky

This task exists to define a safer separation boundary.

==================================================
SCOPE
==================================================

Scope in:
- extracting inline or embedded style-related structures from Python code
- separating HTML template responsibility
- separating CSS responsibility
- proposing safe file structure
- defining how Python should pass data into templates
- identifying least-invasive migration path
- documenting rollback-safe implementation order

Scope out:
- rewriting article text
- changing LLM prompts
- temporal/factual verification logic
- publishing rules
- broad WordPress redesign
- plugin architecture changes unless required for presentation separation only

==================================================
DESIGN TARGET
==================================================

The target structure should make it easy to support a future workflow like this:

1. Python pipeline generates normalized article data
2. Python passes data into template layer
3. HTML template renders structure
4. CSS defines visual style
5. Antigravity / Codex modifies only HTML/CSS files
6. Article-generation logic remains untouched

==================================================
REQUIRED OUTPUT
==================================================

You must produce a practical design, not a vague memo.

Your output must include:

## 1. Current-State Audit
Identify the likely places where style/markup concerns are mixed into Python.
Focus on files such as:
- `main.py`
- `publisher.py`
- any helper files that appear to contain inline HTML/CSS or string-assembled presentation logic

Explain:
- what kind of style/markup logic is embedded
- what should be separated first
- what should remain in Python

## 2. Target Separation Architecture
Propose a target structure that clearly separates:
- logic
- templates
- styles

Recommended form should include candidate directories like:
- `templates/`
- `styles/`
- optional presentation helpers if needed

You may adjust naming, but keep it practical.

## 3. Template Strategy
Explain:
- what should become HTML templates
- how article sections, badges, source blocks, etc. should be represented
- what variables/data Python should inject into templates
- what must never be hardcoded in templates vs Python

## 4. CSS Strategy
Explain:
- what should move into CSS files
- how to split CSS by concern
- how to keep CSS maintainable and safe for future front-end agent work
- what naming conventions or scoping rules are recommended

## 5. Migration Plan
Provide an implementation order that minimizes breakage.

Preferred style:
- Step 1: extract without behavior change
- Step 2: switch Python to template reference
- Step 3: validate HTML parity
- Step 4: split CSS concerns
- Step 5: prepare front-end safe modification zone

## 6. Risk Analysis
Explain risks such as:
- rendering regressions
- article layout drift
- data-template mismatch
- duplicated styling sources
- template escape/sanitization issues if relevant

## 7. Rollback Plan
Explain how to reverse the migration safely if needed.

## 8. Exact Deliverables for Next Phase
Define what the next implementation phase should produce.
This should be concrete enough that Claude Code, Antigravity, or Codex can implement it next.

==================================================
DESIGN RULES
==================================================

1. Prefer minimal-invasive structure over grand redesign.
2. Preserve current publishing behavior as much as possible.
3. Keep Python responsible for data and flow, not visual styling.
4. Keep HTML responsible for structure.
5. Keep CSS responsible for appearance.
6. Make future HTML/CSS-only editing feasible.
7. Make rollback easy.
8. Avoid unnecessary abstractions.

==================================================
IMPORTANT CONSTRAINTS
==================================================

- Do not implement styling redesign yet.
- Do not propose broad WordPress redesign here.
- Do not modify article-generation prompt logic.
- Do not modify verification gates.
- Do not blur logic/presentation boundaries again in the target architecture.
- The result must be useful for a follow-up implementation prompt.

==================================================
OUTPUT FORMAT
==================================================

Return in this structure:

# STYLE SEPARATION STRUCTURE DESIGN

## 1. Current-State Audit

## 2. Target Separation Architecture

## 3. Template Strategy

## 4. CSS Strategy

## 5. Migration Plan

## 6. Risk Analysis

## 7. Rollback Plan

## 8. Next Implementation Deliverables

## 9. Final Recommendation

In the final recommendation:
- say whether this separation should be done now or later
- state the safest implementation order
- state what should remain in Python permanently

==================================================
STYLE OF RESPONSE
==================================================

Be practical, technical, and architecture-focused.
Do not give a generic essay.
Do not jump into unrelated redesign ideas.
Design for safe execution by another coding agent.

---

## Additional operator note

This work is being split intentionally so that:
- Claude Code can continue owning content-quality / pipeline logic
- Antigravity or Codex can later own style-layer work only

Your design must support that operating model cleanly.

---

## 실제 사용 예시

Claude Code에게는 짧게 이렇게 지시하면 됩니다:

`PROMPT_STYLE_SEPARATION_STRUCTURE_DESIGN.md 읽고 설계해. 결과는 요약은 채팅, 상세는 MD로 제출해.`
