# Historical 2025 WAR uncertainty coverage plan

**Status:** frozen before scoring

## Question

Do the Phase 1 central 80% annual WAR reference ranges behave like useful uncertainty
ranges in the first available out-of-time season?

This is a calibration audit, not a model-selection search. It may relabel the ranges
or motivate a later multi-season challenger, but it may not tune the current ranges
against 2025.

## Chronology and target

- Forecast: the frozen March 27, 2025 projection and uncertainty artifacts.
- Target: completed 2025 outcomes.
- The forecast artifact must state that it did not use 2025 outcomes.
- Forecast and outcome WAR use the same neutral event weights, 2024 run environment,
  projected position, average-zero baserunning and average-zero defense.
- Every player in the forecast universe remains in the score. Missing 2025 MLB
  workload is an observed zero, not a dropped row.

This target is intentionally narrower than published WAR. It isolates uncertainty in
the model's own opportunity and event-rate components instead of mixing in a second
WAR definition.

## Frozen checks

For hitters, pitchers and combined whole-player WAR, report:

1. central 80% empirical coverage and a 95% Wilson interval;
2. lower-tail and upper-tail miss rates;
3. median and 90th-percentile interval width;
4. mean standardized error and root-mean-square standardized error;
5. the same diagnostics for observed-active and observed-inactive players.

Also report predeclared forecast-time workload slices:

- hitters: expected PA `<1`, `1-99`, `100-299`, `300+`;
- pitchers: expected BF `<1`, `1-99`, `100-299`, `300+`;
- both components: the existing forecast `coverage_tier`;
- pitchers: the existing forecast `projected_role`.

Slices below 30 players are descriptive and cannot support a decision. No slice is
chosen after observing its result.

## Interpretation

The nominal 80% target is considered plausible when 0.80 lies inside the Wilson
interval. A clear miss is reported when the full Wilson interval is above or below
0.80. Tail imbalance and standardized errors diagnose *how* it misses; they do not
authorize an after-the-fact scale factor.

Because this is one MLB season, passing does not establish universal calibration and
failing does not identify a unique repair. Any promoted repair needs rolling-origin
development and a later untouched confirmation period. Cross-season correlation,
future position error, defense, baserunning, injuries and published-WAR disagreement
remain outside this audit.

## Statistical guardrails

- no result-based row removal or interval clipping;
- no future team depth or 2025 outcome leakage into the forecast;
- no treating repeated player-season rows as independent evidence;
- no claim that a Normal moment interval is a fully simulated probability distribution;
- no parameter search on the confirmation season;
- retain both aggregate and meaningful subgroup failures in the report.
