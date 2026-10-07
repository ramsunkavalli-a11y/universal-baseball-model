# Throwing and blocking talent now have separate opportunity based baselines

2026-10-06. The defense research layer now distinguishes catcher throwing from
blocking using the opportunities each skill actually faces. Shrunk native MLB
history reduces later-quality error by about 7% for throwing and 9% for blocking
against assigning everyone average skill. Both improvements remain uncertain.
The useful baseline is retained for assembly, with its misses and coverage limits;
it is not an approved change to the hitter forecast or a full catcher WAR claim.

## What changed in the evidence

The source contains 1,018 throwing records from 2016–2025 and 870 blocking records
from 2018–2025. Every recorded run numerator matches the separately captured
native fielding ledger. Throwing uses actual tracked attempts and already adjusts
for the presented steal opportunity. Blocking uses difficulty-adjusted blocking
chances, not framing pitches or batting PA.

Blocking CSV display values are rounded. Its exact numerator is expected failures
minus observed failures, converted at 0.25 runs per block. For example, Rutschman's
2022 export displays 18 extra blocks and four runs, but its exact measurement is
17.795 extra blocks and 4.449 runs over 3,288 chances. Using the rounded run column
would silently alter rates, particularly for small samples.

Eight throwing records from 2016–2017 have an unresolved mismatch between their
reported attempts/expected rate and adjusted caught-stealing numerator, despite
reconciling with native contribution. They remain measured contributions but
unknown opportunity-based talent. Salvador Perez's 2016 adjusted numerator is
+10.760 additional caught stealings; the displayed count/expected-rate identity
instead gives +10.498. Do not substitute one for the other or invent an explanation.
Five tiny blocking records also lack opportunity measurements, including Wallach's
six defensive outs in 2025. Any future quality window containing a positive native
catcher exposure with missing/invalid channel measurement remains unknown.

The earlier minor-league narrative blocking/deterrence failures do not establish
that these skills are useless: their extractor omitted most official WP/PB and
many attempts. This comparison does not repair that extractor or establish
minor-to-MLB transfer. The captured tracking measurements are MLB-only here.

## What the quality comparison establishes

Each eligible origin uses three years of known history, with weights 1, 0.5 and
0.25. Throwing adds 100 average-skill attempts to the weighted denominator;
blocking adds 3,000 average-skill chances. These are fixed conservative initial
assumptions, not optimized reliability constants. Small samples shrink directly
inside the formula; a separate reliability label cannot bypass the shrinkage.

Future quality pools the next three calendar years and requires two measured
seasons, at least 100 throwing attempts or 3,000 blocking chances, complete
follow-up and no missing positive native exposure. Non-arrivals, exits and short
samples are unknown quality, not average or bad defenders. Every eligible origin
remains in the coverage ledger. Short 2020 MLB exposure enters at actual counts.

| Main 2022 origin | Throwing runs per 100 attempts | Blocking runs per 1000 chances |
| --- | ---: | ---: |
| Eligible players | 150 | 162 |
| Players with measured 2023–2025 quality | 35 | 57 |
| Average-skill RMSE | 3.901 | 0.395 |
| Shrunk-history RMSE | 3.623 | 0.360 |
| RMSE reduction | 7.1% | 8.9% |
| Paired difference and 95% person interval | −0.277, −0.689 to +0.175 | −0.035, −0.097 to +0.022 |
| Average-skill MAE to history MAE | 3.105 to 2.947 | 0.321 to 0.298 |

The intervals include no gain. Throwing improves in five of six scored origins
but loses slightly in 2019, whose measured cohort contains only nine people.
Blocking improves in three of four origins but loses in the separate 2021 stress
comparison, 0.423 to 0.440. Do not drop that failure. These exposed historical
results are development evidence, not a fresh independent holdout.

Actual future exposures give diagnostic predicted-versus-observed run totals of
+11.03 versus −8.11 for throwing and +22.78 versus +14.03 for blocking. Those are
not forecasts of future opportunity or full-league totals. Throwing mean bias
worsens from +0.258 to +0.420; blocking bias improves from −0.019 to +0.005.
Older blocking and tiny blocking sample groups worsen on point estimates.

Mature held-player training would contain only 21–27 throwing and 44–53 blocking
people at the main origin. All 35 throwing cases and 53/57 blocking cases have
fewer than 20 matching age/exposure training people. No learned age curve was
fitted to these sparse careers; the fixed recipe still does not establish strong
transport evidence for those profiles. Older early histories are left-truncated.

## The named players explain the gains and failures

Twenty-three focal channel cases and 69 origin-selected peers are fully traced;
35 peers lack measured future quality. The rates below are forecasts at the end
of 2022 followed by pooled 2023–2025 reality, using the channel units above.

| Player and component | Shrunk history | Later quality | Baseball finding |
| --- | ---: | ---: | --- |
| Realmuto throwing | +5.880 | +4.203 | Largest gain over neutral; 67 weighted attempts and +9.820 adjusted runs contain genuine positive throwing evidence. |
| Maldonado throwing | +3.279 | −2.453 | Largest deterioration; 71.75 weighted attempts and +5.632 runs preserve an old positive grade that later reverses. |
| Moreno throwing | +1.530 | +9.061 | Largest false low; 16 prior attempts shrink heavily and cannot anticipate the full later development. |
| Barnes throwing | −2.005 | −7.866 | History identifies weakness but misses its magnitude. |
| Raleigh throwing | −0.732 | +2.613 | Historical direction reverses; a shrinking formula alone does not forecast development. |
| Kirk throwing | +0.021 | +2.626 | Near-neutral input misses later improvement. |
| Hedges blocking | +0.483 | +0.503 | 5,022.75 weighted chances and +3.878 runs accurately preserve positive skill. |
| Sánchez blocking | −0.336 | −0.545 | 5,456 weighted chances and −2.845 runs identify weakness; not every good catcher shares every skill. |
| Jansen blocking | +0.555 | +0.860 | Largest improvement; positive evidence carries forward. |
| Grandal blocking | −0.412 | +0.159 | Largest deterioration; historical weakness does not persist. |
| Campusano blocking | +0.203 | −0.668 | Largest false high; 578 weighted chances shrink but still point the wrong way. |
| Fortes blocking | −0.093 | +0.598 | Largest false low; misses later improvement. |
| Raleigh blocking | −0.066 | −0.225 | Below-average blocking coexists with improving throwing; do not transfer one component's grade into another. |
| Kirk blocking | +0.387 | +0.871 | Correct positive direction, but understates later skill. |

Realmuto's blocking estimate is +0.464 versus +0.105 later; his strongest throwing
gain does not justify treating him as elite in every channel. The ordinary cases
also have misses: Fortes throwing is +1.338 versus −0.920; Trevino blocking is
+0.539 versus +0.266. Hedges and Sánchez have no qualifying future throwing label
at this origin, so their throwing forecasts are not scored as neutral reality.

The smallest cases show appropriate direct regression: Wieters and Phegley each
have 0.25 weighted throwing attempts and rates near zero; Gushue's 0.5 weighted
blocking chances and Sands's two supply negligible estimates. Their future
quality is unknown. Bailey has no eligible 2022 MLB history and is absent from
that talent test, not retrospectively given his later measurements.

## Applied research components and the remaining value problem

The same reviewed recipe is now applied separately to valid 2023–2025 history:
140 throwing and 147 blocking players. The saved quality layer keeps numerator,
opportunities, reliability, scope and observed-evidence flags. Missing history
uses an uncertain neutral prior, not an assertion of measured neutral skill.
Sixteen current source cases and 48 peers are replayed independently.

For example, Bailey's current throwing quality is +4.664 runs/100 attempts while
his blocking is +0.041 runs/1,000 chances. Kirk is +1.253/+0.660; Raleigh is
+1.308/−0.154; Sánchez is −0.155/−0.410. These are different skill estimates in
different units, not additive player WAR values or fixed six-year awards.

Independent checks reconstruct all 1,888 source rows, 1,971 origin forecasts,
eligibility/label windows, actual training-fold profiles, scores/intervals,
focal/peer source arithmetic and all 287 current channel rows. Twenty-one tests
cover these source/baseline functions and the existing framing/source regression
checks. The frozen manifest and completed 2026 evaluation hashes are unchanged.

Retain the transparent throwing/blocking research baselines with uncertainty;
do not retune priors to rescue the named failures or claim eventual minor-league
talent validation. Next qualify outfield arms and first-base receiving, then
forecast position/exposure and test delivered defensive value on identical
expanded targets. The selected hitter forecast and explorer remain unchanged.

Evidence: [quality comparison](../reports/model-evidence/catcher-throw-block-v5/talent-report.json),
[player calculations](../reports/model-evidence/catcher-throw-block-v5/talent-player-walkthrough.json),
[independent replay](../reports/model-evidence/catcher-throw-block-v5/talent-final-review.json)
and [current baseline verification](../reports/model-evidence/catcher-throw-block-v5/baseline-verification.json).
