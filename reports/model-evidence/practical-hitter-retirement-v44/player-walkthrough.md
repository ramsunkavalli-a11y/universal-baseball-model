# Dated retirement repair player review

Review all fourteen reported-retirement rows plus three fixed unchanged cases. These are following-calendar-year MLB workload and batting-plus-replacement targets, not full WAR. No fitted parameters change. All original inputs and old forecasts are saved; the policy affects delivered opportunity, not estimated hitting talent. Comparisons are selected by same origin and stage, then age/workload/quality distance, without using later outcomes.

## David Ortiz 2016 to 2017

Player 120074, row 22760; all reported-retired states; age 40.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2014 | MLB | 602 | 35 | 95 | 53 |
| 2015 | MLB | 614 | 37 | 95 | 61 |
| 2016 | MLB | 626 | 38 | 86 | 65 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 293137, 'player_id': 120074, 'known_date': '2016-11-15', 'event_date': '2016-11-15', 'kind': 'retired', 'type_code': 'RET', 'description': 'DH David Ortiz retired.', 'capture_year': 2016, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2016.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 336.588 | 0.000 | 2.36600 | 0.00000 | 2.36476 |
| cohort | 336.588 | 0.000 | 2.36600 | 0.00000 | 2.36476 |
| games | 365.615 | 0.000 | 2.57004 | 0.00000 | 2.36476 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Ortiz's 626 PA and 38 HR in the final season reasonably support positive batting talent, but the November retirement is separately known by cutoff. The policy removes 337 expected PA and 2.366 batting-plus-replacement wins, leaving the 2.365 batting-wins/600 estimate intact. Actual next PA/value are zero. Origin-selected Beltran, Beltre and Martinez continue to receive forecasts: old age itself is not the retirement rule. The raw event is November 15, whereas the confirming public MLB article is November 16; both precede this December cutoff, but they are not falsely called identical publication dates.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Carlos Beltrán | 39.0 | 593 | 479.02 to 479.02 | 509 | 0.0358 |
| Adrian Beltré | 37.0 | 640 | 474.11 to 474.11 | 389 | 3.3126 |
| Victor Martinez | 37.0 | 610 | 472.99 to 472.99 | 435 | 0.7256 |

## Michael Taylor 2016 to 2017

Player 446345, row 22906; all reported-retired states; age 30.0, stage Inactive / unknown. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2014 | AAA | 512 | 11 | 100 | 60 |
| 2014 | MLB | 33 | 0 | 9 | 5 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 216969, 'player_id': 446345, 'known_date': '2015-03-11', 'event_date': '2015-03-11', 'kind': 'retired', 'type_code': 'RET', 'description': 'RF Michael Taylor retired.', 'capture_year': 2015, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source-2015\\captures\\transactions-2015.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 0.000 | 0.000 | 0.00000 | 0.00000 | -0.46981 |
| cohort | 0.000 | 0.000 | 0.00000 | 0.00000 | -0.46981 |
| games | 3.380 | 0.000 | 0.00779 | 0.00000 | -0.46981 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

This is Michael Taylor, player 446345, not Michael A. Taylor. The actual recent history is 512 AAA PA plus 33 MLB PA in 2014, with the retirement recorded in March 2015. The working forecast already clips to zero; the games model's residual 3.38 PA is removed. This row illustrates that explicit retirement adds a meaningful status label even where regression accidentally reaches the right zero. Canzler, Sellers and Marson remain ordinary unknown/low-opportunity forecasts without being falsely labeled retired.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Russ Canzler | 30.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |
| Justin Sellers | 30.0 | 0 | 1.60 to 1.60 | 0 | 0.0000 |
| Lou Marson | 30.0 | 0 | 2.92 to 2.92 | 0 | 0.0000 |

## Mike Marjama 2018 to 2019

Player 605357, row 32923; all reported-retired states; age 28.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 307 | 5 | 46 | 19 |
| 2017 | AAA | 378 | 12 | 68 | 28 |
| 2017 | MLB | 9 | 1 | 1 | 0 |
| 2018 | AAA | 173 | 5 | 35 | 11 |
| 2018 | MLB | 29 | 0 | 6 | 2 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 366998, 'player_id': 605357, 'known_date': '2018-07-06', 'event_date': '2018-07-06', 'kind': 'retired', 'type_code': 'RET', 'description': 'C Mike Marjama retired.', 'capture_year': 2018, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2018.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 24.675 | 0.000 | 0.01890 | 0.00000 | -1.38773 |
| cohort | 24.675 | 0.000 | 0.01890 | 0.00000 | -1.38773 |
| games | 28.084 | 0.000 | 0.02151 | 0.00000 | -1.38773 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Marjama has 378 AAA and nine MLB PA in 2017, then 173 AAA and 29 MLB PA in 2018, with a July 2018 retirement transaction. The working 24.67 PA and 0.0189 contribution are removed, not his hitting-rate estimate. Actual is zero. Susac, Orf and Motter are origin-selected brief-appearance peers and also have zero subsequent PA, but the absence of their RET state prevents using that future outcome to create a rule for them.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Andrew Susac | 28.0 | 26 | 108.23 to 108.23 | 0 | 0.0000 |
| Nate Orf | 28.0 | 25 | 31.67 to 31.67 | 0 | 0.0000 |
| Taylor Motter | 28.0 | 38 | 39.10 to 39.10 | 0 | 0.0000 |

## Albert Pujols 2021 to 2022

Player 405395, row 42072; fixed unchanged counterexample; age 41.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2019 | MLB | 545 | 23 | 68 | 42 |
| 2020 | MLB | 163 | 6 | 25 | 8 |
| 2021 | MLB | 296 | 17 | 45 | 11 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': False, 'retirement': None, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 43.149 | 43.149 | 0.05446 | 0.05446 | -1.12375 |
| cohort | 64.331 | 64.331 | 0.10183 | 0.10183 | -0.93123 |
| games | 52.756 | 52.756 | 0.08351 | 0.08351 | -0.93123 |
| Actual | 351 | 351 | 3.09171 | 3.09171 | 3.4063842632657733 |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Pujols still has 296 MLB PA and 17 HR at this origin, with no eligible recorded retirement. His poor working forecast of 43 PA remains unchanged against 351 actual and 3.092 contribution wins. A retirement policy must not misclassify a merely old or released player, even though leaving him unchanged preserves a large error. Cruz, Molina and Cabrera demonstrate that age-38-plus hitters can still receive substantial next-year playing time.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Nelson Cruz | 40.0 | 584 | 284.06 to 284.06 | 507 | 0.8363 |
| Yadier Molina | 38.0 | 473 | 315.13 to 315.13 | 270 | -0.7961 |
| Miguel Cabrera | 38.0 | 526 | 327.02 to 327.02 | 433 | 0.1539 |

## Buster Posey 2021 to 2022

Player 457763, row 42101; all reported-retired states; age 34.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2019 | MLB | 445 | 7 | 71 | 33 |
| 2021 | MLB | 454 | 18 | 87 | 51 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 523268, 'player_id': 457763, 'known_date': '2021-11-04', 'event_date': '2021-11-04', 'kind': 'retired', 'type_code': 'RET', 'description': 'C Buster Posey retired.', 'capture_year': 2021, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2021.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 256.404 | 0.000 | 0.72717 | 0.00000 | -0.17939 |
| cohort | 263.000 | 0.000 | 0.78926 | 0.00000 | -0.08042 |
| games | 286.012 | 0.000 | 0.85832 | 0.00000 | -0.08042 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Posey returned from the canceled/opt-out year to 454 MLB PA and 18 HR in 2021, then has an explicit November 4 retirement. Remove 256 expected PA and 0.727 contribution while preserving the batting estimate. The separate 2020-origin source check shows no retirement then; absence and restricted-list opt-out are not retirement. Brantley, Crawford and Pollock retain forecasts. This is a cutoff-known availability correction, not a prediction of his personal decision from batting statistics.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Michael Brantley | 34.0 | 508 | 418.17 to 418.17 | 277 | 1.6470 |
| Brandon Crawford | 34.0 | 549 | 372.64 to 372.64 | 458 | 0.6581 |
| AJ Pollock | 33.0 | 422 | 409.76 to 409.76 | 527 | 1.1722 |

## Jay Bruce 2021 to 2022

Player 457803, row 42102; all reported-retired states; age 34.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2019 | AA | 8 | 0 | 4 | 0 |
| 2019 | MLB | 333 | 26 | 82 | 19 |
| 2020 | MLB | 103 | 6 | 24 | 6 |
| 2021 | MLB | 39 | 1 | 13 | 5 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 478836, 'player_id': 457803, 'known_date': '2021-04-18', 'event_date': '2021-04-18', 'kind': 'retired', 'type_code': 'RET', 'description': 'RF Jay Bruce retired.', 'capture_year': 2021, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2021.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 0.041 | 0.000 | 0.00005 | 0.00000 | -1.08535 |
| cohort | 7.771 | 0.000 | 0.01136 | 0.00000 | -1.00361 |
| games | 15.169 | 0.000 | 0.02218 | 0.00000 | -1.00361 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Bruce's 39 MLB PA in 2021 follow 333 in 2019 and 103 in shortened 2020; April retirement is directly recorded. The working forecast was already virtually zero, while the games forecast assigned 15 PA. The rule removes that remnant. Maybin, Campbell and Sandoval have similarly small origin workload and zero later MLB PA, but future zero participation is not evidence they were already retired at this cutoff.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Cameron Maybin | 34.0 | 33 | 6.94 to 6.94 | 0 | 0.0000 |
| Eric Campbell | 34.0 | 12 | 11.34 to 11.34 | 0 | 0.0000 |
| Pablo Sandoval | 34.0 | 86 | 4.32 to 4.32 | 0 | 0.0000 |

## Mike Marjama 2021 to 2022

Player 605357, row 42478; all reported-retired states; age 31.0, stage Inactive / unknown. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| No own observed batting within window | Unknown | — | — | — | — |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 366998, 'player_id': 605357, 'known_date': '2018-07-06', 'event_date': '2018-07-06', 'kind': 'retired', 'type_code': 'RET', 'description': 'C Mike Marjama retired.', 'capture_year': 2018, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2018.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 0.000 | 0.000 | 0.00000 | 0.00000 | -1.20583 |
| cohort | 0.000 | 0.000 | 0.00000 | 0.00000 | -1.27340 |
| games | 0.000 | 0.000 | 0.00000 | 0.00000 | -1.27340 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Marjama's 2018 retirement remains unreversed and there are no own batting rows in the three-year input window. Both working and games forecasts are already zero, so this is a status correction without an incremental forecast gain. The retained negative batting-rate estimate is not a claim that retirement caused poor ability. Unknown inactive comparison players remain distinct from confirmed retirement.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Jabari Blash | 31.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |
| Isaac Galloway | 31.0 | 0 | 7.70 to 7.70 | 0 | 0.0000 |
| Destin Hood | 31.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |

## Nate Orf 2021 to 2022

Player 644337, row 42835; all reported-retired states; age 31.0, stage Inactive / unknown. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 499 | 11 | 74 | 64 |
| 2020 | MLB | 7 | 0 | 1 | 0 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 469744, 'player_id': 644337, 'known_date': '2021-02-16', 'event_date': '2021-02-16', 'kind': 'retired', 'type_code': 'RET', 'description': '2B Nate Orf retired.', 'capture_year': 2021, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2021.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 1.981 | 0.000 | 0.00179 | 0.00000 | -1.33955 |
| cohort | 0.699 | 0.000 | 0.00057 | 0.00000 | -1.38920 |
| games | 0.611 | 0.000 | 0.00050 | 0.00000 | -1.38920 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Orf's source has 499 AAA PA in 2019 and seven MLB PA in shortened 2020, then a February 2021 retirement. The working 1.98 PA and games 0.61 PA are removed; actual is zero. This small change is sensible but cannot explain the material public workload gap or validate any general injury/absence penalty. The status derives from the transaction, not from his peers' later non-arrivals.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Jabari Blash | 31.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |
| Isaac Galloway | 31.0 | 0 | 7.70 to 7.70 | 0 | 0.0000 |
| Destin Hood | 31.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |

## Albert Pujols 2022 to 2023

Player 405395, row 46314; all reported-retired states; age 42.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 163 | 6 | 25 | 8 |
| 2021 | MLB | 296 | 17 | 45 | 11 |
| 2022 | MLB | 351 | 24 | 55 | 27 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 657520, 'player_id': 405395, 'known_date': '2022-11-01', 'event_date': '2022-11-01', 'kind': 'retired', 'type_code': 'RET', 'description': '1B Albert Pujols retired.', 'capture_year': 2022, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2022.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 156.687 | 0.000 | 0.38010 | 0.00000 | -0.42308 |
| cohort | 160.570 | 0.000 | 0.43266 | 0.00000 | -0.26187 |
| games | 128.356 | 0.000 | 0.34586 | 0.00000 | -0.26187 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Pujols' 351 PA and 24 HR in 2022 remain in the talent inputs. A November 1 retirement now changes availability, unlike his 2021-origin case. The working 157 PA and 0.380 contribution go to zero against actual zero. The comparison rule selects Cruz and Cabrera, who actually continue playing, alongside fellow retired Molina. Do not replace this temporal evidence with a blanket old-age suppression.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Nelson Cruz | 41.0 | 507 | 133.77 to 133.77 | 152 | 0.1194 |
| Miguel Cabrera | 39.0 | 433 | 291.06 to 291.06 | 370 | 0.6040 |
| Yadier Molina | 39.0 | 270 | 30.73 to 0.00 | 0 | 0.0000 |

## Yadier Molina 2022 to 2023

Player 425877, row 46316; all reported-retired states; age 39.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 156 | 4 | 21 | 6 |
| 2021 | MLB | 473 | 11 | 79 | 23 |
| 2022 | AAA | 7 | 0 | 0 | 1 |
| 2022 | MLB | 270 | 5 | 40 | 5 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 657521, 'player_id': 425877, 'known_date': '2022-11-01', 'event_date': '2022-11-01', 'kind': 'retired', 'type_code': 'RET', 'description': 'C Yadier Molina retired.', 'capture_year': 2022, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2022.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 30.725 | 0.000 | -0.02650 | 0.00000 | -2.39603 |
| cohort | 23.759 | 0.000 | -0.01845 | 0.00000 | -2.34463 |
| games | 39.992 | 0.000 | -0.03106 | 0.00000 | -2.34463 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Molina has 473 MLB PA in 2021 and 270 plus seven AAA rehab PA in 2022; retirement is explicitly recorded November 1. Remove 30.73 expected PA and negative 0.0265 contribution. Retirement sets delivered contribution to zero even when the unplayed forecast would have been negative; it does not change the -2.396 batting-wins/600 estimate into zero. Similar older players without eligible RET evidence remain unchanged despite later zero PA.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Robinson Chirinos | 38.0 | 220 | 38.31 to 38.31 | 0 | 0.0000 |
| Jed Lowrie | 38.0 | 184 | 28.40 to 28.40 | 0 | 0.0000 |
| Kurt Suzuki | 38.0 | 159 | 0.00 to 0.00 | 0 | 0.0000 |

## Mike Marjama 2022 to 2023

Player 605357, row 46618; all reported-retired states; age 32.0, stage Inactive / unknown. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| No own observed batting within window | Unknown | — | — | — | — |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 366998, 'player_id': 605357, 'known_date': '2018-07-06', 'event_date': '2018-07-06', 'kind': 'retired', 'type_code': 'RET', 'description': 'C Mike Marjama retired.', 'capture_year': 2018, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2018.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 0.000 | 0.000 | 0.00000 | 0.00000 | -1.46912 |
| cohort | 0.000 | 0.000 | 0.00000 | 0.00000 | -1.54151 |
| games | 0.000 | 0.000 | 0.00000 | 0.00000 | -1.54151 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

The same July 2018 retirement remains eligible and no later return transaction is recorded. His own three-year batting window is empty and both mean forecasts are already zero. This repeated season is not a new independent retirement success; count distinct people separately. The rule adds explicit status without improving this zero forecast.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Francisco Arcia | 32.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |
| Isaac Galloway | 32.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |
| A.J. Jimenez | 32.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |

## Nate Orf 2022 to 2023

Player 644337, row 46912; all reported-retired states; age 32.0, stage Inactive / unknown. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 7 | 0 | 1 | 0 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 469744, 'player_id': 644337, 'known_date': '2021-02-16', 'event_date': '2021-02-16', 'kind': 'retired', 'type_code': 'RET', 'description': '2B Nate Orf retired.', 'capture_year': 2021, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2021.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 1.326 | 0.000 | 0.00037 | 0.00000 | -1.71216 |
| cohort | 0.000 | 0.000 | 0.00000 | 0.00000 | -1.80813 |
| games | 0.174 | 0.000 | 0.00002 | 0.00000 | -1.80813 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Orf still has seven 2020 MLB PA in the window and the unreversed 2021 retirement. Remove the working 1.33 PA and games 0.17 PA, with zero actual next participation. This is the same retired person observed again, not a new example validating the return probability. No inferred recovery or foreign-production estimate is inserted.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Francisco Arcia | 32.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |
| Isaac Galloway | 32.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |
| A.J. Jimenez | 32.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |

## Nate Orf 2023 to 2024

Player 644337, row 51024; all reported-retired states; age 33.0, stage Inactive / unknown. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| No own observed batting within window | Unknown | — | — | — | — |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 469744, 'player_id': 644337, 'known_date': '2021-02-16', 'event_date': '2021-02-16', 'kind': 'retired', 'type_code': 'RET', 'description': '2B Nate Orf retired.', 'capture_year': 2021, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2021.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 0.000 | 0.000 | -0.00000 | 0.00000 | -1.88093 |
| cohort | 0.000 | 0.000 | -0.00000 | 0.00000 | -1.94244 |
| games | 0.396 | 0.000 | -0.00006 | 0.00000 | -1.94244 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Orf now has an empty own batting window and the same documented retirement. Working PA is already zero; only the games model's 0.40 PA remnant changes. Nearby inactive players include Nick Ramirez, whose pitcher role is a separate universe/role qualification and is not made retired by this rule. The age/workload peers explain context, not certified hitting similarity.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Isaac Galloway | 33.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |
| Nick Ramirez | 33.0 | 0 | 69.61 to 69.61 | 0 | 0.0000 |
| Matt Skole | 33.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |

## Charlie Blackmon 2024 to 2025

Player 453568, row 54755; all reported-retired states; age 37.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 577 | 16 | 109 | 28 |
| 2023 | AAA | 10 | 0 | 1 | 0 |
| 2023 | MLB | 413 | 8 | 55 | 39 |
| 2024 | MLB | 499 | 12 | 86 | 41 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 801175, 'player_id': 453568, 'known_date': '2024-10-01', 'event_date': '2024-10-01', 'kind': 'retired', 'type_code': 'RET', 'description': 'RF Charlie Blackmon retired.', 'capture_year': 2024, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2024.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 257.789 | 0.000 | 0.70274 | 0.00000 | -0.23888 |
| cohort | 240.998 | 0.000 | 0.67760 | 0.00000 | -0.18752 |
| games | 283.611 | 0.000 | 0.79741 | 0.00000 | -0.18752 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Blackmon's 577/413/499 MLB PA and 16/8/12 HR support a still-active statistical forecast until the October 1 retirement transaction is considered. Remove 258 working PA and 0.703 contribution. Actual is zero. McCutchen and Pham remain active forecasts and actually play; Martinez has zero later PA without a recorded retirement. The rule uses their actual origin state, not knowledge of who will disappear next year.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Andrew McCutchen | 37.0 | 515 | 348.90 to 348.90 | 551 | 1.4641 |
| J.D. Martinez | 36.0 | 495 | 248.77 to 248.77 | 0 | 0.0000 |
| Tommy Pham | 36.0 | 478 | 247.95 to 247.95 | 449 | 1.2131 |

## Aaron Judge 2024 to 2025

Player 592450, row 54849; fixed unchanged counterexample; age 32.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': False, 'retirement': None, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 534.275 | 534.275 | 5.67779 | 5.67779 | 4.50176 |
| cohort | 548.496 | 548.496 | 5.87607 | 5.87607 | 4.55334 |
| games | 547.389 | 547.389 | 5.86421 | 5.86421 | 4.55334 |
| Actual | 679 | 679 | 9.23105 | 9.23105 | 6.287431083532908 |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Judge's 704 MLB PA and 58 HR do not trigger any retirement state. Working 534 PA and 5.678 batting-plus-replacement wins remain bit-exact against 679 PA and 9.231 actual. This source repair does not cure elite talent/playing-time compression. Ozuna, Schwarber and Harper are origin-selected regular comparisons, not fitted retirement evidence.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Marcell Ozuna | 33.0 | 688 | 556.99 to 556.99 | 592 | 2.9170 |
| Kyle Schwarber | 31.0 | 692 | 600.08 to 600.08 | 724 | 6.8326 |
| Bryce Harper | 31.0 | 631 | 538.22 to 538.22 | 580 | 4.0183 |

## Alex Kirilloff 2024 to 2025

Player 666135, row 55338; all reported-retired states; age 26.0, stage Current MLB. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2022 | AAA | 157 | 10 | 26 | 22 |
| 2022 | MLB | 156 | 3 | 36 | 5 |
| 2023 | A | 15 | 1 | 3 | 3 |
| 2023 | AAA | 73 | 5 | 13 | 6 |
| 2023 | MLB | 319 | 11 | 80 | 27 |
| 2024 | AAA | 5 | 0 | 3 | 0 |
| 2024 | MLB | 178 | 5 | 47 | 15 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': True, 'retirement': {'transaction_id': 803310, 'player_id': 666135, 'known_date': '2024-10-31', 'event_date': '2024-10-31', 'kind': 'retired', 'type_code': 'RET', 'description': 'LF Alex Kirilloff retired.', 'capture_year': 2024, 'source_path': 'C:\\Users\\ramav\\Documents\\Codex\\2026-09-13\\wa\\work\\ubm-audit-v3\\reports\\generated\\hitter-injury-history-v2\\source\\captures\\transactions-2024.json'}, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 106.957 | 0.000 | 0.33328 | 0.00000 | -0.00490 |
| cohort | 101.029 | 0.000 | 0.30520 | 0.00000 | -0.06196 |
| games | 110.986 | 0.000 | 0.33528 | 0.00000 | -0.06196 |
| Actual | 0 | 0 | 0.00000 | 0.00000 | not observed at zero PA |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Kirilloff's 319 MLB PA in 2023 and 178 in 2024, with small AAA exposure, precede an October 31 retirement transaction at age 26. Remove 107 working PA and 0.333 contribution. Age alone would not justify this decision: Canzone and Jung, similarly aged partial-workload players, actually get 269 and 511 PA. Do not infer retirement from low durability or retrospectively label all injured young hitters unable to return.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Dominic Canzone | 26.0 | 188 | 176.33 to 176.33 | 269 | 1.9583 |
| Josh Jung | 26.0 | 188 | 296.69 to 296.69 | 511 | 1.0356 |
| Kyle McCann | 26.0 | 157 | 83.69 to 83.69 | 0 | 0.0000 |

## Nick Kurtz 2024 to 2025

Player 701762, row 57052; fixed unchanged counterexample; age 21.0, stage Upper minors. Origin evidence bridge True.

| Season | Level | PA | HR | K | BB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is {'reported_retired': False, 'retirement': None, 'return_evidence': None}.

| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |
|---|---:|---:|---:|---:|---:|
| safe_ridge | 50.494 | 50.494 | 0.14825 | 0.14825 | -0.11288 |
| cohort | 42.495 | 42.495 | 0.12316 | 0.12316 | -0.13556 |
| games | 29.943 | 29.943 | 0.08678 | 0.08678 | -0.13556 |
| Actual | 489 | 489 | 5.72099 | 5.72099 | 5.150009420178844 |

Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.

Kurtz's 35 A and 15 AA PA, age 21 and pick four remain exactly as before; there is no retirement evidence. Working 50.5 PA and 0.148 contribution stay far below 489 and 5.721 actual. The games candidate is also unchanged at 29.9 PA. Retirement context does not solve fast-entry prospect readiness, and the plain age/workload comparison rule here is not a substitute for scouting-quality prospect comparisons.

| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |
|---|---:|---:|---|---:|---:|
| Eduardo Garcia | 21.0 | 0 | 10.06 to 10.06 | 0 | 0.0000 |
| Eddinson Paulino | 21.0 | 0 | 24.19 to 24.19 | 0 | 0.0000 |
| David Calabrese | 21.0 | 0 | 0.00 to 0.00 | 0 | 0.0000 |

## Source and return limits

All fourteen flagged rows actually have zero following-year MLB PA, but they represent only ten people. That observed result is not proof retirement is irreversible or a calibrated zero comeback probability. Unit tests confirm a later eligible signing or retirement-list return clears the state and a backdated future event cannot affect an earlier forecast. Actual retirement-return pairs are not established by this small evaluated subset. The existing transaction captures have incomplete minor/foreign coverage and lack archived publication snapshots. Ortiz and Posey are independently cross-checked against dated primary announcements.

An opt-out, IL activation, release, free agency or mere roster page does not trigger this retirement policy. Unverified roster-only players stay in every original headline comparison and remain source-qualified.

Retain this reversible reported-retirement policy in the working research assembly. The public-matched workload error is unchanged; the practical hitter goal remains incomplete. Frozen 2026 and deployed forecasts remain unchanged.
