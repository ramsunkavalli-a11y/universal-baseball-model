# Hitter explorer with source evidence

The local research explorer now shows the reviewed roster and availability
evidence alongside the same historical forecasts. It covers all 30,506
forecasts, retains the team filter and hitting-only sort, and keeps actual
results and outcome-informed reviews off by default. No model was fitted and
no prediction improved as a result of this display change.

Open the local handoff at `http://127.0.0.1:8792/` while its server is running.
Its artifact is `reports/generated/hitter-qualified-handoff/explorer/index.html`.
The earlier comparative artifact is preserved. This is a historical research
handoff, not a replacement for the frozen 2026 or deployed explorer.

## What can now be inspected

Each player has a separate source panel with the returned year-end listing,
latest narrowly classified transaction, captured availability state, medical
observation scope and missing foreign-production evidence. An evidence filter
finds listing mismatches, unresolved availability, unknown medical coverage,
missing foreign production and unverified origin eligibility.

Of the 30,506 forecasts, 1,165 have listing/event mismatches, 5,216 have covered
medical observation scope, seven have an identified missing foreign-production
flag, and 218 lack the origin eligibility bridge. These are diagnostic source
counts, not confirmed mistakes, complete medical records, or a complete count
of foreign players. Unknown medical coverage is not healthy. An old explicit
transaction cannot certify current reserve rights after ambiguous later moves.

The panel explicitly separates source reliability, earlier training support
and uncertainty about future outcomes. It says that corrected medical and
availability states are not predictors in the current fitted opportunity heads.
Permanent ineligibility and reported retirement remain separate opportunity
rules. No synthetic listing toggle is available as a selectable forecast.

## Browser and population checks

The live browser was checked for the following cases and controls:

- McLain's 2025 forecast remains 131.65 expected PA. The missing returned listing
  and positive dated event are visible as a conflict, not a repaired forecast.
  His October roster activation is not labeled clinical recovery.
- Franco's 2024 forecast remains 559.49 expected PA and roughly 99% appearance
  probability. Administrative leave is visibly unresolved. The probability is
  not presented as legal clearance; this unresolved model gap remains.
- Thames's 2017 forecast remains 20.78 expected PA. The panel distinguishes known
  missing foreign production from zero talent and unknown medical coverage.
- Belt's 2024 forecast remains 244.16 expected PA. Free agency is not relabeled
  retirement or a certain zero outcome. His unusual unsigned outcome does not
  justify a blanket penalty on all free agents.
- MLBAM 808975 remains in the 2025 cohort with its unavailable historical name,
  unknown affiliation and evidence limitations. No later name or signing is
  inserted as a cutoff-known model input.
- The Giants upper-minors filter returns 34 forecasts for 2025. Switching models
  shows 293 expected PA in the original and 322 in the candidate. These are the
  existing cohort totals, not a complete future roster budget.
- The 2025 listing-mismatch filter returns 168 forecasts. It includes established
  stars with intervening signings; the warning is deliberately not proof of a
  broken listing or a reason to overwrite source flags.
- Checking actual results reveals historical outcomes; unchecking hides them.
  Hitting, model switching, season and organization filters remain usable.

Four focused unit tests check unknown evidence, outcome-blind flag decisions,
no automatic availability/foreign zeros, and preservation of the opt-in UI.
The export independently compares every original and exported JSON row: removing
only the added evidence object gives exact equality. Forecasts, histories,
reviews, benchmark scores and probability tables are unchanged. This proves
artifact preservation, not predictive validity or source completeness.

Protected 2026 outcomes did not enter these calculations. The previously
disclosed incidental McLain current-season summary exposure remains a qualification
on any future wholly-unseen-test claim.

## Earlier uncertainty work and the next test

The [paired forest review](practical-hitter-joint-forest-v43-result.md) is complete,
including sixteen player walks. Its point forecasts worsened, its upper-minors
appearance probabilities were too low, and its lower-minors interval coverage
was dominated by the zero-outcome mass. Do not borrow its ranges for the current
model's different means or call them calibrated at all levels.

The [earlier exact mixture](rolling-combined-war-uncertainty-result.md) improved
interval scores in another branch without changing means. It is useful evidence
for separating nonparticipation from active outcomes, but its WAR variance,
workload anchor, cohorts and parameters are not certified for this current
offense candidate. Earlier prospect path ranges also have cohort and chronology
qualifications; they are not a substitute for next-year all-player validation.

The next bounded question is active playing-time uncertainty with fixed current
appearance probabilities and fixed current expected PA. This is a workload-risk
test, not a replacement talent model or full offense distribution. Its contract
must distinguish means from medians, preserve the exact zero mass, estimate spread
from earlier player-separated forecasts, and score interval quality as well as
coverage. Internal forecasts must exclude both the outer tested players and the
inner validation players: simply reusing old held-out predictions from another
fold would allow outer-player information into dispersion estimation.

Use proper distribution scores and actual player checks, not a blanket target
of exactly 80% inclusive coverage for a distribution with many exact zeros.
[Gneiting and Raftery](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)
explain why interval width and calibration must be judged together.
[Meinshausen](https://jmlr.org/papers/v7/meinshausen06a.html) provides the conditional
quantile forest foundation; the earlier ordinary squared-error forest is not
automatically the specialized multivariate distributional method described by
[Cevid and colleagues](https://jmlr.org/papers/v23/21-0585.html).

No new uncertainty fit has run at this checkpoint. Do not use future actual PA
to generate a forecast, require exact means before display, retain non-arrivals,
and inspect active cases and rare prospects separately. Better ranges cannot
waive the current public PA MAE gap, readiness misses, cohort allocation errors
or missing defense, running and control-value layers. The whole goal remains
active.
