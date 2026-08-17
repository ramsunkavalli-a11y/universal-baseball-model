# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

**Current work is on `source-certification-poc`, not `main`.** A new chat or contributor should read [`docs/project-status.md`](docs/project-status.md) first. It records the latest completed milestones, certified workflow runs, important boundaries, current branch/PR state, and the recommended next batch.

The active draft PR is **#1 — Build and certify universal baseball foundation layer**.

**Current stage:** Baseline 1 has beaten Baseline 0 with unchanged candidate settings at common **July 15, Aug. 1, and Sep. 1 cutoffs in 2021–2023**. The main predictive gain is stable and comes from player-specific recent evidence + empirical-Bayes shrinkage. Full-strength level translation remains a smaller, less stable second-order effect and is not frozen. The next gate is a **multi-fold calibration review**, including calibration intercept/slope, before chronological hyperparameter selection. No Current Talent model is frozen yet.

## Core principles

- Separate **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** instead of collapsing them into one opaque score.
- Use a common evaluation language across levels while allowing different evidence and models where data coverage differs.
- Prefer mature public datasets, parsers, and packages over rebuilding source cleanup from scratch.
- Treat MLB/official sources as the authority for reconciliation, not necessarily as the first working dataset.
- Preserve uncertainty, data coverage, provenance, and measurement quality in model outputs.
- Validate chronologically and prevent hindsight leakage.
- Keep production logic in `src/`; notebooks are for exploration only.

## Current milestone documents

- [`docs/project-status.md`](docs/project-status.md) — **canonical current handoff / roadmap**.
- [`docs/current-talent-validation-contract.md`](docs/current-talent-validation-contract.md) — governing Current Talent target, chronology, baseline, and validation contract.
- [`docs/current-talent-baseline-checkpoint.md`](docs/current-talent-baseline-checkpoint.md) — Baseline 0/1 implementation, nine common July/August/September folds, and fitted-vs-zero translation ablation.
- [`docs/current-talent-historical-mlb-checkpoint.md`](docs/current-talent-historical-mlb-checkpoint.md) — certified 2021–2023 historical MLB Current Talent evidence and official reconciliation rules.
- [`docs/current-talent-historical-milb-checkpoint.md`](docs/current-talent-historical-milb-checkpoint.md) — certified 2021–2023 historical affiliated-MiLB evidence.
- [`docs/performance-2024-affiliated-checkpoint.md`](docs/performance-2024-affiliated-checkpoint.md) — first production-shaped completed-2024 affiliated batting Performance materialization.

## Development workflow

1. Reuse existing public work where it survives certification; do not restart settled source research without a concrete failure.
2. Make changes in small batches of roughly **2–3 steps**.
3. Verify each batch before expanding scope so an early assumption cannot contaminate a large downstream change.
4. Keep heavy live-source certification/validation workflows manual after their gate passes; keep deterministic regression tests in normal CI.
5. **Update `docs/project-status.md` at meaningful junctures before continuing**—especially after a major gate passes, a material architecture/modeling decision is frozen, or the recommended next batch changes.
6. Pause for an explicit modeling decision when an unresolved assumption could materially change downstream architecture rather than papering over it in code.

## Foundation references

- [`docs/source-audit.md`](docs/source-audit.md) — research and assignment of public data sources/packages.
- [`docs/source-certification-plan.md`](docs/source-certification-plan.md) — empirical tests reusable sources must pass before feeding canonical tables.
- [`docs/source-certification-current.md`](docs/source-certification-current.md) — detailed foundation/source certification snapshot; use `docs/project-status.md` for the live roadmap.
- [`docs/canonical-data-contract.md`](docs/canonical-data-contract.md) — canonical grains, provenance, and storage semantics.
- [`docs/adr/`](docs/adr/) — accepted architectural decisions.

Foundation work should favor correctness, reversibility, explicit evidence, and reproducibility over speed.
