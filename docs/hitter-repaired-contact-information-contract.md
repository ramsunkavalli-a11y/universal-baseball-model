# Testing repaired contact information against future MLB hitting

2026-10-04. This comparison asks whether reliable minor-league contact detail
adds useful information beyond the current count histories and the separately
tested translated hitting profile. Source repair and sixteen source walks are
complete. No new projection has been fitted when this contract is saved.

## The comparison

Keep exactly 30,506 forecasts, 63,282 source rows and the existing seven origins
and five whole-player folds. Keep appearance probabilities, conditional PA,
expected PA, certified non-arrivals, target counts and replacement references
unchanged. Training outcomes mature by each cutoff, exclude target 2020 and
exclude the entire tested player fold. Predictor histories end at each row's
own origin. The canceled 2020 minor season remains unavailable.

Preserve the existing count-based hitting anchor and the translated Ridge
challenger. Fit three additions to the translated head's 220 inputs:

1. Coverage control: contact exposure by the fourteen existing level buckets,
   total exposure, classified fraction, availability and historical source-year
   indicators. Exposure is not a hitting grade.
2. Contact mix: the same control plus ten ground-ball, line-drive, outfield-fly
   and popup shares, distinguishing pull, center and opposite direction.
3. Joint detail: the same mix plus all ninety contact-type and outcome cells.
   Outcomes distinguish 1B, 2B, 3B, HR, error, fielder's choice reach, sacrifice
   fly, multi-out and other out. Encode each cell as its stabilized joint share
   minus its contact-type share divided by nine. Thus the new block contains
   within-type outcome detail rather than a second copy of the contact mix.

All use Ridge alpha 100, the existing deterministic input scales, equal-origin
times actual next-year PA weights and the same active training rows. No tuning,
parameter sweep or outcome-selected level route. Adding a representation also
changes regularization geometry; differences are not a model-free causal effect
of more information. Save all fitted coefficients and replay every fitted head.

The primary contrasts are mix versus coverage and joint versus mix. Also show
each versus translated and current anchors. Primary replacement is restricted
to never-debuted players with classified contact evidence. A separately locked
all-player sensitivity replaces measured players, including young MLB players
with recent minor contact. Players without contact keep the appropriate anchor
exactly; do not credit a changed star forecast to contact we never measured.

The archive begins in 2016. Consequently 2016 test folds have no active training
examples with this contact block. Keep them in every overall score and use the
translated anchor, explicitly flagging the fallback. In any other fold, fewer
than twenty distinct active training people with contacts also triggers this
predeclared whole-fold fallback, not selective removal of difficult players.
Save finer distinct-person support by stage, debut, age, ranking, sample size,
new-draftee/thin-entry profile and exposure buckets. Twenty is a warning/fallback
threshold, not proof of adequate support for every rare profile.

## Measurements and adjustment limits

Use only the sealed repaired 2016–19 and 2021–24 player-season-actual-league
measurements. Pool three calendar seasons with fixed 1/.8/.6 contact weights.
Keep actual league IDs and separate bucket exposures in the source trace;
Mexico never becomes AAA and rookie identities stay visible. Pooling the ninety
cells across these exposures remains a limitation; it is not an MLB equivalency.

For classified exposure N, stabilized cell share is (weighted count+.5)/(N+45).
Each shape share is the sum of its nine cells. Center shapes on .1 and divide
shape and within-shape detail by .1. With no classified contacts both blocks
are zero and availability is false: this is missing evidence, not measured
average production. Log exposures use log(1+N)/log(1201). No learned prior is
borrowed from a future season or from a held player's labeled examples.

These raw measurements are not park- or opponent-adjusted. This bounded test
revisits the earlier raw ninety-cell result on repaired, matched inputs before
introducing a different learned adjustment. A loss cannot reject park-neutral
contact talent; a win cannot justify calling the block park-neutral or promoting
it without adjustment review. Old event-fold park residuals are not imported
because they have not established exclusion of the outer forecast fold. MLB
players have no own MLB contact in this source. That coverage gap remains.

## Targets and checks

Primary rate loss is actual-PA-weighted error among future MLB hitters who had
not debuted at origin, giving each target year equal weight. The response is
fixed-event batting wins per 600 PA relative to the realized target-season MLB
average. Independently reconstruct it from target event counts and environments;
future environments validate labels only and are never predictors. Also report
equal-player rate error and the common-origin reference sensitivity.

Delivered offense uses the existing common-origin fixed-event batting plus
replacement reference, not published full WAR. Retain every non-arrival with
zero delivered value. Score all players, never-debut, upper/lower minors,
measured/unmeasured, each origin, new draftees, thin histories and the matched
2,627 public forecasts. Show bias, PA/value totals and player-clustered nominal
95% paired intervals. Public event forecasts retain their snapshot/environment
qualifications. No talent-superiority claim from recentering public predictions.

Before fits, verify source approval and hashes, cell accounting, actual league
identity, chronology, exact training/evaluation IDs, finite inputs, all full and
active preflights, contact-aware profile support and anchor head replays. Save
all checks and hashes before any new fit. No forecast clipping; show mathematical
rate-bound violations and empirical extrapolation separately. Preserve all old
columns and prove opportunity unchanged.

## Actual player review and disposition

Fix Kurtz 2024, Langford 2023, Reynolds 2018, McNeil 2018, Meadows 2018,
Julio Rodríguez 2021, Alonso 2018, Holliday 2023, Maitan 2017, Judge 2024 and
Soto 2023 before fitting. Add each arm's largest value gain/harm, false high/low
and ordinary active case, and the joint arm's largest active-rate gain/harm.
Keep all selected cases. Peers are selected without target outcomes, matching
origin/stage/debut and using age, exact level exposure, performance, draft and
rank evidence; show any remaining pedigree/readiness differences.

Trace actual histories, actual league contact counts, inputs, linear sums,
coverage/mix/detail contributions, unchanged arrival and PA, forecasts and future
MLB reality. A same-fit neutral-detail probe explains mechanics only; it is not
a causal or promoted forecast. Complete the readable review before disposition
or the next modeling experiment. Examine origins and totals, not just a pooled
score or a famous successful prospect.

No automatic adoption from a tiny uncertain gain. Retain a challenger only if
its rate/value behavior is coherent and its adjustment/coverage limits remain
explicit. A negative raw result does not reject adjusted contact. The practical
hitter goal still requires better public workload, cohort reasonability, useful
uncertainty and an explorer. Protected 2026 outcomes, all frozen files and the
deployed explorer remain untouched.
