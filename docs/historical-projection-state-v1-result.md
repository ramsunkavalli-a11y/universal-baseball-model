# Historical forecast archive rebuilt

2026-09-23. **Input-building milestone, not a model upgrade.** Live forecasts and the explorer are unchanged.

## What changed

Reconstructed 2012–2015: **53,910 player/year/horizon forecasts**, covering Years 1–3.
Combined archive: **145,344 records** across 11 starting seasons, through the 2025 cutoff.
Each record separates MLB participation, playing time conditional on participation,
research hitting-rate estimates, and delivered batting/replacement value. These are not full WAR.
Older models were refitted using labels available at the time, not today’s fitted coefficients.
These are reconstructed forecasts under current fixed recipes, not forecasts published in those years.

## Verification

- Reproduced 2016 and 2022 opportunity/conditional-head forecasts at all three horizons.
- Reproduced independently fitted H1 rate anchors at both overlaps and all four backfill origins.
- Early raw mean values match the existing archive; later rich mean values are reused, not refitted.
- Changing future labels and future predictors left the tested 2016 H3 pipeline and H1 rate anchor unchanged.
- Full starting populations retained; forecasts have unique keys, cutoff checks and no missing prediction fields.
- Zero playing time produces an unknown observed hitting rate, not zero talent. Future outcomes stay missing.

## Usable three-year history

A complete forecast/error vector must have finished before the next model is fit. Pandemic-crossing
paths are excluded. Counts below are starting-year snapshots, with repeated players identified explicitly.

| Model cutoff | Previous matched snapshots | Rebuilt snapshots | Distinct players | Young brief-MLB snapshots / players |
|---|---:|---:|---:|---:|
| 2012 | 0 | 0 | 0 | 0 / 0 |
| 2013 | 0 | 0 | 0 | 0 / 0 |
| 2014 | 0 | 0 | 0 | 0 / 0 |
| 2015 | 0 | 4,466 | 4,466 | 17 / 17 |
| 2016 | 0 | 8,942 | 5,428 | 46 / 42 |
| 2019 | 4,572 | 22,542 | 8,263 | 128 / 112 |
| 2021 | 4,572 | 22,542 | 8,263 | 128 / 112 |
| 2022 | 4,572 | 22,542 | 8,263 | 128 / 112 |
| 2025 | 12,891 | 30,861 | 12,048 | 196 / 175 |

Every identity has total weight one across its eligible snapshots. A subset’s effective support can
be smaller than its distinct-player count. The packaged audit includes age/stage cells, never-debuted
players, recent debuts, minor-league returners and effective support. Query diagnostics exclude every
snapshot of the query player itself; they do not select a new matching/fallback rule.
Sparse cells remain: 25 of the 4,572 queries at 2016 and one of the 3,907 at 2025 have fewer
than the previous 21-identity rule in their same-age/stage pool after self-exclusion. A future
architecture must declare its broader fallback; these rows cannot be silently dropped.

## What this does—and does not—enable

The missing matched-history problem at the 2016 outer fold is repaired. A three-year anchored-path
experiment can now be specified against dated forecast errors. That is permission to design a test,
not evidence that a particular joint model works or that rare prospect upside is sufficiently supported.
No new accuracy claim is made here; the previous population-only path model remains rejected.

There is still no mature reconstructed three-year error history at 2012–2014 cutoffs. The first is
2015 (one starting season); the 2016 cutoff has only two. Early anchors have less detailed features
than modern forecasts. A residual from an older fallback is not automatically portable to a modern stack.
Whole-vector residuals contain realized variation and selection, not separately measured development
or pure talent. Do not add another independent season-noise layer to them without identifying what
has already been included. Six-year states and full remaining-control dollar values remain incomplete.

## Next bounded step

Freeze one three-year path specification: how projected ability and playing opportunities interact,
what uncertainty persists between years, what developmental changes are supported, and how sparse
states borrow strength. Compare with the delivered mean and the existing distribution controls on
the same players. Preserve prospect-success checks, player exclusions, pandemic separation and
Monte Carlo stability rules. Do not improve apparent results with an after-the-fact blend or FV floor.

## Reproduce

```powershell
.venv/Scripts/python.exe -X utf8 scripts/build_historical_projection_state_v1.py
.venv/Scripts/python.exe -X utf8 scripts/audit_historical_projection_state_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_historical_projection_state_v1.py
```

The original pre-fit contract is saved in the package. Do not overwrite/refreeze it after fitting.
