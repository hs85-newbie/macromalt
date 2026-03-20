# 05. Exact Files to Modify

## 1. /Users/cjons/Documents/dev/macromalt/styles/wordpress/base.css
- **Reason**: Update global design tokens (colors, spacing, font-weight) to match the "Institutional Brief" direction.
- **Classification**: CSS-only.
- **Rollback Impact**: Low. Restores baseline variables.
- **Parent Theme**: Untouched.

## 2. /Users/cjons/Documents/dev/macromalt/styles/wordpress/typography.css
- **Reason**: Implement the final typography stack, refine H1-H3 hierarchy, and optimize line-height/margins for long-form reading.
- **Classification**: CSS-only.
- **Rollback Impact**: Low. Restores baseline reading experience.
- **Parent Theme**: Untouched.

## 3. /Users/cjons/Documents/dev/macromalt/styles/wordpress/components.css
- **Reason**: Redesign analytical badges and refine the visual presentation of "Picks" and "Source" boxes.
- **Classification**: CSS-only.
- **Rollback Impact**: Medium. Changes the appearance of data-heavy sections.
- **Parent Theme**: Untouched.

## 4. /Users/cjons/Documents/dev/macromalt/theme/child-theme/style.css
- **Reason**: Add layout overrides (e.g., hiding theme credits) and target GeneratePress specific classes to remove the "default" look.
- **Classification**: CSS-only.
- **Rollback Impact**: Low. Restores theme defaults.
- **Parent Theme**: Untouched.

## 5. /Users/cjons/Documents/dev/macromalt/theme/child-theme/style.css (Template Field)
- **Reason**: Set the `Template:` header to `generatepress` once confirmed.
- **Classification**: WordPress Child Theme Config.
- **Rollback Impact**: Critical. If incorrect, the child theme won't activate.
- **Parent Theme**: Untouched.
