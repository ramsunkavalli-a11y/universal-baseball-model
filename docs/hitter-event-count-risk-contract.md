# Testing physically possible offense ranges and workload related hitting risk

2026-10-04. Saved before new fits. The previous Normal risk model improved
proper scores but generated impossible outcomes at small PA and ignored strong
rate-error dependence on realized workload. This single bounded comparison
addresses both failures without replacing the current point forecast.

## Target and fixed population

Keep all 30,506 forecasts, seven origins, 35 held-player cells, non-arrivals and
exits from the current candidate. Latest target is 2025; 2020 targets remain
excluded and the canceled minor season remains unavailable, not failed
production. Predict next-calendar-year fixed-event batting plus replacement
in common-origin custom win units. This is not full WAR, latent talent, service
control, trade value or proof of MLB-readiness calibration.

Preserve current appearance probabilities, workload distributions, expected
PA, PA-weighted hitting centers and expected offense. References are workload
only and the saved sample-dependent Normal law, including its physical failure.
Public exports supply point forecasts, not matching uncertainty distributions.

## Two coherent count laws

For positive simulated PA n, draw eight event probabilities from a Dirichlet
law, then n integer events from a multinomial. Categories are other, K, UBB,
HBP, singles, doubles, triples and HR; their counts must sum exactly to n.
The same fixed event weights produce delivered offense. Zero PA contributes
an exact probability atom at zero, never a fake zero hitting-talent observation.

The event-profile center is the smallest exponential tilt of an origin-known
MLB reference profile matching the current scalar hitting center. Build each
reference from that origin's MLB counts, excluding the entire outer player
group and, for inner rows, the entire selected inner group; add .5 to each
category. No future environment, held-player outcome, current affiliation or
undocumented old event-model fit enters this new profile. Common-origin league
index is the existing value reference, not a newly learned talent feature.
The reference shape is a working risk assumption, not a new forecast of every
player's true K/BB/HR mix or a park-neutral talent claim.

Compare independent and workload-associated centers. Independent uses the
same predicted rate for every positive n. Associated uses
predicted rate + beta times (log n minus c), where c is E[n log n]/E[n]
under that player's positive-workload law. Thus E[n times rate(n)] is exactly
the original expected batting total. The associated model learns beta rather
than presuming the future workload is an origin-known predictor or claiming
longer playing time causally improves hitting.

Fit beta within [-1,1] custom wins/600 per log PA. This is one bounded working
dependence form, not a slope sweep. Before fitting, certify that the entire
positive n grid 1–800 remains inside the event-index envelope at both slope
endpoints for every outer forecast and calibration forecast. If it fails,
stop and amend before fitting rather than clip rates or drop players.
If an optimizer reaches a bound, retain it and qualify the restriction.

## Calibration and provenance

Reuse the previous test's exact 95 nested contexts, fifty saved nested Ridge
heads, saved inner conditional-PA heads and earlier active calibration IDs.
Independently replay those forecasts, verify exact membership, targets mature
at each inner cutoff and exclusion of both outer and inner player groups.
No new point-model fits or inner folds are needed. Recheck all 130 actual
source/chronology/player subsets before fitting either new count law. Count
distinct people in relevant calibration profiles; global borrowing remains
qualified where specific prospect or absence analogues are missing.

Fit one Dirichlet concentration phi per outer cell for the independent law;
fit phi and beta for the associated law. Use only the earlier nested common-
origin rate residuals. Calibrate by Gaussian moment quasi-likelihood, not an
exact full-profile likelihood: the forecast has only a validated scalar rate
center, so demanding correct future K/BB/HR proportions would answer a different
question. For a profile q the realized average event-index variance is
Var_q(event) times (n+phi)/(n times (1+phi)); multiply by UNIT squared to obtain
rate variance. Verify this moment against the official covariance formula.
This fitting loss does not make the generated distribution Normal.

Use equal represented calibration-origin weights, not PA weights. Phi lies
in [.1,1000000]; estimate on log scale. Optimize independent phi by bounded
scalar likelihood, then associated phi/beta from beta 0, +.2 and -.2 starts
using the independent concentration. Starts check optimization, not held-out
tuning. Preserve objective, convergence, bounds and bias diagnostics. The
already-fitted workload concentration is a shared nuisance estimate from these
same earlier outcomes, not an inner historical risk forecast with a fictitious
earlier vintage. No outer outcome or held-player calibration label is used.

## Simulation and scoring

Use 4,096 positive draws per forecast/arm with deterministic player-origin
seed streams. Keep non-arrival mass exact and compute quantiles from the
weighted empirical positive draws plus the zero atom. Simulated sample means
are Monte Carlo diagnostics, not replacement point forecasts. Do not recenter
draws or manufacture fractional counts to force empirical mean equality.
Analytically verify the actual distribution means against current expected
offense and check every sampled event envelope, nonnegative integer count and
PA total. Preserve every difficult player and all zero-probability cases.

Primary scores are equal-target-year mean P10/P50/P90 offense pinball losses:
associated versus Normal and associated versus independent. Also score
independent versus Normal, proper 80 percent interval score, coverage, width,
negative offense and two-custom-win Brier/log loss, plus current totals and
public point errors. Show current MLB, upper/lower never-debut, absences, thin
new draftees, every origin and active-outcome diagnostics. Bootstrap players
for nominal paired development intervals; no fresh holdout claim.

Check Monte Carlo stability using 8,192 positive draws and an independent
seed stream for every public match, plus the fixed cases and 256 additional
outcome-blind rows chosen by a deterministic row-ID seed order. Require the
public contrast against Normal to retain its direction and differ by at most
two percent of Normal's mean pinball loss. Otherwise leave model ranking
numerically uncertain, not change the sample or tune a seed. Recompute selected
player mixtures independently and retain the full draws for review.

Fixed walks: Gore 2018, Rortvedt 2023, Soto 2023, Judge 2016 and 2024,
Kurtz 2024, Langford 2023, Alonso 2018, Reynolds 2018, Holliday 2023,
Belt 2023, Franco 2023 and Acuna 2022. Add largest gains/harms against Normal
and independent, false highs/lows and an ordinary active case. Explain raw
stats, actual point inputs and saved-fit contributions, event reference and
tilt, fitted phi/beta, positive-workload centering, simulated counts, mean
conservation, range changes, actual MLB outcome and four origin-selected peers.
Review every case before disposition. Do not mistake variance repair for a
readiness repair, or a favorable offense mean for accurate underlying components.

Retain a count-risk law only with coherent counts, stable scores and acceptable
cohort/player evidence; describe residual tail/support limits. A failed associated
center does not reject all workload/performance dependence. No post-result
parameter sweep, selected high-PA routing, protected 2026 outcomes, frozen
forecast change or deployed explorer promotion. Public workload/readiness and
full player-value gaps remain regardless of this result.

The count-law definition and integer support follow the
[official Dirichlet multinomial documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.dirichlet_multinomial.html).
Proper range scoring follows
[Gneiting and Raftery](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf).
The tilt, mean-preserving dependence form and calibration recipe are explicit
working assumptions of this project, not findings from those references.
