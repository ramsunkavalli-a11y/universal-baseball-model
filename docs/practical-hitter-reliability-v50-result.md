# Learning separate trust levels did not beat the existing hitting estimate

2026-10-03. All 70 fits replay; 25 actual player reviews complete. Keep the
existing batting forecast. The new formula learns sensible differences between
skills, but that alone is not enough to forecast better.

The [contract](practical-hitter-reliability-v50-contract.md) compares fixed-100
shrinkage with eight learned skill strengths, using the same conditional prior,
30,506 historical forecasts and binary-scouting expected PA. The
[execution amendment](practical-hitter-reliability-v50-execution-amendment.md)
records the initial optimizer failure and scaling repair before any completed
fit or scored prediction. All amended fits converge without touching alpha
bounds. Those checks establish execution, not predictive success.

| Same population and workload | Existing rate | Fixed reliability | Learned reliability |
|---|---:|---:|---:|
| Future MLB batting rate RMSE | 1.82465 | 1.93202 | 1.85346 |
| Delivered offense RMSE | 0.43815 | 0.45379 | 0.44351 |
| Public matched rate RMSE | 1.69337 | 1.83032 | 1.73033 |
| Brief debut rate RMSE | 2.27810 | 2.49765 | 2.33173 |
| Current regular rate RMSE | 1.48363 | 1.56142 | 1.50884 |

Rate units are batting wins above the realized MLB average per
600 PA, weighted by actual future PA within equally weighted origins. Delivered
offense is batting plus replacement, not full WAR. Public conversion still has
the old environment/date qualification and does not prove UBM beats Steamer.

Learned versus existing all-row contribution MSE increases 0.00472, nominal
player-clustered 95% interval +0.00184 to +0.00734. Rate MSE increases 0.10599,
interval +0.05064 to +0.15753. Learned versus fixed clearly improves both.
Only origin 2021 improves against existing; most origins and major populations
do not. These repeatedly exposed historical results are development evidence.

Typical learned strengths are about 80–108 PA for K, 247–334 for HR,
253–307 for walks and 1,537–2,174 for doubles. These are fitted predictive
shrinkage parameters, not exact stabilization thresholds or posterior sample
sizes. Normalization couples the eight final probabilities. A larger prior
strength need not mean a skill is unimportant.

## What the players tell us

The [actual walkthrough](../reports/model-evidence/practical-hitter-reliability-v50/player-walkthrough.md)
traces all source counts, transported anchors, learned priors, final events,
support and unsuccessful origin-selected peers. It shows real tradeoffs:

- Established Judge improves: 2023-origin rate rises 3.40 to 4.29 against 7.56
  actual. But the poor 95-PA debut still pulls 2016-origin K too high and HR too
  low; rate falls from -0.06 to -0.86 against 5.33 actual. These are the two
  meaningful PA-weighted rate extremes, not one-to-three-PA noise.
- Winn's good AAA contact is not recovered enough. Steer and Alonso's upper-
  minor power remain compressed. Bellinger and Kurtz still have both power and
  immediate-opportunity misses. No MLB history means a conditional prior,
  not proof of current MLB ability for a DSL player.
- Betts loses useful development information: adaptive 1.65 versus old 2.56,
  actual 6.54. Votto improves, but fixed-100 is better than adaptive in his case.
- Forsythe and Nevin appear accurate in delivered value partly because low PA
  offsets an optimistic batting rate. Tatis's zero next-year PA leaves his
  conditional talent unobserved, not zero. A future absence cannot be inserted
  into origin inputs.

Many old draft records lack school class; the unknown flag is retained. Kurtz's
actual college-junior classification is present. This coverage gap is not a
parser bug and does not authorize new college collection. Three-year minor
stabilization and league-only transport are inherited, not newly certified park
or opponent adjustments.

## Decision and next step

Do not adopt either new talent arm. Retain the implementation as research and
the concrete lesson that skills warrant different trust. This closes one
specification, not empirical shrinkage or minor-league information generally.
Keep existing talent and qualified binary readiness. Next finish the common-
unit public hitting comparison before calling the practical candidate decent.
No protected 2026 outcomes, frozen forecast changes or goal completion.
