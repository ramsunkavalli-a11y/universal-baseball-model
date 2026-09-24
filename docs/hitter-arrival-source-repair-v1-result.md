# Better historical inputs materially improve MLB-arrival forecasts

2026-09-23. Completed the [fixed source-repair plan](hitter-arrival-source-repair-v1-plan.md).
This is a successful **development probability milestone**, not deployment or
proof that projected player WAR/trade value has improved. The 2026 forecast and
explorer are unchanged. No 2026 outcomes were used.

## What actually changed

1. **Complete older debut evidence.** Reconstructed 66 completed-season MLB
   player censuses, 1960–2025, covering 12,447 identities; both previous debut
   inventories agree on their overlapping identities/dates. The lower bound
   predates the earliest inferred birth year in this panel. Corrected prior-debut
   status for 190 players across 494 snapshots. Within that set, 185 former MLB
   players across 478 minor-league snapshots stop being called never-debuted
   prospects. Nobody is removed from the modeling population.
2. **Year-end roster information.** Collected December 31 membership for all 30
   clubs in all 15 study origins, rather than using October 15. The resulting
   17,564 membership records change 794 panel flags from off-roster to on-roster
   and 1,788 in the opposite direction. This captures November protections,
   free agency and other roster turnover, not just convenient positive examples.
3. **Historical league context.** Matched every canonical batting stint to its
   captured league record, with no missing league matches or PA discrepancies.
   Added current/two-prior-year Mexican League PA shares and coverage flags.
   Mexican League players remain in the data, but their historical AAA label
   no longer needs to be the only clue to their different opportunity path.
   No existing batting-rate or level translation was rewritten.

The old panel and old model are preserved. A separate repaired 65,868-row panel
supports the new fits. Targets, row identities, performance history and all
other original inputs remain unchanged. All comparisons use corrected cohort
labels on identical player/origin keys, including the archived predictions.
Only five cases change the six annual test cohorts; most debut repairs are in
older training years. Thus the improvement is not obtained by deleting errors
from the evaluation group.

## Next-year arrival: a useful improvement across every test year

R is the old detailed model. C adds debut/league repairs; T changes only roster
timing; F combines both and is the predeclared primary candidate. Every arm uses
the same fixed LightGBM settings, eligible training years and player weights.

| Model | Brier, lower better | Log loss, lower better | Expected arrivals / observed |
|---|---:|---:|---:|
| R: original | 0.023953 | 0.083344 | 600.6 / 677 |
| C: debut + league | 0.023401 | 0.080740 | 616.5 / 677 |
| T: year-end roster | 0.021763 | 0.077829 | 595.7 / 677 |
| F: combined | 0.021267 | 0.075402 | 624.8 / 677 |

F improves Brier **11.2%** and log loss **9.5%** versus R, improving both scores
in **6/6 origins**. Paired player-cluster 95% intervals for the absolute changes
are [-0.003381, -0.002010] and [-0.010049, -0.005971], respectively. All fixed
annual/stage harm checks pass. Scores give equal weight to origins; counts are
sums of player probabilities across the snapshots, not unique future players.

Roster timing supplies the larger improvement in the controlled comparison.
The debut/league bundle adds further pooled improvement beyond roster timing,
with favorable intervals on both scores (5/6 Brier and 6/6 log-loss directions).
This test does **not** isolate the debut fix from the league features or prove
a causal importance decomposition of tree-model inputs.

F also beats the earlier probability ensemble in both scores in all four
matched origins (2017, 2018, 2021, 2022): Brier improves 13.4%, log loss 9.9%,
with favorable paired intervals. It beats accepted C2 on those same matched
years, both B2 coverage references across six years, and the previous AE
outage/no-era candidate across six years. The stronger ensemble/C2 archives do
not extend through the two latest origins; do not describe them as six-year
comparisons. F passes all of this experiment's next-year candidate gates.

## What it fixes, and what remains wrong

| Forecast origin | MLB season being forecast | Actual arrivals | Old R | Repaired F |
|---|---|---:|---:|---:|
| 2017 | 2018 | 95 | 92.5 | 89.8 |
| 2018 | 2019 | 108 | 90.9 | 92.0 |
| 2021 | 2022 | 157 | 58.1 | 84.7 |
| 2022 | 2023 | 106 | 112.5 | 126.3 |
| 2023 | 2024 | 107 | 145.3 | 134.3 |
| 2024 | 2025 | 104 | 101.3 | 97.8 |

Better individual probabilities need not produce a closer total every year.
The 2021-origin shortfall remains large, and the 2022-origin total overshoots
more than before even though both individual probability scores improve.
Do not declare calibration solved or force these totals to the exposed answers.

For the 2022 MLB season, Jeremy Peña moves from **3.9% to 64.8%** probability of
any MLB PA; Ezequiel Duran moves from **1.2% to 22.1%**. Roster-only refits give
47.6% and 25.3%, respectively. Both were added to 40-man rosters before the
year-end forecast cutoff. These are full refits with the same rules applied
to every vintage, not one-player flag flips. The prior diagnostic's 4.4%/1.6%
numbers came from AE, a different research arm; do not mix that baseline with R.
Examples illustrate a mechanism; they are not the acceptance test.

## Longer-term results are encouraging, not a completed value model

For arrival within three years, F improves Brier/log loss **6.9%/5.8%** versus R
in both available origins. Expected arrivals rise from 460 to 498 versus 649.
Both paired intervals favor F versus R, but improvement over the stronger
logistic coverage benchmark remains uncertain and reverses direction between
the two origins. These windows overlap; they are not independent confirmation.

For becoming a regular (at least 450 PA in two of three future seasons), F's
expected count rises from 19.2 to 23.0 versus 31. Brier improves 3.6% and log
loss 10.6% versus R, but the Brier interval includes no improvement. Gains beyond
the LightGBM coverage control are uncertain on both scores. The 2021-origin
regular count is still 8.6 versus 17; the 2022-origin count is 14.4 versus 14.

Across **all players**, not only never-debuted minor leaguers, next-year and
three-year arrival scores also improve. All-player regular-workload Brier is
slightly worse (0.019477 to 0.019623) while log loss improves. This is another
reason not to replace the complete player-value model from this result alone.
No conditional PA, hitting talent, WAR, six-year control value or trade-value
calculation was refitted or validated in this experiment.

## Source and statistical limits

- Historical roster endpoints were retrieved now with explicit past dates;
  these are not contemporaneously archived snapshots. Returned status, jersey,
  position and parent-team fields are not used. Only requested-set membership
  is certified for this experiment.
- Debut evidence is a retrospective reconstruction of a stable dated event.
  A later debut is never a prior-debut feature at an earlier forecast origin.
- The shared batting store contains later seasons, including 2026; only the
  declared 2007–2024 rows and explicitly dated capture folders enter source
  matching/features. No 2026 player performance enters fitting or scoring.
- League coverage is coverage of this panel's source population, not proof
  that all foreign leagues/players are covered. There are no Mexican League
  rows in the 2018 or post-2020 canonical blocks; zero observed exposure there
  does not mean the Mexican League did not exist. The 2020 block is MLB only;
  it is not an invented minor-league season.
- Historical years have been exposed in prior development. The fixed protocol
  limits this round's researcher choices but does not turn them into a new
  untouched holdout. Player-cluster intervals do not capture every shared
  season shock. No fresh 2026 evaluation has been performed.
- In the score report's illustrative cases, `on_40man` is **corrected year-end
  context**, not the input used by every arm. R/C still use the old flags.

## Decision and next gate

Retain the corrected source foundation and F as the new preferred **research
arrival candidate**. Do not deploy it automatically or revive failed calendar
adjustments by combining everything post hoc. Before any value-model promotion,
test the repaired probabilities in the existing opportunity/value system with
past-only training: conditional workload must remain separate from arrival,
and report delivered PA/WAR errors, calibration, prospect/returner/established
cohorts, and Years 1–3 separately. Do not extrapolate success to Years 4–6.

The next separate feature hypothesis is a player's defensive route to an MLB
job and depth of experience after promotion. The preceding player-error audit
identified these as possibilities, not validated corrections. First preserve
this source-repair baseline so further ideas have a clean control.

## Verification and reproduction

30 new fits, two exact future-data mutation replays, one exact original R
replay, 167,444 archived prediction rows, 32 focused passing unit tests.
Independent verification rebuilds the repaired panel, checks source hashes,
matching rows, target maturity, canceled-season exclusions, player weights and
reported scores. The previous era/schedule archive and 31-file original 2026
seal also verify unchanged.

Artifacts: `model_artifacts/hitter-arrival-source-repair-v1-2026-09-23/`.
Includes the preceding player-error diagnosis and its casebook. Raw external
captures remain local; hashes and derived audit summaries are archived.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/materialize_hitter_arrival_source_repair_v1.py
# --freeze only for a fresh experiment; never overwrite the existing contract.
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_arrival_source_repair_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_arrival_source_repair_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_arrival_source_repair_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_full_2026_freeze.py
```
