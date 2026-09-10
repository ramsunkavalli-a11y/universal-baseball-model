# Prospect nested workload uncertainty plan

Status: frozen before player ranges are calculated.

## Purpose

Replace the missing pre-MLB range with a workload-only distribution that respects
the nested career model. Keep skill-rate uncertainty separate for a later test.

## Distribution

For each pre-MLB player, use four disjoint states: no arrival, fringe arrival,
meaningful-only, and established. Use the already modeled state probabilities. No
arrival has zero workload. Each arriving state uses every observed adjusted six-year
workload from the frozen historical post-debut cohort with equal weight.

Hitters use the hitter tier. Pitchers mix starter, swingman, and reliever samples by
the player's existing role probabilities. A role/tier cell with fewer than 30 players
falls back to the pooled pitcher tier, exactly matching the point-estimate policy.

Multiply workload draws by the player's existing conditional WAR rate. Report the
weighted 10th, 50th, and 90th percentiles and workload-only probability of at least
18 WAR. The weighted mean must equal the current nested expected WAR within numerical
tolerance; otherwise fail the build.

## Boundaries

This is not a full confidence interval. It does not yet vary batting/pitching talent,
aging, injury, defense, position retention, market price, or contract rules. It may be
shown only as a labeled workload range in the private explorer. No outside FV, player
name, grade target, current 2026 outcome, or post-result tuning is allowed.
