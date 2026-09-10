# Prospect pitcher horizon-extrapolation audit

**Status:** development diagnostic; not a promotion gate

The deployed prospect hurdle turns a two-year probability into a longer horizon by
repeating a constant hazard. This audit fits only the 2018 pitcher snapshot and its
2019-2020 outcomes, then evaluates the 2021 snapshot against four completed seasons
from 2022 through 2025. All 3,649 eligible pitchers remain in the sample,
including non-arrivals.

| Four-year outcome | Observed | Predicted | Brier | Log loss |
|---|---:|---:|---:|---:|
| Any MLB arrival | 12.28% | 15.69% | 0.09504 | 0.31855 |
| Meaningful role | 4.96% | 9.20% | 0.04613 | 0.17122 |
| Established role | 2.99% | 4.50% | 0.02827 | 0.10972 |

The repeated-hazard form is not causing low probabilities. It is more optimistic than
the outcomes and worsens both Brier and log-loss scores versus leaving the two-year
arrival probability unchanged (0.09193 versus
0.09504; 0.31769 versus
0.31855). It also worsens the meaningful-role Brier score
(0.04191 versus 0.04613). The largest
supported meaningful-role calibration gap is
16.6%. The subgroup tables in the JSON
cover level, age band, throwing hand, and starter/reliever role.

This is a useful check of the probability chain, not an untouched confirmation set.
The 2018 training label includes shortened 2020, and the 2021 cohort has appeared in
earlier two-year work. It also does not test pitcher WAR conditional on reaching MLB.
No current value changes can be justified from this result alone.
