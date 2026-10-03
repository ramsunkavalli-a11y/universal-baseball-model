# Separate next year MLB participation from playing time when active

2026-10-03, before fitting. The historical ranking and fallback experiments are
fully reviewed. They show real readiness gains and a substantial lower-minor
overprediction: prospect quality does not imply an immediate MLB job. This is
one architecture comparison using the same audited data, not more arbitrary
gates or another algorithm tournament.

## Target and fair comparison

For each of the same 30,506 historical player/origin identities estimate the
probability of any MLB PA next calendar year and expected MLB PA conditional on
any appearance. Their product estimates expected PA. This identity does not
assume participation and workload are independent: the second mean is explicitly
conditional on participation. The conditional model is trained only on positive
PA labels already complete at its training cutoff, never by removing future
nonparticipants from evaluation. Target 2020 remains excluded; canceled 2020
MiLB production remains missing rather than bad hitting.

Compare two binary hurdles: count/games/draft inputs (239), and the same inputs
plus reviewed historical ranking features (251). Contrast with saved count
direct mean, unrestricted rank direct mean, positive-rank fallback and entire
working assembly. No predictor additions, historical source changes, manually
assigned readiness labels or new college collection. Keep all forecast exits,
non-arrivals and 218 unverified roster-only rows with their qualification.

Earlier four-state hurdles used arbitrary workload bins, separate conditional
value heads and did not have this reviewed historical-ranking panel. Their
negative result is not independent evidence for or against this binary
participation/conditional-workload construction. These exposed development
results do not create an untouched final test; 2026 remains protected.

## Fits and support before fitting

Thirty-five existing chronological whole-player cells, with every full and
conditional subset preflight saved before any fit. Count distinct active-label
training people by origin stage, debut, age and ranking profile, separately
from broad-population support. Retain sparse/outside profiles in scores; a
populated broad profile does not certify rare ranked teenagers. Conditional
predictions are hypothetical workload if active for every evaluated person,
including those later inactive; low participation should reduce their mean.

Each arm has one histogram binary log-loss classifier and one histogram
squared-error conditional-PA regressor. Both use unchanged settings: 250
iterations, depth three, leaf thirty, learning rate .05, L2 ten, seed 31,
no early stopping, two threads. Equal-origin weights are recomputed within each
declared training population. No tuning or selection among multiple parameter
settings. There are 140 fitted heads in total, with persistent per-cell handles
and exact saved predictions; do not restart a still-live job.

Probability is [0,1]; conditional PA is bounded [1,800]. Permanent unavailability
and the reviewed reversible retirement rule set expected participation/PA to
zero while the state applies. Preserve raw probability and hypothetical
conditional PA separately. Fixed V34/V38 batting rate and origin replacement
produce delivered offense/replacement from expected PA; no new conditional
talent head, full WAR or service/control valuation is claimed.

## Scoring and mandatory actual cases

Primary equal-origin PA MSE and fixed-rate contribution MSE, with PA MAE,
nominal player-cluster intervals, probability Brier/log loss and group calibration.
Score identical public matches and preserve practical targets. Report all seven
origins, four stages, never-debut upper minors, brief debut, current listed and
top20, ranked lower minors and totals. Check 2021, 2023 excess and lower-minor
overprediction directly; do not rescale totals using future league results.

Fixed reviews: all twenty completed fallback cases, including Salas, Mayer and
Devers; add largest gain/harm, false high/low and ordinary cases for each fitted
arm and value endpoint if distinct. Show actual counts, all model inputs,
probability/logit path, conditional PA path, expected PA, fixed batting rate,
contribution, observation and origin-selected peers. A classifier's path terms
are log odds, not PA; apply its logistic link before multiplying by workload.
Include failed prospects and sparse conditional profiles. No disposition or
next-model choice before these walks are complete.

A useful result must improve the intended readiness mechanism without hiding
established-player/public errors or cohort excess. A negative result closes
this particular binary construction, not scouting or conditional modeling in
general. Do not promote, edit frozen/deployed forecasts or declare the practical
goal complete on a small pooled win.
