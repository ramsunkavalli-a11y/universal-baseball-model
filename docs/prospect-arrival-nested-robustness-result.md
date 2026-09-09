# Prospect arrival nested robustness result

**Run date:** 2026-09-09  
**Status:** retrospective process audit; no model promoted

The first demographic result was rerun under the binding
[model-search policy](model-search-validation-policy.md). The completed audit tested
144 bounded combinations: nine stable feature groups, four logistic regularization
strengths, and four production-rate regression exposures. The added baseball groups
cover age/level development and role/production interactions using inputs available
at every affiliated level. Selection used only the 2021 evaluation origin, whose
two-year outcome window was complete before the 2023 outer origin. The 2022 result was
embargoed because its two-year window was not complete. All failures and non-arrivals
remained in the samples.

StatsAPI country labels were normalized only for modeling; the source value remains
unchanged. This merged 313 of 24,328 records carrying equivalent labels such as
`VEN`/`Venezuela`, `DOM`/`Dominican Republic`, and `Republic of Korea`/`South Korea`.

## Outer 2023 result

Earlier-origin selection chose `C=1` and no added production-rate regression for all
four questions. It chose demographic interactions for hitter arrival, baseball-only
development/role interactions for hitter meaningful role and pitcher arrival, and
combined baseball/demographic interactions for pitcher meaningful role. The wider
search therefore removes birth country from two of the earlier apparent leads.

| Population / target | Core log loss | Candidate | Core Brier | Candidate | Decision |
|---|---:|---:|---:|---:|---|
| Hitters / arrival | .16663 | .16631 | .04651 | .04807 | Reject: Brier materially worse |
| Hitters / meaningful role | .07886 | .07536 | .01804 | .01796 | Mixed: log-loss gain, Brier uncertain |
| Pitchers / arrival | .17208 | .16905 | .04861 | .04796 | Mixed: aggregate gains uncertain |
| Pitchers / meaningful role | .07075 | .06901 | .01780 | .01754 | Mixed: both intervals cross zero |

Paired bootstrap results reinforce those decisions:

- hitter arrival candidate Brier was worse in 99.5% of resamples;
- hitter meaningful-role log loss improved in every resample, while its Brier interval
  crossed zero;
- pitcher-arrival log-loss and Brier intervals both crossed zero;
- pitcher meaningful-role intervals crossed zero for both scores.

Pitcher-arrival calibration moved in the right direction: intercept from .500 to .201
and slope from 1.285 to 1.182, where zero and one are the respective ideals. Pitcher
meaningful-role slope improved from 1.148 to 1.032, but that does not override mixed
proper-score uncertainty.

## Subgroup cautions

The hitter-arrival failure was not subtle: Brier worsened among supported USA, AA,
AAA, age 23–25, age 26–30, and 300+ workload groups. It must not be promoted.

Hitter meaningful role worsened on both scores for the supported age 20–22 group, and
its Brier score worsened for supported AA and switch-hitter groups. Pitcher arrival
worsened on both scores for age 26–30 and worsened Brier in A-or-below, low-workload,
and left-handed groups. Pitcher meaningful role also harmed age 26–30. These are not
universal wins.

None of the production-rate regression exposures was selected from earlier outcomes.
That is evidence against forcing an arbitrary extra shrinkage constant into this
specific arrival model, not proof that raw sparse rates are generally reliable. The
logistic model already contains workload and ridge regression; direct skill models
still require component-specific evidence regression.

The 2023 origin had already been inspected during feature-family development. This
nested rerun validates the process and rejects one apparent winner, but it is not fresh
confirmation. Because the selected families changed when legitimate baseball features
were added, all four remain research-only. Production remains on core features and
current player values are unchanged. The machine-readable result is
[`prospect-arrival-nested-robustness-result.json`](prospect-arrival-nested-robustness-result.json).
