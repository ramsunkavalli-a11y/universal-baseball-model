# Prospect workload distribution validation result

Status: descriptive cohort-stability result; original chronology claim retracted.

Subsequent status: superseded for calibration decisions by the valid as-of replay in
`docs/prospect-workload-asof-validation-result.md`. Its pitcher range passes there.

The full six-year training paths extend beyond the later cohort's debut date. This
means the result cannot confirm a deployable forecast as of that date. It remains a
useful early-versus-late distribution comparison only.

The frozen check summarized 2015-2017 MLB debut cohorts and compared them once with
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

- Retain the hitter workload distribution only as a labeled empirical reference range;
  do not call it historically confirmed.
- Do not use this timing-defective comparison to label the pitcher range too narrow.
  Use the subsequent as-of replay for calibration evidence.
- Do not tune a pitcher widening factor on the already opened 2018-2019 evaluation.
  A replacement method must use resampling or earlier internal development and wait
  for a genuinely later complete six-year cohort for confirmation.
- Do not promote the component-plus-workload research range. It cannot repair a
  miscalibrated workload layer merely by adding unrelated performance noise.

This was a conditional cohort-stability test: every evaluated player had already debuted, and
career tier and role were known for grouping. Arrival probability, WAR skill, and the
end-to-end prospect distribution remain unvalidated.

Machine-readable evidence:
`docs/prospect-workload-distribution-validation-result.json`.
Frozen protocol: `docs/prospect-workload-distribution-validation-plan.md`.
