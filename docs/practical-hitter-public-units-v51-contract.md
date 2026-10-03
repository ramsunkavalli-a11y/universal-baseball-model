# Compare hitting forecasts with the same event units

2026-10-03, before scoring. The reliability player review is complete. This is
a no-fit source and evaluation repair within the talent milestone, not a new
algorithm or hindsight calibration.

The old public comparison subtracts the origin MLB scoring environment from
public event counts, but actual talent labels subtract the realized target
environment. That mismatch adds a common environment offset to public errors.
It also obscures what the UBM relative-rate forecast implies for actual events.
Preserve all old scores and show both versions, never retroactively recenter a
forecast on the future observed league average.

Compare a fixed-weight event index: (0.6926 UBB + 0.7222 HBP + 0.8776 singles +
1.2352 doubles + 1.5572 triples + 1.989 HR) / total PA. It is NOT official
FanGraphs wOBA: denominator, fixed weights, park adjustments and publication
date can differ. UBM's implied index is origin league index plus its predicted
relative batting rate × fixed wOBA scale × 10 / 600. Public index is directly
reconstructed from verified raw projected counts. Actual index is directly
reconstructed from mature future MLB counts. Add a common origin-centered wins
version for readable units; this cannot change errors differently by system.

Use all unchanged V50 historical identities with targets 2022–25. Report both
the exact 1,789 legacy-public current-MLB matches and broader common public
matches, with missingness and actual PA excluded from the *conditional rate*
score explicitly listed. Preserve zeros in delivered offense and workload.
Plain ZiPS conditional PA are not a workload prediction. Only Steamer PA are
scored. Exact preseason archive days remain unknown. Older-player expansion
is coverage, not independent fresh validation.

Primary rate loss: actual-PA-weighted MSE within equal target years on common
positive-actual-PA membership. Secondary MAE/bias, every year, current workload
bands and elapsed 6+ players. Score UBM working, binary readiness plus existing
rate, fixed/adaptive reliability, Steamer and ZiPS. Native delivered offense is
expected PA × ((forecast index - origin league index)/(fixed scale×10) + origin
replacement rate), against actual PA × ((actual index - origin league index)/
(fixed scale×10) + origin replacement rate). This is an event-consistent
offense diagnostic, NOT full WAR and NOT park-neutral talent or surplus value.

Verify public IDs, hit/PA sums and unchanged source hashes, actual count/rate
reconciliation, implied UBM conversion and no future information in forecasts.
No new fitted models, sampling changes, outcome-dependent calibration or 2026
files. Raw exports remain private. Before disposition trace fixed Judge 2024,
Winn 2023, Steer 2022 and Alvarez 2024, plus largest meaningful PA-weighted
relative rate gain/harm, false high/low contribution, ordinary case and at
least one elapsed 6+ player. Select peers by origin age, workload and elapsed,
not future success. Report exact source counts, environments, forecasts and
outcomes. This repair cannot settle missing park/physical talent or claim the
whole system is better than established public projections.
