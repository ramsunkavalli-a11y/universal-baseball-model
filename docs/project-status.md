# Project status and handoff

Last updated: 2026-08-17 21:13 PT

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active development branch: `source-certification-poc`
- PR #1 was merged on 2026-08-17; `main` is the integrated source of truth through that merge.
- Inspect `source-certification-poc` and live Actions for work newer than the latest integration.
- Work in small verified batches.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, playing time/role, defense, WAR/value, and final ranking separate.

## Stage summary

### Performance — complete for current downstream batting needs

Completed-2024 affiliated batting Performance materialization is production-shaped and retained.

Primary checkpoint: `docs/performance-2024-affiliated-checkpoint.md`.

Do not reopen Performance/source-foundation work absent a concrete downstream failure.

### Current Talent — DONE / FROZEN

Frozen universal results-only comparator:

`translated_multiseason_recency_empirical_bayes_v1`

Frozen design:

- current season plus prior certified seasons where available, capped at 1,095 days;
- 180-day exponential half-life;
- EB prior strength 100 effective core events;
- training-only MLB-anchored level translation;
- frozen age/current-level Baseline 0 prior;
- frozen 12-component batting profile.

Richer Challenger 1 is closed after failed development.

Richer Challenger 2 (`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`) passed development but failed the one-shot 2023 confirmation. Binding result: `confirmed = false`. Do not tune/rescue/reselect it or integrate it downstream.

Key Current Talent records:

- `docs/current-talent-results-only-baseline-freeze.md`
- `docs/current-talent-contact-value-confirmation-result.json`
- `docs/current-talent-challenger2-postmortem.md`

### Projection v1 — ACTIVE

Primary question:

> Does a simple leakage-safe age/development adjustment improve next-season batting-rate/profile prediction over carrying frozen Current Talent forward unchanged?

Projection v1 is rate/profile only. Zero future opportunity is not bad batting skill; playing time/role remains a separate later channel.

Untouched confirmation:

- **2025 regular-season outcomes remain quarantined.**

## Projection data/source gates — COMPLETE

### Certified 2024 affiliated MiLB evidence

The exact source-residual quarantine work is complete and the final all-level report-level proof passed.

Binding 2024 MiLB run:

- `32095039114` — **Gate 2024 artifacts on exact reconciliation proof** — success.

The final gate requires exact aggregate reconciliation, zero unresolved outcome residuals, both independent quarantine proofs for every applied row, and exact cross-grain quarantine-key propagation.

The narrow terminal empty-slice case is accepted only after the pre-existing exact two-ledger quarantine has already proven the removed source row. No identity/outcome values are guessed or reassigned.

### Certified 2024 MLB v2 evidence

The older 2024 MLB game-evidence bundle used a pre-v2 schema and was not coerced into the new universal contract.

Instead, the existing historical MLB materializer was reused for 2024 and certified on the current v2 evidence schema:

- `32096473700` — **Materialize certified 2024 MLB Current Talent evidence** — success.

Artifact:

- `current-talent-historical-mlb-2024`
- artifact id `9310382371`
- digest `sha256:bdca35299b7a82130eae197987aa1d1bb0448c8ef9dc9ee6c6ba3d39e79f2efe`

### Universal schema boundary

Certified component artifacts may contain source-specific extra columns, but universal combination now explicitly projects onto the frozen canonical evidence fields before concatenation.

Fast contract CI:

- `32096179903` — **Gate universal evidence schema in Projection CI** — success.

## Projection development surfaces — COMPLETE / VERIFIED

Final evidence-only materialization:

- `32097702869` — **Align Projection history diagnostics with frozen B2 source epoch** — success.

This materializes all three authorized pre-confirmation folds using certified 2021–2024 MLB + affiliated evidence:

1. `2021-10-15 -> 2022`
2. `2022-10-15 -> 2023`
3. `2023-10-15 -> 2024`

The run does **not** fit Projection, score a candidate, or access 2025.

### Frozen B2 history reproduction boundary

Do **not** backfill 2018–2020 merely because the B2 maximum lookback is 1,095 days.

The frozen B2 plan explicitly used current season plus prior **certified** seasons where available, and the certified universal source epoch begins in 2021. The 1,095-day value is a cap, not a command to expand into an unvalidated source era.

Governing record:

- `docs/projection-b2-history-reproduction-contract.md`

Calendar left-censoring remains visible as a diagnostic; it is not a current blocker.

## Projection methodology / model-selection contract — FROZEN BEFORE SCORING

Literature/methodology review:

- `docs/projection-v1-methodology-review.md`

Binding candidate/search/promotion contract:

- `docs/projection-batting-v1-development-contract.md`

Key decisions:

- Baseline 0 = frozen B2 carry-forward.
- Baseline 1 operates on the 12-part profile through a fixed 11-D ILR representation.
- Candidate forms are restricted to:
  - age-only continuous piecewise-linear ridge adjustment;
  - age + as-of-level main effects with the same ridge adjustment.
- No age × level interaction, player-specific aging slopes, tracking, scouting, future level, or opportunity features.
- Lambda grid is frozen at `{0.001, 0.01, 0.1, 1.0}`.
- `2021 -> 2022` is the **training / candidate-selection fold** using deterministic 5-fold player-held-out CV.
- `2022 -> 2023` and `2023 -> 2024` are the two **rolling-origin out-of-time validation folds** and cannot choose model form/hyperparameters.
- 2025 remains untouched confirmation.
- Future-opportunity selection is reported explicitly rather than imputed into the rate model.

## Immediate next batch

1. Materialize frozen B2 latent profiles + fold-specific pre-snapshot translation artifacts for the three pre-2025 Projection snapshots and verify exact reproduction of the frozen B2 contract.
2. Implement/test deterministic ILR transform/inverse and the pre-registered ridge age-design contract.
3. Only after those deterministic tests pass, run **2022-fold candidate selection**. Do not open 2023/2024 validation results to choose form/lambda.

After candidate selection:

- if selected candidate fails to beat carry-forward on held-out 2022 CV log loss, stop and retain Baseline 0;
- otherwise freeze the selected form/lambda and run the two rolling-origin validation folds exactly as pre-registered.

No 2025 outcome materialization/scoring belongs in the current batch.

## Machine-readable/live status

- `docs/projection-recovery-status.json` — current Actions registry.
- `docs/projection-status.json` — Projection checkpoint snapshot.

Recent successful runs include:

- `32095039114` — certified 2024 MiLB all-level gate
- `32096179903` — universal evidence schema contract
- `32096473700` — certified 2024 MLB v2 evidence
- `32097430956` — complete 2021–2024 development surfaces
- `32097702874` — history-contract fast CI
- `32097702869` — corrected-history development-surface materialization

## Governing read order

1. `docs/project-status.md`
2. `docs/projection-batting-v1-development-contract.md`
3. `docs/projection-v1-methodology-review.md`
4. `docs/projection-batting-v1-plan.md`
5. `docs/projection-b2-history-reproduction-contract.md`
6. `docs/projection-recovery-status.json`
7. `docs/current-talent-results-only-baseline-freeze.md`
8. `docs/current-talent-contact-value-confirmation-result.json`
9. `docs/current-talent-challenger2-postmortem.md`
10. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent selection/confirmation work absent a concrete implementation failure.
- Do not broaden source quarantine policies because a workflow fails; inspect the exact failing contract.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Do not alter the pre-registered Projection candidate family/grid after seeing 2023/2024 validation outcomes.
- Keep 2025 quarantined until the selected Projection model has passed development and the final confirmation refit is persisted and reproducible.