# Correct the designated hitter inventory before allocating defensive jobs

2026-10-07. The reviewed source now counts Ohtani's simultaneous pitching and
DH starts. This corrects 65 starts, not his hitting or defensive ability. The
larger forecast problem remains: too many shortstop outs and too little
first-base/DH time. No new accuracy gain or production change is claimed.

## What changed

The original annual fielding source describes position appearances but omits
simultaneous P/DH starts from its DH-start total. All 87 pitching starts from
the five source player-seasons with pitching starts and a DH appearance were
checked against official pitching logs and individual boxscores. Ohtani gains
28 DH starts in 2022, 23 in 2023 and 14 in 2025. Weaver's one pitching start and
Wainwright's 21 remain unchanged: neither started those games in the batting
order. Their incidental DH appearances do not justify added starts.

The additive view is separate from the original source. All eight fielding
positions, batting inputs, defensive quality, native opportunities and saved
forecasts are unchanged. The reviewed league DH total now equals the league's
team-game count in every 2022–2025 season. Before correction, the apparent
shortfall was exactly Ohtani's pitching starts.

Two games required a rule-aware distinction: 2022-08-21 and 2023-07-27 have no
later DH appearance in the final position list. The starting pitching and
batting slots still establish the dual starting role under
[Rule 5.11(b)](https://img.mlbstatic.com/mlb-images/image/upload/mlb/hhvryxqioipb87os1puw.pdf).
The archived initial parser incorrectly required a later DH appearance. The
additive amendment fixes that requirement for any qualifying player, not just
Ohtani. Relief pitching, pinch hitting, absent role evidence and pre-2022 starts
remain ineligible.

## The remaining forecast gap is much larger

| Forecast origin | Own-history DH starts | Pooled-prior DH starts | Total forecast | Actual matched DH starts after source repair |
| --- | ---: | ---: | ---: | ---: |
| 2022 for 2023 | 3,111.49 | 970.97 | 4,082.45 | 4,800 |
| 2023 for 2024 | 3,183.34 | 1,146.17 | 4,329.51 | 4,850 |
| 2024 for 2025 | 3,094.09 | 1,191.00 | 4,285.09 | 4,860 |

The source repair changes only about 20 and 19 expected DH starts through
Ohtani's own-history term at the first two origins, with the saved pooled prior
held fixed. That is a diagnostic sensitivity, not a corrected refit. It cannot
explain hundreds of missing DH starts or surplus shortstop jobs.

The pooled exposure priors also combine different DH environments. Across the
five held-player cells, 74.9%, 59.7% and 49.7% of the broad prior's training PA
come from years with only one DH league. These are actual PA-weighted training
shares, not a count of calendar years. The source verifies one DH slot per
team game in 2020, about half in 2019/2021, and both leagues from 2022 onward.
The prior does not explicitly transport those opportunities into the new rule
environment. This is a design limitation, not proof that it explains the entire
bias; ordinary DH and nondesignated-hitter role groups behave differently.

Every origin's captured forecast population covers all of that origin's MLB
fielding and DH starts. That does not prove complete future coverage: the actual
next-year unmatched remainder is 60 DH starts in 2023, eight in 2024 and zero
in 2025, plus separate fielding outs. Those are diagnostics, not budget inputs.
An allocator must preserve a remainder for missing players instead of using
the future cohort coverage to force known players into all available jobs.

## Player calculations show what a correction must preserve

All seven fixed focal origins and 21 peers are traced in the
[player walkthrough](../reports/model-evidence/defense-budget-v13/player-walkthrough.json).
Peers share the origin, stage and primary role, then are selected by nearest
age/current MLB sample, without looking at outcomes. Primary-role matching is
not an assertion that their physical defensive skills are interchangeable.

Ohtani's 2022 input has 666 MLB PA and originally 125 DH starts; the reviewed
count is 153. Expected PA is 553.72. Own-history weight is 666/766 = 0.86945;
the selected DH/current-MLB prior has 23 people and 0.16432 DH starts per PA.
The saved prediction is 90.36 own-history plus 11.88 prior = 102.24 DH starts.
Correcting only the own-history numerator adds 20.24 starts. The 2023 target
changes from 112 to 135 actual DH starts, while all eight nonpitcher fielding
positions remain zero. The positional source correction is −2.48 runs; the
own-input sensitivity is −2.19 runs. Neither is a new validated value forecast.
His peers include Harold Ramírez, who gets more DH time than forecast, and
Franmil Reyes/Zack Collins, who get less; a blanket DH increase would hurt exits.

At the 2023 origin Ohtani's corrected source is 135 instead of 112 DH starts.
The saved model forecasts 104.87; the source-only sensitivity adds 18.75, versus
159 actual in 2024. Expected PA is still 569.88 versus 731 actual. At the 2024
origin there is no own-source correction: 159 starts are already present. The
model forecasts 124.18 versus 158 corrected actual starts in 2025. Expected PA
is 590.14 versus 727 actual. Correct source alone does not repair workload.
Rooker is underforecast while Calhoun and Ramírez receive no MLB PA in 2025;
the fixed peer review retains both outcomes.

Ohtani's old tiny outfield history also survives through fallback. His 2021
source has three LF outs and 22 RF outs, but zero nonpitcher fielding outs in
2022 and 2023. The repair predicts roughly 130 and 142 future outfield outs at
those origins. This is not evidence of a meaningful current outfield role.
Pure-DH evidence must be distinguished from an unknown defensive repertoire;
aggregate raking should not revive these appearances to fill fielding jobs.

Schwarber is a different failure. The 2023 source has 57 DH starts and 2,617 LF
outs, with 720 PA. With 521.86 expected PA and an own-history weight of 0.87805,
the model predicts 36.28 own plus 1.51 prior = 37.78 DH starts, and 2,010.41 LF
outs. He actually has 144 DH starts and only 123 LF outs in 2024, with 692 PA.
The model repeats a past role rather than identifying the role change. His
positional forecast is −7.53 runs versus −15.77 actual. This is not a DH-count
source error. Profar stays mostly in the field, Yelich receives some DH time,
and Gurriel's projected DH use is too high: their review rules out indiscriminately
moving left fielders to DH. Dated assignment evidence needs its own cutoff.

Alvarez shows the opposite risk. With 635 origin PA, 94 DH starts and 1,263 LF
outs, the model predicts 82.14 DH starts and 1,065.09 LF outs at 546.54 expected
PA. He receives 199 PA, 32 DH starts and 348 LF outs. His positional penalty is
already too large: −10.70 versus −4.05 runs. Raising everyone's DH allocation
to make the league total look right would aggravate this workload miss. Peers
include more DH time for Larnach, no MLB time for Jiménez, and limited time for
Fry; retirement or nonarrival is not a measured defensive grade.

Witt is a counterexample to a blanket shortstop haircut. The 2024 source has
4,181 SS outs, one DH start and 709 PA. The model forecasts 3,898.43 SS outs
and 1.09 DH starts at 657.12 expected PA. Actual 2025 usage is 4,020 SS outs
and four DH starts, with 687 PA. Positional value is already close: +6.57 versus
+6.46 runs. Perdomo, Edwards and Henderson are the origin-selected peers. The
league's excess SS total does not mean every individual shortstop is overrated.

Eldridge's latest minor record is first base, not measured MLB defensive quality.
At zero current MLB PA, the whole exposure forecast uses the supported prior:
68.13 expected PA, 352.31 first-base outs and 2.53 DH starts. He gets 37 MLB PA,
102 first-base outs and six DH starts in 2025. Clifford, Ariza and Isaac do not
reach MLB in that target year. Ariza's upper-minor label rests on only two AA
catching starts, while most of his latest fielding work is complex-ball first
base. The label-based peer rule is too coarse to certify comparable development
evidence; his full record remains visible. Keep their quality unknown and their
possible positions distinct from current major-league job guarantees.

## Verification and next decision

Independent arithmetic reconstructs the 87 captured starts, 65 dual-role
additions, 22 negative controls, all 22 season inventories, 1,128 saved prior
tables and all 12,432 forecast DH decompositions. Twenty-nine focused checks
pass. The corrected source ledger is usable; this is not predictive validation.
The earlier delivered-value result retains its original DH-start approximation
and requires the additive target correction in subsequent matched comparisons.

Next use this reviewed inventory for one predeclared physical-budget comparison,
with unchanged batting and defensive skill, explicit cohort remainder and
individual-role checks. Do not blanket-scale SS/DH, invent future positions,
normalize missing defensive runs to a WAR quota, or treat balanced totals as
proof of player-level accuracy. Pure DH, mixed roles, prospective first arrivals,
exits and reasonable existing shortstops must all survive the player review.
The separate Lovich batting defect, frozen package, explorer and 2026 selection
remain unchanged. The broader defense goal remains active.

Evidence: [compact source inventory](../reports/model-evidence/defense-budget-v13/source-summary.json),
[independent verification](../reports/model-evidence/defense-budget-v13/independent-verification.json),
[source contract](defense-budget-v13-source-contract.md),
[rule amendment](defense-budget-v13-rule-source-amendment.md).
