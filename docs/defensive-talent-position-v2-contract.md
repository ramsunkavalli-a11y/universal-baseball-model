# Infield talent: repaired measurements and one bounded comparison

2026-10-06, recorded before new collection or fitting. This follows the completed
position-source pilot and talent-support audit, not the old next-year contribution
test. It does not alter selected forecasts, the explorer, or use new 2026 outcomes.

## Question and source repair

Does the existing minor ground-ball play-share signal add information about later
MLB range at the **same position**, beyond age, position, source exposure and prior
MLB range? Range is one part of defense, not total defensive talent or WAR.

Preserve all 31,563 original player-position origins and their minor statistics.
Extend the pilot's exact single-year position/aggregate queries through 2016–2025;
reuse its sealed 2022/2025 captures. Certify embedded year and grouping, unique
player-position rows, position outs against aggregate and independent official
usage, and range recomposition. Absent or null position measurements stay unknown.
Exclude individual annual measurements whose independent exposure does not agree;
report every exclusion rather than treat mismatches as rounding. No source-wide
accuracy claim follows from a successful collection check.

Repair name/age from public identity and birth-date captures, with age on July 1
of the origin year. Immutable biography is reconstructed today, not an archived
preseason document. Keep original metadata alongside repaired context. Derive
current and weighted minor fielding levels/shares from dated source rows at the
actual position, including short-season A and DSL separately. A missing current
fielding row means missing current fielding evidence, not retirement. No canceled
2020 minor performance is invented. Source lookback remains three calendar years
with fixed weights 1, 0.5, 0.25; early origins remain left-truncated.

## Labels and actual support

Keep fixed future 3/5/7-calendar-year windows. Quality is pooled position range
runs / position outs times 1,500 (runs per 500 innings), requiring at least 1,500
measured outs and two measured seasons, and the entire calendar window elapsed
through 2025. Missing MLB fielding/non-arrival has unknown quality, never zero.
This estimates observed quality among defenders who received sufficient MLB
exposure; it cannot establish which non-arriving DSL players were good defenders.
Record annual paths, missing measurements and measurement ages. Labels with any
positive official position exposure but unavailable range retain a gap warning.

Recount distinct players in every actual chronological five-way player fold.
Training labels must end by the evaluation origin; exclude all records of held
players, using player_id modulo five. An origin needs at least 30 training people
and two training origins in every fold before any comparison. Twenty exact
age-band/position/fielding-level/prior-MLB peers is a warning threshold, not proof
of sufficient support. Five/seven-year claims stop if chronology leaves no
training. Do not change windows or pool positions to manufacture support.

## Fixed comparison if the three-year screen permits it

Use one standardized ridge regression with alpha=100, no tuning. Age (centered,
quadratic, missing indicator), position, log weighted ground balls, dated level
shares, current-fielding indicator, source-history truncation, and prior same-
position MLB range/exposure form the contextual baseline. Prior range uses the
same three calendar-year weights and 1,500-out shrinkage; all inputs stop at the
origin. Fixed level shares replace unreliable highest-level labels in both arms.
The candidate adds the original adjusted play-share rate (600-ball shrinkage).
Also report a zero-range anchor and a baseline plus unadjusted credit share;
that share is a crude play-count proxy, not fielding percentage or true chances.
Do not claim the contrast separates talent from every pitcher/park/teammate effect.

Fit all supported mature origins, retaining sparse-profile predictions in scores.
2022 is the primary ordinary origin (2023–2025 outcomes); 2021 is separate COVID
stress. Earlier supported origins are development context, not pooled proof of
recent accuracy. Primary RMSE weights each person's position rows to total one
within an origin. Also show unweighted RMSE, mean signed error and group results.
Use a fixed-seed 2,000-draw player-cluster bootstrap for paired RMSE differences.
Future exposure affects label precision, not eligibility or input weights.

Permit only provisional component evidence if the candidate beats contextual
and raw-share benchmarks in 2022 without a clear level/prior-MLB reversal; uncertain
intervals stay uncertain. Small subgroup samples do not pass or fail on a hard
threshold. No deployment or full-WAR improvement claim follows from this test.

## Baseball review and completion

Walk the previous fixed cases plus Tovar through actual annual source, pooling,
reliability, prior range, fit support, prediction and annual MLB outcomes. Add
largest improvement/deterioration, false high/low and ordinary scored cases by
recorded deterministic rules. Select three peers using origin-known level,
position, age and exposure only; preserve unsuccessful comparisons and unknown
outcomes. Reconstruct inputs/labels, replay predictions and keep fit coefficients
and source fingerprints. Conclude separately on integrity, support, prediction,
baseball reasonability and deployment. Unsupported long-window/lower-minors work
is a limitation, not a negative talent finding. Finish the review before choosing
another component.
