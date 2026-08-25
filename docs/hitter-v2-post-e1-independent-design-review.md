# Hitter v2 post-E1 independent design review

Status: **DESIGN REVIEW COMPLETE; NO NEW CANDIDATE AUTHORIZED**  
Date: 2026-08-24

## Executive conclusion

Hitter v2 is still on a viable path to useful projections, but not by adding
more season-level contact-bin percentages to C0. The next credible candidate
should be a **joint contextual terminal-outcome model**. It should estimate
player outcome skill while treating pitcher quality, platoon, park,
league/level, and measurement source as nuisance context, then project the
neutral player effects forward with age and level transitions. Contact shape
and tracking should enter only as separately reliability-weighted measurements
of those latent component skills.

The universal production backbone remains ordinary PBP terminal outcomes.
This is not a retreat to age alone. It is a decision to extract more signal
from who the player faced, where and under which handedness context before
asking sparse or noisy process measurements to improve the forecast.

No result in this review authorizes a fit, a score, E2, tracking promotion,
2026 access, Stage 3, or WAR.

## What E1 did and did not establish

E1 asked a narrow, sensible baseball question: after prior terminal outcomes,
do shrunk `OFFB/contact` and `pulled OFFB/OFFB` histories improve future
`HR/contact`? In the frozen implementation, the answer was no in three of four
required fold/weighting comparisons.

That result does **not** show that pulled air contact lacks value. FaBIO's bins
describe completed-play tendencies, and pulled air balls are plainly valuable.
The result shows that two aggregated shape residuals, used as a small additive
correction to C0, did not provide stable incremental next-year HR information.

Four explanations remain observationally entangled:

1. prior HR outcomes already capture most of the stable public PBP power signal;
2. the available direction/trajectory classifier is noisy across source systems;
3. season-level aggregation loses batter-side, opponent, pitch, count, and
   within-season development information; and
4. the coefficient regularization was not expressed on a scale-invariant or
   baseball-effect scale.

The disclosed results cannot now select among repairs to E1. Any future design
must address these issues prospectively rather than retuning the failed model.

## A concrete regularization problem found in code review

Stage 2c used already-shrunk, context-centered log-odds features whose standard
deviations were only about `0.10–0.14`. It minimized mean per-contact log loss
plus:

`0.5 × mean(coefficient²)`

This has two undesirable properties:

- changing only the units of a feature changes the effective prior; and
- a coefficient of 1.0 costs roughly 0.25 objective units when only one of two
  coefficients is nonzero, vastly larger than the observed per-event loss
  improvements under consideration.

The resulting E1 coefficients were `0.00017–0.00176`, and the largest terminal
probability change on a selection fold was only `0.00005595`. The frozen run
therefore tested an almost-zero increment. This does not invalidate its binding
failure: the penalty was preregistered, and changing it now would be outcome-
informed rescue tuning.

For a genuinely new model, regularization must instead be defined by one of:

- training-only standardized predictors with a frozen prior on standardized
  effect size;
- a hierarchical prior stated as a plausible log-odds or probability change
  between fixed predictor quantiles; or
- empirical-Bayes variance components estimated only from earlier origins.

The same transformation must produce the same effective prior after a harmless
change of input units.

## Literature synthesis

### Outcome components remain the center of gravity

Marcel's enduring lesson is not that age alone is strong. It is that a hard-to-
beat forecast combines multi-year outcomes, recency, regression, and age.
ZiPS describes its core as estimating a present baseline and then an aging
trajectory from comparable careers; it also retains long-run minor-league
translations. OOPSY likewise starts with traditional outcome components and
adds league environments, major-league equivalencies, parks, age, recency, and
component-specific regression before richer measurements.

This supports preserving the outcome simplex as the universal forecast and
making every richer source prove incremental value on the identical cohort.

### Age relative to level belongs in the prior, not as a blanket multiplier

KATOH found age, ISO, K%, and BABIP informative even in the lower minors, while
BB% and stolen-base inputs were less useful below Double-A. OOPSY explicitly
uses age relative to level to set different regression means. Jensen, McShane,
and Wyner show why partial pooling across players and time is preferable to a
single deterministic age adjustment.

The next model should estimate component-specific age/development surfaces by
level and evidence, with strong pooling. It should not apply one global age
multiplier to all positive outcomes.

### Context correction and projection are different tasks

Jonathan Judge distinguishes DRC's context-adjusted estimate of contribution
from a projection system. DRC-style batter, pitcher, park, and platoon effects
can improve the estimate of what a player did, but forecasting still requires
multi-season player persistence, regression, aging, and translation. The next
model should use event context to debias the player signal, not substitute an
in-sample deserved-performance metric for a forecast.

### PBP can add value without contact direction being the first increment

Dan Szymborski has publicly described a minor-league BABIP model using only PBP
with substantial explanatory power. Published matchup models likewise model
ground-ball and ground-ball-hit probabilities from batter/pitcher PBP context.
These precedents favor event-level batter, pitcher, handedness, and contact
context over a two-feature season-summary residual.

### Rich tracking is useful but remains a capability tier

OOPSY uses barrel rate and bat speed while keeping traditional components
central. The repository's earlier tracking challenger found stable forward EV
signal but failed its complete confirmation gate on MAE/calibration. The proper
response is a calibrated reliability-weighted tracking measurement with exact
PBP fallback, not making tracking availability define the player population.

## Recommended Stage 2d architecture

This is a design recommendation, not a frozen development contract.

### Layer A — universal terminal-outcome history

Retain the exhaustive Hitter v2 terminal taxonomy and nested component
factorization. Estimate player effects separately for:

1. `K / PA`;
2. `UBB / non-K`, with IBB modeled separately from neutral batting talent;
3. `HBP / eligible non-K non-BB`;
4. `HR / contact`;
5. `reach / non-HR ball in play`;
6. `1B / hit in play` and `2B/3B` composition; and
7. `MULTI_OUT / actual GIDP opportunity`.

Keep outcome probabilities coherent by reconstructing one normalized simplex.

### Layer B — event-context measurement model

At each chronology-safe PA, separate the batter effect from:

- pitcher quality estimated out of fold and only from prior events;
- batter side × pitcher hand;
- league-season-level environment;
- park/venue with handedness where supported;
- source/capability tier; and
- limited game-state terms needed to make event definitions comparable, not
  to reward lineup context.

Pitcher identity is a grouping key, never a transferable player-name feature.
For pitchers without sufficient prior evidence, use a level-season prior.
Pitcher height, country, or target-year results are not substitutes for prior
pitcher quality.

### Layer C — forward development and translation

Project the neutral batter effects one season forward using:

- component-specific recency and persistence;
- age relative to level with partial pooling;
- chronology-safe mover translations;
- uncertainty that grows for sparse and disconnected level paths; and
- no target-season membership, PA, park, centering, or run environment.

### Layer D — optional PBP process measurements

Only after A–C freeze, test whether event-level side-specific direction/
trajectory measurements improve the same future component targets. Do not use
the ten bins as terminal-value substitutes. Prefer measurements such as:

- pulled air opportunity and success by batting side;
- air-ball versus ground-ball tendencies conditional on pitch/opponent context;
- opposite-ground reach conditional on speed and defensive-era context; and
- within-season trend only if its cutoff and minimum evidence are frozen.

Missing measurements produce exactly the A–C forecast.

### Layer E — optional tracking fusion

For source-certified overlap players, estimate a residual using EV, LA,
distance, barrel/hard-hit, bat speed, plate discipline, or sprint speed. The
fused prediction must be:

`PBP prediction + reliability × tracking increment`

where reliability is a smooth function of event count, recency, source quality,
and stability. Removing tracking must reproduce the PBP prediction exactly.

## How the user's proposed inputs should be routed

| Input | Decision | Rationale |
|---|---|---|
| Height | low-priority age/trajectory interaction | ZiPS uses it only to a lesser extent and warns that public physical data are poor; not a direct talent score |
| Weight | defer | stale and inconsistently updated; no certified repo source |
| Prior lineup slot | separate organizational-belief prior for sparse minor leaguers | may contain information, but is endogenous to recent performance and team context |
| Games/PA as a teenager | opportunity/durability plus age-to-level evidence | informative about availability and organizational assignment, not a direct bonus to batting rate |
| Pitcher age/quality faced | opponent-context correction | useful only with prior-only, cross-fitted pitcher estimates; never use target outcomes |
| Pitcher height | defer behind observed pitch quality | mechanism is indirect and the universal source is absent |
| Country of origin | exclude as a talent predictor | risks encoding acquisition and opportunity systems rather than baseball skill |
| Estimated distance | optional tracking/enriched-PBP residual | only 18.47% affiliated coverage and nearly co-available with EV in the audited source |
| Batter/pitcher handedness | high-priority universal context audit | canonical PBP already carries both fields |

## Repository readiness

The accompanying `docs/hitter-v2-post-e1-source-readiness.json` records the
field-by-field audit. The short version is:

- ready now: terminal outcomes, dates, player/game/league/level identities,
  parks, age, movement histories, batter side, pitcher hand, pitcher identity;
- usable after a source/chronology audit: opponent-quality summaries and
  lineup slot;
- already available only as an optional tier: EV, LA, pitch characteristics,
  and distance;
- absent as certified model inputs: height, weight, country, and sprint speed.

## Prospective development sequence

1. Freeze a target-free source audit for matchup handedness, pitcher identity,
   and prior-only opponent-quality coverage by season/level.
2. Audit the existing C1 damage path and separate translation, age, park, and
   movement effects rather than carrying the combined adjustment forward.
3. Specify a joint nested mixed-effects model with priors stated in effect-size
   units and invariant to predictor rescaling.
4. Implement Layer A–C with synthetic invariants and exact missing-context
   fallback, without loading evaluation outcomes.
5. Use disclosed 2022–2024 only for development and model criticism; never
   relabel them as confirmation.
6. Freeze one candidate, hyperparameters, scorer, artifact hashes, and a
   one-shot confirmation rule before requesting 2026 access.
7. Require the new PBP-only candidate to beat B0/B1 in proper scores and future
   wOBA/runs, with component calibration and supported-level guardrails.
8. Only after the PBP candidate passes, test side-specific contact shape as an
   ablation on the identical cohort.
9. Then test tracking fusion on identical overlap players with exact fallback.
10. Proceed to baserunning and WAR only after the universal PBP rate gate passes.

## Exact next gate

The next authorized work should be **source-only matchup-context readiness**:
measure batter-side, pitcher-hand, pitcher-identity, and chronology-safe prior
pitcher-quality coverage without fitting a hitter candidate or loading a future
offensive target. A separate explicit review must approve that gate before any
Stage 2d development contract is frozen.

## References

- Tom Tango, Predictive wOBA:
  <https://tangotiger.com/index.php/site/article/introducing-predictive-woba>
- Dan Szymborski, ZiPS introduction:
  <https://blogs.fangraphs.com/the-2021-zips-projections-an-introduction/>
- Jordan Rosenblum, OOPSY introduction:
  <https://blogs.fangraphs.com/yet-another-projection-system-a-brief-introduction-to-oopsy/>
- Chris Mitchell, KATOH and prospect forecasting:
  <https://blogs.fangraphs.com/chris-mitchell-on-katoh-and-forecasting-prospects/>
- Jonathan Judge, DRC discussion:
  <https://legacy.baseballprospectus.com/chat/chat.php?chatId=1511>
- Jensen, McShane, and Wyner, hierarchical hitting model:
  <https://arxiv.org/abs/0902.1360>
- Healey, PBP ground-ball matchup models:
  <https://journals.sagepub.com/doi/10.3233/JSA-160025>
- Matt Collier, FaBIO archive and methodology descriptions:
  <https://www.rotoballer.com/author/matthew.collier/page/2>
