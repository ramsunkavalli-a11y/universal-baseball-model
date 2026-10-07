# Correct the position share scoring array before fitting

2026-10-07. The source/support preparation is sealed and no fitted transition
means or forecasts exist yet. A prefit scoring check found that Polars converts
a list-valued Series to a one-dimensional object array, not the two-dimensional
position matrix required by the declared placement score.

Use an explicit numeric matrix from the list values and return `None` for an
empty measured subset. The scoring definition, model, inputs, cohort, support,
cutoff, weights and decision rules are unchanged. Preserve the original runner
snapshot and preflight receipt; the execution amendment seals the corrected
runner and a regression test before fitting. Hash validation checks both
versions rather than overwriting the historical seal.
