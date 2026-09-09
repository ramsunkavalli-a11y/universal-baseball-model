# Model search and validation policy

**Status:** binding for new feature searches

This policy turns broad feature exploration into a repeatable forecast test. It
applies to demographics and to every later StatsAPI, play-by-play, and derived-data
candidate. A large search is allowed; a candidate does not earn production status
because it won the search that created it.

## Required separation

Keep four questions separate until final path simulation:

1. current skill or talent conditional on playing;
2. arrival, participation, and role probability;
3. future workload conditional on role and availability;
4. control, cost, and contract value.

A feature may enter only the question it can defend. Birth country may describe a
development or signing pathway in an arrival model. It may not directly add batting,
pitching, or WAR talent. Expected skill times expected workload is not automatically
expected production when those quantities are dependent; final assembly must model
that dependence or simulate joint paths.

## Closed playing-time system

Player-level opportunity estimates are not allowed to create extra league playing
time. Before WAR or value is finalized, projected workload must be reconciled within
each organization and season against realistic major-league pools:

- hitter PA compete for a fixed team-season batting pool, with position and catcher
  availability treated as constraints rather than talent bonuses;
- pitcher BF or innings compete for a fixed team-season pitching pool, split across
  starter, swingman, and relief roles;
- replacement players, external acquisitions, injuries, trades, and unfilled future
  roster share remain explicit rather than being silently assigned to prospects;
- increasing one player's allocated workload reduces another player's share or an
  explicit replacement/external share;
- reconciliation changes opportunity and uncertainty, never underlying skill.

League- and team-season conservation checks are required alongside player-level error
metrics. Reject a model that improves individual error by forecasting an impossible
total PA, BF, or innings pool.

Opportunity must be reported in two distinct views:

1. **Organization-neutral opportunity** uses a typical MLB environment and supports
   talent, trade, and long-term contract value. A crowded current depth chart cannot
   make a player less talented or less valuable to another club.
2. **Current-organization opportunity** allocates the club's fixed PA and pitcher
   BF/innings pools using its actual roster, positions, roles, options, injuries, and
   depth. This view supports season and near-term production forecasts.

Organization and depth information may change the second view only. It must never
enter the underlying skill estimate or the organization-neutral value directly.

## Eligible evidence

Every predictor must have been available at the forecast cutoff. Include failures,
non-arrivals, inactive players, and zero future MLB outcomes in the defined player
universe. Do not condition a prospect model on later promotion or MLB participation.
Current profile fields such as height, weight, position, or strike-zone bounds cannot
support historical claims until their historical vintage or invariance is established.

The reusable search framework should support these bounded input families:

- prior performance and evidence volume by competition level and recency;
- age and development history, including movement and inactivity;
- pitcher role, workload, handedness, and defensible pitch/process traits;
- hitter platoon, discipline, contact, power, defense, and baserunning evidence;
- park, league, run environment, opponent, and schedule context;
- stable reported demographics and defensible interactions;
- source coverage and missingness indicators where missingness was knowable then.

Play-by-play additions must beat strong aggregate baselines. Do not require expensive
event-level backfills when season totals answer the predictive question.

## Search procedure

1. State one predictive target, horizon, player universe, and simple incumbent.
2. Freeze a bounded feature/interaction and regression grid before scoring it.
3. Use rolling calendar folds, never a random player-season split.
4. Embargo an evaluation origin until its entire outcome horizon is observable.
5. Select features and shrinkage using only completed earlier origins.
6. Fit the one selected candidate on the allowed history and judge it once on the
   later outer origin. The outer cohort must be identical for candidate/incumbent.
7. If researchers already inspected the outer result while designing the family,
   label it retrospective development evidence, not confirmation.
8. Confirm the frozen candidate on a genuinely later untouched period before use.

This nested design controls a broad search by exposing only one selected candidate to
the outer comparison. Reopening the grid after seeing the outer result spends that
comparison and requires another later confirmation.

## Scoring and stability

Use log loss and Brier error as primary probability scores. Report predicted versus
observed rates, calibration intercept/slope, and equal-count reliability groups.
Correlation and ranking may be secondary; they cannot authorize a probability model.

Use paired player-level uncertainty on candidate-minus-incumbent error. Inspect level,
age, evidence volume, role, handedness, source tier, and other supported groups. A
group should ordinarily have at least 100 observations and five positive outcomes
before it is treated as evidence; smaller groups remain descriptive. Reject complexity
that is unstable, materially harms a supported group, or produces only immaterial
aggregate benefit.

Sparse effects require regression toward the relevant comparison population. Search
regression strength inside earlier folds. Never read an unregressed small-country,
small-level, or survivor-only rate as player talent. Aging and level translations must
also account for survivor selection, changing populations, and regression—the core
warnings in Tango's adjacent-season and MLE work.

## Promotion rule

A new model must improve both primary scores on its outer test, remain reasonably
calibrated, avoid material supported-subgroup damage, and have a baseball-coherent
explanation. Small or mixed gains stay research-only. Production player values do not
change until a frozen candidate passes fresh confirmation.
