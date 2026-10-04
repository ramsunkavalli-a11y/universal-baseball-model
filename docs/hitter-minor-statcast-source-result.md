# Minor league Statcast recovered for future MLB testing

2026-10-04. The source recovery and player review are complete. We now have
361,530 complete exit-speed/launch-angle pairs from 2021–24, with exact game,
player, league and played-park identities. This is qualified historical provider
evidence, not a new prospect forecast or evidence of improved predictions.
The reviewed MLB-only research branch remains unchanged, as do the protected
forecast and explorer. The overall hitter-model goal remains unfinished.

## What was recovered and repaired

All 140 weekly contact requests finished below the 25,000-row cap. Twenty official
season/sport schedules independently establish the game and venue coverage. All
returned identities match the accepted player-game backbone. The covered league
contexts include every completed regular-season game in their schedules, but
games in other leagues remain untracked. Game coverage is not measurement coverage.

| Season | League | Games returned and official | Nonbunt physical opportunities | Complete pairs |
| --- | --- | --- | --- | --- |
| 2021 | Florida State predecessor | 586 / 586 | 25,817 | 22,279 |
| 2022 | Pacific Coast | 746 / 746 | 37,824 | 37,562 |
| 2022 | International | 1,491 / 1,491 | 73,051 | 3,945 |
| 2022 | Florida State | 643 / 643 | 28,226 | 25,275 |
| 2023 | Pacific Coast | 747 / 747 | 38,327 | 38,214 |
| 2023 | International | 1,477 / 1,477 | 73,224 | 72,904 |
| 2023 | Florida State | 649 / 649 | 30,093 | 25,043 |
| 2024 | Pacific Coast | 747 / 747 | 38,140 | 37,915 |
| 2024 | International | 1,485 / 1,485 | 72,498 | 71,995 |
| 2024 | Florida State | 644 / 644 | 29,493 | 26,398 |

The table's denominators include seven officially described physical contacts
without canonical pitch evidence; those are never manufactured as measured
contacts. The canonical ledger contains 446,686 contacts, plus those seven
missing opportunities. In 2022 International League, only 5.4% of these full-
season opportunities have complete measurements. The earlier one-day broad-
contact check used a different denominator and cannot establish season coverage.
There is no captured tracking for Double-A, High-A, other Single-A leagues, DSL
or rookie complexes. Absence means unknown, not weak or average contact talent.

Eleven older weekly pitcher-source extracts each stop at exactly 25,000 pitches;
ten lose their first requested dates and the set ends in June. The recovered
April 7 and June 9 dates contain 1,861 terminal contacts absent from those files.
Preserve those capped files and their hashes, but do not fit full-season features
from them. This finding does not reject an older model without checking whether
it actually used those specific files.

Thirty official feeds explain twenty-four initial one-contact differences:
thirteen batter-interference ABs without physical contact, seven physical contacts
without pitch evidence, three terminal-metadata errors, and a foul strikeout
incorrectly labeled in play. Two genuine measured contacts are restored from
the exact same official pitch identities; no launch values are invented. All
171,353 returned-game player boundaries reconcile after these classifications.
Six suspended games use per-PA played-park overrides. Every launch row now has
an authoritative league and actual venue. All 4,255 annual player/league summaries
were independently checked against NumPy for the six continuous sample metrics.
The [boundary review](hitter-minor-statcast-reviewed-boundary.md) records the rules;
original failed checks and ledgers remain preserved.

## What the training history actually supports

These measurements begin in 2021, unlike the ten-year MLB history. At the 2021
forecast origin, no training player has prior tracked minor evidence AND an
already completed next-year MLB label. At the 2022 origin, neither Triple-A
league has such a training example. The Florida context has only 13–17 distinct
MLB-participant training people, of whom 4–6 were pre-debut at their own origin.
A small same-level contact fit would not repair that lack of future MLB support.

By the 2023 origin, each held-player fold contains 105–113 Pacific Coast and
51–63 International League active training people; only 8–18 and 10–16,
respectively, were pre-debut. Florida has 40–44 active training people. By 2024,
the ranges grow to 171–177, 237–252 and 64–71. These totals are not proof of
profile support: age, debut status and sample-size intersections still contain
many absent or sparse groups. Twenty people remains only a warning threshold.

All 35 chronological fold profiles were independently recounted from the
corrected source. No unsupported forecast was dropped and no held-player group
was allowed into its training population. Earlier support artifacts are retained;
the metadata repairs do not change any support-profile membership.

## Player walkthroughs

The machine-readable review contains eleven player-origins, nine distinct people,
actual three-season level statistics, all 199 current hitting inputs, signed
terms/replays of the saved current rate head, exact current opportunity/value,
MLB-only Statcast forecasts, future results and four origin-only comparisons.
All eleven saved current hitting forecasts replay exactly. These source reviews
make no claim of a minor-Statcast gain or loss: no new predictive head was fitted.
Rate units below are future-season-relative MLB batting wins per 600 PA, not
full WAR. Zero future PA means unobserved talent, not observed zero talent.

Elly De La Cruz's 2022 origin contains 210 Single-A PA in 2021 with 5 HR, 65 K
and 10 unintentional walks, followed by 513 High-A/AA PA in 2022 with 28 HR and
158 K. Only his earlier Daytona context is tracked: 76 of 133 nonbunt contacts,
mean EV 89.61 and EV95 108.78. His current forecast is -0.015 rate and 119 PA;
he produces 427 MLB PA in 2023 at -0.748 future-relative rate. This is not an
automatic hard-contact success: both low coverage and high strikeouts matter.
Origin-only Hassell, Gladney, Ramos and Vukovich all have zero next-year MLB PA.

At Elly's 2023 origin, his Louisville sample adds 109 measured contacts, mean EV
93.37 and EV95 116.30, alongside 186 AAA PA with 12 HR, 50 K and 26 walks and
427 MLB PA with 13 HR and 144 K. The old capped cache retains only 70 of those
109 earlier minor contacts. Current rate -0.074 becomes +0.189 in the ALREADY
TESTED MLB-only branch; actual 2024 rate is +1.886 and PA 696 versus projected
407. That existing change uses MLB evidence, not these newly recovered minors.
Origin-only Walker, Diaz, Alvarez and Thomas retain both arrivals and failures;
Diaz has zero next-year MLB PA despite 224 measured minor contacts.

Junior Caminero is untracked in the minors through the 2023 origin: his 2022
Single-A stint is Charleston, not the Florida context; 2023 High-A/AA is also
untracked. His 2023 36-PA MLB debut supplies the MLB-only branch, which moves
rate .346 to .308; 2024 rate is -.154 over 177 PA. There is no missing Florida
sample to manufacture. At the 2024 origin, Durham supplies 167 measured contacts
from 168 opportunities, mean EV 93.27, EV95 111.55 and 56.9% hard contact,
alongside 236 AAA PA with 13 HR/50 K and 177 MLB PA with 6 HR/38 K. Current
rate .280 and MLB-only .588 both trail his 2025 +2.175 over 653 PA; projected
PA remains 419. His new minor evidence may help hitting, but cannot be claimed
to solve the workload miss before a new test. Holliday, Domínguez, Martínez and
Noel are origin-only comparisons; Noel's 153 next-year PA preserves the downside.

Wyatt Langford's 2023 origin has 200 professional PA spread over rookie, High-A,
AA and AAA, with 10 HR, 34 K and 36 walks. Only 26 AAA PA and 13 measured
contacts are tracked: mean EV 88.85, EV95 108.44. That very small contact sample
must not override the rest of his production or pedigree. Current and MLB-only
rate remain .688, close to actual .549; projected 215 PA misses actual 557.
The coarse existing peer rule exposes another LIMIT, not independent validation:
it selects Bannister, Walters, Bellony and Placencia because each is labeled AAA,
but they have only 1–5 AAA PA and predominantly lower-level production. They are
not strong baseball comparables to this recent college draftee. Their failures
cannot establish that Langford's prospects were low. Keep their original identities
and level histories; require actual level exposure and existing pedigree/production
context in the next experiment's support review rather than certifying a AAA label.

Nick Kurtz's 2024 origin has only 50 A/AA PA, 4 HR, 10 K and 12 walks; none are
in tracked leagues. Current and MLB-only rate stay -.063 and expected PA 10,
versus actual 2025 +5.150 over 489 PA. Statcast cannot fix a prospect for whom
it has no measurements. Montgomery, Soto, Moore and Mershon are retained
origin-only comparisons; Moore reaches 184 MLB PA while the other three do not.
Those comparisons do not replace the separately reviewed positive prospect model.

Bryce Eldridge's 2024 origin has 519 PA across A, High-A, AA and AAA, 23 HR,
132 K and 56 walks. Only his final 35 AAA PA produce tracking: 20 contacts,
mean EV 91.56, EV95 105.09. Current and MLB-only rate stay .313 and PA 68;
his 2025 MLB sample is only 37 PA at -3.373. Neither this small measured sample
nor that small future outcome can settle his eventual talent or trade value.
Basallo, Ballesteros, Anthony and House are preserved age/level comparisons with
53–201 minor measurements and 66–303 actual next-year PA. Their measurement
counts differ substantially and must not be flattened into an equal-quality tier.

Juneiker Caceres's age-16 2024 DSL origin has 167 PA, 0 HR, 18 K and 17 walks.
No tracking exists; .499 current batting rate remains unchanged and projected
PA .067 versus zero actual. Stiven Martínez, Javier Sánchez, Johan Rodríguez
and Estivel Morillo also have no tracked sample or next-year MLB PA. This says
nothing about those players' eventual MLB talent; the target is next calendar year.

The pilot high/low daily cases also get full-season checks. Narciso Crook's 2023
sample has 157 measured contacts, mean EV 87.36 and EV95 107.14, with 325 AAA
PA, 10 HR and 117 K. His 2022 238 contacts have NO measurements, not zero EV.
The repaired early-2023 window has 63 nonbunt contacts versus 43 terminal contacts
in the old capped files. He gets zero next-year MLB PA despite the April 7
three-contact mean of 104.43. Origin-only Oliva, Reetz, Miller and Papierski also
retain three zero-arrivals and Reetz's 15 PA. One high-EV day is not a roster forecast.

Brewer Hicklen has 172 measured 2023 contacts, mean EV 91.14 and EV95 107.40,
after a 2022 559-PA AAA season with 28 HR and 202 K. His 2022 International
League contacts are all unmeasured. The old files retain 56 versus 77 recovered
early-2023 contacts. Expected PA 8.5 versus five actual is ordinary low-opportunity
behavior; five PA are not a precise future-talent label. Leyba, Liberato, Harrison
and Papierski all get zero future MLB PA. Good power can coexist with non-arrival.

Jimmy Herron provides the lower-contact-strength contrast: 356 measured 2023
contacts, mean EV 86.10 and EV95 102.08, with 539 AAA PA, 19 HR, 103 K and
68 walks. The repaired early window contains 45 nonbunt contact keys missing
from the capped extracts; older raw terminal counts also contain a bunt, so their
simple count difference is not the same universe. Expected PA 38 becomes zero
actual; neither his strong workload nor a large tracking sample assures promotion.
Dunn, Wendzel, Keirsey and Mann preserve both arrivals and failures.

## Disposition and next work

Approve this source for a QUALIFIED, coverage-limited development experiment
after the final independent receipt, not deployment or original-vintage camera-
only claims. Current provider values may include estimates; individual estimation
flags and publication vintage are unavailable in the export, as stated in
[Savant's definitions](https://baseballsavant.mlb.com/csv-docs).

The justified next step is one regularized prospect contrast with league-specific
measurements learned inside chronological held-player training, against the
reviewed MLB-only branch and the existing prospect alternative. Do not treat
minor EV as MLB-equivalent or retest the closed shape/algorithm challengers.
Explicitly handle absent 2021/2022 training contexts, sparse lower-level future-
MLB examples, real level exposure, limited samples and missing tracking. Preserve
all non-arrivals and untracked forecasts. A new contract precedes those fits;
no predictive improvement for minors is claimed at this source checkpoint.
