# Deep baseball-methodology review: reopen the right failures

2026-09-25. Review-only milestone. No fitting, new model selection, forecast
replacement or protected 2026 performance access. This extends—not repeats—the
[previous accounting audit](model-decision-audit-2026-09-25.md).

**Conclusion:** several negative findings were interpreted more broadly than the
tests support. Most importantly, the minor-league infield range measurement does
not consistently assign missed ground balls to infielders, conditional workload
uses a different weighting population than participation, and a useful defensive
component can lose the total-value comparison through other-component error
interactions. These need targeted repair, not another engine tournament.

## Scope and what was actually verified

Reviewed the main lines of work: historical population/coverage, hitter and pitcher
tournaments, contact and park/opponent tests, level translation and repeaters,
arrival/workload/COVID experiments, health/contracts, fielding/position/catchers,
running, multi-year means, career distributions and control value. The result-file
index contains 221 Markdown documents; indexing them is **not** a claim that every
old experiment or every source pipeline was rerun. Many older results are JSON-only
and are not included in that count.

New source/data checks concentrate on the consequential claims:

- 244 pre-2026 PBP terminal partitions, 2016–2019 and 2021–2024, with input hashes;
- exact ground-ball first-touch attribution and catcher narrative counts;
- the archived 3,929-player 2025 outfield/component bridge;
- activity/workload training functions and all 12 retained D fit manifests;
- 52,181 archived annual integration rows and their prospect subgroups.

`scripts/review_baseball_methodology_v1.py` reproduces these diagnostics in
`model_artifacts/baseball-methodology-review-v1-2026-09-25/diagnostics.json`.
It removes exact repeated rows and excludes 2,234 conflicting game/PA keys in
the selected diagnostic fields. Consequently its PBP counts need not equal older
reports that kept the first copy. This is disclosed denominator handling, not
a revised model dataset. Unknowns are not silently recoded as successes/failures.

Verification: 34 focused tests pass, including six new diagnostic tests. Both
the original 31-file forecast freeze and the latest arrival-coherence delivery
verify unchanged for 3,907 players. Protected outcomes were not used. Local
Markdown links were checked. This certifies the review diagnostics and preserved
artifacts, not the predictive success of the proposed repairs.

## 1. Infield range: the opportunity definition misses an essential failure mode

**Confirmed implementation problem; reopen the measurement before re-testing.**

`pbp_opportunity_events.py` sets `responsible_position = hit_location`, then uses
the player at that first-touch position. `historical_fielding_range.py` retains
positions 4/5/6 for the infield range experiment. A ground ball through shortstop
that is picked up in left field therefore never becomes a shortstop opportunity.

Across the reviewed terminal ground balls:

| Outcome | Total balls | First touch 2B/3B/SS | First touch outfield |
|---|---:|---:|---:|
| Hits/errors | 594,742 | 205,816 | 341,625 |
| Outs | 1,414,328 | 1,093,354 | 270 |

Thus **57.4% of non-out ground balls go to an outfielder**, outside the infield
range denominator. Not every one should be a debit to a particular infielder;
responsibility is uncertain and includes 1B/pitcher. But excluding them all from
the 2B/3B/SS opportunity construction cannot establish complete infield range.

The reported persistence is evidence about converting the balls a player touches,
plus contact/recording effects—not yet a certified measure of reaching all balls
he should reach. Heavy regression, park correction and RE24 conversion cannot
repair that attribution problem. The failed MLB bridge does not establish that
ordinary PBP cannot project MiLB defense.

This is not just an intuitive objection. Sean Smith's
[Total Zone description](https://www.baseball-reference.com/about/total_zone.shtml)
allocates ground-ball hits reaching the outfield back to neighboring infield
positions; it does not equate the recovering outfielder with the responsible
infielder. The search-indexed primary description was available; direct page
access returned 403. Lichtman's [UZR primer](https://blogs.fangraphs.com/the-fangraphs-uzr-primer/)
likewise frames opportunity around ball characteristics and average positional
responsibility, including hits allowed. We should use those principles without
claiming our untracked coordinates have UZR precision.

**Repair:** a complete candidate opportunity ledger with shared responsibility
for through-the-infield hits, explicit 1B/pitcher/unassigned shares, and conservation
checks. Do not choose the "nearest fielder" from coordinates until their meaning
on hits versus outs is certified. Check arm/OF responsibility too; this audit
quantifies the infield flaw, not an identical outfield failure rate.

## 2. Catcher negatives: incomplete event capture is not a clean skill test

**Confirmed extraction restriction; severity needs same-game reconciliation.**

The throwing and deterrence extractors identify attempts from terminal PA English
narratives, not a reconciled inventory of runner events. In our distinct-play
diagnostic there are 26,465 caught-stealing mentions versus 12,705 successful-steal
mentions after removing pickoffs and missing battery IDs: about **67.6% caught**.
The old throwing report independently shows 67.5% on its narrower clean sample.

That unusual composition is a source-representativeness alarm, not a measured
league caught-stealing rate. We have not yet compared these exact games with
official SB/CS counts, so do not invent a precise missing-event percentage.
Deterrence also uses eligible PA starts and observed terminal pitch count; that
count can itself be affected by a steal ending the inning. It is not simply
pre-opportunity exposure known independently of the result.

Broad blocking still recognizes failures from PA narratives, with dirt-pitch
candidate and continuity restrictions. Expanding from one dirt pitch to several
does not establish unbiased PB/WP capture. The prior claim that this "confirms"
the available all-level data cannot separate blocking skill is too strong.

**Repair:** audit event recall by outcome, season and level against official
same-game counts; distinguish unknown events from true non-attempts. Only then
decide whether to rebuild the throwing/deterrence/blocking test. No immediate
catcher WAR bonus, no assertion that a repaired test must win. Battery walk
support remains separate: new-pitcher transport was uncertain and framing can
contribute to its walk association.

## 3. A failed whole-model addition can conceal a better component

**Confirmed mathematical and empirical distinction.**

On the same 3,929 players in the outfield fallback's 2025 bridge, versus neutral
general defense, squared error changes decompose as follows (wins squared):

| Contribution to total MSE change | Change |
|---|---:|
| Defensive component error | -0.00061234 |
| Interaction with errors in the other components | +0.00119135 |
| Whole-player error | +0.00057901 |

The identity is `total change = component change + 2*mean(other error * added forecast)`.
The adverse interaction more than offsets the better measured defense component.
It may reflect correlated model errors, target attribution or systematic bias;
the decomposition does not decide which. It also does not establish that the
MiLB replacement itself is responsible for the component improvement: that arm
retains other existing defensive predictions. Compare replaced-player and
unchanged-player rows separately before making that claim.

Consequences:

- The no-deployment decision remains reasonable; total prediction did worsen.
- "General defense contains no useful signal" and "only the defense skill layer
  is the remaining problem" do **not** follow.
- Position/running/catcher additions must receive the same interaction analysis,
  whether they helped or hurt. A compensating error is not a portable improvement.
- Repair/test the measurement first, then examine component bias and residual
  dependence. Do not add a post-hoc coefficient that merely cancels batting error.

## 4. Workload weights change the quantity being estimated

**Confirmed weighting mismatch; causal forecast impact untested.**

The activity fit weights each player equally across his eligible historical
snapshots. The conditional PA fit first keeps only active outcomes, then
recalculates equal-player weights. Therefore a player's active snapshots get a
different relative weight in the two fits. This is not future-data leakage—the
rows are mature—but the two heads do not use one common weighted population.

For the 2021-origin Year-1 fit:

| Training summary among actual MLB participants | Mean PA | Share with 450+ PA |
|---|---:|---:|
| Equal rows | 284.3 | 27.7% |
| Preserve activity-fit weights after conditioning | 268.0 | 24.8% |
| Recompute weights after conditioning: current D | 212.2 | 17.1% |

Years 2–3 show the same direction: common-measure means 270.9/271.5 versus
214.0/217.0 under the current recomputation. Short MLB careers receive more
relative influence; regular seasons receive less. Equal-person weighting can
be a deliberate research objective, but it is not automatically calibrated for
the equal-origin, all-player-snapshot mean being scored or future league totals.

These averages are not fitted predictions and do not prove that changing weights
improves RMSE. The learner conditions on many features, and different weighting
can change variance as well as bias. Reopen a single controlled comparison,
not a mandate to increase everyone's playing time. Use common weights in both
heads as the coherence test; inspect player-year versus player-level objectives
explicitly rather than treating repeated players as a reason to change the mean
target. Cluster uncertainty instead of confusing clustering with training weights.

## 5. "2021" is not one problem, and the diagnosis changes by horizon

A 2021 cutoff predicts 2022 in Year 1, 2023 in Year 2 and 2024 in Year 3.
The observed outcomes are not a canceled 2021 season. Historical background:

- MiLB entered a 120-team reorganized affiliated structure in 2021.
  [MLB announcement](https://www.mlb.com/news/new-minor-league-affiliates-for-2021)
- Universal DH and temporarily expanded active rosters arrived in 2022.
  [MLB rules announcement](https://www.mlb.com/news/mlb-rule-changes-for-2022)
- Shift restrictions, larger bases and disengagement limits arrived in 2023.
  [MLB rules FAQ](https://www.mlb.com/news/mlb-new-rules-for-2023-faq)

These are candidate explanations for changed opportunity/results, not a fitted
causal decomposition. Rules announced after December 2021 cannot be supplied
as known predictors in a December-2021 backtest. Later stress scenarios may
illustrate them but must not retroactively improve the forecast.

New exact error decomposition for the **3,250 never-debuted 2021 prospects**:

| Target year | Predicted / actual participants | Total PA error | Activity-related PA error | Conditional-workload PA error |
|---|---:|---:|---:|---:|
| 2022 | 84.7 / 157 | -6,155 | -9,753 | +3,597 |
| 2023 | 115.7 / 219 | -24,578 | -15,440 | -9,138 |
| 2024 | 199.5 / 278 | -18,633 | -17,523 | -1,110 |

For forecast `p*q` and realized PA `w`, the diagnostic identity is
`p*q-w = (p-1[w>0])*q + 1[w>0]*(q-w)`.
The first term weights participation error by predicted conditional PA. The
second evaluates conditional workload on actual participants. Realized activity
is used only for explanation, never as an input or deployable oracle forecast.

In Year 1 the conditional head already **overpredicts** the workload of actual
arrivers in aggregate; increasing it cannot be called the missing-arrival fix.
In Year 2 both pieces underpredict. The 2022-origin cohort instead overpredicts
next-year participants (126.3 versus 106). A blanket prospect/COVID multiplier
would therefore address the wrong thing in some cells.

Earlier canceled-input repairs helped 2021 and hurt 2022. That is evidence of a
source-meaning issue but not proof of a validated two-year repair. A schedule-only
feature did not isolate cohort selection or lost development. Keep 2021 visible;
do not declare the model sound merely by dropping it or claim every other value
gap is explained by it.

### Ten seasons of files do not mean ten comparable training seasons

For 2021, retained D training ends with 2019 outcomes at every horizon because
of the pandemic-crossing exclusion. The Year-3 active set has 4,941 rows and
1,373 players, but only 930 rows have the current contact-availability flag.
Only 424 detailed columns vary enough to be used. The earliest Year-3 fit uses
98 columns, not the full detailed panel. Some of this contact support is MLB
history, not all-level minor-league coverage.

This does not invalidate chronological training. It limits the claim that a
negative long-horizon result was a well-supported test of every detailed input.
Every future result needs effective training support by feature family and
relevant player group, not the gross number of PBP rows on disk.

## 6. Which failed approaches deserve another look?

| Failed or inconclusive work | Methodological limitation | Disposition |
|---|---|---|
| MiLB infield range → MLB value | Outcome-dependent first-touch denominator; transport/exposure and old target support also matter | Reopen measurement first; do not repeat old bridge unchanged. |
| OF/general defense → whole value | Own-component improvement opposed by other-error interaction; selected fallback differs from whole arm | Reopen interpretation and attribution; no automatic promotion. |
| Catcher deterrence/throwing/blocking | Narrative event selection and incomplete opportunity certification | Reopen event-source gate, not another shrinkage grid. |
| Park/opponent adjustments | Some tests correct only home exposure; road parks remain; early opponent weights are games, not PA; rich modern context had only two mature test folds | Negative result concerns that representation/support, not portable park-neutral talent. Certify exact exposure and destination target before a retest. |
| Compact adjusted contact residuals | Compression/regularization differs from detailed cells; small value changes and participation effects mixed | Keep detailed-contact evidence that already helped. Do not conclude all contact outcomes fail; no full bin tournament again. |
| Repeat-level hitting test | Future surviving hitters require 30 PA; label itself uses estimated mover translations | Supports little incremental prediction of that conditional translated target, not correct lifetime value of stalled prospects. Reopen only with independent mover/translation diagnostics or a new survival question. |
| Same-player/same-season level translations | Controls identity but not promotion selection, hot streak timing, park/league shifts or aging within season | Useful baseline; not causal league difficulty. Separate up/down movers and out-of-season transport before stronger claims. |
| Durability pilot | Same-level, consecutive >=100-PA restriction removes severe absence and many promotions; productive group 37 players/six arrivals | Inconclusive source-constrained pilot, not evidence against durability. Need dated assignment/availability first. |
| Salary/guarantees | Historical as-of inputs absent; current costs sometimes are model estimates | Not tested. No negative predictive claim. |
| Three-part pitcher value | Workload/rate parameterization and weighting, not just independence; target excludes most contact run prevention | Valid narrow design loss; no rejection of decomposed pitching generally or of soft-contact talent. |
| Long-horizon richer hitters | Sparse mature rich support; switch in target models; survivor and regression effects | Do not impose a smooth age curve; first inspect calibration and feature support on fixed cohorts. |
| Career/donor paths | Mean and prospect-success shortfalls despite better distribution score | Remains rejected. Source/mean bottlenecks precede more simulation complexity. |
| Learned ensemble weights, hard current-MLB expert | Matched chronology and controlled inputs gave no clear gain or harm; no specific new fatal defect found here | Leave closed pending genuinely new evidence. "Baseball plausibility" is not a reason to retune. |

Portable talent, realized MLB output, and team-controlled economic value remain
different targets. The batting label uses realized event outcomes, fixed event
weights and a constructed replacement budget; it is not independently park-neutral
ability or published full WAR. Park-neutralizing an input while scoring an
unadjusted future environment can penalize the very portability we want. That
possibility needs a movers/non-movers and destination-context comparison, not a
declaration that neutralization must improve every score.

## 7. What still looks defensible

The broad hitter ensemble improves strong same-target references; gains are not
just credit for easy minor-league zeros. Detailed contact provides small additional
signal, chiefly among current MLB players. Dated roster status has a clear baseball
connection to opportunity and useful controlled evidence. Position and running
show measurable component signal. Source repairs to historical debuts/rosters
improve probability scores across origins. None should be discarded just because
new integration or defensive measurements need repair.

But some earlier wording is stronger than the evidence: bootstrap frequencies
are not "100% chance a model is better"; same-player resampling does not handle
shared league shocks; testing many models on exposed historical folds still
creates selection bias. Higher detail can legitimately lose through variance,
redundancy or a mismatched target. Plausibility means checking mechanism and
measurement, not requiring every intuitive baseball idea to win.

No new leakage was demonstrated in the current F/D fit cutoffs. Earlier pooled
position/conversion leakage and qualified-only defensive labels were already
documented and partly superseded. Their old results cannot be silently promoted
into evidence for newer versions. Panel-level future-mutation tests are useful,
but do not by themselves certify the upstream source builders or reconstruction
vintage.

## Decision and repair order

See the [repair program](methodology-repair-program-2026-09-25.md). First fix or
certify what is measured; then run one common-weight workload comparison; then
return to the already specified batting-connection diagnostic and component
integration with explicit residual-interaction accounting. Keep 2021 and all
non-arrivers. Revisit failed ideas only when the test changes in a way that
answers the identified flaw. No frozen forecasts change on the strength of this
review alone.
