# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

Read [`docs/project-status.md`](docs/project-status.md) first. `main` is the latest integrated branch; active work newer than the last integration is on `source-certification-poc`.

## Current stage

The portable batting, opportunity, position/role, and defensive-skill channels are frozen.

- **Performance:** completed-2024 affiliated batting materialization retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting rate/profile:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.
- **Defense v1:** **frozen and 2025-confirmed**. Final hierarchy is T1 for eligible MLB tracked range, U1 for other eligible general-range rows, C1 for eligible catcher throwing, and neutral B0 for catcher blocking.
- **Run conversion / positional adjustment:** next authorized stage.
- **WAR/value and Overall Ranking:** not authorized yet.

## Defense v1 final result

Binding result: [`docs/defense-v1-2025-confirmation-result.json`](docs/defense-v1-2025-confirmation-result.json).

Frozen contract: [`docs/defense-v1-2025-confirmation-contract.md`](docs/defense-v1-2025-confirmation-contract.md).

Frozen parameter package: [`docs/defense-v1-confirmation-parameters.json`](docs/defense-v1-confirmation-parameters.json).

Canonical parameter hash:

`sha256:cba6b7ebe4b2598db2c4d9ef360b0784f23a94ad61385f87149b08c46e0390d5`

Final components:

- **General range U1:** confirmed on untouched 2025 outcomes.
- **MLB tracked T1:** confirmed incrementally over U1 on 135 identical tracked rows.
- **Tracked MiLB T1:** closed / insufficient transfer evidence.
- **Catcher throwing C1:** confirmed.
- **Catcher blocking C2:** failed the frozen confirmation gate; final fallback is neutral B0.
- **Tracked framing:** closed / not retained.

No confirmation refit, reselection, recalibration, threshold movement, or rescue tuning is permitted.

## Next stage

The Defense confirmation result authorizes **run-value conversion next**, while WAR/value remains closed.

Before calculating value:

1. inspect existing run-conversion and positional-adjustment work in the repo;
2. freeze the conversion/adjustment methodology and source contract;
3. certify that stage without altering any frozen Defense skill estimate;
4. only then authorize WAR/value aggregation.

## Core principles

- Keep **Performance**, **Current Talent**, **Projection**, **Playing Time**, **Position/Role**, **Defense**, positional adjustment, run conversion, and **Player Value / Overall Ranking** separate.
- Use a common evaluation language across levels while allowing different evidence/models where coverage differs.
- Prefer mature public datasets, parsers, and packages over rebuilding raw-source cleanup.
- Treat MLB/official sources as reconciliation authority, not necessarily the first working dataset.
- Preserve uncertainty, coverage, provenance, and measurement quality.
- Validate chronologically and prevent hindsight leakage.
- Fail closed on unresolved source ambiguity.
- Promote only on fixed out-of-time evidence; do not rescue a challenger after a frozen gate fails.

## Current milestone documents

- [`docs/project-status.md`](docs/project-status.md) — canonical live handoff and next action.
- [`docs/defense-v1-2025-confirmation-result.json`](docs/defense-v1-2025-confirmation-result.json) — binding final Defense-v1 confirmation.
- [`docs/defense-v1-2025-confirmation-contract.md`](docs/defense-v1-2025-confirmation-contract.md) — frozen one-shot rules.
- [`docs/defense-v1-confirmation-parameters.json`](docs/defense-v1-confirmation-parameters.json) — frozen Defense parameter package.
- [`docs/defense-v1-2025-target-source-result.json`](docs/defense-v1-2025-target-source-result.json) — certified 2025 Defense targets.
- [`docs/defense-v1-2024-tracking-predictor-source-result.json`](docs/defense-v1-2024-tracking-predictor-source-result.json) — certified 2024 MLB tracked-range predictor.
- [`docs/position-role-2025-confirmation-result.json`](docs/position-role-2025-confirmation-result.json) — binding Position / Role v1 confirmation.
- [`docs/playing-time-v1-confirmation-result.json`](docs/playing-time-v1-confirmation-result.json) — binding Playing Time v1 confirmation.
- [`docs/projection-batting-v1-development-result.json`](docs/projection-batting-v1-development-result.json) — binding Projection v1 decision.
- [`docs/current-talent-results-only-baseline-freeze.md`](docs/current-talent-results-only-baseline-freeze.md) — frozen Current Talent Baseline 2.
- [`docs/performance-2024-affiliated-checkpoint.md`](docs/performance-2024-affiliated-checkpoint.md) — completed-2024 affiliated batting Performance checkpoint.

## Development workflow

1. Reuse certified public work and existing repo adapters before rebuilding source ingestion.
2. Work in small verified batches, usually 2–3 steps.
3. Verify each batch before expanding scope.
4. Keep heavy live-source certification workflows manual after their gate passes; keep deterministic regression tests in normal CI.
5. Update `docs/project-status.md` whenever a major gate, blocker, or recommended next action changes.
6. Freeze model form/search space/validation rules before opening held-out or confirmation outcomes.
7. When a predeclared gate fails, close the challenger rather than tuning against the failed period.

## Foundation references

- [`docs/source-audit.md`](docs/source-audit.md) — public source/package audit.
- [`docs/source-certification-plan.md`](docs/source-certification-plan.md) — source certification rules.
- [`docs/source-certification-current.md`](docs/source-certification-current.md) — detailed source-certification snapshot.
- [`docs/canonical-data-contract.md`](docs/canonical-data-contract.md) — canonical grains, provenance, and storage semantics.
- [`docs/adr/`](docs/adr/) — accepted architectural decisions.
