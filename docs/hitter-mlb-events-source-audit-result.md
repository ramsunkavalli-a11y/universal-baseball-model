# The removed MLB event inputs reconstruct correctly

2026-10-05. This source-only audit and all seventeen source walkthroughs are
complete. The seven original pooled MLB event rates match independently aggregated
dated statistics in every saved matrix. They retain separate MLB strikeout,
walk, HBP, power and balls-in-play information that is compressed in the common
past-production profile. This does not prove that restoring them improves forecasts.
No model was fitted and no prediction, PA, explorer or final 2026 evaluation changed.

The [contract](hitter-mlb-events-source-audit-contract.md) was saved before the
audit. Actual raw MLB stints aggregate to exactly the same 19,623 annual player
rows as the existing counts. Coverage is the existing certified 2008–2025 MLB
inventory; predictor origins stop at 2024. All 2,215,990 input comparisons
(63,314 rows × seven fields × five matrices) pass at absolute tolerance 1e-12.
Each matrix agrees exactly on these source fields. All seventeen fixed cases
pass mutations of post-origin counts; future records never enter their predictors.
Four focused regression tests check denominators, absence, unknown coverage,
recency, one prior and invalid counts.

## What the seven inputs mean

Each field pools three completed seasons with weights 1/.8/.6, then adds one
100-opportunity prior: (weighted events + 100 × prior rate)/(weighted denominator
+ 100). The model coordinate is (that rate − prior rate)/.1, using the existing
fixed units. The table shows exactly which denominator and prior are used.

| Field | Numerator | Denominator | Fixed prior |
| --- | --- | --- | ---: |
| K | Strikeouts | PA | 23% |
| BB | Walks excluding intentional walks | PA | 8% |
| HBP | Hit by pitch | PA | 1% |
| HR | Home runs | PA | 3% |
| BABIP | Hits excluding HR | AB − K − HR + sacrifice flies | 30% |
| 2B | Doubles | PA | 5% |
| 3B | Triples | PA | 0.5% |

BABIP is not divided by PA, nor are double/triple inputs shares of hits. Walks
are not silently changed to all walks. These overlapping rates do not sum to
one and are not an eight-category outcome distribution. Rates are raw MLB
production, not park/opponent-neutral talent or future event probabilities.
Covered absence produces the prior and a zero centered coordinate, distinguished
by existing workload/presence flags. Unknown season coverage raises an error;
absence is never used as an observed average-talent label.

The 100-opportunity prior is the old field definition, not a newly justified
reliability estimate. The four restored batting summaries use a 1200-PA prior;
they measure a different quantity under different shrinkage. Restoring these
seven fields therefore restores both separate MLB component information and
its original reliability convention. A future comparison cannot claim to isolate
information independently of that convention or establish an optimal prior.
BABIP also has fewer relevant observations than PA-based fields. No further
prior or algorithm search is authorized by this audit.

## All seventeen fixed source walkthroughs

The cases are the exact seventeen reviewed in the completed four-summary test.
Their IDs, dates, raw annual source counts, transformed coordinates and unchanged
forecasts are saved in the machine artifact. The existing
[source to forecast player walks](hitter-mlb-detail-restoration-player-review.md)
retain their actual routes, folds, baselines, coefficients, future outcomes and
successful/failed origin-selected peers. Here only the newly audited source
fields are reconstructed; no downstream effect is invented for a fit not run.

Rates below are percentages after the original prior; exposure is recency-weighted
actual observations, not annualized workload. BIP means the BABIP denominator.

| Player and origin | MLB PA | BIP | K | BB | HBP | HR | BABIP | 2B | 3B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Judge 2016 | 95 | 39 | 33.333 | 8.718 | 1.026 | 3.590 | 29.496 | 3.590 | 0.256 |
| Thames 2017 | 551 | 275 | 28.571 | 11.982 | 1.229 | 5.223 | 30.667 | 4.762 | 0.691 |
| Maitan 2017 | 0 | 0 | 23.000 | 8.000 | 1.000 | 3.000 | 30.000 | 5.000 | 0.500 |
| Davis 2018 | 1541.6 | 839.2 | 27.632 | 8.821 | 1.377 | 6.737 | 27.534 | 4.252 | 0.213 |
| Wilkerson 2018 | 49 | 30 | 26.174 | 7.383 | 0.671 | 2.013 | 29.231 | 5.369 | 0.336 |
| France 2018 | 0 | 0 | 23.000 | 8.000 | 1.000 | 3.000 | 30.000 | 5.000 | 0.500 |
| Alvarez 2018 | 0 | 0 | 23.000 | 8.000 | 1.000 | 3.000 | 30.000 | 5.000 | 0.500 |
| Nola 2021 | 501.4 | 351.2 | 17.792 | 8.114 | 1.796 | 2.760 | 30.363 | 5.221 | 0.316 |
| Tatis 2021 | 974.8 | 527.6 | 27.056 | 9.509 | 0.930 | 6.680 | 33.365 | 4.894 | 0.530 |
| Suzuki 2022 | 446 | 276 | 24.359 | 8.608 | 0.916 | 3.114 | 31.915 | 4.945 | 0.458 |
| Judge 2023 | 1394.6 | 688.2 | 25.947 | 13.676 | 0.508 | 7.561 | 32.276 | 3.867 | 0.033 |
| Misner 2024 | 15 | 5 | 28.696 | 6.957 | 0.870 | 2.609 | 29.524 | 4.348 | 0.435 |
| Perdomo 2024 | 1084 | 731.2 | 17.872 | 10.507 | 0.997 | 1.166 | 29.066 | 4.054 | 0.583 |
| Kurtz 2024 | 0 | 0 | 23.000 | 8.000 | 1.000 | 3.000 | 30.000 | 5.000 | 0.500 |
| Yoshida 2024 | 885 | 672.4 | 14.193 | 6.315 | 2.091 | 2.538 | 30.813 | 5.320 | 0.294 |
| Lee 2024 | 158 | 132 | 13.953 | 6.977 | 0.775 | 1.938 | 28.448 | 3.488 | 0.194 |
| Suzuki 2021 addition | 0 | 0 | 23.000 | 8.000 | 1.000 | 3.000 | 30.000 | 5.000 | 0.500 |

Judge 2016's 42 K in 95 PA become (42+23)/(95+100)=33.333%, a centered model
coordinate +1.03333. Actual observations supply 48.7% of PA-based component
evidence, compared with only 7.3% in his annual batting-quality summary. His
39 BIP opportunities supply 28.1% of BABIP evidence. The poor debut therefore
has a materially different influence in these fields. It is valid data, not
permission to overweight it or erase it after his breakout. Judge 2023 has
93.3% actual share in PA components and high HR/walk rates; this can distinguish
him from Davis's similarly positive value history but higher strikeout and lower
walk rates. Whether the learner uses those differences well needs a future test.

Wilkerson's 49 PA supply 32.9% component evidence; Misner's fifteen supply 13.0%,
while his five BIP opportunities supply only 4.8% BABIP evidence. These are the
opposite-risk cases for restoring less-shrunk components. The four-summary test
already showed that improved delivered numbers can hide inaccurate rate/PA
predictions, so neither may be accepted from final value alone.

Maitan, France, Alvarez, Kurtz and Suzuki's pre-entry addition have no MLB
counts. All seven coordinates are exactly zero. Their minor or foreign production,
age and pedigree remain elsewhere in the existing source profile; no MLB results
are fabricated. A fitted restoration could still move them by changing other
coefficients, which would require an actual trace, not an assertion that absent
MLB fields caused their movement. Their differing future outcomes remain in the
prior walks and do not change this source audit's eligibility.

Nola's 501.4 weighted PA are 194 in 2021 + .8×184 actual PA in shortened 2020
+ .6×267 in 2019. The BABIP denominator is separately 351.2; no 2020 exposure
is inflated. The canceled 2020 minor season supplies no imaginary observations.
Fernando Tatis Jr.'s high HR/BABIP component history does not establish next-year availability;
his next-year absence in the prior walk still has no observed talent label.

Perdomo's pooled low K and HR reflect his distinct contact profile, unlike simply
retaining a negative aggregate batting summary. These pooled fields do not
separately encode the improving year-by-year trend already examined. Lee's
13.953% K and Yoshida's 14.193% K distinguish their MLB contact evidence from
Suzuki's 24.359% K. Thames's strong MLB HR/walk rates remain alongside his
older KBO history. None of these raw component summaries calibrates NPB/KBO to
MLB, resolves sparse foreign adaptation support or corrects the raw park environment.

## Decision and next task

The source gate passes with the above qualifications. There is no predictive
success claim because no model was fitted. Keep the incumbent and all forecasts.
The justified next task is one prospectively specified seven-input restoration
on the completed four-summary direct-rate model, retaining its four summaries,
same baseline, fixed units, alpha, weights, population, routes, PA and anchors.
Do not reinterpret the fixed 100-opportunity prior as newly validated or tune it
to these cases. Preserve every seventeen-case diagnostic, add any new mechanical
extremes and trace the full source/model/output change before a disposition.
That fitted comparison is not yet authorized by a completed fit contract here.

Machine source evidence is `reports/model-evidence/hitter-mlb-events-source-audit/report.json`.
Private receipts and full raw source walks are under
`reports/generated/hitter-mlb-events-source-audit`. The long hitter goal stays active.
