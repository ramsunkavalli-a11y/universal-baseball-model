# Prospect nested career-value result

Status: promoted to the private playable preview; provisional and not publishable.

## Result

The nested career hurdle fixes the statistical contradiction and avoids both earlier extremes.

| Population | Version | 45+ FV | 50+ FV | Total expected six-year WAR |
|---|---|---:|---:|---:|
| Hitters | Full-workload-on-arrival preview | 903 | 320 | 3,813 |
| Hitters | Nested career hurdle | 378 | 81 | 1,687 |
| Pitchers | Full-workload-on-arrival preview | 156 | 18 | 769 |
| Pitchers | Nested career hurdle | 24 | 1 | 232 |

All 6,719 modeled pre-MLB player-type rows satisfy `arrival >= meaningful >= established`; there are zero ordering repairs. Mean hitter probabilities are 15.05% arrival, 9.47% meaningful, and 7.92% established. Mean pitcher probabilities are 9.83%, 5.66%, and 3.96%.

Josuar Gonzalez now remains 45 FV with 1.55 expected six-year WAR. His nested probabilities are 17.34% arrival, 15.77% meaningful, and 12.50% established. This is lower than the inflated 2.84 WAR preview without treating a credible prospect as nearly worthless.

The outside Top-100 diagnostic is worse than the inflated incumbent (11.95 versus 9.06 FV MAE) but materially better than the rejected binary and independent-three-tier versions. It did not fit, select, floor, or calibrate the model.

## Decision and limits

Use this version in the local results explorer so the current model can be inspected honestly. The explorer now shows arrival, meaningful-role, and established-role probabilities separately. Pre-MLB star probability is withheld until uncertainty is rebuilt for the nested distribution.

This is not a finished prospect ranking. Pitcher values remain too compressed, and the very top hitter ordering still needs direct error review against baseball evidence rather than outside FV inputs. The repeated two-year conditional hazards are an explicit six-year approximation requiring later confirmation.

No MLB contract value, service/control logic, skill rate, or public output changed.

Machine-readable detail: `docs/prospect-nested-career-value-result.json`.

