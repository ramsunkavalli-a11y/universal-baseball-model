# Pitcher Opportunity v2 development result

**Decision:** retain recent BF plus 40-man membership as the provisional candidate  
**Production status:** not confirmed  
**Protected 2026 outcomes used:** no

The precommitted pitcher gate used the same zero-inclusive hurdle method and rolling
years as the universal hitter model. Current role was included in every form. The
selected form then added age, current MLB and minor-league BF, and exact-date 40-man
membership.

## Result

Across four expanding-window tests covering 20,855 pitcher-seasons and 3,156 positive
MLB-BF outcomes, both richer candidates passed every gate. The 40-man form won
full-distribution loss in all four folds and was outside the 0.001 simplicity tie.

| Metric | Level/role P0 | Selected P | Change |
|---|---:|---:|---:|
| Full-distribution negative log loss | 1.16076 | 1.13639 | 2.1% lower |
| Participation Brier error | 0.06241 | 0.05586 | 10.5% lower |
| BF mean absolute error | 32.68 | 27.75 | 15.1% lower |
| BF root mean squared error | 83.07 | 74.37 | 10.5% lower |
| Predicted mean MLB BF | 35.79 | 34.86 | — |
| Observed mean MLB BF | 34.54 | 34.54 | — |

## Coverage and boundary

The final development fit contains 25,997 zero-inclusive pitcher snapshots and 3,918
positive next-season outcomes. It retains inactive, unknown-role and missing-age
players. It does not use pitch quality, team depth, future team, future level or future
role. The existing historical role-transition probabilities remain a separate input.

The exact coefficients, standardization, metrics and source hashes are stored under
`model_artifacts/pitcher-opportunity-v2-development-2026-09-09/`. The package may
generate a labeled provisional current forecast, but completed 2026 outcomes are still
required for production confirmation.

