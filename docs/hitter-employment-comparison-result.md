# Employment flag correction does not improve overall forecasts

2026-10-05. The limited flag-only comparison is reviewed. Keep the valid source
parser correction, but do not promote the refitted opportunity model. The player
review found two additional date-derived inputs that still use the old employment
path; this result does not test the complete source correction.

## Exact matched result

All 30,506 original forecasts and thirteen additions remain. Seventy saved
baseline heads replay, 140 full/active prefit checks pass, and seventy corrected
heads fit and replay. No hitting model, availability rule, original comparison,
frozen forecast or completed 2026 evaluation changes. Each target is next year's
actual MLB PA and batting-plus-replacement contribution, not full WAR or value
over club control. Historical development results are extensively exposed.

| Original cohort metric | Saved old job inputs | Corrected flags and signed work | Full incumbent |
|---|---:|---:|---:|
| PA RMSE | 60.253 | 60.314 | 60.499 |
| PA MAE | 20.492 | 20.503 | 20.612 |
| Brier | .032433 | .032417 | .033540 |
| Log loss | .111226 | .111095 | .114736 |
| Batting contribution RMSE | .435319 | .435618 | .435133 |

Primary squared-error change against the old job arm is +7.354 PA², with nominal
paired 95% interval −3.155 to +18.004. Batting squared-error change is +.000261,
interval −.000026 to +.000558. Thus no demonstrated primary improvement. The
corrected model's better probability scores versus the full incumbent mainly
reflect the already developed common job branch, not proof of a parser benefit.

Directly affected original rows improve PA RMSE 31.286 to 31.025, with MAE
change −.213 PA (interval −.296 to −.136). Their squared-error interval still
includes zero. Other rows worsen 63.760 to 63.853 through retraining, even though
their personal inputs are unchanged. Six of seven origin PA RMSEs worsen. No
populated stage exceeds the predeclared 2% deterioration check, but passing that
check is not an improvement. Both scoring and totals must be inspected.

## Totals and public comparison

Original expected PA rise 1,235,119 to 1,235,831 against 1,270,493 actual across
seven seasons. Batting contribution rises 4,179.76 to 4,182.87 versus 4,185.43.
Those close pooled value totals hide opposing errors: never-debut upper minors
project 73,333 PA versus 92,891 actual, while lower minors project 8,143 versus
5,194. Their batting totals are 175.38 versus 196.73 and 18.46 versus 9.48.
The 2021 origin overpredicts value 614.02 versus 568.34 despite underpredicting
PA; the correction does not solve that mismatch.

Thirteen additions project only 735 PA and 2.59 participants versus 1,625 and
six actual. Their research fallback talent is fixed and there is no incumbent
forecast, not a zero benchmark. Foreign originals and additions together project
9,253 PA versus 9,401, but only 23.61 batting contribution versus 41.74. Good
aggregate foreign PA cannot conceal missing individual roles or weak talent.

On the unchanged 2,627 public matches, corrected PA RMSE is 138.02 versus
Steamer 135.38; MAE 105.47 versus 92.08. This narrowly meets the existing working
tolerances, but is still materially worse in average workload error. Batting
contribution RMSE 1.026 versus 1.090 uses the existing qualified raw-public
conversion; snapshot, park and rate-reference limitations prevent a claim of
overall public-system superiority. Ordinary ZiPS PA is not treated as
unconditional workload, and missing foreign public rows are not zero.

## Player findings and training limits

The [player review](hitter-employment-comparison-player-review.md) preserves 113
machine traces and reviews the consequential source/head paths. Bourgeois's
false signed-work removal meaningfully lowers a nonarrival forecast. Machado's
valid source correction worsens PA error, while lowering positive batting value
looks better against a small negative realized value. Slater's nearly exact
batting contribution still overpredicts workload by 93 PA. Judge's largest gain
and harm occur with unchanged personal inputs. Suzuki, Yoshida, Lee, Ohtani,
Kurtz, Yordan, Tatis and Franco remain serious readiness/role/availability misses.

Corrected exact conditional profiles have zero people for 4,880 forecasts and
under twenty for 19,205. All remain in scoring. A large broader training set is
not a substitute for support at the relevant rare profile; these warnings are
not deletion rules or proof that the prediction must fail.

## Decision

Retain the parser correction as source work; no model or explorer promotion.
The player walk exposes an incomplete dependency repair: evidence age and
missing-date inputs still come from old assignment-contaminated employment paths.
Rebuild those two inputs and complete the same bounded contrast, without tuning,
changing talent, using handpicked roles, or reopening 2026. Do not describe this
limited result as rejecting contract/role information or the complete correction.
The broad hitter goal remains active with genuine benchmark and cohort gaps.
