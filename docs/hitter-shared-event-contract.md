# Shared event learning for hitters without MLB experience

2026-10-04. This fixed development comparison follows the completed evidence
comparison and its player review. It tests a common, coherent hitting profile
instead of separate nearly unlearnable foreign production coefficients. The
current model is the benchmark. Completed 2026 outcomes remain unopened.

## Target and exact population

Predict next calendar year's MLB batting wins per 600 PA relative to that
year's MLB environment, and its delivered batting plus replacement contribution.
Rate is unobserved for non-arrivals; their delivered contribution is zero.
Retain all 30,506 original evaluations and separately score the thirteen additions,
all five whole-player folds, seven origins and exact training identities from
the completed representation comparison. Targets end in 2025. Target 2020 stays
excluded; origin-known 2020 short MLB seasons, canceled minors and real foreign
seasons stay as recorded. This is not full WAR, long-term DSL upside, control
years or trade value.

## Preserve useful branches and isolate hitting

Fit two Ridge talent heads per existing cell: common domestic profile, and the
same profile with supported foreign production pooled into it. Both heads use
all active training rows, as the incumbent prospect head does. Use a new head
only when prior MLB debut is zero. Every original previously debuted hitter
retains exactly the incumbent talent forecast, including its tracking routing.
All original rows retain incumbent PA, probability and conditional PA. This
isolates a prospect/newcomer talent change, not a claim to fix opportunity.
The thirteen additions use the previously completed common job heads, identical
in both arms, because they have no incumbent forecast. All thirteen also use the
new raw common talent head, including five with an old MLB debut but no incumbent
row. Their scores are separate; this does not change original-player routing.
Do not select a workload blend or a winning cohort after seeing results.

## Consistent event meaning and learning strength

Use the eight exclusive events other, K, unintentional BB, HBP, 1B, 2B, 3B,
HR. US source histories use actual PA times recency 1, 0.8, 0.6 and the existing
outer-fold-excluded, own-origin translation graph. This includes MLB where
present. Graph connections, offsets and 0.5-per-event smoothing are unchanged.

Existing foreign probabilities already predict following-year MLB events.
Therefore do not pool them with uncalibrated past US equivalencies. Apply the
existing borrowed domestic persistence fit's intercept and per-event slope to
the US pooled relative log probabilities, then normalize with softmax. The
fit is origin-local and excludes outer plus the row's own player fold; use the
same saved exclusion-qualified fits underlying the foreign inputs. Borrowing
MLB persistence for translated minors is a new transport assumption, not a
demonstrated minor-league aging curve. Keep that limitation explicit.

Foreign probabilities are centered on a differently held MLB reference. Rebase
their relative log probabilities onto the US graph's MLB reference before
pooling. Weight US and supported foreign distributions by normalized observed
PA, not old 5/4/3 units. Newer MLB exposure naturally reduces old foreign shares
in the raw profile; deployed established-player talent remains unchanged.
Disconnected/unsupported sources stay missing, not guessed average ability.

The eight common probability deviations, divided by 0.1, are unattenuated.
There is no extra exposure-share multiplication followed by the inherited
penalty. Retain all eight coordinates with symmetric Ridge alpha 100, the
incumbent fixed units, intercept and uncapped future-PA times equal-origin-row
weights normalized globally. There is no new alpha, prior-mass selection or
tuning. Persistence strengths are the existing chronology/player-excluded
training estimates, not choices from named evaluation outcomes. Reliability
and log exposure are separate context controls, not claims of posterior certainty.

Both heads have the same 108 incumbent context/MLB numeric inputs after removal
of the 91 raw non-MLB rate columns, nine scout inputs, twelve shared profile
inputs, four foreign exposure/missingness controls and one broad OF indicator.
Only the eight profile probabilities differ between arms. Foreign controls and
total source reliability use identical definitions in both. No raw minor or
foreign production bypass, tracking replacement, new job fit, new data collection,
team-record test or algorithm tournament.

## Source and support gate

Seal all source/code/contract hashes, five source matrices, all seventy actual
active-head preflights and forecast-profile counts before new hitting fits.
Verify all saved calibration/graph exclusions and chronology, mutually exclusive
counts, coherent probabilities, fixed membership, finite matrices, source-removal
stability and explicit missingness. Each case keeps real level-season counts,
source probabilities, reference alignment, persistence estimates, actual source
weights and final common profile. Retain the prior 41 cases as fixed diagnostics.
Source walks precede fitting. Sparse or absent profiles remain in scoring.

## Scoring and disposition

Primary: original-cohort delivered contribution RMSE and equal-origin actual-PA
weighted hitting RMSE. Also report MAE, bias, totals, seven origins, upper/lower
never-debut cohorts, foreign newcomers, all no-arrivals and separately the thirteen
additions. Public matched Steamer/ZiPS comparisons must remain unchanged for
previously debuted hitters by construction; do not describe this experiment as
closing the public PA gap. Use the existing compatible reference and its release,
environment and park qualifications. Nominal paired player bootstrap: 2,000
draws, seed 84, fixed original origin weights, development evidence only.

Replay all seventy heads and independently reconstruct compatible labels and
scores. Walk retained cases plus largest gain, harm, false high/low and ordinary
cases through actual fit terms and origin-selected peers before disposition.
Check power/contact directions under coherent same-fit probability transfers;
these explain mechanics, not causal effects. A lucky value gain caused by almost
zero PA does not establish good talent prediction. Require improvement in both
primary losses with no unexplained systematic lower/upper-minor or total failures
before research selection. If it loses, retain the incumbent and state which
design assumption failed; do not reject all minor/foreign evidence.

No candidate freeze or 2026 access occurs in this test. User authorization for
2026 evaluation remains conditional on a later immutable candidate freeze.

## Literature behind the design

[Pavlidis on minor-league rates](https://tht.fangraphs.com/adjusting-minor-league-rates/)
distinguishes same-player league transport from simply comparing league averages
and emphasizes park/stringer complications. Our graph follows the former idea
but is not fully park-neutral. [Lichtman's regression discussion](https://tangotiger.net/mgl/regression.pdf)
distinguishes component persistence and the population mean, rather than a universal
regression constant. It does not endorse our numeric settings or prove transport
to minors. [FanGraphs on equivalencies](https://library.fangraphs.com/principles/league-equivalencies/)
describes translating non-MLB performance to a common competition scale. The
shared future-event representation here is our testable design, not a quotation
or claimed recreation of a proprietary public projection system.
