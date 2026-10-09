# First base defense improves slightly with a historical prior

The fixed historical first-base prior improves the main measured-talent test
about 2.35% versus shrinking history toward zero. Retain it as a qualified
research baseline, not a promoted forecast. It barely changes total player-value
error, does not consistently improve older origins, and still misses individual
talent badly. Neither the frozen forecast nor the explorer changes.

## What changed and what stayed fixed

Only the first-base range prior changed. Each player's same three annual MLB
observations retain weights 1, 0.5 and 0.25 and the same 3000-out shrinkage.
The prior is the exposure-weighted native first-base mean from those calendar
years, excluding every player in the focal player's held fold. This is an
origin-known empirical reference, not a learner trained on future quality.
Position penalties, receiving throws, catcher value, hitting, playing time,
other defensive components and observed targets stay fixed.

The main test uses 2022 information to predict pooled 2023–2025 **MLB first-base
range per 1500 defensive outs**, or 500 innings. It retains all 233 first-base
origin histories; only 47 have sufficiently measured later quality. The other
186 have unknown quality, not zero ability. The complete eight-origin ledger
retains 1741 histories. Those are selected MLB-history players, not a validation
of DSL defense or all prospects. Future quality requires 1500 outs, two measured
seasons, complete follow-up and no missing positive official first-base exposure.

All 12432 annual contribution forecasts remain in the separate 2022–2024-origin
ledger. Missing channel outcomes and 318 incomplete total-defense rows stay
unknown. The outfield-corrected baseline was rebuilt in memory from unchanged
inputs because its archive drive is offline. Its serialized bytes reproduce
the original saved checksum exactly. No approximate substitute was used.

## Talent results

| 2022 origin and 47 measured people | RMSE in runs per 500 innings | Mean absolute error | Signed bias |
| --- | ---: | ---: | ---: |
| Raw zero skill anchor | 1.96011 | 1.62506 | +0.68351 |
| Original shrunk history | 1.90843 | 1.51427 | +0.78101 |
| Saved age calibration | 1.89245 | 1.55310 | +0.33310 |
| Historical prior candidate | 1.86361 | 1.47833 | +0.69354 |

The paired person-bootstrap difference versus history is −0.04482 runs, nominal
95% interval −0.07769 to −0.01186. The difference versus the saved age model
is −0.02884, interval −0.16901 to +0.10170; a reliable win over that alternative
is not established. These are exposed development results. The intervals do
not include reference-estimation uncertainty, shared year shocks or past model
selection, and do not establish performance across independent future eras.

All three origin-age groups improve versus the original history: young
2.36722→2.30012 (11 people), prime 1.74405→1.69592 (25), older
1.74500→1.73553 (11). Young-player bias is still +1.72463: the correction
does not solve development or skill measurement. Tiny-history error improves
2.08383→2.01661 across 27 people but remains worse than zero's 1.97862.
Medium exposure improves 1.86701→1.85037 (seven); large exposure is almost
unchanged, 1.50730→1.50550 (13). These small groups are qualifications, not
independent confirmations or grounds for choosing different weights.

| Origin | Measured people | History RMSE | Candidate RMSE |
| --- | ---: | ---: | ---: |
| 2016 | 42 | 2.06462 | 2.06462 |
| 2017 | 44 | 1.95396 | 1.95853 |
| 2018 | 38 | 1.74103 | 1.71435 |
| 2019 | 35 | 1.28814 | 1.29104 |
| 2021 stress | 48 | 1.86895 | 1.87995 |
| 2022 main | 47 | 1.90843 | 1.86361 |

2016 has only one measured reference year and correctly falls back to zero.
Other origins have supported contemporaneous reference pools. The 2021 stress
result is slightly worse, as are 2017 and 2019. Actual shortened 2020 exposure
is retained in eligible histories; no full season is invented. Origin membership
is inherited unchanged from the native ledger, not selected from these scores.

## Separate delivered value results

Measured first-base delivered-run RMSE, averaged equally across the three origins,
changes 0.36960→0.36775. The paired interval for the −0.00185 difference is
−0.00562 to +0.00163. Among actual measured first-base defenders, it changes
1.89079→1.88037. That improvement is not merely from thousands of non-arrivals,
but 2024's target season gets worse and the total effect remains small.

Complete defined-defense error changes 1.49530→1.49480 runs; custom expanded
value changes 0.429686→0.429614 common wins, about **0.017%**. The latter paired
interval is −0.000216 to +0.000066 wins. This is effectively unchanged whole-model
accuracy, not a meaningful new WAR gain. Expanded value here is the unchanged
research batting/replacement plus position and defined defense target; it omits
running and is not FanGraphs WAR, six years of control or trade value.

| Target season and matched measured first-base rows | Original forecast runs | Candidate forecast runs | Actual runs |
| --- | ---: | ---: | ---: |
| 2023 | −4.30 | −10.01 | −59.82 |
| 2024 | −14.75 | −35.79 | −31.76 |
| 2025 | −9.49 | −29.17 | −43.47 |

The much closer 2024 total does **not** rescue its worse individual error.
At actual first-base opportunities, diagnostic error improves 1.82991→1.81269
in 2023, worsens 1.93318→1.93855 in 2024, and improves 1.91446→1.87017 in
2025. A better rate prior helps somewhat; errors are not just playing time.

Complete expanded-value forecasts still total 498.28/523.37/484.07 against
491.61/458.13/477.80 actual. Position allocation and other-channel optimism
remain. Current-MLB and upper-minors expanded error improve trivially; inactive
error worsens trivially. No forecast rows or target memberships were dropped.

## What the player review tells us

The [full source and calculation walkthrough](defense-first-base-prior-v28-player-review.md)
covers eleven selection groups, 44 focal/peer records and 38 distinct player
origins. Fixed cases were retained; outcomes selected gains, harms, false highs,
false lows and an ordinary control only for diagnosis. Peers use origin-known
role, stage, age and exposure, never their later success.

Toglia's 352-out positive MLB sample initially projects +0.465 runs per 500
innings; the new prior lowers it to +0.178, closer to later −2.402. That is the
largest talent improvement, but still a poor forecast. O'Hearn is the largest
harm: +0.297 falls to +0.024 while later quality is +2.226. Santana's useful
positive history is weakened, and Guerrero's known negative history is still
far too mild. Freeman is a modest quality improvement; Olson and Goldschmidt
are quality deteriorations. Annual contribution can move in the opposite
direction to pooled skill, which is why the two are tested separately.

Wilson and his minor peers receive explicit unknown-skill priors, not measured
talent. Their tiny projected first-base exposure means tiny value changes; it
does not make the skill evidence reliable. Several peers have no MLB first-base
history at all. The fixed primary-role peer rule is useful for opportunity
context, but does not create first-base talent comparisons where none exist.

## Decision and stopping point

Keep this one prior as the qualified first-base research baseline, alongside
zero, original history and saved calibration anchors. Its main talent result
supports correcting the sparse-history mean without serious main age/exposure
harm versus history. Mixed earlier origins, remaining young/small-sample bias
and negligible delivered-value improvement rule out stronger claims. Do not
tune a second prior, impose a framing penalty or promote from league totals.

The first-base checkpoint is complete. Independent arithmetic reproduces all
1741 quality histories, 12432 value forecasts, 40 references, 1663 raw native
source rows, scores, intervals, selections and all 44 player records. Six unit
checks pass. Forecast and explorer checksums are unchanged; 2026 was not opened
or rescored. Repository documentation now points to the
[consolidated hitter stopping point](hitter-stopping-point-2026-10-08.md).
