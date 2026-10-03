# A useful hitter candidate and the work that remains

2026-10-03. We now have one coherent historical development candidate instead
of a collection of disconnected winners. It is useful for inspection and close
to public systems on the measured hitting rate. It is not finished front-office
player valuation, nor a replacement for the frozen 2026 forecast. The goal stays
active because opportunity and some prospect profiles still fail important checks.

## The selected construction

Three years of batting counts stay separate by league, with age, career context,
position and dated draft information. The existing regularized batting model
predicts next-year MLB production if the player participates. The source-repaired
V34 rate is paired with reviewed V49 binary scouting readiness: a shallow boosted
classifier estimates any MLB appearance, and a separate shallow boosted model
estimates PA conditional on appearing. Their product gives expected PA.
Rankings help quality/context but do not make a young prospect immediately ready.
Reported retirement is reversible and affects opportunity, not hitting ability.

Delivered offense is expected PA × (batting wins/600 + origin replacement per PA).
That still approximates the joint relationship between talent and opportunity.
It excludes defense, positional adjustment, running and catcher value. A small
next-year MLB expectation is not a small career or trade value. Club membership
is a qualified historical affiliation, not the player's future guaranteed team.

The [explorer](http://127.0.0.1:8787/) contains 30,506 historical player-season
forecasts for 11,020 people, with targets 2017–19 and 2022–25. The 2020 outcome
year is excluded; canceled MiLB exposure is not a bad season. Team/year/stage
filters, actual histories, explicit probability and conditional PA, reviewed
case explanations and the public table are included. It also shows rejected
reliability formulas as alternatives, clearly labeled. Forecasts are unchanged;
actual batting-rate/value comparisons now use a common origin environment.

## How close it is

On 2,627 common current-MLB forecasts the hitting-rate RMSE is 1.745 versus
Steamer 1.775 and ZiPS 1.753; 2,088 participants supply observable talent.
Workload RMSE is 138.28 PA versus Steamer 135.38, but average absolute error
is 106.79 versus 92.08. The original 1,789 matches remain separately reported
and fail the declared MAE tolerance. Public forecasts are not exactly timestamp-
matched and may include additional availability information. No public forecast
enters model training. The comparison uses the same custom event weights and
total-PA denominator, not official wOBA or neutralized latent ability.

The 2024-origin full cohort predicts 182,491 PA versus 182,880 actual. Do not
mistake close totals for good individuals. Judge's hitting forecast is almost
identical to Steamer's but PA too low; Steer is low in both. Acuna is missed in
opposite directions in consecutive origins. Fast entrants Bellinger, Langford
and Kurtz still get much too little opportunity. Upper never-debut totals are
low; lower-minor PA sums can conceal low arrivals offset by too much conditional
workload. The 218 unverified roster-only rows remain qualified and scored.

The skill-reliability test learned sensible differences between K, HR, walks
and doubles, yet lost to existing batting talent. We did not adopt it because
its formula sounds better. The same-event audit corrected evaluation units,
not predictions. Both changes have full actual-player reviews and preserved
results, including the largest consequential harms and unsuccessful peers.

## The next bounded work

1. **Make opportunity information timely and explicit.** Keep the existing
   mean and identify what is demonstrably known at cutoff: active role,
   reversible exits, dated availability and uncertainty. Do not train on public
   one-PA labels or retroactively add spring injuries to December predictions.
   If equally dated public archives cannot be established, keep comparisons
   qualified and use matched cutoff-known scenarios, not a claim of parity.
2. **Repair fast entry and prospect talent together.** Existing counts/draft
   and stale annual ranks miss rapid advancement. Inspect the actual known
   terminal level, professional exposure, pedigree and production translation
   in mature historical folds before a small joint alternative. Include failed
   similarly situated prospects. Do not assign every famous breakout an
   automatic boost, retrieve new college data, or treat conditional future-
   participant rates as present-day DSL grades.
3. **Finish a defensible uncertainty and value layer.** Check probability,
   workload and rate errors separately as well as the product. Preserve exits.
   Use mature Years 2–3 support before longer/control claims. Reconnect running,
   defense and position only with compatible, individually reviewed components;
   never label batting plus replacement full WAR or annual means trade value.

This is a pause in algorithm churn, not an assertion every approach is exhausted.
Further work must address one of these material failures and compare the complete
candidate on unchanged populations, not select a new library to avoid them.
Protected 2026 outcomes and every older/frozen explorer remain untouched.

[Talent reliability result](practical-hitter-reliability-v50-result.md) ·
[Public comparison and eleven actual reviews](practical-hitter-public-units-v51-result.md) ·
[Readiness review](practical-hitter-readiness-v49-result.md) ·
[Controlling plan](practical-hitter-model-v30-plan.md).
