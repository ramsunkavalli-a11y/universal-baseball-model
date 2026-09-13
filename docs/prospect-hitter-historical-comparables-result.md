# Universal hitter historical comparables

Status: **accepted as foundation evidence; not yet an FV model**.

Every current pre-MLB hitter is evaluated with the same method. The model finds 150
prior hitters at the same primary level who are closest in age, workload, walk rate,
strikeout rate, home-run rate and extra-base-hit rate. Rate evidence is regressed by
200 PA before matching. Players who never reach MLB stay in the sample with zero MLB
production.

The time-ordered test trained only on the 2018 origin and evaluated all 3,251 players
from the 2021 origin. Players appearing in both groups were removed from the reference
set.

| Four-year batting-component WAR | Bias | MAE | RMSE |
|---|---:|---:|---:|
| Population baseline | 0.042 | 0.345 | 0.996 |
| Historical comparables | -0.020 | 0.264 | 0.960 |

The universal comparison improved all three point metrics. It is now shown for every
current hitter as evidence of arrival frequency, mean later batting-component WAR and
the frequency of reaching 1 WAR. These values are not total WAR: defense, position and
baserunning are excluded.

Fernando Gonzalez receives 0.08 mean four-year batting-component WAR from the same
process used for everyone else. That is effectively a near-zero batting outcome, but
it is no longer produced by a special player-group rule.

Machine-readable validation is in
`docs/prospect-hitter-historical-comparables-result.json`.
