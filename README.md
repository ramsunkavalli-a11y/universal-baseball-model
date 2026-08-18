# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

Read [`docs/project-status.md`](docs/project-status.md) first. `main` is the latest integrated branch; active work newer than the last integration is on `source-certification-poc`.

## Current stage

The portable batting, opportunity, and position/role channels are frozen. **Defense v1 pre-2025 development is now closed**, and the next authorized work is final refit/parameter freeze of the retained defensive components.

- **Performance:** completed-2024 affiliated batting materialization retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting rate/profile:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.
- **Defense v1:** universal U1/C2/C1 selected; final tracked challenger complete; final refit/parameter freeze is next.
- **WAR/value and Overall Ranking:** later stages; **not authorized yet**.

### Defense v1 binding tracked result

Read [`docs/defense-v1-development-checkpoint.md`](docs/defense-v1-development-checkpoint.md) for the active Defense handoff and [`docs/defense-v1-tracked-challenger-result.json`](docs/defense-v1-tracked-challenger-result.json) for the binding machine-readable result.

Frozen scoring run `32196115227` completed successfully after verifying the tracked-source artifacts from run `32182019495`.

- **Tracked range / Tier A MLB:** T1 (`U1 + tracked_range_z`) **passed**. It improved pooled MSE by 1.93%, beat U1 in all three held folds, and improved pooled Spearman by 0.0118.
- **Tracked range / Tier B MiLB:** **not accepted**. The predeclared transfer diagnostic had zero eligible players and therefore `insufficient_transfer_evidence`, which is not a pass under the frozen contract.
- **Tracked framing:** **failed / closed**. F1 improved pooled MSE, but the 2022 fold was 8.35% worse than F0, breaching the frozen 5% fold-degradation guardrail. No transfer test or rescue is authorized.

Retained Defense evidence entering final freeze:

- Tier A MLB: T1 tracked range + universal C2 blocking/C1 throwing where eligible;
- Tier B tracked MiLB: U1 universal range + universal C2/C1 where eligible;
- Tier C untracked affiliated MiLB: U1 universal range + universal C2/C1 where eligible;
- no tracked framing component.

**Do not open 2025 defensive source/targets or begin WAR/value work yet.**

### Projection v1 boundary

The pre-registered age/development challenger improved in the first 2023 OOT fold but reversed in the fixed 2024 fold, so carry-forward B2 remains Projection v1 without rescue tuning.

**2025 batting-rate/profile outcomes remain untouched.** Later 2025 Playing Time and Position/Role confirmations used only their own separately frozen targets.

## Core principles

- Keep **Performance**, **Current Talent**, **Projection**, **playing time**, **position/role**, **defense**, and **Player Value / Overall Ranking** separate.
- Use a common evaluation language across levels while allowing different evidence/models where coverage differs.
- Prefer mature public datasets, parsers, and packages over rebuilding raw-source cleanup.
- Treat MLB/official sources as reconciliation authority, not necessarily the first working dataset.
- Preserve uncertainty, coverage, provenance, and measurement quality.
- Validate chronologically and prevent hindsight leakage.
- Keep production logic in `src/`; notebooks are for exploration only.
- Fail closed on unresolved source ambiguity.
- Promote only on fixed out-of-time evidence; do not rescue a challenger after a frozen gate fails.

## Current milestone documents

- [`docs/project-status.md`](docs/project-status.md) — canonical live handoff and next action.
- [`docs/defense-v1-development-checkpoint.md`](docs/defense-v1-development-checkpoint.md) — active Defense-v1 handoff.
- [`docs/defense-v1-tracked-challenger-result.json`](docs/defense-v1-tracked-challenger-result.json) — binding final tracked-challenger decision.
- [`docs/defense-v1-tracked-challenger-contract.md`](docs/defense-v1-tracked-challenger-contract.md) — frozen final pre-2025 tracked contract.
- [`docs/defense-v1-tracked-source-result.json`](docs/defense-v1-tracked-source-result.json) — binding successful tracked-source gate.
- [`docs/position-role-2025-confirmation-result.json`](docs/position-role-2025-confirmation-result.json) — binding Position / Role v1 confirmation.
- [`docs/playing-time-v1-confirmation-result.json`](docs/playing-time-v1-confirmation-result.json) — binding Playing Time v1 confirmation.
- [`docs/projection-batting-v1-development-result.json`](docs/projection-batting-v1-development-result.json) — binding Projection v1 decision.
- [`docs/current-talent-results-only-baseline-freeze.md`](docs/current-talent-results-only-baseline-freeze.md) — frozen Current Talent Baseline 2.
- [`docs/performance-2024-affiliated-checkpoint.md`](docs/performance-2024-affiliated-checkpoint.md) — completed-2024 affiliated batting Performance checkpoint.

Older development/confirmation files remain historical evidence, not active work queues.

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
