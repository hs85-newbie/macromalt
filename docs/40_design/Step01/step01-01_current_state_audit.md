# 01. Current State Audit (Macromalt)

## 1. Homepage Issues
- **Identity**: No visible site title or logo. Only "Sample Page" in the navigation.
- **Header**: Too sparse. Lacks professional branding.
- **Rhythm**: Simple vertical list of excerpts. Feels like a default blog, not a financial portal.
- **Footer**: "Built with GeneratePress" credit is visible, reducing the "custom premium" feel.

## 2. Header/Nav Issues
- **Desktop**: Only a single "Sample Page" link. No search or category navigation.
- **Mobile**: Hamburger menu is present but contains only "Sample Page".

## 3. Single-Post Issues
- **Hierarchy**: H1 is very large. H3 has a solid left border and background, which is a good editorial start but could be refined.
- **Spacing**: Paragraph rhythm is decent (1.9 line-height) but bottom margins feel a bit uniform.
- **Identity**: The post author "somang04" is displayed but might benefit from a more professional "Editorial Team" or "Macromalt Research" label.

## 4. Archive/Category Issues
- **Vibe**: Identical to homepage. No visual distinction for "Series" or "Deep Dives".
- **Scanability**: Moderate. Titles are large, but summary text is a bit dense.

## 5. Source-Box Issues
- **Design**: Currently a light gray box with a gold left border. Functional but looks a bit like a generic alert box.
- **Typography**: Uses small text (13px). Could use a more "tabular" or "monospaced" feel for data points.

## 6. Badge Issues
- **Current State**: Mostly just bracketed text like `[심층분석]`, `[캐시의 픽]`.
- **Visibility**: They don't stand out as "labels" or "tags". They blend into the heading text.

## 7. Mobile Issues
- **Navigation**: The menu is empty.
- **Typography**: Large H1s might be too big for narrow mobile screens (375px/390px).

## 8. Safe Override Points
- `styles/wordpress/base.css`: For updating global design tokens.
- `styles/wordpress/typography.css`: For refining hierarchy and body text.
- `styles/wordpress/components.css`: For redesigning badges and source boxes.
- `theme/child-theme/style.css`: For layout-specific overrides and hiding theme credits.

## 9. Uncertain Items
- **Fonts**: Need to check if external fonts (like Google Fonts) can be easily added to the child theme without touching the parent or generator logic.
