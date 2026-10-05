# Player review of the completed 2026 hitter evaluation

We inspected the original sources, frozen inputs, exact fitted calculations and
completed MLB outcomes. No 2026 result changed a forecast. Rates below are
batting wins above the target MLB average per 600 PA. Contribution adds the
fixed 2025 replacement reference; it excludes defense and running.

All ten original focal cases and their original peers remain in the 37 saved
pre-freeze walks. Diagnostics add six largest contribution errors in each
direction, two upper-minors non-arrivals, and an ordinary case at each of MLB
and upper minors. Two peers per focal case are selected from **origin-only**
age, exposure, hitting summary, career exposure, position and tracking within
the same stage/debut state. This is a limited resemblance rule, not a scouting
comparison. In particular it does not match prospect rank, so McGonigle's
unranked peers cannot tell us how a fellow elite prospect should develop.
Outcome-selected cases illustrate errors; they are not independent validation.
There is no matched 2026 benchmark from which to invent an improvement case.

The machine-readable review retains 51 focal identities, 129 total replayed
players, complete input and rate-term lists, exact participation/PA tree traces,
actual profile support, source counts and every peer's forecast and outcome.
The following narratives interpret the important contrasts, including failures.
Terms and tree-path accounting reproduce outputs; they are not causal effects.

## Judge and Yordan show different workload errors

Judge had 458, 704 and 679 MLB PA in 2023–25, with 37, 58 and 53 HR. The source
and inputs include all three seasons and his recorded age of 33. The measured
MLB route gives 99.3% participation, 592 conditional PA, 588 expected PA and
4.689 hitting wins per 600 PA. Current workload, pooled PA per game and recent
hitting have large positive paths in the saved workload model. No early DSL
line or missing 2025 year caused this forecast.

He actually received 285 PA with 18 HR, and his observed rate was 2.358.
Contribution was forecast at 6.425 versus 2.008 actual. Exact error accounting
assigns 3.310 wins to the PA difference at the frozen rate and 1.107 to the
rate difference at actual PA. This identity does not establish an injury cause
or that the short season was knowable. Origin-nearest Ohtani and Schwarber were
forecast at 591/577 PA and actually received 618/701. Judge's PA miss does not
justify treating all comparable stars as part-time players.

Yordan's inputs retain 496 and 635 MLB PA in 2023–24, but only 199 in 2025,
plus the minor appearances. The old seasons were not lost. His forecast was
93.7% participation, 495 conditional PA, 463 expected PA and rate 2.637.
He actually had 692 PA, 42 HR and rate 4.616. The four-win contribution miss
splits into 1.719 workload and 2.283 hitting wins. A low recent workload did not
zero his opportunity, but a fully productive season was underpredicted.
His limited origin peers Pavin Smith and Gavin Lux received 122 and zero PA;
they are opportunity controls, not equivalent elite bats. Simply undoing
workload caution for everyone would worsen such cases.

## Duran and Guerrero were primarily hitting misses

Duran's 2023–25 MLB PA are 362/735/696 and HR are 8/21/16. His source inputs
include the high recent BABIP and extra-base hits, not just HR. The measured
MLB rate is 1.538; expected PA 583 versus 608 actual is close. His actual
rate was −2.155. Of the 3.601-win overprediction, 3.742 is the hitting term,
partly offset by −0.142 from PA. Reducing his playing-time forecast would not
solve the underlying observed rate miss. Gavin Sheets, an origin peer, had
414 expected versus 419 actual PA; another, Arozarena, performed better than
his forecast. This is not a universal workload error in the profile.

Guerrero's source has 682/697/680 MLB PA and 26/30/23 HR. Pooled MLB hitting,
recent hitting and workload contribute positively to his fitted rate 2.919;
tracking is present. He receives 620 expected versus 609 actual PA, but the
actual rate is −0.531. The 3.586-win miss consists of only 0.085 workload
and 3.502 hitting wins. No dropped MLB season or career-PA join explains it.
We have not established whether this decline was predictable from omitted
cutoff-known evidence; neither player warrants a named hindsight override.

## Crow Armstrong was not invisible but his breakout was underpredicted

His source has 19, 410 and 647 MLB PA and 0, 10 and 31 HR in 2023–25.
Age 23, 1,076 career MLB PA and current tracking are included. He is not on the
never-debut path. The forecast gives 98.7% participation, 524 conditional PA,
517 expected PA and rate 0.180. His saved rate sum includes positive current
workload and young age, but negative older AA exposure and era terms alongside
tracking and event terms. Those correlated term contributions are arithmetic,
not proof that AA history causally suppressed talent.

Actual PA were 726, HR 45 and rate 3.965. The 5.293-win underprediction is
0.713 workload plus 4.580 hitting wins. Origin-nearest Pages and Rafaela also
hit above their frozen rates, but much less dramatically. This supports auditing
young MLB rate calibration across older folds, not assuming this one breakout
could have been forecast exactly. Current data and support exist; correct
construction alone did not make the forecast accurate.

## Rumfield and McGonigle expose different prospect weaknesses

Rumfield had 474 AAA PA in 2024 and 587 in 2025, with 15/16 HR and 78/108 K.
The source and weighted inputs retain both AAA years. He is 25, had not debuted,
was not on the December roster, and was not on the archived Top 100 list.
The model gives 25.3% participation but only 106 conditional PA, producing
27 expected PA. It also estimates below-average MLB hitting at −0.898.
Actual outcomes are 631 PA, 16 HR and rate 2.927. The five-win miss splits into
0.979 workload and 4.022 hitting under this particular accounting order.
The low rate makes the PA term smaller; it does **not** mean a 604-PA workload
miss is unimportant. His origin peers Murray and Boissiere received 11 and
zero PA, illustrating why every older unranked minor leaguer cannot be upgraded
on the strength of Rumfield. His actual-head profile counts are not sparse.

McGonigle's age-20 source has 397 minor PA in 2025, including 206 AA PA with
12 HR, 26 K and 33 UBB. He is archived rank 2, explicitly represented by score
0.99, not an unknown pedigree. The saved workload paths show that rank adds
117.5 PA relative to the tree reference while no prior MLB workload subtracts
92.8; those are decomposition terms, not isolated causal effects. Participation
is 72.6%, conditional PA 251 and expected PA 182. His conditional rate is only
0.218. Actual outcomes are 707 PA and rate 2.121: both opportunity and hitting
were low. Scouting was already used; proposing to add it again would miss the
problem. The review's generic origin-nearest unranked peers are a deliberately
limited comparison. A future historical audit must also compare matched
scouting/level exposures, without selecting peers by eventual success.

The other selected tails are not suppressed. Bauers had only 218 MLB PA in
2025 and receives 211 expected PA and rate −0.110; actual is 578 and +3.160.
His older MLB seasons and minor power are present. A larger role and better
hitting both contributed, but neither follows automatically from his source
profile: nearest Tellez received 11 PA and Smith 300. France receives 273 PA
and rate −0.528 after 490 MLB PA and seven HR in 2025; actual is 500 PA,
21 HR and rate +2.818. Those are large improvements, not evidence that their
weak recent histories were omitted.

Rooker has 699 MLB PA and 30 HR in 2025; his forecast is 541 PA and rate
1.854 versus 203 and −1.148 actual. Friedl has 685 MLB PA and 14 HR; forecast
570 and +0.322 versus 272 and −4.047. Polanco has 524 MLB PA and 26 HR;
forecast 421 and +0.607 versus 145 and −5.889. All use measured MLB inputs;
each misses both workload and performance. Their source counts do not tell
us whether later injury, selection or genuine decline caused the shortfall,
so the review does not invent a medical explanation or claim a simple fix.

## Non arrivals and brief promotions stop a blanket prospect upgrade

Jett Williams has 572 AA/AAA PA in 2025, rank 51 and no December roster spot.
The saved forecast gives 85.8% participation, 256 conditional PA and 220
expected PA. Aidan Miller has 526 AA/AAA PA, rank 23, and receives 85.0%,
251 conditional PA and 213 expected PA. Neither has MLB PA in the completed
target. Their hitting ability is unobserved in MLB, not zero. These are genuine
arrival misses; their rank-driven positive paths need cohort calibration,
not a rule that all highly ranked prospects deserve full-season workload.

Made and De Vries are both recorded age 18. Made's 2025 source is 378 A,
123 High-A and only **24 AA PA**; De Vries has 433 High-A and 103 AA PA.
They are both labeled upper minors, but the input vectors do retain the
different exposures. High archived ranks help produce 34%/40% participation
and 89/121 expected PA. Their refined actual-head profile minima are 10/9
people, explicit sparse extrapolation warnings. Neither debuted in this target.
This does not disprove superstar upside or estimate six-year value. It does
show that the display's coarse upper-minors label must not imply the same
readiness as several hundred established AA/AAA PA. A historical exposure/
stage audit is warranted; no after-the-fact relabeling is used to improve this
test.

## Kurtz Lee and the ordinary controls

Kurtz's 489 MLB PA and 36 HR in 2025 are present; he receives the measured MLB
route, not a prospect fallback. Forecast hitting rate 2.650 is close to actual
2.897. Expected PA 535 exceeds actual 434. His contribution overprediction
0.584 combines +0.763 workload and −0.179 hitting. This is a plausible strong
hitter projection with a workload miss, not a successful final-value prediction
in every respect. Lee's 617 MLB PA in 2025 are also present. Forecast PA 516
versus actual 579 and rate −0.089 versus +0.116 produce contribution 1.531
versus 1.917. His prior Korean career was not allowed to overwhelm newer MLB
evidence. The result is a modest miss, not proof foreign history never helps.

The ordinary-case rule chooses Horwitz and Jose Fernandez, not reputational
favorites. Horwitz's 411 MLB PA in 2025 lead to 406 expected PA, rate 0.519
and contribution 1.615. Actual is 451 PA, rate 0.277 and contribution 1.614.
That near-exact final number reflects offsetting PA/rate errors.
Fernandez has 511 AA PA in 2025 and no prior debut. He receives 57.5 expected
PA and rate −1.264; actual is 222 PA and rate −1.654. Contribution 0.058 versus
0.080 looks excellent while workload is badly low. An accurate final number
alone is not enough to certify the underlying projection choices.

## Review decision

The selected source counts, recency exposures, career joins, saved rate sums,
participation links, PA paths and contribution identities reproduce. No new
construction defect was demonstrated by these misses. That conclusion is
limited to the checks performed, not an assumption all underlying information
is perfect. The cohort exposes prospect delivered-value underprediction,
coarse stage interpretation, sparse very-young profiles and foreign-entrant
coverage gaps. Several famous misses are primarily realized performance
variation with no verified predictable cause yet.

The required review is complete and the result remains qualified. Do not tune
these names or this season. Carry the supported issues into a bounded older-
fold audit for a later forecast, obtain a genuinely matched public baseline,
and preserve this complete evaluation as the reference.
