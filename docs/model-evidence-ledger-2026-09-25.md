# Evidence ledger: what we can and cannot conclude

2026-09-25. Read alongside the [current audit](model-decision-audit-2026-09-25.md).
Numbers below retain the original experiment's population and target. Historical
decisions remain recorded; this ledger corrects over-broad interpretations,
not the scores or their predeclared gates. All results are development evidence.

| Work / source | Supported finding | What it does not establish / next implication |
|---|---|---|
| [Arrival source repair](hitter-arrival-source-repair-v1-result.md) | Corrected debut history, year-end roster support and league context; next-year Brier/log loss improve about 11.2%/9.5% over the unrepaired reference. | 2021 participants still undercounted, 2022 overcounted. Better probability scores do not prove better workload or value. Retrospectively captured source facts are not guaranteed historical publication vintages. |
| [Conditional workload D](hitter-conditional-workload-v1-result.md) | With F participation fixed, detailed conditional workload improves prospect three-year PA RMSE to 121.668 versus the stronger ensemble's 126.184. | Does not test whether F misses arrivals. Role-mixture alternative failed. Later H lower-minors warning uses a different scope/guard; not evidence that the earlier score was fabricated. |
| [Talent and draft features](hitter-talent-workload-v1-result.md) | Combined TP barely changes prospect PA RMSE, 121.668 to 121.534; paired difference uncertain, only one of three origins improves. | Rejects this incremental encoding with participation fixed, not the baseball proposition that better prospects get more chances. Public historical FV/international bonuses were not tested. Do not choose a secondary arm after primary failure. |
| [Opportunity/value integration](hitter-integrated-opportunity-value-v1-result.md) | H PA RMSE 190.97 versus E 193.22, paired MSE interval [-1377.56, -349.50]. H batting RMSE 1.210 versus N 1.140; expanded 1.270 versus N 1.213. | Useful workload signal; deficient value assembly. E/N hold PA and other components equal but change two batting ingredients. Neither rate nor formula is isolated. Next experiment addresses this directly. |
| [Multi-year components](multiyear-hitter-components-v1-result.md) | Adding components to the same batting forecast improves three-year expanded-target RMSE 1.347 to 1.277. Position/running useful; provisional MLB general-defense evidence. | Only two complete normal cumulative origins. Not an all-level MiLB defense win, not exact fWAR. Selected versus benchmark-only 1.277 vs 1.278 is tiny; complexity itself is not proven valuable. |
| Same component study: catchers | Framing near-term evidence stronger than long-term; throwing improves its component but slightly worsens integrated Years 1–2 error; blocking uncertain. | A neutral Year-3 framing selection is insufficient evidence, not a known biological decline or forecast ABS adoption date. Original frozen package and later component display have different general-defense policies. |
| [Six-year extension](six-year-hitter-extension-v1-result.md) | Keeping Years 1–3 fixed, richer later batting heads improve six-year RMSE 2.2517 to 2.1789. | Calendar production, not control value; long full paths cross COVID. Later-component incremental expanded gain is 2.1922 to 2.1816, not the larger gain from adding all six years' components. |
| [Path bridge](player-path-value-bridge-v1-result.md) and [population repair](player-path-population-v1-result.md) | Repaired path population improves distribution scores and mean RMSE from 1.333 to 1.222. | Still trails delivered mean 1.214; prospect regular-workload outcomes 23.5 expected vs 44 observed. Better CRPS does not repair mean/calibration failures. Empirical residual paths already contain event noise; do not add it again blindly. |
| [Pitcher role block](pitcher-role-block-v2-result.md) | Small next-year component-value improvements: pruned ensemble RMSE .31128 to .31092, equal ensemble .31138 to .31109. | Pruned uncertainty crosses zero; stronger evidence for the equal ensemble is not broad proof of six-year pitching value. Contact components without support remain neutral. |
| [Whole-player development baseline](player-value-development-baseline-v2-result.md) | Combined hitter/pitcher score improves .39874 to .38807, predominantly from hitters. | Not a six-year full-WAR/control validation. Residual coverage was development-calibrated, not independently confirmed. |
| Rights/cost interface and older contract work | Accounting machinery and synthetic scenario tests exist. | Neither a player-specific validated career distribution nor calibrated dollar/trade rankings. Current six-year display deliberately withholds full-control value. |

## What the latest apparent failures actually mean

### Lower-minors opportunity: sparse, timing-sensitive, not dismissed

H inherits the D prospect recipe; it did not newly change that recipe when
improving MLB-player workload. Its lower-minors Year-1 MSE is 5.50% worse than
E, barely over the previous 5% guard. A real concern remains: four of five
origins have worse point scores. But 2021 dominates the pooled difference;
outside that origin the interval spans benefit and harm. Only 45 participants
occur in 12,098 rows. Neither "all fine" nor "lower-minors approach disproved"
is justified. The old no-deployment decision is retained; the broader claim is not.

Examples explain why a single story is inadequate (2021 cutoff, three-year PA):

| Player | H forecast | E forecast | Actual |
|---|---:|---:|---:|
| Ezequiel Tovar | 565 | 288 | 1,345 |
| Maikel Garcia | 462 | 149 | 1,164 |
| Jorbit Vivas | 509 | 195 | 0 |
| Eddys Leonard | 388 | 126 | 0 |

H anticipates Tovar/Garcia too quickly in Year 1 yet still predicts too little
over three years; Vivas/Leonard remain false positives over the whole window.
These are diagnostic examples selected after inspecting errors, not independent
validation, rules for named players, or grounds for a universal COVID boost.

### Aggregate totals: distinguish cancellation, allocation and missing opportunity

Average absolute three-year cohort PA error is D 21,639, E 38,132, H 38,524.
D looks best partly because it underallocates prospects and overallocates prior
MLB players. H's 392-PA increase versus E is small next to roughly 539,000
actual PA per cohort. Its 2021 shortfall of 72,770 PA is not small. Report both
the absolute signed error by origin and the prospect/prior-MLB decomposition.
A cohort omits future entrants; it should be compared with that cohort's actual
production, not forced to fill every future MLB job.

### Value: a material batting-block problem, especially established MLB players

H minus N three-year batting MSE is positive with a wholly adverse paired
interval [+0.11556, +0.22042]. Expanded interval is [+0.07921, +0.21186].
The batting gap is especially clear for prior MLB players: +0.866 MSE, interval
[+0.613, +1.141]. Prospect batting difference +0.004 is uncertain. This gap
persists outside 2021. Therefore "COVID explains all failures" is unsupported.

E and N have exactly identical PA/nonbatting inputs; their batting difference
is a clean **block** comparison. It is not a clean **mechanism** comparison:
the horizon-specific rate and inherited-direct-value residual both change.
The next fixed test separates those, using the same archived players and rows.

## Repeated or confounded avenues to stop cycling through

- More engines or more features without specifying an uncovered source of
  predictive information. Several current bottlenecks are accounting and
  participation, not insufficient learner flexibility.
- Another F-fixed workload encoding described as a new arrival test.
- A new full path model judged only on average error across non-arrivals.
- Direct-total components divided by tiny expected PA and then rescaled as
  if they were independently estimated rates.
- An old weaker batting construction reused as the only integration benchmark.
- Calling 2012–2015 reconstructed snapshots same-recipe nested E/F/D forecasts.
- Choosing a subgroup, threshold or blend after viewing its favorable result.

These are restrictions on inference and workflow, not a claim that all possible
models in these families are exhausted. Before restarting one, name the changed
assumption, available input, diagnostic prediction and fair control.
