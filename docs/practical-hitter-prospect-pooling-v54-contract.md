# Shared prospect models for MLB arrival and production

2026-10-03. The numeric repair and ten player reviews are complete. Fast entrants
remain missed even where broad support exists; tiny draft-year subsets cannot
supply their own conditional averages. Test one smoothly pooled alternative
for all origin-known never-debut hitters, not a hand-chosen fast-entry group.

## What changes

Keep the corrected prior candidate exact for every player with an observed MLB
debut. For never-debut hitters fit regularized logistic regression for any next
calendar-year MLB PA, Ridge for conditional PA, and Ridge for participant-only
MLB hitting rate. Share slopes across all prospect stages rather than requiring
a boosted-tree leaf to contain numerous similar fast draftees. This is a
different statistical representation, not proof the rare conditional profiles
have become supported.

Inputs are deterministic functions of the repaired source: age and age squared,
position, cutoff 40-man status, source gap, reorganization/cancellation flags,
dated draft rank/class/elapsed time, dated ranking history, log pooled PA and
seven pooled count rates separately for fourteen leagues. Three annual total
minor PA and games/PA-per-game capture exposure. Add highest *observed current*
minor level indicators (not an assertion of season-ending role), draft rank ×
upper-level indicator, age × upper-level indicator, and recent-draft rank
rank/(1+years since draft). No player ID, outcome-selected peer, future scouting
grade, inferred bonus or generated future-rate input enters fitting.

Use StandardScaler fitted only on actual training rows for each head. Logistic
C=.01, maximum 1,000 iterations, tolerance 1e-7; require convergence. Both Ridge
heads use alpha 100. Participation and conditional PA use equal-origin training
weights; rate additionally uses actual future MLB PA and normalizes weights.
The settings are fixed before scores, with no parameter sweep. Conditional PA
is bounded [1,800]. Origin-known hard unavailability and reported retirement
zero opportunity, not ability. Save and replay all 105 heads.

## The fixed question and comparison

Same 30,506 historical forecasts and 35 chronological whole-player cells as the
numeric repair. Mature training outcomes at/before each cutoff; target 2020
excluded, repaired source origin 2020 retained. Never-debut training subsets
receive explicit preflight and distinct-player stage/age/exposure/draft support
checks before any fit. Sparse/unseen profiles stay in scores and are marked.
Unknown international source/pedigree and 218 roster-only qualifications remain.
No additional college collection, protected 2026 access or deployed changes.

Primary effect: equal-target-year delivered offense MSE across all never-debut
forecasts, including zero MLB outcomes, versus the corrected candidate. Report
full population too, PA RMSE/MAE and totals, probability Brier/log loss, conditional
actual-PA-weighted hitting error, upper/lower stage and origin totals. Public
current-MLB forecasts must stay exactly unchanged; this test cannot solve their
availability or playing-time errors. Nominal paired player-cluster intervals
are development evidence after repeated historical exposure.

PA-only and rate-only product contrasts identify offsetting errors. The product
still approximates the joint relationship between talent and opportunity; it
is offense plus replacement, not full WAR, six control years or trade value.
Participant rates do not certify present-day MLB equivalents for young prospects.

Fixed diagnostic cases: Kurtz 2024, Langford 2023, Bellinger 2016, Alonso 2018,
Salas 2024. Add largest delivered gain/harm, false high/low and ordinary
never-debut contribution case. Select four origin-known peers without outcomes;
review actual stats, transformed inputs, exact logistic/Ridge terms, intermediate
forecasts and outcomes before disposition. Do not pick a model because these
five famous cases improve.

Keep a candidate only if the joint scores, groups, totals and mechanics are
credible together. A supported negative result does not reject all smooth
prospect models; a small pooled win does not certify the model. If prediction
improves meaningfully with no material mechanism failure, retain it for research.
Otherwise preserve the corrected candidate and document the narrower lesson.
