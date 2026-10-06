# Prospect arrival diagnosis: two different misses, not one prospect multiplier

2026-10-05. Completed review under the
[sealed diagnosis contract](hitter-arrival-cohort-diagnosis-contract.md).
No model was refitted, no forecast improved at this checkpoint, and no 2026
outcome was opened. The change is to our diagnosis and support warnings.

## What the forecasts actually missed

Here, **origin 2021 means a forecast made after 2021 for the 2022 MLB season**.
An arrival is any MLB PA next year, not becoming a regular, eventual career
success or six years of value. Upper minors means current affiliated AA/AAA PA;
Mexico is not treated as affiliated AAA. All non-arrivals remain in evaluation.

| Origin → target | Upper-minor players | Expected / actual arrivals | Expected / actual MLB PA |
| --- | ---: | ---: | ---: |
| 2021 → 2022 | 847 | 68.9 / 142 | 9,197 / 17,416 |
| 2022 → 2023 | 821 | 101.6 / 96 | 12,897 / 12,896 |
| 2023 → 2024 | 825 | 109.2 / 102 | 14,263 / 11,275 |

The 2021 shortage is broad, not just Kwan, Witt and Rodríguez. Among 414 players
with at least 200 current AA/AAA PA, expected arrivals were 54.5 versus 121.
Among players without a positive freshest scouting score, they were 53.2 versus
118. Among those without a current 40-man listing, 35.2 versus 92. These groups
overlap: their shortages must not be added. A nonpositive score means no positive
score in this source, not proof that scouts considered the player untalented.

The earlier group-level conclusion that conditional workload was approximately
right needs qualification. Across all 2021 upper-minor players, the model's
probability-weighted conditional workload was 133 PA versus 123 among actual
arrivals. That average hides an important failure:

| 2021 forecast arrival chance | Players | Expected / actual arrivals | Expected / actual MLB PA | Model group PA if active / observed PA among arrivals |
| --- | ---: | ---: | ---: | ---: |
| 1–10% | 494 | 17.8 / 55 | 1,479 / 4,057 | 83 / 74 |
| 10–30% | 67 | 9.8 / 24 | 1,072 / 1,872 | 110 / 78 |
| 30–70% | 63 | 31.3 / 51 | 4,471 / 7,769 | 143 / 152 |
| At least 70% | 11 | 8.9 / 10 | 2,092 / 3,633 | 235 / 363 |

The remaining 212 players below 1% had 1.2 expected versus two actual arrivals
and 84 expected versus 85 actual PA. So the very lowest scores were not where
this group's shortage arose. Most missed arrivals were in the middle bands.
For likely arrivals, however, workload was too low. A correct arrival count
would not fix Kwan's or Witt's forecast.

For 2022, almost exactly correct total PA concealed offsetting errors: excess
expected arrivals contributed about +749 PA, lower group conditional workload
about −749. For 2023, both terms contributed to overprediction. These are exact
signed arithmetic decompositions, not causal estimates. An arrival-probability
change also changes which conditional workload forecasts receive weight.
No uncertainty interval or independent validation is claimed for these
descriptive, overlapping groups selected from already exposed historical data.

## Training checks: what is new, and what was already known

All 35 actual chronological/player-held-out training cells were checked for both
opportunity heads. Target 2020 is excluded: the canceled minor-league season
was **not** being trained as a year in which every prospect failed. The repaired
5,133-row origin-2020 source cohort, predicting 2021, remains available to
training. Dates and whole-player separation passed.

For a 2021-origin forecast, cancellation one year back and the reorganized-era
flag were constant zero in training, but one at prediction. Neither feature
appears in a participation-tree split in any of its five folds. A feature being
listed does not mean the model learned what to do with this new context.
Some later folds do split on reorganization; it is incorrect to claim this
feature is unused everywhere, or that its split count explains the later
overshoot. Split usage is not causal importance.

The new support artifact counts distinct people in each actual training fold,
first by readiness profile and then by readiness **plus the cancellation
pattern**. All never-debut 2021/2022 queries lack this exact calendar-context
match. Kwan, for example, has 252 generic participation and 184 generic
conditional-workload training peers, but zero with the same cancellation
pattern in either head. This is an extrapolation warning, not proof that useful
age, performance or level relationships cannot transfer. These coarse profiles
also do not establish support for every individual feature interaction.
An under-20 warning is a reporting convention, not a validated cutoff for
forecast acceptability. No difficult forecasts are dropped.

This is **not a newly discovered reason to rerun the COVID tests**. The completed
[available-season-history comparison](hitter-available-season-history-result.md)
already skipped canceled 2020 when selecting affiliated minor-league history,
while retaining calendar age, draft dates and MLB/international clocks. It
improved arrival Brier by 1.7%, log loss by 2.3% and PA RMSE by 0.63%; delivered
batting-value improvement was tiny and uncertain, and PA absolute error worsened.
Its 2021 shortage narrowed but did not disappear, while later overshoots and
lower-minor harms remained. Keep it as qualified arrival research, not a proven
whole-model replacement. The current working 293-input model is not that
251-input comparison: their populations and outputs must not be interchanged.
The [earlier repair summary](2021-prospect-repair-summary.md) records other
already tested cancellation, source-outage and schedule approaches.

## Actual players, including cases a boost would hurt

Each row below was traced through its actual input frame and both saved models,
not reconstructed from a model description. All 24 head predictions replayed
within 1e-10. The full 293 inputs, three-year source statistics, head provenance,
support counts and three outcome-blind peers per player are saved in
[player-walks.json](../reports/model-evidence/hitter-arrival-cohort-diagnosis/player-walks.json).
The table shows current upper-minor PA and HR/K/BB totals; lower-level evidence
is noted where needed. These are source observations, not neutralized talent.

| Player, origin | Current evidence | Arrival chance | PA if active | Expected → actual MLB PA next year | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| Austin Meadows, 2016 | AA/AAA 335 PA; 12/66/31 | 81% | 338 | 273 → 0 | Largest upper-minor false high. Strong upper evidence does not guarantee a next-year job. The cause of non-arrival is not established here. |
| Bryan Reynolds, 2018 | AA 383 PA; 7/73/43 | 18% | 58 | 10 → 546 | Severe arrival and workload miss before COVID. This is not solely a canceled-season problem. |
| Jhonny Pereda, 2021 | AA/AAA 237 PA; 0/27/31 | 5% | 69 | 3 → 0 | Excellent contact/walk balance alone did not produce next-year MLB work. |
| Donny Sands, 2021 | AA/AAA 380 PA; 18/57/32 | 80% | 90 | 72 → 4 | Arrived, but barely played. A regular-workload floor would worsen this case. |
| Jeremy Peña, 2021 | AAA 133 PA; 10/35/6, plus rookie 27 PA | 37% | 156 | 57 → 558 | Both heads were too low despite a positive 40-man listing. Small current workload is not by itself a health diagnosis. |
| Julio Rodríguez, 2021 | AA 206 PA; 7/37/29; A+ 134 PA | 85% | 304 | 257 → 560 | Already recognized as likely to arrive. Workload and hitting-rate errors still reduced delivered value. |
| Bobby Witt Jr., 2021 | AA/AAA 564 PA; 33/131/51 | 72% | 351 | 254 → 632 | Strong evidence and positive rank, without a current 40-man listing. That listing is not the same thing as readiness or a blocked MLB job. |
| Steven Kwan, 2021 | AA/AAA 341 PA; 12/31/36 | 72% | 158 | 114 → 638 | The model had his contact evidence and expected an arrival. The large miss cannot be explained just by missing his debut chance. |
| Brendan Donovan, 2021 | AA/AAA 350 PA; 10/62/40; A+ 109 PA | 56% | 114 | 64 → 468 | Arrival, workload and hitting-rate misses; not merely absent pedigree. |
| Diego Cartaya, 2022 | A/A+ 445 PA; 22/119/63, no AA/AAA | 58% | 201 | 117 → 0 | Counterexample: a protected, ranked lower-minor player was already forecast to arrive too quickly. Next-year zero does not establish career failure. |
| Wyatt Langford, 2023 | AA/AAA 80 PA; 4/13/17; A+ 106 PA | 62% | 368 | 227 → 557 | A short debut season can hide a ready advanced draftee. His broad calendar-matched profile had only five distinct conditional-head training people. |
| Nick Kurtz, 2024 | AA 15 PA; 0/3/2; A 35 PA, four HR | 6% | 162 | 10 → 489 | Thin professional exposure with strong pedigree was seriously underrated, outside the immediate COVID cohort. Broad calendar-matched conditional support was eight people. |

Peer outcomes prevent a retrospective rule that every impressive contact
prospect should get 500 PA. Kwan's peers included Sands (72 predicted, four
actual), Diego Castillo (66, 283) and Donovan (64, 468). Sands's peers included
Nick Allen (64, 326), Brett Sullivan (56, zero) and Juan Yepez (73, 274).
Peña's peers included René Pinto (38, 83), Travis Swaggerty (43, nine) and
Yusniel Díaz (33, one). Kurtz's short-sample peers included Cam Smith (12, 493),
Ryan Nicholson (one, zero) and Christian Moore (34, 184). Similar measured
evidence can lead to very different opportunities. The peer rule uses origin,
level category, listing, age, PA, K/BB/HR and available draft/rank inputs, not
outcomes; it does not perfectly match position, health or complete scouting.
The fixed names and largest misses are diagnostic examples, not an unbiased
new test set. The review does not infer why a particular player's opportunity
changed from results alone.

## Decision and the next gate

This diagnosis is complete; the hitter model is not. Append explicit
calendar-context support warnings and retire the claim that a broadly similar
training profile certifies the canceled-season interaction. Preserve every
forecast and earlier sealed result. No probability multiplier, regular-PA floor,
zeroed era flags, narrower favorable routing or selected winner is justified by
this review. No explorer promotion follows from a reporting repair.

The remaining opportunity question is specific: can cutoff-known evidence
distinguish a likely regular from a cameo, **without** forcing Sands into a
regular role or Cartaya into MLB? The existing separate entrant-workload,
pedigree/history, model-flexibility and calendar studies must be inventoried
before any new fit. Only an untested mechanism or demonstrated new source defect
may reopen that question. In particular, another generic deeper-tree or COVID
variant is not a next step. A proposed experiment must show what information
or target changes, retain the common full-history backbone and all non-arrivals,
evaluate both heads and delivered value across origins, and walk these harms as
well as the attractive misses. No such new experiment is approved by this
diagnosis alone. Tatis's unconditional availability and hitting-rate misses
remain separate open issues; do not pretend an arrival repair fixes them.
