# Multi-year plan review: decisions

Reviewed 2026-09-22. Implemented in [plan v1.1](multiyear-player-value-plan-2026-09-22.md).
This is a planning revision and read-only source inspection, not a new model result.

| Weakness in v1.0 | Change |
|---|---|
| Usable explorer delayed until M7 | Deliver Year 1–3 and their sum at M2, including the retained baseline if challengers fail |
| Six model families and open-ended tuning | Three fixed annual challenger forms and one direct cumulative diagnostic; no parameter/feature sweep in first batch |
| Blanket horizon embargo | Exact cutoff and availability per learned target; recent one-year transitions need not wait six years |
| Unclear winner/reference/weights | Fixed B0, common Year 1, equal outer-origin three-year MSE, inner-only selection, explicit stronger-benchmark check |
| Thin support could invite repeated tuning | Minimum support and a fixed-form exploratory fallback; bounded source recovery and one justified follow-up after failure |
| Direct opportunity work not explicitly reused | Reuse existing horizons 2–4 sources/builders and verify stored packages |
| Uncertainty effectively depended on simulation | Earlier-residual annual/cumulative marginal intervals allowed; joint path claims deferred |
| Whole-WAR scope left too late | Target/source reconciliation begins M1; first report names missing components and external comparison status |
| 2020 handling was prose only | Existing target accounting identified as a concrete M1 blocker for calendar-value labels |

## Source evidence for the 2020 issue

`build_neutral_mlb_value_targets` in `src/universal_baseball/hitter_value_panel.py`
sets replacement runs per 600 PA from a fixed 570-WAR league allocation divided by
that year's PA. The pitcher equivalent in `pitcher_value_panel.py` uses 430 WAR.
Consequently summing each annual target across MLB players preserves the full pool
even for a shortened season.

Read-only sums of the already materialized target tables, rounded to whole wins:

| Outcome season | Hitter component WAR | Pitcher component WAR |
|---|---:|---:|
| 2019 | 570 | 430 |
| 2020 | 570 | 430 |
| 2021 | 570 | 430 |

Inputs are the `hitter-value-targets.parquet` and `pitcher-value-targets.parquet` tables
under the respective `reports/generated/*-value-panel-v2/tables` directories. Their
hashes are recorded in the [existing availability audit](multiyear-horizon-support-2026-09-22.json).
Only 2019–2021 summary totals were inspected here; protected 2026 outcomes were not read.

The one-year panels excluded 2019-to-2020 and 2020-to-2021, so this finding does not
by itself invalidate their reported comparisons. It matters when cumulative windows
include 2020. M1 must version and reconcile the target before using those windows;
this review does not rewrite historical results or claim a measured model improvement.
