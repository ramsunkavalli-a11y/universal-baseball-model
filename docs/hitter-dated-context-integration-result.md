# Preseason corrections help appearance estimates but do not finish the hitter model

2026-10-04. The fixed context comparison and thirteen player reviews are
finished. Updated roster, missing-position and one missing-age input improve
historical appearance probabilities. Workload and delivered-value gains are
small and uncertain, and one major deterioration exposes a roster-date conflict.
Do not deploy this candidate. Keep the existing forecast unchanged while
reconciling status evidence and integrating the collected foreign performance.

## What was tested

The comparison preserves 63,282 source origins and 30,506 forecasts, including
non-arrivals, across seven origins and five whole-player folds. It uses the same
251 inputs, shallow boosting settings and availability policy as the current
opportunity model. Only returned dated reserve listings, unambiguous missing
positions and verified missing age may change. There are 395 changed source
origins and 182 changed forecast rows. The hitting forecast is held fixed.
Japan and Korea production is not yet an input to these fits.

Every old and new head was replayed: 140 head checks, with all source changes
independently reconstructed. Actual MLB counts and both league references were
rebuilt from dated stints. The initial review's value label was wrong; its files
remain preserved under the [scoring amendment](hitter-dated-context-scoring-amendment.md).
The corrected target is batting plus replacement relative to the target season,
in custom wins, not full WAR. No model was refitted to repair scoring.

## Matched results and uncertainty

| Population and measure | Current | Corrected context |
| --- | ---: | ---: |
| All forecasts PA RMSE | 60.499 | 60.331 |
| All forecasts appearance Brier | .033540 | .033108 |
| All forecasts appearance log loss | .114736 | .113290 |
| All forecasts relative contribution RMSE | .435133 | .434977 |
| Public matched PA RMSE | 138.330 | 138.055 |
| Public matched PA MAE | 106.411 | 106.135 |
| Public matched relative contribution RMSE | 1.023981 | 1.024965 |

Scores weight origins equally. The 2,627 public matches are unchanged; matched
Steamer PA RMSE is 135.379 and MAE 92.083. The candidate MAE is still 15.26%
worse, outside the unchanged 15% engineering allowance. The much smaller
all-population error includes many non-arrivals and is not comparable to a
public major-leaguer-only headline.

Paired 2,000-resample whole-player intervals give an all-population PA MSE
change of -20.285, with nominal 95% interval [-49.554, +8.778]. Relative-value
MSE changes -.000136, interval [-.000977, +.000690]. Both include harm.
Appearance improvements are clearer: Brier changes -.000433, interval
[-.000694, -.000168], and log loss -.001446, interval [-.002210, -.000717].
These are exposed historical development results, not independent confirmation;
the intervals do not cover shared season shocks or repeated experiment selection.

PA improves in five of seven origins but worsens in 2021 and 2024. Relative
contribution RMSE worsens in four origins. Upper never-debut expected PA remains
74,610 against 92,891 observed; lower never-debut expected PA remains 6,940
against 5,194. The changed-context group's PA total moves from 36,402 to 44,069
against 41,687 actual, but its value MAE worsens and expected contribution rises
to 134.97 against 114.91. A better appearance score is not proof of correct
workload, hitting or value calibration.

## Player review and baseball judgment

Exact dated statistics, all 251 old/new inputs, tree-path terms, head outputs,
training profiles, policy and four outcome-blind peers per case are saved in
the private reviewed-cases.json. The [arithmetic walkthrough](../reports/model-evidence/hitter-dated-context-integration/player-walkthrough.md)
contains the same intermediate forecasts and histories. Path terms explain
model arithmetic, not causation. The same fitted candidate was also evaluated
on each player's old inputs to separate own-input mechanics from refitting.
That diagnostic is not a new validated forecast arm.

### Foreign professionals

Hyeseong Kim before 2025 has 1,754 observed KBO PA in three years but no recent
domestic batting. Age changes from imputed 27 to 25.93 at origin December 31,
unknown position becomes second base and the listing becomes positive. Expected
PA rises .36 to 19.82: appearance .00473 to .19777 times conditional PA 76.42
to 100.23. Almost all +19.46 PA comes from his own corrections. Actual PA is
170. The new conditional head still subtracts about 100 PA through zero
domestic work; KBO production is absent. His exact broad training profile has
only two participation people and one conditional-workload person. His four
nearest domestic peers all have zero future PA; this is a poor comparison group
for an established Korean professional, not proof his forecast should be zero.

Jung Hoo Lee before 2025 has 158 MLB PA in 2024 and 1,014 KBO PA in the preceding
two years. His own inputs do not change. Expected PA moves 153.65 to 166.96
entirely from refitting, with .8112 appearance probability and 205.82 conditional
PA, against 617 actual. The 158-PA domestic work feature subtracts about 77 PA
in the conditional head. The unchanged hitting estimate is -.646 custom wins
per 600 versus +.463 observed. Foreign experience and the meaning of a shortened
first MLB season remain missing, not repaired by the small numerical gain.
His closest domestic peers include a non-arrival and low-workload seasons;
they do not establish that all similar domestic players should receive 600 PA.

Ha-Seong Kim before 2023 has 298 and 582 MLB PA in the two preceding seasons,
plus 622 KBO PA in 2020. Expected PA barely moves 445.74 to 445.50, entirely
from refitting, against 626 actual. Recent domestic work contributes about
138 conditional PA and appearance is .9872. The fixed batting estimate is
-.635 versus +.513 observed, so most of his 1.57 contribution shortfall is
hitting rather than opportunity. This context-only test cannot repair that
rate estimate, and substantial MLB evidence must eventually outweigh older KBO
evidence. Broad foreign-profile support is only five and three people.

Eric Thames before 2017 has 1,638 observed KBO PA in three years, including
40 HR and 103 K in 529 PA in 2016, but no domestic PA in that window. His
positive listing already exists; no own source input changes. Refitting moves
expected PA 20.78 to 25.16, against 551 actual. Zero recent domestic MLB/work
inputs subtract roughly 69 and 48 conditional PA; KBO production remains unused.
The unchanged -.711 batting estimate misses +2.423 observed. His reviewed
foreign/inactive conditional-training profile has zero people. Ordinary former
domestic hitters with no recent domestic PA all fail to return; they cannot
stand in for this professional experience. The missing representation affects
both talent and opportunity, not just one multiplier.

### Established and developing hitters

Aaron Judge before 2025 has recent MLB seasons of 696, 458 and 704 PA, with
62, 37 and 58 HR. His own inputs stay fixed. Expected PA changes 530.75 to
531.16 against 679; .9911 participation is not the main limitation. Recent
work and production raise conditional PA, while age contributes about -34 PA.
His contribution miss has +1.68 opportunity and +1.53 hitting terms. Nearest
age/workload peers also generally receive more PA than predicted, but neither
his exceptional actual year nor these few comparisons justify removing all
age/attrition regression. This workload gap remains in the full benchmark.

Nick Kurtz before 2025 has only 50 professional PA: 35 at A with four HR and
15 at AA. College-draft pedigree and a current top-100 ranking are already
inputs; they were not absent. Ranking raises the conditional head by about
73 PA and participation log odds by 1.32, but no reserve listing and zero MLB
work still leave .0549 appearance times 166.23 conditional PA, or 9.13 expected
PA, against 489 actual. The old forecast was 10.18. This is a consequential
readiness miss, not a new source correction. The closest peers were chosen
without pedigree/production in the distance and all have zero future PA; their
failure highlights the limits of that diagnostic comparison. Thousands of
broad age/stage peers do not establish elite thin-sample support.

Steven Kwan before 2022 has 221 AA and 120 AAA PA in 2021, with 31 K and
12 HR combined; the missing 2020 MiLB season is not zero production. Expected
PA falls 115.97 to 110.37 solely from refitting, against 638 actual. Appearance
remains .6765, but conditional PA is just 163.14. AAA batting role helps while
zero MLB work subtracts about 103 conditional PA. The fixed hitting estimate
is -.253 against +1.618 observed. The peer group includes a non-arrival and
several short debuts, so the miss does not establish universal regular workload
for similar prospects. It does show that this roster change does not address
the strong-production newcomer problem.

Junior Caminero before 2025 has 177 MLB PA and 236 AAA PA in 2024; his prior
AA season included 20 HR in 351 PA. Previous top-prospect evidence adds about
86 conditional PA, while short current MLB work subtracts 48. Expected PA
barely changes 419.43 to 421.14 with no own correction, against 653 actual.
The miss includes +.95 opportunity and +1.73 hitting custom wins. Three nearest
peers receive more PA than forecast, while Noel receives less. That contrast
supports reviewing talent/readiness jointly, not granting every young prospect
the same workload. This test changes neither his strong pedigree evidence nor
his conservative hitting forecast.

### Gains and contrary cases

Rhys Hoskins before 2024 is the largest PA squared-error gain. He has 443 and
672 MLB PA in 2021–2022, no MLB PA in 2023, and a January 26 agreement/listing.
The listing correction moves expected PA 26.26 to 193.13 against 517 actual;
about +168 PA comes from his own listing change, offset by -1.39 from refitting.
Appearance reaches .6703 and conditional PA 288.11. The older strong production
raises that head while zero current work still penalizes it. This is a sensible
direction for a known returner but remains too low. Only eight active training
people share the broad profile. Max Stassi, the nearest positively listed peer,
has zero following PA: a listing cannot guarantee recovery.

Luke Voit before 2022 is the largest PA harm. Recent MLB PA are 510, 234 in
the shortened 2020 season, and 241 in 2021; current-year rehabilitation adds
53 AA/AAA PA. The dated March 18 roster omits him from both Yankees and Padres,
while the same stored transaction window has his acquisition and activation.
The Padres announcement confirms a corresponding reserve-roster move that day.
[Dated announcement](https://www.mlb.com/press-release/press-release-padres-acquire-luke-voit-from-yankees)
Own-listing mechanics remove 161 PA; refitting removes another 4.59. Expected
PA falls 345.43 to 179.81 against 568 actual. This is a source/cutoff consistency
failure for the declared date boundary; intraday order is unverified, so do not
pretend the returned negative proves lost rights. The old near-correct value
also hides too little PA and too optimistic hitting. His negatively listed
domestic peers include non-returners, making the incorrect proxy consequential.

Matt McLain before 2024 is the largest false high, 604.71 expected PA versus
zero, up from 599.38 without own-input changes. He had 403 MLB and 180 AAA PA
in 2023, with 28 HR combined. Current work, role and power raise conditional
workload; appearance is .9845. His March shoulder injury postdates the January
forecast cutoff. [Injury timing](https://www.mlb.com/news/matt-mclain-shoulder-surgery)
The realized zero is not a recorded zero hitting ability, and the automated
walkthrough's zero rate is only an accounting placeholder. Do not tune his
preseason point forecast to a future injury. Risk calibration is a population
question; his peers include both substantial and short future workloads.

Fernando Tatis Jr. before 2023 is the largest false low. He had 546 MLB PA
and 42 HR in 2021, zero MLB PA and 14 rehabilitation AA PA in 2022. No own
input changes; refitting lowers PA 39.68 to 22.32, against 635 actual. Both
heads still combine reserve-list absence and zero current MLB work with modest
retained older production. His projected April return was publicly discussed
before this forecast cutoff. [Prior return expectation](https://www.mlb.com/padres/news/fernando-tatis-jr-return-date-from-suspension-in-2023)
This is lost temporary-absence/status representation, not a new surprise talent
breakout or an injury we needed hindsight to discover. The current offseason
transaction window alone omits earlier suspension context. Brief-debut peers
are not reliable analogues for an established temporarily unavailable star.

Martín Prado before 2019 is the ordinary well-predicted PA case: 228.76 becomes
260.03 against 260 actual, entirely from refitting. His recent MLB PA are
658, 147 and 209; low recent work, age and weak production constrain workload.
The fixed hitting estimate -1.193 is much better than observed -3.823, so the
almost perfect PA forecast still predicts +.284 contribution against -.856.
His value worsens slightly. A successful component does not make the player
projection correct; ordinary peers include both rebounds and limited workloads.

## Disposition and remaining work

Player review is complete, not a reasonability pass. Most fixed cases have no
own input change; small movements there are global refitting, not recovery of
foreign experience, health or readiness. Of the 30,506 forecasts, 754 have zero
people in their exact broad conditional profile and 10,676 have fewer than
twenty. These diagnostics retain every forecast, do not prove support at twenty,
and cannot substitute generic people for elite or foreign profiles.

The source review also enumerates 84 old-positive/new-negative listing changes
across the full feature panel, including eight with an event on the information
date. Not all are errors: an outright, release or minor agreement can genuinely
change reserve membership. Resolve event ordering and temporary status rather
than preserving every old positive, OR-ing all cumulative positive events, or
reinterpreting all new negatives as job loss. Voit is a concrete contradiction
to the current date-boundary use, not evidence that all historical rosters fail.

Keep this candidate as diagnostic development evidence. Do not promote it or
reject foreign-history integration because this context-only contrast is weak.
The next bounded integration must separate returned listing, dated contract/role
evidence and temporary unavailability, then add translated foreign component
counts to talent and workload consistently. Existing domestic players and all
original non-arrivals stay; qualified source additions are scored separately.
Ohtani before 2018, Suzuki before 2022, Yoshida before 2023 and Lee before 2024
still have no forecast in this comparison. They are missing forecasts, not zeros.

Focused source/accounting tests and the 31-file freeze check pass. The frozen
forecast, protected 2026 outcomes and existing explorer are unchanged. The public
workload gap, elite newcomer misses, full WAR, long-term support and player-value
uncertainty remain open. This milestone does not complete the active hitter goal.
