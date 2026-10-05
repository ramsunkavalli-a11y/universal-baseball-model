# Test a coherent hitter evidence representation

2026-10-04. This contract follows the completed overseas player review and the
175-head incumbent replay. It tests whether fixing how production evidence is
represented improves next-year MLB hitting and delivered batting value, without
discarding the incumbent's useful MLB tracking and prospect information. It is
exposed historical development, not protected confirmation or a finished full
WAR, six-year control or trade-value model.

## Exact comparison and membership

Keep the unchanged routed incumbent and the failed domestic/overseas heads as
saved comparisons. Fit exactly two new complete models: repaired domestic talent
with foreign exposure/missingness controls, and identical talent plus seven
translated foreign event contrasts. Both use the same repaired playing-time
head inputs and settings; fit the two common job heads once per cell. Do not
fit an algorithm tournament, choose winning subgroups or blend after results.

Retain 30,506 original evaluation rows and thirteen additional-player rows,
from the sealed complete integration. Training source includes all 32 admitted
origins alongside 63,282 old origins where their chronology allows it. The
seven original evaluation origins are 2016–2018 and 2021–2024; every target is
the following calendar year's MLB batting. Use the same five whole-player
groups and exact training/test identities. Preserve non-arrivals and exits.
An addition without an incumbent forecast has no incumbent comparison, not a
zero benchmark. No inclusion based on a future MLB success or signing.

Original compatible labels remain fixed: batting wins per 600 PA relative to
the target MLB event environment, and PA times that yield plus origin-season
replacement. Do not score copied legacy `next_batting_rate`/`next_value` fields
against these forecasts. Target-zero batting rate is unobserved, never average
talent. Actual zero PA needs complete target coverage. Target 2020 remains
excluded; actual short-season MLB, canceled US minors, real overseas 2020 and
post-2021 league changes remain explicit.

## Talent inputs and fixed units

Start from the incumbent's 199 numeric-history rate names. Remove its 98 raw
pooled non-MLB rate columns, not their actual source records. Keep the seven
pooled MLB rates, MLB quality, age, position, draft, exposure and other existing
context. Retain all nine dated scout inputs and all 63 MLB tracking controls
and measurements. Add a broad known-outfield indicator; it does not guess LF,
CF or RF. Correct UNKNOWN to known-unspecified only where dated role codes
actually establish OF. Keep unresolved conflicts visible.

Replace the redundant raw minor rates and all-level translated profile with
seven mutually exclusive non-MLB event contrasts, plus exposure share, supported
fraction and missingness. Events are K, unintentional BB, HBP, 1B, 2B, 3B and HR;
other is the omitted coordinate. Compute the non-MLB event distribution from
actual same-player count history and the incumbent's saved same-origin,
outer-held-player-excluded translation graph. No refitting league translation
or inventing a connection for a disconnected level. Each source season gets
normalized recency 1/0.8/0.6. Graph smoothing stays at 0.5 per event.

For each row define n_MLB, n_minor and n_foreign as normalized recency PA from
their supported sources. Minor event contrasts are their translated probability
minus that graph's MLB reference, divided by 0.1 and multiplied by
n_minor/(n_minor+n_MLB+n_foreign+1200). Foreign contrasts use the same form with
n_foreign in the numerator and the existing borrowed-stability translation's
MLB reference. Foreign league probabilities are pooled by actual normalized
recency PA, not by their saved 5/4/3 units. Preserve the existing nested outer-
plus-own-player-fold exclusions and mover support. Both arms receive the same
foreign exposure/missingness controls and the same information denominators.
Only the second arm receives foreign event contrasts.

The 1200-PA regularization mass is inherited from existing representation,
chosen before fitting this comparison; it is not an estimated stabilization
threshold or proof that foreign/minor PA equal MLB PA. No tuning this mass
against named players or evaluation years. Report its attenuation on real
source cases before the fit. Sparse foreign translation remains uncertain
regardless of a large observed PA count. Do not add raw CLR, mover-count or
duplicated translated columns as independent unattenuated talent coefficients.

Use the incumbent's fixed-unit transform: PA /600, observed career MLB PA /6000,
stat gap /5, pooled rates centered on their saved priors and divided by 0.1.
Other existing inputs keep their declared units. New event contrasts and
information shares are already scaled. No fitted StandardScaler. Ridge alpha
100 with intercept, no future-dependent clipping. All active training rows use
the incumbent weight formula: equal-origin row weights times uncapped actual
future PA, globally normalized to mean one. This changes both features and
routing relative to the incumbent; a gain is a complete-representation gain,
not an isolated causal effect of the sample-share formula.

## Playing time and availability

Both candidates use the 251 existing job features plus the reviewed 28 status
features and fourteen source-derived job inputs. The latter include MLB plus
observed NPB/KBO first-team activity by lag, last observed professional stat gap,
last positive MLB workload/quality and its lag, last positive first-team workload
and its lag, returner MLB workload, dated linked-job first-team workload and the
broad outfield indicator. This lets ordinary experienced returners and foreign
professionals share an opportunity representation. It does not relabel foreign
PA as MLB PA, assume a known starting role or fabricate guaranteed job terms.

Preserve literal roster flags and ambiguous agreement versus explicit MLB link.
Finite, unresolved, medical and permanent restrictions stay distinct in the
reviewed status inputs. No fabricated remaining available games from an original
suspension total; tentative returns remain tentative. Last observed work is
evidence, not proof of recovery. Retired and known permanent-ineligibility rules
remain explicit. Do not retrospectively label Belt retired or import McLain's
later injury. User-closed team-record testing remains closed.

Fit common histogram gradient classifier and conditional-PA regressor:
250 iterations, depth 3, leaf minimum 30, learning rate 0.05, L2 10, no early
stopping, seed 31, equal-origin row weights. Expected PA is probability times
conditional PA clipped to [1,800], with explicit permanent/retirement zero rules.
These two conditional averages are an initial factorization, not demonstrated
joint uncertainty or full value distributions. No unseen job information.

## Prefit requirements and scoring

Before any fit, seal code/contract/source hashes, all 35 actual full/active
preflights, both talent matrices, the common job matrix, exact membership and
compatible labels. Check chronological whole-player exclusion, origin references,
source-derived attenuation, broad OF, future-result/transaction exclusion and
missing-versus-zero behavior. Count distinct people by age, stage, recent MLB
exposure, professional activity, foreign source and restriction context for
each fitted subset. Save extrapolation warnings; do not drop sparse rows or
pretend twenty peers certify a forecast. Replay the incumbent before selection.

Primary comparisons are original-cohort delivered batting-value RMSE and
equal-origin actual-PA-weighted hitting RMSE among observed participants. Report
value MAE/bias, PA RMSE/MAE, Brier/log loss, totals, all origins and stages,
never-debut upper/lower cohorts, brief MLB entrants, established hitters and
foreign cases. Preserve 2021 and inspect other years independently. Report
the thirteen additions separately with their non-arrivals and missing incumbent.
Use matched historical Steamer/ZiPS cohorts in the existing compatible common
rate reference; ZiPS depth-chart/nominal PA limitations stay qualified.

Working public tolerances remain PA RMSE within 10% of Steamer, PA MAE within
15%, delivered batting-value RMSE within 10%, plus meaningful UBM improvement.
Raw public value conversion, release-date and park/environment qualifications
do not permit an unqualified talent-superiority claim. Nominal paired whole-
player bootstrap, 2000 repetitions, seed 84, with fixed original origin weights;
it is development evidence, not independent confirmation. Show mechanical
workload-only and talent-only value changes to detect cancellation, not to select
a post-result blend. Do not force totals to the future realized cohort.

Before disposition walk the existing fixed failure cases, largest new gains,
harms, false highs/lows, ordinary players and non-arrivals through actual source,
shares, fitted terms, job outputs, forecasts and compatible realized outcomes.
Keep the previous 38 cases visible and add outcome-selected cases by the saved
rule. Include outcome-blind peers and actual support limits. A lucky value score
with an extreme rate or very low PA does not pass reasonability.

## Stop conditions and deliverables

Source/chronology/membership failure stops fitting. A passed unit test does not
authorize promotion. A smaller pooled error with systemic lower-minor, foreign,
returner or total failures remains provisional pending concrete player analysis.
If both arms lose, diagnose the failed computation before another fit; do not
reject all foreign or detailed evidence or start another algorithm sweep.

Save a separate complete result and player review. Only a coherent candidate
with meaningful benchmark/cohort/reasonability evidence can become the research
model card and team-filtered explorer. No protected 2026 outcome access, frozen
forecast changes or replacement of existing explorers is authorized. The broad
goal stays active while its practical candidate and final deliverables are absent.
