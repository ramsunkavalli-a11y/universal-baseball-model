# Hitter v2 gap-aware G0 comparison result

Date: 2026-08-26

Scientific result: older demonstrated outcomes improved the model on average,
but G0 did not pass the frozen every-fold promotion gate.

## What improved

G0 supplied the existing C0 terminal-outcome model with accepted 2019 MiLB and
certified 2019-2020 MLB history. It added no contextual predictor and performed
no hyperparameter search.

Compared with frozen C0, G0 improved every pooled primary metric in both player
and PA weighting. It also improved every V2022 metric relative to C0, including
future wOBA and batting-runs RMSE, which confirms that the older history partly
repairs the original thin-history problem.

The pooled improvements versus the metric-wise strongest baseline were:

- player weighted: 0.030% log loss, 0.020% Brier, 0.177% wOBA RMSE, and 0.177%
  runs/600 RMSE;
- PA weighted: 0.039% log loss, 0.008% Brier, 0.417% wOBA RMSE, and 0.417%
  runs/600 RMSE.

These are real directional gains, but smaller than the frozen 0.25% proper-score
and 1% rate-RMSE minimums.

## Why it failed

- V2022: G0 improved all four metrics versus C0, but Marcel still had better
  log loss and Brier score. Correlation, calibration, and supported-subgroup
  guardrails also failed.
- V2023: seven of eight primary metric/view cells improved, but player-weighted
  Brier worsened by 0.000058.
- V2024: proper scores improved, while player/PA wOBA RMSE worsened by
  0.0000075/0.0000246 and runs/600 RMSE by 0.0038/0.0124.
- Calibration did not pass in any fold.

This pattern is coherent: older outcomes stabilize the distribution and help
players with thin recent histories, but they add a small amount of stale signal
for players whose recent skill has changed.

## Decision

G0 is a useful developmental batter forecast, not a promoted production model.
Its failure is final, and its historical weighting cannot be tuned on these
results. The preregistered opponent, contact-process, lineup, and physical
increments required a passing G0 core, so they cannot be fitted as a rescue.

No protected 2026 outcome was opened. Stage 3 and WAR remain closed. The exact
next choice is either a genuinely distinct preregistered batter candidate or an
explicit decision to publish a clearly labeled, non-promoted developmental
forecast while waiting for future confirmation.

Canonical lint passed and all 1,029 repository tests passed.
