# Forecast plausible MLB positions without confusing them with talent

2026-10-07. Preserve the reviewed defensive-time estimate, but replace fixed
minor position shares with supported MLB position distributions. A minor CF
can arrive in a corner and a minor SS at 2B. This comparison addresses where
a player fields, not whether he fields well or reaches MLB.

## Fixed comparison and information dates

Keep all 12,432 forecasts at origins 2022–2024, their player folds, following
season official outcomes and unchanged expected PA. Preserve all earlier
anchors, including the repertoire repair. Reuse its scalar total potential
outs, DH-start forecast and native opportunity conversions exactly. No new
talent, arrival or playing-time fit; no 2026 outcomes, deployment or explorer
change. These already inspected historical years are development evidence.

Use the existing cutoff-known PA/debut fields from the same readiness cache
and audited official/minor fielding history. Join by row ID and player/origin;
verify both identities and current PA before use. The older cache's finite
return/rehab classification remains an upstream limitation, not a new label.

## Individual evidence and position development

Use the preceding three calendar years only. MLB evidence PA is
`pa_0 + 0.5*pa_1 + 0.25*pa_2`; its weight is that amount divided by that amount
plus the already fixed 100-PA stability sample. Do not tune this constant.
Canceled 2020 minor play is not a measured zero defensive season.

Keep the prior repair's individual position vector except when current MLB
PA is zero and older MLB fielding exists in that window. For that return use
the most recent older MLB defensive season, not a minor rehab assignment.
Its primary role comes from the same season's starts, or outs if no starts
are present. This distinguishes an established return from a first arrival
without manually correcting a named player's future position.

Learn one future eight-position out-share vector per **exclusive** dominant
origin role and prior-MLB status. Status means the cutoff-known `prior_debut`
flag, not eventual arrival. Training remains the earlier fixed chronological,
held-person-disjoint conditional-PA population; restrict its transition
subpopulation to positive official future defensive outs. Nonarrival is
unknown position conditional on fielding, not evidence of poor skill; all
nonarrivals and exits remain in the delivered-opportunity score.

Try exact role/status, then exact role. Require 20 distinct contributing
people and 10 effective people, with person mass equal to summed future
defensive outs across that person's training seasons. Count that support
before fitting any position numerators in every actual fold. No broad family
or all-player position donation. If no supported group exists, keep the
individual vector and explicitly mark the unsupported transition.

The learned vector is summed future outs at each position divided by summed
future outs across all eight positions. Exclude C and renormalize unless the
recipient has actual C outs/starts in the three-year window or a cutoff-known
C roster label. Catching evidence can be minor or MLB; a donor's C history is
not sufficient. Other noncatching position changes are allowed as probabilities,
not talent grades or assertions that a player will acquire that position.

Normalize the weighted sum of the individual and allowed learned vectors,
using the fixed MLB evidence weight. Multiply by the unchanged scalar total
potential outs. Unknown individual repertoires remain unallocated; a pitcher
or unexplained DH label does not gain a fabricated nonpitching position.
Keep DH starts separate and unchanged. This cannot solve known dated plans,
future injuries or an incorrect PA forecast.

## Support and scoring

Before fitting save all folds, the conditional-fielding subsets, exact group
counts, fallback choices and detailed stage/age/MLB-sample/primary-role support.
Retain every sparse or unseen test row. Hash the contract, source, code, tests,
anchors and features. No fit may begin before every fold is persisted.

Primary loss remains equal-origin eight-position-cell RMSE on all forecasts.
Compare transition versus the repertoire repair and stronger PA-ratio anchor;
use 2,000 whole-person paired bootstrap draws, seed 708008. Report every
origin, stage, age, position, entrants/continuers/exits/nonarrivals, native
opportunities and matched/full MLB totals. Scalar potential exposure and DH
must remain identical to the earlier repair.

Also report normalized position-share squared error among measured future
defenders, separately for zero-current-MLB-PA players and origin ages 15–19.
This checks actual placement rather than rewarding a diffuse estimate simply
for spreading an excessive PA forecast across positions. Show participant
counts and absolute errors alongside relative changes; rare young arrivals
cannot be hidden by thousands of zero outcomes.

Retain the prior practical tolerances: no more than 2% overall deterioration
against the ratio anchor, no development stage/age group with at least 100
rows over 10% worse, and development totals within 20% of actual. Also require
no increase in equal-origin position-share loss among zero-current-MLB-PA
future defenders versus the repertoire repair. Reasonable individual roles,
support limitations and player reviews qualify all aggregate results. No
automatic adoption from passing numerical tolerances.

## Review and stop conditions

Keep all previous focal cases and origin-selected peers, including Chourio,
Holliday, Lawlar, Basallo, Álvarez, Tatis, Guerrero, Eldridge, planned MLB moves,
exits and nonarrivals. Add the largest new gain/loss and false high/low if not
already present. Preserve peer membership; new peers use only origin-known
stage, role, age and exposure. Trace source statistics through individual
evidence, support, learned distribution, restriction, blend and actual roles.
Replay every distribution and forecast independently before disposition.

If transitions improve usable placement, retain a qualified bridge for the
matched skill-times-opportunity and expanded-value test. If not, retain the
verified mechanics and explicitly unresolved prospect position uncertainty;
do not start another position algorithm or pseudo-sample sweep. A failure
here does not reject minor defensive talent. Future MLB quality, lower-minor
transfer and delivered defensive value remain separate claims.
