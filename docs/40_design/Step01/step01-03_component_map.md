# 03. Component Map

## Implementation Categories

### 1. CSS-Only (Antigravity Primary Scope)
- **Single-Post Body**: Paragraph rhythm, line-height, and measure (max-width).
- **Blockquote / Callout**: Thinner accent border, background refinement.
- **Source Box**: Monospaced font for links, all-caps metadata labels.
- **Analytical Badges**: Stylizing existing `.macromalt-label-*` classes.
- **Footer**: Hiding "Built with GeneratePress" via `display: none`.
- **Archive List**: Tightening meta-data spacing and hover states.

### 2. Template-Required (Antigravity Secondary Scope)
- **Analytical Labels**: If brackets like `[해석]` are hardcoded in content and not wrapped in Spans, template logic in `generator.py` would need a `replace()` call (but this is discouraged; I will try CSS-first).
- **Identity**: If the site title/logo HTML is entirely missing from the DOM, a template part modification would be needed.

### 3. WordPress Admin / Config Required (Operator Scope)
- **Navigation**: Configuring the Menu to replace "Sample Page" with actual categories.
- **Site Title/Logo**: Uploading a logo or setting the Site Title in Customizer.
- **Homepage Shell**: Selecting a static page or configuring the latest posts layout.

### 4. Remove / Not Recommended
- **Pseudo-element tagline insertion**: "Research & Analysis" text injection via CSS is fragile for SEO and accessibility; better handled via WP Admin.
