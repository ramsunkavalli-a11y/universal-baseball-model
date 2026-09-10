# Project status and handoff

Updated 2026-09-10. This is the current start-here document.

## Current P0: pitcher value funnel

The playable build had a material integration defect: its conditional WAR layer still
joined the older generic opportunity paths after the better Phase 2 MLB workload model
had been built. The corrected chain raises projected six-year WAR across 940 debuted
pitchers from 1,108.1 to 1,325.5. Logan Webb moves from 7.45 to 9.21 path WAR, Tarik
Skubal from 9.83 to 11.39, and Paul Skenes from 8.50 to 13.44. Webb's controlled value
is now $10.2 million rather than the earlier near-zero result. Exact source hashes and
the workload model ID are recorded, and the explorer now rejects stale lineage.

This does not solve the prospect-pitcher problem. After removing the weak
age-relative-to-level/hand adjustment, the nested model totals only 68.1 WAR across
3,849 pre-MLB pitchers and has a 2.66-WAR maximum. That adjustment had a small 2025
point-score gain, bootstrap intervals spanning zero, a worse left-handed subgroup,
and a disproportionate current top-end effect. It is no longer in the playable build.
No manual bonus, outside FV input, or altered grade threshold replaces it.

The [stage-by-stage audit](pitcher-value-funnel-audit-result.md) is now the controlling
pitcher handoff. A new [four-year horizon audit](prospect-horizon-extrapolation-result.md)
fits only 2018 and evaluates 3,649 pitchers from the 2021 snapshot through 2025. The
constant-hazard model predicts 15.7% arrival versus 12.3% observed, 9.2% meaningful
roles versus 5.0%, and 4.5% established roles versus 3.0%. It is already optimistic,
especially for AAA, older, and starter-classified pitchers. The hurdle therefore does
not explain low pitcher values. The next P0 is conditional MLB WAR and linked career
production, still retaining all failures and zeroes and using time-ordered selection.

The first [conditional-quality audit](prospect-pitcher-conditional-quality-result.md)
then tests K, UBB, HBP, HR, age, level, workload, role, hand, origin and official draft
pedigree. A model selected only inside the 2018 cohort fails on 225 later successful
pitchers: RMSE is 0.20116 versus 0.20004 for the population mean, and the paired interval
crosses zero. Established pitchers are better in the later cohort, but using the
earlier cohort's tier relationship makes the later score significantly worse; the
relationship changed direction. Neither candidate is promoted. The current aggregate
inputs therefore do not reliably separate quality among successful pitcher prospects.
The first richer all-level batted-ball test is also complete. A streamed, hash-recorded
build reduced 84 public 2021-2023 PBP assets to pitcher contact summaries without
retaining the roughly 7.05 GB raw copy. A heavily regressed ground-ball rate helped
the 2022-to-2023 outer test, but reversed direction and did not improve the untouched
2023-to-2024 confirmation. Popup and pulled-air/pulled-ground increments also failed.
See the [contact increment audit](pitcher-contact-increment-result.md). None enters the
model. The next evidence should be genuinely new cutoff-safe pitch/process or
contact-quality data, or broader mature cohorts—not another bonus, FV threshold
change, or same-period rescue.

The next career-simulation source is now built. The
[historical pitcher performance paths](historical-pitcher-performance-paths-result.md)
align annual component WAR with the existing workload and role vectors for 1,798
pitchers. Established paths average 4.28 component WAR and 1,626 BF over six years;
fringe paths average essentially zero WAR. The current simulation does not preserve
that performance/workload/role dependence: it applies one prospect rate across the
sampled workload path. The next challenger should resample all three from the same
historical pitcher, using only paths observable at each replay cutoff. This source
does not change current values by itself.

The first [linked-path challenger](dependent-career-linked-pitcher-audit-result.md)
has now been run as a sensitivity. It raises total expected controlled WAR for 3,849
pitcher prospects from 64.6 to 1,058.7 and the 99th percentile from 0.69 to 2.78 WAR.
That fixes the obvious scale compression but is far too large to promote without a
cutoff-specific replay; rank correlation with the incumbent is only 0.667. Its ordering
is driven mainly by hurdle and role probabilities because player-specific conditional
quality failed validation, and the six-year hurdle is already known to be optimistic.

The [cutoff-safe 2021 replay](dependent-career-linked-pitcher-replay-result.md) is
promising on scale: across 3,649 pre-MLB pitchers, observed 2022-2025 component WAR
averages 0.090 and the linked forecast predicts 0.105. The simpler arrival-only pooled
path beats zero RMSE 0.551 to 0.576, with a fully favorable paired interval. Splitting
paths into fringe/meaningful/established tiers does not beat the pooled path.

The identical-row historical incumbent is now reconstructed with only 2018/2021
level translations, evidence through 2021, the deployed 800-BF regression and Tango
component aging. It predicts 0.047 mean WAR with 0.558 RMSE. The arrival-only linked
path predicts 0.127 with 0.551 RMSE, closer to the observed mean, but its paired MSE
interval versus the incumbent crosses zero. Diagnostics show the tradeoff: linked
paths better capture later arrivals and higher-probability pitchers but overpredict
non-arrivals and some low-probability groups; the incumbent remains better for the
2021 reliever group. This is promising, not proven. Current rankings remain unchanged.
The next valid gate is a predeclared genuinely later confirmation; do not tune a
role fix on these disclosed subgroups and call it confirmation.

The earlier September 9 stopping point remains useful historical context in
[the prior handoff](current-cycle-stopping-point-2026-09-09.md).

The frozen [prospect PBP hurdle test](prospect-pbp-hurdle-test-result.md) found a small
contact-shape improvement against a core aggregate comparator, but the required
[pedigree stacking check](prospect-pbp-pedigree-stack-result.md) produced a mixed
decision. Log loss improved `0.022501 -> 0.022283`, while Brier worsened
`0.004800 -> 0.004820`, its paired intervals crossed zero and the supported 300+ PA
group was worse on both scores. The PBP addition is therefore rejected for the current
pedigree-inclusive opportunity model. Its conditional-quality use was already
rejected for tiny support and severe calibration failure. No values changed. Catcher
preference, outside FV inputs and non-universal pitch sequences remain excluded.

The first [current-organization capacity layer](current-organization-opportunity-allocation-result.md)
is complete and now has a [2025 historical replay](historical-team-capacity-replay-2025-result.md).
The broad team cap modestly improved pitcher RMSE and MAE and was roughly neutral for
hitters. Keep it as team context. Rigid primary-position and pitcher-role caps removed
too much workload: the hitter version clearly worsened RMSE and the pitcher version
had mixed scores. Both are rejected for display until flexibility can move unused
capacity across positions or roles. None of these layers changes portable value.

The [broad hitter position-capacity diagnostic](current-organization-position-capacity-result.md)
still identifies catcher crowding, but the replay proves that primary-position shares
cannot be used as rigid quotas. Catcher receives no talent bonus or penalty. Flexible
multi-position assignment is Phase 2 research, not a current valuation input.

The [minor-to-MLB position-transition test](prospect-position-transition-result.md)
now passes its time-ordered outer gate. Among 576 arriving hitters, the regressed
origin-position matrix improved multiclass log loss from 1.489 to 0.811 and Brier from
0.751 to 0.403. Catchers retained catcher in 85.9% of observed cases. This authorizes
a private probabilistic-position sensitivity, not a catcher haircut or published change.
The required [positional-runs validation](prospect-positional-runs-validation-result.md)
then rejects that sensitivity for value use: MAE worsens from 3.740 to 4.561 runs per
600 and RMSE from 5.109 to 5.680, with both paired intervals clearly unfavorable.

That [value sensitivity](prospect-position-value-sensitivity-result.md) is complete but
does not replace the playable default. Applying the two-year destination mix to all
six years reduces hitter 50+ counts from 86 to 36 and worsens the outside diagnostic.
The [current-position source audit](prospect-current-position-source-result.md) selects
official fielding outs first, games role second, and listed position last. The next
challenger must target exact player-level positional runs on development data; the
coarse group mixture is rejected.

The [established-tier prospect test](prospect-established-tier-test-result.md) is also
rejected. Mature fringe/meaningful/established workload priors are usable, but three
separately fitted probabilities violate their required ordering and flatten credible
prospects even more. That failure led to one conditional hurdle: arrival, meaningful
given arrival, then established given meaningful.

That [conditional hurdle audit](prospect-conditional-career-hurdle-result.md) now
passes its structural gate. In the outer period, roughly 30% of arrivals become
meaningful and 45-48% of meaningful players become established. Core models calibrate
reasonably; richer interaction and pedigree candidates have no reliable outer gain.
One source-contract defect was then corrected: official numeric hitter position codes
had all fallen into the `OTHER` role. The [position-code correction](prospect-position-code-correction-result.md)
restores the intended role groups without adding a catcher bonus or quota.
The [nested current-value sensitivity](prospect-nested-career-value-result.md) now
passes the private gate and is the local explorer's pre-MLB default. It has zero
probability-order violations, keeps Josuar Gonzalez at 45 FV with a lower 1.83 WAR,
and reduces hitter 50+ counts from 352 to 86 instead of collapsing them to 8 or 17.
Pitcher prospect values remain compressed, and the top hitter ordering still
needs model-based error review. This is private and provisional; MLB contract values
and published outputs are unchanged.

The [2025 pitcher-role audit](pitcher-role-2025-audit-result.md) rules out broad role
suppression as the main pitcher-prospect problem. Predicted starter share is 30.4%
versus 31.0% observed across 801 active pitchers and 27.5% versus 27.0% among 137 with
no prior MLB work. Keep the role probabilities; audit translated pitcher WAR rates
next.

The [pitcher affiliated-rate regression audit](pitcher-affiliated-regression-audit-result.md)
rejects weakening the 800-BF prior. A 600-BF candidate won narrowly in 2024 but made
2025 component log loss worse, with both bootstrap intervals spanning zero. Keep 800
BF. The arriving cohort's implied run rate was too pessimistic overall, so a frozen
component-profile calibration is the next targeted test.

The [pitcher component-calibration audit](pitcher-affiliated-component-calibration-result.md)
also rejects a tempting cosmetic fix. It improved the 2025 cohort's average neutral
run estimate, but worsened both component log loss and Brier and made the top quintile
too optimistic. Keep the existing talent probabilities. Audit the pitcher-specific
controlled-WAR-to-FV mapping next.

The [pitcher FV mapping audit](pitcher-fv-mapping-audit-result.md) confirms that the
grade function is not causing the compression. Displayed 50 begins at 2.6 expected
six-year WAR, while the current pre-MLB maximum is only 2.664 and the 99th percentile
is 0.757. Keep the monotonic mapping. The next challenger belongs upstream: test
chronology-safe age-relative-to-level and stable handedness against later MLB pitcher
components, with no target high-grade count.

That [age-relative-to-level and handedness audit](pitcher-age-level-handedness-result.md)
passes its frozen point-score gate on 2025: component log loss improves by 0.000171
and Brier by 0.000052 after selection on 2024. Both bootstrap intervals cross zero,
and the 36-pitcher left-handed subgroup worsens. Its large current top-end effect is
not supported by that weak validation, so it has been removed from the playable build.

The integration replay exposed and corrected a separate
[player-type source bug](model-player-type-source-correction.md): exclusive pitchers
with negative WAR could be mislabeled hitters because missing hitter WAR was filled
with zero. Player type now follows real path presence, using projected component only
for actual two-way paths. The demographic [current-impact replay](pitcher-demographic-current-impact-result.md)
has zero type switches and zero hitter changes. On identical inputs it moved pitcher
45+ counts from 24 to 40 and 50+ from 1 to 2, while more than doubling the current
pitcher total from 68.15 to 162.68 WAR. That disproportionate effect helped trigger
the decision not to use it without stronger confirmation.

The [pitcher contact-component expansion](pitcher-contact-components-result.md)
was rejected before confirmation. Saved official data can split contact into singles,
doubles and triples, but every richer profile worsened both 2024 development proper
scores under 800-4,000 BF regression. No 2025 challenger score was calculated. Keep
the simpler five-part pitcher profile; extra outcome detail has not earned production
use, and uncertified pitch-sequence fields remain excluded.

The [pitcher contact testing queue](pitcher-next-contact-testing-queue.md) starts
with a broad review of reproducible pitcher-projection methods, using Tango as the
primary framework and other public work from the past two decades as sources of
testable hypotheses. The first [pooled non-HR XBH test](pitcher-pooled-xbh-result.md)
is now rejected: all 800-4,000 BF candidates worsened both 2024 development proper
scores, so 2025 was not calculated. The event-level ground/air, popup, pulled-air and
pulled-ground sequence has now also been tested and rejected after a favorable first
outer period reversed in the untouched confirmation. A separate future test may use frozen
lineup bands 1-6 versus 7-9 and strongly regressed same/opposite-side results to test
future starter potential.
Batter quality, batter side, pitcher hand, opponent mix, park, level and season are
required controls. Pulled air is treated as potential future pitcher damage, not
assumed pitcher talent; each increment must be repeatable and improve later proper
scores.

The [event-context source review](pitcher-event-context-readiness.md) confirms that
the retained matchup design can support a universal platoon test after its ignored
sidecar is rematerialized. It blocks lineup band because batting order was not
retained, and blocks times-through-order/pitch-process work where lower-level feeds
contain outcome-minimal sequences. Missing context must remain the exact aggregate
baseline.

The playable build now has an enforced
[model-law audit](private-preview-model-law-audit-result.md). All 18 checks pass across
probability simplexes, six-year path completeness, expected-workload/WAR identities,
nested hurdle ordering, exact WAR-to-FV mapping, player type, uniqueness, and interval
ordering. Its first run caught 23 MLB rows that mixed a Phase 2 WAR center with old
Phase 1 WAR bounds; the builder now derives center and bounds from the same retained
annual path. Central contract values did not change.

The [upper-tail calibration audit](prospect-upper-tail-calibration-result.md) rejects
both intercept-only and Platt recalibration for every deployed hurdle stage. Hitter
arrival's raw top 1% predicted 87.1% against 81.3% observed, while its broader top
decile was optimistic. Earlier-cohort calibration worsened later proper scores, so no
manual probability cap or recalibration is applied.

The [hitter top-end position audit](hitter-top-end-position-audit-result.md) finds no
broad catcher quota: catchers are 22.9% of modeled hitters and 25.6% of 50+ hitters.
Premium-position persistence is material, however. Standard position runs supply
3.76 WAR to Caden Bodine and 3.29 to Rainiel Rodriguez, moving each from a
position-neutral diagnostic 50 to the displayed 55. Both remain 50 without position.
Do not remove real positional value; the next candidate needs player-level retention
and defense evidence, since the earlier coarse transition mixture failed validation.

The local explorer now exposes those drivers for every modeled pre-MLB player:
expected six-year PA/BF, conditional WAR rate, and hitter batting/running/defense/
position runs or pitcher runs above average. This is display-only transparency and
does not change a forecast. The launcher still runs all 18 model-law checks before
opening the page.

The first [nested prospect uncertainty layer](prospect-nested-workload-uncertainty-result.md)
now adds empirical workload-only P10/P50/P90 outcomes for all 6,719 prospect paths.
Every weighted mean reproduces its point WAR (maximum difference `3.6e-15`), so no
central value changes. The explorer labels these as workload outcomes, not full
confidence intervals; skill-rate, aging, injury, defense and position-retention
uncertainty are still missing.

Latest: official StatsAPI Rule 4 draft history is now a structured, replayable source.
A nested later-cohort audit supports draft pedigree more strongly for arrival than
quality. A proper hurdle test conditions MLB component quality on meaningful playing
time. Its hitter challenger worsens both outer scores and its pitcher challenger is
indistinguishable from core. Origin is explicitly rejected as a quality shortcut and
draft evidence earns no WAR floor. Pre-MLB FV is
now bracketed: the year-by-year paths are too conservative for true elite prospects,
while the six-full-seasons override is too generous across the long tail.

The first closed-system audit also finds that aggregate capacity is not exceeded, but
independent hitter and pitcher paths disagree by as much as 5.4% of the same league
PA/BF pool. A symmetric league-level reconciliation is specified for research; team
and role allocation remains the next step before production use.

## Active plan

The user has prioritized model quality and paused interface development. Read the
[authoritative product roadmap](product-roadmap.md) first. It supersedes narrower
component-specific next-experiment lists for prioritization while preserving their
results and frozen decisions.

The clarified end goal is every-player trade value updated with each game.
The [direction review](trade-value-direction-review.md) finds useful foundations
but missing career/control/cost and continuous-update integration. It also identifies
older opportunity/roster models to reuse before building another challenger.
The broader roadmap now includes pitcher and whole-player value integration;
website work remains paused. No player dollar ranking has been promoted.
A private, generated results explorer now makes the current research checkpoint easy
to inspect without publishing it. It exposes filters, sortable player results,
year-by-year paths, review rows and CSV export while retaining the model warnings.

## Active Phase 2 preview

The [Model FV and workload preview](phase2-model-fv-and-workload-2026-09-09.md)
is now the active continuation. Historical, time-ordered models replace the old
pre-MLB arrival shortcut and separately estimate any debut and a meaningful MLB role.
Both beat a level-only baseline in every evaluation fold. The arrival probability now
enters expected WAR; meaningful-role probability is diagnostic. The top prospect list
is still too crowded because conditional-on-arrival WAR is too generous. Historical
MLB outcome quality and durable draft/signing evidence are the next P0 work.

The first [demographic feature search](phase2-demographic-feature-search-2026-09-09.md)
now retains official profiles for 24,328 players and tests stable and full demographic
groups without outside FV inputs. Narrower searches named stable-interaction and
birth-country development leaders, but neither is promoted because the same periods
were searched to find them. Current-recorded physical measurements remain exploratory
until their historical timing is safe.

A stricter [nested robustness audit](prospect-arrival-nested-robustness-result.md) now
supersedes that initial ranking. It normalizes 313 equivalent StatsAPI country labels
and tests 176 combinations across demographics, baseball development/role interactions,
logistic shrinkage, and production-rate regression. It embargoes incomplete two-year
outcomes, evaluates proper scores/calibration with paired uncertainty, and checks
supported subgroups. Structured draft evidence materially improves hitter arrival and
meaningful-role log loss, but is not selected for the stricter established-role
outcome. Pitcher pedigree gains remain uncertain. No input changes production values.
The reusable rules now govern all StatsAPI/PBP feature searches through the
[model-search policy](model-search-validation-policy.md), not demographics alone.

The first [mature post-debut workload study](prospect-outcome-quality-workload-result.md)
now quantifies the larger Model FV flaw. Actual six-calendar-year workload averages
61 PA for fringe hitter arrivals versus 1,986 PA for hitters with a meaningful season;
meaningful pitchers average 948 BF as relievers, 1,154 as swingmen and 2,505 as
starters. The existing preview assumes far more workload after any arrival. A binary
fringe/meaningful replacement nevertheless overcorrects—hitter 50+ counts fall from
320 to 18 and external Top-100 diagnostic error worsens—so it is rejected. Production
values stay unchanged while regular/impact probabilities and durable pedigree are
built next.

This work builds on the recovered-opportunity commit `7c2a874`. Main now contains the
current model foundations, experiment records and plan. It does not change a website
or promote a player ranking; the public v1 release remains historical.

## Phase 1 foundation progress

- The player-rights universe contract now preserves every required player, represents
  missing evidence as `unknown / prior_only`, rejects future observations and fails
  closed on ownership conflicts. Certified dated 40-man membership is connected as
  one narrow evidence family. A separate candidate inventory unions broad discovery
  sources with provenance while preventing candidate presence from asserting an owner.
- The official `fullRoster` source is the primary player-discovery source: 7,891
  players, with 99.80% having one candidate organization. Its 16 cross-organization
  outliers prevent using it alone as final rights proof, not using it as the denominator.
  A chronology-safe official transaction ledger now supports a bounded ownership gate:
  unique 40-man membership is direct evidence, then exact structured acquisition and
  MLB-rights transactions resolve only the remaining multi-organization cases.
- The career-outcome panel makes completed-season absence an observed zero and later
  seasons right-censored. A real official 2015–2024 inventory contains 10,585 batting
  player-seasons, 8,095 pitching player-seasons and 3,777 distinct MLB players.
- A transparent pitcher component baseline now separates K, UBB, HBP, HR and other-BF
  rate skill from opportunity. It beat a global population comparator in every rolling
  2018–2024 fold; equal-fold log loss was 0.98044 versus 0.98500.
- Team-control arithmetic and the conservative StatsAPI replay are implemented. A
  Padres working sample plus Giants holdout confirms FanGraphs as the dated
  service/options baseline, StatsAPI for forward changes and Rule 5, and transactions
  as a bounded exception layer. Broad comparison coverage is 95.2% and 98.4%; Rule 5
  year agreement is 180/186 where both values are available.
- All 30 payroll workbooks normalize into 915 player records, 3,720 annual terms, 180
  clauses and 417 other payments. Stable IDs attach 870 players; current official
  roster entries corroborate the remaining 45 exact-name identities. Payroll identity
  review is now zero, while liabilities for former roster members remain separate from
  current team control.
- The refreshed 2026-09-08 league build contains 8,393 affiliated players and 50,058
  future-path rows for 8,343 players through 2032. Exact official release evidence now
  separates 37 players with no incumbent rights, while one same-day transaction conflict
  remains in review. All prior multi-organization cases are
  resolved: 15 by unique official 40-man membership and six by exact transactions.
  Its complete 133-player Super Two
  pool has a calculated cutoff of
  `2.144` (488 days), with 30 selected because the cutoff is tied. FanGraphs supplies
  the 2026 opening balance; StatsAPI supplies in-season service through the as-of date.
- The control build now retains all 230 official responses used by the current
  checkpoint as hash-verified canonical JSON. This makes the parsed source values
  reproducible after the live API changes. An offline league rebuild reproduced
  all core tables, summary and manifest byte for byte. The manifest does not claim
  original HTTP-byte fidelity or an unavailable retrieval timestamp.
- Historical FanGraphs Opening Day Tracker captures add MLBAM-keyed 2024 and 2025
  service/options baselines for 2,012 and 2,024 players. They cover all 30 teams and
  avoid name matching. Because the pages were retrieved later, they are accepted for
  retrospective event-cutoff replay, not true vintage-information claims. Historical
  contract obligations remain the material Step 8 source gap. Member workbooks
  independently reproduce every overlapping 2024–2025 control field, add Opening Day
  PA/IP projections, and extend the source back to 2,065 players in 2023. Their raw
  and normalized bulk data remain private.
- A 30-team Cot's-derived 2025 extract has now been inspected as a potential private
  retrospective contract bridge. It includes 2025–2029 salary/control columns but was
  created after the season and has names rather than MLBAM IDs. Use requires a
  same-team name match corroborated by service; it is not vintage or primary authority.
  Its implemented parser produces 1,289 players and 6,445 annual terms; 1,192 players
  attach to MLBAM by exact team/name/service agreement. Ninety-seven remain review.
  The annual valuation gate accepts 1,308 guaranteed salary rows, routes 1,125
  arbitration rows to the CBA calculation, ends control on 473 free-agent rows and
  holds back 118 option rows. Only seven exact-identity numeric cells remain unclear.
- The first 2025 historical projection path now covers 3,891 hitters and 5,090
  pitchers through 2029. The one-year opportunity models were refit using targets
  only through 2024; later years use pre-2025 historical fallbacks. FanGraphs PA/IP
  are external scale checks, not model inputs. The full 2025 universe receives
  183,343 expected hitter PA and 180,383 expected pitcher BF. Eight hitters and 24
  pitchers added by the Opening Day workbook retain labeled population fallbacks.
- The first historical control/value join now connects 7,998 of 8,946 projected
  players to an incumbent owner. FanGraphs supplies 2,019 Opening Day owners; dated
  official 40-man and transaction evidence resolve 199; 5,780 use the unique October
  2024 official full-roster owner. The remaining 948 players stay talent-only. Of
  39,990 owned annual rows, 39,648 calculate and 342 remain review for 33 missing
  service balances, 118 option years, 52 2025 Super Two cases and seven unclear
  contract cells. This is retrospective research evidence, not a ranking.
- The frozen 2025 replay is now scored. Hitter PA is 0.2% high and pitcher BF is
  0.9% low at league scale. Both models improve RMSE over carrying 2024 workload
  forward but lose on MAE; FanGraphs is materially better on its projected-player
  subset. Hitter and pitcher components beat their population log-loss references.
  Whole-player neutral WAR is 1,061.71 projected versus 995.75 observed, 6.6% high.
- The March 2025 value output passes the sequential checkpoint contract with 8,946
  players, 7,803 available values and 1,143 reviews. Joined to the September 2026
  current checkpoint, all 3,850 material deltas have declared reasons. Model and
  universe changes mean this proves mechanics, not same-model value stability.
- The exact March models now also run at an October 15 checkpoint without refitting.
  Official ownership and service evidence produces 7,749 usable October values. Among
  5,660 shared usable players, value correlation is 0.691; all 4,049 material changes
  have declared reasons. Every usable March and October value carries a Phase 1
  reference range. Median remaining-WAR width narrows from 2.76 to 2.07 WAR. These
  ranges are not calibrated coverage guarantees and omit cross-season covariance.
- Contract Economics v0 now keeps WAR, free-agent-equivalent value, contract/control
  value and later trade value separate. It values guaranteed, tender, club-option and
  player-option states, preserves optionality premium, discounts future values and
  fails closed on unresolved option triggers. Official 2022–2026 minimum salaries live
  in a versioned CBA ruleset. FanGraphs' published 2026 three-tier market curve is now
  the main reference; future growth and arbitration remain named assumptions rather
  than hidden constants.
- Projection v1 now has a common guardrail contract and executable audit. Every player-
  year must decompose expected WAR into MLB-active probability, conditional WAR rate
  and conditional PA/BF workload. Current-team depth is forbidden, hitter/pitcher
  components for two-way players remain separate, controlled WAR is summed directly,
  and pre-cutoff historical extremes are flagged without clipping. This is an
  interface and diagnostic layer; it does not claim the missing projection models are
  complete.
- Hitter Opportunity v1 now implements the first universal forecast input. It preserves
  zero-MLB outcomes, can use a frozen selected one-year model when supplied, and fills
  unsupported/later years with horizon-specific age/level cohorts and labeled
  population fallbacks. It never uses team depth or a PA cap and composes directly into
  the Projection v1 WAR schema. Historical cohorts and the current league snapshot are
  fitted. The confirmed B2 form's scoring parameters are not available, so the current
  materialization honestly uses the cohort fallback.
- Pitcher Opportunity v1 now applies the same separation to MLB arrival, conditional
  BF and starter/swingman/reliever probabilities. Sparse age/level/role cohorts shrink
  through a disclosed hierarchy, all fallback sources remain labeled, and the output
  composes with conditional WAR/800 BF and control seasons. Its historical league panel
  and current league snapshot are fitted.
- The official historical opportunity source is now collected for 2018–2024. Because
  `fullRoster` omits hundreds of players with official affiliated stats each year, the
  cohort denominator is their union. The misleading `totalSplits` field is ignored in
  favor of verified pagination. Excluding the cancelled 2020 MiLB season leaves 74,743
  hitter and 90,727 pitcher zero-inclusive cohort rows across horizons 1–6.
- The dated 2026-09-08 snapshot now produces complete 2027–2032 paths for
  3,940 hitters and 5,276 pitchers. Official position evidence reduced false two-way
  classification from 436 players to 22 by excluding incidental mop-up pitching. The
  current hitter and pitcher runs use their new provisional universal models for 2027
  and labeled historical fallbacks for 2028–2032.
- A newly versioned universal hitter-opportunity candidate now replaces the expired-
  artifact dead end without claiming to recreate B2. The precommitted rolling gate
  retains inactive, unknown-level and missing-age players and uses only level, age,
  current MLB/MiLB PA and exact-date 40-man membership. It beat the universal level-only
  model in all four 2022–2025 evaluations; pooled Brier error fell 20.5% and PA RMSE
  fell 26.1%. Its complete scoring package is committed, but it remains a provisional
  2026 candidate until a future protected-outcome confirmation.
- A matching universal pitcher gate now retains zero outcomes and current role while
  adding age, current MLB/minor-league BF and exact-date 40-man membership. The selected
  form won all four rolling folds; pooled Brier error fell 10.5%, BF MAE 15.1% and BF
  RMSE 10.5% against level/role only. Its exact package is committed and remains
  provisional pending protected 2026 confirmation.
- Direct horizon 2–4 models also passed every gate against both their parametric
  baselines and the incumbent cohort method. Hitter PA MAE improves 12–20% and pitcher
  BF MAE 6–8%. Incomplete 2003–2008 sources cannot support honest horizon 5–6 tests,
  so those years retain their labeled historical fallbacks.
- The selected models now score the current universe and connect through WAR,
  uncertainty, current remaining rights and contract economics. They add 564.59 future
  WAR through 2030; 2031–2032 are unchanged. The separate remaining-2026 estimate falls
  1.46 WAR. The scenario still
  has 50,898 annual rows, 8,332 complete controlled-player paths and the same 16 contract reviews.
  Its $5.89 billion discounted point total versus the retained $1.66 billion baseline
  is a research sensitivity, not a promoted ranking.
- The protected 2026 one-year confirmation is now locked before season end. Immutable
  selected, U0/P0 and incumbent forecasts cover the exact 2025-10-15 universe of 3,907
  hitters and 5,206 pitchers. No 2026 outcome file was read. The fixed confirmation
  rule waits for final official regular-season PA/BF and cannot be changed by subgroup
  results.
- The remaining-rights timeline now prevents live valuation from counting WAR already
  produced or salary already paid. Current-season rows require an explicit remaining
  salary obligation and cannot receive a fictional midseason non-tender option. Future
  rows retain full-season production, cost and decision states. Rest-of-season WAR and
  unpaid salary sources are the remaining live-2026 inputs.
- A current Phase 1 conditional-WAR baseline now joins recent official MLB skill
  evidence to all 2027–2032 opportunity rows: 23,640 hitter and 31,656 pitcher
  player-years. Recent-MLB players receive regressed component estimates; all others
  retain explicit population priors. Hitters include batting, primary position and
  replacement while missing defense/running begin as average-zero fallbacks. Pitchers
  use the validated five-part BF baseline and a disclosed Tango adjacent-aging
  fallback. No team depth or rate clipping is used.
- Official 2023–2026 affiliated components now feed a provisional MLB-anchored
  translation fitted on 3,204 hitter and 4,495 pitcher same-player/same-season mover
  pairs from completed 2023–2025. All six levels connect to MLB. Level-based evidence
  discounting plus 1,200-PA hitter and 800-BF pitcher priors replaces most pure
  population fallbacks without allowing raw lower-level rates to dominate a
  conditional-on-future-MLB estimate.
- The affiliated translation improved component log loss and Brier score against the
  same no-translation model in both 2024 and 2025 future-MLB folds for hitters and
  pitchers, and beat the MLB population prior in all four comparisons. It is retained
  as the simple Phase 1 rate fallback; longer replay and subgroup calibration are
  Phase 2 rather than blockers to the coherent baseline.
- Official no-debut evidence now supplies a zero opening service balance only when a
  FanGraphs opening balance is absent. A first debut during the current season also
  proves a zero opening balance; this safely adds Felix Reyes. Earlier debuts without
  a verified balance still fail closed. The six-year future-control path now covers
  8,343 players; unresolved service cases remain null rather than becoming free agents.
- Whole-player expected WAR now joins all 50,058 future-control rows, adding hitter
  and pitcher value for two-way players. Accepted payroll terms supply 610 known
  player-year salaries. The 4,938 projection rows without resolved control stay in the
  talent universe but do not receive invented incumbent rights. All 86 potential
  payroll buyouts map to stable player IDs. With the small dated Spotrac exception
  overlay, 97 projected option rows carry a buyout and 56 remain missing. The ten
  projected Super Two cases now advance
  through all four arbitration classes. Arbitration pay, post-2026 minimums and the
  remaining option exceptions stay explicit rather than becoming hidden defaults.
- The public 2020–2026 FanGraphs tracker supplies 335 reported contracts and all 350
  sampled rows map to MLBAM through the pinned Chadwick register. An independent 143-
  deal one-year reconstruction uses only prior StatsAPI history. On 18 clean 2026
  deals it projects 27.05 WAR versus FanGraphs' 25.40, but the one-year sample does not
  identify the multi-year star premium. The published $6.74M/$8.51M/$12.84M tiers
  therefore remain the main 2026 market reference.
- Arbitration cost now uses the externally tested FanGraphs 15%/35%/50%/75% class
  shares and prior-season projected WAR value. There are 23,291 true prior-season
  basis rows and 393 labeled first-horizon proxies. A complete research scenario now
  calculates 49,999 of 50,058 future annual rows; 59 rows remain in review for option
  buyouts, vesting triggers or one missing salary.
  Three linked Julio Rodriguez structure rows are machine-enforced reviews, so a
  later dollar-term fill cannot silently value the wrong option type.
  Official MLB reporting corrects Tatsuya Imai's 2027–2028 states to player opt-outs;
  a current official report confirms FanGraphs' Pivetta club-option conversion.
  All 13 vesting rows now have sourced, machine-readable triggers. The live evaluator
  reuses retained official StatsAPI totals and the official schedule calendar. As of
  2026-09-08, Yandy Diaz's 500-PA trigger is vested (620 PA), Chapman's 120-out
  threshold is met but its physical is pending (146 outs), and Freeland remains
  pending at 373 of 510 outs. Medical and alternate conditions remain explicit.
  Yandy's final result now changes his 2027 state to a guaranteed $13M season before
  economics are calculated; pending triggers do not alter their contract states.
  The exact-input result is 49,999 of 50,058 rows. A separate named Phase 1
  buyout estimate uses observed option-type median shares for 43 rows with no reported
  buyout. Official MLB reporting also corrects Kyle Tucker's 2028–2029 states to
  player opt-outs, raising the research scenario to 50,210 available rows and leaving
  16 reviews across 11 players. Estimated rows are labeled and do not become source facts.
  Twenty-nine fully specified mutual options now use the conservative normal-expiration
  outcome instead of waiting for a separate decision model.
  The post-2026 minimum and unchanged service rules are explicitly a planning scenario,
  not a claimed successor CBA.
- All 55,164 future whole-player seasons now have a Phase 1 uncertainty reference
  range based on historical positive-workload variance plus event and posterior-rate
  variance. All 50,058 future economics rows receive the bounds. The median annual
  width is 0.51 WAR, and opportunity accounts for 56.2% of modeled variance. The
  range is not yet an out-of-time coverage guarantee or correlated career simulation.
- The frozen Player Value v1 baserunning models now supply current hitter rates from
  official 2023–2026 steal counts and four league-wide Savant advancement files. In
  2027, 3,776 of 3,940 hitters have recent evidence; the three-year model then fades
  to its centered neutral fallback by 2030.
- Frozen U1 general-range defense now covers 1,519 hitters for 2027 using 13,192
  official current fielding rows, prior MLB position outs and the frozen native run
  conversion. Expected defense is position-centered to zero. Unsupported hitters,
  catcher-specific components and 2028–2032 remain explicit neutral fallbacks.
- A modern pitcher-aging challenger was fit on regressed same-pitcher adjacent MLB
  profiles and tested on 2,442 later-period pairs covering 618,983 BF. It lost to both
  no aging and Tango overall; Tango beat no aging in three of four seasons and remains
  the Phase 1 curve. The failed challenger is closed rather than tuned after inspection.
- A dated 2026 rest-of-season baseline projects 114.35 WAR before current availability
  and 105.10 after 247 official season-out statuses plus the narrow historical
  injury-return adjustment over the final 250
  scheduled games. CBA championship-season-day proration produces $535.96 million of
  remaining base salary. Exact current-team matches connect 844 salary rows and
  $508.08 million to the remaining-rights interface; 70 unresolved or conflicting
  rows remain explicit rather than being forced into value. The combined economics
  input contains these 840 current rows plus 50,058 future rows.
- The combined current-and-future economics run now values all 50,898 annual rows in
  one path. It produces complete discounted point and sensitivity totals for 8,332
  players, while the same 16 known contract rows keep 11 players in review. Current
  partial-season WAR uses FanGraphs' published overall 2026 rate rather than an invalid
  full-season player tier. The result remains a research scenario because post-2026 CBA
  rules, opportunity recovery and interval calibration are not final.
- Ordinary IL and rehab status does not itself supply a return date. Official current
  status and transaction replay agree for 263 players; 261 projected players receive
  the 2022-2025 activation-timing factor. Their 10.92 unadjusted WAR becomes 1.84 WAR.
  Unmatched injuries retain their point and zero-to-baseline range. Among matched
  current rights, the combined 80.08 WAR point has an availability-only 78.37 to
  87.72 range. Minor assignment is not used as team-depth blocking.
- A 30-day official workload challenger now redistributes the existing late-season
  league total without adding PA/BF or using team depth. It improved 2025 confirmation
  MAE from 14.76 to 12.01 PA and 16.08 to 13.49 BF. The live build keeps 21,596.6 PA
  and 20,597.7 BF unchanged while moving work toward recently used players.
- The Phase 1 sequential-replay contract and engine are now implemented. The first
  current checkpoint retains all 8,393 rights-universe players, provides 8,369 usable
  records and keeps 24 review players visible. The usable set contains 8,332 controlled
  values plus 37 talent-only rows with zero incumbent trade rights. It validates event cutoffs, true-vintage labels,
  universe/owner coverage, value bounds and material-change reasons. This proves the
  present integration interface; it is not yet a historical accuracy result.

Contracts and results: [rights universe](player-rights-universe-contract.md),
[full-roster source decision](affiliated-full-roster-source-result.md),
[transaction ledger](rights-transaction-ledger-contract.md),
[current organization resolution](current-organization-resolution-2026-09-09.md),
[career panel](career-outcome-panel-contract.md),
[career inventory](career-mlb-outcome-inventory-result.md),
[pitcher baseline](pitcher-component-baseline-result.md).

## Completed research

- Recovered the original 2024 opportunity forecast and verified exact IDs and
  official targets against O2026D. Its lower errors support reuse of the older
  model, with documented subgroup limits. [Comparison](recovered-opportunity-comparison.md).

- Tango-focused review executed: saved translation forecasts still improve
  common-MLB-centered absolute error; historical-support subgroups remain
  descriptive and selection risk remains. The old richer opportunity model has
  promising recorded results and should be recovered for an identical-target
  comparison. [Evidence and next work](tango-focused-model-work.md).

- C2026A: two all-level output-calibration candidates failed.
  [Result](hitter-v2-C2026A-result.md).
- T2026B: one competition-normalized history candidate failed its prospective
  all-level gate. Its presaved MLB-conditional component materially improves
  prediction for prior-minor players but still needs calibration and confirmation.
  [Result](hitter-v2-T2026B-result.md).
- C2026C: two MLB-specific calibration candidates failed. The error audit shows
  much larger optimism among brief MLB call-ups than among players with 100+ PA.
  Future exposure is a diagnostic label, never a preseason predictor or exclusion
  rule. [Result and next step](hitter-v2-C2026C-result.md).

## Next modeling task

The main denominator, control/cost path, integrated current-plus-future economics
engine, projection
guardrails, opportunity paths, conditional-WAR assembly, annual economics-input join,
current baserunning, supported general defense, the rest-of-season path, a narrow
official-status availability boundary and Phase 1 future WAR ranges are now built.
The one-year confirmation forecast and scoring rule are frozen. Do not inspect partial
2026 targets or tune the completed gates; run confirmation only after official regular-
season totals are final. Horizons 5–6 remain on the incumbent until better older
evidence exists. The Phase 1 coherent research path is complete under its declared
boundaries: the 2025 projection, control, value and reference-range paths run together,
outcome scoring is recorded and the multi-checkpoint sequence passes. The same-model
later projection checkpoint now exists:
the exact pre-2025 opportunity fits are committed and hash-verified, and the October
15 update uses completed 2025 evidence without refitting. The matching October
owner/control/economics join and same-method value comparison now pass. They resolve
8,079 owners, produce 7,749 usable values and explain all 4,049 material value moves.
Do not treat this descriptive update as an outcome-accuracy score or authorization to
publish player rankings. The next hard evidence gates are the protected 2026 score
after the regular season and the successor CBA. Remaining service, Super Two and option
exceptions should be resolved only when their value impact warrants it; granular
calibration and component improvements belong in Phase 2.
The 948 missing-owner players and bounded contract/service exceptions stay separate
rather than forced. In the current snapshot, 16
annual contract reviews remain: 12 future vesting
decisions, three linked Julio Rodriguez years and one missing option salary. Granular replacement of the
43 buyout estimates with exact terms is Phase 2. Current role and late-season injury return
now have narrow Phase 1 baselines. Correlated
multi-year uncertainty and empirical coverage refinement belong in Phase 2.
Modern adjacent-season pitcher aging has been tested and rejected for Phase 1; revisit
it only under a new Phase 2 test.
The market-price and Phase 1 arbitration gates are complete. The remaining economic
blockers are successor-CBA facts and the 16 remaining scenario review rows.
The 21 multi-organization ownership cases are closed by the dated 40-man/transaction
resolver. Continue only the bounded contract/CBA exceptions. Do not
publish dollar rankings from placeholder market or arbitration assumptions.

The lost B2 package has now been replaced for forward development by a reproducible
universal v2 candidate. Its current scoring and provisional downstream integration are
complete. Retain O2026D as a simple benchmark and T2026B as a developmental hitter-rate
reference. Stop global hitter calibration searches until the protected confirmation.

The selected B2 hitter-opportunity run is still identified by run `32142220469` and
its expected candidate hash, but GitHub's short-lived coefficient artifact has expired.
The surviving independent 2025 confirmation artifact has now been preserved in
`model_artifacts/playing-time-v1-confirmation-2025/`, with a hash manifest and tests.
It contains scores, not coefficients, and the local archive contains only a different
2024 fold fit. The old run log also contains no coefficient values. Do not silently
refit under changed inputs. Recover the exact frozen package if an external copy exists;
otherwise keep the current proven fallback and rerun a newly versioned selection gate.
All future selected parameter packages must follow
`docs/playing-time-v1-durable-artifact-policy.md`.

The 2022–2024 seasons are disclosed development evidence. Protected 2026 remains
closed. Do not claim long-term value or publish a model from these findings.
Preserve original G0/C0/Marcel benchmarks and all failed decisions.

## Reproduction

New model primitives have chronology, gradient, probability-conservation, and
player-cluster resampling tests. The runners require existing generated research
artifacts; hashes bind the inputs. They reject overwriting an inspected candidate
run. The local implementation passed its tests before this branch was prepared;
branch-specific verification is recorded in the pull request.

Current focused verification: opportunity, economics, guardrail, remaining-rights and
current-availability tests pass; Ruff passes across the changed files. The latest full
run has 1,408 passing tests. Four pre-existing hitter research-contract tests fail only
because their hash-bound ignored research artifacts are absent in this checkout. No new
test failure was observed.

### Prospect uncertainty research

- The accepted private-preview range varies MLB arrival and six-year workload while
  holding skill fixed. It covers all 6,719 pre-MLB paths and exactly preserves point
  values.
- A second research-only layer now combines that mixture with the model's existing
  event and posterior rate variance. It also preserves every point mean, but P10-P90
  does not widen consistently because the career distribution contains a large exact
  non-arrival mass.
- Do not expose the component layer as a calibrated confidence interval. Next test its
  historical coverage by player type and predeclared probability band, using only
  information available at each forecast date.
- Neither uncertainty layer uses outside player FV opinions or partial 2026 outcomes.
- A conditional workload cohort-stability check compared 2015-2017 debuters with
  2018-2019 debuters, but it is descriptive only and cannot set calibration status.
- Timing audit correction: the earlier cohorts' six-year outcomes extend beyond the
  later cohorts' debut dates. This is not a chronology-safe forecast backtest and
  cannot confirm either workload method. The distribution shift remains descriptive.
- The official career backbone is now locally extended to 2009-2025 (generated data),
  with 3,015,872 batting PA exactly matching pitching BF. A lean batched StatsAPI
  people pull resolved exact debut dates for all 5,321 observed players. This is
  enough to rerun the conditional workload check with training windows that truly end
  before each 2018-2019 evaluation cutoff.
- That corrected as-of replay passes the conditional workload method. Pitcher P10-P90
  coverage is 81.1% (95% Wilson interval 76.7%-84.8%) and P25-P75 coverage is 47.7%.
  Hitter central coverage is 53.2%; its P10-P90 range is conservative at 90.6%.
  Remove the old pitcher under-coverage warning. This validates conditional workload,
  not arrival, predicted tier/role, skill, WAR, or end-to-end value.
- Do not fit a pitcher widening factor. The valid as-of replay supports the current
  conditional workload range; remaining uncertainty work belongs in arrival, skill,
  aging, injury, and the tier/role mixture.
- The first frozen pitcher era diagnostic rejected all eight simple fixes. A one-year
  recency half-life modestly improved overall and established-career CRPS but breached
  the supported fringe-tier safety limit and did not repair coverage. Always pooling
  roles widened coverage but materially worsened CRPS. Next separate the league-wide
  pitcher-usage environment from a player's role-relative workload distribution.
- A parallel frozen hitter demographic component test rejected age-for-level,
  batting side, and their interactions. Every family improved the 2024 development
  scores, but the selected interaction worsened both untouched 2025 scores and every
  supported demographic split. Stable demographics therefore receive no direct
  hitter skill bonus.
- The hitter affiliated-component regression audit selected 400 PA on 2024 and
  improved both frozen 2025 point scores versus the current 1,200-PA prior, but both
  player-bootstrap 95% intervals narrowly crossed zero. Retain 1,200 PA. The result
  argues against applying more shrinkage merely to suppress the prospect top end.
- The official MLB pitcher-workload environment audit explains the later-cohort
  distribution shift. Active pitchers increased 13.2% from the 2015-2019 era to 2021-2024,
  while mean/median BF per pitcher fell about 13% and P90 BF fell 16.3%. More pitchers
  also recorded a start, partly because openers and bullpen games make a start count a
  weak proxy for a rotation role. Next model workload relative to the season
  environment and distinguish rotation starters, openers, bulk/swing pitchers, and
  relievers using start share and BF per start. Never boost raw pitcher BF to achieve
  a preferred prospect-value distribution.

The prior long status file is preserved in
[project history through August 26](project-history-through-2026-08-26.md).

### Dependent career-path value research

- The first research engine now simulates arrival timing, a complete six-year
  historical workload/role path, persistent skill uncertainty, annual event noise,
  active-season control, cost, nonlinear market value and discounting together.
- It covers 6,719 pre-MLB players with 2,048 deterministic draws. The historical
  library retains 3,945 hitter/pitcher career paths, zero seasons, returns, attrition
  and pitcher role transitions. No publication FV or rank is an input.
- This remains separate from the main ranking. Any active season still counts as one
  full service year; Super Two, partial service, forecast-time non-tenders,
  guarantees/options and the successor CBA remain provisional or pending.
- A separate 8,192-draw sensitivity on 300 players produced 0.9924 value-rank
  correlation. Fine differences still move: the P90 absolute value change was
  $1.05M. More draws or lower-variance integration is needed before promotion.
- The simulator did not introduce a catcher preference. Catchers were 23% of the old
  and new top-100 hitter lists. Pitcher compression predates it: the old pre-MLB top
  100 already contained 99 hitters and one pitcher.
- A five-fold 2024 pitcher demographic breadth audit rejected birth-country-only,
  age/hand/country and age-by-country families because they worsened both proper
  scores. Current height and weight were not tested against old outcomes because
  using 2026 physical measurements would leak future information.
- The accepted historical tracking artifact needed for a new pitch-quality tier has
  expired, along with upstream workflow artifacts needed to recreate it. Do not
  pretend the checkout contains that source. Rebuild the full source chain before a
  tracked pitcher-quality challenger.
- Current structural verification is 21/21 model-law checks. The latest full suite is
  1,432 passing tests plus four known missing-artifact failures; no new failure exists.
### Current-organization pitcher role capacity (research layer)

- Frozen role definitions and a 2021-2024 development / 2025 confirmation split before scoring.
- Split each current pitcher forecast across starter, swingman, and reliever probabilities instead of forcing a hard role.
- Starter capacity was not exceeded; relief and swingman crowding reduced current-team BF mainly in 2027-2029.
- This remains a team-context scenario only. It does not change pitcher talent, WAR rate, or portable player value.
- Next gate: historical roster-construction replay before displaying team-fit adjustments.

### 2025 historical team-capacity replay

- Replayed the frozen 2025 Opening Day forecasts against full-season MLB PA/BF using only 2021-2024 capacity rules.
- The broad team cap improved pitcher RMSE and MAE with clustered intervals below zero; hitter changes were small and uncertain.
- Rejected rigid hitter-position caps: they materially worsened RMSE and created a large workload shortfall.
- Did not promote rigid pitcher-role caps: MAE improved but RMSE did not, and every pitcher was reduced through fractional crowded-role exposure.
- Next challenger must allow dated, evidence-based multi-position and pitcher-role flexibility before any within-team workload is discarded.
