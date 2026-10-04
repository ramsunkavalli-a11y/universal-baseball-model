# Testing whether projected MLB hitting improves opportunity forecasts

2026-10-03. Fixed before new fitting or scoring, following the completed
workload-risk review. This is one substantive talent-to-opportunity comparison
under the practical hitter plan, not a new library tournament, player bonus or
claim that wider intervals repair readiness.

## Question and earlier evidence

Does a separately projected MLB hitting rate help the current opportunity model
identify next-calendar-year MLB participation and PA, including useful prospects
and returning major leaguers? The current model receives production at each
level, age, workload, ranking and draft evidence, but does not explicitly receive
its separately fitted MLB hitting forecast. A generated prediction summarizes
existing information under another target; it is not a new observation or a
causal estimate of how teams make decisions.

The [September 23 comparison](hitter-talent-workload-v1-result.md) added talent
and pedigree only to never-debut players' conditional PA heads, keeping
participation fixed. It used a different panel, features, player-validation
scheme and horizon coverage. Its small conditional-workload gains cannot reject
a talent-to-arrival link in the current candidate. Its older result is not
recertified under today's detailed player-walkthrough gate; no old model is
promoted or old unfavorable arm selected here. Preserve its original report.
Save a source-design reconciliation and verify its fixed-probability arithmetic
before the new test; do not reinterpret its pooled numbers as this comparison.

## Identical population and three comparisons

Keep exactly the current 63,282 source identities and 30,506 forecasts, seven
origins and 35 chronological whole-player cells. Targets are 2017–19 and
2022–25. Use the exact existing outer training IDs, excluding target 2020.
Unknown histories stay qualified; certified exits/non-arrivals remain zero
delivered PA/value, not zero hitting talent. Preserve the short 2020 MLB source
and canceled minor season conventions. Protected 2026 stays closed.

All forecasts, including current MLB players, are eligible for this comparison:

- Current anchor: saved 251-input appearance and active-PA heads.
- Coverage control: same inputs plus an indicator that an earlier-outcome
  hitting estimate can be produced.
- Talent candidate: the control plus that hitting estimate.

Both new constructions fit appearance and active-only PA, using the unchanged
250-iteration depth-three histogram recipe, leaf minimum 30, learning rate .05,
L2 10, no early stopping, seed 31 and equal-origin training weights. No tuning,
blend, cohort-specific switch or new availability rule. Existing dated permanent
unavailability and reported-retirement wrappers remain, with conditional PA
bounded [1,800]. Report clips rather than deleting forecasts.

The primary feature contrast is talent versus coverage; comparison to the
strong current anchor is also mandatory. Refit both heads for all players;
do not infer public improvement from a prospect-only experiment.

## Nested hitting estimates

Use the current 199-input hitting recipe: numeric-safe scaling, ridge alpha
100 and equal-origin weights multiplied by actual future PA then normalized.
Target is the source's observed next-year MLB batting rate relative to that
year's MLB average, in custom batting win units per 600 PA. It is a
contribution-weighted forecast among participants, not unbiased latent talent
for never-arrivals, a scouting FV grade, defense or total WAR. No new batting
model is selected in this opportunity test.

For outer tested player group k, a training row at origin s in group j receives
a hitting estimate trained only on active outcomes from the actual outer
training IDs with target year at most s, target not 2020, excluding all of
group j as well as group k. Its own target, later labels and all other seasons
of its player must be absent. For an outer tested row at origin y in group k,
use the existing outer active training IDs only; it must reproduce that
candidate's saved hitting forecast. Rate inputs have no preseason scout fields;
coming-season rank release dates still constrain the opportunity fits.

Require at least 200 active training rows, 100 distinct players and two distinct
origins for a generated hitting head. If earlier history cannot supply that,
encode estimate zero and known zero, explicitly meaning unknown, not average
or poor talent. Apply the same known indicator to the coverage control. Every
outer test must have an estimated forecast or remain visibly unsupported; no
silent fallback to future-trained estimates.

Reuse a rate fit only when cutoff, excluded groups and exact training identities
match. Opposite outer/inner group assignments may share the same fit but not
silently exchange validation rows. Save union prediction identities and the
individual outer-cell usage map. All raw source, nested full-player membership
and actual profile checks precede first-stage fits. After generation, save
every full/active opportunity preflight and generated-feature range check before
any second-stage fit. A large global count does not certify thin elite entrants,
medical returns or all lower-level extrapolations.

## Scoring and mandatory review

Hold each current hitting output and batting yield exactly fixed. Delivered
offense remains expected PA times that yield in the current common-origin
fixed-event batting-plus-replacement units. This isolates opportunity effects;
it is not a newly fitted joint value distribution or full WAR.

Score equal-target-year PA RMSE and MAE, appearance Brier/log loss, fixed-yield
offense RMSE, raw matched PA/value/appearance totals and nominal 95% paired
player-clustered MSE intervals against both controls. Show every origin, public
matches, current MLB, upper/lower never-debut, current absences, thin new draftees,
origin-known hitting bands and generated-head support gaps. Current public
benchmark goals remain: PA RMSE within 10% of Steamer and MAE within 15%.
No public quantile or 400-PA-probability claim follows from these point heads.

Fixed player walks: Kurtz 2024, Langford 2023, Alonso 2018, Judge 2016 and 2024,
Pena 2021, McLain 2024, Belt 2023 and Franco 2023. Add largest gain and harm
against coverage/current, major false high/low and an ordinary active forecast.
Trace actual dated level stats, generated model membership/scaling/coefficients,
estimate and support, saved opportunity paths, p and conditional PA, fixed
hitting yield, delivered forecast and next-year MLB reality. Show at least four
origin-selected peers using age, position, workload, rank and projected hitting,
while clearly marking unmatched medical/legal/talent dimensions. Keep both
unsuccessful peers and consequential harms. Do not fit to those names.

Only consider retention after the actual walks. Require a coherent meaningful
PA/value improvement versus the strong anchor and an incremental talent effect
versus the coverage control, interpreted with uncertainty, origins, public and
prospect errors, totals and supported profiles. Small isolated score changes,
a threshold crossed by luck, or a few famous gains cannot certify the whole
model. Major source or mechanism defects block promotion; rare noisy cells do
not automatically require every metric to improve. Historical years are exposed
development evidence. No post-result tuning, new explorer/frozen-forecast
changes or automatic deployment. Failure rejects this encoding, not the
baseball proposition that stronger players earn more opportunities.
