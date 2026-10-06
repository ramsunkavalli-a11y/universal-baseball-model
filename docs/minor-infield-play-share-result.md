# Complete ground-ball exposure did not establish an MLB projection upgrade

2026-10-05. [Locked contract](minor-infield-play-share-contract.md),
[player walkthrough](minor-infield-play-share-player-walkthrough.md),
[source/support report](../reports/model-evidence/minor-infield-play-share/preflight.json),
[scores and fit seals](../reports/model-evidence/minor-infield-play-share/fit-report.json).

## What actually changed

Built an outcome-complete minor infield play-share measurement. Through hits
remain in exposure, even when the ball was recovered by an outfielder. There
is no arbitrary adjacent-fielder blame, no scorer-coordinate out probability
and no double-play double credit. Expected credits exclude the player's defensive
team; park/hand cells shrink toward other-team league rates. Pitcher quality and
starting positions are NOT controlled. This is a coarse proxy, not OAA.

2,026,088 archived distinct ground balls were checked; 2,007,470 meet the fixed
label/source rules. Unknown/conflicting/unsupported outcomes remain in source
accounting. A player at each known 2B/3B/SS position shares exposure; those are
not three independently available outs. Sources include DSL league 130, US
complexes and higher levels, not a census of every scheduled game.

The prepared cohort has 11,524 training/test player-origins. Fifty actual
chronological/player-held-out subsets passed execution/global-fit checks;
conditional-profile gaps remain explicit. All 150 saved models and every pooled
input replay. Five evaluation origins have all eligible forecasts retained;
recent origins 2022–24 contribute 4,852 forecasts, of which two active native
measurements are unknown, leaving 4,850 primary labels. All other nonparticipants
are zero only through the certified official MLB position ledger.

## Matched results

Primary outcome is delivered next-year MLB **range runs**, not full defense or
WAR. The quality diagnostic is runs per 1,500 defensive outs among players
subsequently receiving substantial MLB infield time.

| Forecast | Delivered RMSE, 4,850 forecasts | Weighted quality MSE, 454 forecasts |
| --- | ---: | ---: |
| Zero adjustment | 1.35683 | 13.15305 |
| Simple age/level/usage/MLB-history benchmark | 1.33183 | 12.51955 |
| Benchmark + selected-first-touch proxy | 1.33158 | 12.41852 |
| Benchmark + complete-exposure proxy | 1.33164 | 12.67501 |

The complete proxy changes delivered RMSE only **0.014%** versus the benchmark.
Its paired MSE change is -0.000492 runs², with player-cluster development interval
[-0.002695, +0.001762]. Conditional weighted MSE worsens **1.24%**; the old-style
proxy improves it about 0.81%, mainly among players already having MLB defense.
No arm search or tuning followed these results. MAE also worsens slightly against
the benchmark; it is diagnostic, not a median-target veto of expected value.

Pooled predicted range totals are -265.82 versus -253.57 actual, but good totals
hide misses. AA predicts -48.09 versus -11.34 actual. Players with no prior MLB
defense have worse primary MSE than zero and 2.73% worse conditional weighted MSE
than the benchmark. A and rookie delivered MSE rise about 16% and 15% against
the benchmark, respectively; absolute values are tiny and their near-zero
next-year participation does not measure eventual talent. The benchmark itself
is not a satisfactory deployed minor-range forecast.

## What this CANNOT settle

Recent A and rookie groups contain 689 and 1,528 forecasts but **zero** substantial
next-year MLB infield labels. A+ has seven, AA 35 and AAA 70. Of 454 total quality
labels, 338 have MLB as their origin level and only 100 players lack all prior
MLB defensive outs. Every scored A+/AA quality profile has fewer than 20 matching
training people. Even AAA has 53/70 under that warning threshold.

Thus the primary next-year value target is legitimate, but it is poorly suited
to judging distant A/DSL *fielding ability*. A future longer-path test needs
mature outcome coverage AND actual chronological training examples, not merely
changing Year 1 to Year 5 in a nine-season file. Retrospective native defensive
metrics are noisy/revisable measurements. Conditional selection, pitcher/ball
difficulty, positioning and future role prevent a general causal claim.

Rafaela is the largest delivered gain (+0.050 runs), yet still missed by 19 runs
and mostly played outfield next year. Peña/Mayer positive defense is missed;
Edwards gets worse. Witt's rookie rate and Peguero's modest defense improve.
Linares' 2B cameo yields an unsupported conditional estimate for a catcher.
These cases and unsuccessful origin-known peers are retained in the walkthrough.

## Decision

**Do not add this recipe to production and do not tune it again.** The measurement
is useful for audit and further source construction. The test does not prove
minor defensive statistics or tracking cannot help. Older first-touch-denominator
failures remain qualified; they are not retrospectively repaired by this run.
Existing running/native-MLB/catcher research benchmarks are not withdrawn.

Execution and replay pass. Conditional profile coverage is limited. Predictive
promotion conditions fail. Baseball review is complete and identifies the scope/
extrapolation failures above. No full-WAR, trade-value or long-horizon claim.

Eight measurement/support regression tests pass. Two preparation attempts stopped BEFORE
fits (test season dtype, feature naming/missing age); their local source products
are preserved in versioned failed-preparation directories. No failed forecast
was removed. Frozen 2026 forecasts/evaluation and the explorer are unchanged.

The next component gate is recorded in
[the component review](nonbatting-hitter-component-review.md), not an algorithm
tournament or another sweep of this signal's weights.
