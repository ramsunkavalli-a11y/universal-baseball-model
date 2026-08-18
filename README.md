# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

Read [`docs/project-status.md`](docs/project-status.md) first. `main` is the latest integrated branch; active work newer than the last integration is on `source-certification-poc`.

## Current stage

The portable batting, opportunity, and position/role channels are frozen. Defense v1 is in its **final pre-2025 development gate**: universal range/blocking/throwing components have already been selected, the age challenger is closed, and the frozen tracked range/framing source gate has passed.

- **Performance:** completed-2024 affiliated batting materialization is production-shaped and retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1` (Baseline 2).
- **Projection v1 batting rate/profile:** frozen at `frozen_current_talent_carry_forward_v1`; the age/development challenger failed its fixed OOT gate.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.
- **Defense v1:** universal U1/C2/C1 path selected; final tracked source materialization passed; frozen tracked challenger scoring is next.
- **WAR/value and Overall Ranking:** later stages; **not authorized yet**.

### Defense v1 current handoff

Read [`docs/defense-v1-development-checkpoint.md`](docs/defense-v1-development-checkpoint.md) for the active Defense handoff.

The final tracked source workflow passed on run `32182019495`. It persisted hash-pinned 2021–2023 MLB tracked range/framing evidence plus 2023 tracked MiLB transfer evidence without opening any 2025 source or defensive target.

The next authorized action is to run the already-frozen scorer at `scripts/audit_defense_v1_tracked_challenger.py` against those persisted artifacts:

- general range: selected **U1** vs **T1 = U1 + tracked_range_z**;
- catcher framing: **F0 neutral** vs frozen one-feature **F1**.

If a tracked component passes its MLB gate, only its predeclared 2023-MiLB -> 2024-MLB transfer diagnostic may follow. There are no additional planned pre-2025 Defense challengers after this gate.

**Do not open 2025 defensive source/targets or begin WAR/value work yet.**

### Position / Role v1 result

Official 2021–2024 fielding source certification passed all 64 season×league pairs. After a broad transition smoother failed development, a final pre-frozen selective rule passed both development folds:

- carry the current nine-position role profile forward unchanged when primary-position share `< 0.65`;
- at `>= 0.65`, blend the current profile with the historical next-year destination profile for that current primary position.

All confirmation parameters were frozen before 2025 position data was opened. The one-shot 2025 confirmation then passed on 2,891 players:

- mean TV distance: **0.32553 → 0.32462**;
- mean summed squared error: **0.22692 → 0.21639**.

No confirmation refit, threshold change, candidate reselection, or rescue tuning occurred.

Key Position / Role records:

- [`docs/position-role-2025-confirmation-result.json`](docs/position-role-2025-confirmation-result.json)
- [`docs/position-role-2025-confirmation-contract.md`](docs/position-role-2025-confirmation-contract.md)
- [`docs/position-role-confirmation-parameters.json`](docs/position-role-confirmation-parameters.json)
- [`docs/position-role-historical-source-result.json`](docs/position-role-historical-source-result.json)

### Projection v1 boundary

The pre-registered age/development challenger improved in the first 2023 OOT fold but reversed in the fixed 2024 fold, so carry-forward B2 remains Projection v1 without rescue tuning.

**2025 batting-rate/profile outcomes remain untouched.** Later 2025 Playing Time and Position/Role confirmations used only their own separately frozen opportunity or position-role targets.

## Core principles

- Keep **Performance**, **Current Talent**, **Projection**, **playing time**, **position/role**, **defense**, and **Player Value / Overall Ranking** separate.
- Use a common evaluation language across levels while allowing different evidence/models where coverage differs.
- Prefer mature public datasets, parsers, and packages over rebuilding raw-source cleanup.
- Treat MLB/official sources as reconciliation authority, not necessarily the first working dataset.
- Preserve uncertainty, coverage, provenance, and measurement quality.
- Validate chronologically and prevent hindsight leakage.
- Keep production logic in `src/`; notebooks are for exploration only.
- Fail closed on unresolved source ambiguity.
- Do not force a more complex model merely because one is conventional; promote only on fixed out-of-time evidence.

## Current milestone documents

- [`docs/project-status.md`](docs/project-status.md) — canonical live handoff and next action.
- [`docs/defense-v1-development-checkpoint.md`](docs/defense-v1-development-checkpoint.md) — active Defense-v1 scoring handoff.
- [`docs/defense-v1-tracked-challenger-contract.md`](docs/defense-v1-tracked-challenger-contract.md) — frozen final pre-2025 tracked challenger.
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
