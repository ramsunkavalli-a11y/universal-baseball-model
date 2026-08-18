# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

**Current work is on `source-certification-poc`, not `main`.** A new chat or contributor should read [`docs/project-status.md`](docs/project-status.md) first. It records the latest completed milestones, certified workflow runs, important boundaries, current branch/PR state, and the recommended next batch.

The active draft PR is **#1 — Build and certify universal baseball foundation layer**.

## Current stage

The first batting **Performance** layer is production-shaped for completed 2024 affiliated baseball, and the first universal batting **Current Talent** model is now frozen.

Frozen Current Talent model:

`translated_multiseason_recency_empirical_bayes_v1`

It is a results-only, multi-season, recency-weighted empirical-Bayes profile with training-only MLB-anchored level translation.

Two richer batted-ball challengers were tested under chronological contracts:

- Challenger 1 failed fixed 2022 development and is closed.
- Challenger 2 passed every fixed 2022 development gate but failed the one-shot 2023 confirmation because MAE and calibration-intercept guardrails deteriorated despite lower MSE in all three confirmation folds.

Therefore Challenger 2 is closed without rescue tuning, and Baseline 2 remains the Current Talent model. See [`docs/current-talent-challenger2-postmortem.md`](docs/current-talent-challenger2-postmortem.md).

The project is now moving to **batting Projection v1**. The first question is deliberately simple: can a leakage-safe age/development adjustment improve next-season rate/profile prediction over carrying frozen Current Talent forward unchanged? Projection v1 uses 2022–2024 as chronological development targets and quarantines **2025 outcomes** as the untouched confirmation period. See [`docs/projection-batting-v1-plan.md`](docs/projection-batting-v1-plan.md).

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
- [`docs/current-talent-results-only-baseline-freeze.md`](docs/current-talent-results-only-baseline-freeze.md) — frozen Current Talent Baseline 2.
- [`docs/current-talent-contact-value-confirmation-result.json`](docs/current-talent-contact-value-confirmation-result.json) — binding Challenger 2 confirmation result.
- [`docs/current-talent-challenger2-postmortem.md`](docs/current-talent-challenger2-postmortem.md) — lessons and methodological closeout.
- [`docs/projection-batting-v1-plan.md`](docs/projection-batting-v1-plan.md) — pre-development Projection v1 contract; 2025 quarantined.
- [`docs/current-talent-validation-contract.md`](docs/current-talent-validation-contract.md) — governing Current Talent target/chronology principles and relationship to Projection.
- [`docs/performance-2024-affiliated-checkpoint.md`](docs/performance-2024-affiliated-checkpoint.md) — production-shaped completed-2024 affiliated batting Performance materialization.

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
