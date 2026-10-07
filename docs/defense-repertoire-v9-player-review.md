# Observed positions help regulars but constrain prospect development

2026-10-07. The repair removes donated positions and stabilizes tiny MLB
defensive-time ratios. It improves the full historical score, but it cannot yet
serve all hitter profiles: concentrated minor-league roles miss real MLB position
changes. The distinction is visible in actual players, not just group statistics.

The [16 focal and 48 peer calculation traces](../reports/model-evidence/defense-repertoire-v9/player-walkthrough.json)
retain all earlier diagnostic cases and peers. Each trace has the raw position
records, current MLB and fallback vectors, their sample weights, actual scalar
group support, total-outs/PA shrinkage arithmetic, PA, all five forecast vectors,
native opportunities, and actual position usage. The additional
[young-player traces](../reports/model-evidence/defense-repertoire-v9/young-profile-diagnosis.json)
include four focal cases and 12 origin-selected peers, with overlap retained.
No unsuccessful player was removed, and none of these outcome-selected examples
is independent confirmation.

## What the repair fixes

**Guerrero after 2022:** 706 origin MLB PA gives the current MLB record 87.6%
weight. The group prior is 5.291 fielding outs/PA from 85 people, about 46
effective people. Fixed expected PA remains 621. Current and older repertoires
are almost entirely 1B; the repair predicts 2,995 1B outs versus actual 3,195.
The ratio anchor predicts 2,955. No C/LF/RF exposure is borrowed from his peers.
Pratto and Toglia retain their own observed OF/1B mixtures; Garcia does not
arrive. The repair does not turn their broad age/role resemblance into Guerrero's
position assignment.

**Álvarez after 2022:** just 14 origin MLB PA gives that tiny MLB ratio 12.3%
weight, with the fuller minor catching record defining his repertoire. His
supported catcher prior is 6.312 outs/PA from 125 people, about 65 effective.
The unchanged 388 expected PA produces 2,282 C outs, compared with 1,081 from
the ratio anchor and 2,621 actual. No arbitrary manual player correction is
used. Naylor's 1,560 versus 1,517 C outs and O'Hoppe's 1,210 versus 1,276 also
look reasonable; Pineda's positive expectation accompanies nonarrival, not a
measured poor catcher grade.

**Bohm after 2022:** 631 origin PA makes current 3B/1B usage dominant. The repair
predicts 2,700 3B and 212 1B outs, rather than donating 2B/SS/C exposure. Actual
is 2,059 3B and 1,659 1B: increased 1B usage still goes largely unpredicted.
Devers, Hayes and Riley now remain concentrated at 3B; their PA forecasts explain
part of their underprediction. Tiny older alternate-position observations still
produce tiny alternate allocations, clearly distinct from substantial group-
donated innings.

**Hoskins after 2022:** 672 origin PA gives current 1B usage 87.0% weight. The
repair forecasts 3,065 1B outs and no catcher innings. Actual is zero after a
later March injury; the forecast cannot know that injury at the earlier cutoff.
Sanó also does not play; Bell's forecast stays too 1B-heavy relative to his
actual DH use; Olson's 3,744 1B outs is below actual 4,278, partly from projected
616 versus actual 720 PA. These are different reasons for misses, not evidence
to lower all their defensive talent. Dated injury context is in the previous
[player review](defense-opportunity-v8-player-review.md).

**Eldridge after 2024:** with no MLB PA, his most recent minor season controls
the repertoire. All its fielding is at 1B, so older RF no longer supplies OF
exposure and group averages cannot invent C. The 55-person, 29-effective-person
1B/upper-minors prior gives 352 predicted 1B outs from 68 expected PA. Actual
is 102 outs from 37 PA plus 6 DH starts. The role is reasonable; total opportunity
and DH use remain misses. Isaac, Ortiz and Clifford keep their own 1B/OF evidence
and do not arrive the following season. This does not settle any player's
eventual talent or control-period value.

## Improvements that still leave important misses

**Soto after 2023, largest gain versus the ratio anchor:** current LF history
dominates, but the older repertoire supplies some RF exposure. The repair gives
3,146 LF and 444 RF outs, compared with ratio LF 3,613/RF zero. Actual is LF 156
and RF 3,833. A useful partial gain is not a correct assignment. Baddoo remains
mostly LF but has far less actual PA than projected; Burleson keeps his 1B/OF
mix and receives more PA/DH than projected; Kwan's 2,931 LF versus 2,970 actual
is close. Different observed repertoires now stay different.

**De La Cruz after 2022:** the recent minor SS/3B repertoire yields 605 SS and
168 3B outs from 119 expected PA. The old ratio fallback gives 330 SS/174 3B
plus unrelated roles. Actual is 1,773 SS and 777 3B from 427 PA. Most of the
total shortfall remains upstream PA; the SS/3B split is also imperfect. Winn's
800 predicted versus 954 actual SS outs is more successful, while Martinez and
Hernaiz do not arrive. None is a zero defensive-talent label.

**Springer and Varsho after 2022:** personal repertoires remove donated IF/C
positions for noncatching OF peers, but cannot recognize a new assignment from
old usage alone. Springer is still forecast primarily CF (1,809 outs versus
actual 6) rather than RF (134 versus 3,413). Varsho gets 673 C outs from real
older C evidence but catches none, while his announced LF assignment is missing.
Kiermaier's main CF role is retained but PA is too low; Hicks' main CF/LF mix is
plausible but misses RF; Ortega's broader personal history retains a tiny C
component rather than one donated by other players. McCarthy/Lowe/Trammell keep
their individual OF mixtures, with Lowe's large PA shortfall unchanged.
The dated Toronto plans were available by the forecast cutoff; this is an
omitted role input, not an unavoidable statistical surprise.

**Betts and Schwarber after 2023:** the repair concentrates forecasts in their
observed repertoires but does not solve future assignments. Betts receives
1,914 RF, 1,070 2B and 213 SS outs; actual is 1,014/315/1,594. His December 2B
plan and later March SS revision require different cutoff handling. García and
Kepler are now concentrated in RF, which fits their actual roles; Hernández
still shifts to LF in a way the current-year RF record does not foresee.
Schwarber receives 2,010 LF outs and only 38 DH starts versus actual 123/144;
Profar and Gurriel preserve LF, while Yelich plays less than projected. More
accurate concentration alone cannot replace dated role updates.

## Absence and population limits

**McLain after 2023, largest false high:** 403 origin PA gives current MLB
SS/2B usage 80.1% weight. The repair predicts 2,130 SS/1,328 2B outs from 599
expected PA, but actual is zero after a later shoulder injury. That does not
invalidate a pre-injury talent estimate. Peraza, Soto and Peguero also receive
much more expected PA than actual; their own IF repertoires are retained, not
replaced with a common skill judgment.

**Tatis after 2022, largest false low:** the old cache still supplies only 40
expected PA. The latest minor rehab record makes the repertoire SS; the repair
predicts 259 SS outs versus actual 3,526 RF plus 90 CF. This is both an upstream
finite-return defect and insufficient assignment evidence. Hernandez/Zamora do
not arrive, while Williams gets 112 PA against 2.4 expected. These stage-matched
peers are not equivalent to an established player returning from suspension.
The repair does not close that previously identified production problem.

**Valera after 2022:** 213 expected PA produces 1,241 outs in his observed OF
repertoire; actual is zero, as for Rhodes, Pages and Infante. Nonarrival remains
an opportunity outcome, not observed MLB quality. Concentrating the same expected
opportunities increases squared error for some nonarrivals even when the positions
themselves are sensible. That tradeoff must be judged with arrival calibration,
not hidden by dropping them from the test.

**Dennis Santana, unknown repertoire:** he is a pitcher-only member of the older
batting cache, not an anonymous ordinary position player. The broad old fallback
assigns about 198 nonpitcher fielding outs; the repair does not manufacture a
nonpitching role. Guerra and McKay also have no recent usable nonpitcher
repertoire and no following-season defense in these eight positions. The third
peer lacks a sourced display name and remains identified by player ID in the
trace. This illustrates a legacy cohort limitation; it is not a new skill gain
or a reason to call all unknown players poor defenders. Across all folds, 267
unknown-repertoire forecasts retain 1,703 potential outs explicitly unallocated.

## Young players explain the failed practical check

Origin ages 15–19 are sparse in actual MLB exposure. Their position-cell RMSE
increases from 5.49 to 8.60 outs in the 2023 target, 28.75 to 38.75 in 2024,
and 4.94 to 7.80 in 2025. The relative increases are large, but their absolute
size and sparse actual contributors matter. Four players explain about 95.5%
of the summed increase across these origins; that concentration calls for
case review, not either a blanket rejection or deletion of those players.

**Chourio after 2023, largest deterioration:** at 306 expected PA versus 573
actual, the repair puts 1,824 outs in CF and 137 in RF. Actual is 2,171 LF and
1,450 RF, with zero CF. His minor CF record is real, but it is not a permanent
MLB assignment. Anthony and Restituyo do not arrive; Alcántara arrives briefly
in RF rather than his forecast CF. The same OF-development issue appears in
an origin-selected peer, not just the largest famous miss.

**Holliday after 2023:** 351 expected PA versus 208 actual produces 1,864 SS,
375 2B and 39 3B outs. Actual is 45 SS and 1,379 2B. The error is partly PA,
but mainly failure to shift his real minor SS experience toward his MLB 2B role.
Arroyo, Williams and Vera do not arrive the next season. Their nonarrival does
not establish that their SS skills cannot carry later.

**Lawlar after 2022:** all recent fielding is SS. The repair forecasts 884 SS
outs from 137 expected PA, versus actual 231 SS outs from 34 PA. This is chiefly
an opportunity overprediction, not a position-transition failure. Montgomery
and Valentine do not arrive, while Winn's 800 SS outs versus 954 actual is
reasonable. The same allocation recipe can be sensible yet miss delivered time.

**Basallo after 2024:** observed C/1B shares produce 803 C and 438 1B outs from
196 expected PA; actual is 536 C and 54 1B from 118 PA plus 7 DH starts. The PA
forecast and position mix both overstate fielding. Ballesteros' actual 18 C/12
1B outs and 16 DH starts show that a minor catcher/1B can arrive mainly as a DH;
his 592 C/70 1B forecast misses this sharply. Willems and Lantigua do not arrive.

## Decision

Retain the repair as useful research code, not a general integrated forecast.
It fixes a genuine allocation defect and improves established-player and measured
native-opportunity accuracy. It fails the locked young-profile tolerance and
misses real development/assignment paths. The next repair needs supported
position-transition uncertainty for inexperienced players while allowing strong
MLB evidence to retain individual roles. It must retain the no-donated-catcher
guard and the simple ratio anchor, not undo the source repair or tune around
Chourio/Holliday. Dated plans and upstream PA remain separate inputs. No expanded
value comparison starts before this review closes, and no frozen forecast changes.
