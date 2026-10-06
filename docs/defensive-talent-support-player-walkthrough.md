# Player checks for later MLB defensive quality

2026-10-06. These are measurement and training-support checks, not new
forecasts. The minor statistic is successful first-handler ground-ball credit
relative to other teams in the same season/league, with a park and handedness
context estimate shrunk toward that league. Every team ground ball while the
player occupies the position contributes exposure, including through hits.
Without ball location and difficulty this is a coarse indicator, not OAA.

## Selection and calculation

The 13 fixed player-origins come from the preceding range experiment. For each,
use the position with the most origin-known weighted exposure. Three peers at
the same origin level, position and prior-MLB-defense status are ranked by age
distance, then exposure distance, then player ID. Future success is not part of
that ranking. The machine-readable traces retain every peer, annual source row,
future position path and actual held-player training count.

The pooling rule is the last three calendar years at weights 1, 0.5 and 0.25.
The displayed minor indicator is `(credits − expected credits) / (exposure + 600)`.
The 600 is inherited from the sealed measurement, not refitted here. A native
MLB quality label requires a complete future window and two isolated seasons
with at least 1,500 total defensive outs. Its units are range runs per 500 innings.
Mixed-position seasons remain visible without allocating their aggregate runs.

This audit creates no predictions. Improvement, deterioration and false-high/
false-low forecast categories therefore do not apply. The cases instead cover
clean measurements, development, position changes, non-arrivals, limited samples,
infield cameos and immature windows. No source case is a validated model win.

## Clean shortstop measurements and development

**Bobby Witt Jr., 2021, age 21.** His 1,091.25 weighted shortstop ground balls
produce 205 credits against 222.93 expected, an indicator of −0.01060. The source
combines 2019 rookie evidence at quarter weight with 490 AA and 522 AAA balls in
2021; no 2020 season is fabricated. His 2022 aggregate range score cannot be
called shortstop-only: 1,332 of 3,809 outs were at third. In 2023–2024 he has
8,021 clean shortstop outs and +21.136 range runs, or +3.953 per 500 innings.
This is a real disagreement between the coarse minor indicator and later
developed MLB range, not evidence to tune the model to Witt. His actual fold has
33 training people but only two matching age/level/position/prior-MLB profiles.

The origin-selected peers are Oswald Peraza, Gabriel Arias and Brice Turang.
Peraza and Arias have mixed-position MLB measurements. Turang's 2023–2024
infield-only exposure totals 6,962 outs, but cannot establish his origin
shortstop quality. Successful movement to second base must remain a separate
development/position question, not disappear as zero talent or become SS proof.

**Anthony Volpe, 2022, age 21.** The weighted source has 1,631.5 balls, 337.5
credits and 342.09 expected, or −0.00206. Most current-year source exposure is
AA: 1,013 balls versus 205 AAA. The panel's highest-level label is AAA; that
label alone loses meaningful development context. His full 2023–2025 shortstop
path has 12,201 outs and +6.217 range runs, +0.764 per 500 innings. Annual range
changes from +0.904 to +10.519 to −5.207, illustrating why one season is not a
fixed talent grade. Forty training people still give only two matching profiles.

Peers Jarryd Dale, Brayan Rocchio and José Tena illustrate different unknowns:
Dale has no recorded future MLB fielding in the window; Rocchio has 3,306 clean
shortstop outs but just one isolated season; Tena has mixed-position exposure.
None should receive a zero-quality label. Highest-level peer matching also needs
source exposure shares before any new fit; a brief AAA stop is not a full AAA year.

**Jeremy Peña, 2021, age 23.** His 469.5 weighted balls produce 103.5 credits
versus 102.08 expected, +0.00133. The current year contributes 242 AAA and 29
rookie balls; old 2019 evidence contributes at quarter weight. All three later
seasons are clean shortstop measurements: 11,642 outs and +4.192 range runs,
or +0.540 per 500 innings. This target measures range only, not his entire
defensive reputation, arm, double plays or awards. Thirty-three training people
again shrink to two matching profiles. Brendon Davis fields elsewhere; Lucius
Fox has only 198 infield-group outs; Kevin Vicuña has no recorded MLB fielding.
Their arrival/exposure paths are different questions from fielding quality.

**CJ Abrams, 2021, age 20.** The 425 weighted balls yield 87.25 credits versus
89.69 expected, −0.00238. His 2022 aggregate includes second base and right
field, so it is excluded from SS quality. His 2023–2024 isolated shortstop path
has 7,395 outs and −20.143 range runs, or −4.086 per 500 innings. Only two
matching training people support the profile. His peers Daniel Castillo, Jose
Guzman and Derwin Barreto have no recorded future MLB fielding. The completed
measurement separates observed poor range from those three unknown qualities.
Abrams's separate 2023 origin retains a partial 2024–2025 path, not a completed
three-year label.

## Position changes and small samples

**Jorge Mateo, 2018, age 23.** His 2,098.25 weighted balls yield 451.5 credits
versus 444.80 expected, +0.00248. He later becomes a substantial MLB shortstop.
But only 2022 is isolated: 3,772 outs and +7.590 range runs. In 2023, 60 CF outs
make the season's aggregate score inseparable; 2024–2025 are also mixed. He
fails the two-season measurement rule even across seven years. This does NOT
mean his talent is unmeasurable in principle or unsupported by substantial
playing time. It identifies a defect of our aggregate target source. Nicky
Lopez has substantial infield-only exposure but mixed positions; Tommy Edman
mixes infield/outfield; Alex De Goti has a tiny second-base appearance. All
Mateo-origin folds have zero mature historical training windows for these labels.

**Jordan Lawlar, 2022, age 19.** His 868.5 weighted balls produce 177 credits
versus 174.99 expected, +0.00137. Only 168 current-year balls are AA; much more
comes from A/A+. His later isolated SS measurement is 231 outs in 2023. The
2025 aggregate includes 111 second-base, 228 third-base and 24 SS outs. Neither
231 SS outs nor 594 infield-group outs establishes a stable MLB quality grade.
Peers Jefrey De Los Santos and Angel Del Rosario have no recorded MLB fielding;
Darell Hernaiz has 2,333 infield-group outs but mixed positions. Unknown quality
is not poor quality. Lawlar's fold has 39 people, only two matching profiles.

**Marcelo Mayer, 2024, age 21.** The 1,133.25 weighted SS balls produce 209.75
credits versus 218.78 expected, −0.00521. His partial 2025 path has 926 outs,
only nine at SS, with most at third. Calling the +2.412 aggregate range runs
proof of SS talent would be wrong. All 3/5/7-year windows are incomplete.
Maximo Acosta, Frederick Bencosme and Arol Vera are retained as origin-selected
peers; no completed quality target is fabricated for any of them.

**Ceddanne Rafaela, 2024.** Only 140.25 weighted minor SS balls remain, with
35.5 credits against 28.53 expected, +0.00942. There is no current minor source
season in this pooled SS evidence. His 2025 aggregate has 3,502 CF outs and
495 second-base outs, no SS outs. Its +19.419 range runs cannot validate SS
play share. Peers Neto, Henderson and Abrams have different future positional
paths; their SS innings do not repair Rafaela's missing SS target.

**Xavier Edwards, 2023.** His 796.5 weighted second-base balls produce 160.5
credits versus 155.81 expected, +0.00336. In 2024 he fields 1,770 SS outs and
only 27 at second; 2025 has both. The 5,319 infield-group outs are genuine
measurement evidence, but not a second-base-only label. All windows remain
incomplete. Sosa, Gelof and Soto stay in the peer traces; the group outcome and
future position mix cannot be substituted silently for same-position quality.

**Liover Peguero, 2024.** His 1,274.75 weighted SS balls produce 254.25 credits
versus 263.21 expected, −0.00478. No future 2025 official/native fielding row
appears. The full window is incomplete, so it is neither a completed non-arrival
nor a zero-quality label. Tena, Brooks Lee and Leo Jiménez illustrate differing
partial infield exposure. They are not forecasts of Peguero's eventual failure.

**Oswaldo Linares, 2024.** Only 51 second-base source balls from 2023 remain at
half weight, or 25.5. Six weighted credits against 4.58 expected produce
+0.00227 after shrinkage, but the panel's infield role share is zero. This is a
catcher/infield cameo, not a confident second-base talent grade. Dorighi, McNair
and Howe are input-selected peers; their small exposures remain visible. The
Linares profile has zero matching training people in each audited window.

## Nonarrival and DSL evidence

**Jeter Downs, 2018, age 19.** At second base he has 842 balls, 147 credits
and 150.46 expected, −0.00240. There is no recorded MLB fielding in 2019–2021.
The longer windows contain 348 mixed-infield outs in 2022–2023, still no
substantial isolated second-base measurement. Non-arrival is unknown quality,
not a validated poor defender. Oswaldo Cabrera, Reinaldo Ilarraza and Kervin
Suarez were selected without later results: Cabrera eventually fields across
positions, while the other peers lack recorded MLB fielding in these windows.

To include actual DSL sources rather than equate all rookie records with DSL,
the supplementary review selects the three largest 2016 SS exposures with at
least 100 weighted balls and at least 80% from league 130. Selection occurs
after the coverage calculation, using only origin inputs, not future quality.
Carlos Baez, 18, has 886 balls and a −0.00428 indicator; Jonathan Guzmán, 16,
has 788 and +0.01129; Jesús Bastidas, 17, has 749 and +0.00827. None has
recorded MLB fielding inside the seven-year window. Positive minor indicators
are not evidence of future MLB value, and these unknown qualities must not be
converted into negative talent targets. The reviewed traces include their peers.

Among all origins with some DSL source exposure and no prior MLB defense, only
three distinct people have substantial isolated quality in mature seven-year
windows: Giménez, Perdomo and Tovar. These outcome-selected names diagnose
coverage, not independently confirm a predictor. Their origin rows overlap
and are not independent players each time they appear.

## Confirmed source gap and next step

Tovar's 2019 audit origin is marked INACTIVE with missing age/name in the
existing panel, despite 660 SS and 66 second-base balls in the 2019 short-season
source. This is a confirmed origin-metadata mismatch, not no minor activity.
His Boise/Grand Junction participation is corroborated by the
[official transaction history](https://www.mlb.com/player/ezequiel-tovar-678662).
Do not use that stale panel label to assign him an inactive training profile.
The audit preserves it to expose the defect; no model uses the mismatched row.

The same-position rule is safe but highly selective. Mateo and Turang show why
we need actual position-split quality, not relaxed purity or invented allocation.
The saved official leaderboard HTML exposes a position-split control, which is
a promising source route but not yet a certified split dataset. Repair that
target and the origin metadata, then recount chronological support before
deciding on a talent fit. Long-window absence of historical training examples
also remains: more target detail cannot create pre-2016 minor features.

Walkthrough complete for the source/support question. No talent predictor has
been adopted or rejected; no additional accuracy or full-WAR claim follows.
