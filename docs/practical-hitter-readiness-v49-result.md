# Readiness is clearer, but the hitter model is not finished

2026-10-03. All 140 saved heads replay; all 31 actual player reviews are complete.
This is historical research, not a change to the protected 2026 forecast.
See the [fixed contract](practical-hitter-readiness-v49-contract.md) and
[actual source-to-forecast walkthrough](../reports/model-evidence/practical-hitter-readiness-v49/player-walkthrough.md).

## What changed

Estimate two things separately: whether the player gets any MLB PA next year,
and how much he plays if he does. Their product gives expected PA. Compare the
same count/games/draft inputs with and without twelve historical ranking fields.
All 30,506 forecasts, non-arrivals and old comparison outputs are retained.
Batting ability is held fixed: this test cannot claim to improve hitting talent.
The conditional head uses only earlier known active outcomes, not future test
participants. Each head separately balances its training origins; no exact
joint weighted distribution or causal feature attribution is claimed.

| Identical population / measure | Direct count/games | Binary count | Binary scouting |
|---|---:|---:|---:|
| All forecasts: PA RMSE | 61.149 | 60.936 | 60.650 |
| All: batting + replacement RMSE | 0.43947 | 0.43894 | 0.43815 |
| Public 1,789: PA RMSE | 143.191 | 142.651 | 142.110 |
| Public: average absolute PA error | 111.320 | 111.171 | 110.087 |
| Top20 listed 105: PA RMSE | 214.524 | 210.686 | 182.749 |
| Ranked lower minors 70: PA RMSE | 43.343 | 39.256 | 40.851 |

Steamer's same public PA RMSE/MAE are 135.019/92.399. The scouting binary is
5.3% worse on RMSE (within the declared 10% goal), but 19.1% worse on MAE
(outside 15%). Do not quietly change the practical target. Public dates and
batting-value conversions remain qualified. The all-row PA squared-error change
from adding rankings to the binary model is -34.73, nominal player-cluster 95%
interval -63.84 to -2.55; contribution change -0.000691, interval -0.001557
to +0.000110. Other architecture contrasts include no gain. These are repeatedly
exposed development comparisons, not independent confirmation.

## What makes baseball sense, and what still fails

The previous positive-ranking fallback allocated 3,769 immediate PA to seventy
ranked lower-minor forecasts, versus 836 observed. Binary scouting reduces that
to 1,044. Salas goes from 232 expected PA to 7; quality no longer implies an
immediate job. But that group has only 5.55 expected MLB participants versus nine
actual: an almost reasonable PA sum still hides low arrival and high conditional
use. Do not call the probability estimates fully calibrated.

Volpe improves from 166 direct-count PA to 334 versus 601 actual, and Rodriguez
from 103 to 236 versus 560. Judge's debut workload rises from 150 to 287 versus
678, but the fixed batting estimate still badly misses his breakout. Brinson is
a real harm: 121 becomes 297 versus 55. Mayer still gets 188 versus zero.
Ranked teenage conditional training profiles can contain only a few people.

Fast-entry misses remain serious: Langford 47 versus 557, Kurtz 2 versus 489,
Bellinger 14 versus 548. Preseason tables are stale for new draftees and rapidly
advancing prospects; the actual fourth draft picks are present, not lost joins.
Alonso has a 73% participation estimate but only 180 PA if active, producing 132
versus 693. Distinguish arrival mistakes from compressed opportunity after
arrival rather than applying one universal prospect boost.

Never-debut upper minors total 73,989 PA versus 92,891 actual, with 593.7 expected
participants versus 730 actual. Lower minors overall remain high: 8,165 versus
6,072 PA. The 2021 origin is low on PA but high on contribution; a good pooled
score does not erase the COVID/era problem.

Origin-only diagnostics also retain absence/roster qualifications. Prior regulars
currently absent get 2,052 versus 3,892 PA, including the large Tatis return miss.
Current 400-PA players not listed on the captured roster have almost exact PA
totals (60,954 versus 60,860) while participation is too low and conditional use
offsets it. Therefore do not blanket-remove roster evidence or assume every
absent player returns healthy. Later injury/release facts are not forecast inputs.

## Decision and next work

Retain this binary architecture as a useful research candidate, not a certified
whole-model replacement. The hitter goal remains active. Preserve the stronger
working assembly and all failed alternatives. Next finish the talent milestone
in the [controlling practical plan](practical-hitter-model-v30-plan.md): inspect
the actual hitting-rate assumptions and compatible older evidence, then make a
bounded meaningful comparison. Judge/Votto/Bellinger rate misses cannot be
fixed by more PA gates. No new college collection or protected 2026 outcomes.

The new local explorer shows historical probability, conditional PA, expected PA,
batting rate and actual results with organization/year filters and the actual
review notes. It is a research comparison through target 2025, not a six-year
valuation model. Older explorer and frozen forecast files are unchanged.
