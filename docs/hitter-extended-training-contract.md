# Testing earlier training histories for hitter projections

2026-10-04. Compare the same next-year hitter models with and without the
reviewed 2008–2010 forecast origins. The purpose is to improve future MLB
playing time, batting ability and delivered batting value, especially readiness
errors for advancing prospects. More rows alone are not evidence of improvement.
This contract precedes fitting. The practical hitter plan remains controlling.

## Fixed population and comparison

Retain all 30,506 current evaluation forecasts at origins 2016–2018 and
2021–2024, including inactive players and every non-arrival. Keep the current
63,282 training-source rows and add all 13,357 reviewed earlier rows, not only
successful or famous players. Older target seasons are 2009–2011. Every actual
fold excludes the entire held player's fold and outcomes after its information
cutoff; the 2020 target remains excluded. Forecasts use coming-season preseason
rankings where certified, not future season results. Their existing retrospective
publication-vintage qualification remains.

Fit a restricted and an extended arm with identical feature definitions and
settings. Restricted uses only the original source; extended additionally uses
the earlier rows. Preserve the unchanged current candidate and the reviewed
translated/ranking rate alternative as separate anchors. Do not change evaluation
inputs, labels or identities to accommodate early coverage. Apply both fitted
arms to the whole evaluation population, reporting never-debut players separately.
No post-result routing, tuning or selective age/level augmentation is permitted.

Opportunity uses the existing 251 inputs plus two explicit provenance flags:
roster coverage known and debut elapsed unknown. Hitting uses the existing 199
inputs plus those same flags. Both arms use the existing depth-three histogram
classifier for any MLB PA, histogram regression for active PA and Ridge alpha
100 for active batting rate. Keep 250 iterations, minimum leaf 30, learning rate
.05, L2 10, seed 31 and no early stopping. Equal-origin weights and normalized
actual-PA rate weights remain unchanged. Adding origins changes their relative
training weight under that fixed rule; this is part of the training-history
comparison, not a claim about independent new player identities.

## Consistent inputs and missing information

Use three calendar years of raw counts, separate levels and rookie leagues,
recency weights 1/.8/.6 and the existing fixed event priors. Reconstruct games
and PA per game from archived captures and require exact count reconciliation.
Use the already reviewed birth-date repair; the one remaining unknown age stays
flagged, with the existing numeric placeholder rather than a claim of known age.

The 2008 roster listing is unknown: encode on-40-man as -1 and coverage-known
as 0. For reviewed 2009–2010 listings and all current source origins use the
existing soft listing convention with coverage-known 1. Listings are not
certified legal rights, guaranteed health or actual jobs. Unknown early prospect
rankings preserve the existing unavailable/unknown representation; missing
rankings are never classified as unranked. The available 2011 preseason list
may enter origin 2010, with its 50-player capacity.

Only an official debut date no later than origin may determine debut elapsed.
If earlier observed MLB PA prove participation but no such date is recorded,
mark prior participation, leave elapsed numerically unknown (-1) and set the
explicit elapsed-unknown flag. Do not use existence of a later debut date or
the source audit's future-debut outcome category as predictors. No observed MLB
history is not an official certificate of never having appeared before 2004.
Report that coverage limit rather than selecting players using later success.

Preserve the current career-PA definition: sum primary MLB history beginning
in 2008; earlier lag counts do not silently extend that separate career input.
Preserve the corresponding left-truncation convention and document its limits.
For 2006–2008 lagged MLB batting quality, reconstruct the same fixed-event
season-centered batting runs directly from certified MLB counts. Subtracting
replacement cancels the schedule term; do not invent early future-value labels.
Early workload uses the existing nominal full-season convention. Verify the
reconstructed batting formula against overlapping 2009 labels before fitting.

The new runner consumes the sealed older-source tables and defines its own
static level mapping. It must not depend on the unrelated dirty source-mapping
module, modify old sealed helpers or claim that earlier source construction was
already reproducible from a bare checkout.

## Preflight and scoring

Persist all 210 actual arm/head chronological and held-player preflights before
fitting. Count distinct people in broad and refined age, level, ranking, exposure
and draft profiles, with full and active subsets separate. Preserve unsupported
forecasts in headline scores. All current inputs remain bit-identical apart
from the two newly declared provenance flags; all evaluation labels are exact.
Require finite features, source and model hashes, saved-fit replay and correct
probability and PA/value arithmetic.

Primary contrast is extended versus restricted delivered-value error, with PA
RMSE/MAE, appearance Brier/log loss and active rate error reported separately.
Use equal target-year weighting; rate scores use actual PA within year. Save
player-clustered nominal paired intervals, origins, stages, never-debut,
established and matched public samples, with raw cohort totals. Preserve current
and translated anchors. The original rate labels are centered on the realized
target season; the scored delivered-value labels use the existing common-origin
environment. Do not confuse these two rate columns. Value is fixed-event
batting plus replacement in custom win units, not full WAR or club-control value.

Inspect 2021, recent versus early origins, upper/lower minors and unsupported
DSL/teenage AAA profiles. A small overall gain cannot excuse a repeated readiness
miss, harmful mechanism or materially worse public comparison. Exposed historical
results and intervals are development evidence, not fresh confirmation.

## Required player review and disposition

Before disposition, walk through Kurtz 2024, Langford 2023, Alonso 2018, Acuna
2017, Julio Rodriguez 2021, Holliday 2023, Judge 2024 and a teenage DSL case.
Add the largest gain, harm, false high, false low and an ordinary active case,
allowing overlap. Trace dated statistics, all actual inputs, saved tree paths
and Ridge terms, appearance, conditional PA, rate, value and next-year reality.
Select four peers by origin-known age, level exposure, position, pedigree and
performance without future outcomes; sparse matches remain visibly sparse.
Do not explain a major miss away using dissimilar peers' zero outcomes.

Keep the current candidate unless the matched effect, player mechanisms and
meaningful cohort evidence support a coherent improvement. A failed test rejects
neither historical data generally nor a different readiness model. No protected
2026 outcomes, frozen forecasts or deployed explorer change. Completion of this
experiment is not completion of the full practical hitter goal.
