# Prospect positional-runs validation result

Status: transition-weighted value adjustment rejected.

## Outer result

The frozen comparison used 576 hitters with a 2023 minor-league origin and official
MLB fielding usage in 2024 or 2025.

| Model | MAE (runs/600) | RMSE (runs/600) | Bias |
|---|---:|---:|---:|
| Carry current minor-league usage forward | 3.740 | 5.109 | +0.454 |
| Transition-weighted destination estimate | 4.561 | 5.680 | +0.545 |

Candidate-minus-baseline MAE is +0.821 with a 95% player-bootstrap interval of +0.495
to +1.140. RMSE difference is +0.571 with an interval of +0.197 to +0.936. The
candidate is clearly worse on both frozen proper-error measures.

No origin group rescues it. Catcher RMSE improves slightly but MAE worsens. Middle-
infield RMSE improves while MAE worsens. Corner, outfield, and the small other group
worsen materially.

## Meaning

The earlier transition classifier answered a narrower question correctly: current
minor-league position group strongly predicts future MLB position group. That does not
mean the coarse five-group probabilities accurately predict the numerical positional-
run component. Exact positions and within-player multi-position usage matter.

The value sensitivity is rejected and the playable default remains unchanged. Do not
penalize catchers or shortstops from the coarse transition matrix. A future candidate
must target player-level positional runs directly and be selected on development data;
the 2023-to-2025 group is now disclosed and cannot be reused as untouched confirmation.

No outside FV, current player value, organization depth, or subjective position rule
was used. Machine-readable detail:
`docs/prospect-positional-runs-validation-result.json`.
