# Hitter v2 post-H0 diagnostic result

Date: 2026-08-25  
Status: complete; diagnostic only; no new candidate fit or scored

## Scientific outcome

The PBP outcome foundation remains viable. Raw C0 beat Marcel on future wOBA
and batting-runs/600 RMSE in all three disclosed folds under both player and PA
weighting. It also beat Marcel on terminal-outcome log loss and Brier score in
2023 and 2024, although it lost both proper scores in the 2022 fold. C0 won
future-wOBA RMSE in 131 of 148 supported subgroup/view cells across the three
folds. Its recurring weak spots were players age 30+, AAA, demotions, and very
low prior evidence.

H0's added transformations caused the failure:

- Age-conditioned level translation worsened all four primary metrics in both
  views in 2023 and 2024. It added 0.000113/0.000016 player/PA wOBA RMSE in
  2023 and 0.000564/0.000485 in 2024.
- Development worsened future wOBA and runs/600 RMSE in both views in both
  fitted folds. Its 2024 wOBA RMSE costs were 0.000905 player-weighted and
  0.000710 PA-weighted.
- Calibration existed only for 2024. It modestly improved player-weighted rate
  RMSE but worsened PA-weighted wOBA RMSE by 0.002876 and runs/600 RMSE by
  1.446. It increased terminal log loss by about 0.036 in both views. The
  largest marginal damage came from FC_REACH, 3B, SF, HR, and HBP.

The correct response is not to rescue H0 or discard PBP outcomes. It is to keep
C0 and Marcel frozen, add one narrow improvement at a time, and require every
increment to prove itself on identical players and outcomes.

## Ten-step disposition

1. C0, Marcel, the folds, and all H0 artifacts remain frozen references.
2. C0-versus-Marcel wins and losses are now recorded by outcome, level, age,
   evidence, movement, strikeout band, and power band.
3. H0 was decomposed in the fixed order: reference C0, age translation,
   development, calibration.
4. The next core is a stability blend of C0 and Marcel, with one globally
   selected convex weight and no demographic, level, or identity interaction.
5. Level translation is a later, separate increment restricted to sufficiently
   supported common nested components; rare conditional branches stay at the
   core estimate.
6. Aging is a separate challenger and cannot be bundled with translation.
7. Contact direction/trajectory is a small HR/XBH residual only, never a
   replacement for terminal outcomes.
8. Tracking is another optional residual with exact PBP fallback and smooth
   reliability shrinkage.
9. Every increment uses identical-player comparisons and must improve proper
   scores and future wOBA/runs without a supported-subgroup reversal.
10. The ladder is preregistered before fitting. This checkpoint stops before
    any candidate fit or score.

## Integrity note

Two execution incidents are preserved. The first stopped before a report was
written because the wrapped C0 artifact omitted prior level. The second report
was superseded because source level labels were not normalized before lookup.
Neither incident changed the scientific question, ablation order, folds, or
boundaries. The corrected report has SHA-256
`02269c941585240decf46ec4a30e86f99236fe5ab10ee9046d2576c2a65a4f4d`.

The protected confirmation season, candidate fitting, Stage 3, and WAR remain
closed.

Validation completed with 993 tests passing and canonical lint passing across
`src`, `scripts`, and `tests`.
