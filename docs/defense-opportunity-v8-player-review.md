# Defensive time forecasts need a better position allocation

2026-10-07. This review covers 13 focal players and their 39 comparisons selected
from information available at the forecast origin. It traces the same fixed
playing-time forecast through four position-allocation methods. These are
next-season defensive opportunities, not grades of defensive talent.

The simple PA-scaled prior-season usage is more accurate overall than either
learned role average. The learned averages also spread innings into unrelated
positions. That failure prevents their use as a general value layer, even though
the contextual version meets the contract's numerical tolerances.

## What each number means

Position forecasts are fielding outs, with three outs equal to one defensive
inning. DH is games started, not defensive outs. The fixed PA estimate already
includes the chance of not playing in MLB. It is not conditional full-season PA.
Native catcher pitches, throwing/blocking chances, OF advancement chances and
received 1B throws are separately estimated opportunities, not defensive runs.

[The complete calculation](../reports/model-evidence/defense-opportunity-v8/player-walkthrough.json)
contains every 2020–origin source row, MLB/minor starts and outs, weighted role
fractions, chosen empirical rates and actual distinct/effective training people,
all four forecast vectors, five native-opportunity outputs and actual position
usage for each focal player and peer. The three-year weights are 1, 0.5 and 0.25.
The origin uses no following-season fielding or actual PA. Actual-PA rescaling is
an explanation probe only, never a replacement forecast.

## Established players and planned moves

**George Springer, after 2022, largest gain over the pooled role average.**
Prior three-year starts are 64.7% CF, 1.8% RF and 33.5% DH. Fixed expected PA is
469, versus 683 actual. The context branch has 76 CF-role peers but only 17
effective people, reflecting uneven exposure. It moves expected CF outs from
1,175 to 867 and RF from 455 to 606. Actual is 6 CF and 3,413 RF outs. The change
is in the right direction but far too small; it also assigns 100 catcher outs.
It is not an adequate role forecast merely because it is the largest paired win.

The comparison set shows the distinction. Kiermaier gets 202 expected PA versus
408 actual and 636 predicted CF outs versus 2,944 actual; both workload and
allocation are low. Hicks' total of 1,819 versus 1,953 is much closer, but CF/LF
allocation remains diffuse. Ortega's total of 936 versus 930 is close, showing
that correct total exposure does not establish correct position shares.

**Daulton Varsho, after 2022.** His origin starts include C 23.1%, CF 31.2%, RF
34.8%, LF 2.3% and DH 8.6%; the model genuinely observes a mixed player rather
than a full-time catcher. At 528 expected PA versus 581 actual, context predicts
777 C, 423 LF, 840 CF and 825 RF outs. Actual is 2,453 LF and 1,387 CF with zero
catcher outs. More historical C evidence raises C exposure relative to the
PA-ratio anchor instead of recognizing his new assignment. His noncatching OF
peers McCarthy, Lowe and Trammell also receive spurious small C allocations.
Lowe's 205 predicted versus 501 actual PA is a separate large opportunity miss;
McCarthy and Trammell do not have that same pattern.

Toronto had announced Varsho primarily in LF, Kiermaier in CF and Springer in RF
by December 24, 2022. [The dated MLB report](https://www.mlb.com/bluejays/news/daulton-varsho-traded-to-blue-jays)
therefore identifies a missing available input, not an unforeseeable move.
It does not justify adding their eventual innings or a name-based override.

**Mookie Betts, after 2023.** Three-year starts are 66.3% RF, 26.4% 2B and only
4.8% SS, with 2.5% CF. Expected PA 576 is reasonably close to actual 516. Context
predicts 1,193 RF, 696 2B and 155 SS outs, plus unrelated LF/1B exposure. Actual
is 1,014 RF, 315 2B and 1,594 SS. Workload is not the main explanation: the role
distribution is wrong. His RF-dominant peers García and Kepler have no measured
2024 catcher innings despite receiving small C allocations; Hernández changes
between LF and RF, a much more plausible OF transition than learning C/1B/3B.

Betts' everyday 2B plan was announced on December 4, 2023; the SS change followed
on March 8, 2024. Those are different information dates. A December/January
forecast should use the first, not the second; an Opening Day update should
incorporate the later plan. [December plan](https://www.mlb.com/dodgers/news/mookie-betts-second-base-dodgers-2024),
[March change](https://www.mlb.com/news/mookie-betts-dodgers-shortstop).

**Kyle Schwarber, after 2023.** Weighted starts remain 73.4% LF and 25.8% DH,
with a small older 1B share. Fixed PA is 522 versus 692 actual. Context raises
LF exposure from 1,151 pooled outs to 1,371 while predicting only 26 DH starts.
Actual is 123 LF outs and 144 DH starts. The PA-ratio anchor also misses, at
1,897 LF outs. Context additionally assigns 70 C outs despite no recent C role.
Profar's 319 versus 668 PA explains much of his low total; Gurriel's 518 versus
553 PA is close but his LF concentration is lost; Yelich's actual PA 315 is
below projected 490 and his total consequently goes the opposite direction.

The primary-DH plan was reported on February 21, 2024, after the historical
January information date. It supports an offseason-update requirement, not a
retroactive January input. [Dated plan](https://www.mlb.com/news/kyle-schwarber-ready-for-2024-after-injury).

## Ordinary cases and deterioration

**Alec Bohm, after 2022, ordinary active case.** Three-year starts are 91.3% 3B,
4.4% 1B and 4.3% DH. At 508 expected PA versus 611 actual, context predicts
1,815 3B and 324 1B outs. Actual is 2,059 3B and 1,659 1B. The method gets his
main position but cannot identify the increased 1B assignment. It also spreads
354 outs to 2B, 143 to SS and 24 to C. His 3B peers Devers, Hayes and Riley are
under-concentrated at 3B in the same way. Riley's 564 versus 715 PA adds a
workload shortfall; Devers' PA is much closer, so his allocation failure cannot
be blamed primarily on PA.

**Vladimir Guerrero Jr., after 2022, largest deterioration.** His starts are
79.5% 1B and 20.5% DH. Expected PA 621 versus actual 682 is not an extreme miss.
Context reduces 1B from 2,194 pooled outs to 1,728 while assigning 696 LF, 294 RF
and 130 C outs. Actual is 3,195 1B and zero outs elsewhere. The ratio anchor's
2,955 1B outs is much more sensible. Age-conditioned role averages borrow
young players' broader future usage instead of recognizing his concentrated
current position. Pratto and Toglia have much smaller PA forecasts, 245/148
versus 345/152 actual; Garcia does not arrive. None establishes that Guerrero
should be spread across unrelated positions. These peers are chosen by broad
role/age/exposure, not equivalent MLB establishment; that limitation matters.

## Absences and returns are not defensive talent labels

**Rhys Hoskins, after 2022, exit.** Origin starts are 97.8% 1B and 2.2% DH.
Expected PA is 536; actual is zero. Context predicts 2,143 1B outs but also 89
C outs, with 135 2B and 235 3B. The ACL injury occurred March 23, 2023, after
the forecast date; it explains zero delivered value without implying poor
defensive ability. [Dated injury](https://www.mlb.com/news/rhys-hoskins-suffers-left-knee-injury).
The false catcher allocation remains a model defect regardless of that injury.
Sanó also has zero future exposure but much lower expected PA; Bell becomes
more DH-heavy; Olson remains at 1B. Group averaging spreads all three instead
of preserving these distinct roles.

**Matt McLain, after 2023, largest false high.** The actual origin mix is 64.5%
SS, 31.2% 2B and 4.3% DH. Context forecasts about 1,974 SS and 966 2B outs from
599 expected PA; actual is zero. His March 2024 shoulder injury/surgery is later
information, not evidence that those January talent expectations were absurd.
[Dated injury](https://www.mlb.com/news/matt-mclain-shoulder-surgery).
The peer forecasts also reveal distinct risk: Peraza, Soto and Peguero receive
320/221/249 projected PA but only 11/16/10 actual. Those are role/arrival misses
that cannot be repaired by lowering everyone's defensive quality.

**Fernando Tatis Jr., after 2022, largest false low.** The cached upstream
forecast supplies only 40 expected PA despite older SS/RF history; actual is
635. Context gives 117 SS and 14 RF outs, against actual 3,526 RF and 90 CF.
This repeats a known limitation of the older PA cache, not evidence against
defensive opportunity forecasting. A finite suspension return must be distinct
from loss of talent or general inactivity. The anticipated April 20 return was
public in October 2022. [Dated return expectation](https://www.mlb.com/news/fernando-tatis-jr-return-date-from-suspension-in-2023).
The stage-matched peers Hernandez and Zamora do not arrive; Williams gets 112 PA
despite only 2.4 expected. Their matching stage does not make them comparable
to a previously established superstar returning from a known suspension. Do not
carry this cache's miss forward as a validated current-production output.

## Prospects and sparse MLB samples

**Francisco Álvarez, after 2022.** Combined starts are 67.0% C and 33.0% DH;
the model observes the substantial minor catching record. Fixed expected PA is
388 versus 423 actual. Context predicts 1,608 catcher outs, compared with 1,670
pooled and only 1,081 from scaling his tiny prior MLB usage. Actual is 2,621 C
outs. The prior MLB ratio is noisy and his minor DH starts pull down catching
too strongly. Naylor and O'Hoppe arrive and have reasonably close total exposure;
Pineda does not. That is useful differentiation of opportunities, not proof
that Pineda has poor catching skill. The benchmark needs a stable newcomer
fallback rather than blindly scaling a handful of MLB PA.

**Elly De La Cruz, after 2022.** Starts are 63.6% SS, 27.6% 3B and 8.8% DH.
At 119 expected PA versus 427 actual, context predicts 273 SS and 162 3B outs;
actual is 1,773 SS and 777 3B. Context gives 192 outs to 2B, diluting his known
SS/3B history. The actual-PA-only sensitivity raises context total from 748 to
about 2,684 outs: most of the total shortfall comes from PA, while allocation
remains wrong. Martinez and Hernaiz do not arrive; Winn arrives with 137 PA
versus 123 expected. Future nonarrival does not supply a zero talent label.

**Bryce Eldridge, after 2024.** Starts mix recent 1B with older RF and DH:
76.0% 1B, 9.9% RF and 14.1% DH. Fixed expected PA is 68 versus 37 actual.
Context predicts 173 1B outs, 56 LF, 43 RF and 26 C, against actual 102 1B outs
and 6 DH starts. His 2024 raw position rows are all at 1B; older RF exposure
should not be confused with a new major-league OF assignment. The catcher
allocation is borrowed group usage, not evidence he can catch. Isaac, Ortiz
and Clifford do not arrive; their projected PA is 46, 5 and 4. This is a
next-season check, not a verdict on their eventual MLB value or defense.

**George Valera, after 2022, prospect nonarrival.** Origin starts are RF 53.9%,
LF 26.1%, CF 11.5% and DH 8.6%. Fixed expected PA 213 produces 1,255 context
outs; actual is zero. Rhodes, Pages and Infante also do not arrive in the next
season. This cluster exposes an upstream opportunity issue for this cohort;
it provides no measured MLB defensive quality. The positive forecast is an
expectation that sometimes accompanies nonarrival, not necessarily a position
bug. Its spurious C/IF allocations are a separate structural problem.

## Cross case judgment

The empirical means replay exactly, but their design is not sufficiently
specific. A player with a little historical 1B or DH use contributes his entire
future position vector to that group's mean. Mixing those means again spreads
future exposure across roles that the forecast player never held. This is not
a data-join bug and not a scientific rejection of age or position development.
It is an inappropriate general allocation rule for the intended value layer.

Aggregate totals can conceal this problem. In each test year, context allocates
roughly 14,800–17,100 catcher outs to players with zero origin catcher share;
the matched actual C total for those people is zero. Full matched defensive
totals are within 3.3% of actual, yet new/returning defenders receive only about
half their actual combined exposure. Overpredictions for exits and nonarrivals
offset those deficits. The subgroup outcomes are diagnostic, not information
available when making a forecast.

The disposition is **repair the role allocation before value integration**.
Retain the tested skill baselines, audited sources and native opportunity
conversions. Keep the ratio anchor as the strongest established-player reference,
but do not claim its broad newcomer fallback is deployment-ready. The next
bounded repair should preserve a player's observed position repertoire, separate
total fielding exposure from its allocation, stabilize tiny MLB ratios using
the fuller minor position record, and distinguish dated assignment information
from statistical development. No model or explorer is changed by this review.
