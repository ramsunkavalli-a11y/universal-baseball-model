# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

**Active work is on `source-certification-poc`, not `main`.** New chats, coding agents, and contributors should read [`docs/project-status.md`](docs/project-status.md) first.

The active draft PR is **#1**. The branch is far ahead of `main`; do not infer project status from the default branch.

## Current stage

The project has completed the first batting **Performance** and **Current Talent** stages far enough to support downstream Projection work.

- **Performance:** completed-2024 affiliated batting materialization is production-shaped and frozen for downstream reuse.
- **Current Talent:** finished and frozen. The retained universal model is `translated_multiseason_recency_empirical_bayes_v1` (Baseline 2).
- **Projection v1:** active work.
- **Player Value / WAR / Overall Ranking:** later stages; not yet implemented.

Two richer Current Talent batted-ball challengers were tested under predeclared chronological contracts. Challenger 1 failed development. Challenger 2 passed development but failed the single fixed 2023 confirmation because MAE and calibration-intercept guardrails deteriorated despite lower MSE in all three folds. Challenger 2 is closed without rescue tuning. Baseline 2 remains the production Current Talent model.

Projection v1 asks whether a leakage-safe age/development adjustment improves next-season batting-rate/profile prediction over carrying frozen Current Talent forward unchanged. Development uses 2022–2024 target seasons; **2025 outcomes remain quarantined as the untouched confirmation period**.

### Live Projection status

Projection contracts and fast deterministic CI are passing, including the next-year dataset contract and exact-game outcome/league fallback behavior. The current implementation blocker is the heavy **2024 MiLB historical-evidence reuse/materialization path**.

A dedicated recovery audit has isolated a concrete official-source condition: `game_pk 755829` returns **404 Not Found** from the expected Stats API `/feed/live` endpoint. The next step is to classify that exact source condition, encode the narrowest supported handling rule with regression coverage, continue the audit, and only then rerun the full 2024 evidence path.

Machine-readable workflow snapshots:

- [`docs/projection-status.json`](docs/projection-status.json)
- [`docs/projection-recovery-status.json`](docs/projection-recovery-status.json)

Human handoff and modeling contract:

- [`docs/project-status.md`](docs/project-status.md)
- [`docs/projection-batting-v1-plan.md`](docs/projection-batting-v1-plan.md)

## Core principles

- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Use a common evaluation language across levels while allowing different evidence/models where coverage differs.
- Prefer mature public datasets, parsers, and packages over rebuilding raw-source cleanup.
- Treat MLB/official sources as reconciliation authority, not necessarily the first working dataset.
- Preserve uncertainty, coverage, provenance, and measurement quality.
- Validate chronologically and prevent hindsight leakage.
- Keep production logic in `src/`; notebooks are for exploration only.
- Fail closed on unresolved source ambiguity.

## Current milestone documents

- [`docs/project-status.md`](docs/project-status.md) — canonical live handoff and next action.
- [`docs/projection-batting-v1-plan.md`](docs/projection-batting-v1-plan.md) — frozen Projection v1 design and 2025 quarantine.
- [`docs/projection-status.json`](docs/projection-status.json) — persisted Projection workflow status.
- [`docs/projection-recovery-status.json`](docs/projection-recovery-status.json) — focused recovery/source-gap workflow status.
- [`docs/current-talent-results-only-baseline-freeze.md`](docs/current-talent-results-only-baseline-freeze.md) — frozen Current Talent Baseline 2.
- [`docs/current-talent-contact-value-confirmation-result.json`](docs/current-talent-contact-value-confirmation-result.json) — binding Challenger 2 failure/closeout.
- [`docs/current-talent-challenger2-postmortem.md`](docs/current-talent-challenger2-postmortem.md) — methodological lessons and closeout.
- [`docs/performance-2024-affiliated-checkpoint.md`](docs/performance-2024-affiliated-checkpoint.md) — completed-2024 affiliated batting Performance checkpoint.

Older Current Talent development/confirmation files are historical evidence. Do not treat them as active work queues.

## Development workflow

1. Reuse certified public work and existing repo adapters before rebuilding source ingestion.
2. Work in small verified batches, usually 2–3 steps.
3. Verify each batch before expanding scope.
4. Keep heavy live-source certification/validation workflows manual after their gate passes; keep deterministic regression tests in normal CI.
5. Update `docs/project-status.md` whenever a major gate, blocker, or recommended next action changes.
6. Do not open quarantined confirmation data before the model form, search space, refit rule, and promotion gates are frozen.

## Foundation references

- [`docs/source-audit.md`](docs/source-audit.md) — public source/package audit.
- [`docs/source-certification-plan.md`](docs/source-certification-plan.md) — source certification rules.
- [`docs/source-certification-current.md`](docs/source-certification-current.md) — detailed source-certification snapshot.
- [`docs/canonical-data-contract.md`](docs/canonical-data-contract.md) — canonical grains, provenance, and storage semantics.
- [`docs/adr/`](docs/adr/) — accepted architectural decisions.
