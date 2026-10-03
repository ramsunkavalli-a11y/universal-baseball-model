# Recorded open injury spells contradicted by later MLB use

This explains a defect in the completed status experiment. No new model is fitted and no forecast is replaced.
Compare only origin-known captured medical records and certified historical MLB windows, before reading future outcomes.
A positive PA window entirely after a spell begins disproves uninterrupted IL roster absence. It does not prove complete recovery.
An injury beginning during or after the window is not cleared from aggregate PA.
47 of 81 source open-spell rows and 44 of 72 evaluation open-spell rows meet the strict contradiction rule.
These are repeated player-origins, not independent people. Other rows are unresolved, not certified valid.
The rare-signal training counts and learned medical coefficients are therefore not clean evidence about actual current injury.

## Six actual source and forecast checks

### Yordan Alvarez at the 2022 cutoff

Captured entry 2022-07-10; late window 2022-09-06 to 2022-10-05: 100.0 PA.
Model open input 1; strict contradiction True.
Preserved expected PA 511.58; status forecast 488.81; next-year actual 496.
Appearance 98.86%, conditional PA 494.46, unchanged hitting rate 2.814 per 600 PA.

July 10 hand placement remains open after a July 21 reserve-list activation. The September 6 to October 5 window has 100 PA, proving a subsequent observed MLB return within that window. This does not prove complete health or an exact return date. An uninterrupted July-to-December IL spell is contradicted. The candidate open flag costs about twenty conditional PA, yet the resulting PA estimate is closer to actual; do not infer source correctness from that lucky result.

Actual source counts:
- 2020 MLB: 9 PA, 1 HR, 1 K.
- 2021 MLB: 598 PA, 33 HR, 145 K.
- 2022 MLB: 561 PA, 37 HR, 106 K.

Eligible captured records relevant to placement or return:
- Known 2022-07-10, occurred 2022-07-10: Houston Astros placed 1B Yordan Alvarez on the 10-day injured list. Right hand inflammation..
- Known 2022-07-21, occurred 2022-07-21: Houston Astros activated 1B Yordan Alvarez from the reserve list..

Actual saved participation output 4.460478; status terms: status_minor_contract +0.0035; status_log_absence730 +0.0023; status_offseason_activation +0.0019.

Actual saved conditional_pa output 494.455131; status terms: status_open_medical -20.1665; status_ordinary_departure +0.9661; status_log_absence730 +0.5056.

Origin-known open-spell comparisons, including unresolved cases:
- Eloy Jiménez: entry 2022-07-06, 99.0 late PA, contradiction True; projected 422.4 PA versus 489 actual.
- Randal Grichuk: entry 2022-03-30, 84.0 late PA, contradiction True; projected 412.3 PA versus 471 actual.
- Mike Trout: entry 2022-07-15, 105.0 late PA, contradiction True; projected 473.3 PA versus 362 actual.

### Nick Castellanos at the 2016 cutoff

Captured entry 2016-08-07; late window 2016-09-03 to 2016-10-02: 15.0 PA.
Model open input 1; strict contradiction True.
Preserved expected PA 499.13; status forecast 506.49; next-year actual 665.
Appearance 99.20%, conditional PA 510.55, unchanged hitting rate 0.854 per 600 PA.

An August 7 entry stays open despite 15 PA during the later September window. His captured open spell also persists into later source years. Lack of a named IL activation cannot outweigh actual MLB use as evidence against uninterrupted roster absence; it still does not certify the arm fully healed.

Actual source counts:
- 2014 MLB: 579 PA, 11 HR, 140 K.
- 2015 MLB: 595 PA, 15 HR, 152 K.
- 2016 MLB: 447 PA, 18 HR, 111 K.

Eligible captured records relevant to placement or return:
- Known 2016-08-07, occurred 2016-08-07: Detroit Tigers placed 3B Nick Castellanos on the 15-day disabled list. Fractured left hand..

Actual saved participation output 4.824941; status terms: none.

Actual saved conditional_pa output 510.554318; status terms: status_ordinary_departure +0.0314.

Origin-known open-spell comparisons, including unresolved cases:
- Aledmys Díaz: entry 2016-08-01, 59.0 late PA, contradiction True; projected 544.5 PA versus 301 actual.
- Domingo Santana: entry 2016-06-08, 101.0 late PA, contradiction True; projected 304.1 PA versus 607 actual.
- Maikel Franco: entry 2015-08-12, 101.0 late PA, contradiction True; projected 554.4 PA versus 623 actual.

### Maikel Franco at the 2016 cutoff

Captured entry 2015-08-12; late window 2016-09-03 to 2016-10-02: 101.0 PA.
Model open input 1; strict contradiction True.
Preserved expected PA 554.35; status forecast 554.35; next-year actual 623.
Appearance 97.77%, conditional PA 567.00, unchanged hitting rate 0.551 per 600 PA.

The reconstructed open entry starts August 12, 2015, yet 2016 late MLB usage is 101 PA. It also persists into 2017 and 2018 despite subsequent MLB appearances. This is a stale observation-state defect, not evidence of years of continuing roster absence. Do not train a medical penalty on it as current injury status.

Actual source counts:
- 2014 AAA: 556 PA, 16 HR, 81 K.
- 2014 MLB: 58 PA, 0 HR, 13 K.
- 2015 AAA: 151 PA, 4 HR, 25 K.
- 2015 MLB: 335 PA, 14 HR, 52 K.
- 2016 MLB: 630 PA, 25 HR, 106 K.

Eligible captured records relevant to placement or return:
- Known 2015-08-18, occurred 2015-08-12: Philadelphia Phillies placed 3B Maikel Franco on the 15-day disabled list retroactive to August 12, 2015. Non-displaced fracture of his left wrist.

Actual saved participation output 3.780311; status terms: none.

Actual saved conditional_pa output 566.998530; status terms: none.

Origin-known open-spell comparisons, including unresolved cases:
- Nick Castellanos: entry 2016-08-07, 15.0 late PA, contradiction True; projected 506.5 PA versus 665 actual.
- Aledmys Díaz: entry 2016-08-01, 59.0 late PA, contradiction True; projected 544.5 PA versus 301 actual.
- Domingo Santana: entry 2016-06-08, 101.0 late PA, contradiction True; projected 304.1 PA versus 607 actual.

### Jarrett Parker at the 2016 cutoff

Captured entry 2016-10-12; late window 2016-09-03 to 2016-10-02: 13.0 PA.
Model open input 1; strict contradiction False.
Preserved expected PA 131.11; status forecast 131.11; next-year actual 177.
Appearance 86.12%, conditional PA 152.24, unchanged hitting rate 0.157 per 600 PA.

October 12 entry occurs AFTER the September late-window start and after that window ends. Thirteen late PA cannot disprove this later injury. This control prevents a blanket rule that every player with any late PA is healthy or returned after a particular spell.

Actual source counts:
- 2014 AA: 419 PA, 12 HR, 103 K.
- 2014 AAA: 89 PA, 3 HR, 23 K.
- 2015 AAA: 504 PA, 23 HR, 164 K.
- 2015 MLB: 54 PA, 6 HR, 21 K.
- 2016 AAA: 222 PA, 16 HR, 66 K.
- 2016 MLB: 151 PA, 5 HR, 44 K.

Eligible captured records relevant to placement or return:
- Known 2016-10-12, occurred 2016-10-12: San Francisco Giants placed LF Jarrett Parker on the 10-day disabled list..

Actual saved participation output 1.825088; status terms: none.

Actual saved conditional_pa output 152.244135; status terms: none.

Origin-known open-spell comparisons, including unresolved cases:
- Mark Canha: entry 2016-05-09, 0.0 late PA, contradiction False; projected 137.8 PA versus 187 actual.
- Matt Adams: entry 2016-08-10, 49.0 late PA, contradiction True; projected 324.9 PA versus 367 actual.
- Preston Tucker: entry 2016-08-12, 0.0 late PA, contradiction False; projected 160.3 PA versus 0 actual.

### Kyle Garlick at the 2022 cutoff

Captured entry 2022-09-16; late window 2022-09-06 to 2022-10-05: 29.0 PA.
Model open input 1; strict contradiction False.
Preserved expected PA 128.07; status forecast 125.94; next-year actual 30.
Appearance 92.91%, conditional PA 135.55, unchanged hitting rate -0.798 per 600 PA.

September 16 entry falls INSIDE the September 6 to October 5 window. Its 29 PA may all precede the injury; aggregate window PA alone cannot locate the return. Keep timing unresolved rather than automatically clearing the flag.

Actual source counts:
- 2020 MLB: 23 PA, 0 HR, 7 K.
- 2021 AAA: 8 PA, 0 HR, 1 K.
- 2021 MLB: 107 PA, 5 HR, 32 K.
- 2022 AAA: 46 PA, 3 HR, 16 K.
- 2022 MLB: 162 PA, 9 HR, 48 K.

Eligible captured records relevant to placement or return:
- Known 2022-09-16, occurred 2022-09-16: Minnesota Twins placed RF Kyle Garlick on the 10-day injured list. Left wrist sprain..
- Known 2022-10-03, occurred 2022-10-03: Minnesota Twins transferred RF Kyle Garlick from the 10-day injured list to the 60-day injured list..

Actual saved participation output 2.573173; status terms: status_log_absence730 +0.0544; status_capture_scope +0.0064.

Actual saved conditional_pa output 135.550827; status terms: status_open_medical -8.9008; status_log_absence730 +3.3934; status_ordinary_departure +1.1400; status_offseason_activation -0.4265; status_medical_scope +0.2755; status_capture_scope +0.1744.

Origin-known open-spell comparisons, including unresolved cases:
- Nick Solak: entry 2022-09-21, 7.0 late PA, contradiction False; projected 216.2 PA versus 0 actual.
- Mike Trout: entry 2022-07-15, 105.0 late PA, contradiction True; projected 473.3 PA versus 362 actual.
- Randal Grichuk: entry 2022-03-30, 84.0 late PA, contradiction True; projected 412.3 PA versus 471 actual.

### Mark Canha at the 2016 cutoff

Captured entry 2016-05-09; late window 2016-09-03 to 2016-10-02: 0.0 PA.
Model open input 1; strict contradiction False.
Preserved expected PA 142.48; status forecast 137.79; next-year actual 187.
Appearance 88.96%, conditional PA 154.90, unchanged hitting rate -0.561 per 600 PA.

May 9 entry has zero PA in the late window. This check finds no contradiction, but no PA is not proof an injury remained open: demotion, role, rehabilitation and source gaps can also prevent MLB use. The unchanged forecast and real future workload are shown, not used to establish the flag.

Actual source counts:
- 2014 AAA: 537 PA, 20 HR, 112 K.
- 2015 MLB: 485 PA, 16 HR, 96 K.
- 2016 MLB: 44 PA, 3 HR, 20 K.

Eligible captured records relevant to placement or return:
- Known 2016-05-10, occurred 2016-05-09: Oakland Athletics placed 1B Mark Canha on the 15-day disabled list retroactive to May 9, 2016. Back strain.
- Known 2016-06-11, occurred 2016-06-11: Oakland Athletics transferred 1B Mark Canha from the 15-day disabled list to the 60-day disabled list. Back strain.

Actual saved participation output 2.086194; status terms: none.

Actual saved conditional_pa output 154.895582; status terms: status_ordinary_departure +0.0314.

Origin-known open-spell comparisons, including unresolved cases:
- Jarrett Parker: entry 2016-10-12, 13.0 late PA, contradiction False; projected 131.1 PA versus 177 actual.
- Cory Spangenberg: entry 2016-04-20, 0.0 late PA, contradiction False; projected 161.3 PA versus 486 actual.
- Elias Díaz: entry 2016-09-13, 0.0 late PA, contradiction False; projected 84.9 PA versus 200 actual.

## Repair requirement

Separate observed roster return from medical recovery. Reconstruct spells using dated actual MLB appearances,
or use bounded interval evidence when exact return dates are unavailable. Keep late-injury counterexamples and unknowns.
Do not merely flip the open flag or zero all past absence days; duration, recurrence and roster state must stay distinct.
The existing V59 predictive result is source-qualified and not a rejection of health information.
Do not refit this same ten-feature sweep until a corrected source-to-workload design is explicitly contracted.
