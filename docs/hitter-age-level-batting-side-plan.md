# Hitter age-relative-to-level and batting-side plan

Status: frozen before scoring.

## Question

Do stable, universally available age-for-level and batting-side fields improve later
MLB hitter component forecasts beyond translated affiliated performance?

## Candidates

Start from the incumbent seven-component profile: UBB, HBP, 1B, 2B, 3B, HR, and
other. Use the current 1,200-PA regression prior. Test four small multinomial
adjustments:

1. age relative to the same-season, same-level median;
2. left and switch hitter indicators, with right-handed as reference;
3. age and batting side additively;
4. age, batting side, and the two age-by-side interactions.

Age is divided by three years and clipped to `[-2, 2]`. The adjustment receives a
fixed player-scale L2 penalty of 1. All seven probabilities move coherently and must
sum to one. Height, weight, position, birth country, organization, contracts, and
outside FV are excluded.

## Chronology and gate

- Select on 2024 MLB outcomes using only information through 2023.
- Freeze the selected family and coefficients before opening 2025.
- Confirm on 2025 MLB outcomes using only information through 2024.
- Include hitters with earlier affiliated PA, no earlier MLB PA, and positive target-
  year MLB PA. Target membership is never a feature.
- A family is selectable only if both development log loss and Brier improve.
- Promotion additionally requires both confirmation point scores to improve and both
  player-bootstrap 95% upper bounds to be at or below zero.

Report younger/older-for-level and right/left/switch subgroups. Subgroups diagnose;
they do not change the frozen global gate. No current 2026 outcome is opened.
