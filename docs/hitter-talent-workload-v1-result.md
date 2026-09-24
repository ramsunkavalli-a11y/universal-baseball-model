# Explicit talent and pedigree: small, uncertain workload gains

2026-09-23. Completed under the [fixed plan](hitter-talent-workload-v1-plan.md).
Decision: retain the prior detailed D workload candidate. Do not promote TP,
select an ablation after failure, or change the explorer/frozen 2026 forecast.

## What this means in baseball terms

Better prospects should generally receive more opportunities. This experiment
does not refute that proposition. It asks whether giving the existing detailed
playing-time model explicit batting-talent forecasts and draft pedigree helps
it distinguish those players more accurately.

The changes barely improve pooled three-year error, with uncertainty spanning
improvement and harm. They do not resolve the missed regulars or the 2021 cohort
shortfall. The talent estimates are themselves imperfect batting-rate forecasts,
not scouting assessments of all-around ceiling, defensive fit or team commitment.
Public historical FV grades were not available in a certified dated panel.

## What changed in the experiment

- T adds independently generated, historical-cutoff batting-rate predictions
  for Years 1 and 3, plus support flags. These are predicted batting-plus-
  replacement wins per 600 PA conditional on playing, not full WAR or projected
  value divided by expected PA. They summarize existing detailed information
  using a separate performance target; they do not introduce new observations.
- P adds five draft-history fields: matched Rule 4 evidence, within-draft pick
  quality, school-class information and years since the latest eligible draft.
- TP adds both, and was the sole predeclared candidate. T/P are ablations.

The earlier model D already uses age, level, production, contact/pitch details,
progression and 40-man status. We held its repaired participation probabilities
fixed and changed only PA conditional on playing for never-debuted minor leaguers.
Every starting prospect remains in the evaluation, including zero-PA outcomes.

Twenty supported talent heads were fitted within 26 historical year/horizon
slots; six insufficient-history slots remain explicitly missing. Each historical
talent input is predicted using only labels mature at its own snapshot, not a
model trained at the later outer cutoff. Thirty-six workload fits compare T/P/TP
across the same twelve annual folds as the previous experiment.

## Results

All-starting-prospect PA RMSE; lower is better. Years refer to separate future
seasons, while the bottom row evaluates each player's summed three-year PA.

| Forecast | Current research D | Add talent T | Add pedigree P | Add both TP | Older ensemble E |
|---|---:|---:|---:|---:|---:|
| Year 1 | 28.603 | 28.536 | 28.624 | 28.633 | 29.631 |
| Year 2 | 50.814 | 50.617 | 50.810 | 50.647 | 51.917 |
| Year 3 | 66.281 | 66.231 | 66.044 | 66.284 | 67.075 |
| Three-year total | 121.668 | 121.434 | 121.207 | 121.534 | 126.184 |

TP's cumulative MSE difference versus D is -32.47 PA squared, with paired
97.5% player-bootstrap interval [-244.04, +162.31]. Only one of three origins
improves versus D; Years 1 and 3 are slightly worse. TP beats the older ensemble,
but D already did, so that is not sufficient incremental evidence.

T's cumulative interval versus D is [-194.03, +80.38]; P's is
[-327.87, +94.82]. Neither ablation supplies a clear incremental win either.
The slight point gains are not grounds to select another arm after TP fails.

TP improves cumulative MAE from 33.12 to 32.46 PA and passes all 23 supported
subgroup/origin harm guards. However, mean absolute cohort-total error worsens
from 23,862 to 25,417 PA. The cumulative 2021-origin prediction falls from
72,078 to 65,952 PA, versus 121,444 actual. The 2022 total moves from 98,994
to 96,739 versus 97,303 actual. Calibration changes are mixed, not repaired.

The false-optimism guard passes: among prospects with no MLB PA anywhere in
the three-year window, mean predicted PA falls from 10.68 to 9.97. Thus the
failure is not a broad increase in forecasts for non-arrivers; the model still
misses substantial workloads among successful players.

## What the diagnostics tell us

Using the new cutoff-time talent estimates to sort prospects into quintiles,
the old D model already forecasts more next-year PA for the highest quintile
(9.36 per starting prospect) than the lowest (1.43). The highest quintile
actually averages 12.51. TP raises its forecast only to 9.72 and slightly worsens
its RMSE. These are population averages including thousands of non-arrivers,
not projected workloads for a regular. This association is consistent with D
already capturing part of the quality signal; it is not causal attribution or
proof that prospect quality is fully represented.

Among prospects who actually became next-year regulars (450+ PA), T increases
mean conditional PA from 200 to 211; TP stays near 200. This survivor-defined
slice is descriptive only. Expectations need not equal successful realizations,
but the aggregate shortfall remains evidence of underprediction.

| 2021-origin example | D expected PA | TP expected PA | Actual 2022 PA |
|---|---:|---:|---:|
| Jeremy Pena | 91.8 | 93.4 | 558 |
| Ezequiel Duran | 28.6 | 25.7 | 220 |

Pena's conditional PA changes only from 142 to 144 in TP. His draft-only
ablation reaches 170, but that is not a reason to choose P after seeing his name.
Duran has no matched Rule 4 draft record; he receives no invented poor draft rank.

The largest misses still include Alonso, Reynolds, Kwan, Bellinger, Soto and
Pena at their pre-debut cutoffs. Some are limited heavily by participation
probability as well as workload: Soto's expected next-year PA moves from 1.94
to 2.10 despite a conditional estimate rising from 211 to 229. Fixed annual
participation makes this a deliberate workload isolation test, not a test of
whether talent/pedigree can improve arrival or speed of promotion.

## Source coverage and limitations

The official draft capture was recovered read-only from the September 7
checkout. The narrow archived extract uses only <=2022 pick/year/school records;
one exact duplicate 2008 pick was removed, with no conflicting records accepted.
It contains no bonuses, slot values, current scouting descriptions or current FV.
Draft records after each player's snapshot cannot enter the features.

Draft matches cover 1,533/3,395 prospects at the 2016 origin, 1,335/3,250 in
2021 and 1,175/3,188 in 2022. Unmatched means missing Rule 4 evidence, not a
certified international-signing category. International signing investment is
not measured. The 2006 start also limits older-entry coverage. Draft facts were
reconstructed from a later capture rather than certified original publication
archives; the test restricts itself to selection-time facts.

TP's cumulative RMSE improves among draft-matched prospects (164.45 to 163.61)
but worsens among unmatched prospects (81.02 to 81.92). These groups have very
different baseline opportunity; this does not establish a causal draft effect.

The talent target is observed MLB batting rate among participants, weighted by
PA and player identity. It is not an unbiased latent-talent label for players
who never play, a prospect-ceiling distribution, or a full defensive/positional
talent measure. The new encoding may be redundant, noisy or incomplete; this
experiment does not identify which explanation dominates.

## Verification and disposition

Twenty supported nested talent fits, 36 workload fits, an exact prior-D replay,
two inner and two outer future-label mutation replays pass. Outer checks also
prove 24/26 eligible nested training sets unchanged at their respective cutoffs.
The verifier checks past-only draft joins, source/code hashes, label maturity,
reference predictions, weights, probability products and reproduced scores.
All 28 focused tests pass; the prior workload archive and original 2026 freeze
verify. No protected 2026 outcomes, non-prospect forecasts, live forecasts or
value components changed. Evidence is archived in
`model_artifacts/hitter-talent-workload-v1-2026-09-23/`.

This is historical development evidence on already exposed folds, not fresh
confirmation. Repeated-player bootstrap does not capture all shared season
shocks. No Years 4–6, full WAR or trade-value improvement is established.

Keep D as the research workload head. Do not impose a manual high-prospect PA
bonus or retune these arms to the missed names. A separate next test may address
the participation/promotion-timing bottleneck, or add certified dated scouting
and broader talent evidence. It must start from the retained D/F control and
keep the unsuccessful prospects and cohort-total checks. The safe connection
to component value remains a separate outstanding milestone.
