# Hitter v2 S0 target-free fit checkpoint

Date: 2026-08-25  
Status: fit complete and frozen; not scored

## Outcome

S0 is now a valid unscored challenger. It is a single convex blend of the
frozen C0 and Marcel terminal-outcome probabilities, using the same weight for
every player and every outcome within a fold.

- V2022 had no earlier training origin, so the preregistered fallback selected
  pure C0: 100% C0 and 0% Marcel.
- V2023 selected 87.5% C0 and 12.5% Marcel using the 2022 training origin.
- V2024 independently selected the same 87.5%/12.5% blend using the 2022 and
  2023 training origins.

The interior selection is directionally encouraging but weak. Its mean
training-origin terminal-log-loss improvement over pure C0 was only 0.000166
for V2023 and 0.000117 for V2024. Those are selection results, not evidence of
future performance.

All 4,705, 5,568, and 6,381 frozen forecast players were retained. Every
probability was finite and nonnegative; maximum simplex error was
`6.66e-16`.

## Boundary

The runner did not load disclosed outer-fold outcomes and computed no disclosed
validation metric. Protected 2026 remains sealed. The prediction hashes and
selection-grid hashes are recorded in the machine-readable checkpoint.

The next gate is a separately authorized, one-shot comparison against both C0
and Marcel using the already-preregistered proper-score, future-wOBA/runs,
calibration, correlation, and subgroup rules. No weight may change after that
comparison.

Validation completed with all 999 repository tests passing and canonical lint
passing across `src`, `scripts`, and `tests`.
