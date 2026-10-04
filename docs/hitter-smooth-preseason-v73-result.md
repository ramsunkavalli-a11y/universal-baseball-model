# Fresher rankings help but the smooth model does not settle prospect readiness

2026-10-03. Keep the current fresher-ranking tree candidate and unchanged hitting
estimate. Reopening the exact smooth opportunity model with better ranking
information was worthwhile: its earlier result understated what this source could
provide. However, replacing the current trees is not a clear delivered-offense
improvement. No protected 2026 results, frozen forecasts or explorers change.

## What was compared

The [locked comparison](hitter-smooth-preseason-v73-contract.md) retains 63,282
source rows, 30,506 historical forecasts and 35 chronological whole-player folds.
The prospect subset contains 24,199 forecasts. The exact old smooth opportunity
heads keep their 171 inputs, fold-fitted StandardScaler, logistic C .01 and
conditional-PA Ridge alpha 100. Only eight scouting-vintage inputs differ; no
penalty tuning, new college data or hitting refit was added. Both smooth
assemblies keep the current tree forecasts for already-debuted players.

All 140 old/new head checks and seventy old-head replays preceded fitting. After
fitting, 140 opportunity heads replayed and thirteen selected fixed hitting heads
were reconstructed. Actual inputs, source counts, intermediate outputs, failed
peers and interpretation are in the [player walkthrough](../reports/model-evidence/hitter-smooth-preseason-v73/player-walkthrough.md).
These are execution checks, not predictive certification.

The [review amendment](hitter-smooth-preseason-v73-review-amendment.md) records an
incorrect review-list ID: the intended Maitan name pointed to Burger. Burger's
case is retained and Maitan's correct case appended; no forecast, membership,
score or model was changed. The ordered largest raw conditional-PA case is also
reviewed to inspect extrapolation rather than concealing it behind the final mean.

## Matched forecast results

The target is next-calendar-year MLB PA and custom batting plus replacement,
not full WAR, career talent or trade value. Losses weight target years equally;
totals below are raw, without league scaling.

| Never debuted group | Rows | Original tree PA RMSE | Fresh tree PA RMSE | Old smooth PA RMSE | Fresh smooth PA RMSE | Fresh tree offense RMSE | Fresh smooth offense RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All prospects | 24,199 | 27.745 | 27.252 | 27.547 | 27.098 | 0.152257 | 0.152316 |
| Upper minors | 5,454 | 56.242 | 55.127 | 55.792 | 54.773 | 0.312832 | 0.312277 |
| Lower minors | 17,852 | 7.828 | 7.966 | 7.923 | 7.990 | 0.043039 | 0.043132 |
| Drafted at origin | 2,205 | 25.303 | 23.192 | 22.345 | 22.270 | 0.163825 | 0.162233 |
| Thin professional sample | 5,317 | 11.561 | 11.372 | 10.975 | 11.000 | 0.088416 | 0.087603 |

Fresher information improves the same smooth model's prospect PA MSE by 24.521,
with a nominal whole-player paired 95% development interval of -41.912 to -9.197.
Its offense MSE also improves versus its old-source version, with an interval
below zero. That supports the source correction; it does not certify every
historical ranking's first-publication vintage.

Against the current fresh trees, prospect PA MSE improves by only 8.388, with
interval -35.803 to +21.543. Offense MSE worsens by 0.000018, with interval
-0.000558 to +0.000521. Prospect MAE improves 4.764 to 4.663; draftee MAE worsens
2.129 to 2.244. Overall and upper-minor arrival scores improve slightly, but
ranked top-group Brier/log loss and the 2021 origin deteriorate versus fresh trees.
There is no single clear winner across the claimed job.

The public matched 2,627 forecasts are unchanged: PA RMSE 138.330 versus Steamer
135.379; MAE 106.411 versus 92.083, still 15.56% worse and outside the original
15% working MAE target. Prospect-only improvements cannot close this established
player gap. Public offensive conversion and information-date differences remain
qualified; this is not proof of superior hitting talent forecasts.

## Totals and individual baseball checks

Upper-minor PA rises from 74,239 to 75,096, still well below 92,891 actual.
Lower-minor PA falls from 7,055 to 6,221, closer to 5,194 actual, despite slightly
worse RMSE and offense loss. Lower-minor mean and individual accuracy therefore
give different answers; neither alone settles the model choice.

For the post-COVID 2021 origin, prospect PA RMSE improves 31.617 to 29.562, but
expected debuts fall from 77.63 to 62.22 against 158 actual, and PA falls from
10,432 to 9,764 against 18,944. For the 2023 origin, expected PA rises from
14,725 to 18,415 against 11,697 actual. Better pooled loss does not repair those
allocation failures. Keep 2021 and the other origins, not just the favorable years.

| Player and source year | Fresh tree PA | Fresh smooth PA | Actual next-year MLB PA | What the saved heads show |
| --- | ---: | ---: | ---: | --- |
| Kurtz 2024 | 10.18 | 28.20 | 489 | Old smooth already gave 28.14; exact active elite/thin/draft-year support remains zero. |
| Langford 2023 | 214.92 | 244.03 | 557 | Higher arrival helps; only 305 conditional PA and an old rookie doubles term subtracts about forty PA. |
| Bellinger 2016 | 102.57 | 123.76 | 548 | Arrival reaches 71%, but conditional PA is only 173. |
| Alonso 2018 | 215.03 | 206.67 | 693 | Arrival is already 84%; conditional workload and hitting remain too low for this breakout. |
| Julio Rodríguez 2021 | 254.11 | 217.53 | 560 | Smooth model replacement harms this better-supported prospect profile. |
| Acuña 2017 | 101.53 | 274.50 | 487 | Largest offense gain; fresher rank changes both opportunity heads substantially. |
| Holliday 2023 | 351.19 | 421.20 | 208 | Largest offense harm; higher conditional workload magnifies a fixed hitting miss. |
| Mauricio 2022 | 69.65 | 88.62 | 108 | Ordinary gain with a reasonably close fixed hitting estimate. |

Successful peers are not the only comparables. Crews played little; DeLauter,
Shaw and Teel did not debut the following year. Young Moniak, Salas and Maitan
had no following-year MLB PA, as did their selected peers. These reasonable low
immediate-use forecasts say little about eventual upside. One-year debut targets
cannot settle long-term prospect value. Conversely, the superstar breakouts
above do not justify assigning every similar prospect a full MLB season.

The smooth conditional head hits the declared bounds in 5,582 of 24,199 prospect
rows: 5,562 lower and twenty upper. Most do not play; twenty-one actual active
players have lower-bound outputs. Morales' 201 DSL PA with fourteen HR and forty
walks become about 1,151 raw conditional MLB PA, driven by DSL rate columns dozens
of active-training standard deviations from their means. His chance is only
0.202%, so the bounded final estimate is 1.62 expected PA. That small point mean
is reasonable for immediate use; it does not make the conditional head coherent.
Rare-column extrapolation remains a limitation, not a reason to reject every
linear model or automatically fail a test because many unobserved heads clip.

## Belt correction and the next model question

The [judgment correction](hitter-review-judgment-v73.md) distinguishes unusual
outcomes from repeatable flaws. The origin-known productive free-agent control
contains 102 forecasts for 82 people: 37,299 projected PA versus 37,613 actual,
and 83.07 projected appearances versus 88 actual. Belt remains included. These
pooled descriptive totals give no basis for a blanket extra unsigned-player
penalty, and do not prove calibration in every subgroup.

Keep the current candidate. Close this exact ranking-vintage comparison without
another penalty or feature-scale sweep. Fresher scouting affects opportunity,
but is absent from the unchanged 199-input hitting head. Replayed fixed estimates
are -0.063, +0.085, +0.286 and +0.164 batting wins per 600 PA for Kurtz, Bellinger,
Alonso and Acuña. Their much larger realized breakouts show why workload-only
changes cannot settle delivered value, not what their exact preseason talent
forecasts should have been.

Next pursue the controlling plan's prospect batting-talent milestone: establish
which prior translated component/MLE tests have compatible future-MLB targets,
cutoffs and failed-player coverage, then make one bounded matched comparison
with explicit thin-sample pedigree and production behavior. Preserve established
player benchmarks. Do not relaunch an algorithm tournament, collect college
information, tune around these names or mistake one-year low use for low career
value. Whole hitter goal remains active; the candidate is still research, not a
finished valuation system.
