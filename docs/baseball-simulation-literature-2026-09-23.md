# Baseball simulations: what to borrow, and what not to claim

2026-09-23. Literature/design review only. No fits, forecast revisions or protected
2026 outcomes. Companion: [bounded next checkpoint](projection-anchored-path-next-checkpoint.md).

## Main conclusion

Keep our independently estimated player projection at the center. Test whether
historical development patterns improve its uncertainty and future paths. Do not
assume copying entire comparable careers is better than the existing projection,
or that running more simulations corrects a biased probability model. This is our
design inference from the sources below, not a disclosed proprietary algorithm.

Our destination remains player-rights value: price each possible supported career
with its control and obligations before averaging. Expected production, controlled
production, surplus, likely trade return and a particular team's utility are
different quantities. Public FV is a separately dated comparison, not a predictor.

## Public methodological evidence

### ZiPS: estimate the baseline, then development

Szymborski describes establishing baseline performance and comparing its quality
and shape with historical players at multiple points in their careers. Those
comparisons inform player-specific aging midpoints and ranges. This supports
retaining historical young-player snapshots and separating the current estimate
from uncertain development. It does not validate our donor weights, an exact
residual-path formula, or every historical comparable as equally relevant.
Source: Dan Szymborski, November 10, 2020,
[The 2021 ZiPS Projections: An Introduction](https://blogs.fangraphs.com/the-2021-zips-projections-an-introduction/).

### PECOTA: component aging, reliability and future opportunity

Wyers describes component-specific aging and comparable-based curves shrunk toward
generic curves according to reliability. Long-term playing time starts from
expected peak use rather than indefinitely carrying forward a prospect's limited
current opportunity. Percentiles incorporate forecast reliability, projected
exposure and population tendencies. Crucially, the article qualifies the ten-year
display with a survival/attrition convention: it is not directly comparable with
our unconditional forecasts containing all non-arrivals and inactive players.
Source: Colin Wyers, March 8, 2012,
[Reintroducing PECOTA: House of Cards](https://www.baseballprospectus.com/news/article/16189/reintroducing-pecota-house-of-cards/).
Access note: direct page retrieval failed; the primary article's indexed text,
including its methodological bullets and update, was available. This is not a
review of proprietary source code or a claim about every current PECOTA version.

### PECOTA UPSIDE: success magnitude matters, but it is a different target

Silver's prospect-ranking approach emphasizes the probability and magnitude of
above-average production over a peak window, motivated by inexpensive prospect
rights. Its treatment of unproductive outcomes is a purpose-built upside score,
not a full surplus ledger. Borrow the separate success/upside diagnostic; do not
copy its zero-credit convention into guaranteed obligations, eliminate failures
from evaluation, or substitute a peak-window score for all controlled production.
Source: Nate Silver, February 1, 2007,
[PECOTA Takes on Prospects, Introduction](https://www.baseballprospectus.com/news/article/5836/lies-damned-lies-pecota-takes-on-prospects-introduction/).
Primary indexed article text was available; no subscription bypass was used.

### ZiPS team simulations: distinguish the sources of uncertainty

The 2025 standings explanation simulates roster strength and injury availability,
fills replacement depth according to who can play, then simulates games. That
supports distinguishing ability uncertainty, availability and game-event noise.
This is a team-season application, not evidence that a long-term minor-league,
service-time or controlled-value simulator has been validated.
Source: Dan Szymborski, July 3, 2025,
[The ZiPS Midseason Standings Update](https://blogs.fangraphs.com/the-zips-midseason-standings-update-2/).
Only the methodological description informs this review; no standings are model inputs.

### ZiPS extension analysis: compare earnings paths, not just mean WAR

Szymborski's 2021 extension article describes a separate simulation comparing
year-to-year earnings and a later contract with guaranteed terms, including minimum
pay, arbitration and free agency. Reporting downside, middle and upside earnings
illustrates why paths matter financially. It does not provide a current pricing
curve, complete source code or proof of forecast accuracy. The article explicitly
describes an additional simulation rather than claiming it was already standard
ZiPS infrastructure.
Source: Dan Szymborski, November 24, 2021,
[Wander Franco Lands A Monster Deal](https://blogs.fangraphs.com/wander-franco-lands-a-monster-deal/).

### KATOH: a useful alternative to simulation

Mitchell describes direct models of MLB arrival and production thresholds. A later
revision lengthens forecast windows for lower starting levels to capture delayed
production, and distinguishes stats-only from scouting-enhanced forecasts. This
supports keeping a direct probability benchmark and an explicit late-arrival tail;
simulation need not win. Level-dependent calendar windows remain approximations,
not exact service-day accounting. Our existing failed threshold/skill-tail work
must be retained, not reopened as a parameter sweep under the KATOH name.
Sources: Chris Mitchell,
[A Primer on a New and Improved KATOH](https://blogs.fangraphs.com/a-primer-on-a-new-and-improved-katoh/) (November 25, 2015),
[An Improved KATOH Top-100 List](https://blogs.fangraphs.com/an-improved-katoh-top-100-list/) (2016).

### Academic baseball precedent: share information without asserting certainty

Jensen, McShane and Wyner use hierarchical Bayesian modeling, information sharing
across players/time and mixture-based shrinkage for MLB hitting forecasts. This
supports reliability-aware pooling and investigating persistent player differences.
It does not establish a complete MiLB promotion, survival, service or financial
simulator. More elaborate joint survival or multistate models remain possible
future challengers, not proven best practice for this project.
Source: [Hierarchical Bayesian Modeling of Hitting Performance in Baseball](https://arxiv.org/abs/0902.1360), 2009.

## Application to our completed experiment

The [completed result](player-path-value-bridge-v1-result.md) remains rejected.
Hitting-history CRPS 0.2894 beats the basic forest's 0.2968 and age/stage baseline's
0.3641, but mean RMSE 1.333 loses to delivered 1.214. Prospect regular-workload
counts are 28.7 predicted versus 44 observed. No literature finding reverses that.

The post-score young/brief-MLB group has 98 player-origin observations: 46.8
predicted disappearances versus 10 actual, and 6.75 predicted regular outcomes
versus 16 actual. It is a hypothesis-generating subgroup, not a retroactively
passed selection gate. The current donor library has only 43 young MLB profiles
for H3 and 34 for H6. Eldridge's H6 samples average age 24.6; 287 of 400 start in
the minors. These are support diagnostics, not proof that all minor-origin donors
are invalid or that an individual public FV must be correct.

The latest-snapshot rule discards earlier versions of historical players. We should
test identity-balanced retention of those snapshots before altering the modeling
architecture. Then, only if cutoff-safe inputs can be reconstructed, consider one
projection-anchored development-path challenger. Historical residuals must be
out-of-time; repeated simulated noise must not duplicate uncertainty already in
the sampled trajectories. Both are our proposed tests, not guarantees from ZiPS
or PECOTA. Keep the current projection and every failed result as comparators.

No dollar values, real All-Star probabilities or full controlled-WAR claims follow
from batting/replacement labels. Preserve the valuation interface, whole-WAR and
service/cost gates, beyond-2031 tail and a separate future-entrant reserve. More
draws address Monte Carlo noise only; they cannot cure biased development,
opportunity or cohort selection.
