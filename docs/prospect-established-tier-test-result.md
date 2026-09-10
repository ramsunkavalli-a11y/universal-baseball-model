# Prospect established-tier workload test result

Status: rejected; the next model must be one coherent conditional hurdle.

## Result

Adding an established-player tier did not fix the prospect values. It made the blanket workload correction more severe.

| Population | Version | 45+ FV | 50+ FV | Total expected six-year WAR |
|---|---|---:|---:|---:|
| Hitters | Current private preview | 903 | 320 | 3,813 |
| Hitters | Binary fringe/meaningful | 162 | 17 | 931 |
| Hitters | Three tiers | 122 | 8 | 732 |
| Pitchers | Current private preview | 156 | 18 | 769 |
| Pitchers | Binary fringe/meaningful | 10 | 0 | 170 |
| Pitchers | Three tiers | 3 | 0 | 124 |

The mature workload priors themselves are useful and sensibly ordered. For hitters, the six-year means are 61 PA for fringe arrivals, 754 PA for meaningful-only players, and 2,290 PA for established players. For pitchers they are 149 BF, 575 BF, and 1,770 BF before supported role splits.

The failure is upstream: three separately fitted unconditional probabilities do not form a coherent career path. Meaningful probability exceeded arrival probability for 248 current players, and established probability exceeded meaningful probability for 294. Clipping restores arithmetic order but not calibration.

Josuar Gonzalez illustrates it. His ordered six-year probabilities are 17.34% arrival, 6.71% meaningful, and 2.35% established. The three-tier sensitivity gives 0.46 expected WAR and 40 FV, below even the rejected binary result. More workload buckets cannot rescue overly low outcome probabilities.

The outside Top-100 comparison remained diagnostic only and was not used to fit or select anything. Three-tier MAE was 16.33 FV on 76 matches, worse than both the current preview (9.06) and binary sensitivity (14.59).

## Decision

Reject the three-tier value replacement. Retain the mature workload tiers as reusable outcome evidence.

The next model must estimate a single nested path:

1. probability of arrival;
2. probability of meaningful opportunity conditional on arrival;
3. probability of an established role conditional on meaningful opportunity.

Multiplying conditional probabilities guarantees the statistical ordering by construction. Selection must use time-ordered proper scores and supported sample checks. No outside FV, country shortcut, catcher preference, or arbitrary value floor is allowed.

Machine-readable detail: `docs/prospect-established-tier-test-result.json`.

