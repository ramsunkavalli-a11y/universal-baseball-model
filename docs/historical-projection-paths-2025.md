# Historical 2025 projection paths

Status: Phase 1 retrospective replay input, not a promoted ranking.

The first 2025 Opening Day projection path is now materialized at the March 27,
2025 event cutoff. It covers 3,891 hitters and 5,090 pitchers for 2025–2029.
Thirty-five two-way players retain separate hitter and pitcher components.

## What was built

- The selected one-year hitter and pitcher opportunity forms were refit using only
  the 2018, 2021, 2022 and 2023 snapshots and targets through 2024.
- Those fits score 2025. Pre-2025 age/level/role references supply 2026–2029.
- Conditional WAR rates use official MLB components through 2024 and the 2024
  league environment.
- FanGraphs Opening Day projected PA/IP are comparison data only. They are not
  predictors, targets or automatic overrides.
- The 2025 workbook adds 8 hitters and 24 pitchers absent from the official 2024
  snapshot. Those players receive labeled population opportunity fallbacks.
- Baserunning and defense remain average-zero Phase 1 fallbacks in this replay.
  Affiliated-to-MLB rate translation is also omitted to avoid later-fit leakage.

The build is retrospective event-cutoff evidence, not a vintage-information claim.
The underlying FanGraphs and contract files were obtained later.

## Scale check

The 2025 model allocates 183,343 expected hitter PA and 180,383 expected pitcher BF
across the full player universe. Against the players with FanGraphs projections, the
model is more conservative: mean expected PA is 245.9 versus 302.5, and mean expected
BF is 182.0 versus 288.1 after converting FanGraphs IP with the 2024 league BF/IP
ratio. Mean absolute differences are 159.8 PA and 153.0 BF.

This does not establish which player allocation is better. It shows that the model
roughly closes the league workload while spreading more probability to the broader
universe than the Opening Day depth chart does. Outcome scoring comes later and must
remain separate from this scale comparison.

## Remaining work

Join the 2025 Opening Day service/options baseline and the gated Cot's-derived annual
terms to these paths. Guaranteed salaries can be valued, arbitration rows use the CBA
calculation, free-agent rows end control and unresolved identities/options stay in
review. That join is the next Step 8 checkpoint.

Reproduce with:

```text
python scripts/materialize_historical_projection_paths_2025.py
```

Generated private outputs live under
`reports/generated/historical-projection-paths/2025-03-27/`.
