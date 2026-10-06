# Seven known career departures now change the forecast

2026-10-05. Completed source/status repair, historical development evidence.
The live explorer and both frozen forecasts are unchanged. This is not a new
hitting model, a complete injury model, full WAR or a competitive-accuracy claim.

## What changed

Seven explicit public reports now gate unconditional contribution, using the
existing reversible retirement-state machinery. Medical career departure is
kept distinct from formal retirement. Both announcement and effective dates must
precede the actual forecast cutoff. Subsequent positive playing evidence can
reverse the gate; bare rights transfers cannot. A released/unsigned player is
not assigned zero merely because he later receives no MLB playing time.

Every original prediction/input column is preserved. Conditional PA and hitting
talent remain identical. Only seven of 30,519 historical forecasts change; the
other 30,512 retain bit-exact outputs. All 24,207 never-debut forecasts are
unchanged. The source supplement is manual and partial, not certified coverage
of every retirement, medical departure or subsequent comeback.

## Player review: all seven changes and the controls

The [24 persisted walks](../reports/model-evidence/hitter-reported-departure/player-walks.json)
include all seven changed rows, nine earlier unchanged source-player forecasts
and eight fixed controls. All 48 actual saved opportunity heads independently
reproduce. Three years of level-specific PA/HR/K/BB, all actual opportunity
inputs, original probability/conditional PA/rate/value, dated departure evidence,
and origin-selected comparison players are saved. The hitting-rate fit is not
refitted or independently replayed here; its saved output is held fixed.

| Player, season predicted | Latest MLB PA / HR / K | Old probability / conditional PA | Old expected PA → corrected | Old value → corrected |
| --- | ---: | ---: | ---: | ---: |
| Teixeira, 2017 | 438 / 15 / 105 | 21% / 313 | 67 → 0 | 0.219 → 0 |
| Fielder, 2017 | 370 / 8 / 63 | 96% / 437 | 419 → 0 | 1.355 → 0 |
| Beltrán, 2018 | 509 / 14 / 102 | 33% / 300 | 100 → 0 | 0.251 → 0 |
| Beltré, 2019 | 481 / 15 / 96 | 41% / 405 | 168 → 0 | 0.627 → 0 |
| Martínez, 2019 | 508 / 9 / 49 | 32% / 206 | 67 → 0 | 0.080 → 0 |
| Utley, 2019 | 187 / 1 / 34 | 24% / 89 | 22 → 0 | 0.0002 → 0 |
| Mauer, 2019 | 543 / 6 / 86 | 46% / 418 | 191 → 0 | 0.591 → 0 |

All seven actually recorded zero target-season MLB PA. The correction follows
dated departure evidence, not that outcome. Forecast cutoffs are January 28,
2017; January 27, 2018; and January 27, 2019. Source dates and URLs are in the
[sealed report supplement](../config/hitter_reported_career_departures.json).
[Beltré's own statement](https://www.mlb.com/press-release/statement-from-adrian-beltre-300952152)
is dated November 20, 2018.
[Mauer's announcement](https://www.mlb.com/news/joe-mauer-announces-retirement-c300522134)
is dated November 9, 2018.
[Beltrán's announcement](https://www.mlb.com/news/carlos-beltran-retires-has-manager-potential-c261747188)
is dated November 13, 2017.
[Utley's confirming report](https://www.mlb.com/news/dodgers-release-chase-utley-who-will-retire-c300524382)
is dated November 10, 2018.
[Teixeira's final-game report](https://www.mlb.com/news/mark-teixeira-plays-final-game-of-career-c204599800)
is dated October 2, 2016. Fielder and Martínez source judgments are linked in the
[group audit](hitter-big-miss-group-audit-result.md).

The nine earlier source-player forecasts remain unchanged because their
departure reports were still in the future: Beltré 2017/2018; Beltrán 2017;
Martínez 2017/2018; Utley 2017/2018; Mauer 2017/2018. Those actual returning
players prevent a retrospective career-ending label from rewriting their
earlier seasons. Their actual PA range is 187–597; a blanket player-ID hard zero
would have created major harms.

Fixed controls also remain unchanged:

| Player, predicted season | Expected PA / actual PA | Judgment |
| --- | ---: | --- |
| Belt, 2024 | 195 / 0 | No affirmative cutoff-known departure; keep the miss. |
| Donaldson, 2024 | 62 / 0 | Retirement was March 4, after the January forecast. |
| Votto, 2024 | 91 / 0 | Retirement was August 21, after the January forecast. |
| Kwan, 2022 | 114 / 638 | Genuine prospect/role miss; retirement repair cannot solve it. |
| Tatis, 2023 | 61 / 635 | Finite suspension and medical return uncertainty remain open. |
| Wander Franco, 2024 | 545 / 0 | Unresolved legal availability is not a confirmed retirement. |
| Estevez, 2025 | 0.20 / 0 | DSL non-arrival control; no change. |
| Smoak, 2019 | 489 / 500 | Ordinary workload control; no change. |

[Donaldson's dated announcement](https://www.mlb.com/video/donaldson-announces-retirement)
and [Votto's dated announcement](https://www.mlb.com/reds/video/joey-votto-announces-his-retirement-from-mlb)
establish why the January forecasts cannot use those retirements.
For ordinary source peers, Fielder's closest comparable historical workload
group includes Lowrie (387 expected, 645 actual), Francoeur (90, 0), and Navarro
(104, 0). Only affirmative departure evidence changes the focal player's policy,
not a rule assuming that all aging players with interrupted workload disappear.
Full peer lists remain in the walks; they are origin-only diagnostic matches,
not perfect talent/health controls. No changed-row harms emerged. The substantial
unchanged false highs/lows above remain in scoring, rather than being omitted.

## Measured effect and limits

| Scope | Old PA RMSE | Corrected PA RMSE | Old value RMSE | Corrected value RMSE |
| --- | ---: | ---: | ---: | ---: |
| All 30,519 | 60.236 | 60.165 | 0.436289 | 0.436187 |
| 6,312 with MLB history | 121.128 | 120.958 | 0.912741 | 0.912507 |
| No MLB debut | 27.362 | 27.362 | 0.150832 | 0.150832 |

These are pooled row-weighted descriptive errors. Equal-origin PA RMSE also
improves 60.334 → 60.267. Brier improves 0.032483 → 0.032430 and log loss
0.111446 → 0.111261. Gains occur only in origins 2016–2018; later origins are
identical. Overall PA RMSE improves about 0.12%, not a large competitive advance.
Removing 1,032.98 incorrectly assigned PA and 3.124 batting-plus-replacement
wins slightly worsens the overall underprediction of totals while improving
individual accuracy. Compensating errors must not be retained to make totals
look right. Forecast PA totals become 1,235,972.95 versus 1,272,118 actual;
value totals become 4,181.38 versus 4,193.77 actual.

The [machine report](../reports/model-evidence/hitter-reported-departure/report.json)
retains every origin/career-group score and the earlier selected architecture
reference. Public projections are absent from this exact saved cohort: no
alternative target/vintage was silently inserted, and no Steamer gap is claimed
closed. The seven development-selected reports cannot establish a generalized
accuracy gain or calibrate comeback probabilities. Their supported contribution
is correcting dated factual status in actual forecast arithmetic.

Walkthrough complete; retain this source/status repair for the research recipe.
Deployment remains separate. Do not rerun this source contrast as another
algorithm test. The broader gaps and cohort-dependent prospect diagnosis remain
in the [audit follow-up](hitter-big-miss-group-origin-follow-up.md).
