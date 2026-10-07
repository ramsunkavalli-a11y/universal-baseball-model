# A usable framing history baseline without an unsupported age penalty

2026-10-06. The native MLB framing component now uses actual received pitches,
retains backups and strongly shrinks small samples. Its ordinary-origin quality
error is about 10% lower than neutral framing, although the interval includes
no gain. The added age calibration is not retained: it loses accuracy, lacks
young-profile support and penalizes a missing age as if it were poor ability.
The underlying age-source defect is corrected separately, with old tests intact.

## What the test measures

The source contains modern framing measurements for 2018–2025. Modern 2016–2017
all-zero placeholders remain excluded. There are 889 eligible catcher origins;
each uses only received non-swing pitches known by that origin. Future MLB
quality is pooled native framing runs per 1,000 received pitches over the next
three calendar years, requiring at least two measured seasons, 6,000 pitches,
complete follow-up and no missing positive native catcher exposure.

At the ordinary 2022 origin, 165 catchers receive a forecast but only 55 have
measured 2023–2025 quality. The others remain unknown—not zero-quality labels.
Training has 45–54 distinct people from 2018 and 2019 depending on the held-player
fold, not hundreds of independent careers. All those early histories are cut
short by the 2018 source boundary. Fifty-three of the 55 measured test cases have
fewer than 20 people in their age/exposure training profile.

Neutral framing has error **0.866 runs per 1,000 pitches**; transparent shrunk
history has **0.782**, a 9.6% reduction. Its paired difference is −0.0834, with
a 95% person-bootstrap interval of −0.1815 to +0.0141. It also improves mean
absolute error, 0.736 to 0.661. Earlier origins show the same direction, including
the separate 2021 stress comparison, 0.974 to 0.882. These exposed comparisons
are development evidence, not a new independent protected season.

The small age/reliability calibration increases ordinary-origin error to 0.825.
It improves older-catcher point estimates on average, but worsens the young group
from 0.716 to 0.891 and the under-1,000-pitch group from 0.593 to 0.862. Its better
mean bias does not erase those failures. Do not adopt it, tune its polynomial
against these players or claim that age or framing information is useless.

## The player calculations explain the choice

Thirteen focal cases and 39 origin-selected peers are fully traced; 20 peers have
unknown future quality. Numbers below are future pooled framing runs/1,000 pitches.

| Catcher | Shrunk history | Age calibration | Later measured quality | Finding |
| --- | ---: | ---: | ---: | --- |
| Austin Hedges | +0.257 | +0.162 | +2.596 | Both miss the resurgence. His 2020–2022 native rate was much lower than his 2019 or future record; the three-year input omits that older elite season. |
| Alejandro Kirk | +0.484 | −0.034 | +1.650 | Reliable positive receiving evidence is pulled too low by a sparsely supported young-age curve. |
| Cal Raleigh | +0.823 | +0.370 | +1.004 | Simple evidence pooling is materially closer than the calibration. |
| Yasmani Grandal | +0.725 | +0.140 | +1.152 | An old-age adjustment is not universally appropriate: this older catcher retains positive receiving quality. |
| J T Realmuto | +0.251 | +0.081 | −1.119 | Calibration moves toward the decline, but neither catches its size. |
| Gary Sánchez | −0.208 | −0.054 | −0.030 | Calibration helps an ordinary near-neutral case; this does not justify adopting the entire curve. |
| Martín Maldonado | −0.050 | −0.669 | −1.328 | Largest calibration gain; the age-square term supplies much of the decline. |
| Francisco Alvarez | −0.006 | −1.093 | +0.825 | Largest deterioration. Just 95 prior pitches should not establish bad ability; age/exposure terms create the negative prediction. |
| Jake Rogers | −0.213 | −1.048 | +0.924 | A missing-age term supplies −0.968 despite usable older dated age records. That is a source/design defect, not baseball talent evidence. |
| Ryan Jeffers | +0.555 | +0.406 | −0.803 | A remaining false high; positive historical framing does not guarantee future quality. |
| Victor Caratini | −0.047 | +0.042 | +0.670 | Ordinary median-error case; both still underpredict improvement. |

Tzu-Wei Lin's 2.25 weighted pitches and Jakson Reetz's five yield history rates
of zero and +0.0029. Their later quality is unknown. The calibration instead
assigns +0.214/+0.132 from generic context; neither is an observed talent grade.
Patrick Bailey has no eligible 2022 MLB framing history and is explicitly absent
from that test, not quietly assigned average ability or added using later data.

Hedges's source shows +0.70, +0.40 and +0.40 native runs/1,000 pitches in
2020–2022, versus +2.82, +2.23 and +2.63 in 2023–2025. His 2019 +3.19 lies
outside the fixed three-year predictor window. That identifies a possible
longer-lived skill/recency limitation; it does not prove a hindsight rule or
authorize another history-weight sweep. These are the source's revised native
measurements, not assumed agreement with every older framing system.

## A source repair is applied without rewriting the old result

The corrected age view fills only unknown values, using consistent dated ages
already available by the forecast origin, at most three years earlier. Rogers's
2021 age of 26 implies 27 at the 2022 origin. No later player performance or
fabricated birth date is required. Ninety-one unknown origin-age records are
recovered; all 19 missing ages in the 2022 eligible cohort are resolved. Known
ages, labels, pitch histories, old fits and scores remain unchanged.

The retained practical component uses the simple rate—not the failed calibration
or its missing-age penalty. It has been applied separately to **149 players with
2023–2025 measured MLB history**. Their corrected context and exact numerators/
denominators are saved for the subsequent defense/value assembly. This is a
research quality layer, not a change to the selected hitter forecast or explorer.

The formula is 1,000 × weighted framing runs ÷ (weighted received pitches +
6,000), with recent-year weights 1, 0.5, 0.25. Current history-only quality is
Bailey +1.971, Hedges +1.385, Kirk +1.256, Raleigh +0.701, Sánchez −0.208 and
Realmuto −0.715 runs/1,000. Tiny current samples such as Kolozsvary's 4.25 weighted
pitches remain near zero. Missing history returns a neutral prior *estimate*
with no observed-quality flag, not a measurement of average talent.

## What remains outside the claim

The baseline's ordinary-origin mean overprediction is +0.145; actual-exposure
predicted runs total +49.7 versus −75.1 observed in the selected 55 catchers.
Full-league framing sums are near zero, but this survivor subset is not the full
league. Do not force its total to zero or claim a workload/value gain. Those
totals use actual future pitches and are diagnostic, not a forecast of exposure.

Unknown-age and other tiny subgroup bootstrap outputs cannot establish population
uncertainty from one or a few observations. The original calibration failure is
qualified by source loss, young extrapolation and left-truncated training; it is
not a general rejection of aging. The practical baseline still misses developing
or rebounding talent and is not validated for unobserved minor-league framing.

Independent checks replay all 889 forecasts and histories, 15 learned fits,
source labels, person-bootstrap intervals, all player/peer arithmetic, 91 age
repairs and the 149 current component calculations. Six focused framing tests
cover chronology, player separation, actual pitch units, tiny-sample shrinkage
and cutoff-safe age recovery. Execution integrity and player review are complete;
full defensive value is not. No 2026 outcomes were used.

Next: qualify arms/first-base receiving and catcher throwing/blocking, then
independently forecast positions and opportunities. Framing ability does not
automatically deliver equal value under traditional calls, challenges or full
ABS. Keep those scenarios in the exposure/value layer; no fixed six-year bonus.

Evidence: [talent scores](../reports/model-evidence/catcher-framing-talent-v4/report.json),
[player calculations](../reports/model-evidence/catcher-framing-talent-v4/player-walkthrough.json),
[applied baseline and source correction](../reports/model-evidence/catcher-framing-talent-v4/baseline-preparation-review.json)
and [independent verification](../reports/model-evidence/catcher-framing-talent-v4/baseline-verification.json).
