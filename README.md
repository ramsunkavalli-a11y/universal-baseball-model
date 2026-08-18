# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

Read [`docs/project-status.md`](docs/project-status.md) first. `main` is the latest integrated branch; active work newer than the last integration is on `source-certification-poc`.

## Current stage

The batting Performance, Current Talent, and one-year rate Projection v1 stages are complete enough to support the next channel.

- **Performance:** completed-2024 affiliated batting materialization is production-shaped and retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1` (Baseline 2).
- **Projection v1 batting rate/profile:** complete. The explicit age/development challenger failed fixed out-of-time development, so the retained one-year rate projection is `frozen_current_talent_carry_forward_v1`.
- **Playing time / role:** **next active stage**.
- **Defense, WAR/value, Overall Ranking:** later stages.

### Projection v1 result

The pre-registered age/development search selected `projection_age_level_ilr_ridge_v1` with ridge lambda `0.01` using only the 2022 target fold.

It improved on carry-forward B2 in the first 2023 out-of-time fold, but reversed in the fixed 2024 fold:

- 2023 log-loss delta: **-0.000480**;
- 2024 log-loss delta: **+0.000257**.

The frozen contract required improvement in both validation folds, so the challenger is rejected without rescue tuning. Carry-forward B2 remains Projection v1.

**2025 outcomes were never accessed** and remain untouched evidence for a future separately pre-registered Projection challenger if useful.

Key Projection records:

- [`docs/projection-batting-v1-development-checkpoint.md`](docs/projection-batting-v1-development-checkpoint.md)
- [`docs/projection-batting-v1-development-result.json`](docs/projection-batting-v1-development-result.json)
- [`docs/projection-batting-v1-development-contract.md`](docs/projection-batting-v1-development-contract.md)
- [`docs/projection-v1-methodology-review.md`](docs/projection-v1-methodology-review.md)

## Core principles

- Keep **Performance**, **Current Talent**, **Projection**, **playing time/role**, **defense**, and **Player Value / Overall Ranking** separate.
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
- [`docs/projection-batting-v1-development-checkpoint.md`](docs/projection-batting-v1-development-checkpoint.md) — Projection v1 closeout.
- [`docs/projection-batting-v1-development-result.json`](docs/projection-batting-v1-development-result.json) — binding Projection v1 decision.
- [`docs/current-talent-results-only-baseline-freeze.md`](docs/current-talent-results-only-baseline-freeze.md) — frozen Current Talent Baseline 2.
- [`docs/current-talent-contact-value-confirmation-result.json`](docs/current-talent-contact-value-confirmation-result.json) — binding richer Current Talent challenger failure/closeout.
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
