# Universal hitter historical comparables

Status: **accepted as foundation evidence; not yet an FV model**.

Every current pre-MLB hitter is evaluated with the same method. The model finds 150
prior hitters at the same exact primary level who are closest in age, workload, walk rate,
strikeout rate, home-run rate and extra-base-hit rate. Rate evidence is regressed by
200 PA before matching. Players who never reach MLB stay in the sample with zero MLB
production.

The time-ordered test trained only on the 2018 origin and evaluated all 3,251 players
from the 2021 origin. Players appearing in both groups were removed from the reference
set.

| Four-year batting-plus-replacement WAR | Bias | MAE | RMSE |
|---|---:|---:|---:|
| Population baseline | 0.042 | 0.345 | 0.996 |
| Historical comparables | -0.023 | 0.263 | 0.959 |

The universal comparison improved all three point metrics. It now reports arrival,
regressed MLB batting-plus-replacement quality conditional on arrival, cumulative
batting-plus-replacement WAR conditional on arrival, and its all-player expectation
separately.
The last value retains non-arrivals as zero and exactly equals arrival probability
times conditional cumulative WAR. These values are not whole-player WAR: defense,
position and baserunning are excluded.

Fernando Gonzalez receives 0.06 mean four-year batting-plus-replacement WAR from the same
process used for everyone else. That is effectively a near-zero batting outcome, but
it is no longer produced by a special player-group rule.

Machine-readable validation is in
`docs/prospect-hitter-historical-comparables-result.json`.

Neighbor-count sensitivity from 25 through 250 does not produce one dominant choice.
At 100 neighbors all-player MAE is lowest (0.249), while 25 has the lowest RMSE
(0.921), 25 has the lowest arrival Brier (0.0777), 150 has the lowest arrival log loss
(0.3017), and 250 has the best conditional-rate errors. The production foundation
therefore retains 150 rather than selecting a count from one favored metric.

## Conditional-rate support gate

An upper-tail audit found that some Rookie-level neighborhoods had only one eventual
MLB arrival. That one outcome created identical 3+ WAR/600 estimates for many current
players despite their very low arrival odds. Average error alone did not expose this.

Conditional rate is now displayable only with at least ten neighboring MLB arrivals.
This is not a raw-PA cutoff: unsupported players retain all official workload, arrival
and all-player expected-outcome estimates. On the 2019 selection cohort, supported
conditional-rate MAE/RMSE are 0.740/0.948 versus 0.900/1.150 for the population
baseline. On the untouched 2021 confirmation cohort they are 0.700/0.916 versus
0.795/1.019. Direct shrinkage-strength candidates were rejected because they improved
2021 but worsened 2019.
