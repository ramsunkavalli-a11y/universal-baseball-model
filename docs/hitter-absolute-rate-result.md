# Freely learned hitting does not improve the full forecast

2026-10-05. The single contracted comparison and twenty actual
[player walkthroughs](hitter-absolute-rate-player-review.md) are complete.
Keep the incumbent. Removing the imposed past-production baseline helps some
established hitters and overseas overestimates, but gives back useful information
for other players. Do not combine the favorable subgroups or launch another
offset/prior search to chase the near-tie.

## What changed and what stayed fixed

The prior seven-input model predicts a fixed past-production baseline plus a
learned correction. The new model learns batting rate directly from exactly
the same matrix. Past production is still an input. The output target and
regularization center change; the data, 123/132/186 feature routes, Ridge alpha
100, fixed units, active training people, weights, five whole-player groups,
35 chronological cells, all forecast identities and expected PA do not.

All 30,506 originals and thirteen separately scored additions remain. Origins
2016–2018 and 2021–2024 predict next-calendar-year MLB performance through 2025.
Canceled 2020 target remains absent; actual short-season inputs stay. Hitting
means batting wins above league mean per 600 PA, observed only for active MLB
players. Delivered value adds replacement at expected PA, not defense, full WAR,
six years of control or trade value. No 2026 outcome was accessed or reused.

## Overall result

| Model | Hitting RMSE | Delivered RMSE | Delivered MAE | Expected value |
| --- | ---: | ---: | ---: | ---: |
| Incumbent | 1.804813 | 0.435133 | 0.123874 | 4,155.430 |
| Same inputs with imposed baseline | 1.799172 | 0.435373 | 0.123507 | 4,174.414 |
| Freely learned absolute hitting | 1.806607 | 0.435859 | 0.124136 | 4,130.825 |

Actual delivered value is 4,185.434. Expected PA is unchanged at 1,228,732.5
versus 1,270,493 actual. Removing the baseline worsens both primary measures
against both required comparisons, but the differences are small. Nominal
2,000-draw player-clustered development intervals include zero:

| Absolute model minus anchor | Hitting MSE change and interval | Delivered MSE change and interval |
| --- | ---: | ---: |
| Incumbent | +0.006478 [−0.010613, +0.024744] | +0.000632 [−0.000164, +0.001421] |
| Matched residual model | +0.026810 [−0.002832, +0.057711] | +0.000423 [−0.001117, +0.001945] |

This repeatedly exposed history is not independent confirmation. The result
does not establish that imposing a baseline is universally best, or that
all foreign/minor information should be discarded. It does not justify replacing
the incumbent or selecting a model separately for each subgroup.

## Which groups changed

These are conventional within-cohort equal-origin scores, not additive global
attributions. Cohorts overlap; do not add their losses together.

| Cohort | Forecasts and active labels | Incumbent hitting and delivered RMSE | Matched residual | Absolute model |
| --- | ---: | ---: | ---: | ---: |
| Current MLB | 4,541 / 3,596 | 1.705463 / 1.067759 | 1.703455 / 1.069490 | 1.706132 / 1.069843 |
| At least 600 weighted recent MLB PA | 1,995 / 1,821 | 1.537229 / 1.332732 | 1.539145 / 1.338484 | 1.534646 / 1.334499 |
| Upper minors never debuted | 5,454 / 730 | 2.563248 / 0.301695 | 2.543232 / 0.299501 | 2.573931 / 0.302263 |
| Lower minors never debuted | 17,852 / 54 | 3.179084 / 0.045813 | 3.092598 / 0.045603 | 3.265105 / 0.045853 |
| Foreign history | 253 / 28 | 1.880241 / 0.493093 | 1.800729 / 0.496624 | 1.705384 / 0.484743 |
| No target MLB PA | 25,968 / 0 | Unobserved / 0.069388 | Unobserved / 0.071795 | Unobserved / 0.069191 |
| Thirteen additions | 13 / 6 | No incumbent | 3.364943 / 1.434346 | 2.896429 / 1.544546 |

The intended mature-MLB hitting improvement appears, but delivered still loses
incumbent. Upper/lower-minor gains from the residual model are lost. The declared
review warnings are lower-minor hitting +5.58% versus matched, additions delivered
+7.68%, and hitting +16.70%/+25.30% in the mature/no-MLB foreign cells. The last
two have only four/five active labels; their uncertainty cannot be hidden by
the broad foreign aggregate improvement. The 54 lower-minor active labels cannot
certify lifetime prospect ability or DSL success identification.

Against matched, hitting improves in only two of seven origins (2021 and 2022),
delivered in four (2017, 2021, 2022 and 2023). Against incumbent, both improve
together only at 2023. Keep 2016/2018/2024 failures as well as 2021's gain; a
COVID-only story cannot explain the whole result. Every origin and all six
source-history cells are retained in the public evidence.

## Public projections remain a qualified check

The unchanged 2,627 matched public rows have 2,088 active labels. On the saved
future-relative target, the absolute model's hitting RMSE is 1.661279 versus
incumbent 1.664751 and matched 1.665695; delivered is 1.022806 versus 1.023981
and 1.023942. That favorable subset does not override the full-population result.

On the origin-centered public reference, absolute hitting RMSE is 1.721425,
incumbent 1.728481, matched residual 1.712542, Steamer 1.774589 and ZiPS
1.753361. Reference conventions change the internal ranking. Existing vintage,
park/environment and ZiPS workload qualifications remain; these values are not
proof of overall superiority to the named systems or a certified WAR comparison.

## What the player review shows

Thames's rate falls from +3.083 to +0.768 versus actual +0.622, and established
Judge rises from +3.749 to +3.950. Those are sensible local gains. But Suzuki's
post-debut rate falls from +2.553 to +0.519 versus +1.997 actual; the pre-debut
addition falls from +3.314 to −0.489 versus +1.175 actual. The freely learned
model handles foreign dominance less aggressively, not uniformly more accurately.

Cowser is the new mechanical largest gain; he remains far too high, +1.059 versus
−1.344 actual. Acuña is the new largest false high: both hitting and projected PA
remain high relative to reality. Refsnyder's almost exact delivered value still
cancels −0.0453 hitting and +0.0466 opportunity errors. Misner's delivered gain
versus matched accompanies a worse, overly pessimistic hitting rate. France and
Nola move toward actual hitting but lose favorable PA compensation. Thus even
the favorable cases need the error decomposition, not just a value leaderboard.

## Verification and disposition

All 105 heads replay, twelve independent headline equations pass, source/target
checks preserve every identity, and all previous forecast columns and PA are
exactly unchanged. There are no theoretical physical-rate-envelope violations.
The same absent/sparse joint-support warnings remain. The review join was corrected
before scores were written because the newer diagnostic table contained only
originals; the full source-profile table now retains all thirteen additions.
No fit or forecast changed because of that repair. A nonfatal collection warning
in the sealed fit runner does not change the independently checked row membership.

The model does not meet the declared replacement requirement. Keep incumbent;
retain the matched separate-component evidence as research. Do not tune an offset
weight, split models by favorable exposure groups, retest closed team opportunity
ideas or reopen 2026. No forecast/explorer deployment follows from this comparison.

Next close this representation sequence in a single candidate-readiness record:
reconcile the strongest justified hitting and opportunity forecasts with the
existing selected candidate, benchmark limitations and player misses. Review the
already tested opportunity evidence before deciding that another fit is necessary,
especially prospect workload and mature-player absence. This is not a fresh menu
of context features or a repeat of known closed tests. The long goal remains active;
this completed negative comparison is not completion of the hitter model.
