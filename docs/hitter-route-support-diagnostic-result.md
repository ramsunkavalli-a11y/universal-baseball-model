# Playing time misses need different explanations across player groups

2026-10-05. The read-only route diagnostic and thirteen player walks are complete.
All seventy saved heads reproduce the same 30,519 historical forecasts. No model
was fitted and no forecast, explorer or completed 2026 evaluation changed.

## Missing history is flagged but the flags themselves are unused

The actual inputs distinguish missing current MLB production with quality_present_0
and retain previous MLB history with last_MLB_known and last_MLB_work. They also
retain professional foreign activity, scouting, draft and dated job evidence.
The checked missingness flags have zero splits across both saved heads, but
numeric workload, prior quality and other redundant exposure inputs are used.
An unused flag does not mean the underlying history is omitted. A negative
zero-work path is not by itself proof of a source bug or a removable causal effect.

Across 35 participation heads, roster status is used in 1,546 splits, employment
evidence age in 1,615, last first-team work in 1,036, prior MLB quality in 932,
current scouting rank in 1,496 and draft rank in 1,078. Across conditional-workload
heads, signed first-team work appears in 1,995 splits and current professional
work in 747. Finite/unresolved nonmedical flags remain unused. These counts show
which calculations can be influenced, not validated feature importance.

## Whole groups do not support one universal adjustment

Routes come from actual origin inputs rather than explorer stage labels.
Hard retirement/permanent-status rules take precedence. Mexico is not affiliated
AA/AAA. Foreign means positive observed first-team history, not merely a source
row. These mutually exclusive groups sum to the entire 30,519-row comparison;
they are not interchangeable with earlier stage tables.

| Origin-defined group | Forecast records | Expected participants | Actual participants | Expected PA | Actual PA |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current MLB | 4,533 | 3,540.4 | 3,596 | 1,132,868 | 1,156,856 |
| Previously debuted but currently absent | 1,760 | 168.1 | 156 | 20,250 | 15,326 |
| Never debuted with current AA/AAA | 5,408 | 598.5 | 729 | 74,183 | 92,651 |
| Other never-debuted players | 18,678 | 97.3 | 56 | 8,712 | 5,267 |
| Foreign first-team history without MLB history | 22 | 3.45 | 7 | 993 | 2,018 |
| Cutoff-known hard unavailability | 118 | 0 | 0 | 0 | 0 |

These are sums across seven exposed historical origins, not an MLB-wide annual
budget. The foreign route is small and excludes returned former MLB players.
Current-MLB contribution totals are nearly equal, 3,951.4 expected versus 3,954.8
actual, while playing-time RMSE is 140.69. Good totals are not good individual
forecasts. Previously debuted absentees are overallocated in aggregate, despite
the large Tatis miss. A blanket return boost would target the wrong overall bias.

## Relevant support is much smaller than the broad sample

All actual full and active-only training memberships were checked with distinct
people, chronological labels and held-player exclusions. The broad and more
specific profile counts are saved separately. Tatis's broad absent-career sets
contain 866/208 people, but his audited age/roster/job/work profile has zero in
both. Hoskins has 913/225 broadly, but only five/four matching people. Their
different roster and job inputs produce 61 versus 367 expected PA; neither is
an identical generic comeback profile.

Franco has 149/148 matching *sporting* profiles, but those strata do not include
his legal restriction. The preceding availability audit has no exact legal
analogue. Do not use these 149 sporting profiles to certify a 99% participation
forecast under an unresolved restriction. Ordinary workload and eligibility
are distinct uncertainty sources.

Kurtz initially appears to have no matching active college-draft example. That
statement is qualified by the [cached-school support amendment](hitter-route-support-school-amendment.md):
the learner retains old blank school classes, although V65 already recovered
broad college backgrounds. With the existing overlay, his matched full/active
counts are two/one, not one/zero. The two people are Zunino and Brooks Lee;
only Zunino participated the next year, with 193 PA. This is still thin support,
not evidence that his 489-PA breakout was certain or that a college boost is safe.
V66 already tested the school substitution without a useful gain; it is not rerun.

The support-only correction changes 22 source-row fresh-college classifications
and 23,370 repeated training-support records, not that many newly added people.
No junior/senior information is invented and no new college facts are collected.

## Decision and next substantive work

The [player review](hitter-route-support-player-review.md) includes actual counts,
saved paths, both support views and five outcome-blind training peers per case.
It confirms distinct problems: thin elite entry, some missed upper-minors readiness,
rare interrupted careers, foreign entrants, genuine downside risk, and occasional
component cancellation. Source flags or coarse support cannot settle those issues.

Close this diagnostic with no predictor or architecture adoption. Do not repeat
the school, generic return, separate conditional-prospect, tree-capacity, available-
season or team-record comparisons. Existing forecasts remain the anchor.

The next substantive design should follow the already completed
[production-learning diagnosis](hitter-evidence-learning-diagnosis.md): preserve
the useful talent routes and test common event learning instead of learning
seven tiny foreign-only effects after attenuating them and applying a large
inherited penalty. Resolve the pooled-event source units, translation references,
prior strength and actual nested memberships before fitting. Hold opportunity
fixed in that talent comparison so a gain cannot be credited to a new job model.
Sparse-entry and interrupted-career availability still need separate qualification;
a talent improvement will not automatically fix their PA. The long-range goal
remains active, not certified full WAR, club-control value or public-system superiority.
