# Testing minor league tracking against future MLB hitting

2026-10-04. This comparison asks whether the recovered minor-league launch
measurements improve next-calendar-year MLB hitting beyond the already reviewed
production, pedigree, rankings, translation and MLB tracking evidence. It is not
another contact-bin test, a test of next-year minor performance, or a claim about
full WAR or career value. Freeze inputs and all support checks before fitting.

## Population and benchmarks

Keep the existing 30,506 forecasts, seven origins 2016–18 and 2021–24, five
whole-player folds, exact labels and current playing-time forecasts. Training
uses the existing eligible rows, next-year MLB participants only, with target
years completed by each outer origin. Exclude target 2020 and the entire held
player group. Inactive players remain in delivered-contribution scoring; they
have no observed hitting-rate label. Short MLB 2020 history and absent MiLB 2020
remain distinct. Protected 2026 forecasts, outcomes and explorers stay closed.

Retain three benchmarks: current UBM; the reviewed MLB-only regularized Statcast
forecast; and a fixed combined research benchmark using the reviewed translated
linear prospect forecast for never-debuted players, otherwise the MLB-only
forecast. These branches do not overlap because predebut players have no prior
MLB tracking. Reproduce their saved predictions, rather than refitting them.
The combined benchmark is an assembly of previously tested components, not an
already validated joint model. Matched public Steamer/ZiPS comparisons retain
their conversion and archive-vintage limitations.

## One bounded regularized comparison

Fit two Ridge heads with alpha 100 and the existing deterministic base input
scaling. Both receive the exact 199 current hitting inputs, nine reviewed ranking
inputs, twelve translated-profile inputs from the already sealed own-origin,
held-player translation files, and the 63 reviewed MLB tracking inputs. Add the
minor coverage block to both. Only the measurement head gets the minor values.
Use the existing equal-origin times actual future-PA training weights, normalized
to mean one. No parameter search, alternative algorithms or post-result rescue.

For each of three annual lags and each covered league (112 Pacific Coast,
117 International, 123 Florida State/predecessor), the coverage block contains
log(1+n)/log(601) for EV, angle and joint sample counts, joint measurement
coverage, source-year availability, and six metric-known flags. The measurement
block contains mean EV, EV95, best-half EV, mean angle, angle standard deviation
and hard-air fraction, plus best-half EV times EV sample and hard-air fraction
times joint sample. Keep leagues and lags separate. A null measurement has value
zero AFTER centering and known flag zero; it is unknown, not average talent.
There is no universal EV bonus or fixed reliability weight.

Best-half EV is an additive source summary justified by the literature review:
sort valid nonbunt terminal EV readings and average the largest ceil(n/2), with
equal weight within that annual player/league sample. Recompute it from the
reviewed ledger, independently check counts and retain the existing annual
source unchanged. It is not EV95 or a new camera-only claim. Original provider
publication vintage and estimated-versus-observed flags remain unavailable.

## League and historical calibration

For each annual feature season, compute each metric's contact-count-weighted
mean and between-player standard deviation from that same league and season,
excluding the complete held player group. Use EV count for EV metrics, angle
count for angle metrics, and pair count for hard-air share. No later season
enters an earlier row's reference. Preserve reference people, exposure, means
and scales. With no eligible reference use an explicit missing reference; a
constant reference uses the declared unit scale (10 mph, 20 degrees, or 1 for
fractions). This is source-distribution centering, not park neutralization.

Separate league coefficients then learn the association with actual future MLB
hitting inside the outer training fold. Do not subtract an assumed minor-to-MLB
speed penalty or transplant the MLB EV coefficient. Park, ball, selection of
movers and opponent context are not fully disentangled by league centering.
Existing production adjustments stay shared across arms. These limitations must
remain visible even if the new head improves its loss.

Forecast routing is fixed before fitting: the minor branch is eligible only
when the player has valid own minor EV in the three-year window and at least
one represented league has 20 distinct tracked future-MLB training participants
in that actual outer fold. This is a minimum fallback rule, NOT certification
of sufficient comparable support. Disable an absent/sparse league's entire
minor feature block in training and test for that fold. Early absent contexts
therefore use the exact combined benchmark, not extrapolated minor coefficients.
Both heads use the same routing and disabled blocks. Everyone else retains
the combined benchmark exactly, including untracked prospects such as Kurtz.
Sparse refined profiles remain eligible, flagged and included in all scores.

## Prefit checks

Verify approved source and benchmark receipts and hashes, fixed memberships,
unique player/league/year measurements, actual source dates, training chronology
and whole-player separation. Run active-rate preflight in every cell. Save
distinct tracked active training people by league and refined intersections of
prior debut, age band, real level exposure, sample band and ranking band.
Use observed recent AAA/AA/A/A+ PA amounts rather than accepting a latest-level
label as a comparable. Report ranges and absence separately from integrity.

Tests must show that changing later seasons or held players cannot change earlier
calibration; no measurements stay unknown; best-half EV follows the declared
order statistic; source absence triggers exact fallback; and source/profile
eligibility never depends on a test player's future outcomes. Hash all code,
contracts, generated inputs and support before any new rate heads.

## Scores and decisions

Primary: future-season-relative MLB batting wins per 600 PA, among eligible
minor-tracked participants, equal-origin and actual-PA weighted. Also show equal
active-row weighting and never-debuted tracked participants. Separately score
all-player common-origin batting plus replacement contribution at unchanged
expected PA, including all non-arrivals. A rate win cannot fix opportunity.

Compare the measurement head with its matched coverage control and all three
benchmarks. Report each origin, 2021 explicitly, source leagues, sample bands,
prior debut, actual level exposure, upper/lower minors, sparse support and the
matched public cohort. Keep totals and signed bias alongside RMSE/MAE. Use
2,000 paired player-cluster resamples with seed 724; intervals are nominal
development evidence, not independent confirmation or multiplicity adjustment.

Retain useful research evidence only if values add to the coverage control and
the combined benchmark with coherent player behavior and no substantive,
systematic contribution harm. Do not reject tracking universally for an uncertain
rare-group loss. Explicitly review an origin's rate MSE worsening over 5%, total
drift, short-sample failures and unsupported extreme profiles. No clipping hides
rate extrapolation; report broad mathematical bounds and training ranges. All
integrity, support, accuracy, baseball judgment and deployment fields are separate.
No automatic deployment follows any result.

## Required player walkthrough

Retain all eleven reviewed minor-source player origins, including Elly 2022/2023,
Caminero 2023/2024, Langford, Eldridge, Kurtz, Caceres and Crook/Hicklen/Herron.
Append the measurement head's largest contribution gain, harm, false high,
false low and an ordinary active case among the fixed eligible population.
Trace dated level stats, rankings/pedigree, actual launch samples, held-player
league references, all fitted terms, fixed opportunity, forecast and future MLB
results. Keep inactive rate observations null and tiny outcomes visibly uncertain.

Select four peers from origin-known age, debut, actual pooled level PA, draft
pedigree and rank evidence, never future results. Save their actual level stats
so a one-PA AAA promotion cannot masquerade as a full AAA comparable. Named
gains and harms are diagnostics, not independent confirmation. No disposition
or another modeling experiment before the readable review is complete.

## Research behind this design

[Sapolsky and Cross](https://tht.fangraphs.com/improving-projections-with-exit-velocity/)
found prior exit velocity added information beyond preseason forecasts but warned
that established production already embeds some power information. Their older
velocities were reconstructed; the reported regression is not a prospective
independent accuracy contest.

[Andrews](https://blogs.fangraphs.com/the-doomed-search-for-a-perfect-way-to-interpret-exit-velocity-data/)
compared exit-velocity summaries against next-season hitting and found sample
size important. That motivates best-half and upper-end measures plus explicit
counts, not importing his optimized cutoffs as universal priors or assuming
correlation proves incremental improvement.

[Carty](https://fantasy.fangraphs.com/introducing-the-bat-x/) describes combining
traditional and tracking forecasts, including sample regression and aging.
His developer-reported backtests support investigating complementary information,
not automatically certifying our minor-league translation or full player value.
