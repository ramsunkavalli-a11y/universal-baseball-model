# Hitter health-state and league-budget checkpoint

Frozen 2026-09-22 before new fits. No 2026 outcomes, current forecast changes,
team/job forecasts or automatic rescaling. Earlier broad injury counts and residual
corrections failed; this is a narrow reported-state/cutoff repair, not a claim that
we have diagnoses or medical recovery observations.

## Source and state

Reuse saved 2015–2023 transaction and regular-season schedule captures. Treat the
latest valid transaction/effective/resolution date as the earliest eligible date;
never move a cross-year effective date back into its capture year. Historical
captures are reconstructed, not archived publication vintages. Exclude non-MLB
team transactions using MLB team IDs in the corresponding schedule. Distinguish
in-season activation from offseason roster reinstatement; neither proves medical
recovery. Do not infer diagnoses from inconsistent free text.

Features at December 31: MLB observation scope (positive MLB PA in either of the
last two calendar years), log IL days in the last 730 days, open IL spell at cutoff,
log elapsed days in that open spell, offseason activation during the cutoff year,
and in-season activation in the final 90 days of that season. Unobserved minor
league injury history is unknown, not healthy. State fields are masked outside MLB
observation scope; zero within scope means no recorded evidence, not certified health.
Keep open spells until an observed activation; don't assume January 1 cures injury.

Audit date disagreement, cross-year deferrals, event support by year, missing
coverage and orphan activations. Preserve existing parsers/artifacts; use a separate
conservative reconstruction. Reject future-only information in mutation tests.

## Fixed conditional-PA test

Use the existing 77 aggregate features plus four anchored-performance features.
Hold the previous challenger's participation probability and carry-forward rate
fixed; this isolates conditional PA, not the delivered model's direct value mean.
Training origins start in 2016 to provide two prior years of injury capture. Train
only origin+2<=cutoff active-label rows. Test origins 2019, 2021, 2022, 2023; the
first has two mature training origins. Show actual target-2021 separately from the
three ordinary forecast windows. No model tuning or subgroup-based selection.

Three fixed forms, standardized/imputed Poisson alpha=1, max_iter=2000, clipped
conditional PA 1–750 (record counts):

- R: calendar PA, no new health fields;
- E: PA divided by the historical target's certified schedule fraction, weighted
  by that fraction, no health fields;
- H: identical exposure treatment plus the six health-state fields.

The exposure-weighted rate loss has the same coefficient-dependent Poisson terms
as a count model with a known exposure offset. Target-year exposure is used only
for already-mature training labels. Future predictions assume an ordinary schedule;
no realized future exposure is supplied. Observed labels remain actual calendar PA.
Do not promote a hindsight-scaled forecast. Brier/log loss remain identical by design.

Primary health comparison H versus E: ordinary-window paired player-cluster 95%
MSE interval favorable, MAE not worse, majority of three origins improve, and the
same MSE/MAE tests for supported recorded-IL-history players (>=100 rows, >=2 origins).
Fixed-rate value MSE must not worsen >1% overall or >5% in supported baseline-defined
stage/age/top-50 groups. Across all four origins neither PA nor fixed-rate value MSE
may worsen >5%. R versus E is a separately reported exposure diagnostic, not a way
to substitute a different winning model if health fails. Unsupported groups are
descriptive. All exposed folds remain development evidence.

Even a pass is only eligibility for further validation: this batch cannot deliver
new current forecasts without current health coverage and a coherent value comparison.

## League accounting, not forced accuracy

Audit current 2026–2028 PA and batting-plus-replacement means against a league PA
budget estimated from the latest three completed ordinary seasons available at
the cutoff, and the label system's normal-season 570 batting-plus-replacement budget.
Show unallocated PA and any excess explicitly. The difference in value is signed
and can reflect outsiders AND model calibration; never call all of it future talent.

For each historical test cohort, compare actual PA/value captured by its players
to the complete target-season table and record actual outsiders' signed contribution.
This checks how much opportunity belongs to future entrants or omitted players.
Check actual league PA equals pitching BF where the certified source supports it.
Full WAR cannot be reconciled from this partial-value target; state that limitation.
Do not transfer injury-lost PA or WAR arbitrarily among the named players, and do
not normalize predictions to 570 to claim improved forecasting.

Save source hashes, feature/support audits, predictions, paired results and budget
ledgers. Test date safety, ordering, unknown health scope, exposure maturity,
no-play handling, residual identities, and original forecast hashes. Update notes
and commit the completed evidence; preserve the frozen forecasts and explorer.
