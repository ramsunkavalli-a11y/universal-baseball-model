# Peak-talent skill-direction challenger

Status: frozen before score.

## Question

Does a player's recent direction—improving or declining—add repeatable information
about age-24-to-26 component talent beyond the current translated profile, age, level
and evidence?

## Exact challenger

Keep the promoted peak model and its regression strength unchanged. Add only the ILR
component difference between the translated, regressed profile available at the origin
year and the profile available one year earlier. Both snapshots use the same three-year
recency system and their own cutoff-year MLB environment. A prior-evidence flag is
included; a player without prior evidence receives a zero trend, never an invented
improvement.

No public rank, FV, organization, contract, future workload, position, current height,
birth country or 2026 outcome may enter. This is skill direction, not an age bonus.

## Gate

- Fit through peak-window end year 2014; inspect 2015-2017 development.
- Then replay unchanged structure on end years 2018, 2019, 2023, 2024 and 2025.
- Compare directly with the promoted component-development model, not a weak constant.
- Require better equal-player log loss and Brier in at least 4/5 replays, no worse event
  scores in at least 4/5, and paired equal-player uncertainty support in at least 4/5.
- If the development period does not improve both equal-player scores, reject before
  promotion regardless of later descriptive results.

