# 06. Rollback Plan

## Overview
In the event of a visual regression or layout breakage, follow these steps to restore the original baseline.

## 1. Per-File Rollback Method
- **Option A (Git)**: Run `git checkout styles/wordpress/*.css theme/child-theme/style.css`.
- **Option B (Manual)**: Revert individual changes using the `TargetContent` and `ReplacementContent` logic if git is unavailable.

## 2. Rollback Priority Order
1. `theme/child-theme/style.css`: Reverting this will disable layout-wide overrides.
2. `styles/wordpress/base.css`: Reverting this will restore original color tokens and dimensions.
3. `styles/wordpress/typography.css`: Reverting this will restore the original reading hierarchy.
4. `styles/wordpress/components.css`: Reverting this will restore the original badge/box styles.

## 3. Fast-Disable Path
If the site's layout breaks entirely (e.g., due to a CSS syntax error), comment out the `@import` lines in `theme/child-theme/style.css` to instantly revert to the parent theme's default styles (minus the `generator.py` inline styles).

## 4. What to Revert First
If "Single Post" view looks broken, revert `typography.css`.
If "Homepage/Header" looks broken, revert `style.css`.
If "Analytical Badges" look broken, revert `components.css`.
