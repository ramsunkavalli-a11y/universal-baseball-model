# Rolling opportunity probability calibration

Status: calibration layer rejected; retain raw participation probabilities.

The universal opportunity models were replayed on consistent snapshot-only player
universes for 2022–2025. Each model used only earlier completed training folds. A
logistic intercept/slope calibrator for each target year was fitted only on earlier
rolling forecasts and outcomes; 2022 served as the warmup origin.

On the pooled 2023–2025 evaluation, calibration changed scores as follows:

| Group | Brier delta | Log-loss delta | Decision |
| --- | ---: | ---: | --- |
| Hitters | +0.000245 | +0.001154 | Reject |
| Pitchers | +0.000006 | +0.000010 | Reject |

Positive is worse. Pitcher slopes were 0.993, 0.997 and 0.999 for the 2023–2025
forecasts, showing that the raw probability scale was already close to the rolling
identity line. Hitter calibration chased the direction of the immediately prior
season and was unstable: it raised 2023 probabilities when the observed rate fell,
then reduced 2025 probabilities when the observed rate rose.

Keep the raw participation probabilities. Continue publishing fixed-band reliability
diagnostics, but do not add a blanket calibrator. The separate 30%–60% band concern
can be studied after more origins exist; it is not enough to override better overall
proper scores.

## Conditional active workload

The fitted zero-truncated negative-binomial workload distribution was also checked
without changing its parameters. Its intended P10–P90 range covers 81.8% of 2,644
active hitter outcomes and 80.1% of 3,156 active pitcher outcomes across 2022–2025.
Annual hitter coverage ranges from 79.7% to 83.3%; pitcher coverage ranges from 78.7%
to 81.7%.

This clears the broad conditional-workload range. The undercoverage found in active
WAR is therefore mainly downstream: performance/WAR-rate uncertainty or the method
used to combine rate and workload. Do not widen workload merely to repair WAR.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\audit_rolling_opportunity_calibration.py
```
