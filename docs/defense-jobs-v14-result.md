# League job limits do not fix individual position forecasts

2026-10-07. The new allocation respects the league's available fielding and DH
jobs and reduces excess positional credit. It does **not** improve the primary
player-value forecast, and the player review finds role logic that needs repair.
Keep the corrected DH source and capacity accounting; do not adopt this candidate
as a better individual position forecast. The existing useful defensive-skill
baselines are unchanged, not rejected by this result.

## What changed and what stayed fixed

The [contract](defense-jobs-v14-contract.md) compares 12,432 forecasts for 2023–2025.
Both arms use the same corrected DH measurements, including Ohtani's simultaneous
P/DH starts. The reference preserves the old repertoire calculation; its fielding
forecasts replay unchanged. The candidate models fielding and DH jointly using
same-rule historical targets, then caps positions at the origin-known league
inventory. Unknown roles and historically omitted players retain a separate
reserve. It does not award value to that reserve.

Expected PA, hitting, twelve history-based defensive rates and native opportunity
conversions are identical. This is a test of where defense will be used, not a
new talent estimate. The expanded value includes batting, replacement, positional
adjustment and the measured native channels. It is not full WAR or trade value.

## Scores and totals

The primary matched value error is essentially unchanged: RMSE 0.433262 for the
reference and 0.433346 for the candidate. The difference is +0.000084 custom wins,
with a person-clustered 95% interval of −0.001130 to +0.001232. Average absolute
error improves from 0.121369 to 0.120662, but that does not establish an overall
accuracy improvement. The ordinary 2025 target worsens from 0.421754 to 0.424056;
the other two targets improve slightly. Removing framing does not change the
conclusion.

Individual position-run error rises from 0.952537 to 0.965248 runs. Native-defense
delivery error rises from 1.557133 to 1.561132 runs. Their nominal paired intervals
indicate small deteriorations, not gains. Actual defenders show the same direction:
expanded error 1.155458 to 1.156345, position error 2.286877 to 2.325801 and defense
error 4.240499 to 4.251906. No origin exceeds the predeclared 5% component-loss
threshold, but passing that tolerance is not permission to adopt flawed roles.

| Forecast target | Reference position runs | Candidate position runs | Matched actual position runs |
| --- | ---: | ---: | ---: |
| 2023 | −348.09 | −415.78 | −508.27 |
| 2024 | −388.51 | −507.64 | −524.38 |
| 2025 | −380.46 | −495.94 | −525.79 |

Shortstop totals were substantially overallocated. The reference grants 150,692,
152,427 and 144,284 SS outs, versus full origin inventories near 129,000. The
candidate respects the position caps. Candidate DH totals are 4,074, 4,799 and
4,797 starts, versus matched actual 4,800, 4,850 and 4,860. Totals look better,
but they do not identify which players change roles. Joint job-cell error improves
in all three targets after the caps; positional and value errors still do not.

For the middle origin, reference total job exposure exceeds available capacity;
the declared rule reduces known defensive job time by 1.14% while leaving batting
PA unchanged. That fills the remaining capacities mathematically, not through a
claim that every job belongs to the known cohort. The other origins retain unused
capacity. Numerical cap residuals are under 0.004 out-equivalent units.

## What the player calculations reveal

The [full walkthrough](../reports/model-evidence/defense-jobs-v14/player-walkthrough.md)
contains nineteen focal cases and 57 origin-selected peer records. The saved
machine-readable cases include source history, actual priors, support, fixed
quality, capacity multipliers and all three forecast paths. The source diagnosis
also preserves raw source identifiers and the actual people supplying each prior.

**Ohtani exposes a fallback defect.** His 2022 origin role evidence is 99.8% DH,
and own-history reliability is 91.1%. The DH-specific group is too thin, so the
fallback borrows the whole league's noncatcher role mix. The candidate grants
about 124 infield outs across 1B/2B/3B/SS despite no such origin evidence. It still
predicts only 118 DH starts against 135 actual. By the 2024 origin, his own record
is entirely DH, yet the candidate invents about 49 infield outs. A capacity check
does not justify these assignments. The earlier source correction helps the
reference DH calculation; it is not evidence for the new allocator.

**Witt shows stale role evidence.** He played 4,181 SS outs and no 3B in 2024.
The weighted role vector nevertheless retains his 1,332 third-base outs from
2022. The candidate forecasts 3,528 SS and 221 3B outs versus actual 4,020 SS and
zero 3B. The reference's 3,898 SS outs was closer. His native-defense forecast is
also low, 5.24 versus 18.16 runs, but this test deliberately keeps skill fixed;
the small role loss must not be described as a failure of all defensive evidence.
Volpe, De La Cruz and Henderson are the origin-selected peers, not handpicked
successes.

**Buxton separates injury use from established position.** His 2023 record is
80 DH starts and no MLB center-field outs; 2024 has 2,301 CF outs and only five
DH starts. The three-year mixture restores 35.1% DH evidence. Reference forecasts
2,378 CF outs and 4.5 DH starts; candidate forecasts 1,510 and 32.4, against
actual 2,919 and eight. This is the largest expanded-value harm, from 1.970 to
1.512 against actual 4.265. Bader, Mullins and Friedl show that the same CF label
does not imply the same health or role history. Contemporary reporting expected
continued CF use after his May 2024 IL return.
[MLB report](https://www.mlb.com/news/byron-buxton-expects-to-play-center-field-in-return-to-twins)

**Schwarber remains a role miss, not an improvement.** The candidate predicts
about 2,000 LF outs and 33 DH starts against actual 123 LF outs and 144 DH starts.
His −7.16 positional runs remain far from −15.77 actual; defense is −7.55 versus
−0.88 actual. Expanded value rises slightly because errors partly cancel, not
because his assignment was correctly forecast. A November 8, 2023 announcement
already identified Schwarber as the predominant DH.
[MLB announcement](https://www.mlb.com/news/bryce-harper-phillies-full-time-first-baseman)
That information was not an input here; it must not be retroactively injected
into these frozen predictions.

**Eldridge shows why primary position is insufficient.** His 2024 fielding is
entirely 1B; earlier RF history is present, but no 2B/3B. The candidate grants
about 46 combined 2B/3B outs. His learned group contains 25 first arrivals, but
many are older multi-position players: Bride already had 2B/3B history, Aranda
played several infield positions and Wagaman had 3B history. Their real future
infield jobs became spurious Eldridge assignments after the input compressed
them all into primary 1B. His detailed profile has zero matching training people.
This does not reject learning prospect position changes; it identifies a lossy
representation. Isaac, Brown and Sanabria remain the origin-selected peers, all
with no MLB contribution that target year.

**Carter is a misleading apparent win.** Expected PA is 426 versus 162 actual.
The candidate lowers his expanded forecast from 2.029 to 1.682 against −0.135
actual, but worsens positional runs from −1.52 to −4.71 against −1.59 actual.
Reducing a positive batting overforecast through an incorrect positional charge
is error cancellation. Pereira and Thompson fail to establish MLB careers that
year; Ramos receives substantial time. The case does not validate any single
outfield assignment recipe.

**The remaining cases keep important gaps visible.** Bailey's 12.46 defensive
runs remain below 31.47 actual, with too little expected PA and fixed quality;
Raleigh's 486 expected PA remains below 705 actual. Kirk is the largest defense
harm: old DH use lowers catching from 2,341 to 2,145 outs versus 2,896 actual.
Rafaela retains excess SS time and understates CF ability. Chourio shifts some
forecast CF time to corners, closer in direction to his eventual assignment, but
still substantially misses the corner role and playing time. Alvarez's 547
expected PA versus 199 actual dominates his false-high value; adding DH cannot
repair that workload error.

Acuña and Judge are the largest false high and low in expanded value. Their
fixed PA and hitting misses dwarf this allocation change. Judge's announced
2024 CF assignment was knowable by December 22, 2023.
[MLB report](https://www.mlb.com/yankees/news/alex-verdugo-embraces-yankees-after-trade)
Hernández is the largest defense-error improvement but still misses his actual
SS usage and negative defense badly. Abrams is the apparently ordinary case:
expanded forecast 1.668 versus 1.668 actual, while defense is −3.95 versus −13.65
runs. Even the well-predicted final value hides offsetting errors.

Reyes remains a partial native measurement, not observed neutral defense or
zero talent. Ohtani's peers include DH-heavy players with very different later
playing time; broad status alone cannot make them interchangeable.

## Disposition and next work

Do not promote this individual allocator. Its tiny total-value loss is not the
reason: unobserved position borrowing, stale assignments and missing dated role
information are substantive baseball failures. Keep the corrected source,
physical feasibility checks, explicit remainder and independent arithmetic.
The old reference remains an accuracy anchor, not a physically complete final
model; its excessive SS totals and too few DH jobs remain unresolved.

The next repair must use the full known repertoire instead of a primary label,
distinguish a current assignment from historical ability or temporary injury
usage, and incorporate dated role evidence where recoverable. First audit the
existing game/position history for those distinctions. Do not run another
algorithm, prior-strength or broad role-bin sweep. No target-informed player
override, forced WAR total or micro-loss veto will close the issue.

All 15 chronological/player-separated folds, 1,849 group tables, 12,432 forecasts,
149,184 fixed native-channel rows and 108 score rows replay independently.
11,380 detailed profiles are sparse and 4,618 are unseen; broad fallback coverage
does not erase that limitation. All 179 unknown-role rows remain unassigned.
Native partial outcomes stay visible. Frozen forecasts, the explorer and 2026
model selection are unchanged. The defense goal and the separate Lovich batting
repair remain unfinished.
