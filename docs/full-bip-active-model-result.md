# Full BIP active-model comparison

**Status:** pitcher advances; hitter remains research-only

## Fair comparison

The first attempted active-model comparison was rejected before use because it mixed
MLB-translated predictions with raw minor-league outcomes. The corrected replay puts
all three quantities on the same MLB-neutral contact scale:

1. the active three-season, level-translated component estimate;
2. the full ten-bin BIP estimate, with each bin's earlier outcome mix translated to
   MLB; and
3. the next-season contact target, translated with only offsets available at the
   forecast cutoff.

The contact environment is estimated from the batting side of the same official
events, which supplies singles, doubles and triples that the aggregate pitching table
does not retain. Batter and pitcher rows describe the same contact outcomes; this is
not an outside rating or an offensive prior imposed on pitchers.

Home-run value is zero in this layer because the active model already forecasts home
runs separately. One incremental weight was learned on 2021 predicting 2022 and
frozen before 2022 predicted 2023. Public rankings, names, positions and demographics
were not inputs.

## Results

| Player type | Frozen weight | Confirmation players | Baseline MAE | Blend MAE | Baseline RMSE | Blend RMSE | Level gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Pitcher | 0.7883 | 2,512 | 0.04845 | 0.03236 | 0.05983 | 0.04131 | pass |
| Hitter | 0.7310 | 2,249 | 0.03860 | 0.03163 | 0.04891 | 0.04017 | fail |

Pitchers improve on player- and contact-weighted MAE and RMSE at A, High-A, AA, AAA
and Rookie. The active pitcher model currently treats nearly all non-HR contact as
one population-average outcome, so the complete contact shape fills a clear structural
gap.

Hitters improve overall, but AA and AAA reverse on both equal-player errors. Much of
the aggregate gain comes from Rookie-level players. That fails the predeclared
no-level-reversal rule and is not rescued by the strong overall score.

## Decision

- Advance the pitcher weight to a full pitcher-rate replay. That
  [replay is now complete](full-bip-pitcher-rate-replay-result.md) and fails, so the
  adjustment does not enter current-player values.
- Keep hitter production weight at zero. Next diagnose why the candidate helps Rookie
  and lower levels but loses at AA/AAA; do not tune to individual prospects or public
  FV.
- Preserve the rejected mixed-scale outputs only as generated debugging evidence.
  They do not support a model decision.
