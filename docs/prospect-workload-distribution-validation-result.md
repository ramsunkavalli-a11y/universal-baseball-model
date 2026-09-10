# Prospect workload distribution validation result

Status: hitter conditional workload coverage passes; pitcher coverage fails.

The frozen check trained on 2015-2017 MLB debut cohorts and evaluated once on
2018-2019 debut cohorts. It includes 198 hitters and 166 pitchers.

| Player type | Later players | 50% range coverage | 95% Wilson interval | 80% range coverage | 95% Wilson interval | Result |
|---|---:|---:|---:|---:|---:|---|
| Hitter | 198 | 46.0% | 39.2%-52.9% | 74.7% | 68.3%-80.3% | descriptive targets retained |
| Pitcher | 166 | 35.5% | 28.7%-43.1% | 66.3% | 58.8%-73.0% | under-covered |

Hitter coverage is somewhat low, but both declared targets remain inside their 95%
sampling intervals. Pitcher coverage is too narrow at both levels. Established
pitchers cover only 64.5% in the nominal 80% range; the small meaningful-only group
covers 31.3%. Both role-specific and pooled pitcher sources under-cover.

## Decision

- Retain the hitter workload distribution as a labeled empirical reference range.
- Treat the current pitcher workload range as descriptive and too narrow, never as an
  80% confidence interval.
- Do not tune a pitcher widening factor on the already opened 2018-2019 evaluation.
  A replacement method must use resampling or earlier internal development and wait
  for a genuinely later complete six-year cohort for confirmation.
- Do not promote the component-plus-workload research range. It cannot repair a
  miscalibrated workload layer merely by adding unrelated performance noise.

This was a conditional submodel test: every evaluated player had already debuted, and
career tier and role were known for grouping. Arrival probability, WAR skill, and the
end-to-end prospect distribution remain unvalidated.

Machine-readable evidence:
`docs/prospect-workload-distribution-validation-result.json`.
Frozen protocol: `docs/prospect-workload-distribution-validation-plan.md`.
