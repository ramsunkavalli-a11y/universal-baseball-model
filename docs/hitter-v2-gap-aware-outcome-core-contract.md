# Hitter v2 gap-aware outcome-core contract

Date: 2026-08-26
Status: frozen before new source materialization, fitting, or scoring

## Decision

Return to the batter model now. The next candidate is not another broad context
model. It is the existing interpretable terminal-outcome C0 backbone supplied
with certified 2019-2020 history while treating the missing 2020 MiLB season as
an observation gap.

`G0_GAP_AWARE_HISTORICAL_C0` adds no new predictor and fits no new contextual
effect. It reuses the frozen C0 component half-lives and prior strengths. Its
only change is more chronology-safe terminal-outcome evidence.

## Why this candidate comes first

C0 already beat Marcel on future wOBA and batting-runs RMSE throughout the
disclosed folds, but its 2022 proper scores were weak when only one prior season
was available. Historical outcome evidence addresses that specific information
deficit without using contact direction, age, or opponent context to reconstruct
known HR and extra-base-hit results.

The candidate will use accepted 2019 MiLB outcomes plus separately certified
2019 and 2020 MLB outcomes. No 2020 MiLB row may be created or imputed. A
2019-to-2021 reappearance contributes ordinary older recency evidence but is
never treated as a one-year development or translation pair.

## Later refinements

Only a passing outcome core may advance. Later, separately preregistered
residuals may test:

1. prior opponent quality, pitcher hand, and pitcher age relative to level;
2. pulled/opposite-field air and ground contact against narrow HR, XBH, and
   non-HR-reach residuals;
3. lagged, team/level-centered lineup position as a small sparse-player prior;
4. height and age-relative-to-level as a low-weight physical similarity prior;
5. capability-aware tracking with exact PBP fallback.

Games and PA continuity remain opportunity/durability inputs, not batting-rate
skill. Country of origin is excluded as a direct talent predictor. Missing
optional evidence always returns the exact outcome-core forecast.

## Evaluation and stop

G0 retains the existing V2022-V2024 disclosed folds, identical cohorts, proper
scores, future wOBA/runs metrics, calibration checks, and supported-subgroup
guardrails. It must beat the metric-wise strongest of B0, Marcel, and frozen C0
on all four primary metrics in every fold and both weighting views. There is no
post-result tuning.

The implementation and one-shot scorer must be locally committed and hash-pinned
before scoring. Protected 2026, later increments, Stage 3, and WAR remain closed.
