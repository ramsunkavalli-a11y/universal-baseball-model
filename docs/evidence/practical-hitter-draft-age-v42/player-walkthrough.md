# V42 complete player walkthrough

Identical population/folds, future MLB targets and learners; school flags replaced with three draft-age inputs. Exact tree-path/coefficient accounting is descriptive, not causal. Every case includes actual counts, actual inputs, saved intermediates, results and origin-only selected peers. No protected 2026 outcomes.

## Nick Kurtz — 2024 to 2025

Selection: Fixed diagnostic.

Age 21.0; stage Upper minors; listed position 3; draft 2024/pick 4/class 4YR JR; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 42.495 | -0.13556 | 0.12316 |
| draft_age | 44.333 | -0.13470 | 0.12855 |
| age_pa_only | 44.333 | -0.13556 | 0.12849 |
| age_rate_only | 42.495 | -0.13470 | 0.12322 |
| Actual | 489 | 5.150009420178844 | 5.72099 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00312416). Separate means, not a joint distribution; no full WAR.

control pa: reference 39.299703, raw prediction 42.494583.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| draft_rank | 0.817615 | 34.484966 |
| work_0 | 0.000000 | -23.699251 |
| age_centered | -1.200000 | 8.736002 |
| on_40man | 0.000000 | -6.575131 |
| pooled_AA_BB | 0.086957 | 2.004532 |
| AAA_0_pa | 0.000000 | -1.882722 |
| regular_window_scaled | 0.000000 | -1.843877 |
| pooled_MLB_BB | 0.080000 | -1.692418 |

control rate: reference -0.972293, raw prediction -0.135562.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -1.200000 | 0.642920 |
| reorganized | 1.000000 | -0.276479 |
| draft_rank | 0.817615 | 0.160851 |
| position_3 | 1.000000 | 0.133637 |
| draft_known | 1.000000 | -0.089751 |
| age_squared | 1.440000 | 0.088090 |
| draft_college | 1.000000 | 0.073031 |
| pooled_A_BB | 0.533333 | 0.063729 |
| draft_rank_low_exposure | 0.545076 | 0.020263 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_jc | 0.000000 | -0.000000 |
| draft_hs | 0.000000 | 0.000000 |
| draft_class_unknown | 0.000000 | -0.000000 |

candidate pa: reference 39.297520, raw prediction 44.332843.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| draft_rank | 0.817615 | 36.268468 |
| work_0 | 0.000000 | -23.699251 |
| age_centered | -1.200000 | 8.739198 |
| on_40man | 0.000000 | -6.512126 |
| pooled_AA_BB | 0.086957 | 1.989150 |
| AAA_0_pa | 0.000000 | -1.876375 |
| regular_window_scaled | 0.000000 | -1.843877 |
| pooled_MLB_BB | 0.080000 | -1.691511 |

candidate rate: reference -1.048671, raw prediction -0.134696.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -1.200000 | 0.696571 |
| reorganized | 1.000000 | -0.267585 |
| draft_rank | 0.817615 | 0.177653 |
| position_3 | 1.000000 | 0.143205 |
| age_squared | 1.440000 | 0.105535 |
| pooled_A_BB | 0.533333 | 0.067074 |
| absence_window_scaled | 1.000000 | -0.056795 |
| pooled_A_BABIP | 0.157895 | 0.031241 |
| draft_known | 1.000000 | -0.021758 |
| draft_age_known | 1.000000 | -0.021758 |
| draft_rank_low_exposure | 0.545076 | 0.020350 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | 0.000000 |

The actual 35 A/15 AA PA, four homers and pick four remain intact. The source control already knows his college class. Replacing that label changes PA only 42.5 to 44.3 and batting -0.136 to -0.135, versus 489 PA and +5.150 actual. Draft rank adds opportunity but no prior MLB work subtracts it; centered draft age 21 adds zero direct age term. Only five distinct future-active training players match the low-pro-exposure/older-draft/never-debut rate profile. This does not support a precise talent grade. Moore and Smith arrive, while the exposure-aware peer rule also retains Jenkins with zero next-year MLB PA. The wider early-top-pick cohort usually did not arrive immediately; this individual breakout cannot justify assigning every new college pick 600 PA.

Actual distinct-player profile support: [('pa', 1395), ('rate', 5)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Christian Moore | 21.0 | 110.0 | 46.4 → 46.4 → 184 | 0.1980 |
| Cam Smith | 21.0 | 134.0 | 18.9 → 18.5 → 493 | 1.0135 |
| Walker Jenkins | 19.0 | 483.0 | 44.8 → 45.7 → 0 | 0.0000 |

## Heston Kjerstad — 2023 to 2024

Selection: Fixed diagnostic.

Age 24.0; stage Current MLB; listed position 9; draft 2020/pick 2/class 4YR JR; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | A | 98 | 2 | 17 | 12 |
| 2022 | Aplus | 186 | 3 | 47 | 16 |
| 2023 | AA | 206 | 11 | 31 | 15 |
| 2023 | AAA | 337 | 10 | 69 | 26 |
| 2023 | MLB | 33 | 2 | 10 | 2 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 261.967 | 0.22232 | 0.90814 |
| draft_age | 261.967 | 0.08619 | 0.84870 |
| age_pa_only | 261.967 | 0.22232 | 0.90814 |
| age_rate_only | 261.967 | 0.08619 | 0.84870 |
| Actual | 114 | 0.6372881167291873 | 0.47709 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00309608). Separate means, not a joint distribution; no full WAR.

control pa: reference 40.158995, raw prediction 261.967012.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 93.638287 |
| draft_rank | 0.908807 | 78.498701 |
| pooled_AA_HR | 0.045752 | 34.556219 |
| pooled_AA_pa | 206.000000 | 15.697279 |
| age_centered | -0.600000 | 12.007027 |
| AA_0_pa | 206.000000 | 10.352667 |
| MLB_0_pa | 33.000000 | -7.742313 |
| pooled_mlb_quality | -0.011299 | -7.431207 |

control rate: reference -0.785423, raw prediction 0.222318.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -0.600000 | 0.342300 |
| reorganized | 1.000000 | -0.195725 |
| draft_rank | 0.908807 | 0.170059 |
| pooled_A_BABIP | 0.877005 | 0.154735 |
| position_9 | 1.000000 | 0.154160 |
| draft_college | 1.000000 | 0.141676 |
| pooled_AAA_BABIP | 0.385580 | 0.118372 |
| prior_debut | 1.000000 | 0.096121 |
| draft_known | 1.000000 | -0.055035 |
| draft_rank_low_exposure | 0.094667 | 0.004721 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_jc | 0.000000 | -0.000000 |
| draft_hs | 0.000000 | -0.000000 |
| draft_class_unknown | 0.000000 | -0.000000 |

candidate pa: reference 40.158995, raw prediction 261.967012.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 93.638287 |
| draft_rank | 0.908807 | 78.498701 |
| pooled_AA_HR | 0.045752 | 34.556219 |
| pooled_AA_pa | 206.000000 | 15.697279 |
| age_centered | -0.600000 | 12.007027 |
| AA_0_pa | 206.000000 | 10.352667 |
| MLB_0_pa | 33.000000 | -7.742313 |
| pooled_mlb_quality | -0.011299 | -7.431207 |

candidate rate: reference -0.868906, raw prediction 0.086190.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -0.600000 | 0.362202 |
| reorganized | 1.000000 | -0.189300 |
| draft_rank | 0.908807 | 0.180380 |
| pooled_A_BABIP | 0.877005 | 0.155011 |
| position_9 | 1.000000 | 0.153443 |
| pooled_AAA_BABIP | 0.385580 | 0.115953 |
| prior_debut | 1.000000 | 0.096588 |
| pooled_AA_HR | 0.157516 | 0.075125 |
| draft_rank_low_exposure | 0.094667 | 0.004725 |
| draft_known | 1.000000 | -0.001124 |
| draft_age_known | 1.000000 | -0.001124 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | -0.000000 |

The model sees 543 AA/AAA PA and 33 MLB PA, not only draft pedigree. PA stays exactly 262, driven by roster/rank/AA power, versus actual 114. Removing the college coefficient lowers batting 0.222 to 0.086, farther from actual +0.637, yet improves delivered value because the excessive PA offsets the rate reduction. This is not a smarter talent forecast. Cowser gets 561 actual PA, Bart 282, Frazier zero: similar histories do not establish the same opportunity. The draft-age representation neither learns health nor resolves organizational use.

Actual distinct-player profile support: [('pa', 521), ('rate', 425)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Clint Frazier | 28.0 | 931.0 | 44.6 → 46.4 → 0 | 0.0000 |
| Joey Bart | 26.0 | 946.0 | 126.9 → 124.4 → 282 | 1.7731 |
| Colton Cowser | 23.0 | 1251.0 | 220.1 → 220.1 → 561 | 2.7475 |

## Jake Burger — 2021 to 2022

Selection: Fixed diagnostic.

Age 25.0; stage Current MLB; listed position 5; draft 2017/pick 11/class missing; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 340 | 18 | 91 | 23 |
| 2021 | MLB | 42 | 1 | 15 | 4 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 144.420 | -0.15591 | 0.41523 |
| draft_age | 148.360 | -0.10144 | 0.44003 |
| age_pa_only | 148.360 | -0.15591 | 0.42656 |
| age_rate_only | 144.420 | -0.10144 | 0.42834 |
| Actual | 183 | 0.6690108995886976 | 0.77702 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00313500). Separate means, not a joint distribution; no full WAR.

control pa: reference 38.249895, raw prediction 144.419682.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 94.629053 |
| pooled_MLB_K | 0.267606 | -12.921480 |
| MLB_0_pa | 42.000000 | 10.502316 |
| quality_0 | 0.054996 | 6.795318 |
| draft_rank | 0.684525 | 6.766831 |
| pooled_MLB_2B | 0.056338 | 6.533636 |
| work_0 | 42.017291 | -4.362681 |
| pooled_AAA_HR | 0.047727 | 4.025144 |

control rate: reference -0.852237, raw prediction -0.155912.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -0.400000 | 0.228697 |
| pooled_AAA_HR | 0.177273 | 0.111167 |
| position_5 | 1.000000 | 0.107074 |
| prior_debut | 1.000000 | 0.096991 |
| draft_class_unknown | 1.000000 | -0.094576 |
| work_0 | 42.017291 | 0.059833 |
| AAA_0_pa | 0.566667 | 0.054573 |
| pooled_AAA_BABIP | 0.201320 | 0.050317 |
| draft_rank | 0.684525 | 0.048310 |
| draft_rank_low_exposure | 0.142018 | 0.002492 |
| draft_known | 1.000000 | -0.001541 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_jc | 0.000000 | 0.000000 |
| draft_hs | 0.000000 | -0.000000 |
| draft_college | 0.000000 | 0.000000 |

candidate pa: reference 38.249521, raw prediction 148.360068.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 94.629053 |
| pooled_MLB_K | 0.267606 | -13.277523 |
| MLB_0_pa | 42.000000 | 10.761933 |
| draft_rank | 0.684525 | 8.991190 |
| quality_0 | 0.054996 | 6.819103 |
| pooled_MLB_2B | 0.056338 | 6.551367 |
| pooled_AAA_HR | 0.047727 | 4.633948 |
| work_0 | 42.017291 | -3.699467 |

candidate rate: reference -0.972834, raw prediction -0.101436.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -0.400000 | 0.243750 |
| pooled_AAA_HR | 0.177273 | 0.109933 |
| prior_debut | 1.000000 | 0.099077 |
| position_5 | 1.000000 | 0.095589 |
| work_0 | 42.017291 | 0.059566 |
| AAA_0_pa | 0.566667 | 0.054597 |
| draft_rank | 0.684525 | 0.052589 |
| pooled_AAA_BABIP | 0.201320 | 0.048208 |
| draft_known | 1.000000 | 0.033374 |
| draft_age_known | 1.000000 | 0.033374 |
| draft_rank_low_exposure | 0.142018 | 0.002301 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | -0.000000 |

Known age 25 and 2017 pick 11 recover approximate draft age 21 where school class is missing. His 340 AAA PA/18 HR and 42 MLB PA remain; missing prior seasons are not supplied as healthy performance. PA 144.4 to 148.4 and batting -0.156 to -0.101 both approach actual 183/+0.669. Old class-unknown coefficient disappears, but changes to intercept and other coefficients offset much of that term; do not identify the entire improvement as a causal school-data repair. Origin-selected Ray and Deichmann have zero next-year PA and Harrison 14, guarding against forcing every recovery/debut into a regular role.

Actual distinct-player profile support: [('pa', 421), ('rate', 351)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Corey Ray | 26.0 | 452.0 | 99.5 → 99.5 → 0 | 0.0000 |
| Greg Deichmann | 26.0 | 763.0 | 93.4 → 94.8 → 0 | 0.0000 |
| Monte Harrison | 25.0 | 640.0 | 92.7 → 91.1 → 14 | 0.1041 |

## Anthony Volpe — 2022 to 2023

Selection: Fixed diagnostic.

Age 21.0; stage Upper minors; listed position 6; draft 2019/pick 30/class missing; approximate draft age 18.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': -0.6000000000000001, 'draft_age_low_exposure': -0.027420702915428665}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | A | 257 | 12 | 43 | 51 |
| 2021 | Aplus | 256 | 15 | 58 | 26 |
| 2022 | AA | 497 | 18 | 88 | 57 |
| 2022 | AAA | 99 | 3 | 30 | 8 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 82.525 | -0.14770 | 0.23807 |
| draft_age | 82.525 | -0.17553 | 0.23424 |
| age_pa_only | 82.525 | -0.14770 | 0.23807 |
| age_rate_only | 82.525 | -0.17553 | 0.23424 |
| Actual | 601 | -1.3447727729230707 | 0.51373 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00313097). Separate means, not a joint distribution; no full WAR.

control pa: reference 38.768214, raw prediction 82.524648.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 0.000000 | -22.818125 |
| pooled_A_3B | 0.014725 | 21.690618 |
| age_centered | -1.200000 | 12.033576 |
| pooled_AAA_BABIP | 0.307692 | 11.688254 |
| draft_rank | 0.552527 | 9.261965 |
| on_40man | 0.000000 | -5.981171 |
| pooled_AA_K | 0.185930 | 5.933202 |
| pooled_A_2B | 0.063482 | -5.203496 |

control rate: reference -0.851468, raw prediction -0.147697.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -1.200000 | 0.679419 |
| position_6 | 1.000000 | -0.248138 |
| pooled_A_BB | 0.796859 | 0.235365 |
| reorganized | 1.000000 | -0.138872 |
| draft_class_unknown | 1.000000 | -0.124039 |
| age_squared | 1.440000 | 0.120673 |
| pooled_AA_BABIP | -0.216981 | -0.081557 |
| AA_0_pa | 0.828333 | 0.072831 |
| draft_rank | 0.552527 | 0.050345 |
| draft_known | 1.000000 | -0.022054 |
| draft_rank_low_exposure | 0.045701 | 0.000507 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_jc | 0.000000 | -0.000000 |
| draft_hs | 0.000000 | -0.000000 |
| draft_college | 0.000000 | 0.000000 |

candidate pa: reference 38.768214, raw prediction 82.524648.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 0.000000 | -22.818125 |
| pooled_A_3B | 0.014725 | 21.690618 |
| age_centered | -1.200000 | 12.033576 |
| pooled_AAA_BABIP | 0.307692 | 11.688254 |
| draft_rank | 0.552527 | 9.261965 |
| on_40man | 0.000000 | -5.981171 |
| pooled_AA_K | 0.185930 | 5.933202 |
| pooled_A_2B | 0.063482 | -5.203496 |

candidate rate: reference -0.996791, raw prediction -0.175528.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -1.200000 | 0.726585 |
| position_6 | 1.000000 | -0.260313 |
| pooled_A_BB | 0.796859 | 0.237213 |
| age_squared | 1.440000 | 0.138889 |
| reorganized | 1.000000 | -0.134259 |
| draft_age_centered | -0.600000 | -0.130104 |
| pooled_AA_BABIP | -0.216981 | -0.080752 |
| AA_0_pa | 0.828333 | 0.071735 |
| draft_rank | 0.552527 | 0.053913 |
| draft_age_known | 1.000000 | 0.026129 |
| draft_known | 1.000000 | 0.026129 |
| draft_rank_low_exposure | 0.045701 | 0.000466 |
| draft_age_low_exposure | -0.027421 | 0.000033 |
| draft_elapsed | 0.000000 | 0.000000 |

The model retains 497 AA and 99 AAA PA, 21 current homers, 118 current strikeouts and substantial 2021 production. Approximate draft age 18 comes from known age 21 and dated 2019 pick, not a reconstructed school record. PA remains exactly 82.5 versus actual 601; the roster/level opportunity bottleneck is untouched. Batting -0.148 to -0.175 happens to approach actual -1.345 but is small. Value is still misleadingly close because too little PA offsets too optimistic a rate. DeLoach does not arrive, Meadows has 145 PA and Loftin 68; prospect readiness is probabilistic, but this important high-exposure miss remains.

Actual distinct-player profile support: [('pa', 1006), ('rate', 213)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Zach DeLoach | 23.0 | 1000.0 | 18.8 → 18.5 → 0 | 0.0000 |
| Parker Meadows | 22.0 | 976.0 | 99.7 → 99.7 → 145 | 0.3203 |
| Nick Loftin | 23.0 | 1003.0 | 28.4 → 25.6 → 68 | 0.3875 |

## Aaron Judge — 2016 to 2017

Selection: Fixed diagnostic; value false low.

Age 24.0; stage Current MLB; listed position 9; draft 2013/pick 32/class missing; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 143.966 | -0.05720 | 0.43085 |
| draft_age | 146.211 | 0.02582 | 0.45780 |
| age_pa_only | 146.211 | -0.05720 | 0.43757 |
| age_rate_only | 143.966 | 0.02582 | 0.45077 |
| Actual | 678 | 5.329875619792154 | 8.10841 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00308809). Separate means, not a joint distribution; no full WAR.

control pa: reference 38.360689, raw prediction 143.965611.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 72.971051 |
| MLB_0_pa | 95.000000 | 27.203824 |
| age_centered | -0.600000 | 13.668747 |
| pooled_MLB_K | 0.333333 | -9.543102 |
| pooled_A_3B | 0.006372 | 7.595328 |
| quality_0 | -0.175091 | -6.734861 |
| pooled_AA_BABIP | 0.326014 | -6.403581 |
| pooled_Aplus_BB | 0.138007 | 6.237603 |

control rate: reference -0.746346, raw prediction -0.057204.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -0.600000 | 0.286822 |
| draft_class_unknown | 1.000000 | -0.204214 |
| position_9 | 1.000000 | 0.165561 |
| pooled_mlb_quality | -0.175091 | -0.119076 |
| pooled_Aplus_BB | 0.580074 | 0.113202 |
| pooled_Aplus_BABIP | 0.367983 | 0.090674 |
| work_0 | 95.078254 | 0.083463 |
| AA_1_pa | 0.466667 | -0.078361 |
| draft_known | 1.000000 | 0.062907 |
| draft_rank | 0.544036 | 0.019063 |
| draft_rank_low_exposure | 0.031852 | 0.000455 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_jc | 0.000000 | 0.000000 |
| draft_hs | 0.000000 | -0.000000 |
| draft_college | 0.000000 | 0.000000 |

candidate pa: reference 38.354008, raw prediction 146.210669.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 72.884112 |
| MLB_0_pa | 95.000000 | 27.175023 |
| age_centered | -0.600000 | 13.681238 |
| pooled_MLB_K | 0.333333 | -10.109528 |
| pooled_A_3B | 0.006372 | 7.595328 |
| quality_0 | -0.175091 | -6.729768 |
| pooled_Aplus_BB | 0.138007 | 6.256998 |
| pooled_AA_HR | 0.038889 | 5.995545 |

candidate rate: reference -0.980427, raw prediction 0.025820.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -0.600000 | 0.289265 |
| position_9 | 1.000000 | 0.158649 |
| pooled_mlb_quality | -0.175091 | -0.119372 |
| pooled_Aplus_BB | 0.580074 | 0.112523 |
| pooled_Aplus_BABIP | 0.367983 | 0.091431 |
| work_0 | 95.078254 | 0.088148 |
| draft_age_known | 1.000000 | 0.077606 |
| draft_known | 1.000000 | 0.077606 |
| draft_rank | 0.544036 | 0.010880 |
| draft_rank_low_exposure | 0.031852 | 0.000371 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | -0.000000 |

The learner sees 410 current AAA PA with 19 HR and 98 K separately from 95 MLB PA with 42 K. Missing 2013 school class becomes approximate draft age 21. PA 144 to 146 and batting -0.057 to +0.026 barely improve the enormous 678/+5.330 actual miss. The old missing-class term is -0.204, but the changed intercept and refitted history coefficients mean removing it does not add that whole amount. Nimmo gets 215 next-year PA, Cowart 117, Shaffer zero; the initial Judge forecast is not certified by broad training support or by the hindsight breakout. Stronger prospect/brief-debut translation remains unresolved.

Actual distinct-player profile support: [('pa', 240), ('rate', 198)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Richie Shaffer | 25.0 | 1585.0 | 121.3 → 119.6 → 0 | 0.0000 |
| Kaleb Cowart | 24.0 | 1558.0 | 178.7 → 178.7 → 117 | 0.1227 |
| Brandon Nimmo | 23.0 | 1516.0 | 195.7 → 195.7 → 215 | 1.1440 |

## Aaron Judge — 2024 to 2025

Selection: Fixed diagnostic.

Age 32.0; stage Current MLB; listed position 8; draft 2013/pick 32/class missing; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 548.496 | 4.55334 | 5.87607 |
| draft_age | 548.496 | 4.65344 | 5.96758 |
| age_pa_only | 548.496 | 4.55334 | 5.87607 |
| age_rate_only | 548.496 | 4.65344 | 5.96758 |
| Actual | 679 | 6.287431083532908 | 9.23105 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00312416). Separate means, not a joint distribution; no full WAR.

control pa: reference 39.316467, raw prediction 548.495726.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 704.289831 | 349.200542 |
| pooled_mlb_quality | 3.648566 | 59.624652 |
| quality_0 | 2.794425 | 38.851972 |
| regular_window_scaled | 1.000000 | 28.647865 |
| work_2 | 696.000000 | 23.835761 |
| age_centered | 1.000000 | -23.717465 |
| MLB_0_pa | 704.000000 | 16.915036 |
| pooled_MLB_pa | 1488.000000 | 12.057541 |

control rate: reference -0.912484, raw prediction 4.553340.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 3.648566 | 2.685922 |
| quality_0 | 2.794425 | 1.297297 |
| work_0 | 704.289831 | 0.841611 |
| age_centered | 1.000000 | -0.558514 |
| quality_2 | 2.408333 | 0.477308 |
| work_2 | 696.000000 | 0.414097 |
| quality_1 | 1.317130 | 0.285426 |
| reorganized | 1.000000 | -0.276917 |
| draft_rank | 0.544036 | 0.128683 |
| draft_known | 1.000000 | -0.090134 |
| draft_class_unknown | 1.000000 | -0.071445 |
| draft_elapsed | 1.000000 | -0.037530 |
| draft_rank_low_exposure | 0.027785 | 0.001173 |
| draft_jc | 0.000000 | -0.000000 |
| draft_hs | 0.000000 | -0.000000 |
| draft_college | 0.000000 | 0.000000 |

candidate pa: reference 39.316467, raw prediction 548.495726.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 704.289831 | 349.200542 |
| pooled_mlb_quality | 3.648566 | 59.624652 |
| quality_0 | 2.794425 | 38.851972 |
| regular_window_scaled | 1.000000 | 28.647865 |
| work_2 | 696.000000 | 23.835761 |
| age_centered | 1.000000 | -23.717465 |
| MLB_0_pa | 704.000000 | 16.915036 |
| pooled_MLB_pa | 1488.000000 | 12.057541 |

candidate rate: reference -0.996610, raw prediction 4.653443.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 3.648566 | 2.677434 |
| quality_0 | 2.794425 | 1.313017 |
| work_0 | 704.289831 | 0.842945 |
| age_centered | 1.000000 | -0.587458 |
| quality_2 | 2.408333 | 0.483882 |
| work_2 | 696.000000 | 0.408336 |
| quality_1 | 1.317130 | 0.289054 |
| reorganized | 1.000000 | -0.267075 |
| draft_rank | 0.544036 | 0.139194 |
| draft_known | 1.000000 | -0.021391 |
| draft_age_known | 1.000000 | -0.021391 |
| draft_elapsed | 1.000000 | -0.015604 |
| draft_rank_low_exposure | 0.027785 | 0.001223 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | -0.000000 |

His three MLB seasons have 696/458/704 PA and 62/37/58 HR. Those observations dominate saved paths/coefficients, appropriately more than 2013 schooling. PA stays 548.5; rate 4.553 to 4.653 moves closer to actual 6.287. Value rises 5.876 to 5.968 versus 9.231. Removing a metadata penalty is a modest representation improvement for this case, not discovery of superstar talent or a fix to remaining PA/rate shortfalls. Chapman/Castellanos/Arenado peers have divergent later results and are opportunity/context matches, not equivalents in batting talent.

Actual distinct-player profile support: [('pa', 562), ('rate', 457)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Nolan Arenado | 33.0 | 1867.0 | 514.1 → 514.1 → 436 | 0.3764 |
| Nick Castellanos | 32.0 | 1888.0 | 529.0 → 538.5 → 589 | 1.3089 |
| Matt Chapman | 31.0 | 1849.0 | 516.8 → 521.9 → 535 | 2.7612 |

## Victor Scott II — 2024 to 2025

Selection: pa largest gain.

Age 23.0; stage Current MLB; listed position 8; draft 2022/pick 157/class 4YR JR; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | A | 142 | 2 | 26 | 24 |
| 2023 | AA | 310 | 7 | 45 | 18 |
| 2023 | Aplus | 308 | 2 | 52 | 28 |
| 2024 | AAA | 362 | 6 | 57 | 36 |
| 2024 | MLB | 155 | 2 | 42 | 6 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 178.515 | -1.18245 | 0.20590 |
| draft_age | 192.260 | -1.32428 | 0.17631 |
| age_pa_only | 192.260 | -1.18245 | 0.22176 |
| age_rate_only | 178.515 | -1.32428 | 0.16370 |
| Actual | 463 | -2.092713234733604 | -0.17216 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00312416). Separate means, not a joint distribution; no full WAR.

control pa: reference 39.700981, raw prediction 178.514775.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 97.332232 |
| MLB_0_pa | 155.000000 | 32.105566 |
| quality_0 | -0.499888 | -21.133220 |
| age_centered | -0.800000 | 14.490027 |
| pooled_mlb_quality | -0.499888 | -13.717181 |
| pooled_A_3B | 0.015659 | 12.395220 |
| pooled_A_BB | 0.120950 | 7.566898 |
| pooled_AAA_K | 0.173160 | 6.776372 |

control rate: reference -0.902660, raw prediction -1.182446.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -0.800000 | 0.456131 |
| pooled_mlb_quality | -0.499888 | -0.381315 |
| quality_0 | -0.499888 | -0.239050 |
| work_0 | 155.063812 | 0.215872 |
| reorganized | 1.000000 | -0.212707 |
| draft_college | 1.000000 | 0.164565 |
| pooled_AA_BABIP | 0.403361 | 0.135615 |
| position_8 | 1.000000 | -0.134314 |
| draft_known | 1.000000 | -0.067694 |
| draft_rank | 0.334783 | 0.050746 |
| draft_rank_low_exposure | 0.024313 | 0.000221 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_jc | 0.000000 | -0.000000 |
| draft_hs | 0.000000 | -0.000000 |
| draft_class_unknown | 0.000000 | -0.000000 |

candidate pa: reference 39.700396, raw prediction 192.260217.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 97.348432 |
| MLB_0_pa | 155.000000 | 32.959328 |
| quality_0 | -0.499888 | -21.583676 |
| age_centered | -0.800000 | 14.497306 |
| pooled_A_3B | 0.015659 | 13.974969 |
| pooled_mlb_quality | -0.499888 | -13.101747 |
| pooled_AAA_K | 0.173160 | 10.036925 |
| pooled_A_BB | 0.120950 | 7.817386 |

candidate rate: reference -1.001244, raw prediction -1.324275.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -0.800000 | 0.488259 |
| pooled_mlb_quality | -0.499888 | -0.380465 |
| quality_0 | -0.499888 | -0.242345 |
| work_0 | 155.063812 | 0.214632 |
| reorganized | 1.000000 | -0.197129 |
| pooled_AA_BABIP | 0.403361 | 0.135049 |
| position_8 | 1.000000 | -0.129034 |
| prior_debut | 1.000000 | 0.118837 |
| draft_rank | 0.334783 | 0.056526 |
| draft_age_known | 1.000000 | -0.002619 |
| draft_known | 1.000000 | -0.002619 |
| draft_rank_low_exposure | 0.024313 | 0.000245 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | -0.000000 |

Actual histories include 362 AAA PA and 155 MLB PA, with six and two homers respectively. PA rises 178.5 to 192.3, closer to actual 463; batting falls -1.182 to -1.324, closer to actual -2.093. Combined value nevertheless stays positive 0.176 versus actual -0.172 because opportunity is still too low to deliver his below-replacement batting. Removing college information and refitting changes old power/age paths too. This largest PA gain is only 14 PA, not resolution of the mechanism. Peers retain low-use Baddoo/Kavadas and regular Manzardo.

Actual distinct-player profile support: [('pa', 572), ('rate', 470)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Akil Baddoo | 25.0 | 1232.0 | 63.9 → 67.2 → 18 | -0.1736 |
| Niko Kavadas | 25.0 | 1484.0 | 123.1 → 123.3 → 23 | -0.2010 |
| Kyle Manzardo | 23.0 | 1332.0 | 224.4 → 226.8 → 531 | 2.3866 |

## Jordan Walker — 2023 to 2024

Selection: pa largest harm.

Age 21.0; stage Current MLB; listed position 9; draft 2020/pick 21/class HS SR; approximate draft age 18.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': -0.6000000000000001, 'draft_age_low_exposure': -0.0224514046924169}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | A | 122 | 6 | 21 | 18 |
| 2021 | Aplus | 244 | 8 | 66 | 14 |
| 2022 | AA | 536 | 19 | 116 | 57 |
| 2023 | AAA | 135 | 4 | 32 | 16 |
| 2023 | MLB | 465 | 16 | 104 | 37 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 478.836 | 0.81041 | 2.12927 |
| draft_age | 497.077 | 0.84186 | 2.23644 |
| age_pa_only | 497.077 | 0.81041 | 2.21038 |
| age_rate_only | 478.836 | 0.84186 | 2.15437 |
| Actual | 178 | -2.035928354476044 | -0.04812 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00309608). Separate means, not a joint distribution; no full WAR.

control pa: reference 38.986504, raw prediction 478.836231.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 465.000000 | 292.353419 |
| quality_0 | 0.342889 | 47.758954 |
| age_centered | -1.200000 | 38.902073 |
| regular_window_scaled | 0.333333 | 27.485749 |
| on_40man | 1.000000 | 13.050237 |
| pooled_mlb_quality | 0.342889 | 12.548303 |
| AAA_0_pa | 135.000000 | 7.844854 |
| pooled_MLB_K | 0.224779 | 7.819861 |

control rate: reference -0.906445, raw prediction 0.810410.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -1.200000 | 0.685566 |
| work_0 | 465.000000 | 0.565543 |
| pooled_mlb_quality | 0.342889 | 0.253606 |
| reorganized | 1.000000 | -0.206516 |
| prior_debut | 1.000000 | 0.175350 |
| quality_0 | 0.342889 | 0.150932 |
| pooled_AA_BABIP | 0.474946 | 0.146337 |
| position_9 | 1.000000 | 0.131857 |
| draft_rank | 0.599453 | 0.106946 |
| draft_hs | 1.000000 | -0.102990 |
| draft_known | 1.000000 | -0.061245 |
| draft_rank_low_exposure | 0.037419 | 0.001614 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_jc | 0.000000 | 0.000000 |
| draft_college | 0.000000 | 0.000000 |
| draft_class_unknown | 0.000000 | -0.000000 |

candidate pa: reference 38.987566, raw prediction 497.076770.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 465.000000 | 292.236342 |
| age_centered | -1.200000 | 48.038807 |
| quality_0 | 0.342889 | 47.771121 |
| regular_window_scaled | 0.333333 | 28.136930 |
| on_40man | 1.000000 | 12.619803 |
| pooled_mlb_quality | 0.342889 | 12.549914 |
| AAA_0_pa | 135.000000 | 11.322213 |
| pooled_MLB_K | 0.224779 | 7.811227 |

candidate rate: reference -0.985083, raw prediction 0.841862.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -1.200000 | 0.707533 |
| work_0 | 465.000000 | 0.565651 |
| pooled_mlb_quality | 0.342889 | 0.253376 |
| reorganized | 1.000000 | -0.202363 |
| prior_debut | 1.000000 | 0.173950 |
| quality_0 | 0.342889 | 0.152809 |
| pooled_AA_BABIP | 0.474946 | 0.148656 |
| position_9 | 1.000000 | 0.129428 |
| draft_rank | 0.599453 | 0.112683 |
| draft_age_centered | -0.600000 | -0.083373 |
| draft_age_known | 1.000000 | -0.007647 |
| draft_known | 1.000000 | -0.007647 |
| draft_rank_low_exposure | 0.037419 | 0.001635 |
| draft_age_low_exposure | -0.022451 | 0.000115 |
| draft_elapsed | 0.000000 | 0.000000 |

The origin has 465 MLB PA and 16 HR at age 21, plus 135 AAA PA. A substantial next-year role is reasonable ex ante. Refit age-path opportunity raises PA 479 to 497, farther from actual 178; batting also rises 0.810 to 0.842 despite actual -2.036. This is the largest PA harm, not a concealed tradeoff. Turang later gets 619 PA but Thomas/Baty only 103/171, showing retention risk. The model does not know the future demotion or breakdown and the change does not improve its assessment of that risk.

Actual distinct-player profile support: [('pa', 253), ('rate', 220)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Brice Turang | 23.0 | 1610.0 | 308.0 → 307.9 → 619 | 1.1015 |
| Alek Thomas | 23.0 | 1567.0 | 368.5 → 365.3 → 103 | -0.0977 |
| Brett Baty | 23.0 | 1357.0 | 375.3 → 375.3 → 171 | 0.1261 |

## Matt McLain — 2023 to 2024

Selection: pa false high.

Age 23.0; stage Current MLB; listed position 6; draft 2021/pick 17/class 4YR JR; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | Aplus | 119 | 3 | 24 | 17 |
| 2021 | RK121 | 7 | 0 | 0 | 0 |
| 2022 | AA | 452 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 16 | 115 | 31 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 561.901 | 0.88467 | 2.56818 |
| draft_age | 558.430 | 0.80234 | 2.47570 |
| age_pa_only | 558.430 | 0.88467 | 2.55232 |
| age_rate_only | 561.901 | 0.80234 | 2.49109 |
| Actual | 0 | not observed | 0.00000 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00309608). Separate means, not a joint distribution; no full WAR.

control pa: reference 39.120812, raw prediction 561.901395.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 403.000000 | 266.373658 |
| age_centered | -0.800000 | 65.589750 |
| quality_0 | 0.672812 | 42.318393 |
| pooled_mlb_quality | 0.672812 | 32.869643 |
| pooled_AAA_HR | 0.053571 | 30.573945 |
| regular_window_scaled | 0.333333 | 30.526850 |
| on_40man | 1.000000 | 22.716499 |
| pooled_MLB_K | 0.274354 | -19.008612 |

control rate: reference -0.951149, raw prediction 0.884667.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 0.672812 | 0.519938 |
| work_0 | 403.000000 | 0.513726 |
| age_centered | -0.800000 | 0.430328 |
| quality_0 | 0.672812 | 0.321554 |
| position_6 | 1.000000 | -0.294284 |
| prior_debut | 1.000000 | 0.207816 |
| pooled_AA_BB | 0.569151 | 0.199951 |
| reorganized | 1.000000 | -0.197988 |
| draft_rank | 0.627253 | 0.096634 |
| draft_college | 1.000000 | 0.080541 |
| draft_known | 1.000000 | -0.061564 |
| draft_rank_low_exposure | 0.049743 | 0.001961 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_jc | 0.000000 | -0.000000 |
| draft_hs | 0.000000 | 0.000000 |
| draft_class_unknown | 0.000000 | -0.000000 |

candidate pa: reference 39.122314, raw prediction 558.429915.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 403.000000 | 266.385236 |
| age_centered | -0.800000 | 60.157637 |
| quality_0 | 0.672812 | 42.326402 |
| pooled_mlb_quality | 0.672812 | 32.883975 |
| regular_window_scaled | 0.333333 | 30.526850 |
| pooled_AAA_HR | 0.053571 | 29.080251 |
| on_40man | 1.000000 | 22.248507 |
| pooled_MLB_K | 0.274354 | -16.717411 |

candidate rate: reference -1.034302, raw prediction 0.802343.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 0.672812 | 0.518463 |
| work_0 | 403.000000 | 0.513638 |
| age_centered | -0.800000 | 0.462078 |
| quality_0 | 0.672812 | 0.325763 |
| position_6 | 1.000000 | -0.302314 |
| prior_debut | 1.000000 | 0.208525 |
| pooled_AA_BB | 0.569151 | 0.197598 |
| reorganized | 1.000000 | -0.194759 |
| draft_rank | 0.627253 | 0.106785 |
| draft_known | 1.000000 | -0.007347 |
| draft_age_known | 1.000000 | -0.007347 |
| draft_rank_low_exposure | 0.049743 | 0.001958 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | 0.000000 |

The source supplies 403 MLB PA, 16 HR and 180 AAA PA with 12 HR at age 23. Expected PA 562 to 558 barely reduces the largest false high versus a zero season. Batting 0.885 to 0.802 lowers value 2.568 to 2.476, but this is not anticipation of a later injury. Unknown future absence remains unmodeled, not a failure to import a fact that was unavailable at cutoff. The three peers have 388/448/171 actual PA, not uniform healthy seasons; a distribution would better express this uncertainty than a renamed point forecast.

Actual distinct-player profile support: [('pa', 505), ('rate', 412)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Will Benson | 25.0 | 1363.0 | 363.3 → 356.6 → 388 | 0.4203 |
| Patrick Bailey | 24.0 | 1167.0 | 268.8 → 266.2 → 448 | 0.3939 |
| Brett Baty | 23.0 | 1357.0 | 375.3 → 375.3 → 171 | 0.1261 |

## Jackson Merrill — 2023 to 2024

Selection: pa false low.

Age 20.0; stage Upper minors; listed position 6; draft 2021/pick 27/class HS SR; approximate draft age 18.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': -0.6000000000000001, 'draft_age_low_exposure': -0.03464151336400815}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | RK121 | 120 | 0 | 27 | 10 |
| 2022 | A | 219 | 5 | 42 | 19 |
| 2022 | RK121 | 31 | 1 | 2 | 1 |
| 2023 | AA | 211 | 5 | 25 | 18 |
| 2023 | Aplus | 300 | 10 | 37 | 17 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 43.099 | -0.34702 | 0.10851 |
| draft_age | 43.099 | -0.39899 | 0.10478 |
| age_pa_only | 43.099 | -0.34702 | 0.10851 |
| age_rate_only | 43.099 | -0.39899 | 0.10478 |
| Actual | 593 | 1.9557615852648753 | 3.78481 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00309608). Separate means, not a joint distribution; no full WAR.

control pa: reference 40.158995, raw prediction 43.099452.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 0.000000 | -23.546906 |
| pooled_AA_pa | 211.000000 | 15.290332 |
| draft_rank | 0.566389 | 12.855300 |
| pooled_AA_K | 0.154341 | 8.709011 |
| age_centered | -1.400000 | 7.281750 |
| on_40man | 0.000000 | -6.052880 |
| pooled_AA_BABIP | 0.292308 | -3.341883 |
| pooled_AA_2B | 0.057878 | 3.032012 |

control rate: reference -0.785423, raw prediction -0.347021.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -1.400000 | 0.798700 |
| position_6 | 1.000000 | -0.304589 |
| reorganized | 1.000000 | -0.195725 |
| age_squared | 1.960000 | 0.123089 |
| draft_rank | 0.566389 | 0.105984 |
| pooled_A_BABIP | 0.509091 | 0.089822 |
| pooled_Aplus_K | -0.800000 | 0.084604 |
| draft_known | 1.000000 | -0.055035 |
| draft_hs | 1.000000 | -0.032217 |
| draft_rank_low_exposure | 0.057736 | 0.002879 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_jc | 0.000000 | -0.000000 |
| draft_college | 0.000000 | 0.000000 |
| draft_class_unknown | 0.000000 | -0.000000 |

candidate pa: reference 40.158995, raw prediction 43.099452.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 0.000000 | -23.546906 |
| pooled_AA_pa | 211.000000 | 15.290332 |
| draft_rank | 0.566389 | 12.855300 |
| pooled_AA_K | 0.154341 | 8.709011 |
| age_centered | -1.400000 | 7.281750 |
| on_40man | 0.000000 | -6.052880 |
| pooled_AA_BABIP | 0.292308 | -3.341883 |
| pooled_AA_2B | 0.057878 | 3.032012 |

candidate rate: reference -0.868906, raw prediction -0.398988.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| age_centered | -1.400000 | 0.845137 |
| position_6 | 1.000000 | -0.311086 |
| reorganized | 1.000000 | -0.189300 |
| age_squared | 1.960000 | 0.140438 |
| draft_rank | 0.566389 | 0.112417 |
| draft_age_centered | -0.600000 | -0.107641 |
| pooled_A_BABIP | 0.509091 | 0.089982 |
| pooled_Aplus_K | -0.800000 | 0.076800 |
| draft_rank_low_exposure | 0.057736 | 0.002882 |
| draft_known | 1.000000 | -0.001124 |
| draft_age_known | 1.000000 | -0.001124 |
| draft_age_low_exposure | -0.034642 | 0.000300 |
| draft_elapsed | 0.000000 | 0.000000 |

Actual age 20, 211 AA/300 A+ PA, 15 current HR and 62 current K survive the source and features. Approximate draft age 18 replaces known HS class. PA stays 43.1, versus actual 593; rate -0.347 to -0.399 worsens against actual +1.956. A high-level readiness/talent miss remains. Beavers, Muncy and Montgomery have zero next-year MLB PA under the origin-only peer rule, so Merrill's leap is a tail event rather than evidence all similar upper-minor hitters should be immediate regulars. His unusually successful leap still needs to appear as plausible upside in a practical prospect forecast.

Actual distinct-player profile support: [('pa', 1039), ('rate', 213)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Dylan Beavers | 21.0 | 631.0 | 58.4 → 58.3 → 0 | 0.0000 |
| Max Muncy | 20.0 | 1134.0 | 59.5 → 59.2 → 0 | 0.0000 |
| Colson Montgomery | 21.0 | 826.0 | 22.1 → 22.0 → 0 | 0.0000 |

## Nicky Lopez — 2021 to 2022

Selection: pa ordinary.

Age 26.0; stage Current MLB; listed position 6; draft 2016/pick 163/class missing; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 138 | 3 | 5 | 20 |
| 2019 | MLB | 402 | 2 | 51 | 18 |
| 2020 | MLB | 192 | 1 | 41 | 18 |
| 2021 | MLB | 565 | 2 | 74 | 49 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 478.687 | -0.53969 | 1.07012 |
| draft_age | 480.152 | -0.49713 | 1.10745 |
| age_pa_only | 480.152 | -0.53969 | 1.07339 |
| age_rate_only | 478.687 | -0.49713 | 1.10407 |
| Actual | 480 | -3.0392768582335714 | -0.92855 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00313500). Separate means, not a joint distribution; no full WAR.

control pa: reference 38.761667, raw prediction 478.686830.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 565.232606 | 339.129304 |
| quality_0 | 0.165756 | 24.872340 |
| regular_window_scaled | 1.000000 | 21.920776 |
| pooled_MLB_pa | 959.800000 | 18.229091 |
| age_centered | -0.200000 | 17.462435 |
| pooled_MLB_K | 0.151349 | 14.183502 |
| on_40man | 1.000000 | 13.456526 |
| MLB_0_pa | 565.000000 | -12.180009 |

control rate: reference -0.907827, raw prediction -0.539686.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 565.232606 | 0.685276 |
| pooled_mlb_quality | -0.453732 | -0.339285 |
| work_2 | 402.165500 | 0.304301 |
| position_6 | 1.000000 | -0.261110 |
| work_1 | 519.554566 | 0.208022 |
| prior_debut | 1.000000 | 0.199560 |
| pooled_MLB_pa | 1.599667 | -0.168228 |
| quality_present_1 | 1.000000 | 0.152312 |
| draft_class_unknown | 1.000000 | -0.053377 |
| draft_rank | 0.329849 | 0.042767 |
| draft_known | 1.000000 | -0.023200 |
| draft_rank_low_exposure | 0.023611 | 0.000847 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_jc | 0.000000 | 0.000000 |
| draft_hs | 0.000000 | 0.000000 |
| draft_college | 0.000000 | 0.000000 |

candidate pa: reference 38.763005, raw prediction 480.151520.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 565.232606 | 339.129304 |
| quality_0 | 0.165756 | 24.865338 |
| regular_window_scaled | 1.000000 | 21.920776 |
| pooled_MLB_pa | 959.800000 | 18.229091 |
| age_centered | -0.200000 | 16.996679 |
| MLB_0_pa | 565.000000 | -14.131703 |
| pooled_MLB_K | 0.151349 | 14.101553 |
| on_40man | 1.000000 | 13.456526 |

candidate rate: reference -0.990209, raw prediction -0.497130.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 565.232606 | 0.687954 |
| pooled_mlb_quality | -0.453732 | -0.339283 |
| work_2 | 402.165500 | 0.312853 |
| position_6 | 1.000000 | -0.268758 |
| work_1 | 519.554566 | 0.209736 |
| prior_debut | 1.000000 | 0.202636 |
| pooled_MLB_pa | 1.599667 | -0.171110 |
| quality_present_1 | 1.000000 | 0.154507 |
| draft_rank | 0.329849 | 0.048895 |
| draft_age_known | 1.000000 | 0.015372 |
| draft_known | 1.000000 | 0.015372 |
| draft_rank_low_exposure | 0.023611 | 0.000825 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | 0.000000 |

565 current MLB PA, low homers and strong contact produce essentially correct next-year PA (479 to 480, actual 480). This ordinary PA case is not ordinary batting: actual rate falls to -3.039 while forecast becomes more optimistic -0.540 to -0.497. The changed metadata/intercept does not identify that collapse. Expected contribution rises to 1.107 versus actual -0.929, a harm hidden by a near-perfect workload estimate. Cronenworth/Lowe/Hays peers span 266 to 684 actual PA and very different batting outcomes.

Actual distinct-player profile support: [('pa', 404), ('rate', 338)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Jake Cronenworth | 27.0 | 1254.0 | 543.2 → 541.9 → 684 | 2.5854 |
| Brandon Lowe | 26.0 | 1185.0 | 519.5 → 522.6 → 266 | 0.7901 |
| Austin Hays | 25.0 | 1124.0 | 429.3 → 429.9 → 582 | 2.0867 |

## Khris Davis — 2018 to 2019

Selection: value largest gain.

Age 30.0; stage Current MLB; listed position 10; draft 2009/pick 226/class JR; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2016 | MLB | 610 | 42 | 166 | 42 |
| 2017 | MLB | 652 | 43 | 195 | 72 |
| 2018 | MLB | 654 | 48 | 175 | 54 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 582.706 | 2.27562 | 4.00405 |
| draft_age | 581.402 | 2.00222 | 3.73016 |
| age_pa_only | 581.402 | 2.27562 | 3.99509 |
| age_rate_only | 582.706 | 2.00222 | 3.73852 |
| Actual | 533 | -1.51848026967886 | 0.27927 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00307877). Separate means, not a joint distribution; no full WAR.

control pa: reference 38.323514, raw prediction 582.706175.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| MLB_0_pa | 654.000000 | 250.666782 |
| work_0 | 653.730975 | 99.358422 |
| quality_0 | 0.872361 | 52.881775 |
| pooled_MLB_K | 0.276316 | -44.679257 |
| pooled_mlb_quality | 1.228087 | 40.290906 |
| MLB_2_pa | 610.000000 | 33.687217 |
| regular_window_scaled | 1.000000 | 31.860267 |
| pooled_MLB_pa | 1541.600000 | 20.876716 |

control rate: reference -0.852402, raw prediction 2.275624.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 1.228087 | 0.844572 |
| work_0 | 653.730975 | 0.518248 |
| work_1 | 652.000000 | 0.482113 |
| quality_0 | 0.872361 | 0.369112 |
| age_centered | 0.600000 | -0.313920 |
| work_2 | 610.502471 | 0.267525 |
| quality_1 | 0.764499 | 0.208571 |
| draft_college | 1.000000 | 0.202477 |
| draft_known | 1.000000 | 0.041225 |
| draft_rank | 0.286856 | 0.016661 |
| draft_rank_low_exposure | 0.014229 | 0.000434 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_jc | 0.000000 | 0.000000 |
| draft_hs | 0.000000 | -0.000000 |
| draft_class_unknown | 0.000000 | -0.000000 |

candidate pa: reference 38.325429, raw prediction 581.402184.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| MLB_0_pa | 654.000000 | 250.893569 |
| work_0 | 653.730975 | 99.016089 |
| quality_0 | 0.872361 | 52.657092 |
| pooled_MLB_K | 0.276316 | -44.816800 |
| pooled_mlb_quality | 1.228087 | 39.789678 |
| MLB_2_pa | 610.000000 | 33.884037 |
| regular_window_scaled | 1.000000 | 31.860267 |
| pooled_MLB_pa | 1541.600000 | 20.955856 |

candidate rate: reference -1.031500, raw prediction 2.002217.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 1.228087 | 0.847237 |
| work_0 | 653.730975 | 0.533441 |
| work_1 | 652.000000 | 0.498198 |
| quality_0 | 0.872361 | 0.374195 |
| age_centered | 0.600000 | -0.315688 |
| work_2 | 610.502471 | 0.287723 |
| quality_1 | 0.764499 | 0.209133 |
| position_10 | 1.000000 | 0.183363 |
| draft_known | 1.000000 | 0.056691 |
| draft_age_known | 1.000000 | 0.056691 |
| draft_rank | 0.286856 | 0.010640 |
| draft_rank_low_exposure | 0.014229 | 0.000395 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | -0.000000 |

Three consecutive 42/43/48-HR seasons at 610/652/654 PA justify expecting substantial power, not foreknowledge of collapse. PA falls only 583 to 581 while rate 2.276 to 2.002 moves toward actual -1.518; combined value 4.004 to 3.730 remains far above 0.279. Removing the college coefficient and refitting produces the largest value gain but is not a validated aging/injury insight. Same-draft-age Goldschmidt, Dozier and Merrifield do not all collapse. A real gain for Davis is counterbalanced by Martinez's harm.

Actual distinct-player profile support: [('pa', 320), ('rate', 265)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Paul Goldschmidt | 30.0 | 2060.0 | 597.1 → 597.1 → 682 | 3.6247 |
| Brian Dozier | 31.0 | 2028.0 | 449.5 → 453.3 → 482 | 1.9038 |
| Whit Merrifield | 29.0 | 2010.0 | 538.4 → 538.4 → 735 | 3.5179 |

## J.D. Martinez — 2017 to 2018

Selection: value largest harm.

Age 29.0; stage Current MLB; listed position 9; draft 2009/pick 611/class JR; approximate draft age 21.0.

New inputs: {'draft_age_known': 1, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2015 | MLB | 657 | 38 | 178 | 46 |
| 2016 | AAA | 38 | 0 | 11 | 1 |
| 2016 | MLB | 517 | 22 | 128 | 47 |
| 2017 | AAA | 18 | 1 | 6 | 2 |
| 2017 | Aplus | 8 | 1 | 1 | 0 |
| 2017 | MLB | 489 | 45 | 128 | 45 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 474.787 | 3.23769 | 4.02255 |
| draft_age | 474.787 | 2.99727 | 3.83231 |
| age_pa_only | 474.787 | 3.23769 | 4.02255 |
| age_rate_only | 474.787 | 2.99727 | 3.83231 |
| Actual | 649 | 5.378874677720724 | 7.81709 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00307618). Separate means, not a joint distribution; no full WAR.

control pa: reference 40.067776, raw prediction 474.787325.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| MLB_0_pa | 489.000000 | 199.811930 |
| work_0 | 489.000000 | 82.246491 |
| on_40man | 0.000000 | -62.109487 |
| quality_0 | 1.546489 | 47.129295 |
| regular_window_scaled | 1.000000 | 33.204969 |
| MLB_2_pa | 657.000000 | 33.068830 |
| quality_1 | 1.015609 | 22.629885 |
| pooled_MLB_pa | 1296.800000 | 19.789561 |

control rate: reference -0.773903, raw prediction 3.237690.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 2.053077 | 1.412356 |
| quality_0 | 1.546489 | 0.651496 |
| work_2 | 657.270482 | 0.541168 |
| work_0 | 489.000000 | 0.395458 |
| quality_1 | 1.015609 | 0.300298 |
| position_9 | 1.000000 | 0.202698 |
| age_centered | 0.400000 | -0.182010 |
| work_1 | 517.425865 | 0.173479 |
| draft_college | 1.000000 | 0.118343 |
| draft_known | 1.000000 | 0.099376 |
| draft_rank | 0.156009 | 0.005884 |
| draft_rank_low_exposure | 0.008539 | 0.000262 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_jc | 0.000000 | 0.000000 |
| draft_hs | 0.000000 | 0.000000 |
| draft_class_unknown | 0.000000 | -0.000000 |

candidate pa: reference 40.067776, raw prediction 474.787325.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| MLB_0_pa | 489.000000 | 199.811930 |
| work_0 | 489.000000 | 82.246491 |
| on_40man | 0.000000 | -62.109487 |
| quality_0 | 1.546489 | 47.129295 |
| regular_window_scaled | 1.000000 | 33.204969 |
| MLB_2_pa | 657.000000 | 33.068830 |
| quality_1 | 1.015609 | 22.629885 |
| pooled_MLB_pa | 1296.800000 | 19.789561 |

candidate rate: reference -0.998473, raw prediction 2.997272.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 2.053077 | 1.418455 |
| quality_0 | 1.546489 | 0.663444 |
| work_2 | 657.270482 | 0.553730 |
| work_0 | 489.000000 | 0.406571 |
| quality_1 | 1.015609 | 0.299890 |
| position_9 | 1.000000 | 0.195346 |
| age_centered | 0.400000 | -0.186440 |
| work_1 | 517.425865 | 0.185044 |
| draft_age_known | 1.000000 | 0.087428 |
| draft_known | 1.000000 | 0.087428 |
| draft_rank | 0.156009 | 0.002174 |
| draft_rank_low_exposure | 0.008539 | 0.000234 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | 0.000000 |

489 current MLB PA with 45 HR plus two prior strong MLB seasons support exceptional hitting. PA stays 474.8 versus actual 649; batting falls 3.238 to 2.997 versus actual 5.379, creating the largest value harm. School class was observed in 2009, not missing: its removal loses a useful fitted association for this player, with changed intercept/other coefficients also contributing. The saved PA path includes a negative roster-listing effect; free-agent/nonlisted status is not proof of inability to play, and the older roster source remains imperfect. Reddick/Moreland/Gennett peers have 459 to 638 PA, not proof Martinez deserved his later exact outcome.

Actual distinct-player profile support: [('pa', 275), ('rate', 231)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Josh Reddick | 30.0 | 1595.0 | 498.8 → 501.8 → 487 | 1.3380 |
| Mitch Moreland | 31.0 | 1611.0 | 474.2 → 469.1 → 459 | 1.8809 |
| Scooter Gennett | 27.0 | 1531.0 | 500.4 → 499.9 → 638 | 4.4348 |

## Yordan Alvarez — 2024 to 2025

Selection: value false high.

Age 27.0; stage Current MLB; listed position 10; draft None/pick None/class missing; approximate draft age None.

New inputs: {'draft_age_known': 0, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 584.774 | 3.70970 | 5.44249 |
| draft_age | 582.293 | 3.72452 | 5.43378 |
| age_pa_only | 582.293 | 3.70970 | 5.41940 |
| age_rate_only | 584.774 | 3.72452 | 5.45694 |
| Actual | 199 | 0.919648372891386 | 0.92510 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00312416). Separate means, not a joint distribution; no full WAR.

control pa: reference 39.299703, raw prediction 584.774268.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 635.261424 | 351.759640 |
| pooled_mlb_quality | 2.457089 | 39.928198 |
| quality_0 | 1.415653 | 34.967096 |
| regular_window_scaled | 1.000000 | 25.914489 |
| MLB_0_pa | 635.000000 | 22.881456 |
| quality_1 | 1.383087 | 19.770831 |
| pooled_MLB_HR | 0.057886 | 16.270451 |
| age_centered | 0.000000 | 12.203306 |

control rate: reference -0.972293, raw prediction 3.709704.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 2.457089 | 1.888702 |
| work_0 | 635.261424 | 0.764881 |
| quality_0 | 1.415653 | 0.683356 |
| work_2 | 561.000000 | 0.456937 |
| quality_2 | 1.738114 | 0.337737 |
| quality_1 | 1.383087 | 0.321080 |
| position_10 | 1.000000 | 0.295454 |
| reorganized | 1.000000 | -0.276479 |
| draft_class_unknown | 1.000000 | -0.056273 |
| draft_known | 0.000000 | -0.000000 |
| draft_rank | 0.000000 | 0.000000 |
| draft_hs | 0.000000 | 0.000000 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_jc | 0.000000 | -0.000000 |
| draft_college | 0.000000 | 0.000000 |
| draft_rank_low_exposure | 0.000000 | 0.000000 |

candidate pa: reference 39.297520, raw prediction 582.293254.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| work_0 | 635.261424 | 351.759640 |
| pooled_mlb_quality | 2.457089 | 39.941107 |
| quality_0 | 1.415653 | 34.960632 |
| regular_window_scaled | 1.000000 | 25.914489 |
| MLB_0_pa | 635.000000 | 22.881456 |
| quality_1 | 1.383087 | 19.769013 |
| pooled_MLB_HR | 0.057886 | 15.453516 |
| age_centered | 0.000000 | 12.192753 |

candidate rate: reference -1.048671, raw prediction 3.724522.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 2.457089 | 1.883472 |
| work_0 | 635.261424 | 0.765145 |
| quality_0 | 1.415653 | 0.692088 |
| work_2 | 561.000000 | 0.458712 |
| quality_2 | 1.738114 | 0.343670 |
| quality_1 | 1.383087 | 0.323067 |
| position_10 | 1.000000 | 0.291378 |
| reorganized | 1.000000 | -0.267585 |
| draft_known | 0.000000 | -0.000000 |
| draft_rank | 0.000000 | 0.000000 |
| draft_elapsed | 0.000000 | 0.000000 |
| draft_rank_low_exposure | 0.000000 | 0.000000 |
| draft_age_known | 0.000000 | -0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | 0.000000 |

The model sees 561/496/635 MLB PA and 37/31/35 HR. No dated draft is known; age at draft stays explicitly unknown rather than becoming 27 or college. PA/rate remain about 582/+3.724 versus actual 199/+0.920. This largest value false high reflects future lost availability and performance; removing school flags does not solve it. Devers becomes a huge contributor, De La Cruz gets 50 PA and Contreras 659 under the same origin-based peer rule, demonstrating why point means do not express downside risk.

Actual distinct-player profile support: [('pa', 872), ('rate', 616)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Rafael Devers | 27.0 | 1871.0 | 617.6 → 617.6 → 729 | 5.2343 |
| Bryan De La Cruz | 27.0 | 1657.0 | 468.2 → 467.5 → 50 | -0.2693 |
| William Contreras | 26.0 | 1717.0 | 556.2 → 558.0 → 659 | 3.0970 |

## Willians Astudillo — 2018 to 2019

Selection: value ordinary.

Age 26.0; stage Current MLB; listed position 2; draft None/pick None/class missing; approximate draft age None.

New inputs: {'draft_age_known': 0, 'draft_age_centered': 0.0, 'draft_age_low_exposure': 0.0}.

| Season | Bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 342 | 4 | 11 | 4 |
| 2017 | AAA | 128 | 4 | 5 | 4 |
| 2018 | AAA | 307 | 12 | 14 | 9 |
| 2018 | MLB | 97 | 3 | 3 | 2 |

The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement |
|---|---:|---:|---:|
| cohort | 254.435 | -1.56266 | 0.12069 |
| draft_age | 254.435 | -1.57496 | 0.11547 |
| age_pa_only | 254.435 | -1.56266 | 0.12069 |
| age_rate_only | 254.435 | -1.57496 | 0.11547 |
| Actual | 204 | -1.4916410381797318 | 0.11601 |

Contribution = PA × (batting rate / 600 + origin replacement 0.00307877). Separate means, not a joint distribution; no full WAR.

control pa: reference 39.692720, raw prediction 254.434920.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 86.909393 |
| quality_0 | 0.250809 | 52.209566 |
| pooled_mlb_quality | 0.250809 | 43.810128 |
| pooled_MLB_K | 0.131980 | 25.636481 |
| pooled_MLB_BB | 0.050761 | 9.409855 |
| AAA_0_pa | 307.000000 | 7.954299 |
| pooled_AA_BABIP | 0.275766 | 6.160284 |
| pooled_AAA_HR | 0.035728 | 3.887367 |

control rate: reference -0.757539, raw prediction -1.562663.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_AAA_K | -1.495132 | -0.346018 |
| pooled_AA_K | -1.330144 | -0.276080 |
| position_2 | 1.000000 | -0.228404 |
| pooled_mlb_quality | 0.250809 | 0.180415 |
| draft_class_unknown | 1.000000 | -0.168554 |
| prior_debut | 1.000000 | 0.125095 |
| pooled_AA_BB | -0.459240 | -0.119424 |
| pooled_MLB_K | -0.980203 | 0.117881 |
| draft_known | 0.000000 | 0.000000 |
| draft_rank | 0.000000 | 0.000000 |
| draft_hs | 0.000000 | 0.000000 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_jc | 0.000000 | 0.000000 |
| draft_college | 0.000000 | 0.000000 |
| draft_rank_low_exposure | 0.000000 | 0.000000 |

candidate pa: reference 39.692720, raw prediction 254.434920.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 86.909393 |
| quality_0 | 0.250809 | 52.209566 |
| pooled_mlb_quality | 0.250809 | 43.810128 |
| pooled_MLB_K | 0.131980 | 25.636481 |
| pooled_MLB_BB | 0.050761 | 9.409855 |
| AAA_0_pa | 307.000000 | 7.954299 |
| pooled_AA_BABIP | 0.275766 | 6.160284 |
| pooled_AAA_HR | 0.035728 | 3.887367 |

candidate rate: reference -0.948725, raw prediction -1.574960.

| Actual feature | Input (scaled for rate) | Accounting effect |
|---|---:|---:|
| pooled_AAA_K | -1.495132 | -0.337804 |
| pooled_AA_K | -1.330144 | -0.279063 |
| position_2 | 1.000000 | -0.236856 |
| pooled_mlb_quality | 0.250809 | 0.180986 |
| prior_debut | 1.000000 | 0.127255 |
| pooled_AA_BB | -0.459240 | -0.116222 |
| pooled_MLB_K | -0.980203 | 0.110538 |
| quality_0 | 0.250809 | 0.105800 |
| draft_known | 0.000000 | 0.000000 |
| draft_rank | 0.000000 | 0.000000 |
| draft_elapsed | 0.000000 | -0.000000 |
| draft_rank_low_exposure | 0.000000 | 0.000000 |
| draft_age_known | 0.000000 | 0.000000 |
| draft_age_centered | 0.000000 | 0.000000 |
| draft_age_low_exposure | 0.000000 | 0.000000 |

97 MLB PA with three strikeouts sit beside 307 AAA PA with 14 K, 12 HR and only nine UBB. No dated draft age is fabricated. PA stays 254 versus actual 204 and rate becomes -1.575 versus actual -1.492. Predicted contribution 0.1155 nearly equals actual 0.1160, but wrong PA offsets a somewhat wrong rate: this ordinary value result is not evidence of component accuracy. Saved rate coefficients on very low upper-minor strikeouts do not by themselves prove causal contact value; power, walks, selection and exposure are intertwined. Santana's future success and Sanchez/Castro's small or zero use remain in peer evidence.

Actual distinct-player profile support: [('pa', 736), ('rate', 505)]. Sparse groups are retained, not certified by the pooled sample.

| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |
|---|---:|---:|---|---:|
| Adrián Sanchez | 27.0 | 1122.0 | 128.3 → 129.0 → 32 | -0.1911 |
| Danny Santana | 27.0 | 840.0 | 48.4 → 48.4 → 511 | 2.9941 |
| Daniel Castro | 25.0 | 1115.0 | 23.2 → 28.7 → 0 | 0.0000 |

## Disposition

No working-model promotion. Retain explicit draft-age/source-coverage diagnostics, and the consistent-age representation as research. Overall conditional batting improves slightly but combined value gain is tiny/uncertain, public PA/value slightly worsen, and fast-entry/return opportunity is essentially untouched. Source-label inconsistency was real; its simple replacement was not a practically established cure. No additional school/age parameter sweep.

The next substantial question is uncertainty and opportunity: distinguish next-year participation/range from longer-term talent promise and assess systematic PA calibration by observable workload profiles. Do not equate an individual breakout miss with a wrong cohort mean or use current-year outcomes to force a favorable prospect rank.
