# Prospect nested career-value result

Status: promoted to the private playable preview; provisional and not publishable.

## Result

The nested career hurdle fixes the statistical contradiction and avoids both earlier extremes.

| Population | Version | 45+ FV | 50+ FV | Total expected six-year WAR |
|---|---|---:|---:|---:|
| Hitters | Full-workload-on-arrival preview | 930 | 352 | 3,876 |
| Hitters | Nested career hurdle | 404 | 86 | 1,687 |
| Pitchers | Full-workload-on-arrival preview | 215 | 38 | 558 |
| Pitchers | Nested career hurdle | 40 | 2 | 163 |

All 6,719 modeled pre-MLB player-type rows satisfy `arrival >= meaningful >= established`; there are zero ordering repairs. Mean hitter probabilities are 15.73% arrival, 9.67% meaningful, and 8.07% established. Mean pitcher probabilities are 13.41%, 8.04%, and 5.97%.

Josuar Gonzalez remains 45 FV with 1.83 expected six-year WAR. His nested probabilities are 19.98% arrival, 18.31% meaningful, and 14.95% established. This is lower than the inflated 3.28 WAR preview without treating a credible prospect as nearly worthless.

The outside Top-100 diagnostic is worse than the inflated incumbent (10.92 versus
8.37 FV MAE) but materially better than the rejected binary and independent-three-tier
versions. It did not fit, select, floor, or calibrate the model.

## Decision and limits

Use this version in the local results explorer so the current model can be inspected honestly. The explorer now shows arrival, meaningful-role, and established-role probabilities separately. Pre-MLB star probability is withheld until uncertainty is rebuilt for the nested distribution.

This is not a finished prospect ranking. Pitcher values remain compressed, although
the confirmed private age-for-level/hand adjustment now gives the top end more spread.
The very top hitter ordering still needs direct error review against baseball evidence
rather than outside FV inputs. The repeated two-year conditional hazards are an
explicit six-year approximation requiring later confirmation.

MLB contract value and service/control logic did not change. The private pitcher skill
rate now includes the confirmed age-for-level/hand adjustment; public output remains
unchanged.

Machine-readable detail: `docs/prospect-nested-career-value-result.json`.
