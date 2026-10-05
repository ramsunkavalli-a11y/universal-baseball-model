# Check whether a source correction can reach the forecast

2026-10-05. Add this check to the existing experiment and player-review gates.
The nonmedical opportunity comparison returned exactly identical forecasts:
all eight corrected inputs were unused by both saved tree ensembles. A changed
source value is not necessarily a changed model mechanism. This should be
checked before spending another complete fitting batch on a similar correction.

Before a source-correction refit, list every dependent learner input and identify
whether the saved baseline actually uses them. For trees, inspect split counts
and selected player paths; for linear or probabilistic models inspect coefficients,
transformations and link functions. Check source joins and generated inputs too.
Use saved parameters to probe eligible changed rows, preserving consistent
derived values. This is a mechanical sensitivity, not a validated forecast or
causal effect. Retain corrected data even if fitted parameters ignore it.

Distinguish three outcomes. An influential correction requires a matched refit
and full score/player review. An ignored input with insufficient variation or
profile support does not establish that the baseball idea is useless. A source
correction that cannot reach any downstream calculation is a source milestone,
not an accuracy test. A prospective refit can still be justified if the corrected
training distribution plausibly creates a newly learnable signal; state that
mechanism before fitting rather than automatically cycling through variants.

Do not force importance by lowering leaf sizes, adding a tuned bonus or selecting
named-player overrides. Rare temporary interruption, genuinely indefinite absence
and ordinary low workload may require different structural assumptions, but
those assumptions need their own source/support review and predeclared comparison.
Inspect existing tests first. No automatic reopening of employment, team-record,
broad injury-feature sweeps or the completed 2026 evaluation follows from this gate.
