# Test dated status evidence in hitter playing time

2026-10-03. The question is whether already captured December-known status
records improve expected next-calendar-year MLB PA beyond the corrected
historical hitter baseline. Hitting ability is held exact. This is one bounded
source and workload contrast, not another injury-category sweep.

## Population and comparison

Keep all 30,506 evaluation rows and the 35 chronological player-group folds
from the numeric repair. Reuse its 63,282 source rows, with training outcomes
mature by each origin; exclude the canceled target season and incomplete
origin-2020 windows. Never read protected 2026 outcomes. Retain prospects,
inactive players, unsuccessful returns and established hitters of all ages.

The benchmark is corrected baseline V53. The candidate adds ten status inputs
to its appearance and active-player PA models, using exactly the same shallow
histogram boosting settings and training weights. Its batting rate, replacement
accounting and existing definitive-status rules remain bit-exact. Do not change
the original roster flag or silently turn activation into certified recovery.

## Sources and definitions

Reuse the reviewed transaction normalization and fact catalog from V29b,
including its event-versus-availability date repair. Raw annual captures cover
2015 through 2024. Only versions available by December 31 of the forecast year
may contribute. Historical publication vintages are not certified; captured
historical records are not guaranteed original December snapshots.

The ten added inputs are:

1. Captured transaction-era coverage.
2. Observed MLB medical scope, requiring recent MLB PA and origin 2016 or later.
3. An acquisition in the preceding 365 days.
4. An explicit minor-contract event in that period, not a verified current deal.
5. Unresolved ordinary MLB scope departure, excluding nonmedical restrictions.
6. Log captured MLB absence days in the preceding two years.
7. An open captured MLB injury spell.
8. A full MLB missed season with prior 200 PA and captured medical absence,
   without an observation-scope interruption.
9. Recorded offseason MLB activation following a captured injury spell.
10. Unresolved nonmedical restriction, retained as a warning, not permanent zero.

Early coverage is explicitly unknown. Neutral numeric fills are accompanied
by the coverage inputs; absence of an all-level medical record is not health.
Medical fields are zero-filled only with their observed-scope flag retained.
Acquisition is not a starting job. Game suspensions are not calendar-day bans.
The generic departure flag is suppressed while a nonmedical restriction is
unresolved, avoiding the old suspended-star demotion mechanism.

Before any fit, save all actual head/subset preflights and distinct-player
support by origin-known stage, age, prior MLB workload and status. Save positive
and zero-outcome support for each added signal. If fewer than twenty distinct
exposed training players occur in a head, disable that particular status input
in that head, explicitly recording the fallback. Keep unsupported test rows.
Coverage controls are never disabled. This is a sparse-support precaution,
not proof twenty players identify a medical or legal effect.

## Scoring and stopping

Primary score is equal-target-year expected-PA squared error; report PA RMSE,
MAE, probability scores and delivered batting-plus-replacement error alongside
player-cluster paired uncertainty. Expected PA must remain a mean, not a median
chosen to win MAE. Compare the identical 2,627 common Steamer/ZiPS rows, retaining
the unknown archive-date and environment qualifications. Report origins,
current MLB, never-debut, absent former regulars, brief debuts, 600-PA regulars
and medical/context groups, with actual and predicted totals. Do not force a
fixed cohort to equal the whole league.

Save and replay every fitted head. Candidate PA equals appearance probability
times bounded conditional PA; neither a useful source correction nor a
small pooled improvement certifies full player value. Check clipping frequency
and no dropped evaluation rows.

Before disposition, trace Judge at the 2022 cutoff, McLain 2024, Lux 2023,
Tatis 2022, Franco 2023, Ford 2023 and Langford 2023. Add the largest delivered
gain and harm, false high and low, and an ordinary case as needed. Use actual
source statistics, all model inputs, saved head traces, dated context,
actual training support and four peers selected only from origin-known
information. Distinguish sensible risk from a lucky miss or unsound mechanism.

Close this contrast after review. Keep a coherent candidate only if the
effect is meaningful and does not introduce material cohort or baseball harms.
Do not sweep penalties or add more diagnostic categories after seeing scores.
No frozen forecast or deployed explorer changes are authorized.
