# V35: reconcile competing levels of batting evidence

2026-10-02. Written before preparation/fitting. V34's source-extension review is
complete; retain its repaired-source population as the matched control and keep
the V33b working anchor. This is one representation experiment, not a library
tournament or a promise to fix every opportunity miss.

## Question and baseball mechanism

Does a count-based, relative-exposure representation better predict next-year
MLB batting and delivered offense than independently stabilized league rates?
The current linear model cannot directly let the influence of a league's rate
depend on a competing league's sample. A 50-PA poor debut and 500-PA productive
AAA season are not equivalent observations. Old minor performance should also
lose influence as the recent MLB sample becomes large.

For each of seven events and fourteen league buckets, sum actual dated counts
over three years with weights 1/.8/.6. Let n be event count, d its opportunities,
p the existing fixed prior, and D the sum of all buckets' opportunities for that
event. Replace that bucket's pooled event feature by:

    prior + (n - d * prior) / (D + 100)

The old feature is prior + (n - d * prior)/(d + 100). The new denominator shares
reliability across actual evidence, rather than treating independent samples as
equally influential rate inputs. Sum of centered features equals a single pooled
centered event rate, but separate fitted league coefficients can still learn
different predictive translations. No-observation buckets contribute exactly
zero deviation. BABIP uses actual balls-in-play opportunities, not PA. No second
shrinkage of already stabilized rates; no chosen percentage of prospect value.
The 100-opportunity prior and recency weights stay fixed from V33/V34, not tuned
on this test. All other 199 feature definitions remain unchanged.

This is a predictive encoding, not a certified MLB equivalency or environment-
neutral estimate. Raw park/league/ball/opponent context is still unresolved.
Translation coefficients and conditional selection can mix ability and context;
do not interpret them as causal talent gaps. MEX remains a separate source.

The basic principles are supported by [Cross and Mailhot's projection lesson](https://blogs.fangraphs.com/fangraphs-prep-build-and-test-your-own-projection-system/)
(recency, regression, aging and actual error checks) and [Steamer's public
description](https://www.steamerprojections.com/index.php/privacy-policy/2-about)
(reliability and regression). Neither source prescribes or validates our exact
cross-level denominator. That formula is the specific hypothesis being tested.

## Fixed contrast and targets

Same 30,506 evaluation identities, 35 chronological/whole-player cells and mature
training identities as V34. All non-arrivals remain zero next-year outcomes.
Target-2020 excluded; actual shortened 2020 batting counts remain actual counts,
while schedule-normalized workload stays a separate existing feature. No 2026
outcomes, public current-season results or frozen-forecast modification.

Fit two fixed heads per cell, using the same settings and equal-origin weights:
HistGB expected PA; PA-weighted fixed-scale ridge alpha 100 for conditional
future-active batting wins/600. Keep all 199 features and learner settings.
Save rate-only (old PA/new rate), PA-only (new PA/old rate), and combined products
beside unchanged V34 and V33b. Seventy fits, no tuning or post-score arm expansion.
Products estimate batting-plus-replacement contribution, not full WAR or an
independence-validated joint distribution. Rate target is future MLB performance
conditional on play, not same-level minor success or a current FV scouting grade.

Materialize origin-only counts and audit all fold/all-active profile support
before any fit. Preserve canceled/missing histories and certified target zeros.
Save every source hash, transformation input, training/test membership and fitted
artifact. Test conservation of centered evidence, absent-level neutrality and
decreasing minor influence as MLB exposure grows. No outcome-total rescaling.

## Evaluation, player review and decision

Primary: PA-weighted conditional MLB rate loss and delivered contribution RMSE;
workload RMSE/MAE, public matches, each origin, stage, current absence/partial/
regular, brief debut and thin entrants remain visible. Compare equal-origin
losses and nominal player-cluster intervals. Public converted-value offsets and
snapshot-date differences remain qualifications; matching a converted value is
not enough to call hitting talent successful. Keep the plan's public PA targets.

Predeclared cases: McNeil 2018, Steer 2022, Winn 2023, Kurtz 2024, Olson 2022,
Judge 2024, Lux 2023, McLain 2024 and Tatis 2022. Add each product's largest
value gain/harm and false high/low plus an ordinary example. Show raw counts,
old/new inputs, saved linear terms, predicted heads, actual outcomes and origin-
selected peers (same year/stage/debut, nearest age/current MLB PA/upper-minor PA/
quality/draft rank). Unsupported profiles are marked, not removed. Completed
review is required before selecting another experiment.

Retain a representation only for meaningful predictive/baseball benefit, not a
passing script or a lucky cancellation between PA/rate. If it fails, retain
the source and baseline; do not reject all component/MLB-equivalency approaches.
An improvement remains development evidence and cannot promote frozen forecasts.
