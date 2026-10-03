# A cleaner hitter foundation, with a specific remaining problem

2026-10-03. Retain corrected V53 as the historical research baseline. The
long-range goal stays active. This is not a completed full-WAR, six-control-year
or trade-value system, and no frozen/deployed 2026 projection has changed.

## What the current model actually does

It keeps three years of batting history separate by league and uses age,
position, career context and dated draft evidence to forecast next-year MLB
hitting among future participants. It is a regularized count-history model,
not a Statcast model. The opportunity side uses shallow boosted models to
estimate any MLB appearance and PA if active, with historical rankings,
exposure and qualified cutoff-known availability context. Their product gives
expected PA. Expected offense adds batting above average and replacement,
not defense or baserunning.

The source correction reconstructs floating-point draft elapsed time and pooled
PA from original counts. The real defect affected 23,401 drafted source rows.
It did not change component rates or explain the whole prospect problem.

On 2,627 identical current-MLB public matches, hitting-rate RMSE is 1.7435
versus Steamer 1.7746 and ZiPS 1.7534 on a common fixed-event metric. Only the
2,088 actual participants have observable hitting rates. Public archive dates
are not exactly matched, environments are not fully neutralized, and repeated
development comparisons prevent superiority claims.

Playing-time RMSE is 138.49 PA versus Steamer 135.38; average absolute error
is 106.87 versus 92.08. That remaining average-error gap is about 16%, not proof
our hitter talent estimate is far behind. The declared practical goal is not
waived. Prospect readiness and some origin-year calibration are materially worse
than a small aggregate score suggests.

## What this batch settled

The shared linear prospect construction partly fixes fast entry but gives
implausible weight to rare rookie rates. Fixed baseball units stop the largest
rate extremes but over-shrink useful opportunity signals; the same numeric
penalty in different units is not the same effective regularization.
Combining those heads does not earn a new hitting model. The 79-input compact
readiness version is easier to explain but slightly worse overall.

Langford improves from 43 to about 212 expected PA versus 557 actual.
Alonso and Bellinger remain severe underforecasts. Holliday becomes less
overconfident, but Julio Rodriguez loses useful readiness signal. Ordinary
Zimmer/Fisher cases show how hitting and PA mistakes can cancel into a close
offense number. The 2021-origin interruption cohort and 2023-origin overforecast
also remain visible; this is not uniquely proven to be a COVID effect.

Keep the numeric repair and baseline talent. Preserve the modest, uncertain
detailed prospect PA-only variant for inspection, not automatic adoption.
All four comparisons have actual source-to-fit player reviews; no more
representation/penalty micro-sweeps in this batch.

## Next material work, in order

Update after the [V59 status review](practical-hitter-opportunity-status-v59-result.md):
captured transaction status alone does not earn an upgrade. Public PA error is
essentially unchanged and whole offense slightly worsens. The medical source
has 44 evaluation open-spell rows contradicted by later MLB use, so that result
does not reject health information. Repair observed-return state and uncertain
absence duration before further status fitting. Six source controls prevent
clearing injuries that started during/after the late PA window. The following
sequence remains the coherent direction, not another sparse-feature sweep.

The [V60 source adapter](hitter-observed-return-v60-result.md) now corrects
those stale observation states using safe roster activations and disjoint
actual MLB windows. Eight reviewed cases preserve late-injury counterexamples.
It reports possible-duration bounds, not invented exact injury days, and does
not change forecasts. Use it under a substantive workload contract; the prior
four-state/direct tests are anchors, not untried architectures to rename.

1. Keep batting talent fixed while addressing **timely opportunity information**.
   Identify actual December-known role, finite absences and exits in the large
   workload misses. The 386 one-PA public forecasts may contain later job/health
   information, not automatically superior talent. Do not copy those public
   labels into training or pretend a spring injury was knowable in December.
   Reuse prior verified timing/status sources and their reviewed failures.
2. Treat **role-to-workload uncertainty** as a substantive target. A chance to
   arrive is not a chance to immediately have a starting job. Check large
   starters, brief debuts, returns and fast entrants separately. Keep all exits
   and unsuccessful peers. Model expected PA, not an opportunistically chosen
   median solely to improve MAE while still calling it expected value.
   Interruption and vintage associations require particular care after 2020.
   Write one bounded architecture/source contract before any further fits.
3. Integrate **joint delivered-value uncertainty** after opportunity holds up.
   Probability × separate conditional averages remains an approximation when
   playing time and production co-vary. Use reviewed mature historical support;
   do not multiply six annual means and claim six years of club control.
   Defense, running, position and catcher value need compatible separate evidence
   before the sum is called full hitter WAR.

The [new local research explorer](http://127.0.0.1:8788/) contains all 30,506
historical forecasts with year/team/stage filters, hitting-only sorting, actual
histories, explicit appearance probability and conditional PA, public comparison
and version-labeled reviews. Corrected baseline is default; alternatives are
labeled uncertain/not adopted. Original explorers stay unchanged.
The information year 2024 means a forecast for 2025, not 2026. Organization
is a qualified historical cohort, not a guaranteed future roster or club budget.

[Numeric repair](practical-hitter-numeric-repair-v53-result.md) ·
[Shared prospect test](practical-hitter-prospect-pooling-v54-result.md) ·
[Fixed units](practical-hitter-prospect-units-v55-result.md) ·
[Head assembly](practical-hitter-head-assembly-v56-result.md) ·
[Compact readiness](practical-hitter-compact-readiness-v57-result.md).
