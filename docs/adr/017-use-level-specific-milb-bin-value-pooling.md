# ADR 017 — Use level-specific MiLB Performance-bin value pooling

**Status:** Accepted  
**Date:** 2026-08-15

## Context

ADR 014 established a modest same-level AAA shrinkage rule after leakage-safe
2025 validation and a pre-specified 2024 confirmation. The universal Performance
layer still needed equivalent evidence for AA, High-A, and Single-A using the
final foul-air-screened FaBIO-style bins.

A single all-MiLB prior would be convenient but would erase real run-environment
and level differences. Conversely, direct league-season bin means are noisy in
45-game samples. The middle-level gate therefore tested only **same-level,
same-season peer priors**, always excluding the target environment from its own
prior.

The primary 2025 audit covered all nine actual leagues represented by AA,
High-A, and Single-A, with 45 games per league. It used both alternating
split-half comparisons and leakage-safe five-fold held-out prediction. A
positive strength had to be robust in both diagnostics before it could even be
nominated for an independent season.

The 2025 gate nominated, before inspecting 2024 outcomes:

- AA: 75 prior-equivalent occurrences;
- High-A: 150;
- Single-A: 25.

The independent 2024 audit then used a separate June source snapshot, again 45
games per actual league and final screened bins. Promotion required the
pre-specified strength to improve or tie the direct estimator on all four held-
out summaries: cell MAE, cell RMSE, event MAE, and event RMSE. The 2024 full
strength grid was retained only as secondary evidence and was not allowed to
replace a failed pre-specified candidate.

## Decision

Use the following production Performance-bin value policies for affiliated MiLB:

| Level | Prior strength | Decision |
|---|---:|---|
| AAA | 25 | same-level, same-season pooling |
| AA | 75 | same-level, same-season pooling |
| High-A | 0 | direct league-season estimate |
| Single-A | 25 | same-level, same-season pooling |
| Rookie / complex | 0 | direct league-season estimate |

For every pooled level, the prior for a target league-season-bin is the
occurrence-weighted mean of the same bin from other leagues at the **same level
and same season**. The target environment never contributes to its own prior.
No AAA, MLB, Rookie, adjacent-season, or universal-MiLB fallback is substituted
when same-level peer evidence is unavailable.

These strengths apply only to **league-typical Performance-bin value
estimation**. They are not player-talent shrinkage parameters.

## Evidence

### AA

The 2025 primary gate found strengths 5–100 robust in both split-half and
five-fold validation; lambda 75 had the lowest five-fold cell MAE among the
shared robust candidates.

Independent 2024 confirmation at the pre-specified lambda 75 passed all four
metrics:

- cell MAE: 0.078908 direct -> 0.074064 pooled;
- cell RMSE: 0.109248 -> 0.103726;
- event MAE: 0.306509 -> 0.306287;
- event RMSE: 0.460518 -> 0.459777.

### Single-A

The 2025 primary gate found strengths 5–25 robust in both diagnostics; lambda 25
was nominated.

Independent 2024 confirmation passed all four metrics:

- cell MAE: 0.071408 direct -> 0.069898 pooled;
- cell RMSE: 0.102832 -> 0.100220;
- event MAE: 0.311649 -> 0.311459;
- event RMSE: 0.464185 -> 0.463858.

### High-A

The 2025 primary gate nominated lambda 150 after broad split-half support and
five-fold robustness through 150. The independent 2024 test did **not** pass the
pre-registered all-four-metric criterion:

- cell MAE improved: 0.076831 -> 0.076016;
- cell RMSE improved: 0.106806 -> 0.104451;
- event RMSE improved: 0.459814 -> 0.459598;
- event MAE worsened slightly: 0.303817 -> 0.304506.

The 2024 secondary grid showed smaller strengths could have passed, but choosing
one after inspecting the independent season would be post-hoc tuning. High-A is
therefore kept direct. A future positive High-A rule would require a newly
pre-registered validation cycle on fresh evidence.

### Rookie / complex

Earlier split-half and five-fold diagnostics disagreed about whether modest
positive pooling was beneficial. The conservative direct estimator remains in
force.

## Consequences

1. The universal Performance output uses a common value framework but does not
   force identical estimator strength across levels.
2. AA and Single-A gain modest variance reduction that replicated out of year.
3. High-A remains deliberately unpooled despite suggestive secondary evidence;
   this avoids contaminating the independent test with post-hoc selection.
4. Missing same-level peer support never triggers an undocumented fallback.
5. Estimator policy is explicit machine-readable metadata and can be surfaced in
   player-level uncertainty / coverage outputs later.

## Implementation

`src/universal_baseball/bin_value_policy.py` is the machine-readable policy.
`tests/test_bin_value_policy.py` prevents silent changes to the certified
strengths or level mapping.

The supporting audits are:

- `scripts/audit_middle_level_bin_value_validation.py` — primary 2025 gate;
- `scripts/audit_middle_level_bin_value_independent_validation.py` — fixed 2024
  confirmation;
- ADR 014 — AAA precedent.
