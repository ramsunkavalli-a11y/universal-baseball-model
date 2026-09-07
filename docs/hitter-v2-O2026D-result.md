# O2026D: a useful first MLB opportunity benchmark

The fixed level-aware baseline improved prediction of any next-season MLB batting
PA by **10.0% in pooled Brier error** versus a baseline using only prior MLB PA
exposure. It improved in both 2023 and 2024. Retain it as a development benchmark;
it does not establish career value, individual precision, or release readiness.

## What was tested

Include prior-season-active affiliated players plus official prior MLB batters,
without requiring a future appearance or an existing batting forecast. Predict
any MLB PA, 100+ MLB PA, and total MLB PA. Train 2023 on 2022, and 2024 on 2022–2023.
The level-aware model adds primary prior league level to three prior MLB exposure
buckets, using the fixed 50-player smoothing in the [contract](hitter-v2-O2026D-contract.md).

Official MLB-wide totals exactly reconcile to summed AL/NL player PA for every
2021–2024 season. Full pagination and raw-response hashes are recorded. An absent
player in these certified batting totals receives zero MLB batting PA, not a
claim about roster membership, defensive appearances, or lifetime debut status.

| Forecast year | Cohort | Zero MLB PA | MLB batters outside cohort | Their PA |
|---|---:|---:|---:|---:|
| 2022 (training only) | 4,710 | 4,025 | 8 | 715 |
| 2023 | 4,039 | 3,395 | 12 | 2,212 |
| 2024 | 3,985 | 3,340 | 6 | 1,259 |

## Results

Lower error is better. These are player-weighted development scores.

| Pooled 2023–2024 metric | Exposure-only reference | Level-aware baseline |
|---|---:|---:|
| Any MLB PA Brier error | 0.05815 | 0.05233 |
| Any MLB PA log loss | 0.21859 | 0.17850 |
| 100+ MLB PA Brier error | 0.04317 | 0.04174 |
| Total MLB PA RMSE | 89.13 | 87.30 |
| Total MLB PA mean absolute error | 34.65 | 33.41 |

Any-PA Brier improves from .05787 to .05191 in 2023 and .05843 to .05276 in 2024.
The pooled paired player-cluster difference is -.005816, with a 95% bootstrap
interval [-.006950, -.004677] across 4,903 unique players / 8,024 player-seasons.
This interval describes this historical comparison, not prospective certainty.

Among 6,675 player-seasons with **zero MLB PA in the preceding year**, actual MLB
batting participation was 3.685%; the level-aware prediction averaged 3.804%.
Their Brier error improved from .03556 to .03264, and PA RMSE from 33.73 to 33.19.
These include possible former MLB players; this is not a pure debut cohort.
Overall participation is still underpredicted (15.36% predicted vs 16.06% actual).
Low average PA error among minor leaguers partly reflects the many zero outcomes;
it must not be presented as precise playing-time prediction for future MLB batters.

## Limits and next step

- One-year batting participation is a distinct component from batting ability.
  Do not multiply these outputs into WAR or claim the selection problem is solved.
- The cohort excludes players inactive throughout the prior season and players
  with no observed prior play. A small share of target MLB PA lies outside this
  cohort, but coverage of the full non-arriving prospect denominator is unproven.
- Pitchers who previously batted are included. The 2022 DH change is a known
  historical shift; role-aware cohorts need prior-date role information.
- Five 2022 players lacked an old ability forecast; none did in the active 2023–24
  evaluations. We therefore have no scored evidence for that subgroup.
- The initial run mistakenly used an upstream eligibility-filtered table. It is
  preserved, superseded, and explained in the [execution note](hitter-v2-O2026D-execution-note.md).
  The corrected run follows the original population contract without retuning.
- The 2022–2024 seasons remain disclosed development evidence. Protected 2026
  stays closed. Tests validate implementation, not model quality.

Next: audit the omitted participants and prior-date roster/role/age availability,
then freeze one player-specific opportunity alternative against this benchmark.
Focus on material coverage and predictive differences; no exhaustive event-level
reconciliation is needed for this task. Keep website work paused.

## Reproduction

Run `python scripts/run_mlb_opportunity.py` with the original generated 2021–2023
player-season artifact and G0 prediction files present. The script fetches only
declared completed seasons; saved official responses can be reused. It refuses
to overwrite a completed output directory. New tests cover incomplete sources,
traded players, cohort membership and chronology. Full machine-readable
[results](hitter-v2-O2026D-result.json) include sources, hashes, learned parameters,
subgroup scores and calibration bins. External source data remains uncommitted.
