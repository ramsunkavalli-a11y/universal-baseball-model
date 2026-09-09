# Phase 2 Model FV and workload preview

**Status:** implemented private preview; not production-confirmed
**As of:** 2026-09-08

## What changed

Phase 2 now derives each player's Model FV from this repository's projected MLB
production. A publication's player grade or rank is never an input. The calculation
keeps three ideas separate:

1. **Talent/outcome:** expected six team-control years of WAR, including arrival risk.
2. **Model FV:** a granular internal score, with the nearest five-point grade shown.
3. **Contract surplus:** controlled production value minus salary and other obligations.

FanGraphs' current hitter/pitcher cohort WAR and dollar table supplies only the common
FV scale and dollar benchmark. Its Top 100 is joined afterward for validation.

For players who have not debuted, six control seasons begin after probabilistic MLB
arrival. Annual active probabilities are overlapping marginal forecasts, not
independent arrival hazards, so the preview conservatively uses their maximum until a
true arrival/survival model is fitted. Conditional hitter workloads use 450 PA for
catchers and 550 PA for other positions. This prevents the catcher positional credit
from being applied as though every catching prospect will receive 600 PA per year.
Risk is already present in the arrival-weighted outcome and is not discounted again.

## Workload correction

The Phase 1 hurdle forecast understated the established-player tail. Phase 2 blends
conditional workload with recent MLB workload using a reliability weight that fades
each future year. It never changes MLB-active probability and gives no MLB anchor to
players without MLB workload.

On the already disclosed 2025 check:

| Group | Phase 1 MAE | Phase 2 MAE | Established bias before | After |
|---|---:|---:|---:|---:|
| Hitters | 29.56 PA | 28.05 PA | -70.01 PA | -12.24 PA |
| Pitchers | 28.76 BF | 28.45 BF | -32.85 BF | -1.92 BF |

The hitter correction is stronger than the pitcher correction because the stronger
pitcher setting overshot the observed workload. This is a disclosed diagnostic, not a
new pristine confirmation.

## Example results

- Logan Webb: 4.58 controlled WAR, 60 displayed Model FV, about $10.2M contract
  surplus. His separate talent benchmark is about $58.8M; his guaranteed salary is
  why those values differ.
- Josuar Gonzalez is expected to fall below the earlier 49.0 FV preview because that
  preview incorrectly accumulated overlapping annual MLB-active probabilities.

The external Top 100 comparison is rerun after every structural correction. It is
diagnostic only and is not used to force individual grades or league counts.

After removing the invalid independent-hazard assumption, 70 pre-MLB players grade
50 or higher, including 22 catchers. The external Top 100 check is now 9.56 FV points
MAE and 17.6% within five points. That worse external match is accepted because the
previous improvement came from invalid probability accumulation. The gap makes a
proper historical arrival/survival model the first priority.

## Next priorities

1. Validate the pre-MLB arrival-as-hazard interpretation on historical prospect
   cohorts and replace it if the transition data disagree.
2. Improve minor-league development paths and pitcher starter/reliever role value.
3. Calibrate outcome intervals and star probabilities from historical six-year paths.
4. Inspect league role/position/FV distributions as diagnostics; never force quotas.
5. Replace the first-future-year market-tier proxy with signing-time talent tiers.

Run the current private build with `play-with-results.cmd`. Generated data remain
ignored; the scripts, tests and methodology are versioned.
