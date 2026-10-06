# Test whether recent training better represents prospect promotions

2026-10-05 before fitting. User priority: ordinary-season prospect readiness,
including faster recent paths, rather than repeatedly repairing origin 2021.
One comparison, not a new algorithm or history-clock sweep. Retain 2021 in all
scores and show it separately; do not let its gain select this candidate.

## Question and existing evidence

Can training that gives recent seasons more influence improve next-calendar-year
MLB arrival, expected PA and delivered batting contribution for never-debuted
hitters? Faster arrival and workload after arrival are different quantities.
Neither establishes career talent, six service years, full WAR or trade value.
Include every eligible non-arrival at zero delivered PA/value, not zero talent.

MLB's [promotion incentive explanation](https://www.mlb.com/news/prospect-promotion-incentive-faq)
describes incentives for earlier promotions. It does not quantify a population
speed increase. Our observed draft cohorts, not a few success stories, must
establish the size and scope of any change. Players who already reached MLB
during their draft year leave the never-debut risk set. Show that known fraction
as well as next-year arrivals among those still waiting; otherwise faster
development can misleadingly resemble slower promotion in the remaining group.
These source cohorts are observed professional hitters, not every selected or
signed amateur. School-class coverage differs by vintage; use age as an explicitly
imperfect comparison proxy rather than pretending old school zeros are known HS.

Prior school-source substitution V66, draft-age V42, separate entrant workload,
deeper histogram/LightGBM workload, smooth prospect pooling, fresher rankings,
and available-season history are already tested. They changed source fields,
architecture, training eligibility or individual history, not this training-era
weighting. Keep their qualified conclusions and do not rerun them. The separate
employment-recency interaction changes record staleness, not training seasons.
The older pitcher uncertainty recency test is a different target and population.

## One fixed change

Reference: completed 293-input nonmedical-observation opportunity model, with
the separate seven cutoff-known departure corrections applied identically.
Keep the selected frozen architecture as an additional saved anchor where its
original output exists. Preserve all 30,519 historical evaluation identities,
all actual training rows, ordered inputs, tree settings and targets. Same 35
chronological, whole-player-held-out cells and 70 candidate heads. The conditional
head retains established active hitters; this does not repeat entrant-only fitting.

The reference gives each training origin equal total weight. Multiply each row's
reference weight by `2 ** ((origin_year - latest_training_origin) / 4)` and
renormalize total weight to the original number of training rows, separately for
each actual head. Thus a season four years older gets half the relative influence,
not zero influence. Four is a single moderate engineering choice, not an estimated
baseball constant. No half-life tuning or post-result window/feature variants.
Normalization preserves overall sample-weight scale; distribution and effective
regularization still change, so this is not a causal estimate of MLB policy.

Route candidate outputs to ALL never-debut queries, using cutoff-known prior
debut status. Keep previously debuted predictions bit-identical. Preserve the
current status/departure rules, clip conditional PA to [1,800], multiply chance
by conditional PA, and keep hitting rate and the compatible replacement
reference exactly fixed. No ranking floor, named-player boost or new source.
Record raw heads and the status transform. This tests opportunity only: a hitting
miss such as Kurtz's is still a separate miss.

## Pre-fit coverage and support

Verify source/sealed-completion hashes, replay all 70 reference heads, and run
`forecast_validation.preflight` on full and active subsets before any fit. Same
training identities and mature targets no later than origin; target 2020 omitted,
repaired origin-2020 retained, held test players excluded in every generated input
as in the saved reference. No new learned/generated feature is introduced.
No 2026 read, rescore, freeze or explorer edit.

Retain existing profile/calendar warnings. In both heads count distinct people
by prior debut, current upper exposure, age, listing, rank and draft-time category;
also inspect first-draft-year age-20+ top-fifteen picks with up to 250 observed
three-year minor PA. Count support per actual fold, not total pooled rows.
Record each profile's training-origin weight mass and person-aggregated effective
count `(sum person_weight)^2 / sum(person_weight^2)`. This is a concentration
diagnostic, not independent sample size or proof of elite-trajectory support.
All absent/sparse profiles stay scored. Unknown pedigree/background stays unknown.

Show observed draft cohorts by year with current MLB participation known at the
origin, and next-year arrival/PA among the remaining never-debut players. Keep
canceled-origin 2020 separate. Do not infer a promotion-speed change from unmatched
school vintages, all-player counts or next-year regulars selected in hindsight.

## Fixed scoring and decision

Primary development population: never-debut forecasts at origins 2022, 2023 and
2024, with equal origin weight. Primary loss: expected MLB PA MSE. Require a
negative point difference against the working reference, no worsening in
delivered batting MSE or arrival Brier/log loss over 2%, and no major upper/lower
group PA MSE harm over 2%. Report each origin, raw arrival/PA/value totals, MAE,
active-only workload error and non-arrival allocation. An individual recent origin
PA MSE deterioration over 10% requires a baseball explanation and bars a generic
recent-cohort improvement claim. Guardrail percentages are practical tolerances,
not scientific constants or a mandate for every noisy small profile to improve.

Also score all six non-2021 origins with equal origin weight, requiring no PA
MSE harm over 2%, and all seven including the 2021 stress cohort. Show the same
selected-architecture contrast separately without pretending source/model/weight
differences isolate a causal effect. Preserve all current MLB forecasts and
public-matched predictions; a prospect change cannot close their workload gap.
Use 2,000 paired whole-player bootstrap draws, seed 105, for recent and six-origin
PA/value MSE differences; intervals are exposed development evidence, not fresh
holdout confirmation or protection against the many previous experiments.
Nominal interval favoring improvement plus consistent walks is required for a
convincing research improvement. No automatic deployment, even if point gates pass.

## Required player review and stop

Fixed cases: Langford 2023, Kurtz 2024, Cartaya 2022, Roman Anthony 2024,
Meadows 2016, Reynolds 2018 and Sands 2021. Add largest recent PA gain/harm,
largest recent candidate false high/low and an ordinary recent positive-PA case
closest in absolute PA error (ties row ID). Preserve adverse cases. These are
diagnostic selections, not independent validation or tuning targets.

Trace each case's three-year dated level PA/HR/K/BB, all actual inputs, both
reference/candidate raw heads and saved hashes, status handling, probability,
conditional PA, fixed hitting and delivered value versus reality. Select three
peers by origin, known draft-time/current upper category and listing, then age,
exposure, K/BB/HR and pedigree distance without outcomes; report insufficient
exact peers without quietly replacing them. Show distinct/effective training
support and modern-era weight mass. Complete walks before final disposition.

If the comparison fails, retain the current forecasts and close this exact
training-decay experiment. Do not switch half-lives, add a COVID exception or
route only to favorable subgroups. Any source defect stops the fit until repaired
under an append-only amendment. The goal is a usable forecast, not accumulating
new diagnostics or declaring a weighted fit a validated player-value model.
