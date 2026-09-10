# Historical 2025 WAR uncertainty coverage result

**Status:** completed diagnostic; Phase 1 ranges remain sensitivity bounds, not
probability claims

The frozen March 27, 2025 central 80% WAR ranges were compared with completed 2025
outcomes using the same neutral WAR definition. The forecast did not use 2025
outcomes, all forecast-universe players remained in the score, and players without
2025 MLB workload were observed zeroes. No interval was clipped or changed.

## Main result

| Group | Players | Coverage | 95% Wilson interval | Lower miss | Upper miss |
|---|---:|---:|---:|---:|---:|
| Hitters, all | 3,891 | 96.9% | 96.3%–97.4% | 0.9% | 2.2% |
| Pitchers, all | 5,090 | 95.9% | 95.3%–96.4% | 1.4% | 2.7% |
| Whole player, all | 8,946 | 96.3% | 95.9%–96.7% | 1.2% | 2.5% |
| Hitters who appeared | 667 | 82.0% | 78.9%–84.7% | 5.2% | 12.7% |
| Pitchers who appeared | 801 | 73.7% | 70.5%–76.6% | 9.0% | 17.4% |
| Whole players who appeared | 1,467 | 77.4% | 75.2%–79.5% | 7.3% | 15.3% |

The full-universe result is not evidence of excellent 80% calibration. All 7,479
whole-player nonparticipants had zero inside their range. That structural point mass
dominates aggregate coverage. Conditioning on realized activity is also not a valid
standalone calibration target because activity is learned after the forecast, but it
is a useful diagnostic: the continuous part is materially less secure than the full
roster number suggests.

Among forecast-time workload groups, the most established rows behaved better:

- hitters at 300+ expected PA covered 89.7% (235/262);
- pitchers at 300+ expected BF covered 84.7% (155/183), with 80% inside the Wilson
  interval;
- pitchers at 100–299 expected BF covered 85.4% (356/417);
- low-workload groups strongly overcovered because their symmetric ranges nearly
  always included zero.

Misses were more often above the upper endpoint than below the lower endpoint. Among
active pitchers, 17.4% beat the upper endpoint while 9.0% fell below the lower one.
This is consistent with the range compressing an arrival/workload mixture into one
symmetric Normal band; it does not by itself identify a scale correction.

## Decision

Do not advertise the Phase 1 output as an empirically calibrated central 80%
probability interval. Keep its existing **sensitivity range** label. Do not tune a
multiplier on this single 2025 result.

The reusable audit now also reports the proper interval score and fixed forecast-time
participation reliability bands. Overall participation probability is close, but both
hitter and pitcher forecasts understate the observed return rate in the 30%–60% band.
See the [probability calibration result](forecast-probability-calibration-2025-result.md).

Phase 2 should represent the two-part process explicitly:

1. a discrete probability of no MLB appearance;
2. a conditional distribution for workload and performance after arrival;
3. asymmetric quantiles from the combined distribution rather than a symmetric
   Normal interval;
4. rolling-origin development followed by an untouched later confirmation period;
5. calibration reported both unconditionally and by forecast-time probability and
   workload bands, never only after conditioning on realized activity.

This follows the core Tango-style separation between playing time and rate talent,
keeps regression tied to evidence, and avoids turning a descriptive subgroup miss
into an after-the-fact model rule.

## Boundary

This is outcome-cutoff-safe but not a claim that the March artifact recreates every
piece of information exactly as it existed on March 27. It tests one MLB season and
the model's neutral WAR components. It does not test published WAR, defense,
baserunning, future-position error, cross-season correlation or a full career value
distribution.
