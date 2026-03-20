# Implementation Plan - Macromalt Visual Refinement

Refine the WordPress visual layer to achieve a "premium financial editorial" aesthetic without touching the generation logic.

## Proposed Changes

### Styles & Theme

#### [MODIFY] [base.css](file:///Users/cjons/Documents/dev/macromalt/styles/wordpress/base.css)
- Update color tokens for "restrained luxury" (warm backgrounds, ink tones).
- Refine spacing variables for better editorial rhythm.

#### [MODIFY] [typography.css](file:///Users/cjons/Documents/dev/macromalt/styles/wordpress/typography.css)
- Implement refined H1-H3 hierarchy.
- Optimize line-height and paragraph spacing for long-form reading.
- Style list items and blockquotes for institutional feel.

#### [MODIFY] [components.css](file:///Users/cjons/Documents/dev/macromalt/styles/wordpress/components.css)
- Redesign analytical badges (replace bracketed text with pill styles if possible via CSS selectors).
- Refine "Picks" box and "Source" box layout.

#### [MODIFY] [style.css](file:///Users/cjons/Documents/dev/macromalt/theme/child-theme/style.css)
- Add global layout overrides (hide theme credits, refine header/footer).
- Target GeneratePress specific classes to remove "default" look.

## Task Separation Matrix

| Issue | CSS-Only? | Template? | WP-Admin? | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Typography/Spacing | Yes | No | No | Antigravity |
| Badge/Box Styling | Yes | No | No | Antigravity |
| Hide Theme Credit | Yes | No | No | Antigravity |
| Site Title Visibility | Partial | Yes | Yes | Operator/Antigravity |
| Navigation Menu | No | No | Yes | Operator |
| Logo Upload | No | No | Yes | Operator |

## Implementation Sequence

1. **Style Task (CSS-Only)**: Apply refinements to `styles/wordpress/*.css`.
2. **Setup Task (WP-Admin)**: Operator (or Antigravity if access provided) configures site identity and menus.
3. **Template Task (Fallback)**: Only if styling cannot solve identity/visibility issues.

## Verification Plan

### Manual Verification
1. **Live Site Comparison**:
   - Use `execute_browser_javascript` to inject new CSS and capture screenshots.
2. **Mobile Audit**:
   - Verify readability and no overflow at 395px/375px.
3. **Checklist Review**:
   - Cross-reference with `07_QA_CHECKLIST.md`.
