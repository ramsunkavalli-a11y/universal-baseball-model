# V40: completed contact-source compatibility walkthrough

No model fitted or scored. Source hashes verified. Same broad eligibility; missing rows retained as null, not neutral/zero talent. Eight fixed source cases and origin-only same-stage/debut age/exposure/draft peers. No future success used for source selection.

Earlier gradient target levels are A, High-A, AA, AAA and Rookie only; all target rows have positive observed contact. Earlier folds hold time out but contain repeated train/test players, unlike the present whole-player folds. That is a different validation design, not automatic proof the earlier test is invalid for its stated conditional target. Its score cannot certify future MLB hitting, arrival, workload or value.

Earlier source contact cells are raw measured counts with a 100-contact source-level-bin prior. Mean prior-opponent/hand and park effects are separate covariates. This is not direct fully park-neutralized player evidence. The universal shape table includes MLB, uses actual league identity and spans 2021–24; the examined older gradient table spans those same years but minor contacts only. Neither inspected table supplies 2016–20 shape measurements.

## Aaron Judge: origin 2016

Actual 410 AAA PA and 95 MLB PA remain in the broad backbone, but neither inspected contact table covers 2016. Null contact fields mean unavailable in these tables, not no contact skill. Cowart/Decker/Marrero have the same source limitation. These tables cannot repair or validate the 2017 Judge forecast without reconstructing the older source.

| Year | Actual league bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

Actual source-to-input join: {'age': 24.0, 'stage': 'Current MLB', 'source_position': '9', 'pa_0': 95, 'AAA_0_pa': 410.0, 'AA_0_pa': 0.0, 'draft_known': 1, 'pick_number': 32, 'legacy_contact_level': None, 'materialized_contacts': None, 'opponent_context_known_rate': None, 'park_factor_known_rate': None, 'shape_all': None, 'shape_mlb': None, 'shape_minor': None}.

| Shape year | Actual league ID | Source level | Bin | Observations |
|---|---:|---|---|---:|

Old detailed source history (minor-only): [].

Origin-only peers: Kaleb Cowart (MLB/AAA/AA PA 87/458.0/0.0; old contacts None; universal MLB/minor shapes None/None); Jaff Decker (MLB/AAA/AA PA 57/417.0/0.0; old contacts None; universal MLB/minor shapes None/None); Deven Marrero (MLB/AAA/AA PA 14/388.0/0.0; old contacts None; universal MLB/minor shapes None/None).

No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.

## Aaron Judge: origin 2024

The old gradient source has no row because he has no current minor-league contact evidence. The separate universal shape table has 381 current MLB contacts, plus 396 in 2022 and 236 in 2023. Castellanos/Chapman/Olson show the same distinction. Calling the old missing join no current detailed contact evidence without qualifying MiLB-only would mislead the explorer user; MLB evidence exists in a different source.

| Year | Actual league bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

Actual source-to-input join: {'age': 32.0, 'stage': 'Current MLB', 'source_position': '8', 'pa_0': 704, 'AAA_0_pa': 0.0, 'AA_0_pa': 0.0, 'draft_known': 1, 'pick_number': 32, 'legacy_contact_level': None, 'materialized_contacts': None, 'opponent_context_known_rate': None, 'park_factor_known_rate': None, 'shape_all': 381, 'shape_mlb': 381, 'shape_minor': 0}.

| Shape year | Actual league ID | Source level | Bin | Observations |
|---|---:|---|---|---:|
| 2022 | 103 | MLB | CENTER_GB | 49 |
| 2022 | 103 | MLB | CENTER_LD | 32 |
| 2022 | 103 | MLB | CENTER_OFFB | 63 |
| 2022 | 103 | MLB | IFFB | 8 |
| 2022 | 103 | MLB | OPPO_GB | 9 |
| 2022 | 103 | MLB | OPPO_LD | 13 |
| 2022 | 103 | MLB | OPPO_OFFB | 46 |
| 2022 | 103 | MLB | PULL_GB | 90 |
| 2022 | 103 | MLB | PULL_LD | 44 |
| 2022 | 103 | MLB | PULL_OFFB | 42 |
| 2023 | 103 | MLB | CENTER_GB | 17 |
| 2023 | 103 | MLB | CENTER_LD | 19 |
| 2023 | 103 | MLB | CENTER_OFFB | 55 |
| 2023 | 103 | MLB | IFFB | 13 |
| 2023 | 103 | MLB | OPPO_GB | 4 |
| 2023 | 103 | MLB | OPPO_LD | 8 |
| 2023 | 103 | MLB | OPPO_OFFB | 24 |
| 2023 | 103 | MLB | PULL_GB | 52 |
| 2023 | 103 | MLB | PULL_LD | 27 |
| 2023 | 103 | MLB | PULL_OFFB | 17 |
| 2024 | 103 | MLB | CENTER_GB | 38 |
| 2024 | 103 | MLB | CENTER_LD | 43 |
| 2024 | 103 | MLB | CENTER_OFFB | 75 |
| 2024 | 103 | MLB | IFFB | 11 |
| 2024 | 103 | MLB | OPPO_GB | 17 |
| 2024 | 103 | MLB | OPPO_LD | 14 |
| 2024 | 103 | MLB | OPPO_OFFB | 43 |
| 2024 | 103 | MLB | PULL_GB | 67 |
| 2024 | 103 | MLB | PULL_LD | 44 |
| 2024 | 103 | MLB | PULL_OFFB | 29 |

Old detailed source history (minor-only): [].

Origin-only peers: Nick Castellanos (MLB/AAA/AA PA 659/0.0/0.0; old contacts None; universal MLB/minor shapes 462/0); Matt Chapman (MLB/AAA/AA PA 647/0.0/0.0; old contacts None; universal MLB/minor shapes 398/0); Matt Olson (MLB/AAA/AA PA 685/0.0/0.0; old contacts None; universal MLB/minor shapes 423/0).

No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.

## Masyn Winn: origin 2023

Old detailed features summarize 353 minor contacts, with primary label AAA, 97.17% matched prior opponent context and complete park-feature coverage. They are not his 95 MLB shape contacts. The universal shape source preserves both 353 minor and 95 MLB contacts separately, and retains actual league identity for earlier A/High-A/AA exposure. The old contact probabilities pool minor levels with source-bin priors, while overall shares originate in a separate annual surface. Do not interpret his successful player/year join as a current MLB contact profile.

| Year | Actual league bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 2 | 40 | 6 |
| 2022 | AA | 403 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 2 | 26 | 10 |

Actual source-to-input join: {'age': 21.0, 'stage': 'Current MLB', 'source_position': '6', 'pa_0': 137, 'AAA_0_pa': 498.0, 'AA_0_pa': 0.0, 'draft_known': 1, 'pick_number': 54, 'legacy_contact_level': 'aaa', 'materialized_contacts': 353, 'opponent_context_known_rate': 0.9716713881019831, 'park_factor_known_rate': 1.0, 'shape_all': 448, 'shape_mlb': 95, 'shape_minor': 353}.

| Shape year | Actual league ID | Source level | Bin | Observations |
|---|---:|---|---|---:|
| 2021 | 118 | a+ | CENTER_GB | 18 |
| 2021 | 118 | a+ | CENTER_LD | 10 |
| 2021 | 118 | a+ | CENTER_OFFB | 9 |
| 2021 | 118 | a+ | IFFB | 6 |
| 2021 | 118 | a+ | OPPO_GB | 16 |
| 2021 | 118 | a+ | OPPO_LD | 4 |
| 2021 | 118 | a+ | OPPO_OFFB | 10 |
| 2021 | 118 | a+ | PULL_GB | 20 |
| 2021 | 118 | a+ | PULL_LD | 2 |
| 2021 | 118 | a+ | PULL_OFFB | 6 |
| 2021 | 123 | a | CENTER_GB | 22 |
| 2021 | 123 | a | CENTER_LD | 21 |
| 2021 | 123 | a | CENTER_OFFB | 20 |
| 2021 | 123 | a | IFFB | 14 |
| 2021 | 123 | a | OPPO_GB | 14 |
| 2021 | 123 | a | OPPO_LD | 13 |
| 2021 | 123 | a | OPPO_OFFB | 20 |
| 2021 | 123 | a | PULL_GB | 38 |
| 2021 | 123 | a | PULL_LD | 8 |
| 2021 | 123 | a | PULL_OFFB | 5 |
| 2022 | 109 | aa | CENTER_GB | 37 |
| 2022 | 109 | aa | CENTER_LD | 18 |
| 2022 | 109 | aa | CENTER_OFFB | 26 |
| 2022 | 109 | aa | IFFB | 24 |
| 2022 | 109 | aa | OPPO_GB | 14 |
| 2022 | 109 | aa | OPPO_LD | 13 |
| 2022 | 109 | aa | OPPO_OFFB | 25 |
| 2022 | 109 | aa | PULL_GB | 61 |
| 2022 | 109 | aa | PULL_LD | 15 |
| 2022 | 109 | aa | PULL_OFFB | 18 |
| 2022 | 118 | a+ | CENTER_GB | 16 |
| 2022 | 118 | a+ | CENTER_LD | 5 |
| 2022 | 118 | a+ | CENTER_OFFB | 18 |
| 2022 | 118 | a+ | IFFB | 5 |
| 2022 | 118 | a+ | OPPO_GB | 11 |
| 2022 | 118 | a+ | OPPO_LD | 2 |
| 2022 | 118 | a+ | OPPO_OFFB | 15 |
| 2022 | 118 | a+ | PULL_GB | 17 |
| 2022 | 118 | a+ | PULL_LD | 7 |
| 2022 | 118 | a+ | PULL_OFFB | 5 |
| 2023 | 104 | MLB | CENTER_GB | 14 |
| 2023 | 104 | MLB | CENTER_LD | 8 |
| 2023 | 104 | MLB | CENTER_OFFB | 12 |
| 2023 | 104 | MLB | IFFB | 7 |
| 2023 | 104 | MLB | OPPO_GB | 15 |
| 2023 | 104 | MLB | OPPO_LD | 6 |
| 2023 | 104 | MLB | OPPO_OFFB | 9 |
| 2023 | 104 | MLB | PULL_GB | 17 |
| 2023 | 104 | MLB | PULL_LD | 3 |
| 2023 | 104 | MLB | PULL_OFFB | 4 |
| 2023 | 117 | aaa | CENTER_GB | 61 |
| 2023 | 117 | aaa | CENTER_LD | 41 |
| 2023 | 117 | aaa | CENTER_OFFB | 52 |
| 2023 | 117 | aaa | IFFB | 21 |
| 2023 | 117 | aaa | OPPO_GB | 22 |
| 2023 | 117 | aaa | OPPO_LD | 18 |
| 2023 | 117 | aaa | OPPO_OFFB | 30 |
| 2023 | 117 | aaa | PULL_GB | 61 |
| 2023 | 117 | aaa | PULL_LD | 28 |
| 2023 | 117 | aaa | PULL_OFFB | 19 |

Old detailed source history (minor-only): [{'season': 2021, 'source_level': 'a', 'contacts': 275, 'materialized_contacts': 275, 'opponent_context_known_rate': 0.9490909090909091, 'park_factor_known_rate': 1.0, 'park_effect__hr': -0.09020787447995696, 'share__PULL_OFFB': 0.0441764676291564, 'contact_result__PULL_OFFB__HR': 0.31976833357390255}, {'season': 2022, 'source_level': 'aa', 'contacts': 352, 'materialized_contacts': 352, 'opponent_context_known_rate': 0.9715909090909091, 'park_factor_known_rate': 1.0, 'park_effect__hr': 0.04207327056624737, 'share__PULL_OFFB': 0.0686865305728846, 'contact_result__PULL_OFFB__HR': 0.32412388576770135}, {'season': 2023, 'source_level': 'aaa', 'contacts': 353, 'materialized_contacts': 353, 'opponent_context_known_rate': 0.9716713881019831, 'park_factor_known_rate': 1.0, 'park_effect__hr': -0.015101792947367257, 'share__PULL_OFFB': 0.05470136977127016, 'contact_result__PULL_OFFB__HR': 0.4494674011248467}].

Origin-only peers: Parker Meadows (MLB/AAA/AA PA 145/517.0/0.0; old contacts 328; universal MLB/minor shapes 85/327); Xavier Edwards (MLB/AAA/AA PA 84/433.0/0.0; old contacts 320; universal MLB/minor shapes 57/320); Jonathan Ornelas (MLB/AAA/AA PA 8/517.0/0.0; old contacts 295; universal MLB/minor shapes 3/297).

No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.

## Spencer Steer: origin 2022

Old contact features contain 330 minor contacts and strong context coverage, while universal shape contains 331 minor plus 65 MLB contacts. Small cross-source count differences are disclosed, not forced to reconcile through guessed events. His 492 upper-minor PA and 108 MLB PA remain separate in the primary backbone. Brennan/Henderson/Freeman also mix minor and MLB exposure; a new MLB-target test needs explicit league/source exposure rather than one primary-level label.

| Year | Actual league bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 10 | 32 | 35 |
| 2022 | AA | 156 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 2 | 26 | 11 |

Actual source-to-input join: {'age': 24.0, 'stage': 'Current MLB', 'source_position': '5', 'pa_0': 108, 'AAA_0_pa': 336.0, 'AA_0_pa': 156.0, 'draft_known': 1, 'pick_number': 90, 'legacy_contact_level': 'aaa', 'materialized_contacts': 330, 'opponent_context_known_rate': 0.990909090909091, 'park_factor_known_rate': 1.0, 'shape_all': 396, 'shape_mlb': 65, 'shape_minor': 331}.

| Shape year | Actual league ID | Source level | Bin | Observations |
|---|---:|---|---|---:|
| 2021 | 109 | aa | CENTER_GB | 17 |
| 2021 | 109 | aa | CENTER_LD | 15 |
| 2021 | 109 | aa | CENTER_OFFB | 30 |
| 2021 | 109 | aa | IFFB | 8 |
| 2021 | 109 | aa | OPPO_GB | 10 |
| 2021 | 109 | aa | OPPO_LD | 8 |
| 2021 | 109 | aa | OPPO_OFFB | 19 |
| 2021 | 109 | aa | PULL_GB | 36 |
| 2021 | 109 | aa | PULL_LD | 14 |
| 2021 | 109 | aa | PULL_OFFB | 20 |
| 2021 | 118 | a+ | CENTER_GB | 15 |
| 2021 | 118 | a+ | CENTER_LD | 9 |
| 2021 | 118 | a+ | CENTER_OFFB | 23 |
| 2021 | 118 | a+ | IFFB | 12 |
| 2021 | 118 | a+ | OPPO_GB | 6 |
| 2021 | 118 | a+ | OPPO_LD | 5 |
| 2021 | 118 | a+ | OPPO_OFFB | 16 |
| 2021 | 118 | a+ | PULL_GB | 14 |
| 2021 | 118 | a+ | PULL_LD | 11 |
| 2021 | 118 | a+ | PULL_OFFB | 20 |
| 2022 | 104 | MLB | CENTER_GB | 13 |
| 2022 | 104 | MLB | CENTER_LD | 5 |
| 2022 | 104 | MLB | CENTER_OFFB | 9 |
| 2022 | 104 | MLB | IFFB | 3 |
| 2022 | 104 | MLB | OPPO_GB | 2 |
| 2022 | 104 | MLB | OPPO_LD | 3 |
| 2022 | 104 | MLB | OPPO_OFFB | 5 |
| 2022 | 104 | MLB | PULL_GB | 15 |
| 2022 | 104 | MLB | PULL_LD | 7 |
| 2022 | 104 | MLB | PULL_OFFB | 3 |
| 2022 | 109 | aa | CENTER_GB | 15 |
| 2022 | 109 | aa | CENTER_LD | 11 |
| 2022 | 109 | aa | CENTER_OFFB | 14 |
| 2022 | 109 | aa | IFFB | 6 |
| 2022 | 109 | aa | OPPO_GB | 3 |
| 2022 | 109 | aa | OPPO_LD | 9 |
| 2022 | 109 | aa | OPPO_OFFB | 11 |
| 2022 | 109 | aa | PULL_GB | 13 |
| 2022 | 109 | aa | PULL_LD | 10 |
| 2022 | 109 | aa | PULL_OFFB | 17 |
| 2022 | 117 | aaa | CENTER_GB | 39 |
| 2022 | 117 | aaa | CENTER_LD | 14 |
| 2022 | 117 | aaa | CENTER_OFFB | 34 |
| 2022 | 117 | aaa | IFFB | 12 |
| 2022 | 117 | aaa | OPPO_GB | 12 |
| 2022 | 117 | aaa | OPPO_LD | 12 |
| 2022 | 117 | aaa | OPPO_OFFB | 15 |
| 2022 | 117 | aaa | PULL_GB | 50 |
| 2022 | 117 | aaa | PULL_LD | 14 |
| 2022 | 117 | aaa | PULL_OFFB | 20 |

Old detailed source history (minor-only): [{'season': 2021, 'source_level': 'aa', 'contacts': 308, 'materialized_contacts': 308, 'opponent_context_known_rate': 0.9837662337662337, 'park_factor_known_rate': 0.9448051948051948, 'park_effect__hr': -0.009015447658217442, 'share__PULL_OFFB': 0.11503974846330171, 'contact_result__PULL_OFFB__HR': 0.3297773859510229}, {'season': 2022, 'source_level': 'aaa', 'contacts': 330, 'materialized_contacts': 330, 'opponent_context_known_rate': 0.990909090909091, 'park_factor_known_rate': 1.0, 'park_effect__hr': 0.03603022589049689, 'share__PULL_OFFB': 0.10115482195238568, 'contact_result__PULL_OFFB__HR': 0.3423749865384712}].

Origin-only peers: Will Brennan (MLB/AAA/AA PA 45/433.0/157.0; old contacts 453; universal MLB/minor shapes 38/455); Gunnar Henderson (MLB/AAA/AA PA 132/295.0/208.0; old contacts 291; universal MLB/minor shapes 78/291); Tyler Freeman (MLB/AAA/AA PA 86/343.0/0.0; old contacts 259; universal MLB/minor shapes 64/259).

No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.

## Nick Kurtz: origin 2024

Both contact sources have 27 minor contacts and no MLB observations. The old annual primary label is A, although the broad backbone includes a 15-PA AA finish too. A small-sample per-bin probability such as pulled-fly HR 0.2769 is mostly the pooled prior, not an observed 28% MLB homer probability. Johnson/Montgomery/Jenkins have very different contact sample sizes despite similar age/pedigree/AA exposure. No source or model result here proves rapid MLB arrival.

| Year | Actual league bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Actual source-to-input join: {'age': 21.0, 'stage': 'Upper minors', 'source_position': '3', 'pa_0': 0, 'AAA_0_pa': 0.0, 'AA_0_pa': 15.0, 'draft_known': 1, 'pick_number': 4, 'legacy_contact_level': 'a', 'materialized_contacts': 27, 'opponent_context_known_rate': 1.0, 'park_factor_known_rate': 1.0, 'shape_all': 27, 'shape_mlb': 0, 'shape_minor': 27}.

| Shape year | Actual league ID | Source level | Bin | Observations |
|---|---:|---|---|---:|
| 2024 | 109 | aa | CENTER_GB | 3 |
| 2024 | 109 | aa | CENTER_LD | 1 |
| 2024 | 109 | aa | OPPO_LD | 2 |
| 2024 | 109 | aa | PULL_GB | 4 |
| 2024 | 110 | a | CENTER_GB | 3 |
| 2024 | 110 | a | CENTER_LD | 3 |
| 2024 | 110 | a | CENTER_OFFB | 1 |
| 2024 | 110 | a | OPPO_LD | 1 |
| 2024 | 110 | a | OPPO_OFFB | 2 |
| 2024 | 110 | a | PULL_GB | 4 |
| 2024 | 110 | a | PULL_LD | 1 |
| 2024 | 110 | a | PULL_OFFB | 2 |

Old detailed source history (minor-only): [{'season': 2024, 'source_level': 'a', 'contacts': 27, 'materialized_contacts': 27, 'opponent_context_known_rate': 1.0, 'park_factor_known_rate': 1.0, 'park_effect__hr': -0.02622608010571676, 'share__PULL_OFFB': 0.06047151069651452, 'contact_result__PULL_OFFB__HR': 0.27685302738201595}].

Origin-only peers: Termarr Johnson (MLB/AAA/AA PA 0/0.0/57.0; old contacts 324; universal MLB/minor shapes 0/324); Benny Montgomery (MLB/AAA/AA PA 0/0.0/48.0; old contacts 26; universal MLB/minor shapes 0/26); Walker Jenkins (MLB/AAA/AA PA 0/0.0/28.0; old contacts 245; universal MLB/minor shapes 0/245).

No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.

## Gavin Lux: origin 2023

Current contact joins are absent after a missed season, but universal shape history retains 248 MLB plus 52 minor contacts in 2021 and 324 MLB in 2022. The old feature table retains only the 52-contact rehab/minor component. Thus an old-row join alone discards the much larger relevant major-league record. Plummer/Ciuffo/Craig similarly lack current evidence; source absence cannot by itself identify medical return versus exit.

| Year | Actual league bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 74 | 1 | 15 | 6 |
| 2021 | MLB | 381 | 7 | 83 | 38 |
| 2022 | MLB | 471 | 6 | 95 | 47 |

Actual source-to-input join: {'age': 25.0, 'stage': 'Inactive / unknown', 'source_position': '4', 'pa_0': 0, 'AAA_0_pa': 0.0, 'AA_0_pa': 0.0, 'draft_known': 1, 'pick_number': 20, 'legacy_contact_level': None, 'materialized_contacts': None, 'opponent_context_known_rate': None, 'park_factor_known_rate': None, 'shape_all': None, 'shape_mlb': None, 'shape_minor': None}.

| Shape year | Actual league ID | Source level | Bin | Observations |
|---|---:|---|---|---:|
| 2021 | 104 | MLB | CENTER_GB | 47 |
| 2021 | 104 | MLB | CENTER_LD | 30 |
| 2021 | 104 | MLB | CENTER_OFFB | 27 |
| 2021 | 104 | MLB | IFFB | 12 |
| 2021 | 104 | MLB | OPPO_GB | 10 |
| 2021 | 104 | MLB | OPPO_LD | 13 |
| 2021 | 104 | MLB | OPPO_OFFB | 14 |
| 2021 | 104 | MLB | PULL_GB | 62 |
| 2021 | 104 | MLB | PULL_LD | 20 |
| 2021 | 104 | MLB | PULL_OFFB | 13 |
| 2021 | 112 | aaa | CENTER_GB | 11 |
| 2021 | 112 | aaa | CENTER_LD | 9 |
| 2021 | 112 | aaa | CENTER_OFFB | 4 |
| 2021 | 112 | aaa | IFFB | 1 |
| 2021 | 112 | aaa | OPPO_GB | 1 |
| 2021 | 112 | aaa | OPPO_LD | 2 |
| 2021 | 112 | aaa | OPPO_OFFB | 2 |
| 2021 | 112 | aaa | PULL_GB | 15 |
| 2021 | 112 | aaa | PULL_LD | 5 |
| 2021 | 112 | aaa | PULL_OFFB | 2 |
| 2022 | 104 | MLB | CENTER_GB | 50 |
| 2022 | 104 | MLB | CENTER_LD | 25 |
| 2022 | 104 | MLB | CENTER_OFFB | 34 |
| 2022 | 104 | MLB | IFFB | 10 |
| 2022 | 104 | MLB | OPPO_GB | 16 |
| 2022 | 104 | MLB | OPPO_LD | 19 |
| 2022 | 104 | MLB | OPPO_OFFB | 25 |
| 2022 | 104 | MLB | PULL_GB | 97 |
| 2022 | 104 | MLB | PULL_LD | 35 |
| 2022 | 104 | MLB | PULL_OFFB | 13 |

Old detailed source history (minor-only): [{'season': 2021, 'source_level': 'aaa', 'contacts': 52, 'materialized_contacts': 52, 'opponent_context_known_rate': 1.0, 'park_factor_known_rate': 1.0, 'park_effect__hr': -0.02855342422300036, 'share__PULL_OFFB': 0.05918702361840297, 'contact_result__PULL_OFFB__HR': 0.3522514533451572}].

Origin-only peers: Nick Plummer (MLB/AAA/AA PA 0/0.0/0.0; old contacts None; universal MLB/minor shapes None/None); Nick Ciuffo (MLB/AAA/AA PA 0/0.0/0.0; old contacts None; universal MLB/minor shapes None/None); Will Craig (MLB/AAA/AA PA 0/0.0/0.0; old contacts None; universal MLB/minor shapes None/None).

No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.

## Chase Meidroth: origin 2024

The old feature table has 369 materialized contacts but its annual surface says 367; the universal shape total is 369 minor contacts. Prior opponent context is known for 97.02% and park context for 99.46%, with mean HR park effect −0.0082. Detailed probabilities are raw contact-cell counts shrunk toward source-level priors; park/opponent values are separate covariates, not direct fully neutralized player results. This is reusable measurement/context, but the old positive next-year minor-contact score does not establish future MLB batting or opportunity. Caissie/Peters/Lavigne provide comparable source rows without target-based selection.

| Year | Actual league bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | A | 85 | 4 | 9 | 12 |
| 2022 | RK124 | 11 | 0 | 2 | 2 |
| 2023 | AA | 396 | 7 | 78 | 59 |
| 2023 | Aplus | 97 | 2 | 20 | 21 |
| 2024 | AAA | 558 | 7 | 71 | 105 |

Actual source-to-input join: {'age': 22.0, 'stage': 'Upper minors', 'source_position': '6', 'pa_0': 0, 'AAA_0_pa': 558.0, 'AA_0_pa': 0.0, 'draft_known': 1, 'pick_number': 129, 'legacy_contact_level': 'aaa', 'materialized_contacts': 369, 'opponent_context_known_rate': 0.9701897018970189, 'park_factor_known_rate': 0.994579945799458, 'shape_all': 369, 'shape_mlb': 0, 'shape_minor': 369}.

| Shape year | Actual league ID | Source level | Bin | Observations |
|---|---:|---|---|---:|
| 2022 | 122 | a | CENTER_GB | 10 |
| 2022 | 122 | a | CENTER_LD | 7 |
| 2022 | 122 | a | CENTER_OFFB | 8 |
| 2022 | 122 | a | IFFB | 3 |
| 2022 | 122 | a | OPPO_GB | 5 |
| 2022 | 122 | a | OPPO_LD | 4 |
| 2022 | 122 | a | OPPO_OFFB | 8 |
| 2022 | 122 | a | PULL_GB | 7 |
| 2022 | 122 | a | PULL_LD | 7 |
| 2022 | 122 | a | PULL_OFFB | 1 |
| 2022 | 124 | rk | CENTER_LD | 1 |
| 2022 | 124 | rk | OPPO_OFFB | 1 |
| 2022 | 124 | rk | PULL_GB | 3 |
| 2023 | 113 | aa | CENTER_GB | 47 |
| 2023 | 113 | aa | CENTER_LD | 19 |
| 2023 | 113 | aa | CENTER_OFFB | 26 |
| 2023 | 113 | aa | IFFB | 9 |
| 2023 | 113 | aa | OPPO_GB | 33 |
| 2023 | 113 | aa | OPPO_LD | 18 |
| 2023 | 113 | aa | OPPO_OFFB | 28 |
| 2023 | 113 | aa | PULL_GB | 48 |
| 2023 | 113 | aa | PULL_LD | 4 |
| 2023 | 113 | aa | PULL_OFFB | 13 |
| 2023 | 116 | a+ | CENTER_GB | 14 |
| 2023 | 116 | a+ | CENTER_LD | 2 |
| 2023 | 116 | a+ | CENTER_OFFB | 7 |
| 2023 | 116 | a+ | IFFB | 2 |
| 2023 | 116 | a+ | OPPO_GB | 11 |
| 2023 | 116 | a+ | OPPO_LD | 5 |
| 2023 | 116 | a+ | OPPO_OFFB | 2 |
| 2023 | 116 | a+ | PULL_GB | 7 |
| 2023 | 116 | a+ | PULL_LD | 3 |
| 2023 | 116 | a+ | PULL_OFFB | 1 |
| 2024 | 117 | aaa | CENTER_GB | 58 |
| 2024 | 117 | aaa | CENTER_LD | 46 |
| 2024 | 117 | aaa | CENTER_OFFB | 35 |
| 2024 | 117 | aaa | IFFB | 15 |
| 2024 | 117 | aaa | OPPO_GB | 58 |
| 2024 | 117 | aaa | OPPO_LD | 26 |
| 2024 | 117 | aaa | OPPO_OFFB | 26 |
| 2024 | 117 | aaa | PULL_GB | 69 |
| 2024 | 117 | aaa | PULL_LD | 23 |
| 2024 | 117 | aaa | PULL_OFFB | 13 |

Old detailed source history (minor-only): [{'season': 2022, 'source_level': 'a', 'contacts': 65, 'materialized_contacts': 65, 'opponent_context_known_rate': 0.8615384615384616, 'park_factor_known_rate': 1.0, 'park_effect__hr': 0.004069143500273686, 'share__PULL_OFFB': 0.042301833723597033, 'contact_result__PULL_OFFB__HR': 0.28655822367680284}, {'season': 2023, 'source_level': 'aa', 'contacts': 299, 'materialized_contacts': 299, 'opponent_context_known_rate': 0.9665551839464883, 'park_factor_known_rate': 1.0, 'park_effect__hr': 0.036240037809940846, 'share__PULL_OFFB': 0.05250005231173008, 'contact_result__PULL_OFFB__HR': 0.32414308014614485}, {'season': 2024, 'source_level': 'aaa', 'contacts': 367, 'materialized_contacts': 369, 'opponent_context_known_rate': 0.9701897018970189, 'park_factor_known_rate': 0.994579945799458, 'park_effect__hr': -0.008215194378186495, 'share__PULL_OFFB': 0.04059408757232279, 'contact_result__PULL_OFFB__HR': 0.4003279249637019}].

Origin-only peers: Owen Caissie (MLB/AAA/AA PA 0/549.0/0.0; old contacts 306; universal MLB/minor shapes 0/305); Tristan Peters (MLB/AAA/AA PA 0/478.0/0.0; old contacts 301; universal MLB/minor shapes 0/301); Grant Lavigne (MLB/AAA/AA PA 0/530.0/0.0; old contacts 292; universal MLB/minor shapes 0/292).

No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.

## Cody Bellinger: origin 2016

The broad backbone knows 465 AA PA/23 HR and a twelve-PA AAA finish, but the inspected contact tables begin in 2021. Neither supplies a 2016 shape profile or a validated MLB-arrival forecast. Westbrook/Wong/Kiner-Falefa have the same missing-source limitation. Treating these nulls as neutral skill would be an error; source reconstruction is required before a claim of decade-wide contact testing.

| Year | Actual league bucket | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

Actual source-to-input join: {'age': 20.0, 'stage': 'Upper minors', 'source_position': '3', 'pa_0': 0, 'AAA_0_pa': 12.0, 'AA_0_pa': 465.0, 'draft_known': 1, 'pick_number': 124, 'legacy_contact_level': None, 'materialized_contacts': None, 'opponent_context_known_rate': None, 'park_factor_known_rate': None, 'shape_all': None, 'shape_mlb': None, 'shape_minor': None}.

| Shape year | Actual league ID | Source level | Bin | Observations |
|---|---:|---|---|---:|

Old detailed source history (minor-only): [].

Origin-only peers: Isiah Kiner-Falefa (MLB/AAA/AA PA 0/0.0/457.0; old contacts None; universal MLB/minor shapes None/None); Jamie Westbrook (MLB/AAA/AA PA 0/0.0/473.0; old contacts None; universal MLB/minor shapes None/None); Kean Wong (MLB/AAA/AA PA 0/0.0/492.0; old contacts None; universal MLB/minor shapes None/None).

No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.

## Source disposition

Re-use canonical raw measurements only after a new MLB-target assembly with separate league/evidence reliability, proper earlier-source coverage and whole-player/time learning. Do not import the old fitted contact forecast weights as certified MLB talent. Current inputs cannot support a decade-wide contact claim. Universal shape supplies otherwise missing MLB records for the supported 2021–24 source years; earlier sources must be materialized or forecasts remain exact baseline fallback with explicit unsupported labels. A failed transfer coverage check is not a negative contact-model experiment.
