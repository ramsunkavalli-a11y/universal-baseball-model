# Test playing time probabilities and outfield positional value

2026-10-08. The user requested testing of Lau Sze Yui's positional-adjustment
thread and Dan Szymborski's percentile-calibration example. These are two fixed
diagnostics, not new fitted forecasts or permission to change the explorer.
The unfinished first-base prior comparison remains separate.

## Playing time probability test

Use the existing 30,506 historical next-calendar-year MLB PA forecasts and their
saved nested beta-binomial dispersion fits. Targets are 2017–2019 and 2022–2025.
Keep every origin, person, absence, non-arrival, mean and appearance probability.
No 2026 outcome access, new fit, width adjustment or choice among recipes.
Compare the saved beta-binomial law with its mean-matched binomial reference;
the latter is a narrow technical control, not ZiPS or Steamer uncertainty.

Reconstruct the full discrete distribution on 0–800 PA from saved appearance
probability, conditional mean and concentration. Verify its mean, saved quantiles,
CRPS and 400-PA probabilities. Check saved provenance: nested training/validation
people exclude the outer held group, validation labels mature by the outer
origin, and available recorded source/forecast/calibration hashes still agree.
The relocated forest reference is not used in this new contrast; its disconnected
file is recorded as an unverified upstream reference, not fabricated or silently
certified. Missing required distribution inputs or maturity failures stop the
affected assertion, not row drops. Prior upstream feature certification remains
qualified where its older raw inputs cannot currently be reopened.

At percentiles .05, .10, .20, .30, .40, .50, .60, .70, .80, .90 and .95 report
the fraction strictly exceeding the predicted quantile and the model's actual
probability of doing so. Integer PA and the large zero atom mean that probability
need not equal one minus the percentile. Also compute the randomized probability
integral transform analytically: spread each outcome's mass uniformly across
[F(y-1), F(y)] and integrate its share into ten percentile bins. Under correct
calibration each bin averages 10%; do not replace tied zeros with arbitrary
midpoints or call inclusive 99% coverage an 80% calibration pass.

Report proper CRPS, P10/P50/P90 pinball loss, interval width/coverage, any-PA and
400-PA Brier/log loss, expected and observed counts. Weight represented target
years equally and show pooled counts too. Use 1,000 deterministic player-cluster
bootstrap draws, seed 100826, for primary probability-bin deviations and paired
CRPS; these conditional development intervals do not include shared season
shocks, fitting uncertainty or repeated-model-selection bias.

Show all, current MLB, never-debut upper/lower minors, previously debuted but
absent, source-unsupported profiles, each origin, forecast probability bands and
current MLB age bands. Positive-PA conditional-law results are a separately
labeled survivor diagnostic, not a way to select the forecast. A 250-actual-PA
slice, if shown, is likewise not population calibration. For discrete conditional
PA retain randomized treatment of ties. Do not claim hitting, full WAR or career
value uncertainty: these saved distributions describe workload only and predate
later hitting/readiness repairs.

Walk all fourteen previously reviewed saved cases again with the new calibration
quantities; preserve their dated histories, actual input/head traces and existing
origin-only peers. Explain central/upper/lower outcome placement, activity and
400-PA chances, as well as misses and ordinary cases. Verify every saved case PMF
against the reconstruction. Prior player reviews supply upstream traces, not
automatic approval of these new diagnostics.

## Outfield position switch test

Use the certified native range ledger for 2016–2025, no new download or 2026
results. Retain annual range/exposure validity and show excluded/unknown counts.
Primary same-player/same-season pairs require at least 450 native outs at CF and
450 at measured LF/RF combined (150 innings each); a predefined 900-out
sensitivity checks whether short stints dominate. Never count missing corner
measurements as zero or build a pair from a partially measured corner season.

Compare CF and corner range runs per 500 innings. For each player-season show:
raw range difference; position-relative difference after subtracting the full
measured seasonal position means; and that difference plus the fixed schedule's
10 runs per 1458 innings CF premium. Corner annual references are weighted by
that player's measured LF/RF exposure. Show LF-only and RF-only pairs as separate
diagnostics and each year, including 2020 and 2021 explicitly. Primary mean gives
each distinct person equal weight across repeated seasons; report row-balanced
and harmonic-exposure-weighted means as sensitivity, not alternatives to select.
Use 1,000 person-cluster draws, seed 100827.

The equalization gap is the positional credit that would offset the average
paired position-relative difference. It is descriptive switcher evidence, not
an identified universal replacement-value constant: switching is selected,
position experience, assignments, park, opponent, difficulty and within-season
health can differ. Range is not arm value or all defense. Same-season pairing
reduces aging/era confounding but cannot erase these limitations. Do not choose
a positional schedule by RMSE against a target that embeds the same schedule.

Separately demonstrate raw versus position-relative accounting on the identical
pairs: transferring the reference offset between range and position columns must
leave totals unchanged. A changed total must be explicitly a different valuation
assumption. Existing fixed schedule is a reference, not validated by agreement
with itself. No single CF premium is deployed from this diagnostic.

Fixed cases: Mookie Betts, Cody Bellinger, Harrison Bader and Ceddanne Rafaela
when eligible. Add extremes in both paired-difference directions and an ordinary
median-difference case. For each retain all native annual position rows and
annual reference calculations; choose three peers using same season and nearest
CF/corner exposure only, never later outcomes. Trace raw runs and outs through
rates, reference subtraction, positional credit and implied full-season gap.
Report any missing fixed case instead of changing eligibility.

For SS/1B, report same-season pair counts under the same exposure thresholds but
do not combine the infield and outfield baselines into one switch matrix. Catcher
value, framing under ABS, minor defensive talent and playing-time allocation are
outside this range-only comparison.

## Decision and preservation

Both tests end in diagnostic findings, not accuracy-gain or deployment claims.
Complete the player walks before interpreting either test. Persist contracts,
source hashes, per-person derived quantities, summaries, uncertainty and
independent arithmetic checks. Fail on duplicates, invalid mass, changed means,
unknown evidence made zero or altered protected files. Save small compressed
evidence; avoid copying bulky inputs because C: is low on space and relocated D:
sources are currently disconnected. These tests use inputs still on C:.

Sources: [Lau's thread](https://x.com/903124S/status/2093001808780390412),
[Szymborski's example](https://x.com/DSzymborski/status/2089018876080124113),
[FanGraphs' outfield accounting correction](https://blogs.fangraphs.com/a-fangraphs-war-fielding-update/),
and [proper scoring rules](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf).
