# Prospect hitter joint one-year audit result

Status: diagnostic complete; no candidate or current value changed.

The test fit the deployed arrival/role structure only on origins through 2023, rebuilt
translated batting-plus-replacement rates through 2024, and evaluated all 2,964
eligible pre-MLB hitters against completed 2025 MLB outcomes. Non-arrivals remain as
zeros.

## Results

| Group | Players | Predicted WAR | Observed WAR | Bias | RMSE |
|---|---:|---:|---:|---:|---:|
| All hitters | 2,964 | 0.0033 | 0.0100 | -0.0067 | 0.1742 |
| High-arrival, below-average batting | 10 | 0.0588 | 0.0897 | -0.0308 | 0.4467 |
| Hitters who reached MLB | 104 | 0.0276 | 0.2848 | -0.2572 | 0.9296 |

Overall one-year arrival was calibrated: 3.57% predicted versus 3.51% observed.
Meaningful roles were underpredicted (0.60% versus 0.94%), as were established roles
(0.17% versus 0.34%). The high-arrival/below-average-batting subgroup was small, but
eight of ten reached MLB versus 6.64 implied; its WAR bias interval spans both
directions.

## Decision

Do not lower hitter arrival or workload merely to make the prospect list look more
familiar. The completed 2025 evidence does not support that direction and shows the
model misses positive outcomes among actual arrivals.

The 28 model-only hitters with below-average batting are still important casebook
rows, but the next missing piece is ceiling discrimination: separate likely MLB depth
from future impact players using cutoff-safe skill/process and entry-path evidence.
Official Rule 4 pedigree may enter an arrival/role candidate only through a separate
Rule 4 path with a neutral international path; it may never become a WAR bonus or FV
floor. Broader PBP contact/process evidence remains preferable when available.

No public rank, public FV, 2026 outcome, position, defense, baserunning, or
organization depth entered this audit. Machine-readable detail is in
`docs/prospect-hitter-joint-one-year-audit-result.json`.

