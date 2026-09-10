# Pitcher age-relative-to-level and handedness plan

Status: frozen before score.

## Question

Do universally available, stable pitcher demographics explain later MLB component
quality that is missing from the translated K/UBB/HBP/HR profile?

## Features

Use the most recent pre-target season's reported age relative to the median age at
that same affiliated level. Test four small adjustment families: age-relative only,
throwing-hand only, both additive, and both plus their interaction. Throwing hand is
stable official profile data. Current height, weight, strike-zone measurements, birth
country, organization, and outside FV are excluded.

Each challenger starts from the incumbent translated five-component probabilities
and learns only centered multinomial adjustments. Coefficients receive a fixed L2
penalty at the player—not pitch—scale. All five probabilities are changed together
and renormalized; no component clipping is permitted.

## Chronology and gate

- Development target: 2024 MLB, using only information through 2023.
- Confirmation target: 2025 MLB, using only information through 2024.
- Population: pitchers with earlier affiliated BF, zero earlier MLB BF, and positive
  target-year MLB BF. Target membership is never a predictor.
- Select the lowest 2024 log loss among families that also improve Brier versus the
  unchanged profile. Freeze that family and coefficients before scoring 2025.
- Promote only if the frozen candidate improves both 2025 component log loss and
  Brier. Report player-bootstrap intervals and age/hand subgroup diagnostics.

No 2026 outcomes, physical measurements without historical snapshots, contract data,
individual prospect grades, target grade counts, or post-confirmation tuning are
allowed.
