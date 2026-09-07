# Tango-focused production-model work

Updated 2026-09-06. The main modeling priority is KATOH-like future production for
hitters and pitchers. Cost/control data is a downstream layer, not the current
research bottleneck. Website work remains paused.

## Completed: diagnostic of the saved batting translation

Ran `scripts/audit_tango_translation.py` on saved 2022–2024 forecasts. No fitting,
new calibration, candidate selection, or protected 2026 outcomes. Input hashes
are in [the machine-readable result](hitter-v2-tango-translation-audit.json).

Following Tango's evaluation example, compare PA-weighted absolute error after
removing each model's mean error over the SAME full evaluated MLB cohort. Keep
raw errors beside these scores. Centering uses evaluation outcomes and is ONLY
a scoring diagnostic; it must never be deployed as a forecast correction.
[Tango's evaluation](https://www.insidethebook.com/ee/index.php/site/article/testing_the_2007_2010_forecasting_systems_official_results/).

| Prior-minor MLB participants | G0 centered MAE | Translation centered MAE | Adapted Marcel centered MAE |
|---|---:|---:|---:|
| 2022, 302 players | .04003 | .03624 | .04322 |
| 2023, 279 players | .03930 | .03294 | .04259 |
| 2024, 279 players | .04099 | .03312 | .04141 |

The improvement survives common-cohort centering. It is therefore not exclusively
an overall MLB mean correction. Among players with no recorded MLB history in the
available window, translation also improves centered MAE in every year, although
2022 is nearly flat (.03898 to .03835). This is not proof of no lifetime MLB history.

Among prior-minor players without any historical same-season pair meeting the
translation's 50-PA-per-level threshold, MAE changes from .04137 to .03783 in
2022 (104 players), .04334 to .03482 in 2023 (57), and .04653 to .03594 in 2024
(35, below the declared 50-player support threshold). Benefits are not confined
to the players whose own history supplies qualifying translation contrasts.

These remain overlapping descriptive subgroups, not independent confirmation.
They still condition on subsequent MLB participation and available model-ready
batting outcomes. No result proves universal prospect transport. Tango explicitly
warns that promoted/staying players are selected, that aging can contaminate
translation, and that regression populations matter.
[Tango on MLEs](https://www.tangotiger.net/hateMLEs.html).

**Decision:** keep T2026B's MLB-conditional component as a developmental building
block, keep its failed all-level decision, and stop output-calibration searches.
Neither this new MAE diagnostic nor the earlier RMSE gain is career-value accuracy.
The repo's baseline is Marcel-inspired: it uses affiliated history and a coherent
terminal-outcome adaptation. Do not label comparisons as beating original Marcel.

## Completed: identify the older opportunity model worth recovering

**Subsequent update:** the original 2024 scored artifact was found in an older
centering-inputs archive and verified. The identical-target comparison is now
[complete](recovered-opportunity-comparison.md). The initial inventory below is
retained to explain why recovery was prioritized; its missing-file limitation is
resolved for the 2024 scored surface, not the entire feature pipeline.

The existing `playing_time_model.py` already implements participation and positive
PA distributions with age, prior MLB/MiLB PA, dated 40-man membership and optional
B2 features. The old selected model's published results are:

| Development year | Old model Brier | Old model PA RMSE | O2026D Brier | O2026D PA RMSE |
|---|---:|---:|---:|---:|
| 2023 | .04776 | 79.20 | .05191 | 88.64 |
| 2024 | .04610 | 75.20 | .05276 | 85.92 |

This is an inventory comparison, NOT a new head-to-head test. The 2023 populations
differ (4,040 vs 4,039); identical 2024 row counts do not prove identical IDs and
targets. Timing, features and fitting protocols also differ. Nevertheless, the
older results provide a strong reason to recover that model before inventing
another challenger. Its B2-dependent features cannot be assumed sound just because
the opportunity model previously passed development.

Sources: `playing-time-v1-validation-2023-result.json`,
`playing-time-v1-validation-2024-result.json`, and `hitter-v2-O2026D-result.json`.
The earlier generic roster audit failed; use the later dedicated
`playing-time-historical-40man-membership-result.json` and membership-only adapter,
not diagnostic row status as a historical injury/role feature.

The old scored parquets were not present in the two inspected local generated-data
directories, so a row-level comparison was not fabricated. The 2024 candidate
artifact is recorded as
`reports/generated/playing-time-v1-validation-2024/tables/candidate_2024_scored.parquet`,
SHA-256 `9896560f41a738f85d928c973f6e55f6a5a9cf64afe8dc58d2403879a92e3e28`.
Recover/reproduce the dated feature and forecast artifacts, join by player/year,
verify targets against O2026D official totals, then compare unchanged models.
If reconstruction is necessary, preserve the original declared model and clearly
label reconstructed forecasts. Do not silently retrain a new candidate.

## Completed: identify the career-data boundary

Existing historical audit evidence identifies promising 2017 and 2019 MiLB
sources, but 2018 lower-level coverage is incomplete. The G0 materialized history
already includes 2019 and MLB 2020; no affiliated MiLB season existed in 2020.
The old source-audit document predates that materialization and must not be read
as current evidence that 2019 remains unavailable.

For career modeling, distinguish three assets: prior playing evidence, complete
future MLB participation/production, and dated player/roster membership. None
substitutes for the others. With outcomes ending in 2024, a 2018 cutoff has six
following calendar seasons; this is not six MLB seasons or six service years.
Later debutants and still-controlled players have censored career outcomes.
We do not yet have a certified mature first-six-MLB-season dataset for everyone.

**Next source task:** inventory aggregate season batting and pitching histories
and complete MLB outcome coverage for older cohorts. Start with season totals
for career labels; full pitch-by-pitch backfill is unnecessary for that purpose.
Missing future data is unknown, not failure. Track incomplete leagues explicitly.
No protected 2026 collection or new bulk backfill occurred in this work.

## Execution priorities

1. Recover/reproduce the old opportunity surfaces and test on identical repaired
   targets; retain O2026D as the simple reference. Reuse dated roster and age inputs.
2. Build an older-cohort, year-by-year outcome inventory for both hitters and
   pitchers, with non-arrivals, return from inactivity and censoring explicit.
3. Fit one simple pitcher component baseline using existing K/UBB/HBP/HR/BF
   sources; assess rate accuracy separately from role and workload. Do not copy
   a hitter aging curve. Tango's pitcher analysis specifically demonstrates
   selection and regression problems in naive adjacent-season aging.
   [Pitcher forecasting](https://www.tangotiger.net/adjacentPitching.html).
4. Predeclare a bounded career-production baseline once label coverage is known.
   Evaluate future MLB contribution and uncertainty, including zero outcomes,
   with separate views by level, age, role and prior evidence. Preserve component
   checks, but do not make tiny event-score gains the whole project's objective.

Do not revise old failed contracts or impose new gates retrospectively. Every
additional experiment needs a concrete predictive question and a defined end.
