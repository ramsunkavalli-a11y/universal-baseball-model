# Park and opponent component: final result

Status: **complete as a model input; not promoted as a forced player correction**

## Bottom line

UBM is measuring real park effects. It generally agrees with Baseball America
and FanGraphs about which parks help or suppress each kind of hit. The numbers
are not supposed to match exactly because the systems answer slightly different
questions and use different amounts of history.

The affiliated estimator also improved prediction of the next season's home
environment in both tested years. But directly correcting player stat lines with
those estimates did not consistently improve next-season player forecasts.
Therefore, the completed component gives the gradient model park context and its
reliability; it does not overwrite the current hitter or pitcher forecast.

## What UBM estimates

For singles, doubles, triples, homers, and the other terminal outcomes, UBM
estimates how the probability changes at each venue after accounting for the
quality of the opposition. The event-level MLB check additionally accounts for
the identities of the batter and pitcher and their handedness. All outcomes are
estimated together, so increasing one outcome necessarily takes probability
from another instead of creating impossible totals.

For a future player row, only a factor fitted through an earlier season can be
attached. A new or unobserved park receives neutral effects, zero reliability,
and an explicit `park_factor_known = false` flag. The player model sees the raw
and park-context versions separately and decides from past-to-future validation
whether the adjustment helps.

## Baseball America comparison

The like-for-like comparison uses the same 2022-2023 period and 119 matched
full-season minor-league parks. Baseball America's published values are direct
home/road factors. UBM additionally adjusts the schedule's opponent mix and
shrinks estimates based on sample size.

| Outcome | Pearson agreement | Rank agreement | Same side of neutral | Average index gap |
|---|---:|---:|---:|---:|
| Overall offense | 0.926 | 0.901 | 94% | 2.9 |
| Home runs | 0.923 | 0.912 | 88% | 10.3 |
| Doubles | 0.864 | 0.821 | 81% | 5.8 |
| Triples | 0.827 | 0.813 | 81% | 16.3 |
| Singles | 0.669 | 0.671 | 79% | 3.3 |

This is strong agreement. The largest differences are mostly triples, which are
rare and therefore unstable. Baseball America's estimates are much more extreme:
for example, its home-run indexes have a standard deviation of 23.4 points,
versus 12.7 for UBM. That is expected from raw home/road results versus UBM's
opponent adjustment and 5,000-opportunity shrinkage.

Examples illustrate scale rather than a basic directional conflict. Baseball
America rates Charlotte at 157 for home runs while UBM gives 123; it rates Lake
County at 153 while UBM gives 119. UBM agrees that both are strong homer parks,
but is less certain about the size.

## FanGraphs comparison

The MLB diagnostic uses 182,765 regular-season 2024 plate appearances and 29
matched primary parks. It does not use launch angle, exit velocity, or any other
Statcast contact-quality measurement. UBM fits one season while the FanGraphs
comparison values are multi-year, regressed factors. FanGraphs publishes the
factors already halved for applying to a full-season player line, so they were
converted back to full in-park effects before comparison.

| Outcome | Pearson agreement | Rank agreement | Same side of neutral | Average index gap |
|---|---:|---:|---:|---:|
| Singles | 0.858 | 0.843 | 96% | 3.1 |
| Doubles | 0.762 | 0.754 | 96% | 7.2 |
| Triples | 0.793 | 0.780 | 79% | 14.6 |
| Home runs | 0.726 | 0.735 | 79% | 7.1 |

Again, the broad signal agrees. The largest disagreements are concentrated in
one-season and rare-event estimates: Fenway and Houston triples, Cleveland
doubles, and the 2024 home-run estimates for San Diego and the White Sox. These
are plausible differences from time window, changing personnel, weather, park
configuration, and random variation; this audit cannot assign one cause to each
park.

The MLB one-season venue term did **not** improve prediction of plate appearances
from August 15 onward after the batter, pitcher, and hands were already included.
Log loss was worse by 0.000008 and Brier score by 0.000094. That is a useful
rejection: the descriptive 2024 effects track FanGraphs, but a one-season fixed
effect is too noisy to promote as a standalone event predictor. Multi-year
pooling remains necessary.

## Internal future-season evidence

The existing affiliated model uses a 5,000-opportunity prior selected on 2024 and
then held unchanged for 2025. Negative score changes are improvements.

| Model use | 2024 log loss | 2024 Brier | 2025 log loss | 2025 Brier | Decision |
|---|---:|---:|---:|---:|---|
| Hitter environment | -0.000446 | -0.000050 | -0.000437 | -0.000107 | Pass |
| Pitcher environment | -0.000466 | -0.000141 | -0.000558 | -0.000173 | Pass |
| Correct hitter stat line | -0.000046 | -0.000011 | +0.000019 | -0.000017 | Reject |
| Correct pitcher stat line | -0.000296 | -0.000084 | -0.000146 | +0.000029 | Reject |

This resolves the apparent contradiction. Parks matter and UBM can measure them,
but a useful context measurement does not guarantee that subtracting its full
estimate from every player improves the next player forecast.

## Why UBM is allowed to differ

- **Different purpose:** raw observed environment, neutral talent, and future
  performance are three different targets.
- **Different history:** FanGraphs uses a multi-year regressed MLB window; the
  MLB UBM diagnostic used one year. Baseball America used a two-year raw split.
- **Different personnel handling:** UBM removes opponent mix and, at MLB event
  level, controls batter, pitcher, and handedness rather than assuming schedules
  and rosters cancel perfectly.
- **Different shrinkage:** UBM pulls low-information parks and rare outcomes
  toward neutral, especially in the minor leagues.
- **Different probability structure:** UBM estimates an exhaustive set of
  outcomes jointly. Published one-outcome ratios do not have to sum to a valid
  plate-appearance distribution.
- **Remaining omitted context:** weather, temporary venue changes, and park
  configuration eras are not yet modeled. These are candidates only after their
  historical coverage and chronology can be guaranteed.

## Final decision and next use

The park/opponent component is complete for the next hitter-gradient experiment.
The approved inputs are prior-vintage component effects, park sample strength,
number of training seasons, reliability, and whether the park is known. The model
will project neutral player skill first; destination-park effects can be applied
separately when a future team/venue is actually known.

No existing player projection changes from this work. Promotion requires the
full next-season player gate, including level advancers, park movers, established
players, and small samples. No 2026 outcomes were used.
