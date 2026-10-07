# Keep held players out of baseline penalty selection

2026-10-07, before any quality or nuisance fit. The source-only reference phase
is complete and unchanged. The original proposed training-residual construction
reused the outer baseline's selected penalty. That penalty had been chosen using
earlier validation outcomes from some of the same people whose residuals were
being generated. Excluding them only from coefficient fitting would not make
their nuisance prediction fully held-player.

Keep the incumbent outer baseline's prediction and penalty exactly unchanged.
For each nuisance model, independently choose its penalty from 10 and 100 using
only people outside both the outer held fold and its nuisance held fold. Use the
latest two mature validation origins, just as the incumbent algorithm does.
Each nested validation fold is additionally excluded from coefficient fitting
at all source origins and positions. Its training label windows must end by the
validation origin; its validation windows must end by the outer cutoff. Every
actual nested training cell needs 30 distinct people and two source origins.
Unknown quality is retained in validation membership but not scored as zero.

Select the penalty by distinct-person-balanced validation RMSE over supported
cells; ties choose 100. If no supported measured validation exists, use 100 and
record that limitation. Persist all nested memberships, cutoffs and exclusions
before any quality fitting. These cells are not extra independent participants:
deduplicate identical nested cells and report actual measured validation people.
The count correction remains penalty 100 with no count tuning, no intercept and
the same support/fallback rules. Only nuisance baseline selection changes.

The original contract, runner, source preflight and count-prior results are
preserved. A sibling quality runner applies the amended selection and records
its dependencies and actual chosen penalties. It must verify each intercepted
nuisance fit's identities, design, target and weights before using that penalty.
No quality scores were inspected or model forecasts generated before this repair.
The amendment does not address sparse detailed profiles or certify minor talent.
