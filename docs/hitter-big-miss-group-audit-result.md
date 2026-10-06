# What the big hitter misses actually tell us

2026-10-05. Historical development diagnosis, not a new model win. The fixed
30,519 forecasts predict next-year MLB PA and batting plus replacement value,
not full WAR or trade value. Targets stop at 2025. No forecasts were refitted.

## Three different problems, not one adjustment

| Origin-known group | Forecast MLB arrivals | Actual arrivals | Forecast PA per arrival* | Actual PA per arrival |
| --- | ---: | ---: | ---: | ---: |
| No MLB debut, current AA/AAA experience | 599 | 730 | 124 | 127 |
| No MLB debut, lower/other leagues | 100 | 62 | 96 | 114 |
| Current MLB season of at least 400 PA | 1,386 | 1,409 | 476 | 477 |
| Established MLB player, no current MLB PA | 27 | 24 | 191 | 210 |

*Model-implied conditional group average is total expected PA divided by sum
of arrival probabilities. The unweighted conditional estimate over EVERY player
is not comparable with actual workload among ONLY arrivals. That comparison
would wrongly suggest that upper-minor conditional workload is the main group
shortfall. The correct aggregate diagnosis is missing arrivals. This does not
prove that workload is right for every prospect or that arrival and workload
errors are causally independent.

The lower/other-minors group already predicts too many arrivals. Established
gap-year totals are close. Raising all prospect estimates, all zero-PA return
estimates, or all conditional workloads is not supported. Across all origins,
forecast batting-plus-replacement totals are 4,184.51 versus 4,193.77 actual;
good totals do not certify individual predictions. These are pooled descriptive
figures, not the equal-origin weighting used in the previous medical experiment.

## Player walkthrough and baseball judgments

The persisted [walks](../reports/model-evidence/hitter-big-miss-group-repair/audit-player-walks.json)
contain three years of actual level/PA/HR/K/BB statistics, all 293 opportunity
inputs, training and exact-profile counts, independently replayed saved heads,
probability, conditional PA, batting rate, value, and three origin-selected peers.
All 28 saved heads reproduce. Top-50 PA/value selection yields 91 distinct
diagnostic rows; fourteen player-origins cover patterns and ordinary controls.

| Player, forecast season | Prior evidence and forecast mechanics | Forecast PA / actual PA | Judgment |
| --- | --- | ---: | --- |
| Fielder, 2017 | 693 PA in 2015, 370 in 2016; model p=.959, conditional PA=437 | 419 / 0 | Known career departure missing from forecast policy; repair it. |
| McLain, 2024 | 403 MLB PA, 16 HR, 115 K in 2023; p=.986, conditional=606 | 598 / 0 | March shoulder injury cannot be used in a January forecast. High estimate still requires role/durability scrutiny; zero outcome alone does not justify a hard zero. |
| Tatis, 2023 | 546 MLB PA and 42 HR in 2021, none in 2022; p=.154, conditional=400 | 61 / 635 | Known finite suspension is not an indefinite career exit. Exact legal/role training profile has zero people. Health overlap remains unresolved; do not assign a guessed recovery probability. |
| Wander Franco, 2024 | 491 PA and 17 HR in 2023; p=.991, conditional=550 | 545 / 0 | Unresolved legal availability with no exact-profile examples; unqualified near-certainty is unsound. Final outcome is not grounds for inventing a cutoff-known permanent ban. |
| Kwan, 2022 | 341 combined AA/AAA PA, 12 HR and only 31 K in 2021; p=.721, conditional=158 | 114 / 638 | Both role and hitting outcome underestimated. Upper-minor cohort supports an arrival problem, not a universal 600-PA assignment. |
| Reynolds, 2019 | 383 AA PA, 7 HR, 73 K, 43 BB in 2018; p=.175, conditional=58 | 10 / 546 | Low arrival estimate plus low projected workload/rate; only 12 exact-profile active training people. |
| Judge, 2017 | 410 AAA PA, 19 HR; brief MLB sample 95 PA with 42 K; p=.902, conditional=348 | 314 / 678 | Batting-value error -7.01: -1.28 workload accounting, -5.72 rate accounting. A playing-time change alone cannot fix this breakout miss. |
| Judge, 2025 | 62/37/58 HR in preceding three MLB years; p=.995, conditional=536 | 533 / 679 | Elite established players are more plausibly underallocated workload. This forecast also extrapolates beyond training feature ranges. |
| Chris Davis, 2018 | 47/38/26 HR, latest K=195 in 524 PA; p=.983, conditional=533 | 524 / 522 | PA almost exact. Value overprediction +4.22 is almost entirely hitting-rate error, not a job model failure. |
| Belt, 2024 | 404 PA, 19 HR, 61 BB in 2023; p=.601, conditional=325 | 195 / 0 | No affirmative retirement at cutoff. Unsigned is not retired; leave unchanged. |
| Maikel Franco, 2022 | 403 MLB PA, 11 HR in 2021; p=.628, conditional=293 | 184 / 388 | More PA would improve workload error but, with the fixed optimistic rate, worsen value error. |
| Estevez, 2025 | Three DSL years, 112/180/193 PA; p=.0024, conditional=85 | 0.20 / 0 | Ordinary lower-minor non-arrival. Conditional workload has only four exact-profile training people; nearly zero expected MLB PA is not proof of a validated active-player rate. |
| Hoskins, 2024 | Prior 672 PA/30 HR then zero MLB PA; p=.921, conditional=399 | 367 / 517 | Recognized as likely return, still short on workload; three exact-profile training people. Do not confuse this with a release-only player. |
| Smoak, 2019 | 637 then 594 PA, 38 then 25 HR; p=.993, conditional=493 | 489 / 500 | Ordinary workload control is close; hitting value still overpredicted by 0.83. |

The original peer rule uses age/current MLB PA/last MLB quality. For never-debut
players, its last two measures are zero: Kwan's original peers therefore are not
necessarily comparable bats. The appended audit adds AA/AAA exposure and K/BB/HR
profile matching, without using outcomes. These are diagnostic comparisons,
not causal controls or an independently validated similarity model. No unmatched
legal-return peers should be described as evidence that Tatis cannot return.

## Reporting flaw and source repair

The old `sparse_profile` flag comes from a COARSER preflight group than the
adjacent `profile_people` count. Thus it can say false next to zero exact-profile
people. This is a reporting trap, not proof that every absent interaction is
unlearnable. Preserve the old evidence, append explicitly named exact-profile
zero and under-20 warnings for both heads, and require them in future summaries.
Twenty is the existing warning threshold, not statistical certification.

Proceed with dated affirmative career-departure supplementation. Fielder
announced a medical career end, not formal retirement; preserve that distinction.
[Official report](https://www.mlb.com/news/prince-fielder-left-his-mark-in-milwaukee-c194819958).
Martínez's final game was announced before the forecast cutoff.
[Official report](https://www.mlb.com/news/victor-martinez-to-play-final-game-saturday-c295503108).
No blanket old-player or free-agent penalty is warranted. The next fitted
question should address upper-minor ARRIVAL discrimination, preserving the
full-history backbone and checking workload/value and lower-level non-arrivals.
Do not repeat the closed source-covered medical refit or team-record test.

Audit judgment complete; deployment not approved. Retirement coverage remains
partial, Tatis/Franco availability remains unresolved, hitting-rate tail misses
remain, and the full player-value project is not complete.
