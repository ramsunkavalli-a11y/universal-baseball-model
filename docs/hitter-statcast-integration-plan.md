# Adding Statcast to future MLB hitting projections

2026-10-04. The user has reopened tracking data as an evidence source. Add it
where genuinely available without replacing the results and pedigree model for
untracked players. The question is whether it improves future MLB hitting and
delivered offense, not whether it predicts a contact-shape bin. Team-record
testing remains closed. No frozen forecast or explorer changes are authorized.

## What earlier work established

The first Current Talent challenger used mean exit velocity and sweet-spot share
to predict ten contact-shape probabilities and lost its 2022 development test.
The second used the same measurements to predict contact value conditional on
realized future shape and level. In 2023, its mean squared error improved from
.203382 to .203021, but MAE worsened from .356167 to .356923 and calibration
failed. Preserve that rejection; do not retune it. These were 90-day conditional
contact tests, not the current next-year MLB hitting forecast. Their 2023 results
are exposed development evidence, not an untouched confirmation year.

Sources: [shape test](current-talent-batted-ball-development-checkpoint.md),
[value confirmation](current-talent-contact-value-confirmation-result.json),
[postmortem](current-talent-challenger2-postmortem.md).

## Baseball rationale and limits

Exit velocity can describe power before enough home runs accumulate. Joint
speed and angle describe whether that power produces useful contact, while
strikeouts and walks still determine how often the hitter produces an opportunity.
An established hitter's result history already contains some of this information;
do not give every hard hitter an automatic bonus. This was explicitly recognized
in Sapolsky and Cross's [2016 projection research](https://tht.fangraphs.com/improving-projections-with-exit-velocity/).
[Clemens's repeatability analysis](https://blogs.fangraphs.com/you-cant-fake-exit-velocity/)
supports investigating upper-end velocity rather than one maximum; repeatability
alone is not proof of incremental future MLB accuracy.

Public [minor-league coverage](https://baseballsavant.mlb.com/statcast-search-minors)
includes all Triple-A games from 2023, with earlier partial Triple-A and Florida
State League coverage. Verify actual historical game coverage, not just level
names. [Bat tracking](https://www.mlb.com/news/what-you-need-to-know-about-statcast-bat-tracking)
begins in April 2024 and cannot support the same long historical comparison.
Leave bat speed, fielding tracking and sprint speed to separately justified work.
Do not use modern xwOBA as a next-year projection or as a historically fixed
feature without knowing its estimation vintage and information boundary.

## Source construction before fitting

First reuse the captured 2023 and 2024 MLB raw files whose identities and official
result counts were reconstructed in the ordinary contact audit. Project only the
ordinary identity/result fields plus launch speed and angle. No expected outcomes,
future-game intervals, contemporary ages or bat-tracking fields enter this source.
Hash the original bytes and verify the existing capture receipts. No source
redownload or fit belongs to this first materialization.

Build a ledger of regular-season, result-producing, non-bunt in-play contacts.
Exclude foul measurements even when EV/LA exists. Preserve missing/invalid
measurements and their denominators. A missing spray coordinate must not remove
an otherwise measured EV/LA contact. Keep actual venue, hand and league identities.
Reported launch measurements are provider values; the export does not certify
which individual values may have been estimated by the provider. Do not describe
every historical measurement as directly observed by a camera.

Save sample counts, mean and 95th-percentile EV with a specified quantile method,
hard-contact fraction, launch-angle distribution and joint hard-contact/angle
counts. These are raw measurements, not already park-neutral MLB talent. At
this stage there is no guessed reliability weight or promotional threshold.
No measured contact is not average contact. Missing seasons are not zero events.

Count actual tracked, active training people in every current outer fold at each
predictor row's own origin. Two recovered source years only support one later
evaluation year, and cannot establish broad forecast improvement. Recover earlier
MLB history and supported minor evidence before launching a model comparison.
Use 2020 MLB's actual short-season measurements where available; canceled MiLB
2020 supplies no measurements. Keep tracking hardware/coverage changes explicit.

Review Judge, Soto, Belt, Torkelson, McLain, Kurtz, Caceres and the ordinary audit's
two largest excluded-contact profiles. Save dated counts, actual measurements,
missingness, unchanged forecasts/outcomes and the previously selected origin-only
peers. Reconcile source differences and explain them before source approval.

## The subsequent forecast contrast

After source/support review, freeze one bounded experiment contract. Compare the
current hitting forecast against the same evidence plus tracking, with identical
players, targets, playing-time estimates and contributions. Do not force tracking
through the old contact-bin residual. Give a regularized direct rate model and one
bounded nonlinear rate model the opportunity to learn its relation to hitting.
Keep the existing prospect alternative as a named benchmark, not a new contest.

Predict next-year future-season-relative MLB batting wins per 600 PA among active
players; separately score common-origin delivered offense on everyone, including
non-arrivals. A zero-PA season has zero delivered offense, not observed zero talent.
Learn scaling, source/league calibration, reliability and any shrinkage inside
chronological training that excludes the entire held-player group. Minor EV cannot
silently be treated as MLB-equivalent. Untracked players retain the exact current
forecast in the incremental contrast. Do not award value for simply having coverage.

Predeclare the concrete features, folds, losses, training support and acceptance
limits in that contract after source feasibility is known, before fitting. Report
all-player and tracked-player effects, current MLB, promoted prospects, source
tiers, sample bands, origin years, totals, paired player uncertainty and the
matched public comparison. Carry conspicuous gains and harms through full player
walkthroughs. No subgroup-selected rescue, repeated hyperparameter sweep, blanket
power bonus, or automatic deployment follows a favorable pooled score.

The full model goal remains active. This addition will not by itself solve
playing time, missing foreign history, defense, or six years of player value.
