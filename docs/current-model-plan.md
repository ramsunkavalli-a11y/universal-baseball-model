# Current model plan

Updated 2026-09-10. The user wants the model made credible before further interface
work. The [product roadmap](product-roadmap.md) is now the authoritative active plan;
this document retains detailed evidence from the current hitter/opportunity workstream.
Earlier experiment contracts remain historical records.

## Phase 2 priority update — 2026-09-10

Proceed now with the broad, source-supported improvements that apply across the
player universe:

1. dropout-adjusted aging, while keeping conditional skill separate from return and
   workload probability;
2. explicit hierarchical fallback ladders for sparse coverage;
3. component-level uncertainty followed by calibration of the combined ranges;
4. dated injury and transaction hazards in the workload path;
5. finer minor-league league, park and run-environment translations;
6. partial pooling so small samples move toward the correct population rather than
   an arbitrary zero; and
7. rolling probability, quantile and interval calibration.

Pitch-quality and command models are deferred until the next phase because their
all-level source coverage is not ready. Transaction-price validation is also deferred;
it is not required to make the present research preview more coherent. The existing
age/level opportunity tables already provide a first hierarchical, partially pooled
fallback. New work should measure and improve that foundation rather than create a
parallel system.

The first finer-context measurement is complete. Official league and home-venue
identity covers all 695 saved affiliated team-seasons. A partially pooled
league-within-level translation was selected on 2024 and confirmed on 2025, but did
not pass: hitters lost the selection year and pitchers lost confirmation. Retain the
level-only translation. The next park candidate must use actual home/away or game
context; venue identity alone is not a park factor. See the
[source result](affiliated-team-context-result.md) and
[league test](affiliated-league-translation-result.md).

The next injury additions are also resolved. Broad age and recent-IL-recurrence
cells, partially pooled toward the validated IL-type/elapsed baseline, failed the
2024 four-metric gate. They are not promoted and were not tuned against 2025. Keep
the existing injury hierarchy; diagnosis remains deferred until consistent source
coverage exists. See the [result](injury-return-age-recurrence-result.md).

The first distribution-shape test confirms that annual WAR cannot be represented by
one bell curve. A zero-activity mass plus active-player distribution materially
improves overall interval score, but the current conditional-active spread then
undercovers. The next rolling-origin uncertainty build must calibrate participation
and conditional-active shape separately, then combine them. Do not use a global width
multiplier. See the [hurdle result](war-hurdle-uncertainty-result.md).

Rolling 2022–2025 participation replays now reject a blanket logistic calibration
layer. Raw probabilities beat the recalibrated version on pooled 2023–2025 proper
scores for both hitters and pitchers. Keep raw participation probabilities and move
the uncertainty work to the conditional-active distribution. See the
[rolling result](rolling-opportunity-calibration-result.md).

Within that distribution, the conditional positive-workload model already achieves
81.8% hitter and 80.1% pitcher coverage against an 80% target over 2022–2025. Hold
workload uncertainty fixed. Rolling prior-origin performance scaling raises
conditional-WAR coverage from 71.8% to 81.5% for hitters and from 71.4% to 80.7% for
pitchers while improving pooled interval score. The exact workload/performance mixture
is implemented and improves the 2025 overall score without changing point estimates.
The combined mixture then improved interval score in every 2022–2025 origin for both
components and is now in the private playable build. The 2023–2025 pooled improvement
is 19.5% for hitters and 19.2% for pitchers. Point WAR and Model FV do not change; only
WAR and contract-value ranges change. See the
[combined result](rolling-combined-war-uncertainty-result.md).

The required flexible team-depth challenger is also complete. Supported historical
position and role movement reassigns unused group capacity before cuts, fixing the
rigid model's structural flaw. It still produces a mixed RMSE/MAE tradeoff versus the
simpler broad team cap for both hitters and pitchers. Retain only the broad team cap
and close aggregate position-share tuning on disclosed 2025 outcomes. The next depth
input, when pursued, must use dated player-level roster, option, IL and competition
state. See the [flexible result](flexible-team-capacity-replay-2025-result.md).

## Goal

Build a comparable trade-value estimate for every player, updated after each game
and material transaction. The recommended common measure is expected remaining
surplus value of transferable team rights, with projected MLB wins and uncertainty
shown separately. KATOH-style prospect production is one component of that goal.

Execution now follows the roadmap's ten steps: eight Phase 1 foundations leading to a
complete universal research valuation and two Phase 2 granular-improvement steps.

Read the [repo and literature direction review](trade-value-direction-review.md).
It governs the broader sequence: player/rights coverage; reuse of existing models;
career paths and control/cost data; integrated research valuation; historical
game-by-game replay. Next-season batting refinement alone cannot deliver the goal.

The [GitHub projection-method review](github-projection-methods-review-2026-09-10.md)
now governs the next model-development block. Its immediate P0 is a joint score of
aging, return/attrition and workload that retains non-returners, followed by
component-specific shrinkage selected with walk-forward tests. This does not merge
skill and opportunity models: it evaluates their product on the production target
that ultimately enters WAR and value.

## What we have learned

The active production-focused execution sequence and completed Tango-style
diagnostic are in [Tango-focused model work](tango-focused-model-work.md).
Career production is the main modeling effort. The financial/control layer must
have a clear interface, but should not displace batting/pitching development.
Recover the existing richer opportunity model before designing another challenger.

All new broad feature searches now follow the binding
[model-search and validation policy](model-search-validation-policy.md). The framework
is not limited to demographics: it covers legitimate forecast-date StatsAPI, PBP, and
derived performance, development, role, workload, process, defense, baserunning, and
context inputs. It requires time-ordering, an outcome embargo, nested selection,
regression for sparse evidence, proper scores, calibration, uncertainty, and supported
subgroup review. Skill, opportunity, workload, and contract value remain separate
until final assembly.

That policy now has a reusable [experiment harness](forecast-experiment-harness.md).
Future age, level, handedness, origin, role, performance, PBP and context families use
the same frozen-family, chronology, common-cohort and promotion checks. This enables
broad testing without converting the winning noise from a large search into a player
value adjustment.

**Recovery completed for 2024:** original forecasts were found and hash-verified.
All 3,985 player IDs and official PA targets match O2026D. The recovered model
improves participation Brier by 12.6% and PA RMSE by 12.5%; lower-level exceptions
remain. [Verified comparison and next step](recovered-opportunity-comparison.md).
Next recover its dated feature pipeline and resolve B2-dependent inputs before
integration. O2026D remains the simple benchmark; no release promotion occurred.

- v1's batting representation is not a sound product foundation.
- G0's terminal-outcome history is useful but mixes competition levels.
- Two final-output calibration fixes failed; do not revisit their tuning.
- Competition-normalized history materially improves the MLB-conditional batting
  estimate for prior-minor players. Its all-level prospective mixture still failed.
- Remaining MLB-conditional problems include optimism, weak individual separation,
  and selection into MLB/playing time. The 29% improvement is not career-value accuracy.

## Completed batch: C2026C

Calibrate the already saved MLB-conditional estimates using ONLY earlier MLB
forecast/results pairs. Test two fixed alternatives: a probability-score calibration
and a direct batting-value calibration. Compare to the unchanged transport component,
G0, C0, and Marcel on identical players. Examine minor-origin players explicitly.
See [the exact experiment contract](hitter-v2-MLB-calibration-contract.md).

Both candidates failed: minor-origin pooled improvements were 1.18% and 1.87%,
with uncertainty intervals spanning zero and damage to established MLB players
in 2023. [Results and error audit](hitter-v2-C2026C-result.md).

The reason for testing the second alternative was substantive: fitting every
terminal event equally under log loss need not optimize the batting-value estimate.
Keep coherent probabilities and use event-score guardrails to detect harmful tradeoffs.

## Next sequence

**Current research P0 (2026-09-10):** build the complete next-season transition
scoreboard, including observed inactivity, and compare the incumbent separate
skill/opportunity bundle with simple baselines. Then tune hitter and pitcher
component shrinkage independently inside the development window and freeze it before
later-season scoring. Do not change playable values until the joint production gate
passes. Do not reopen demographic families or use outside FV to repair rankings.

The complete transition denominator is now implemented: 5,018 of 21,742 observed
source player-seasons have zero MLB workload the next year and can no longer vanish
from the combined score. The first component-specific affiliated pitcher regression
also finished and failed: its 2024 gain reversed on 2025 in both proper scores. Retain
the 800-BF universal pitcher prior, do not search more combinations on those seasons,
and proceed to attaching cutoff-safe age and incumbent opportunity predictions to the
joint transition scoreboard.

The parallel hitter component-specific test improves both 2024 and 2025 point scores,
but it is mostly the previously tested 400-PA challenger and still misses the frozen
2025 Brier uncertainty gate by a narrow margin. Retain 1,200 PA. Both hitter and
pitcher regression searches are now closed on the disclosed 2024–2025 source; broader
history or a future untouched season is required before revisiting them.

The zero-inclusive pitcher aging replay is now complete on the frozen March 27, 2025
forecast. Holding opportunity and all other inputs constant, Tango aging improves
component log loss, WAR MAE and WAR RMSE versus no aging across all 5,090 pitcher
rows, while removing 19.0 WAR of aggregate optimism. The paired MAE improvement is
clear; the MSE interval crosses zero. Retain Tango aging and use this same joint
scoreboard for any future curve. No current value changed.

The identical hitter replay gives the opposite answer. Removing the generic Marcel
age multiplier improves component log loss, zero-inclusive WAR MAE and WAR RMSE and
removes 35.1 WAR of aggregate optimism. The paired MAE gain is clear, while the MSE
interval crosses zero. Because the counterfactual was constructed after 2025 outcomes
were disclosed, current values remain unchanged. Freeze no hitter aging as the leading
simple challenger for the next valid confirmation; any richer curve must beat both it
and Marcel without dropping non-returners.

That confirmation is now frozen before final 2026 outcomes. The October 15, 2025
forecast supplies 3,907 identical hitter rows for Marcel and no-aging candidates;
only the event-rate age adjustment differs. Marcel projects 611.2 hitter WAR and no
aging 581.5. The hashes and decision rule are locked in
`model_artifacts/hitter-aging-2026-confirmation-forecast-2026-09-10/`. Do not score it
until the regular season is complete and official totals have stabilized.

The matching pitcher confirmation is frozen on 5,206 identical rows from the same
October 15, 2025 evidence. Tango aging projects 449.7 pitcher WAR and no aging 474.1;
only the age treatment differs. Its fixed gate tests component loss, zero-inclusive
WAR error, aggregate bias and supported age bands after final 2026 totals. The frozen
files live under `model_artifacts/pitcher-aging-2026-confirmation-forecast-2026-09-10/`.

A first explicit survivor-bias correction is also complete for pitcher aging. An
age-by-prior-BF return model materially beats a population-only return baseline on
2022–2025, and bounded inverse-return weighting slightly improves the modern fitted
aging curve. The adjusted curve still loses to Tango and no aging, so Tango remains.
Retain the return model for opportunity/attrition work; do not confuse a good return
model with evidence that a new conditional skill curve won. See the
[survivorship-adjusted result](survivorship-adjusted-pitcher-aging-result.md).

The matching hitter test reaches the same structural lesson. Age and prior PA
strongly predict next-season return, and survivor weighting slightly improves a new
fitted component curve, but that curve and Marcel both lose to no aging on 2022–2025.
Keep the no-aging hitter challenger and move the return signal into opportunity, not
skill. See the [hitter result](survivorship-adjusted-hitter-aging-result.md).

The frozen 2025 uncertainty replay now includes proper interval scores and fixed
forecast-time participation calibration bands. Aggregate active probabilities are
close, but both hitters and pitchers are underpredicted in the 30%–60% band. Do not
fit a 2025-only correction. The next calibration challenger must learn a monotone
mapping on earlier rolling origins and freeze it before later scoring. See the
[probability calibration result](forecast-probability-calibration-2025-result.md).

The existing injury-return hierarchy now has a true later-period test. Fit on
2022–2023 and applied unchanged to 2024–2025, broad IL type plus elapsed days beats
the population mean on return Brier/log loss and availability MAE/RMSE in each year.
Keep it. Phase 2 may next add age and prior IL recurrence, but both must beat this
validated baseline and remain cutoff-safe. See the
[injury-return result](injury-return-out-of-time-result.md).

The playable build's fallback ladder is now enforced by code. All 3,940 hitters and
5,276 pitchers have complete six-year paths with explicit opportunity, workload and
talent provenance. Years 1–4 use selected opportunity models; years 5–6 back off to
partially pooled age/level history, plus pitcher role. Conditional skill backs off
from MLB history to translated affiliated evidence to a population prior. See the
[fallback coverage result](current-fallback-coverage-result.md).

**Current P0:** use the corrected playable-build chain
`current-opportunity-paths-v2 -> phase2-workload-paths ->
phase2-conditional-war-paths -> phase2-war-uncertainty/model-fv -> current value`.
The prior explorer silently joined the older generic opportunity paths. That defect
reduced projected six-year WAR for 940 debuted pitchers from 1,325.5 to 1,108.1.
The corrected materializer records both input hashes and the opportunity model ID;
the explorer refuses to open a stale or changed source. See the
[pitcher funnel audit](pitcher-value-funnel-audit-result.md).

The correction materially repairs MLB pitchers but not prospect pitchers. The current
nested result totals only 68.1 expected WAR across 3,849 pre-MLB pitchers and tops out
at 2.66 WAR. Do not repair that output with an FV floor, a changed grade mapping, or
the weak age/level/hand adjustment. A four-year replay finds the existing constant-
hazard probabilities are already optimistic, so low arrival odds are not the cause.
The next test targets conditional MLB WAR and linked career production, with failures
retained, earlier-cohort selection, and one untouched later cohort. See the
[horizon audit](prospect-horizon-extrapolation-result.md).

The first [conditional-quality test](prospect-pitcher-conditional-quality-result.md)
also rejects the available aggregate-feature challenger. Minor-league component rates,
age, level, workload, role, hand, origin and official draft pedigree do not beat a
population mean on later successful pitchers. A tier-quality relationship also
reverses across periods. The next input class must add genuinely new cutoff-safe
pitch/process or batted-ball evidence, or a broader mature cohort; do not rescue the
same features through more tuning.

The first all-level batted-ball candidate is now rejected too. Ground-ball rate,
popup rate, pulled-air rate and pulled-ground rate were tested in a fixed order with
exposure shrinkage. Ground-ball rate improved 2022-to-2023 error, then failed to
improve 2023-to-2024 error under the unchanged 2021 fit. The later reversal controls;
no pitcher projection or value changed. Exact PBP asset hashes and results are in the
[pitcher contact increment audit](pitcher-contact-increment-result.md).

The linked [historical pitcher performance-path source](historical-pitcher-performance-paths-result.md)
is also ready. The next career-value challenger must sample performance, workload and
role from the same historical pitcher path. It must not keep the current constant
prospect rate across every simulated year, and each replay may use only career paths
fully observable by that forecast cutoff.

The current-date linked-path sensitivity changes pitcher-prospect WAR from 64.6 to
1,058.7 in total and the 99th percentile from 0.69 to 2.78. This establishes that the
constant prospect-rate assumption is the main compression source, but it is not a
promotion result. The cutoff-safe 2021 development replay finds plausible scale and a
clear gain over zero for the simpler arrival-only pooled path; tier splitting adds no
reliable gain. The identical-row incumbent replay is also complete: the incumbent
predicts 0.047 mean WAR and 0.558 RMSE versus 0.127 and 0.551 for the arrival-only
path, with 0.090 observed. The paired improvement interval crosses zero, so no method
is promoted. Prespecified subgroup diagnostics are retained as failure checks, not
new model-selection opportunities. The next P0 is genuinely later confirmation.
Current rankings stay unchanged.

The same linked-path replacement is rejected for hitters. A cutoff-safe 2021 replay
of batting-plus-replacement WAR finds incumbent RMSE 0.955, tier-linked RMSE 0.960
and arrival-only RMSE 0.978 on 3,260 players. This test restores intentional walks
from the original StatsAPI captures and excludes unavailable historical defense,
running and position inputs from both sides. Do not transfer the pitcher decision to
hitters or use the disclosed subgroup results for post-hoc tuning.

The reusable continuous-outcome gate adds a second reason not to promote the pitcher
path from this evidence: its small RMSE gain comes with a clear MAE loss (`0.154` to
`0.199`). The hitter path has the opposite tradeoff—better MAE but worse RMSE and
absolute bias. Future path candidates must improve the declared integrated target
without hiding typical-player damage behind a few large tail errors.

A simple exposed-cohort blend sensitivity finds a useful future hitter challenger:
75% incumbent plus 25% linked improves RMSE, MAE and absolute bias at the point
estimate, though its RMSE interval crosses zero. Preserve that exact weight for a
later untouched test; do not tune it further or change current hitter values. No
pitcher blend is clean because all tested weights worsen MAE.

The next frozen test is the [conditional-WAR bridge](prospect-conditional-war-bridge-plan.md):
fit one strongly regressed core model on 2018 and evaluate two-year component WAR on
the 2021 cohort, with all non-arrivals retained in the end-to-end score. It asks
whether cutoff-known production, age, level, role and evidence volume can improve the
positive MLB tail without using demographics as talent or changing arrival odds.

That test is now complete. The regressed core candidate improves end-to-end RMSE and
MAE, paired uncertainty, and arrived-player RMSE for both hitters and pitchers. It
misses the frozen gate only because absolute bias moves slightly farther from zero.
Keep the exact form as promising research; do not use the disclosed outer cohort to
add a calibration correction. Current values remain unchanged.

The next frozen gate is an unchanged-fit [2022/2023 stability extension](prospect-conditional-war-bridge-stability-plan.md).
It must not refit or recenter the 2018 bridge. Later cohorts test whether the small
bias failure and accuracy gains persist; they remain retrospective evidence because
those seasons have been inspected elsewhere.

The unchanged-fit stability extension is complete and fails. Later hitter cohorts
reverse the arrived-player RMSE gain; later pitcher cohorts retain worse absolute bias
and uncertain MSE gains. Reject the ridge as a current replacement. Preserve the
evidence that core features improve typical-player MAE, then move to a predeclared
positive-tail hurdle rather than tuning this conditional mean.

The next exact test is now frozen in the [positive-WAR hurdle plan](prospect-positive-war-hurdle-plan.md).
It uses the supported `0.25` two-year component-WAR threshold, one fixed strongly
regularized logistic model, unchanged 2018 group means and unchanged arrival odds.
It must pass probability and continuous-value checks across 2021-2023 without refit.

The fixed positive-WAR hurdle fails. Its 2021 hitter probability gain reverses in
2022; pitcher probability gains are uncertain and reverse by 2023. Do not search more
thresholds, penalties or aggregate-core interactions on these disclosed cohorts. The
next positive-tail attempt requires a new evidence class or broader historical source.

The broader-history attempt is also complete and rejected. A chronology audit removed
2011–2012 from training before corrected scoring because their outcomes overlap the
first evaluation snapshot. The fixed 2008–2010 fit does not reliably carry into either
2013–2017 or 2021–2023. This closes age, level, workload and broad role alone as the
conditional positive-WAR solution. Preserve the
[result](prospect-broad-history-positive-tail-result.md), leave production unchanged,
and require richer cutoff-dated performance evidence for the next challenger.

Official 2008–2017 component totals were then added under a frozen Tango-style
200-opportunity regression. They improve the basic candidate in 5/8 hitter and 6/8
pitcher evaluation years, but uncertainty and subgroup gates fail and the complete
candidate does not beat the population-rate baseline. Reject the tested combination.
The exception is old-era pitchers, where the candidate beats the constant; it still
fails modern transport. The useful forward hypothesis is that regressed component
rates may work after removing unstable basic effects, but these outcomes are now
disclosed and cannot be used to validate that change.

The untouched 2006–2007 rate-only confirmation is complete. Hitters improve both
scores in both years, but uncertainty crosses zero and supported level groups reverse.
Pitchers improve only one of two years. Reject the simple aggregate rate-only family
without another subset or shrinkage search. The next valid prospect-quality advance
requires either genuinely new pitch/contact evidence across levels or future seasons;
current production values stay unchanged.

**Direction correction:** the sequence below is the batting/opportunity workstream,
not the whole project roadmap. Before another opportunity challenger, inventory
the existing `playing_time_model.py` and dated 40-man source adapter; reuse and
revalidate them on repaired inputs. The player-rights contract, dated 40-man adapter,
censored career-outcome panel and first pitcher-component baseline are now implemented.
The broader official `fullRoster` source is now the primary candidate denominator:
99.80% of players have one candidate organization. Its 0.20% multi-team outliers must
be reconciled through dated transactions or another rights authority. Financial/control
sources and whole-player integration remain open.

O2026D is now complete: official MLB batting-PA labels include non-arrivals,
and a frozen level-aware opportunity baseline improves pooled any-PA Brier error
by 10.0% over prior-exposure-only means, with improvement in both active years.
Playing-time gains are modest. [Results and scope](hitter-v2-O2026D-result.md).
This is a prior-season-active cohort, not complete roster/no-history coverage.

1. Keep the competition-normalized ability component; stop global calibration
   experiments. C2026C is closed and all results are preserved.
2. The completed error audit finds much larger optimism among brief MLB call-ups
   than among players with 100+ MLB PA. This motivates the opportunity cohort;
   observed future PA remains diagnostic, never a predictor or exclusion rule.
3. Keep O2026D as the opportunity benchmark. Audit the participants outside its
   cohort and prior-date roster, role, and age availability. Expand inactive and
   no-history coverage explicitly; the full prospect denominator remains unverified.
   Then freeze one player-specific opportunity alternative. Preserve verified
   official batting-PA zero labels and evaluate against the same baseline.
4. Specify the long-term value horizon and label availability, then compose value
   only after component behavior is understood. Do not attach unvalidated WAR labels.
5. Define prospective confirmation before examining its outcomes. The repeatedly
   inspected 2022–2024 seasons remain development evidence. Protected 2026 stays closed.

## What can wait

Website changes and presentation polish are paused. Pitching, defense and value
integration remain required modeling milestones. Quarantine bounded data exceptions;
stop only for identity, leakage,
denominator, coverage, scale, or material forecast errors. Track known omissions,
including the players outside the original G0 forecast population.
