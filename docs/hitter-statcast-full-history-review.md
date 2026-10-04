# Historical Statcast source and player review

2026-10-04. MLB 2015–24 now supplies 1,153,554 complete exit-velocity and launch-angle
pairs after the declared special-result exclusions. All earlier hit counts match
the official backbone, and all twenty normal-contact discrepancies are explained
at the play level. This is source preparation, not a better projection: no new
model has been fitted, and current forecasts and protected 2026 files are unchanged.

## Coverage and source decisions

| Season | Usable non-bunt contacts | Complete launch pairs |
| --- | ---: | ---: |
| 2015 | 128,184 | 125,365 |
| 2016 | 126,796 | 124,625 |
| 2017 | 125,761 | 124,974 |
| 2018 | 124,549 | 123,826 |
| 2019 | 124,233 | 123,272 |
| 2020 | 43,598 | 43,301 |
| 2021 | 120,286 | 119,919 |
| 2022 | 123,209 | 122,683 |
| 2023 | 123,206 | 122,857 |
| 2024 | 123,095 | 122,732 |

Twenty player-season totals differed by one under the original AB−K+SF+SH rule.
Thirteen were official batter-interference outs with no in-play pitch. The other
seven were interference awards outside the normal at-bat count. The corrected
normal-contact equality is exact for every player in 2015–22. No raw row, hit
count or original failed receipt was rewritten. Devon Travis's 2015 award has
69.2 mph and −27 degrees but is excluded from the normal measurement universe;
Jorge Soler's 2021 interference out has no contact to measure. Tim Beckham's
ordinary 2016 fielding-error play remains, despite later interference during it.
The exact descriptions, game IDs and classifications are in the evidence ledger.

Actual parks are joined from completed historical schedules, not current franchise
homes. Three games resumed at a different park: Detroit to Oakland in 2019,
Washington to Baltimore in 2020, and Atlanta to San Diego in 2021. Their contacts
use terminal play timestamps to select the original or resumed schedule segment.
Giving all contacts the feed's final game venue would misassign the earlier ones.
The raw ATH display label is mapped to historical OAK for league identity only.

[Savant](https://baseballsavant.mlb.com/csv-docs) includes provider estimates of
some launch values. [Tango's description](https://tangotiger.com/index.php/site/article/statcast-lab-no-nulls-in-batted-balls-launch-parameters)
explains that those estimates may use the observed outcome and be revised
retroactively. Missing flags alone cannot identify estimated balls. This source
therefore cannot prove original preseason availability or camera-only incremental
information. Historical predictor-season outcomes are legitimate inputs; unknown
provider vintage is a separate limitation. Expected-outcome and future-game
fields are not included. Raw launch measurements are not park/opponent-adjusted talent.

## The same players from stats to current forecasts

All ten fixed source cases retain their original IDs, origins, dated statistics,
199 actual hitting inputs, 251 opportunity inputs, saved rate-model terms,
forecasts, outcomes and origin-only peers. The [earlier complete walkthrough](hitter-own-mlb-contact-source-result.md)
contains the unchanged adjustment and saved-head calculations; the new case
artifact extends those same traces with three years of launch and actual venue
history. No hypothetical Statcast upgrade is inserted into those forecasts.
Rates below are our custom MLB batting wins per 600 PA, not full WAR. An inactive
player has no observed rate, not a zero hitting-talent label. PA and rate are
separate heads, and expected contribution includes the origin replacement term.

| Player and origin | Origin MLB PA / HR / UBB / K | Current rate / expected PA | Following-year rate / PA |
| --- | --- | --- | --- |
| Judge 2023 | 458 / 37 / 79 / 130 | +3.360 / 536 | +7.558 / 704 |
| Judge 2024 | 704 / 58 / 113 / 171 | +4.534 / 531 | +6.287 / 679 |
| Soto 2023 | 708 / 35 / 121 / 129 | +3.941 / 634 | +5.516 / 713 |
| Belt 2023 | 404 / 19 / 60 / 141 | +0.686 / 244 | unobserved / 0 |
| Torkelson 2023 | 684 / 31 / 66 / 171 | +1.296 / 547 | −0.721 / 381 |
| McLain 2023 | 403 / 16 / 31 / 115 | +0.915 / 599 | unobserved / 0 |
| Kurtz 2024 | No MLB; 50 A/AA PA | −0.063 / 10 | +5.150 / 489 |
| Caceres 2024 | No MLB; 167 DSL PA | +0.499 / 0.067 | unobserved / 0 |
| Friedl 2023 | 556 / 18 / 46 / 90 | +0.408 / 451 | −0.255 / 341 |
| Siani 2024 | 334 / 2 / 21 / 92 | −1.527 / 187 | −2.537 / 19 |

Judge's 2021–23 history contains 394, 398 and 239 complete pairs. His EV95 is
114.60, 113.24 and 113.14 mph; his hard-air share rises from 32.0% to 41.2% to
47.3%. His 2022 production already includes 62 HR in 696 PA. The existing 2023
forecast receives +2.064 from pooled MLB quality, +0.581 from recent quality and
+0.564 from recent workload; summed age terms subtract 0.405. This is not an
absence of power evidence. The new measurement might improve how that power is
represented, but only a matched fit can establish the effect. His 2024 origin
adds 388 pairs with EV95 113.70 and 42.3% hard air. Mookie Betts, selected as an
origin-known peer in the earlier manifest, has current +2.945 versus observed
+3.043; Adolis García has +0.791 versus −0.699. The comparison pool is not all successes.

Soto's 2021–23 complete samples are 413, 427 and 440; EV95 is 111.18, 109.40 and
111.21, with hard-air shares 26.6%, 26.7% and 29.1%. His 2023 walk/strikeout
history remains crucial: launch quality is conditional on contact, not the whole
hitter. Existing pooled quality contributes +1.595, current workload +1.110 and
recent quality +0.497. Four Mexico City contacts retain the actual MLB venue.
His peer Nolan Jones has +1.279 projected versus −1.160 observed, unlike Soto's
better-than-projected following season. Neither contact evidence nor youth
guarantees a breakout.

Belt's three samples are 216, 168 and 196 pairs, with EV95 106.93, 105.26 and
107.40. Strong contact in 2023 does not explain why nobody employed him in 2024.
His existing age term alone subtracts 0.890 while pooled quality adds 0.717.
Origin-known peers J.D. Martinez, Blackmon, McCutchen and Canha all played the
following year. Preserve Belt as an employment miss, not evidence to force his
talent to zero or teach Statcast that good contact causes absence.

Torkelson has 262 pairs in 2022 and 438 in 2023, EV95 107.10 to 108.60 and
hard-air share 23.7% to 30.6%. He hit 31 HR at origin and still deteriorated.
Current workload adds 0.842, age 0.445 and first-base position 0.232 in the rate
head. An automatic hard-contact bonus could make this miss worse. His preselected
peers include Guerrero (+2.683 versus +4.095) and Vaughn (+0.834 versus −0.241),
so retain both sides when testing incremental contact information.

McLain's 2023 sample has 247 pairs, EV95 105.84 and 29.1% hard air; there is no
earlier own-MLB launch sample. He also had 180 AAA PA with 12 HR before his 403
MLB PA. Current pooled quality, workload and age contribute +0.521, +0.518 and
+0.416, but his following-year rate is unobserved because he played zero MLB PA.
Peer Elly De La Cruz played 696 PA; peer Wander Franco played zero. Good launch
measurements cannot settle future availability, and those exits stay in value scoring.

Kurtz has 35 A PA and 15 AA PA, four HR, twelve UBB and ten K, without own-MLB
launch data. His draft-history term adds 0.165 and age adds 0.619; other terms
pull the forecast back. His previously positive translated prospect alternative
remains a separate benchmark, not a new Statcast result. Eldridge and Xavier
Isaac remain the original origin-only peers, including Isaac's following-year
non-arrival. A MLB-only extension must leave Kurtz unchanged, not pretend to
solve his fast-arrival miss by dropping him from the score.

Caceres is sixteen, with 167 DSL PA, zero HR, seventeen UBB and eighteen K.
He has no own-MLB launch evidence. Linear and squared age terms add 1.216 and
0.270 to his latent rate, a known extrapolation concern, while expected next-year
MLB PA is essentially zero. His original young DSL peers also did not arrive.
Retain the distinction between an unsupported conditional talent estimate and
little immediate contribution; Statcast coverage does not repair this case.

Friedl's samples expand from 30 to 181 to 378 pairs in 2021–23; EV95 stays
102.81, 103.70 and 103.40. Hard-air share falls from 20.0% to 20.4% to 13.0%.
His 2023 bunts and measured foul-air contacts do not enter terminal non-bunt
launch summaries, but their official hits remain in batting production. Existing
workload and pooled quality add 0.714 and 0.399. Selected peers include Nootbaar,
who improved, and Outman, who deteriorated sharply. This tests a different contact
profile than Judge rather than defining low velocity as uniformly bad hitting.

Siani's 2022, 2023 and 2024 samples are sixteen, four and 195 pairs, EV95 102.12,
98.53 and 102.28. Four balls do not establish a decline in power. He has 531 AA
PA in 2022 and 493 AAA PA in 2023 in the dated history; these are not invented
MLB tracking. Pooled MLB quality subtracts 0.559, while workload and age add
0.399 and 0.322. His next-year rate comes from only nineteen PA and is noisy.
Original peers range from Johan Rojas (−3.102 observed) to Moniak (+1.734), with
Pache not appearing. Small future samples require their proper PA weighting.

## Training support and allowed next step

Every one of the thirty-five current chronological, whole-player-separated folds
now has active tracked training people. Counts range from 403–416 people for
origin 2016 to 975–1,022 for origin 2024, instead of zero in every early fold.
The first origin still has only 2015 measurement history; earlier years remain
unknown, not zero production. People can occur in more than one sample band over
their training seasons, so summing band counts does not give distinct people.
These are source-support counts, not certification of every model profile.

The source walkthrough is complete. The next bounded contrast may use this
qualified MLB provider source after independent output verification. Preserve the
vintage limitation, all inactive and untracked players, exact existing PA, and
the separate prospect alternative. Freeze model features and comparisons before
fitting; report the actual tracked/nontracked effects and full player gains and
harms before any disposition. Covered minor-league tracking still needs its own
league/source calibration and is not supplied by this MLB-only checkpoint.
