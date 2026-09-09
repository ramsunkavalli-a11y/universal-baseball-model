# Prospect arrival nested robustness result

**Run date:** 2026-09-09  
**Status:** retrospective process audit; no model promoted

The first demographic result was rerun under the binding
[model-search policy](model-search-validation-policy.md). The audit tested five stable
feature groups at four regression strengths. Selection used only the 2021 evaluation
origin, whose two-year outcome window was complete before the 2023 outer origin. The
2022 result was embargoed because its two-year window was not complete. All failures
and non-arrivals remained in the samples.

StatsAPI country labels were normalized only for modeling; the source value remains
unchanged. This merged 313 of 24,328 records carrying equivalent labels such as
`VEN`/`Venezuela`, `DOM`/`Dominican Republic`, and `Republic of Korea`/`South Korea`.

## Outer 2023 result

Earlier-origin selection chose stable demographic interactions with `C=1` for all
four questions. That does not mean all four survived the outer test.

| Population / target | Core log loss | Candidate | Core Brier | Candidate | Decision |
|---|---:|---:|---:|---:|---|
| Hitters / arrival | .16663 | .16631 | .04651 | .04807 | Reject: Brier materially worse |
| Hitters / meaningful role | .07886 | .07404 | .01804 | .01763 | Promising development result |
| Pitchers / arrival | .17208 | .16837 | .04861 | .04789 | Promising development result |
| Pitchers / meaningful role | .07075 | .06985 | .01780 | .01763 | Inconclusive |

Paired bootstrap results reinforce those decisions:

- hitter arrival candidate Brier was worse in 99.5% of resamples;
- hitter meaningful-role log loss improved in 99.95%, while its Brier interval still
  crossed zero;
- pitcher arrival improved log loss in 99.95% and Brier in 97.8% of resamples;
- pitcher meaningful-role intervals crossed zero for both scores.

Pitcher-arrival calibration also moved in the right direction: intercept from .500 to
.266 and slope from 1.285 to 1.222, where zero and one are the respective ideals.

## Subgroup cautions

The hitter-arrival failure was not subtle: Brier worsened among supported USA, AA,
AAA, age 23–25, age 26–30, and 300+ workload groups. It must not be promoted.

Pitcher arrival improved in aggregate, but the Dominican Republic and Venezuela
groups improved log loss while Brier worsened slightly. Age 26–30 also worsened on
both scores. Those tensions require either a simpler pooled pathway effect or another
later test; country coefficients must not be read as talent.

The 2023 origin had already been inspected during feature-family development. This
nested rerun validates the process and rejects one apparent winner, but it is not fresh
confirmation. Production remains on core features and current player values are
unchanged. The machine-readable result is
[`prospect-arrival-nested-robustness-result.json`](prospect-arrival-nested-robustness-result.json).
