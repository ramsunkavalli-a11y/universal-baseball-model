# Completed 2026 hitter evaluation

The candidate was frozen and pushed in commit `e661958` before the authorized
2026 outcome retrieval. We have now scored that exact forecast once. Its total
playing time is close, but that hides too little contribution from new MLB
players and too much from established players. This is an evaluated research
candidate, not a proven replacement for Steamer or a finished player-value model.

## What was evaluated

The fixed population contains 4,030 hitters, including prospects, exits and
non-arrivals. The forecast asks how much **MLB batting contribution in 2026**
each player will deliver. It combines probability of any MLB PA, PA conditional
on appearing, and conditional MLB hitting wins above average per 600 PA.
Replacement is fixed at the 2025 reference. Defense, position and running are
not included. These numbers are not FanGraphs WAR, six-year control value,
peak ability or a trade valuation.

This was assembled retrospectively without looking at the protected outcomes;
it was not demonstrably published in January. Historical source revisions and
foreign-player coverage qualifications remain. January prospect ranks were
separately archived and qualified before fitting.

## Completed target checks

Official regular-season player totals match all thirty team totals for all
eight events. There are 2,429 completed games and one canceled game, not an
uncaptured season ending. Twenty-eight clubs played 162 games and two played
161. The first collection console incorrectly said all thirty played 162;
the saved schedule and subsequent reconciliation record the correct counts.

The player endpoint contains 751 rows but only **662 players with positive PA**;
89 zero-PA rows include pitchers and other roster members. They are not 751
batters who actually hit. Conditional hitting rate is unobserved for zero PA,
not zero talent. The scorer's independent-label assertion caught that placeholder
distinction before producing scores; the correction and unchanged forecasts are
recorded in its receipt.

## Accuracy and totals

| Measure | Frozen forecast | Completed outcome or error |
| --- | ---: | ---: |
| MLB participants in the fixed cohort | 644.3 expected | 655 |
| Fixed cohort PA | 181,374 | 182,453 |
| Fixed cohort batting contribution | 578.73 | 567.58 |
| All-player PA RMSE | — | 64.34 PA |
| Conditional hitting RMSE weighted by actual PA | — | 1.732 wins per 600 PA |
| Delivered contribution RMSE | — | 0.4594 wins |
| Delivered contribution MAE | — | 0.1356 wins |
| Participation Brier and log loss | — | 0.03477 and 0.11928 |

The small all-player error includes thousands of players with no MLB PA.
Among the 667 players classified as current MLB at the cutoff, PA RMSE is
140.66 and contribution RMSE is 1.0542. The headline is not a typical regular
player's error. Nor does it directly compare with the historical multi-origin
0.4351 contribution RMSE: year, membership and league conditions differ.

The primary target centers actual hitting on the completed 2026 MLB league.
The predeclared secondary target centers the same outcomes on the 2025 league;
its contribution RMSE is 0.4614 and actual cohort total is 578.07. Both are
reported; the near-perfect secondary total is not chosen instead of the primary
result. These are fixed neutral event weights applied to observed MLB outcomes,
not a complete park-neutral measure of intrinsic talent.

A descriptive 2,000-player-resampling interval for contribution RMSE is
0.4210–0.4987. It describes this season's player mix, not performance across
independent future seasons and not improvement over a matched public system.
There is no verified preseason 2026 public export in this comparison. No claim
of beating ZiPS or Steamer is supported.

## The prospect imbalance is real but not a reason to raise everyone

Among the 3,116 players who had never debuted, the model expected 102.7 arrivals
and 105 occurred. That aggregate is close. It forecast 13,098 PA and 27.33
batting-contribution wins; actual totals were 15,976 PA and 46.24 wins. Thus the
miss is not simply failing to predict enough debuting players. Workload and
hitting among arrivals also matter. Conditional hitting is too low by 0.333
wins per 600 PA when weighted by their actual PA.

Prior MLB players receive 551.40 projected contribution versus 521.33 actual.
These errors partly cancel in the league-wide total. Upper minors as a whole
receive 13,786 projected PA versus 17,226 actual; their contribution is 27.30
versus 49.22. These are origin-defined groups, not selected winners.

In contrast, grouping by **actual** 400+ PA necessarily selects players who
stayed healthy, won jobs or broke out. Their underprediction alone does not
prove a preseason model should raise every player. The report retains these
descriptive outcome groups but does not use them for post-result calibration.
Jett Williams and Aidan Miller were forecast for roughly 220 and 213 PA and
received none; those misses argue against a blanket prospect multiplier.

## Coverage and baseball checks

The full league had 183,849 PA. Seven actual participants outside the forecast
universe account for 1,396 PA and 5.30 contribution wins. Okamoto, Murakami,
Song and returning Wisdom account for all but three incidental pitcher PA.
These are missing forecasts, not model predictions of zero. Austin was a
known unmodeled rostered hitter but had no PA in this target. The domestic
model is therefore not a universal entrant projection, even with 99.24% of
actual league PA inside its fixed cohort.

[Player reviews](hitter-final-2026-player-review.md) separate source defects,
workload error, hitting error and uncertainty. All 37 pre-freeze construction
cases remain; error tails and ordinary controls were added. We replayed 129
players and origin-selected peers through actual source counts and saved models.
The narrated review covers the important contrasts; 129 mechanical replays
should not be read as 129 independent expert endorsements.

Judge's miss is mostly workload; Duran's is almost entirely hitting. Kurtz's
hitting forecast is close but workload is high. Rumfield and McGonigle were
missed in both workload and hitting. Made and De Vries had no MLB PA, which
does not establish that their future careers are poor. Horwitz's accurate final
contribution partly reflects offsetting errors. These distinctions matter more
than calling every large miss a missing feature.

## Decision and next work

Execution and the required player review are complete. No forecast was refitted,
blended, clipped or selected after viewing 2026. Both frozen packages remain
unchanged. The model can be inspected in a separate team-filtered results
explorer; the old explorer is not overwritten.

Keep the candidate as a qualified reference, not automatic deployment of a full
value model. For a later-season model, first close entrant coverage and obtain a
genuine matched public benchmark. Then audit prospect **conditional** workload
and level/stage representation on the older chronological folds. In particular,
a 24-PA AA cameo must not stand in for established AA experience. Evaluate
scouting contrasts in the same audit rather than repeatedly trying new algorithms
or revisiting the closed team-record idea. A bounded historical repair must earn
its improvement and pass source-to-outcome walks; 2026 is now development
evidence for any later changes, never another protected test to pass.
