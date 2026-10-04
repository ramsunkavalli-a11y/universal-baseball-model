# Minor tracking precision repair improves behavior but not proven measurement value

2026-10-04. The repair prevents tiny minor samples from overwhelming extensive
MLB history. The adjusted forecast modestly improves errors versus the combined
benchmark, but nearly all of that improvement is also obtained without the
contact measurements. Their incremental benefit remains uncertain, and promising
International League hitters still get questionable downward adjustments. Retain
the precision-aware construction as reviewed research, not a new production
forecast or proof that minor Statcast has been fully integrated.

## Fixed comparison and results

The [contract](hitter-minor-statcast-precision-contract.md) preserved all 30,506
forecasts and current playing time. The existing translated prospect/MLB Statcast
base is not refitted. Two small additive Ridge heads estimate an adjustment:
precision-weighted exposure alone, or exposure plus four measurement families.
All 35 base test forecasts reproduce before adjustments are fitted; twenty new
heads operate only in the same supported 2023/2024 origin cells. Everyone else
retains the combined forecast exactly. No outcomes from protected 2026 enter.

| Future MLB rate population | Combined RMSE | Exposure adjustment RMSE | Exposure and measurements RMSE | Earlier joint head RMSE |
| --- | ---: | ---: | ---: | ---: |
| Eligible participants | 1.85225 | 1.84303 | 1.84259 | 1.89579 |
| Eligible never debuted | 2.48872 | 2.44742 | 2.44506 | 2.41912 |
| Eligible prior MLB | 1.78347 | 1.77826 | 1.77807 | 1.84117 |

The primary RMSE falls .52% versus combined but just .024% versus the exposure
control. Paired MSE difference versus combined is -.03568, nominal 95% player
interval [-.06402, -.00752]. Versus exposure it is -.00160, interval
[-.00673, .00353], so additional measurement information is not established.
The never-debuted rate gain versus combined also has a nominal interval below
zero, but its incremental measurement interval spans zero. No post-result
prospect-only branch is selected.

All-player delivered-contribution RMSE improves .451153 to .450866 versus
combined, but exposure alone gets .450886. Nominal MSE intervals versus combined
and exposure are [-.000464, -.000043] and [-.000065, .000028]. These are exposed
development comparisons, not independent confirmation, adjusted multiple-testing
results or full WAR. Rate means future-season-relative batting wins per 600 PA
among actual participants, weighted by actual PA within equally weighted origins.
Contribution uses the separate common-origin batting/replacement reference at
unchanged expected PA, retaining all non-arrivals.

Both supported origins improve rate errors. Delivered errors improve in 2023
origins but slightly worsen in 2024 (.587526 to .587911). Eligible total bias
improves: actual contribution 518.36, combined 636.69, repaired 610.46. However
the full cohort's existing total shortfall increases: actual 4,264.19, combined
4,155.43, repaired 4,129.20. Public contribution RMSE changes 1.053196 to
1.052083; the comparison with converted Steamer is qualified, not native WAR
superiority. No improvement to PA or its outstanding public MAE gap is claimed.

## What was actually repaired

All 4,255 annual measurement counts and means are reconstructed from the reviewed
ledger. Contact variability relative to between-player variability estimates
prior-equivalent samples, rather than choosing an arbitrary veteran percentage.
Representative priors are roughly 20–75 contacts, varying by metric/league/year;
some references lie outside that illustrative range. Best-half EV uses a qualified
bootstrap approximation. Source-only same-season references exclude held players
and never use future MLB outcomes.

Measurement deviations and exposure are attenuated by their fraction of recent
minor plus MLB information, including the estimated noise prior. The information
guard is a modeling regularizer, not an exact posterior for batting talent or a
claim that minor and MLB contacts are equivalent. Distinct league/lag coefficients
learn their relation to future hitting. Raw angle-SD and unshrunk known-flag
bypasses are absent. Unknown measurements remain unknown; sparse historical
outcome support still triggers fallback despite a calculable source share.

The prior combined model retains its production and pedigree coefficients.
Training residuals use the mature outer-cutoff model's fitted training predictions;
they are not independently cross-fitted. That and the limited two-origin minor
tracking sample restrict generalization. Same-season source centering does not
neutralize park/opponent effects, sensor changes or correlated contacts.

## Player review and remaining baseball problems

The [complete player walkthrough](../reports/model-evidence/hitter-minor-statcast-precision/player-walkthrough.md)
retains all sixteen prior origins and adds Encarnacion-Strand's largest gain and
Thomas's ordinary active case. Caminero is the largest harm, Alvarez the false
high and Perdomo the false low. Every case includes dated production, actual
counts/noise references, information shares, all fitted terms, unchanged playing
time, observed outcomes and four origin-selected peers. No future outcomes
enter the peer distance. Zero-PA players' observed batting rates remain null.
Raw source information shares are labeled as before support routing; they are
not applied forecasts when the relevant league lacks mature training support.

Bichette's six AAA contacts beside 1,453 measured MLB contacts get about .4%
share. His 2023 rate changes +1.449 to +1.4475, rather than old +.122. This gives
up an apparent gain before his poor 2024 season but removes the implausible
mechanism. In the next origin, eighteen minor contacts beside 1,192 MLB contacts
move -.0188 to -.0212, not -1.105. The base still misses his rebound, but tiny
minor readings no longer cause a huge additional miss. His original peers
show varied workloads; neither later result proves the old mechanism sensible.

Caminero's 167 contacts are enough to matter: about 45–49% shares, mean EV
93.27 and best-half 104.72. Yet exposure and negative conditional IL velocity
coefficients lower +.588 to +.397 before his +2.175 next-year rate. This is less
harmful than +.094 but still the largest deterioration. Elly also remains pushed
down slightly despite strong IL contact. Only seventeen refined IL people
support Caminero, two support Elly. This is not physically explained by harder
contact being bad; uncertainty, residual selection and missing conditional
representation remain hypotheses, not established causes.

Encarnacion-Strand's +1.115 to +.848 is the largest contribution gain before a
poor short next season, but most of it comes from exposure, not measurements.
Fixed 445 expected PA versus 123 actual still misses his delivered value badly.
Thomas's near-perfect contribution again involves cancellation: rate -.172
versus -1.123, and seventy expected PA versus 132 actual. Both retain their
real origin-level statistics and unsuccessful as well as successful comparisons.

Langford and Eldridge retain moderate, sample-aware updates with sparse support,
not validated prospect breakthroughs. Crook/Herron have zero observed future
rates; Hicklen has only five PA, so their apparent direction cannot establish
true talent. Kurtz and Caceres remain exact untracked fallbacks; this repair
cannot solve Kurtz's ten-PA forecast or infer eventual DSL value from non-arrival.
Alvarez's workload miss and Perdomo's breakout remain large base uncertainties.

## Disposition and next milestone

The precision and anchoring defect has been materially repaired, but this fixed
measurement head has not demonstrated useful improvement over its matched
exposure control. Do not deploy it, promote the prospect subgroup or reject
minor tracking generally. Retain its representation and evidence; do not keep
tuning the same named cases or choose a new algorithm to conceal the issue.
The already positive MLB Statcast branch remains unchanged research evidence.

The next coherent milestone is to assemble the strongest reviewed branches into
a historical research candidate and explain its strengths and unresolved gaps
in a team-filtered explorer. Show rate, opportunity and delivered batting value
separately, with source/support warnings and player traces. Keep this uncertain
minor update as an explicit comparison, not silently part of the main candidate.
Do not label a batting-only historical explorer full WAR, club-control value or
a promoted 2026 forecast. The overall model goal remains active, particularly
playing-time calibration, long-horizon support and missing value components.

Code, source-noise estimates, support, scores, fitted adjustments, compact
predictions and full reviewed player evidence are saved with hashes under
`reports/model-evidence/hitter-minor-statcast-precision`. Full feature frames
remain local. The first descriptive scoring error was repaired before score
outputs; its receipt is preserved and no source, preflight, fit or contrast changed.
