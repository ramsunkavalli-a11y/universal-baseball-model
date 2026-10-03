# Hitter research handoff and remaining gaps

2026-10-03. The reviewed next-year means are frozen in a separate historical
explorer with team, stage and season filters. Hitting, appearance chance,
conditional PA, expected PA and offense are separate. This finishes the research
handoff, not the active model goal. See the [model card](practical-hitter-model-card.md)
for the construction, benchmarks and boundaries.

## What changed

No forecasts were refitted or upgraded. Every retained PA and hitting output
matches the saved selected candidate; offense uses the reviewed corrected
reference. Displayed inputs use actual source features rather than stale
prediction-table metadata. Missing names no longer break search. Older MLB team
names use existing season-specific captures. The filter distinguishes a requested
year-end roster from the last batting club and does not relabel inactive players
as current employees. Some affiliations remain unknown; historical API requests
are reconstructed evidence, not proof of a contemporary roster snapshot.

The explorer defaults to 2025 and hitting-only sorting, with realized results and
outcome-informed reviews hidden. It can expose all nineteen completed source and
saved-fit reviews. All seven years, Giants upper minors, unknown affiliations,
sorting, pagination, name/ID search, Judge histories and Kurtz outcomes/peers were
checked in the browser. A missing-name search failure was repaired and rechecked.

## Appearance probability walkthrough

The eight cases were specified before the probability audit. They reuse the
completed actual-source, saved-fit and outcome-blind peer reviews, not a new
favorable case selection. All figures below are next-year MLB PA, not career
arrival or an eventual prospect grade.

| Origin player | Any MLB PA | PA if active | Expected PA | Actual PA | Baseball interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| 2016 Judge | 92.59% | 304.04 | 281.50 | 678 | Appearance is recognized; workload and breakout talent are understated. His 410 AAA PA and 19 HR were available, alongside 95 MLB PA with 42 K. |
| 2024 Judge | 99.21% | 534.78 | 530.54 | 679 | Near-certain appearance is sensible; it does not solve workload or another extreme hitting season. Prior MLB HR were 62, 37 and 58. |
| 2024 Kurtz | 1.73% | 115.97 | 2.00 | 489 | Known pick four and college class plus 50 minor PA are not adequately represented. Zero earlier active-MLB peers in the coarse profile warns against false precision. |
| 2023 Langford | 20.18% | 213.56 | 43.10 | 557 | Known pick four, college class and 200 minor PA do not produce sensible immediate readiness. Only two active-MLB training people support the coarse profile. |
| 2017 Soto | 0.26% | 49.01 | 0.13 | 494 | Age 18 and excellent A contact in 96 PA precede an exceptional jump. Six active-MLB training people are weak support; generic low-level peers mostly do not arrive. |
| 2022 Tatis | 12.60% | 275.95 | 34.77 | 635 | Current blank MLB season overwhelms prior star evidence. Availability/return failure is real; a rehab-club label is not an MLB opportunity estimate. |
| 2024 Salas | 2.56% | 281.84 | 7.22 | 0 | Low immediate chance is reasonable for an 18-year-old with 469 A-plus PA and four HR. It is not a career-quality rejection. |
| 2024 McLain | 53.60% | 323.94 | 173.62 | 577 | Blank current season underestimates return workload. Close offense totals are misleading because rate and use errors cancel. Only one training person supports this coarse profile. |

The machine-readable walkthrough preserves each source history, actual input,
saved calculation, profile support and successful/failed comparisons. Kurtz's
peers include Cam Smith and Christian Moore, who played, and Montgomery/Williams,
who did not. They argue for a readiness representation test, not a guarantee
for every draft pick. Judge, Soto and Tatis remain prominent misses rather than
being explained away as acceptable aggregate noise.

## What the probability audit found

Across all forecasts the model expected 4,404.8 appearances versus 4,538 actual.
But the upper-minors total is 727.5 versus 858, while lower minors are 88.6
versus 58. Origin 2021 expected 587.5 versus 686, demonstrating that the COVID
transition cannot be dismissed by a favorable overall total.

The lowest probability band contains 18,811 forecasts, with 58.1 expected
appearances and only 15 actual. Middle bands generally underpredict appearance.
These are fixed descriptive bands with equal-year rates and raw totals, not
calibration trained on the same exposed outcomes. People repeat across years;
individual uncertainty is not identified by a pooled reliability table.

## Disposition and next work

Keep the selected coherent means as a research baseline. No continuous ranges,
defense, running, club control or trade-value distribution is certified by this
handoff. Public PA absolute error still misses the working target and elite
readiness remains materially weak. The goal remains active.

The next bounded study must distinguish *entry readiness* from current hitting
talent. First trace the existing college-entry and prospect-level progression
evidence into actual mature training support. Do not collect more college stats
or patch Kurtz/Langford/Soto individually. If comparable historical support is
insufficient, expose that limitation rather than claim a trained solution.
Any replacement must retain the full evaluation population and review failed
high-pedigree peers as well as fast successes. No protected 2026 outcomes or
deployed forecasts were changed.
