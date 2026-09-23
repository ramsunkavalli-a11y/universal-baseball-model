# Rookie-ball arrival repair: a targeted improvement

2026-09-23 · Development evidence only · Outcome cutoff 2025-12-31

## What changed

The explorer exposed a real problem: rookie-ball players received too much
near-term MLB playing time, while batting value was estimated separately from
that playing time. The passing repair links those quantities. Historical
players of the same starting level and age band establish annual MLB
participation probability; separate models estimate playing time and hitting
rate conditional on playing. Expected batting/replacement value is expected
PA multiplied by the independently predicted rate. Non-arrivals remain in the
data. This is annual participation, not cumulative career arrival.

Only 1,093 never-debuted rookie-ball players change in each of Years 1–3.
Other players and all Years 4–6 retain their prior forecasts exactly. Existing
component rates are held fixed, with component amounts reduced in proportion
to repaired PA. This does not establish better defensive talent estimates.
Original forecast packages, including the protected one-year 2026 freeze, are
untouched. No 2026 performance outcomes were used.

The new explorer is at `http://127.0.0.1:8777/`. Team/stage filters remain, and a
totals link shows PA, batting/replacement value and the combined scenario for
both the selected players and the entire unique-player pool. Historical team
affiliations are not forecasts of future rosters. Do not sum organization
groups without deduplicating players.

## What this does to the example that exposed the problem

| 2027 quantity | Before | After |
| --- | ---: | ---: |
| Giants' 38 rookie-ball players: expected MLB PA | 183.55 | 5.14 |
| Same group: batting/replacement wins | 0.701 | 0.012 |
| All unique players: expected MLB PA | 189,695 | 184,389 |
| All unique players: batting/replacement wins | 601.14 | 580.35 |
| All unique players: combined component scenario | 555.75 | 536.67 |

Those league totals were not forced to a target. For context, the 2025 full-MLB
labels contain 182,926 PA and 570 batting/replacement target wins. The latter
is our internal target, not a universal full-WAR budget. The combined ledger
still needs accounting normalization, particularly position value. Its label
must not imply that this is already a confirmed full-WAR forecast.

## Evidence for the narrow repair

The [plan](hitter-arrival-coherence-v1-plan.md) was saved before fitting and
scoring. There were two fixed scopes: all never-debuted minor leaguers, followed
by a rookie-ball-only fallback if the broader change failed. Horizon-specific
training used only labels mature at the forecast cutoff and excluded paths
crossing 2020. The retained input set has 77 features. The age/level probability
estimate uses a fixed 100-player prior; strengths 50 and 200 are sensitivity
checks, not alternative winners selected after viewing results.

Across 4,222 affected player-origin paths in the three usable normal cumulative
origins (2016, 2021, 2022), three-year batting/replacement RMSE improves
**0.237 to 0.206**, with improvement in all three origins. The paired MSE change
is -0.01361, with a player-clustered 95% interval of [-0.01589, -0.01070].
Cumulative MAE improves 0.1095 to 0.0137. Annual PA error, probability scores
and aggregate error also improve against the delivered reference.

For the entire player population, cumulative MSE improves only 1.47772 to
1.47326: this is a modest whole-model gain, not a wholesale model breakthrough.
With the expanded component target, the corresponding complete-case cumulative
MSE improves 1.63003 to 1.62542. Only two complete normal origins support that
component check. The cold-player sensitivity excludes test identities from
candidate fitting, but its inherited reference was not fitted disjointly; it
is not a fair independent cold-start tournament.

Very few rookie-ball players reach MLB this quickly. Actual active counts in
the annual affected test rows are 1, 5 and 31 in Years 1, 2 and 3. Only the
Year-3 age-18-and-under cell has enough positives to meet the predeclared
subgroup support threshold. This supports shrinking implausible near-term
contributions, not a claim that we can identify individual rapid breakouts.

## What did not work

The all-minors version failed. First-year affected value MSE increased 8.7%,
and the age-21–22 AAA cell worsened 28.1%. Probability and aggregate PA guards
also failed. Its cumulative improvement was statistically uncertain. It was
not applied to upper-minors players or major leaguers.

The earlier five-model opportunity ensemble also remains slightly better than
this recipe on the pooled affected comparison: PA RMSE 12.108 versus 12.187,
and linked batting-value RMSE 0.07725 versus 0.07766. The repair passed against
the delivered forecast; it is **not the best universal opportunity engine**.
Do not change that comparator or replace the predeclared recipe after scoring.

## Remaining gaps and next test

- Years 4–6 keep their old arrival estimates. All mature six-year paths cross
  the pandemic; short-horizon success is not permission to alter those means.
- Repaired league PA is 184,089 / 184,389 / 178,389 in 2026–2028. Batting value
  is 523.5 / 580.4 / 578.1. The uneven totals remain visible. Forecasts cover
  today's player pool, not unknown future entrants; a later PA shortfall cannot
  automatically be fixed by scaling today's players upward.
- Batting/replacement and combined scenario values need explicit common
  league accounting before claiming normalized WAR. Do not target the same
  numerical budget for both quantities.
- Six calendar years are still not six years of team control. Full remaining
  control values stay unavailable until joint service paths and the late-arrival
  tail are validated.

Next predeclare a joint opportunity/value test built on the stronger earlier
ensemble, using earlier-fold-only probability calibration and preserving
individual differences. Include level/age, top-player, aggregate PA/value,
unseen-entrant and full-ledger checks from the outset. Do not apply a blanket
league multiplier. Long-horizon calibration and joint service paths remain
separate acceptance decisions.

## Reproduction and audit

Run from the repository with the existing local historical inputs:

```text
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_arrival_coherence_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_arrival_coherence_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_hitter_arrival_coherence_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_arrival_coherence_v1.py
.venv/Scripts/python.exe -X utf8 -m pytest tests/test_hitter_arrival_coherence.py tests/test_six_year_hitter.py tests/test_hitter_three_year_opportunity.py -q -p no:cacheprovider
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_full_2026_freeze.py
```

The package is `model_artifacts/hitter-arrival-coherence-v1-2026-09-23/`.
It records 43 fits, 188,080 prediction rows, training cutoff evidence, source
hashes, decisions and delivered forecasts. Eighteen focused tests pass. The
original 31-file, 3,907-player 2026 freeze verifies unchanged. Delivery asserts
exact equality for unaffected player/horizon quantities. Local-only service
annotations are not added to the committed forecast; they do not use 2026
performance. The generated explorer is local and the prior explorer remains
available separately.
