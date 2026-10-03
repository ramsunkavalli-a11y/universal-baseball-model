# Practical hitter rebuild: completed V30–V32 checkpoint

2026-10-02. **Subsequent qualification:** the training expansion accidentally
included 597 incomplete origin-2020 rows contrary to the contract, with missing
roster coverage encoded as non-listing. Preserve the reproduced results below,
but do not adopt the gains or reject the designs from them. See
[the source/training repair](practical-hitter-v33b-training-repair.md); V33b
refits both candidates and a matched direct control before new conclusions.

The broad rebuild's reported scores improve playing-time prediction against the
recent V24 model, but it is not yet a better complete hitter forecast. Keep the
stronger older batting/value approach while testing missing representation.

## What changed

Rebuilt the broad historical population from dated, reconciled source stints:
30,506 forecasts across seven cutoffs, including minor leaguers, exits and older
MLB players. Separated Mexican League from affiliated AAA and DSL from other
rookie leagues. Corrected 9,396 source rows whose career MLB PA omitted secondary
stints. Preserved all 4,396 V24 comparison identities and all non-arrivals.

Six fixed workload families were tested in V30; switching boosted libraries
did not materially help. V30b repaired a near-constant environment variable
that caused linear extrapolation, not a general failure of linear regression.
V31 then compared simple staged, detailed staged and direct broad models, plus
conditional batting-rate diagnostics. V32 tested improved PA × preserved older
contribution yield without refitting or selecting weights.

## Exact comparisons

| Same players / measure | V24 | Broad simple | Broad detailed | Steamer |
|---|---:|---:|---:|---:|
| 4,396 rows: PA RMSE | 128.62 | 125.87 | 126.07 | — |
| 1,789 public-matched rows: PA RMSE | 149.12 | 146.34 | 145.23 | 135.02 |
| Public-matched PA MAE | 116.01 | 113.65 | 113.18 | 92.40 |
| 4,396 rows: batting + replacement RMSE | 0.91725 | 0.92606 | 0.92701 | — |

The detailed PA gain versus V24 is supported by a nominal player-clustered
paired MSE interval, −1,012 to −271 PA-squared. But combined contribution worsens.
Keeping V24's yield with new PA recovers contribution RMSE to about 0.9141;
the small gain's interval includes no improvement. It does not beat the stronger
older N reference: N's 21,819-row value RMSE is 0.44582 versus 0.44853 for the
detailed reconnection. New population rows cannot dilute the fixed comparisons.

Public conversion uses forecast-origin environment whereas targets use realized
environment; converted Steamer contribution has a substantial mean offset.
Archives are not certified identical-information December snapshots. A lower
converted contribution error is not a claim that UBM predicts talent better.
The PA MAE gap still exceeds the practical plan's tolerance.

## Baseball checks that matter

- Steer gains useful opportunity from his upper-minor performance, but 265
  expected PA remains far below 665 actual. Failed comparable players stay shown.
- Olson's 24 MLB HR plus 23 AAA HR are present, yet detail lowers expected PA
  from the simple model's 463 to 311. Adding detail is not automatically useful.
- Tatis's finite suspension and McLain's full missed season are poorly represented
  by ordinary absence and a zero captured roster listing. Listing is not rights.
- Kurtz's 50 professional PA provide too little context without his existing
  draft evidence. A nearly zero next-year forecast misses 489 PA and 5.72 value.
- Eldridge/Made/De Vries have different arrival horizons. Low next-year MLB PA
  does not establish low six-year prospect or trade value.
- A rare-league standardized ridge diagnostic predicts physically absurd rates;
  this is unsupported feature geometry, not a usable talent grade.
- The broad 2021 cutoff still underprojects next-year league PA by roughly
  18,700 in detail. Canceled-MiLB flags alone cannot learn a first-ever event.
  No held-out-total rescaling was used to conceal it.

Pre-DH hitter-cohort batting-plus-replacement totals can exceed 570 because
negative pitcher batting sits outside that cohort. Source-rebuilt targets
reconcile; forcing every hitter cohort to 570 would introduce a different error.

## Review, artifacts and next action

V31: 700 saved heads replayed, sources/targets independently reconciled, 27
complete player walkthroughs. V32: every assembly arithmetic replayed, identical
membership/targets, 20 complete walkthroughs. Completed review is not predictive
certification or deployment approval. Contracts and original outputs preserved.

Local generated evidence: `reports/generated/practical-hitter-v31/` and
`reports/generated/practical-hitter-v32/`; each has `player-walkthrough.md`,
machine-readable cases, scores and provenance. These generated/source artifacts
remain local, not committed private exports. Historical team-filtered explorer:
`reports/generated/practical-hitter-v31/explorer/index.html`, served locally on
port 8782. It shows earlier forecasts versus actual 2017–25 results, not 2026.

Next follows [the fixed V33 contract](practical-hitter-v33-contract.md): pooled
count evidence, existing cutoff-known draft pedigree, and a safely scaled linear
diagnostic. Keep broad direct contribution and weighted-rate products separate.
No more library tournament, manual star boosts or frozen forecast overwrite.
Temporary-absence semantics, medical/foreign context, park/opponent inputs and
late-season jobs remain explicit gaps; V33 does not claim to repair them all.
