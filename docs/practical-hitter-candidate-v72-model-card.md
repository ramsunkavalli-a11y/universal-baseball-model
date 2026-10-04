# Chosen hitter research candidate

2026-10-03. Use the fresher-preseason-ranking version as the current research
candidate, with the original model retained as the comparison. It is a usable
next-year hitting and opportunity forecast, not a finished player-valuation
system. Established-player hitting is competitive on the matched development
sample; playing time and immediate prospect readiness still need work.

## The three separate forecasts

Hitting ability is custom-event batting contribution above an average MLB hitter
per 600 plate appearances. A regularized linear model uses 199 inputs built from
three years of batting counts separated by level, age and MLB history. Recent
years matter more and small samples shrink toward a prior. Future MLB participants
provide the hitting labels, weighted by their actual plate appearances. For a
minor leaguer, this is an uncertain conditional MLB extrapolation, not a career
grade or a promise that he could immediately hit at that level.

Playing time uses two shallow histogram gradient-boosting models with 251 inputs.
One estimates the chance of any MLB PA next year; the other estimates PA if the
player appears. They use production, workload, age, draft/pedigree evidence,
preseason rankings, games and role history. Their product is expected PA. A 10-PA
mean can describe a small chance of a substantial season—not a prediction that
the player will literally receive ten PA. Exits and players who never arrive
remain in the population.

Expected offense multiplies expected PA by the contribution-weighted hitting
yield plus a compatible replacement reference. No new independent-means claim
or full distribution is implied. The 2020 shortened MLB schedule has its own
reference; the canceled minor season is not treated as poor performance.
Defense, baserunning and position are absent from this research branch. Expected
offense is not official WAR, club-control value or trade value.

## What changed and what was not kept

The candidate replaces origin-year prospect ranking inputs with the later
coming-season preseason lists. That materially improves several rapid-arrival
forecasts: Langford 43 to 215 PA, Bellinger 15 to 103, Alonso 127 to 215.
Upper-minor PA RMSE improves 56.24 to 55.13, with favorable nominal development
intervals for PA and offense. Hitting itself is unchanged. The ranking release
dates are explicit, including March 18 for the 2022 list: these are not equal
December information cutoffs or independently certified archived vintages.

Graduation-aware rank absence and transaction employment flags were separately
tested and reviewed, but not combined into this candidate. They supplied little
whole-model improvement and did not repair the intended workload misses.
All-Star assignment records also cannot be sold as contract information.
The recovered source facts and negative results are preserved. No name-specific
overrides or outcome-selected per-player model switches are used.

## How close it is to the public systems

On the same 2,627 historical public matches, PA RMSE is 138.33 versus Steamer
135.38. Average absolute error is 106.41 versus 92.08, 15.56% worse and slightly
outside the 15% working target. Custom-event hitting RMSE is 1.7435, versus
Steamer 1.7746 and ZiPS 1.7534. Converted offense RMSE is 1.0605 versus Steamer
1.1187. Those hitting/offense comparisons are not proof of general superiority:
archive timing is uncertain and event conversion is not each provider's native
target. ZiPS playing-time exports are not assumed available where they are not.

The broad development test contains 30,506 forecasts for 2017–2019 and 2022–2025,
with whole-player chronological folds and only mature training outcomes.
Repeated historical inspection means these are development results, not a new
independent test. All arithmetic and source metadata are checked against saved
forecasts. Protected 2026 outcomes were not used in these calculations; the
incidental search exposure disclosed below qualifies future unseen-test claims.

## Important misses and limits

Kurtz is still projected for ten PA before 489, with near-average hitting before
a major breakout. Meadows falls from 327 to 248 before 591; recent graduation
still exposes a ranking interpretation weakness. Bader receives 140 before 437,
and Belt 113 before 404 then 244 before zero. Judge's debut breakout remains
underpredicted. Some of these cases lack closely matched earlier training
examples; large generic profile counts do not solve that. Individual head support
is shown, including zero matched active examples, rather than disguised as
certainty.

Expected appearances are 4,392 versus 4,538 actual. Upper-minor expected PA totals
are 74,239 versus 92,891, while lower-minor totals are 7,055 versus 5,194. For
origin 2021, arrivals are 581 versus 686. Overall totals are therefore not proof
of good opportunity allocation. Close offense forecasts for Bader and Rortvedt
hide optimistic hitting offsetting low workload. The player reviews expose that.

This branch is not certified park-neutral. Historical foreign/signing evidence
and opportunity conditions are incomplete. Continuous uncertainty is not
certified across the population; the separately reviewed workload-risk research
below does not change this point candidate. Support flags and descriptive
probability bands are not confidence intervals. Do not interpret next-year
appearance chance as eventual MLB success
or use low immediate PA to erase long-term prospect value.

The [completed listing review](hitter-roster-provenance-audit-result.md) confirms
that the input matches the saved requested sets, not that those sets completely
describe historical reserve rights. Missing listing is a proxy, not certified
nonmembership; listed status is not health or playing eligibility. The last
explicit transaction cannot replace it without an ordered reconstruction of
intervening moves, later signings and missing coverage. Current forecast values
are unchanged. A historical search incidentally displayed one current McLain
2026 summary; those outcomes were not used, but a future wholly-unseen-test claim
must acknowledge that exposure.

## Explorer and next milestone

The [source-qualified handoff](hitter-qualified-handoff-result.md) now carries
the completed roster and availability review into a separate local explorer.
Its evidence filter and player panel distinguish returned listings, unresolved
availability, unknown medical coverage and missing foreign production. All
30,506 original forecasts remain identical. This does not repair those gaps or
add calibrated ranges. Actual results and outcome-informed reviews remain opt-in.

The comparative local explorer has a team filter, season and stage selectors,
hitting-only sorting and a candidate/original switch. Each player shows both
forecasts and the actual source statistics. Actual outcomes and outcome-informed
reviews are hidden by default. Organization is the requested historical year-end
roster when available, otherwise the last observed club, not his future employer.
Filtered totals cover known players, not a complete future team budget.

The [active-workload uncertainty test](hitter-workload-risk-result.md) is now
complete, with fourteen actual player walkthroughs. A nested, mean-preserving
distribution improves quantile loss overall and in upper minors versus an older
forest, but public gains are uncertain and absent/thin entrants remain worse.
The comparison also changes means and source context; existing retirement rules
account for 9.68% of its net advantage. Keep the new distribution as qualified
research, not deployed ranges or certified whole-population risk. Expected PA,
hitting and offense remain exactly unchanged; no batting-performance or full
value distribution has been established. Earlier distributions cannot simply
be attached to this candidate.
Supported immediate-readiness and talent extrapolation for thin professional
samples remain substantive unresolved problems, not solved by wider intervals.
Reconcile the earlier explicit-talent/workload study before selecting a substantive
readiness repair: it held participation fixed in a different population and did
not test talent's contribution to arrival in this candidate. Preserve the
established-player benchmark and distinguish uncertain prospect ceilings from
next-year use; do not reopen a status-flag or library tournament.
The historical handoff does not change the frozen 2026 forecast or deployed
explorers, and does not complete the broader hitter goal.
