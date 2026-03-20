# PROMPT_CLAUDE_CODE_MACROMALT_SEO_MONETIZATION_v1

아래 프롬프트를 Claude Code에 그대로 전달한다.

```text
You are working on the Macromalt SEO / monetization track.

Use the attached SSOT document `MACROMALT_SEO_MONETIZATION_SSOT_v1.md` as the single source of truth.
Follow it strictly.

Your role:
Implement the safest possible technical SEO baseline and a conservative monetization architecture for the current WordPress presentation layer.

Do NOT modify:
- article generation logic
- temporal SSOT
- verifier / reviser core structure
- factual / verification logic
- publishing gates
- slot policy
- content quality policy
- Post2 opener rules
- Phase 19 quality logging structure

Allowed scope:
- WordPress theme / child-theme
- template parts
- CSS
- metadata injection
- schema injection
- robots / sitemap / ads.txt
- script loading order
- page-level information architecture
- ad placement and disclosure UX
- internal linking / taxonomy / archive policy

Priorities:
1. technical SEO baseline
2. conservative monetization placement
3. schema / performance guardrails
4. rollout-safe optimization

Brand target:
- premium financial editorial
- restrained luxury
- calm, intelligent, dense but breathable
- typography-first
- mobile readable
- not a generic news portal
- not a retail trading app
- no gimmicky motion

Execution order:
Step 1 — current-state audit
Step 2 — exact file inventory
Step 3 — technical SEO baseline plan
Step 4 — monetization placement plan
Step 5 — code changes
Step 6 — QA checklist
Step 7 — rollback plan

Required output format:
1. current-state audit
2. exact files to change
3. implementation plan
4. code changes
5. QA checklist
6. rollback plan
7. risks / open questions

Additional constraints:
- separate required items from optional items
- separate safe immediate changes from deferred/risky changes
- do not rewrite article text
- do not redesign the publishing pipeline
- preserve mobile readability
- protect source/reference block readability
- avoid misleading navigation-like ad placement
- avoid H1-adjacent ad placement
- avoid meaningful Core Web Vitals regression

Begin by auditing the current theme / child-theme / metadata / schema / robots / sitemap / ad-loading structure.
Then propose the least invasive implementation path.
```
