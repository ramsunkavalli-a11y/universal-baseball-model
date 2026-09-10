# Prospect pitcher horizon-extrapolation audit

**Status:** development diagnostic; not a promotion gate

The deployed prospect hurdle turns a two-year probability into a longer horizon by
repeating a constant hazard. This audit fits only the 2018 pitcher snapshot and its
2019-2020 outcomes, then evaluates the 2021 snapshot against four completed seasons
from 2022 through 2025. All 3,642 eligible pitchers remain in the sample,
including non-arrivals.

| Four-year outcome | Observed | Predicted | Brier | Log loss |
|---|---:|---:|---:|---:|
| Any MLB arrival | 12.27% | 15.47% | 0.09530 | 0.31968 |
| Meaningful role | 4.97% | 8.90% | 0.04579 | 0.17022 |
| Established role | 2.99% | 3.83% | 0.02740 | 0.10860 |

The direct-evidence cap lowers meaningful-role Brier from
0.04579 to 0.04234 and log loss from
0.17022 to 0.16087. For established
roles it changes Brier from 0.02740 to
0.02701 and log loss from 0.10860 to
0.11663.

The repeated-hazard form is not causing low probabilities. It is more optimistic than
the outcomes and worsens both Brier and log-loss scores versus leaving the two-year
arrival probability unchanged (0.09201 versus
0.09530; 0.31976 versus
0.31968). It also worsens the meaningful-role Brier score
(0.04206 versus 0.04579). The largest
supported meaningful-role calibration gap is
16.7%. The subgroup tables in the JSON
cover level, age band, throwing hand, and starter/reliever role.

This is a useful check of the probability chain, not an untouched confirmation set.
The 2018 training label includes shortened 2020, and the 2021 cohort has appeared in
earlier two-year work. It also does not test pitcher WAR conditional on reaching MLB.
No current value changes can be justified from this result alone.
