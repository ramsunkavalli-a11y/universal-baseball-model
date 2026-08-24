# Hitter v2 Stage 2 final-validation checkpoint

Recorded: 2026-08-24

## Scientific outcome

Neither pre-registered PBP-only candidate passed the disclosed 2022-2024
promotion gate. Hitter v2 therefore stops at Stage 2. No candidate is promoted,
and tracking fusion, protected 2026 confirmation, baserunning, defense, playing
time, and WAR remain closed.

The scorer and every candidate parameter were frozen and committed before the
one-pass run. Scoring ran from commit
`7c066b8816739e4dc58b39329fa2d678ad766fc3` with:

```text
.venv\Scripts\python.exe scripts/score_hitter_v2_stage2_final_validation.py
```

The ignored full report is bound by SHA-256
`4695d9a7c6b13b67271c52f1bcd2efaf195d64bc423a4c39e7c72934fb8150c9`
and is summarized in `docs/hitter-v2-stage2-final-validation-result.json`.
Completed 2026 hitter outcomes were not opened.

After recording the result, Ruff passed and the complete test suite passed all
869 tests in 9.42 seconds.

## Candidate C0 — nested empirical Bayes

C0 showed a real but insufficient pooled future-rate improvement. In the
PA-weighted view, wOBA MAE improved 1.1487% and RMSE improved 1.1682% over the
strongest simple rate baseline. The paired player bootstrap also favored C0:
the candidate-minus-baseline wOBA RMSE delta was `-0.0003918`, with a 90%
interval of `[-0.0005171, -0.0002680]`.

That evidence did not satisfy the full gate:

- V2022 did not strictly beat the strongest baseline in either weighting view;
- pooled terminal Brier score was worse than B1 Marcel;
- pooled terminal log-loss improvement was only 0.0435%, below the frozen
  0.25% requirement;
- player-weighted wOBA/runs RMSE improved only 0.6523%, below the frozen 1%
  requirement;
- calibration failed in all three folds; and
- supported-subgroup reversals failed in V2022 and V2023.

C0 remains a documented failed challenger. Its favorable rate evidence does not
permit relaxing the proper-score, calibration, fold, or subgroup requirements
after observing validation.

## Candidate C1 — hierarchical PBP enrichment

C1 failed decisively. Against the strongest simple baseline, its pooled
PA-weighted wOBA MAE and RMSE were worse by 15.37% and 14.94%; player-weighted
MAE and RMSE were worse by 9.13% and 5.52%. Proper event scores also worsened.
The paired bootstrap put the candidate-minus-baseline wOBA RMSE delta at
`+0.0033148`, with a 90% interval of `[+0.0027129, +0.0039205]`.

C1 failed per-fold primary performance, pooled relative improvement,
correlation, calibration, bootstrap, and supported-subgroup gates. It remains a
documented failure and will not be rescued by tuning on these disclosed results.

## Interpretation and boundary

The result suggests that the basic nested component representation has useful
future-rate signal, but the frozen shrinkage choices do not improve the full
terminal probability distribution enough and remain poorly calibrated across
levels and seasons. The selected C1 environment, movement, age, and GIDP
adjustments substantially degraded generalization.

The only currently authorized next gate is review of this failed result. A new
candidate would require a new, versioned development contract with a genuinely
independent future evaluation boundary before fitting or scoring. This result
does not authorize 2026 access, tracking fusion, Stage 3, or WAR.
