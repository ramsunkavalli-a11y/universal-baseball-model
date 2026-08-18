# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

Read [`docs/project-status.md`](docs/project-status.md) first. `main` is the latest integrated branch; active work newer than the last integration is on `source-certification-poc`.

## Current stage

The portable batting, opportunity, position/role channels are frozen. **Defense v1 pre-2025 development and parameter fitting are also closed.** The active work is isolated confirmation-source preparation under a frozen one-shot contract.

- **Performance:** completed-2024 affiliated batting materialization retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting rate/profile:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.
- **Defense v1:** pre-2025 parameters frozen; 2024 MLB tracking-predictor source preparation is next/in progress before any 2025 defensive target is opened.
- **WAR/value and Overall Ranking:** later stages; **not authorized yet**.

### Defense v1 frozen pre-2025 package

Read [`docs/defense-v1-development-checkpoint.md`](docs/defense-v1-development-checkpoint.md) for the active Defense handoff, [`docs/defense-v1-2025-confirmation-contract.md`](docs/defense-v1-2025-confirmation-contract.md) for the frozen one-shot rules, and [`docs/defense-v1-confirmation-parameters.json`](docs/defense-v1-confirmation-parameters.json) for the immutable parameter package.

Canonical parameter hash:

`sha256:cba6b7ebe4b2598db2c4d9ef360b0784f23a94ad61385f87149b08c46e0390d5`

Retained forms:

- **General universal:** U1, lambda `0.0`.
- **MLB tracked increment:** T1 = exact U1 + `tracked_range_z`, only when eligible MLB tracking exists.
- **Tracked MiLB:** U1 only; Tier-B T1 was not accepted because the frozen transfer gate had insufficient evidence.
- **Catcher throwing:** C1.
- **Catcher blocking:** C2.
- **Tracked framing:** failed / closed.

Frozen coverage hierarchy:

- eligible MLB + eligible tracking -> T1;
- eligible MLB without tracking -> U1;
- eligible affiliated MiLB -> U1;
- insufficient component evidence -> declared neutral/insufficient B0 fallback, not an assertion of observed average talent.

The final refit used only authorized 2022–2024 development responses and reproduced deterministically. **At the parameter freeze, neither the 2024 confirmation tracking predictor nor any 2025 defensive target had been accessed.**

### Defense confirmation sequence

1. Materialize and certify 2024 MLB tracked-range predictor evidence only under the frozen source rule.
2. Separately materialize completed-2025 Savant range/throwing/blocking targets.
3. Run the frozen one-shot confirmation with no fitting, reselection, threshold movement, or rescue tuning.
4. Freeze the final confirmed/fallback Defense-v1 component set.
5. Only then proceed toward run conversion, positional adjustment, WAR/value, and final ranking.

The 2024 tracking source is isolated from both model fitting and 2025 outcomes. No 2024 MiLB tracking or framing source is needed for the retained v1 model.

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
- [`docs/defense-v1-2025-confirmation-contract.md`](docs/defense-v1-2025-confirmation-contract.md) — frozen one-shot confirmation/source contract.
- [`docs/defense-v1-confirmation-parameters.json`](docs/defense-v1-confirmation-parameters.json) — frozen pre-2025 Defense parameter package.
- [`docs/defense-v1-2024-tracking-predictor-source-result.json`](docs/defense-v1-2024-tracking-predictor-source-result.json) — binding 2024 MLB tracked-range predictor source result once materialized.
- [`docs/defense-v1-tracked-challenger-result.json`](docs/defense-v1-tracked-challenger-result.json) — binding final tracked-development decision.
- [`docs/defense-v1-tier-b-cohort-audit.json`](docs/defense-v1-tier-b-cohort-audit.json) — diagnostic explanation of the sparse Tier-B transfer cohort.
- [`docs/defense-v1-tracked-source-result.json`](docs/defense-v1-tracked-source-result.json) — binding successful tracked-development source gate.
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
