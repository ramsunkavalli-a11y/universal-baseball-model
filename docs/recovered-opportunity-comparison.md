# Recovered opportunity model: identical-target comparison

Completed 2026-09-06. No refit, new candidate, or protected 2026 outcomes.

Recovered the original 2024 selected-model forecast from an older local project
folder. SHA-256 exactly matches the committed validation record:
`9896560f41a738f85d928c973f6e55f6a5a9cf64afe8dc58d2403879a92e3e28`.
The earlier search in two generated directories had missed this copy in a
centering-inputs archive. Original source files were not modified.

## What is now verified

- All 3,985 player IDs match O2026D exactly.
- Every original observed PA total matches the newly certified O2026D labels.
- Original participation and expected-PA arithmetic reconcile.
- Published old-model Brier and PA RMSE reproduce to numerical precision.
- Comparison uses the original saved forecasts; no reconstructed or retuned model.

| 2024 metric (lower is better) | O2026D level baseline | Recovered model |
|---|---:|---:|
| Participation Brier | .05276 | .04610 |
| Participation log loss | .17818 | .15545 |
| MLB PA RMSE | 85.92 | 75.20 |
| MLB PA mean absolute error | 32.68 | 27.86 |

The old model reduces participation Brier by 12.6% and PA RMSE by 12.5% on this
same population. Both broad groups, with and without prior-year MLB PA, improve
on these error measures. However, Rookie and Single-A origin groups have worse
Brier and PA RMSE; do not claim uniform superiority or splice models by subgroup
after observing these results. Rookie players' near-zero next-year participation
also illustrates why a one-year opportunity score cannot rank long-term upside.

The old model underpredicts participation more for the dominant-MLB-origin group,
despite its lower Brier error. Calibration and discrimination are distinct.
All subgroup scores and a paired 1,000-draw player bootstrap are preserved in
[the result](recovered-opportunity-comparison.json).

## Decision and next work

Use the recovered model as the leading existing opportunity candidate for further
integration research. Retain O2026D as the transparent simple benchmark. This is
one disclosed historical year, not a new release gate or independent confirmation.
The original systems had different fitting/selection histories, and the old
model's B2-dependent inputs still need an explicit reuse/replacement decision.

Next recover the model's dated feature/parameter pipeline and isolate its B2
dependency before replacing features or fitting alternatives. Extend evaluation
to sparse/inactive players with a declared coverage policy. Continue the older
career-outcome inventory and pitcher baseline alongside that integration work;
do not start another global batting-calibration search.

Reproduction: `python scripts/compare_recovered_opportunity.py`. Required local
artifacts are named in that script, source hashes are recorded, and completed
results cannot be overwritten. Identity, target, probability, expected-PA and
score-reproduction checks passed; lint passed. No raw player data was committed.
