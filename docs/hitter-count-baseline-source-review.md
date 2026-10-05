# Past-only baseline source walkthrough

2026-10-05, before any future-count learner is fitted. This is a source approval,
not an accuracy claim. The same ten diagnostic cases are retained from the last
completed experiment, including its failures. Baseline units below are batting
wins above the contemporaneous MLB mean per 600 PA, before learned future change.
They are neither WAR nor predictions that these players will receive 600 PA.

## What the baseline actually says

| Player, origin | Past baseline | Observed-mass share after prior | Source judgment |
| --- | ---: | ---: | --- |
| Judge, 2016 | -0.726 | 51.5% | 95 MLB PA and 1,179.8 recency-weighted minor PA; minor histories are not erased by one short MLB stint. Translated strikeouts remain high; the baseline is not already a superstar forecast. |
| Yordan, 2018 | -0.468 | 37.7% | 34.2 weighted DSL PA versus 379 current AA/AAA PA and 312.8 earlier domestic PA. DSL no longer controls the profile, but translated strikeouts/other events still leave the starting point below average. |
| Kurtz, 2024 | +0.238 | 4.0% | 35 A PA with four homers plus 15 AA PA with none. Four homers in a tiny sample cannot establish an MLB superstar. Draft/scouting can still inform the fitted prospect head. |
| Suzuki, 2021 | +3.921 | 52.2% | 1,311.4 normalized weighted NPB PA. This is past local dominance placed on the MLB reference, not a certified MLB equivalency. The future count model must learn the overseas shift; sparse support remains a major risk. |
| Lee, 2024 | +1.840 | 41.3% | 158 MLB PA plus 685.8 weighted KBO PA. The local KBO fingerprint has strong contact and power relative to its league. MLB adaptation is not known merely from that fingerprint. |
| Yoshida, 2024 | +1.597 | 50.0% | 885 weighted MLB PA, 8 AAA PA and 304.8 weighted NPB PA. NPB contributes 12.7% of total mass including the prior, less than MLB's 36.9%. Earlier foreign production remains material, not automatically correct. |
| Maitan, 2017 | -1.132 | 12.8% | 176 rookie PA, 49 strikeouts and two homers. A highly regarded young prospect can have a weak conditional next-year MLB baseline without that being a lifetime-failure prediction. |
| Perdomo, 2024 | -0.265 | 48.1% | 1,084 weighted MLB PA and 27 minor PA. Older minor evidence is negligible; modest past power does not itself reveal his later breakout. |
| Tatis, 2021 | +2.086 | 44.9% | 974.8 weighted MLB PA versus 4.8 minor PA. Positive hitting ability is sensible. A later absence cannot be coded as zero hitting talent; opportunity stays fixed in this experiment. |
| Wilkerson, 2018 | -1.113 | 40.2% | 49 MLB PA and 757.4 weighted minor PA across several levels. A below-average starting point is plausible; future delivered-value agreement can still hide errors in hitting and workload. |

The foreign starting points are intentionally provisional, and much higher than
the previously regressed foreign future inputs. That difference demonstrates the
temporal distinction rather than an accuracy improvement. League adaptation is
learned only from mature training targets; no future forecast is treated as an
observed foreign season. The old foreign future slope/intercept is not read.

All 2,685 foreign contribution instances across five matrices reconstruct their
own probabilities from source counts and their local past reference. A separate
source-row reconstruction verified 4,675 cached seasonal foreign references
with own and outer folds excluded. Its receipt is
`reports/generated/hitter-count-baseline/reference-review.json`, SHA256
`eb1e7cc2acf8ba337019198acd11ee93f515385ad12853454a50e480a96343a2`.
Unknown identities remain in the league reference as explicitly inherited source
coverage, not claimed perfectly player-excluded identities. Sparse mover and
future learner support must be shown in the final walks.

## Meaning, precision and chronology checks

Each domestic source is a same-season graph equivalency; each overseas source
is a same-season local relative fingerprint, followed by a learned context
correction. Both describe the past before pooling. Raw counts are mutually
exclusive and use observed denominators. All matrices stop origin 2024 and target
2025. Every test person's outer fold is excluded from source graphs and raw
league reference; training rows also have their own fold excluded. Complete
future environments appear only in mature training offsets and evaluation labels,
not prediction features or test offsets. No learned scaler has hidden membership.

The fixed 1,200-PA prior limits a 50-PA source to 4% of the starting probability
pool. Adding MLB evidence lowers the mass fraction of older sources. This is a
declared regularization assumption, not proof of correct cross-level precision.
The graph remains selected-mover and park-pooled: Yordan/Judge's translated
starting points cannot be called neutral intrinsic talent. This test does not
resolve that limitation or prove the inherited prior is optimal.

All 105 active-head preflights, full/active profile counts, feature ranges and
raw target-count pairings exist before fit. Unit tests independently check
the likelihood gradient, event-coordinate permutation symmetry, normalization,
prior dilution and that corrupting the archived foreign future probability has
no effect. Approve the one contracted historical fit, subject to convergence,
full-cohort scores and post-fit player review. No deployment approval follows.
