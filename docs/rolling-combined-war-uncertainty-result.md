# Rolling combined WAR uncertainty

Status: passed and promoted to the private playable build.

The complete annual range now combines three separate pieces: the chance of no MLB
activity, workload conditional on activity, and performance conditional on workload.
Participation remains raw, workload spread remains unchanged, and the performance
scale is learned only from earlier completed forecast origins.

On pooled 2023–2025 forecasts, the exact mixture beats the prior single bell curve:

| Component | Old interval score | New interval score | Improvement |
| --- | ---: | ---: | ---: |
| Hitters | 0.912 | 0.734 | 19.5% |
| Pitchers | 0.621 | 0.502 | 19.2% |

The challenger improves interval score in every individual year from 2022 through
2025 for both hitters and pitchers. Point estimates are identical. Overall coverage
falls from 97.0% to 94.3% for hitters and from 96.1% to 93.9% for pitchers. Coverage
remains above 80% because the discrete zero outcome makes exact nominal coverage
impossible for many low-activity players; the proper interval score is the controlling
comparison.

The playable build uses a moment-matched positive-workload gamma because the current
workload anchor intentionally scales the original count distribution into continuous
exposure. Single-component player ranges retain the simulated percentiles. The 22
known two-way players retain an independent-moments combination until a joint
simulation is worthwhile. Displayed ranges are minimally extended when needed to
contain the expected value required by contract economics.

No projected WAR mean, Model FV, contract status, salary or prospect grade changed.
The change affects uncertainty and the low/high contract-value sensitivity only.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\audit_rolling_combined_war_uncertainty.py
```
