# Direct future-MLB contact transfer: useful source, no forecast upgrade

2026-10-03. Completed source review, 60 replayed rate heads and 16 actual
stats-to-forecast player walkthroughs. Neither challenger is adopted. V33b remains
the working research forecast; V38 games/involvement remains a research extension.

## What changed

The reconstructed source now combines minor contact from 2016–19/2021–24 with
475,972 MLB contacts from 2021–24. League identities survive: DSL, separate rookie
leagues and MEX are not relabeled generic affiliated AAA. Exposure, measured/PA
fraction and missingness accompany every ten-bin profile. No EV/launch-angle input,
saved minor-target weights, future outcomes or retrospective target eligibility
entered the inputs.

Four ambiguous 2023 terminal keys disagree on batter side and are quarantined.
Another 953 raw player/league/seasons, totaling 78,688 contacts, fail the official-
count bridge; mostly MEX/rookie/DSL. Those buckets are excluded from this predictor,
not the player population or official batting history. This reveals an unverified
join, not proof the original PBP or official data is wrong. Raw sources and the
initial diagnostic are preserved. See [the source amendment](practical-hitter-contact-v41-source-amendment.md).

There are 22,881 supported applications and 7,625 exact baseline fallbacks among
the same 30,506 historical forecasts. Pre-2016 minor and pre-2021 MLB shape remain
unobserved. All 2016 forecasts are exact fallbacks because no earlier contact-
bearing training exists. MLB shape itself has no active training examples at
the 2021 cutoff; a player's older minor shape can support the broader candidate
without making the new MLB measurements learnable in that first year.

## The actual future-MLB comparison

Playing time stays bit-exact V34. Two locked batting heads add shape to the broad
count/draft history: scaled ridge and histogram boosting. Whole players are held
out, targets are mature next-year MLB outcomes, and no non-arrivals disappear.
Conditional rate uses future-active outcomes, weighted by actual PA within equally
weighted years. Value includes batting plus replacement, not full WAR.

| Forecast | MLB batting-rate RMSE, wins/600 | Delivered contribution RMSE | Public-matched contribution RMSE |
|---|---:|---:|---:|
| Count/draft source control | 1.82465 | 0.440603 | 1.016384 |
| Added shape, ridge | 1.82760 | 0.441003 | 1.019843 |
| Added shape, histogram | 1.84819 | 0.444964 | 1.027336 |

On supported rows alone, contribution RMSE is 0.444047 / 0.444486 / 0.449563 in
the same order. The ridge's paired overall value-MSE difference is +0.000353,
95% development interval −0.000368 to +0.001047: small and uncertain, not a useful
established gain. Histogram difference +0.003862, interval +0.001411 to +0.006348,
is clearly worse in this development comparison. These are nominal player-cluster
intervals after a long research program, not a fresh protected test.

Ridge improves 2017, 2018 and 2024 contribution slightly but loses in 2021–23.
Upper-minor rate improves 2.66725→2.66465, while current-MLB rate worsens
1.72436→1.72829. No wholesale declaration that contact fails for prospects is
justified; neither is a promotion based on this tiny subgroup improvement.

Histogram also changes architecture relative to ridge. Its loss cannot be
attributed solely to adding shape, nor generalized to all tree libraries or all
shape×outcome/park-adjustment systems. The current test does not evaluate
park-neutralized residuals. The later old neutralization-v2 experiment did have
a future-MLB component-value target and an uncertain small shape gain; V40's
target qualification concerns the earlier minor-target gradient test, not every
experiment with contact in its name.

## What the players tell us

- Established Judge: ridge moves batting 4.553→4.678, closer to actual 6.287;
  histogram compresses him to 3.387. Similar compression recurs in his 2023 case.
- Winn: both new rates worsen, despite separately retaining stronger AAA history
  and his short MLB debut. More bins alone do not fix early-MLB translation.
- Kurtz: only 50 professional PA, including 28 measured contacts. Draft pick four
  is known but not translated strongly enough. All variants greatly understate
  his fast entry; this is a talent/opportunity gap, not a shape-data cure.
- Meidroth: the tree gets a closer conditional rate, yet worse delivered value
  because the unchanged model expects 40 PA versus 505 actual.
- Langeliers/Rivera: near-perfect contribution predictions hide wrong rates
  offsetting wrong PA. We explicitly reject those as proof of smart components.
- Martinez/Bregman: genuine gains exist, but their earlier MLB shape is missing
  and saved paths remain dominated by production/history. Do not credit tiny
  rehab/minor shape with explaining the entire gain.

All 16 reviews include actual histories, input counts/shares, reconstructed
coefficient or tree-path intermediates, fixed-PA multiplication and origin-selected
successful/unsuccessful peers. See [the full walkthrough](evidence/practical-hitter-contact-v41/player-walkthrough.md).

## Decision

Retain the reconstructed source and source-quality flags. Do not add either
batting challenger to the working forecast or start a contact-prior parameter
tournament. Close this batch. The practical model still needs stronger
fast-entry/temporary-return opportunity and better prospect-rate support; the
public PA-MAE tolerance is not met. The protected 2026 forecast is unchanged.

[Scores](evidence/practical-hitter-contact-v41/scores.json),
[paired intervals](evidence/practical-hitter-contact-v41/intervals.json),
[source walkthrough](evidence/practical-hitter-contact-v41/source-walkthrough.md).
