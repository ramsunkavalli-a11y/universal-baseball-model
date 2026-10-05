# Repaired evidence is stable but does not improve the hitter model

2026-10-04. The completed comparison removes the extreme old DSL and foreign
production effects and improves some sensible playing-time forecasts. It does
not improve overall future MLB hitting or delivered batting value against the
strongest current model. Keep the current model; do not promote either new
complete model or choose a subgroup blend from these results.

## What was tested

Both fixed candidates retain MLB production, draft/scouting information and MLB
tracking inputs. They replace 91 raw minor rate columns with a coherent translated
event profile weighted by actual exposure, and use normalized foreign exposure.
Only one adds seven translated foreign production contrasts. Their playing-time
heads are identical and recognize prior MLB and foreign professional activity.
The comparison changes representation and routing together, not just one feature.

All 30,506 original forecasts and thirteen previously absent additions remain.
Targets are the following calendar year's actual MLB PA, hitting rate and batting
plus replacement contribution, not full WAR or six years of control. The original
origins are 2016–2018 and 2021–2024. Training is chronological and player separated;
2020 targets are excluded. Historical results are exposed development evidence.
No 2026 outcomes were accessed. [Contract](hitter-evidence-representation-contract.md),
[count correction](hitter-evidence-representation-prefit-correction.md) and
[source review](hitter-evidence-representation-source-review.md) preserve the setup.

## Results against the unchanged current model

| Original cohort metric | Current | Repaired domestic | Repaired overseas |
| --- | ---: | ---: | ---: |
| PA RMSE | 60.4991 | 60.2530 | 60.2530 |
| PA MAE | 20.6124 | 20.4920 | 20.4920 |
| Delivered batting contribution RMSE | 0.43513 | 0.43606 | 0.43606 |
| PA weighted future hitting RMSE | 1.80481 | 1.80850 | 1.80850 |
| Predicted PA total | 1228733 | 1235119 | 1235119 |
| Predicted contribution total | 4155.43 | 4128.50 | 4128.48 |

Actual totals are 1,270,493 PA and 4185.43 batting/replacement wins across these
seven cohorts. Do not interpret them as one MLB season's league totals.
The PA improvement is about 0.4%; it is not a demonstrated player-value gain.
For repaired domestic versus current, paired-player value MSE change is +0.000811,
nominal 95% interval [-0.000633, +0.002205]. PA MAE change is -0.1204, interval
[-0.2429, +0.00295]. Hitting MSE change is +0.01331, interval
[-0.00610, +0.03483]. These are uncertainty ranges for exposed development data,
not independent confirmation or multiplicity-adjusted discovery.

Delivered errors improve in only two of seven origins, 2022 and 2023. The outcome
is not explained away by 2021. Workload-only value RMSE is 0.43532; talent-only
is 0.43611. Those are same-output mechanical diagnostics, not proposed blends.

On 2,627 matched public forecasts, repaired PA RMSE is 137.81 versus current
138.33 and Steamer 135.38. PA MAE is 105.27 versus 106.41 and 92.08: repaired
passes the declared 15% tolerance, but is still about 14.3% worse than Steamer.
Repaired contribution RMSE is 1.02620 versus current 1.02398; converted Steamer
is 1.09011. Public rates and values have snapshot, park and environment limitations.
In the common origin-rate reference, PA-weighted hitting RMSE is 1.73401 versus
current 1.72848, Steamer 1.77459 and ZiPS 1.75336. This does not establish talent
superiority or certify ZiPS's displayed PA as a playing-time forecast.

## Cohort failures remain

For upper-minor never-debuted hitters, hitting RMSE worsens 2.56325 to 2.58627;
predicted PA falls 74239 to 72749 versus 92891 actual. For lower minors it worsens
3.17908 to 3.30340. Their predicted contribution rises 16.18 to 23.29 versus 9.48
actual. Small all-player errors dominated by non-arrivals cannot hide those totals.
These are next-year contribution checks, not conclusions about long-term DSL value.

The 253 original foreign-source origins improve contribution RMSE 0.49309 to
0.46748, but predicted PA overshoots their total: 8563 versus 7776 actual. The
thirteen additions improve predicted PA coverage substantially compared with the
previous failed integration, yet still predict only 742 versus 1625 actual PA.
Their contribution total is 1.57 versus 8.34 actual. Six become MLB participants.
Do not erase the seven non-arrivals or invent current forecasts for the additions.

## What the player review establishes

The [completed player walkthrough](hitter-evidence-representation-player-review.md)
keeps all 38 earlier cases and adds Cruz's largest gain, Bautista's largest harm
and Pearce's ordinary case. Judge's brief-debut forecast is the largest false low;
Acuña's subsequent injury produces the largest false high.

The source-removal probes show genuine repair: removing Yordan's old DSL history
changes the fixed new rate by only -0.000723 wins per 600 PA, not the old +6.01
effect from a separate DSL walk term. Removing Benintendi's old short-season
history changes it +0.00394, not the old -1.26 term. Hoskins's expected PA rises
26 to 365 versus 517 actual; Thames's 2016-origin PA rises 21 to 292 versus 551.
Both have understandable retained professional-work and known-job paths.

But stability is not sufficient learning. The seven foreign production terms
contribute only +0.00657 to Lee's 2024-origin hitting rate, versus +0.29913 from
exposure/missingness controls. For debut Yoshida they contribute +0.00703 versus
+0.40027 from those controls. The two talent arms are consequently almost identical.
This is a weak test of incremental foreign production in this heavily regularized
pooled head, not evidence that NPB/KBO hitting is irrelevant. The same consolidated
head largely fails to identify prospect production and readiness. Yordan, Kurtz,
Kwan and Caminero remain serious misses despite their real source evidence.

Tatis's temporary absence still yields only 16.4% participation; Franco's unresolved
restriction still yields 99.1%. Literal list absence and known employment are
present, but the learner does not distinguish these rare cases adequately.
Source flags, unit tests and large coarse peer counts are not enough.

## Execution and decision

All 140 fitted heads replay. Targets are independently reconstructed from dated
MLB event counts, and the two job forecasts match exactly. Twelve focused tests
pass. Profile intersections remain absent for 1227 conditional forecasts and
below twenty people for 11021; these difficult rows are retained, not deleted.
The original 31-file forecast remains unchanged.

The run needed [documented recovery](hitter-evidence-representation-fit-recovery.md):
an overbroad finite assertion incorrectly included null incumbent comparisons for
an addition. The original runner and seals remain intact; four already fitted
models were loaded, not refitted, and their first recorded hashes were captured
after interruption. No settings or membership changed. Preparation repairs are
also recorded. Score and fit receipts originally marked pending remain preserved;
the final review supplies the completed decision separately.

Do not adopt either complete candidate. Preserve the reviewed source precision
and professional activity construction for future use, without claiming a proven
whole-model gain. Do not launch another coefficient tweak or algorithm sweep.
The next design must preserve the current useful talent routing and explicitly
address how strong production is represented for players without established
MLB history, separately from their likely opportunity. First determine why the
pooled head assigns so little effect to that evidence; use the saved source and
coefficient traces rather than treating this loss as a rejection of the evidence.

The long-range goal stays active. A newly selected practical candidate, team-filtered
research explorer and authorized final 2026 evaluation are still outstanding.
Your authorization remains [freeze first, evaluate second](hitter-2026-final-evaluation-authorization.md).
No model is being frozen merely to get permission to open 2026, and no full-WAR,
club-control or trade-value completion is claimed.
