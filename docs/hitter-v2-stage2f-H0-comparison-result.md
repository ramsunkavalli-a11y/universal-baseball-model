# Hitter v2 Stage 2f H0 disclosed-comparison result

## Scientific outcome

`H0_NEUTRAL_HIERARCHICAL_OUTCOMES` failed its frozen development gate. It did
not beat the metric-wise strongest wrapped baseline on any of the four primary
metrics in any required fold/weighting view. Pooled results were also worse,
and correlation and calibration guardrails failed in every fold. H0 is a final
failed challenger and cannot be retuned on these results.

This does not mean PBP terminal outcomes lack predictive value. Reference C0
remained the strongest comparator for most rate metrics, confirming the broad
outcome-history signal found earlier. It means this particular combination of
level translation, age-development surfaces, and earlier-origin calibration
did not improve that signal reliably.

## Fold pattern

- V2022: H0 intentionally reduces to the untranslated C0 fallback. It ties B0
  on wOBA/runs RMSE and loses proper event scores to wrapped Marcel, so strict
  improvement is impossible. Calibration and supported-subgroup gates also
  fail.
- V2023: this is the closest fold. H0 is only `0.00017` worse in player-weighted
  wOBA RMSE and `0.00029` worse in player-weighted log loss than reference C0,
  and it avoids material subgroup reversal. It still loses every primary
  metric in both views and fails correlation/calibration requirements.
- V2024: the architecture breaks materially. H0 is worse than reference C0 by
  `0.03642` player-weighted and `0.03678` PA-weighted terminal log loss. Its
  PA-weighted wOBA RMSE is `0.00407` worse and runs/600 RMSE is `2.05` runs
  worse. The wOBA calibration slopes fall to `0.589` player-weighted and
  `0.515` PA-weighted, far below the frozen `0.90` lower bound.

Pooled across folds, H0 worsens player-weighted wOBA/runs RMSE by 0.51% and
PA-weighted RMSE by 3.92%. It also worsens pooled log loss by roughly 0.73% to
0.75%, rather than achieving the required improvement.

## Concrete failure mechanism

The 2024 probability surface becomes too compressed and collapses several rare
but real terminal outcomes. On a PA-weighted basis, H0 predicts FC reaches at
about `0.0000013` versus `0.00195` observed and `0.00221` from reference C0.
It predicts triples at `0.00040` versus `0.00372` observed, sacrifice flies at
`0.00164` versus `0.00702`, and multi-outs at `0.01381` versus `0.02058`.
Those near-zero probabilities incur a large proper-score penalty. Meanwhile,
H0 overpredicts singles and ordinary outs, so the problem is not merely a
different but equally calibrated decomposition.

The likely architectural issue is that multiple link-scale transformations—
translation, forward development, and calibration—compound on sparse nested
branches. Training-origin selection did not reveal the instability strongly
enough, particularly because V2023 could not identify the surface settings and
V2024 had only one informative earlier surface origin. This is a diagnosis,
not authorization to repair H0.

## Execution integrity and boundary

Two executions stopped before producing any report because fractional
reference-target counts encountered an exact-equality legacy diagnostic. The
recorded numerical amendment changed no model, target probability, or gate;
the maximum PA reconciliation adjustment was `1.14e-13`. No partial metric was
inspected or used. The completed report SHA-256 is
`cde2b669cc0d1381195eb328a25aff5f47f81a1c4c74a4c94fcd7ceb81f65ea3`.

H1 cannot rescue a failed H0 under the frozen contract. H1, tracking, protected
confirmation, Stage 3, and WAR remain closed. Any further batting candidate
requires a genuinely distinct preregistered contract and must treat the H0
result as disclosed development evidence.
