# Hitter v2 Stage 2b disclosed-development checkpoint

Recorded 2026-08-24 on `hitter-v2-pbp-outcomes`.

## Scientific outcome

No Stage 2b candidate passed the frozen disclosed-development gate. The run
used only the already-disclosed V2022-V2024 folds and never opened protected
2026 outcomes, tracking data, Stage 3, or WAR.

This is not evidence that contact shape is useless. D1's four trajectory groups
improved pooled proper scores over calibrated C0 in both player and PA views,
passed its richer-model ablation, beat the strongest simple baseline on every
required proper score in V2023 and V2024, and improved pooled wOBA RMSE versus
B0. It nevertheless failed two independently frozen safety requirements:

- pooled calibration distance worsened versus uncalibrated C0 in both views;
- V2023 AAA had a material PA-weighted rate reversal: +0.00207847 wOBA RMSE
  and +1.04533 runs/600 RMSE versus the metric-wise strongest baselines.

D0 also worsened calibration and had a V2023 AAA reversal. Its V2023
PA-weighted Brier score narrowly lost to B0. D2's full ten direction and
trajectory bins added no supported incremental value over D0: pooled
PA-weighted proper scores worsened, and wOBA RMSE worsened by 0.8027% in the PA
view and 0.3752% in the player view, both beyond the frozen 0.25% guardrail.

## Numerical execution incident

The first run stopped before any V2023 score because the deterministic
optimizer exceeded a 2,000-iteration numerical ceiling. The incident was
recorded before repair. Raising only that ceiling to 20,000—without changing
the objective, penalty, candidates, inputs, folds, or gates—was committed at
`80bf449` before the successful restart.

## Reproducibility and boundary

- generated report SHA-256:
  `1b54190d21304fe25c14e1751ab5bc4fb2e8e33cb4d77869a6db7ce846830428`;
- report size: 368,999 bytes;
- two complete executions produced the exact same report hash;
- 18 generated prediction/coefficient tables total 4,855,515 bytes;
- 6,260 player-fold rows and 1,750,625 target PA enter the pooled V2023-V2024
  evaluation;
- no candidate was selected;
- no result-driven retuning is allowed;
- protected 2026 confirmation, tracking, Stage 3, and WAR remain closed.

The exact next authorized gate is review of this failure and, only if desired,
a new versioned candidate contract based on the diagnosis rather than on
protected outcomes.
