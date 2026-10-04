# Recovered launch measurements for hitter projections

2026-10-04. The 2023 and 2024 cached MLB files now supply launch measurements
on 245,589 result-producing non-bunt contacts. This is a usable additional source,
not evidence that a new projection beats the current model. No new model was
fitted and no forecast or explorer changed. Earlier history is being recovered
before the separately declared future-MLB comparison.

| Season | Non-bunt terminal contacts | Complete EV and angle | Missing either | Complete pairs outside direction cells |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 123,206 | 122,857 | 349 | 3,379 |
| 2024 | 123,095 | 122,732 | 363 | 3,542 |

All launch contacts join uniquely to physical identities and actual game venues.
No invalid-range reading was found in these two seasons. Measurements are provider
values; their individual camera-versus-estimation provenance is not known.
Missing readings remain missing, not zeros. EV-only and angle-only observations
have separate denominators. The source is not already neutralized for park,
opponent or league. A regular-season chunk with no regular-season rows is valid;
the first attempt rejected such a 2024 chunk, before sealing this source report.
That source-loader error was fixed and covered by an additional unit test.

All sixty-nine homers missing direction geometry have a complete launch pair.
Direction-cell completeness must not be used as the launch-measurement filter.
Conversely, five other homers have missing launch measurements across the two
seasons, and their official HR counts remain intact. Statcast measurements do
not replace the independently reconciled batting-count backbone.

## What the actual players show

EV95 is the linearly interpolated 95th-percentile exit velocity in mph, not the
single hardest ball. Hard contact means EV at least 95 mph. Hard-air fraction
here means EV at least 95 and angle 8 to 50 degrees among complete pairs; it is
a transparent source summary, **not the official barrel statistic**. These raw
values have no fitted reliability weights and are not a new hitting forecast.

| Player and measured season | Complete pairs | Mean EV | EV95 | Hard contact | Hard air |
| --- | ---: | ---: | ---: | ---: | ---: |
| Aaron Judge 2023 | 239 | 97.65 | 113.14 | 64.4% | 47.3% |
| Aaron Judge 2024 | 388 | 96.22 | 113.70 | 61.3% | 42.3% |
| Juan Soto 2023 | 440 | 93.23 | 111.21 | 55.9% | 29.1% |
| Brandon Belt 2023 | 196 | 88.37 | 107.40 | 40.8% | 31.6% |
| Spencer Torkelson 2023 | 438 | 91.77 | 108.60 | 50.9% | 30.6% |
| Matt McLain 2023 | 247 | 89.32 | 105.84 | 42.9% | 29.1% |
| TJ Friedl 2023 | 378 | 86.54 | 103.40 | 29.9% | 13.0% |
| Michael Siani 2024 | 195 | 84.18 | 102.28 | 25.1% | 10.8% |

These are the same ten forecast cases reviewed in the
[ordinary contact walkthrough](hitter-own-mlb-contact-source-result.md), including
two Judge origins and the two players without own-MLB measurements. The source
case manifest carries actual dated stats, all current rate inputs, saved-model
terms, current PA/rate/value, observed next-year outcomes and the same origin-only
peer choices. It does not select successful players based on the new measurements.

Judge's 2024 homer in game 745747 has EV 114.4 mph and angle 28 degrees despite
missing direction. It now remains in launch summaries. His 391 physical contacts
become 390 terminal in-play non-bunt contacts because one was catcher interference
in game 747044, not a normal Statcast BBE. Of those 390, two lack launch readings.
This distinction is supported by structured events, not convenient denominator
selection. His +4.534 current rate and 531 expected PA are unchanged; +6.287 and
679 were observed in 2025. The strong production terms already used by the model
mean these measurements cannot simply justify adding another power bonus.

Soto's four Mexico City contacts retain their actual MLB venue and NL identity.
His high power and contact quality complement 121 unintentional walks and 129 K,
but do not establish a numeric upgrade to his +3.941 current hitting forecast.
Judge and Soto are plausible beneficiaries of finer power representation, not
preselected proof that the new model must win.

Torkelson had 31 HR and strong measured contact at origin 2023, yet his next-year
rate was -.721 against a +1.296 forecast. Thus "hard hitter" is not sufficient
reason to raise a projection. This opposite-risk case remains in the eventual
model review. An optimistic change that improves Judge can still worsen Torkelson.

Belt and McLain have 196 and 247 measured pairs, respectively, but zero next-year
MLB PA. Their observed next-year rates remain null, not zero. Launch quality
cannot by itself explain a surprising absence from MLB or forecast injury.
Delivered offense remains zero, and the model's PA/value misses remain visible.

Friedl and Siani's launch universes are larger than their classified direction
universes, despite excluding bunts: 378 versus 365 for Friedl, and 197 versus
192 before missing readings for Siani. The ordinary direction classifier puts
terminal foul-air contacts outside its core bins; the launch source accepts a
terminal type-X result rather than every foul pitch. That is a legitimate
measurement-universe distinction, not permission to combine denominators blindly.
Siani's four 2023 measured contacts also yield an EV95 number, but four contacts
cannot be treated as equivalent evidence to 195 or 440. Sample uncertainty must
be modeled before projection use.

Nick Kurtz's fifty A/AA PA and Juneiker Caceres's 167 DSL PA yield no own-MLB launch evidence
in this source. That is not measured average or bad contact. Their current
forecasts remain ten PA/-.063 and .067 PA/+.499 respectively. The already tested
prospect hitting alternative remains separate; the MLB tracking source cannot
repair a thin-sample entrant through invented readings. Covered minor-league
data requires its own source and league-calibration review.

## Support and next action

There are 398 to 424 distinct active tracked training players in each origin-2024
outer fold, with only origin 2023 represented. Earlier folds have zero tracked
active training players from this pilot. The 735 tracked origin-2024 test players
and 648 origin-2023 test players do not manufacture earlier training histories.
Missing source seasons stay explicitly separate from absent player measurements.

Accept this two-season measurement source after the additive final verification
and complete player walkthrough. Do not launch a one-year winner search merely
because these files are ready. Recover earlier MLB measurements, preserve 2020's
short season and document older measurement uncertainty; then freeze the direct
future-MLB hitting contrast in the [integration plan](hitter-statcast-integration-plan.md).
No predictive improvement, prospect solution or deployment approval is claimed.
