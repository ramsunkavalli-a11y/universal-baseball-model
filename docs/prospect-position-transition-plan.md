# Prospect minor-to-MLB position-transition test plan

Status: frozen before first score.

## Question

For a hitter who reaches MLB, does his minor-league position group improve the
prediction of his MLB position group over the overall destination distribution?
If so, use a probability mixture rather than assuming his current position forever.

## Sources and population

Use only the certified StatsAPI fielding-usage tables. Current minor-league position
is the group with the most summed games started in the origin season. Destination is
the group with the most summed MLB games started in the next two completed seasons.
The test is conditional on having MLB fielding usage in that horizon; non-arrivals
remain handled by the separate arrival hurdle.

Groups are catcher, middle infield, corner infield, outfield, and DH/other. Pitcher
fielding is excluded.

## Chronology

- Development: train on 2021 origins and evaluate 2022 origins.
- Outer check: train on 2021 and 2022 origins and evaluate 2023 origins through
  completed 2025.
- The 2023 outcome is not used to select smoothing.

## Models and scoring

The baseline is the training destination distribution without origin position.
The candidate is the origin-to-destination count matrix regressed toward that
baseline. Select one prior weight from 10, 25, or 50 MLB arrivals using development
multiclass log loss, with multiclass Brier as a no-harm gate.

Report outer log loss, Brier, exact destination accuracy, calibration by predicted
probability, counts, and every origin/destination cell. A candidate may advance only
if both outer proper scores beat the marginal baseline. No single subgroup or exact-
match rate can rescue a failure.

## Boundaries

No outside FV, organization, depth chart, birth country, physical measurement,
prospect list, or current-season outcome is an input. A passing result authorizes a
private position-probability sensitivity only; it does not authorize a subjective
catcher bonus, quota, or published value change.
