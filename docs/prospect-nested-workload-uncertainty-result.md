# Prospect nested workload uncertainty result

Status: accepted for labeled private-preview display; not a full confidence interval.

The empirical mixture covers all 6,719 modeled pre-MLB player paths. Its weighted
mean reproduces every existing point estimate; the largest absolute difference is
`3.6e-15` WAR. No player value or grade changed.

The distribution makes non-arrival and career-role risk visible. Examples:

| Player | Mean WAR | P10 | P50 | P90 | Workload-only P(18+ WAR) |
|---|---:|---:|---:|---:|---:|
| Caden Bodine | 10.06 | 0.11 | 10.46 | 17.88 | 9.03% |
| Rainiel Rodriguez | 9.20 | 0.01 | 9.40 | 18.31 | 10.97% |
| Josuar Gonzalez | 1.83 | 0.00 | 0.00 | 9.17 | 0.51% |
| Tyson Hardin | 3.04 | 0.00 | 2.66 | 7.07 | 0.00% |
| Anthony Eyanson | 2.60 | 0.01 | 2.01 | 6.31 | 0.00% |

Josuar's zero median is not a zero valuation: it reflects that most weighted career
paths contain no MLB arrival, while the successful tail produces meaningful value.
Likewise, zero 18+ WAR probability for the displayed pitchers does not mean no ace
upside; this first layer holds skill rate fixed and varies workload only.

The private explorer may show P10/P50/P90 and the workload-only 18+ probability with
that limitation. Skill-rate, aging, injury, defense, and position-retention uncertainty
remain separate Phase 2 work.

Machine-readable evidence: `docs/prospect-nested-workload-uncertainty-result.json`.
Frozen protocol: `docs/prospect-nested-workload-uncertainty-plan.md`.
