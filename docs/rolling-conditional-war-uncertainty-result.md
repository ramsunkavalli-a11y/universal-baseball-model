# Rolling conditional WAR uncertainty

Status: performance scale supported and promoted after full-mixture confirmation.

The test separates the two sources of annual uncertainty. It uses observed workload
only to isolate skill/performance error; it does not use that workload to make a
forecast. The workload distribution is tested separately.

Across the rolling 2023–2025 evaluation origins, the existing conditional-performance
ranges cover 71.8% of hitter results and 71.4% of pitcher results against an 80%
target. A standard-deviation multiplier learned only from earlier completed origins
raises coverage to 81.5% for hitters and 80.7% for pitchers while improving pooled
interval score:

| Component | Raw coverage | Scaled coverage | Raw score | Scaled score |
| --- | ---: | ---: | ---: | ---: |
| Hitters | 71.8% | 81.5% | 2.866 | 2.825 |
| Pitchers | 71.4% | 80.7% | 2.133 | 2.074 |

The scale used for the current forecast, learned through the 2025 origin, is 1.207 for
hitters and 1.245 for pitchers. Point estimates do not change. The hitter interval
score improves in 2023 and 2024 and is nearly neutral in 2025; the pitcher score
improves in all three evaluation years.

An exact simulation of the 2025 zero-activity/workload/performance mixture was also
added. It improves the overall interval score versus the current single-normal range
from 0.968 to 0.789 for hitters and from 0.635 to 0.512 for pitchers. It also confirms
that many low-probability players should have a P10–P90 range of exactly zero. This is
the correct shape. The subsequent rolling combined test passed in every year and the
private playable ranges now use it. See the
[combined result](rolling-combined-war-uncertainty-result.md).

Method boundaries:

- participation probabilities remain raw because rolling recalibration failed;
- conditional positive workload remains unchanged because its coverage is already
  near target;
- only performance standard deviation is scaled;
- the displayed P10–P90 range is minimally extended when necessary to contain the
  expected value required by the contract-value interface;
- defense and baserunning are neutral in the rolling performance test;
- no later target is used to fit its own scale; and
- outside FV opinions are not used.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\audit_rolling_conditional_war_uncertainty.py
.\.venv\Scripts\python.exe scripts\audit_historical_war_hurdle_uncertainty.py
```
