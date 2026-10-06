# Recent promotions: weighting recent training did not fix fast-track prospects

2026-10-05. Player review complete. **Do not adopt this candidate.** Keep the
current forecasts. Close the exact four-year training-decay comparison, not the
idea that some prospects reach MLB faster now. No half-life sweep, favorable
upper-minors-only routing, COVID multiplier or named-player boost follows.

## What we tested and what changed

The [pre-fit contract](hitter-recent-promotion-contract.md) asks whether giving
recent training seasons more influence improves next-calendar-year MLB playing
time for hitters who have not debuted. This is not career talent, six service
years, total WAR or trade value. Zero MLB PA means no delivered contribution
that year, not zero talent.

The working reference is the completed 293-input nonmedical-observation
opportunity model with seven cutoff-known career-departure corrections. The
candidate keeps the same inputs, training identities, whole-player chronological
folds, tree settings, targets, status handling and hitting rates. It changes only
training weights: an origin four years older receives half the relative
influence, with each head's total weight normalized to its original row count.
Both arrival and conditional-PA models are refitted on their original subsets;
conditional PA still learns from established active hitters. Only never-debut
queries receive new outputs. Previously debuted forecasts are bit-identical.

There are 35 cells, 70 new heads and 30,519 historical forecasts, all retained.
Training targets end no later than the forecast origin, held-out players are
excluded, and target 2020 is not trained as a zero season. Actual target PA and
compatible batting contribution were independently rebuilt from dated MLB
statistics. All 140 old/new heads were replayed over their evaluation rows.
The 2026 freeze, completed final evaluation and explorer are unchanged; no
protected outcomes were read or rescored for this comparison.

## A small PA gain, not a useful player-value improvement

Primary population: 9,700 never-debut forecasts at origins 2022–24, representing
4,834 people. Each origin has equal scoring weight. The table uses the square
root of equal-origin MSE, not pooled RMSE. Lower is better.

| Population / measure | Reference | Candidate | Interpretation |
| --- | ---: | ---: | --- |
| Recent prospects, PA RMSE | 27.843 | 27.558 | 1.02% lower |
| Recent prospects, PA MAE | 5.466 | 5.498 | Slightly worse |
| Recent prospects, batting-value RMSE | 0.136872 | 0.137413 | Worse, not a value gain |
| Recent upper minors, PA RMSE | 53.87 | 53.20 | Better point estimate |
| Recent lower minors, PA RMSE | 7.94 | 8.12 | MSE worsens 4.46%; fails 2% guardrail |
| Six non-2021 origins, PA RMSE | 26.67 | 26.46 | Small improvement without relying on COVID |
| Six non-2021 origins, batting-value RMSE | 0.147465 | 0.147618 | Slightly worse |

Recent arrival Brier/log loss improve about 0.60%/0.70%. Those probability losses
can improve while cohort calibration gets worse: expected arrivals rise from
337 to 353 against 320 actual, and PA rises from 42,702 to 44,817 against 41,697.
Expected batting contribution rises from 99.51 to 104.62 against 66.24 actual.
The reference was already too high in aggregate. Lower-minors PA totals become
closer (3,868 → 3,804 versus 2,952), but allocation across players becomes worse.
Neither a closer total nor a lower probability score alone establishes better
player projections.

The nominal whole-player paired interval for recent PA MSE change is
−15.77 [−37.44, +4.89]; it includes no improvement. Batting MSE change is
+0.000148 [−0.000188, +0.000488]. These are exposed development intervals,
not fresh confirmation, season-shock protection or correction for hundreds of
earlier experiments. The six-origin PA interval also crosses zero.

PA MSE point estimates improve in all seven scored origins: 2016 −1.07%,
2017 −1.14%, 2018 −0.73%, 2021 −1.76%, 2022 −3.23%, 2023 −1.63%,
2024 −1.32%. No recent origin breaches the 10% harm guard. But 2022/23 recent
totals overshoot further, while 2024 remains short. Origin 2021 is retained as
a separate stress cohort; its arrivals fall 82 → 80 against 159 actual. We do
not tune around it or use it to justify adoption.

The original selected architecture is an additional, separately matched anchor.
Thirteen later source-added forecasts have no original anchor; all remain in
primary evaluation, but are not assigned fictitious zero anchor predictions.
Recent matched PA improvement against the selected anchor has a nominal interval
below zero, but this comparison also includes intervening source/model changes.
It does not isolate the effect of training decay, and its batting-value change
is uncertain. The 2,627 public-matched established hitters are unchanged, so
there is no improvement against Steamer or ZiPS for that benchmark population.

## What the faster-promotion evidence actually says

We inspected observed professional hitters in their draft year, age 20+, top-15
picks, with at most 250 recorded affiliated minor-league PA over the three-year
input window. This is an age proxy for advanced draftees, not a complete amateur
draft census or reliably matched historical school-class sample.

Among the 24 still waiting for MLB in origins 2011–18, four played MLB the next
year. In 2022–24, eight of 26 did. The recent counts are 1/7, 3/7 and 4/12.
One additional player in the 2023 observed cohort had already reached MLB and
therefore left the waiting risk set. Missing school labels are much more common
in older cohorts. Canceled/short-season 2020 context is reported separately.
These small, uneven cohorts are consistent with the user's concern; they do
not establish the size of a league-wide or causal speed change.

The candidate still expects only 2.55 arrivals and 525 PA for those 26 recent
waiting players, versus eight arrivals and 2,519 PA. The reference expects 2.94
and 633. Simply increasing recent training influence does not repair this
specific failure. Nor does that failure justify giving all top picks regular PA:
unsuccessful peers must remain in training and evaluation.

## Player walkthrough: evidence, heads, outcomes and harms

Seven fixed cases plus five prescribed diagnostics give 12 unique player-origins:
largest recent improvement/harm, largest candidate false high/low, and the
ordinary positive-PA case closest to predicted PA. Outcome-selected cases are
diagnostics, not independent validation. Each has three-year dated statistics,
all 293 actual inputs, four saved-head path traces, two actual-fold support
records, status transforms, fixed hitting, compatible value and origin-known
peers in [the raw walks](../reports/model-evidence/hitter-recent-promotion/player-walks.json).

The rows below show the latest origin season, not an invented complete career.
Counts are PA/HR/K/BB. Earlier level histories are included in the raw walks.
Probabilities are MLB participation next year; conditional PA means workload if
active. Expected PA is their product, not a prediction conditional on success.

| Player, origin | Latest dated evidence received (PA/HR/K/BB) | MLB chance, old → new | Conditional PA, old → new | Expected PA, old → new / actual |
| --- | --- | --- | --- | --- |
| Austin Meadows, 2016 | AA 190/6/32/16; AAA 145/6/34/15; A− 17 PA | 80.9% → 82.8% | 338 → 332 | 273 → 275 / 0 |
| Bryan Reynolds, 2018 | AA 383/7/73/43 | 17.5% → 17.4% | 58 → 67 | 10 → 12 / 546 |
| Donny Sands, 2021 | AA 215/10/25/16; AAA 165/8/32/16 | 79.6% → 77.1% | 90 → 84 | 72 → 64 / 4 |
| Samad Taylor, 2022 | AAA 280/9/62/28 | 60.5% → 73.5% | 105 → 94 | 64 → 69 / 69 |
| George Valera, 2022 | AA 387/15/100/52; AAA 179/9/45/22 | 88.8% → 93.9% | 249 → 247 | 221 → 232 / 0 |
| Diego Cartaya, 2022 | A 163/9/44/23; A+ 282/13/75/40 | 58.3% → 54.3% | 201 → 208 | 117 → 113 / 0 |
| Jackson Chourio, 2023 | AA 559/22/103/41; AAA 24/0/1/2 | 91.2% → 92.8% | 344 → 421 | 314 → 391 / 573 |
| Wyatt Langford, 2023 | A+ 106/5/18/18; AA 54/4/7/11; AAA 26/0/6/6; rookie 14/1/3/1 | 61.8% → 61.1% | 368 → 384 | 227 → 235 / 557 |
| Edgar Quero, 2024 | AA 292/12/49/26; AAA 110/4/21/13 | 57.9% → 43.4% | 173 → 147 | 100 → 64 / 403 |
| Roman Anthony, 2024 | AA 376/15/96/48; AAA 164/3/31/31 | 90.7% → 91.0% | 379 → 363 | 344 → 331 / 303 |
| Cam Smith, 2024 | A 57/6/12/8; AA 20/0/3/1; A+ 57/1/9/6 | 7.0% → 4.6% | 168 → 126 | 12 → 6 / 493 |
| Nick Kurtz, 2024 | A 35/4/7/10; AA 15/0/3/2 | 6.3% → 5.8% | 162 → 118 | 10 → 7 / 489 |

All four saved heads per case account for their raw predictions. Feature-path
contributions sum within each fit; they are mechanical accounting with correlated
inputs, not causal effects or a claim that changing one feature would reproduce
the cross-fit difference. No named case was given a post-result override.

### Improvements that are real but insufficient

Chourio has substantial AA exposure and current rank evidence. His conditional
rank path increases from about +189 to +221 PA; the conditional model reference
is almost unchanged. Both chance and workload rise. Compatible batting value
improves 0.84 → 1.05 against 3.04 actual, but the fixed hitting rate remains too
low. Participation/conditional support has 23/18 distinct people, effective
counts 14.0/13.4; about 42% of this profile's weighted mass is from 2022 onward.
Selected peers are Eddys Leonard (111 candidate PA / zero actual), Ángel Martínez
(96/169), Julio Carreras (51/zero). Not all apparent readiness warrants regular PA.

Cartaya's chance declines despite ranked-prospect/40-man positives; conditional
PA rises a little. This reduces a false high, compatible value 0.284 → 0.274
against zero that next year. His support is 10/6 people, effective 7.6/4.9.
Peers Luciano, Marte and De La Rosa actually receive 45, 123 and zero PA. This
is a next-year miss, not proof Cartaya has zero career talent.

Sands illustrates why the earlier COVID cohort cannot justify a blanket regular
workload. His 40-man evidence keeps arrival likely, but the candidate lowers both
heads and improves a false high (value 0.061 → 0.055 / −0.031 actual). Support
165/132, effective 135.8/116.1. Nick Allen, Brett Sullivan and Brendan Donovan
are selected peers; their actual PA are 326, zero and 468. Shared roster evidence
does not determine an individual's next-year job.

Anthony's expected PA becomes closer to 303, but compatible value worsens
1.406 → 1.352 against 2.605 because hitting is fixed too low. Conditional rank
and AAA-role path contributions decline. Support is 53/44, effective 38.3/33.1,
with about 44–46% modern weight. Rushing, Baldwin and Jett Williams peers finish
with 155, 446 and zero PA. A workload improvement is not a batting-value win.

Taylor is the ordinary case: expected PA becomes almost exactly the observed
69 as arrival rises and conditional PA falls. Yet value rises 0.120 → 0.130
against −0.198 actual. His batting prediction is wrong. Support is 196/155,
effective 145.6/123.2. Davis, Fletcher and Shewmake peers finish with zero, 102
and four PA. The nearly exact workload is not evidence of good value forecasting.

### Fast movers remain missed, despite pedigree inputs being present

Langford's actual 200 minor PA, ten HR, 34 K and 36 BB are present, along with
college and strong draft/current-rank inputs. His conditional rank and AAA-role
paths rise, but arrival chance slightly declines. Value changes 1.248 → 1.290
against 2.234; expected PA remains far short. Support is just three/two distinct
people, effective 2.3/1.4; 92%/84% of profile weight is already modern. The fixed
peer rule yields only Nik McClaughry (0.3 candidate PA / zero actual), not a
representative elite comparison. We report the shortage rather than substitute
successful famous peers after seeing outcomes.

Kurtz has only 50 observed minor PA but strong draft pedigree, a college flag,
positive rank evidence and four HR/ten K/12 BB. None is missing from the inputs.
Both heads worsen: conditional rank path falls +57 → +29 PA. Smith follows the
same broad failure with 134 PA, seven HR, 24 K and 15 BB. Each has six/four
distinct profile people, effective 5.2/3.3, with 97%/95% of weighted mass already
modern. Reweighting cannot create absent examples of elite, short-history entrants.
Kurtz's value falls 0.050 → 0.033 against 5.724; Smith 0.038 → 0.018 against
1.017. Kurtz's **current fixed hitting input is +1.024**, not the older negative
rate in a previous report; his production miss remains a separate problem.
Their peer sets include each other, Christian Moore (20 candidate PA / 184 actual)
and Ryan Nicholson (about one PA / zero).

An important source clarification: `professional_work_*` and
`signed_first_team_work` mean MLB plus NPB/KBO first-team work in this branch;
they intentionally exclude affiliated minors. The zero first-team values for
these entrants are not missing minor-league PA or evidence they never played
professional baseball. Minor PA are separate inputs. Negative first-team paths
(about −73 and −38 conditional PA in the Kurtz/Smith candidate) show the fit's
transfer from a pooled employment/workload baseline. They identify a plausible
representation weakness, **not** prove that zeroing those paths or adding a
floor is a validated repair. No retirement, hard-unavailability or departure
override explains these low estimates.

### Harms and older controls prevent a flattering conclusion

Quero is the largest recent PA deterioration: both chance and conditional work
fall despite 402 upper-minor PA and 16 HR. Conditional rank path falls +47 → +28;
the participation listing path also weakens. Value drops 0.246 → 0.157 against
1.135. Support is 12/9 people, effective 9.3/7.7, only about 19–21% modern weight.
Ballesteros, Mendoza and Palma peers finish with 66, zero and zero PA. Recency
can harm a credible advanced prospect; there is no source-loss explanation here.

Valera is the largest recent candidate false high. Both rank and roster evidence
are present; chance rises and his 566 AA/AAA PA do not yield a next-year MLB job.
Value worsens 0.613 → 0.643 against zero. Support is 19/14, effective 13.5/11.2.
Mead, Valdez and Canario peers receive 92, 149 and 17 PA. We do not label Valera's
later health or employment as known at the origin to explain away this error.

Meadows remains an older false high, with rank evidence and upper exposure
producing high chance and workload despite no next-year PA. Value worsens
0.964 → 0.970 against zero. Support is 16/11, effective 15.1/10.3. Freeman,
Delmonico and Field peers finish with zero, 166 and zero PA. No cutoff-known
reason for Meadows's non-arrival is established in this test.

Reynolds remains an older false low, not merely a recent-era problem: 383 AA PA
and seven HR/73 K/43 BB produce only 12 candidate expected PA before 546 actual.
First-team-history and strikeout/workload paths suppress conditional work;
positive minor-role/exposure evidence does not overcome them. Value improves
0.020 → 0.024 against 4.167, which is still a large rate and opportunity miss.
Support 211/49, effective 182.5/43.5, is broad but does not certify elite-trajectory
support. Robinson, Giambrone and Boldt peers all have zero next-year MLB PA.

## Decision and the next coherent checkpoint

Execution checks pass. Predictive replacement checks do not: the lower-minors
guard fails, the primary paired interval is inconclusive, batting contribution
does not improve, and fast-track cases remain systematically too low. This is
a closed research experiment, not an adopted component or a completed hitter
model. Earlier source seals and pending score artifacts remain append-only;
the separate completion receipt records this final reviewed disposition.

The useful next question is **why known elite short-history entrants receive a
generic low-opportunity baseline even when their pedigree/performance inputs are
present**, not another era weight. First reconcile the existing pedigree,
school-source, separate entrant workload, pooled-workload and prospect-pooling
tests against these actual inputs and support. Specify a genuinely different
shared readiness/prior mechanism only if that review exposes one; retain failed
top-pick peers, all lower-level non-arrivals and the current model as controls.
No promise that pedigree floors, deeper trees or successful-player anecdotes
solve it. Rate/availability fixes and six-year value calibration remain separate
open parts of the controlling hitter plan.
