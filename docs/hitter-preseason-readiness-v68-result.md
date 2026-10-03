# Fresher rankings help prospect readiness, but graduation needs to be understood

2026-10-03. Completed all 140 saved-head replays and eleven actual player
walkthroughs. Retain this as a useful research extension, not a deployed
replacement or a declaration that the hitter goal is finished.

Only twelve ranking-vintage inputs change. Hitting, school flags, settings,
training memberships and all 30,506 historical forecasts stay fixed. This adds
coming-season preseason information to a December-based model; it is not a
December bug fix or a fully updated Opening Day health/roster forecast. Lists
are qualified retrospective reproductions. Protected 2026 remains untouched.

## What improves and what does not

| Same population | Baseline PA RMSE | Preseason PA RMSE | Baseline PA MAE | Preseason PA MAE |
| --- | ---: | ---: | ---: | ---: |
| All forecasts | 60.686 | 60.499 | 20.745 | 20.612 |
| 2,627 public matches | 138.488 | 138.330 | 106.871 | 106.411 |
| Never-debuted players | 27.745 | 27.252 | 4.875 | 4.764 |
| Never-debuted upper minors | 56.242 | 55.127 | 19.097 | 18.732 |
| Newly listed prospects | 135.016 | 123.085 | 56.860 | 60.491 |
| Draft-year top-fifteen picks | 113.741 | 104.125 | 35.748 | 37.421 |

Equal-origin offense RMSE changes .453810 to .453384 overall, .154066 to
.152257 among never-debuted players, and .317058 to .312832 in the upper-minor
non-debuted group. These are custom-event batting-plus-replacement wins, not
full WAR or trade value. Hitting ability was not refitted.

Nominal whole-player 95% development intervals support the never-debut and
upper-minor PA/offense squared-error improvements. Upper-minor PA-MSE difference
is -124.22 [-242.06, -18.25], offense -.002662 [-.005101, -.000538]. Overall
intervals still span zero: PA -22.61 [-51.91, 4.51], offense -.000387
[-.001020, .000183]. These are repeatedly exposed development results, not
independent final-test confirmation. Better prospect RMSE comes with higher
absolute error in the newly listed and latest-draft groups.

Newly listed prospects get 11,925 expected PA versus 17,040 observed, up from
6,564; appearance totals improve 42 to 60 versus 74. Top draft picks rise
510 to 1,098 PA versus 3,126. But upper-minor non-debuted forecasts still total
only 74,239 versus 92,891 and expected arrivals decline 593 to 589 versus 730.
Lower-minor non-debuted PA falls toward reality, 7,652 to 7,055 versus 5,194,
while its RMSE slightly worsens. Better individual probability scores do not
imply correct appearance counts or workload allocation.

Public PA MAE remains 15.6% worse than Steamer's 92.083, outside the unchanged
15% practical tolerance, with archive-date qualifications. Established MLB
offense RMSE slightly worsens, 1.113723 to 1.113963. The 2021-origin arrival
shortfall grows, 588 to 581 expected versus 686 actual. No blanket whole-model
upgrade is established.

## The baseball findings

Langford rises 43 to 215 expected PA versus 557; Bellinger 15 to 103 versus
548; Alonso 127 to 215 versus 693. Actual saved paths and fixed-fit ranking
reversion confirm that fresher standing raises participation and active workload,
not just an accidental hitting offset. They remain substantial misses. Kurtz
improves two to ten versus 489; Cam Smith also stays near ten versus 493.
Their very fast entry paths lack close earlier active examples. Exact profile
support is zero for Langford's newest-draft top-20 slice, although shared
model branches borrow information from broader profiles.

Moniak's new number-19 rank raises expected PA .49 to 6.36 versus zero, not
an immediate regular's job. Salas stays low, 7.22 to 5.89 versus zero. Burger
remains unlisted and low. These failed/immature peers stay in evaluation.
Judge improves workload modestly despite a lower latest rank, but the fixed
hitting forecast still misses his breakout. Chris Davis's workload is close;
his severe decline remains a talent miss, not a prospect-readiness error.

Meadows is the major new harm. Expected PA drops 327 to 248 versus 591 after
he disappears from the latest ranking. The raw origin source records 178 MLB
at-bats. MLB's [2019 ranking eligibility explanation](https://www.mlb.com/news/mlb-s-top-100-prospects-for-2019-c303077544)
sets a 130-at-bat limit; Meadows graduated rather than losing prospect standing.
The model retains prior ranking history but still cuts active workload when
current rank becomes zero. This is a concrete representation problem, not a
wrong historical rank or permission to boost all graduates.

Rortvedt's nearly exact offense total is another misleading success: 82 predicted
PA versus 328 observed is offset by an optimistic batting rate. The required
walkthrough prevents counting that cancellation as a convincing forecast.

## Next bounded correction

Distinguish known at-bat-based graduation from current unlisting. Preserve
previous standing as historical reputation; do not pretend it is a current
scout assessment or replace every absence with a peak rank. Audit successful
and failed graduates and actual source coverage before one matched fit. Service
days and left-truncated histories that cannot be reconstructed remain unknown.
Keep both old and fresher-source baselines, membership and scoring fixed; no
post-result subgroup blending or generic learner sweep. Then return to the
remaining broad workload/talent gap. The overall hitter goal stays active.

Evidence and all four-player comparison sets:
`reports/model-evidence/hitter-preseason-readiness-v68/`.
