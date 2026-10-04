# Repaired raw contact detail does not improve the prospect hitting anchor

2026-10-04. The repaired contact measurements do not earn a new hitting-model
upgrade in this matched comparison. Keep the current count-based model and its
tested translated hitting alternative. The declared all-player sensitivity has
some useful young-MLB changes, but its overall gain is small and uncertain and
its matched public delivered-value error worsens. Do not promote it.

This is a result about a fixed linear model using raw minor contact, not a
rejection of park-adjusted contact talent, nonlinear interactions or own MLB
contact. Protected 2026, the frozen forecast and deployed explorer are unchanged.
The practical hitter goal remains active.

## What changed and what stayed fixed

The [contract](hitter-repaired-contact-information-contract.md) separates contact
coverage, contact mix and within-type outcome detail. All three additions use
the translated head's same original 220 inputs, Ridge settings, training weights,
chronological whole-player folds and matched outcomes. Separate level exposures
remain; Mexican League contacts never become AAA. The ninety cells distinguish
singles, doubles, triples, HR and non-hit outcomes within each contact type.
They are still pooled across the player's measured minor levels and unadjusted
for park/opponent context. No old learned park residual is imported.

All 30,506 forecasts remain, including 24,199 never-debut forecasts and exits.
Playing time stays exactly fixed. Primary forecasts change only never-debuted
players with measured contact. The all-player sensitivity can also change
recently debuted players with measured minor contact. Unmeasured players retain
the anchor, so absent Judge/Soto contact cannot receive spurious attribution.

All five 2016 folds lack earlier contact-bearing active training examples.
They retain the translated anchor and remain in overall scores. Later folds
have 328–1,110 distinct active training people with measured contacts. Finer
profile gaps remain: Kurtz has zero coarse/refined active people and Langford
has zero refined people. A large pooled count does not validate those profiles.

All 210 full/active checks and 35 anchor replays preceded the ninety new fits.
Every new head replays; eleven focused tests pass. Scores, paired intervals,
actual target-event labels and nineteen selected player traces were independently
checked before disposition. This is repeated historical development evidence,
not a new untouched holdout. Mathematical rate bounds pass; those permissive
bounds do not establish baseball accuracy.

## Matched hitting and offense results

Among 787 future MLB debutants, rate scores weight actual PA within target year
and give years equal weight. Rate is fixed-event batting wins per 600 PA relative
to the realized future MLB average. Delivered offense uses a separate common-origin
batting plus replacement reference and retains non-arrivals with zero value.
It is not full WAR or trade value. Target environments validate labels only;
they are not predictors. Common-origin rate scores remain a named sensitivity.

| Primary prospect hitting estimate | Rate RMSE | Delivered offense RMSE |
| --- | ---: | ---: |
| Current count model | 2.6144 | .152257 |
| Translated anchor | 2.5831 | .151662 |
| Add coverage | 2.5924 | .151654 |
| Add contact mix | 2.5892 | .151709 |
| Add joint contact detail | 2.5886 | .151685 |

Joint detail improves slightly over mix, but not over the translated anchor.
Its paired rate-MSE difference against mix is -.00318, nominal player-clustered
95% interval [-.01299, +.00667]. Against translated it is +.02848,
interval [-.03033, +.09255]. Delivered-value difference against translated is
+.00000716, interval [-.00010092, +.00010550]. These changes are too small and
uncertain to justify another feature upgrade. They do not correct for the
project's repeated research selection.

Upper-minor rate RMSE changes 2.5632 to 2.5679; lower-minor rate 3.1791 to
3.2036, with only 54 observed lower-stage MLB batting rows. Two unmeasured
never-debut players have observed future MLB batting; no conditional-talent claim
is made from that tiny subgroup. New draftees supply only eleven observed rates
and thin professional histories eight. Missing coverage is not zero talent.

| Prospect origin | Translated rate RMSE | Joint rate RMSE | Joint offense total | Actual offense total |
| --- | ---: | ---: | ---: | ---: |
| 2016 | 2.8388 | 2.8388 | 25.98 | 21.28 |
| 2017 | 2.4896 | 2.4920 | 20.38 | 23.57 |
| 2018 | 2.7123 | 2.6866 | 25.32 | 64.28 |
| 2021 | 2.4911 | 2.5132 | 30.01 | 35.36 |
| 2022 | 2.5842 | 2.6159 | 35.22 | 31.07 |
| 2023 | 2.5496 | 2.5762 | 37.14 | 5.12 |
| 2024 | 2.3895 | 2.3713 | 26.12 | 34.07 |

The 2018 and 2024 batting improvements do not fix delivered offense totals.
The 2023 overestimate remains severe. Raising the pooled expected total from
194.67 to 200.17 against 214.75 actual is not itself evidence of better individual
forecasts; it conceals opposing annual errors. Fixed playing time means these
contact additions cannot repair readiness or workload mistakes.

The all-player sensitivity changes full-population offense RMSE .453223 to
.452728. Paired MSE is -.000449, interval [-.001314, +.000418], still uncertain.
Its public-matched offense RMSE worsens 1.060504 to 1.061816. All-player rate
changes 1.8199 to 1.8176, also with uncertainty including no gain. The primary
public sample stays exactly unchanged. Public workload remains 138.33 RMSE and
106.41 MAE versus Steamer 135.38/92.08; the practical MAE gap remains unresolved.
Public event-reference and snapshot qualifications still apply.

## What the players show

The [complete nineteen-player walkthrough](hitter-repaired-contact-information-walkthrough.md)
contains actual dated stats, actual league measurements, model inputs and linear
sums, fixed appearance/workload forecasts, future MLB outcomes and four
origin-selected peers. No gain, harm or false high/low was removed.

Alonso's hitting estimate rises +.592 to +.726, but coverage alone already gives
+.721; joint detail does not explain the whole improvement. His +3.283 actual
rate and 693 actual PA still far exceed +.726 and 215 expected. Reynolds rises
-.639 to -.544, but his detail block contributes only +.005 inside the fit;
thirteen expected PA versus 546 remains the larger readiness miss.

Langford becomes more optimistic, +1.439 to +1.650 versus +.549 actual hitting.
His delivered value moves slightly closer only because optimistic hitting masks
215 expected PA versus 557 actual. Holliday's estimate also rises, worsening
his false high. Kurtz hardly changes and remains unsupported at the thin-contact
profile. Azocar's nearly correct value masks twelve expected PA versus 216;
Collins also has compensating hitting/workload errors. Those are not accurate
integrated player forecasts.

The all-player route helps Carroll and McNeil, but hurts Torkelson. Carroll rises
+.869 to +1.587 toward +2.478 actual; Torkelson after 2023 rises +1.296 to +1.681
against -.721 actual, partly using older minor contacts without current MLB
contact. Actual-PA-weighted rate extremes retain Alvarez's gain and Torkelson's
2021 harm. Schneider's useful rate lift and Jackson's fifteen-PA collapse are
separately labeled unweighted extremes, not the primary weighted evidence.

Some linear contact terms assign positive coefficients to center-field fly outs.
These can proxy correlated contact quality or context; they are not causal run
values or proof that outs are good. Source geometry, context and collinearity
limits remain. Within-fit block sums and neutral-detail probes are not the total
change between refitted models. Peer restrictions improve some exposure matches
but sometimes exclude equivalent elite pedigree; their non-arrivals cannot explain
away the famous misses. Original unknown school-class fields remain explicit;
the earlier cached school-background repair was already tested separately.

## Decision and next work

Do not add the raw contact bundle to the prospect anchor or cherry-pick the
successful all-player cases into a new route. Preserve the repaired measurements
and all-player research forecasts. This closes the matched raw-information
comparison, not the question of adjusted contact talent.

Return to the practical plan's candidate and uncertainty work with current,
translated-rate and available-minor-season opportunity anchors. The available
season experiment already scored its combination with translated hitting
(.151630 delivered-offense RMSE); simply recombining them is not a new experiment
or a meaningful value gain. Do not repeat that assembly, team-record, pedigree
or generic learner sweeps. Next establish useful predictive uncertainty and
support-aware explanations around the preserved forecasts rather than report
another tiny point-score gain. If an adjusted-contact
extension is pursued, first establish outer-fold-clean park/opponent measurements
and usable own MLB coverage; the old two-fold event adjustment is not that proof.
Public workload, readiness/cohort errors and full player value remain unfinished.

Evidence: [completed report](../reports/model-evidence/hitter-repaired-contact-information/report.json),
[scores](../reports/model-evidence/hitter-repaired-contact-information/scores.json),
[uncertainty](../reports/model-evidence/hitter-repaired-contact-information/intervals.json),
[reviewed actual traces](../reports/model-evidence/hitter-repaired-contact-information/reviewed-cases.json).
