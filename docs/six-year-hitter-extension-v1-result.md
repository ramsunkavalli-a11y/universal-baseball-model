# Six-year hitter extension

2026-09-22. **Delivered: six calendar years of development forecasts. Not yet
delivered: value over every player's remaining six-year MLB service clock.**

Explorer: <http://127.0.0.1:8776/>. The previous three-year view remains on 8775.

## What changed

All 3,907 hitters now have annual 2026–2031 batting/replacement and playing-time
forecasts, plus a separate provisional position/running/defense scenario. The
team filter, minor-league stages, annual sorting, six-season totals, component
breakdown and zero-framing sensitivity work across all six seasons. Batting-only
is the default. Every earlier forecast column is unchanged, not merely rounded
to the same display value. The original 31-file frozen 2026 package still verifies.

Years 4–6 are separately fitted future-year Ridge models using the existing
ordinary batting, age, level and three-year workload/performance history. They
are not repeats of Year 3 and do not assume prospects remain in their current
league. Future labels measure actual MLB production, including zero for players
who never get there. The existing all-level PA hurdle is separately refitted.
This extension does not adopt the failed three-year PA challenger.

## What the tests say

Equal-origin annual batting/replacement RMSE, same starting players and targets:

| Future year | Age/level/workload | Repeat Year-3 forecast | Richer direct forecast |
|---|---:|---:|---:|
| 4 | 0.5743 | 0.5470 | 0.5385 |
| 5 | 0.5501 | 0.5502 | 0.5248 |
| 6 | 0.5682 | 0.5742 | 0.5417 |

The richer model improves on the simpler model in 6/7, 4/5 and 4/4 origins.
Year-4 pandemic-free RMSE improves 0.6166 → 0.5790 over three origins.
**Years 5–6 have no pandemic-free full-path outer test.** Their endpoints can be
normal seasons, but the player paths cross 2020. No 2020 calendar output is
inflated. Training excludes pandemic-crossing paths; no outcomes beyond 2025
enter fitting or scoring.

Six-calendar-year batting/replacement RMSE improves **2.2517 → 2.1789** over
18,252 player-origin paths from 2016–2019. The earlier three predictions are
identical in both alternatives. Player-cluster bootstrap MSE difference:
−0.3227, interval [−0.4729, −0.1784]. This interval does not account for common
season shocks or turn overlapping origins into independent confirmation.

Player-disjoint sensitivity still favors the richer model, but by less:
RMSE 0.6080 → 0.5863 / 0.5773 → 0.5670 / 0.5981 → 0.5928.
Most gains come from current MLB hitters. Upper-minors RMSE improves roughly
1.3% at each long horizon; lower-minors gains are small. Inactive/unknown players
worsen roughly 1–2%. This is not a solution to the previously identified
prospect-arrival underprediction.

The fixed long-horizon component benchmarks add modest improvement. Holding
Years 1–3's integrated forecasts fixed, adding Years 4–6 components changes
six-year expanded-target RMSE **2.1922 → 2.1816**. Only 13,641 complete paths
from 2017–2019 qualify: missing blocking coverage excludes 2016, and missing
active-player measurements are not zero-filled. All three paths cross 2020.
The larger 2.2821 → 2.1816 comparison adds components in all six years and must
not be described as the benefit of this turn's long-horizon additions alone.

## Why the control objective is still open

For a zero-service prospect, six consecutive full MLB seasons beginning in 2029
end in 2034—not 2031. A partial first season can push eligibility later still.
For an established player, the opening service already earned must count.
Injured MLB players can accrue service without PA. Statutory eligibility is not
the same as current-team retention or a guaranteed contract term.

The new tested accounting layer handles delayed arrival, partial service,
zero-output injury years, already-eligible veterans, whole final seasons, missing
opening balances and unresolved tails. It accounts a supplied path; it does
**not** pretend to forecast that path. Incomplete control totals remain null.

Local display-only service evidence resolves 2,825 players and leaves 1,082
unknown; 126 are already past the statutory six-year threshold. These are
retrospective opening-2026 balances/no-prior-debut evidence, not certified
contemporaneous Dec-31 captures. Only identity, opening balance, baseline status
and debut date are read from the existing control container. Current 2026
service increments, performance, organization and payroll fields are excluded.
Private individual control annotations remain local and are not copied into
the committed forecast package.

The older workload-to-service mapping is not promoted. Its cumulative endpoint
error, zero-workload injury treatment and missing-next-tracker selection remain
material. Stopping every player's path after six calendar years would simply
hide the very value the user asked us to capture.

## Next control milestone, in order

1. Recover missing opening balances using dated official identity/transaction
   evidence and earlier service snapshots; do not replace unknown with zero.
2. Build complete historical active/IL/minors/exit states, retaining players who
   disappear from the next tracker. Separate missing observation from no service.
3. Fit a joint arrival/participation/service/production path with player-level
   dependence. Compare with the existing monotone service map and full-service
   shortcut. Use cutoff-safe folds and report service exhaustion and cumulative
   production errors, not only annual PA accuracy.
4. Carry paths beyond six calendar seasons when control remains; handle right
   censoring explicitly. Validate the tail before reporting a full total.
5. Keep statutory pre-FA production separate from current-organization control,
   extensions/options, non-tenders and salaries. Add dated contract terms only
   after historical-vintage validation.

Do not mark the full-control objective complete based on this explorer.

## Reproduce / verify

```
.venv/Scripts/python.exe -X utf8 scripts/extend_six_year_hitter_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_six_year_hitter_v1.py
.venv/Scripts/python.exe -X utf8 -m pytest tests/test_six_year_hitter.py tests/test_multiyear_hitter_components.py tests/test_control_path.py -q -p no:cacheprovider
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_full_2026_freeze.py
```

18 focused tests pass. The builder checks immutable earlier columns, chronology,
future null labels, finite forecasts, PA/probability bounds and unresolved control
totals. Source/code hashes and fixed fit notes are in
`model_artifacts/six-year-hitter-v1-2026-09-22/`. Raw source inputs remain local.
The [pre-fit plan](six-year-hitter-extension-v1-plan.md) records the scope and limits.
