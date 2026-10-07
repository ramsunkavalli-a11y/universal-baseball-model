# Forecast defensive opportunities with fixed batting playing time

2026-10-06. This comparison connects the prepared position history to actual
future MLB defensive exposure. It does not refit arrival, batting PA or defensive
skill. The target is next-season opportunity, not eventual defensive talent.
The reviewed skill baselines will be integrated only after this player review.

## Fixed population and targets

Use every prepared historical forecast at the 2022, 2023 and 2024 origins. The
first two are development comparisons; the already exposed 2025 outcomes are an
additional development check, not an untouched holdout. Keep age/role gaps,
non-arrivals, exits and the six historical defense-only/zero-PA cases in coverage.
No 2026 outcomes, current explorer changes or automatic deployment are permitted.

Forecast eight actual fielding-out totals, plus DH starts separately. Compare the
same official outcomes, identities and fixed `preseason_pa` in all arms. Only
the exposure bridge changes. The cached population is not the repaired 2026
production population; show the full MLB remainder beside matched totals.

Native opportunity outputs are distinct: framing pitches, tracked throwing
attempts, blocking chances, isolated outfield advancement opportunities and
received first-base throws. Missing positive-position measurements stay unknown.
An independently observed absence of the relevant defensive position permits
zero opportunity, unless a positive native record contradicts it. Mixed-position
arm aggregates cannot be treated as isolated OF opportunities. Every forecast
remains in the primary eight-position exposure score, even if a native outcome
cannot be measured.

## Origin role evidence

Use the complete nine-position start vector over the previous three calendar
years, weighted 1, 0.5 and 0.25. Combine actual MLB and minor starts as role
observations, not as equally translated defensive skill. MLB regulars naturally
contribute many more recent starts than a brief minor rehab stint. Preserve the
two histories and their amounts in the walkthrough; no claim is made that an
MLB start and a minor start have identical implications for future position.

If all starts are zero but defensive outs are observed, use defensive-out shares
as an explicitly labeled role fallback. If both are absent, use the cutoff-known
roster position only as a weak fallback. An unknown or pitcher-only roster label
gets the broad conditional opportunity prior, not fabricated position evidence.
Do not hard-reduce mixed catchers/outfielders or utility players to one position.
Origin age is reported age where known, in the already audited five-year bands;
unknown age remains unknown.

## One contextual bridge and required anchors

The **pooled-role reference** estimates, for each origin role, a future
eight-position-outs-plus-DH-starts vector per actual future MLB PA. A training
player contributes to a role in proportion to his origin role share. Numerators
are share-weighted future opportunities; denominators are share-weighted actual
future PA. A forecast mixes these role-specific vectors using its origin shares,
then multiplies by the unchanged expected PA. This is an empirical conditional
mean, not an inverse solution of a latent role-transition matrix.

The **contextual challenger** uses the same calculation with stage and age when
supported. Pool in this fixed order: role/stage/age, role/stage, role, all active
training batters. A group needs at least 20 distinct contributing people and at
least 10 effective people, where each person's mass is his summed share-weighted
PA and effective count is squared total mass divided by summed squared masses.
These are conservative fallback rules, not estimated reliability thresholds or
proof of transport. Save chosen groups, actual support and fallback mass for
every forecast. No tuning, learner tournament or future-selected branches.

Additional anchors are prior-year official position-out persistence and prior
position outs multiplied by expected PA divided by origin MLB PA. The latter
falls back to the pooled-role reference when origin MLB PA is zero. It is a
diagnostic anchor, not a cap or a selected player-specific override. DH starts
are not included in the defensive-out loss because they have different units.

## Chronology and native conversions

Role training uses positive-PA historical targets available by the test origin
and excludes every season of the held player. The existing player folds are
retained. Save all checks, row IDs, source hashes, group support and original
target definitions before calculating fitted means. Zero-PA defenders remain
in evaluation even though this conditional training does not explain their
special opportunity independently of batting PA.

For each native channel, learn one recent league conversion from qualified
observed opportunities divided by corresponding official outs: catcher outs,
OF outs or 1B outs. Use the same fixed three-year weights and exclude held
players at every origin. At least 20 people and two measured seasons are needed;
otherwise expand to all available earlier seasons and label the fallback. Do
not use future pitching, actual future fielding or quality estimates in this
conversion. Report the official exposure covered by measured source records,
since conditioning on available native measurements may bias transport.

Multiply each forecast's corresponding outs by that channel's conversion.
These are opportunity predictions, never skill denominators invented from
innings. Keep native observed counts in the talent histories. Preserve native
opportunity persistence as an anchor and the old fixed throwing/blocking
50/50 PA-ratio hybrid; framing keeps prior-pitch persistence as its legacy
anchor. Missing origin opportunities give an explicitly unmeasured zero-history
forecast in those anchors, not a measured zero talent claim.

## Scores and practical checks

Primary loss is equal-origin mean RMSE over the eight position cells, on the
complete fixed population. Report per-origin cell RMSE/MAE, per-player total-out
RMSE/MAE, every position's predicted/actual total, stage and origin-age errors,
entrants, continuing defenders, exits, source/profile fallbacks and native
measurement coverage. Also score known positive native outcomes separately from
the largely zero full population. Preserve DH-start errors separately.

Use 2,000 paired whole-player bootstrap draws, seed 708006, keeping a player's
origins together. Intervals are nominal development uncertainty, not fresh
confirmation. Nonnegative inputs must produce finite, nonnegative opportunities
and sums must reconcile. Forecasts beyond historical player-season exposure
ranges are warnings, not an excuse to impose a false 162-game hard ceiling.

The contextual bridge is an integration candidate only if it improves the
primary score over the pooled reference, has no stage or age group with at
least 100 forecasts worsening more than 10% in development RMSE, and keeps
each development-origin total within 20% of matched actual outs. These practical
tolerances are not significance tests and are not sufficient for deployment.
Otherwise retain the useful pooled reference if its own checks are reasonable;
a tiny challenger loss does not reject position history or the entire defense
layer. Compare against persistence and the ratio anchor too. No post-result
retuning of bins, support thresholds, priors, cohorts or blends.

## Required player review

Fixed diagnostics: Varsho 2022, Betts 2023, Schwarber 2023, De La Cruz 2022,
Álvarez 2022 and Eldridge 2024 when present. Add largest gain, deterioration,
false high, false low, an ordinary case and an exit/non-arrival. Select three
peers from origin stage, age, role mix and exposure where supported, without
future-success filtering. Show dated source rows, role fractions, chosen group
rates/support, fixed PA, each position and native forecast, then actual outcomes.
Separate learned mechanics, upstream PA error, missing known role plans and
unexpected events; do not explain a Betts or Schwarber position change as
unpredictable merely because the source omitted a dated preseason plan.

Only after this walkthrough and independent arithmetic replay may a bridge be
retained for the next matched delivered-runs/value integration. An opportunity
gain alone is not a defensive-talent or full-WAR validation.

## Literature and preserved limits

[FanGraphs positional adjustment](https://library.fangraphs.com/misc/war/positional-adjustment/)
uses actual defensive position exposure, with DH accounted separately.
[FanGraphs depth charts](https://blogs.fangraphs.com/introducing-fangraphs-depth-charts-and-standings/)
separates projected performance from assigned playing time. The present bridge
is our empirical implementation of that separation, not their unpublished model.
Older frozen exposure contracts remain historical anchors; the active defense
goal authorizes this separate research comparison, not rewriting those verdicts.
