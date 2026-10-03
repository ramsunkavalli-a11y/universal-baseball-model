# Compatible hitting and delivered offense comparison

2026-10-03. Follow the practical hitter plan after closing the smooth workload
batch. Test hitting and delivered offense on one explicit event/value scale,
without refitting opportunity or choosing another generic tree library.
Protected 2026 and frozen/deployed forecasts remain unchanged.

## Source correction before fitting

Preserve V53's 63,282 source rows, 30,506 evaluation rows and 35 chronological
whole-player cells. Join the already reconstructed eight MLB outcome counts and
origin/target league distributions from V50. Independently reconstruct actual
counts from the dated V31 count table. Keep source publications/vintages qualified.
Every non-arrival stays in delivered scoring; conditional rate is unobserved,
not zero talent, when actual MLB PA is zero. Exclude target 2020 as before.

The source origin replacement rate divides a season's replacement-per-PA rate
by schedule fraction twice overall: 570*fraction/league_PA, then /fraction.
For 2020 this yields .008571 instead of roughly .00317 per PA. The retained
rate and workload models do not use this field as a predictor; no attribution
of their misses to this error is warranted. It matters when reconstructing
common-origin value training labels, especially for the 2020-origin cohort.

Use 570*fraction/league_PA, the original seasonal replacement allocation per
actual PA, as the full-season forecast reference: annualized expected league PA
is league_PA/fraction, so 570 divided by that annualized exposure is this rate.
Use only completed origin-season values; the next league mean never becomes a
predictor. Keep the old rate in a separate field. Correct all origins consistently,
including tiny full-season schedule differences, not only the most visible year.
Preserve old source labels and recorded forecasts. Rebuild comparison baseline
value from its exact unchanged PA and hitting rate under the corrected reference.
Separate this measurement change from predictive differences.

With fixed event weights, actual numerator/PA minus origin numerator/PA gives
common-origin batting rate, converted by 600/(10*wOBA_scale). Common delivered
offense is PA*(that rate/600 + corrected origin replacement rate). A matched
relative target uses actual numerator/PA minus the target league numerator/PA,
but the SAME corrected origin replacement rate. Zero participation gives zero
delivered offense in either target. This isolates environmental centering in
the new direct comparison, not a different replacement budget.

The prior relative rate is a sensible hypothesis about league-neutral talent,
not automatically a bad label: forecasting absolute events requires an assumed
future environment. The origin-centered alternative learns the historical raw
transition instead. Unknown future run environments remain irreducible uncertainty.
Neither is certified park-neutral talent or official WAR.

## Locked models and interpretation

Retain the same public matches and exact V53 expected PA and policy overrides.
Keep existing V53 batting as the benchmark. Three fitted heads per actual cell:

1. Common-origin conditional rate: the exact 199 V53 rate features, fixed safe
   physical scales and Ridge(alpha=100), weighted by actual future PA within
   equal origins as V53. Only the rate target changes.
2. Relative delivered offense: V53's 251 opportunity features, fixed V53 histogram
   regressor settings and equal-origin weights, all outcomes including zeros.
3. Common-origin delivered offense: identical to head 2 except common-origin
   delivered target. Their paired contrast isolates the environmental target.

No extra feature collection, status-source mix, tuning, output tail cap, public
projection predictor or selected blend. Definitive unavailability/retirement
forces delivered value to zero. Direct value heads do NOT predict playing time,
appearance probabilities or conditional talent. Their outputs are expected
contribution; dividing by baseline expected PA is not a validated talent grade.
Report the compatibility envelope against physically possible event rates at
the retained expected PA. An incoherent PA/value combination cannot be promoted
just because its value RMSE improves. PA-weighted rates target contribution yield,
so separate PA/rate heads do not necessarily assume independence.

Shared cancellation/reorganization context cannot be credited with creating
extra MLB jobs: PA is exact V53 throughout. Report its actual fitted rate/value
terms and origin errors; this does not certify correct handling of the new regime.
All transformations use origin-known own histories, not target-year environments.
Target environments enter historical labels only when those targets are mature.

## Required checks and decision

Before fitting all 105 heads, persist all-player and conditional-active preflight,
actual distinct-player profiles by stage/debut/age/workload/quality, paired labels,
source hashes and the short-season reference reconciliation. Independently match
eight target event counts to V31, the old relative rate and the V53 scored labels
apart from the declared replacement correction. Whole players remain separated.
Unknown or unsupported histories remain warnings with all forecasts scored.

Score conditional rates with actual-PA weighting within equal target years,
whole-population delivered RMSE/MAE/bias and totals, all 2,627 public matches,
current/absent/brief/large MLB use, never-debut and each stage/origin. Preserve
Steamer/ZiPS on the same custom-event scale; plain ZiPS PA are not workload.
Use nominal paired player-cluster development intervals, not fresh validation.
No historical score can waive remaining opportunity/public-MAE or career gaps.

Fixed cases: Judge at 2016, 2022 and 2024; Winn 2023; Steer 2022; McLain 2024;
Tatis 2022; Kurtz 2024; Langford 2023; Soto 2017; Alvarez 2022. Add largest value
gain/harm, false high/low and ordinary case for each arm. Keep origin-selected
successful and failed peers. Reconstruct actual counts, target/reference math,
scaled inputs, saved fit terms, PA/rate/value intermediates and realized outcomes.
Include 2020-source Semien/Freeman/Guerrero plus full-season Judge and non-arrival
examples in the source/reference review. Review is mandatory before disposition.

Retain a new component only if compatible measurements, cohort/player behavior
and meaningful delivered improvement support it. A direct-value win alone is
not a complete hitter model or six years of club control. Preserve qualified
negative results rather than rejecting all event or joint models. Once this
comparison is reviewed, carry the strongest coherent candidate into calibrated
uncertainty and a plain-language, team-filtered research handoff.
