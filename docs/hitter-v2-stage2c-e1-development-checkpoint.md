# Hitter v2 Stage 2c E1 development result

Status: **FAILED — LADDER STOPPED**  
Date: 2026-08-24  
Execution commit: `59832379317099970d318230aa7bb69f95c6bae2`

## Scientific outcome

The pulled-air E1 increment did not add repeatable future home-run information
beyond the frozen outcome-only C0 reference. It improved HR-conditional log
loss in only the V2023 equal-player view and worsened it in the other three
required fold/weighting views. The changes were extremely small, consistent
with the fitted feature coefficients shrinking close to zero.

E1 passed the terminal proper-score comparisons against the simple B0/B1
baselines, both pooled future-wOBA/runs RMSE comparisons, and the supported-
level reversal check. Those results do not rescue it: they largely reflect the
C0 outcome model that E1 inherits. The preregistered question was whether
pulled-air shape adds information beyond C0, and that incremental HR gate
failed.

| HR log-loss comparison | E1 minus C0 | Pass |
|---|---:|:---:|
| V2023, player weighted | -0.0000000248 | yes |
| V2023, contact weighted | +0.0000000212 | no |
| V2024, player weighted | +0.0000000116 | no |
| V2024, contact weighted | +0.0000000625 | no |

## Interpretation

This does not contradict the descriptive baseball fact that pulled air balls
are highly valuable. It says that these two shrunk, season-level direction/
trajectory summaries did not forecast next-season HR outcomes beyond the
player's existing terminal outcome history. Likely explanations include a
weak incremental signal, measurement/classification noise across sources,
loss of handedness and count/pitch context, and an estimator whose fitted
increment is effectively zero. The disclosed folds cannot now be used to tune
among those explanations.

The auxiliary coverage report omitted three V2023 evaluable players through a
feature-table inner join and used an imprecise `exact_fallback` label. The
decisional metrics used the complete 3,172-player V2023 and 3,088-player V2024
prediction/target overlaps, so the gate is unaffected. The run was not repeated
to cosmetically repair a non-decisional report.

## Boundary

E2 is not authorized because it was explicitly forbidden from rescuing a
failed E1. There is no retuning or grid expansion. Protected 2026, tracking,
Stage 3, and WAR remain closed. The next authorized work is documentation and
independent design review only; any new candidate family would need a new
prospective contract and genuinely independent evaluation evidence.
