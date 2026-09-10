# Prospect component uncertainty plan

Status: frozen before player results are calculated.

## Question

How much wider do prospect WAR outcomes become when the workload mixture is combined
with the batting or pitching component uncertainty already estimated by the model?

## Method

Retain the exact no-arrival/fringe/meaningful/established workload distribution from
`nested_empirical_workload_only_v1`. For every positive historical workload value,
add zero-mean component noise using the existing event-run variance and posterior
run-rate variance:

`Var(runs | W) = W * event variance + max(W^2 - W, 0) * posterior rate variance`

Convert runs to WAR with the frozen 2025 runs-per-win environment. Use a fixed,
symmetric 41-point standard-normal quadrature so the component-noise mean is exactly
zero rather than relying on a lucky simulation seed. Average the already projected
six annual variance inputs; do not refit or recalibrate them.

Report P10/P50/P90, probability of at least 18 WAR, and the exact weighted mean. The
mean must reproduce current nested WAR within `1e-8`. Compare widths with the
workload-only layer.

## Boundaries

This adds batting/pitching outcome-rate uncertainty only. It still omits uncertainty
in position retention, defense, baserunning, aging, injury, league translation,
market price, and contracts. It is research-only until historical coverage is tested.
No 2026 outcomes, outside FV, player names, grade counts, or post-result tuning may
enter the calculation.
