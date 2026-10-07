# Position uncertainty helps some arrivals and obscures others

2026-10-07. Allowing minor SS and CF prospects to reach MLB at other positions
helps Chourio and Holliday, but a role average also moves Volpe and Winn away
from the SS roles they actually retain. The model knows their positions, not
the quality of their defense or their club's intended assignments. That is
the important limitation, not a reason to discard minor fielding information.

The [20 focal and 60 peer traces](../reports/model-evidence/defense-transition-v10/player-walkthrough.json)
contain dated raw fielding records, PA, individual vectors, exact held-player
support, fitted position distributions, restrictions, blend weights, all
position/native forecasts and actual outcomes. All earlier focal cases and
peers are retained. New gain/loss and false-high/low selection uses development
errors; peers use origin information only. Those examples diagnose the model,
not independently confirm it. Outs divided by three are innings; DH starts
are separate and never counted as fielding outs.

## Young players show both sides of the tradeoff

**Chourio after 2023, largest gain:** the latest minor fielding is about 93%
CF and 7% RF. With no MLB PA, the new forecast uses the supported transition
distribution of 79 prior players without an MLB debut at their origin. About
57% of their future fielding is CF, 27% LF and 13% RF, with small other non-C
shares. His unchanged 306 expected PA versus 573 actual yields CF 1,109,
LF 536 and RF 251 outs; the previous forecast was CF 1,824, LF zero and RF
137. Actual is LF 2,171/RF 1,450/CF zero. This is a partial position repair,
not a correct assignment or a solved playing-time forecast.

Anthony and Restituyo do not arrive the following year; their modeled totals
do not change. Alcántara does: CF falls from 469 to 265 outs, with RF 60
against 78 actual and zero CF. This origin-selected peer illustrates the same
corner-transition possibility. Positive opportunities for nonarrivals remain
expectations, not observations that they are poor defenders.

**Holliday after 2023:** 74 supported prior no-debut SS players supply about
53% SS, 32% 2B and 12% 3B. His recent individual record was roughly 82% SS,
16% 2B and 2% 3B. At unchanged 351 expected PA versus 208 actual, SS falls
from 1,864 to 1,218 and 2B rises from 375 to 722 outs. Actual is SS 45/2B
1,379. The direction makes sense but remains too SS-heavy. Arroyo, Williams
and Vera do not arrive; Williams' personal CF evidence is compressed by the
same SS average. The new distribution does not preserve every real secondary
skill or role signal.

**Volpe after 2022, largest loss:** his 2022 AA/AAA source contains 127 SS
starts and 3,337 SS outs, with no other defensive position that season. He
has no MLB PA, so 63 earlier no-debut SS players replace that individual
vector with about 55% SS, 29% 2B and 14% 3B. At unchanged 387 expected PA
versus 601 actual, SS drops from 2,514 to 1,371 outs; actual is 4,040 SS
outs and no other fielding position. This is not fixed by predicting more PA:
the loss includes excessive uncertainty about where he will field.

His peers show why the group is not wholly wrong: Mauricio actually plays
541 outs at 2B and 134 at 3B, with only 6 SS outs, so spreading his former
SS forecast is useful. Neto actually stays at SS and receives 329 PA versus
43 expected; his forecast falls from 277 to 138 SS outs and worsens. Nuñez
does not arrive. A generic SS average cannot distinguish defensive keepers
from movers using a primary position label alone.

**Lawlar after 2022:** expected PA 137 versus actual 34 is unchanged. His
SS forecast falls from 884 to 441 outs, with the remainder mostly at 2B/3B;
actual is 231 SS outs. The smaller delivered error partly comes from spreading
too much total exposure, not getting his actual position right. The separately
reported normalized position score exposes that distinction. Montgomery and
Valentine do not arrive. Winn's SS forecast falls from 800 to 437 against 954
actual, a real deterioration among the preserved peers.

**Basallo after 2024:** his individual minor vector is about 65% C/35% 1B.
The 82-person no-debut C transition prior is about 80% C, so C rises from 803
to 994 outs while 1B falls from 438 to 91. Actual is C 536/1B 54 from 118 PA
versus 196 expected. Less 1B is useful; more C and too little DH are not.
This comparison holds DH starts fixed and cannot solve that exposure defect.
Ballesteros still receives 585 C outs versus 18 actual and only 1.7 DH starts
versus 16 actual. Willems and Lantigua do not arrive. Catcher arrival as a DH
requires separate exposure/role evidence, not a favorable fielding grade.

**Eldridge after 2024:** latest minor fielding is entirely 1B. The 47-person
no-debut 1B prior is 72% 1B, about 14% LF and 5% RF, with small IF shares.
The unchanged scalar forecast distributes 352 potential outs into 254 at 1B,
49 LF, 18 RF and other small non-C roles. Actual is 102 at 1B plus six DH
starts. That reduces delivered error but does not establish a credible LF/IF
assignment for this specific player. His latest personal role and fuller
defensive profile are underused. Isaac, Ortiz and Clifford do not arrive;
Clifford's real 1B/OF mixture is also replaced by the same dominant-role mean.

## Tiny MLB catching samples remain much better than the old ratio

**Álvarez after 2022:** 14 observed MLB PA gives individual usage just 12.3%
weight, while the 130-person prior-MLB C group is about 97% C. Predicted C
outs move from the prior repair's 2,282 to 2,217 versus 2,621 actual; the
original PA-ratio anchor was only 1,081. This preserves the useful tiny-sample
repair but the extra position spreading is not an improvement in his case.
Naylor receives 1,504 versus 1,517 C outs, O'Hoppe 1,156 versus 1,276, and
Pineda does not arrive. Their small non-C allocations are probabilities from
catcher transitions, not evidence of their individual non-C defensive talent.

## MLB players retain their main roles but dated plans are still missing

Three years of weighted MLB PA give these established players roughly 80–92%
individual position weight. The scalar playing-time forecast is unchanged.
The new non-C tails are possible-role probabilities; they are not borrowed
catcher innings or declarations that each player can defend every position.
Some tails remain unhelpfully broad for a specific established player.

| Player and origin | Previous repair to transition forecast | Actual next season | Baseball judgment and preserved peers |
| --- | --- | --- | --- |
| Guerrero 2022 | 1B 2,995 to 2,955, C stays zero | 1B 3,195 | Small regression; Pratto's OF mixture persists, Toglia loses too much RF, Garcia does not arrive. |
| Bohm 2022 | 3B 2,700 to 2,643; 1B 212 to 210 | 3B 2,059; 1B 1,659 | Still misses increased 1B use. Devers/Hayes/Riley remain mainly 3B, but added alternate-position tails do not solve their PA shortfalls. |
| Springer 2022 | CF 1,809 to 1,748; RF 134 to 152 | CF 6; RF 3,413 | Missing announced RF move, not lack of defensive talent. Kiermaier remains CF with too little PA; Hicks' CF/LF mix is plausible; Ortega's tiny own C history remains distinct from donated C. |
| Varsho 2022 | C 673 to 597; CF 1,014 to 934; RF 1,237 to 1,321; LF 53 | LF 2,453; CF 1,387; no C/RF | The dated LF plan is still absent. McCarthy's RF increases in a useful direction; Lowe's PA shortfall and Trammell's LF/RF mismatch remain. |
| Betts 2023 | RF 1,914 to 1,927; 2B 1,070 to 986; SS 213 to 197 | RF 1,014; 2B 315; SS 1,594 | Role average cannot anticipate the assignment. García/Kepler stay mostly RF; Hernández's real LF shift is still largely missed. |
| Schwarber 2023 | LF 2,010 to 1,950; DH stays 38 starts | LF 123; DH 144 starts | Historical LF evidence does not predict the later DH plan. Profar/Gurriel remain LF but their PA errors persist; Yelich plays less than expected. |
| Soto 2023 | LF 3,146 to 3,075; RF 444 to 453 | LF 156; RF 3,833 | A tiny improvement does not solve the RF assignment. Baddoo plays much less, Burleson much more with extra DH, and Kwan retains mostly LF. |

The dated plans and later injury distinctions were verified in the preceding
[player review](defense-repertoire-v9-player-review.md), which this comparison
does not replace or claim to have added as inputs. No later news is used to
manually adjust these forecasts.

## Absence and return cases do not become talent labels

**Hoskins after 2022:** 1B falls from 3,065 to 3,019 outs with unchanged 536
expected PA; actual is zero after the later injury. Spreading a little into
other positions lowers squared error for the wrong reason in this case. Sanó
also has zero; Bell still receives too much 1B relative to actual DH use, and
Olson's 3,684 1B outs remains below 4,278 partly because PA is too low. Do not
describe the absence as an identified lack of defensive ability.

**McLain after 2023, false high:** SS/2B becomes 2,203/1,162 outs versus zero
actual, with 599 expected PA unchanged. The later injury was not known at the
earlier cutoff. Peraza, Soto and Peguero also have large PA overforecasts;
reallocating their IF roles cannot solve those delivered-time errors.

**Tatis after 2022, false low:** the return now uses actual older MLB SS/OF
evidence rather than only minor rehab SS. Weighted MLB evidence PA is 337.25,
giving individual roles 77.1% weight. But the old cache still forecasts only
40 PA: SS 205/RF 29/CF 11 outs versus actual RF 3,526/CF 90. The known finite
return and intended role remain upstream/dated-context problems. Hernández and
Zamora do not arrive, while Williams receives 112 PA versus 2.4 expected;
their old stage labels do not make them comparable established returners.

**Valera after 2022:** expected PA 213 and potential fielding 1,241 outs stay
unchanged, now more spread across OF. Actual is zero, as for Rhodes, Pages
and Infante. Reduced concentration can improve delivered squared error without
knowing anything new about fielding ability or fixing arrival calibration.

**Dennis Santana after 2022:** no own nonpitching repertoire exists, so no
nonpitching position is assigned. Guerra, McKay and the preserved unnamed-ID
peer remain similarly unknown. These legacy pitcher/cohort cases are not
new discoveries of bad hitter defense.

**DJ Peters after 2023, recovered return:** the last older MLB outfield record
removes the prior unknown-repertoire state. The same 35.379 potential outs
are now allocated mainly CF/LF/RF instead of left unallocated; expected PA
remains 6.2 and actual is zero. The separate
[return-history trace](../reports/model-evidence/defense-transition-v10/return-history-review.json)
completes three outcome-blind comparisons: Sierra and Crook also do not return;
Hicklen receives five PA/36 RF outs, versus 8.5 expected PA and a more CF-heavy
forecast. This recovers evidence, not a successful arrival prediction.

## Decision

The comparison passes its development numerical tolerances and partly improves
prospect placement. It does not solve individual role development, dated plans,
PA or future MLB defensive quality. Volpe/Winn/Neto demonstrate genuine lost
individual information; Lawlar/Hoskins demonstrate superficially improved
delivered scores from dilution. Rare young exposure also remains a 2025 stress
failure. Retain the position-distribution code as qualified research, not a
full production allocator. No further position algorithm or constant sweep:
next measure whether the separately reviewed defensive-quality histories help
delivered runs and expanded player value on matched targets, with position and
opportunity limitations visible.
