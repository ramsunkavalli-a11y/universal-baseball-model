# Hitter Opportunity v2 development result

**Decision:** retain the universal recent-opportunity plus 40-man model as the
provisional 2026 candidate  
**Production status:** not confirmed  
**Protected 2026 outcomes used:** no

The lost B2 coefficients were not guessed or recreated. A new, simpler model was built
from reproducible official aggregate data under the precommitted
`hitter-opportunity-v2-development-contract.md`.

## Result

The selected form uses broad level, age, a missing-age indicator, current MLB PA,
current MiLB PA and exact-date 40-man membership. It retains inactive, unknown-level
and missing-age players. It does not use batting skill, player names, team depth or
future team/level information.

Across four expanding-window tests covering 16,295 player-seasons and 2,644 positive
MLB-PA outcomes, the selected model beat the universal level-only baseline in every
test year.

| Metric | Level-only U0 | Selected U | Change |
|---|---:|---:|---:|
| Full-distribution negative log loss | 1.25553 | 1.20293 | 4.2% lower |
| Participation Brier error | 0.05653 | 0.04494 | 20.5% lower |
| PA mean absolute error | 40.95 | 28.32 | 30.8% lower |
| PA root mean squared error | 98.88 | 73.03 | 26.1% lower |
| Predicted mean MLB PA | 45.15 | 44.85 | — |
| Observed mean MLB PA | 44.74 | 44.74 | — |

The model without 40-man membership also passed all gates, but the 40-man form had the
lower pooled loss and was outside the 0.001 simplicity tie. The 40-man model was
therefore selected under the frozen rule.

## Coverage and chronology

Training uses 20,643 zero-inclusive player-snapshot rows from 2018, 2021, 2022, 2023
and 2024, with 3,278 positive next-season MLB outcomes. The cancelled 2020 minor-league
season is excluded. Each validation year was scored using only earlier training folds.

Official source pulls reproduced 32,719 hitter snapshots, 41,149 pitcher snapshots and
9,342 exact-date 40-man memberships across the retained source years. Row-level roster
status was not used.

## Boundary

This is materially stronger and more universal than the current historical cohort
fallback, but it is development evidence. The exact coefficients, standardization,
fold metrics, source hashes and report are permanently stored under
`model_artifacts/hitter-opportunity-v2-development-2026-09-09/`.

The package now generates a clearly labeled provisional current forecast and has been
carried through the WAR and contract-economics pipeline. See
`current-hitter-opportunity-v2-2026-09-08.md`. It cannot be called B2 or
production-confirmed until completed 2026 outcomes pass a separately frozen
confirmation gate.
