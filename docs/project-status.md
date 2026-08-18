# Project status and handoff

Last updated: 2026-08-17 21:35 PT

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active development branch: `source-certification-poc`
- `source-certification-poc` contains newer work than the latest integration into `main`.
- Work in small verified batches.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, playing time/role, defense, WAR/value, and final ranking separate.

## Stage summary

### Performance — DONE for current batting pipeline

Completed-2024 affiliated batting Performance materialization is production-shaped and retained.

Primary checkpoint: `docs/performance-2024-affiliated-checkpoint.md`.

### Current Talent — DONE / FROZEN

Retained universal model:

`translated_multiseason_recency_empirical_bayes_v1`

Frozen design:

- current season plus prior certified seasons where available, capped at 1,095 days;
- 180-day exponential half-life;
- EB prior strength 100 effective core events;
- training-only MLB-anchored level translation;
- frozen age/current-level Baseline 0 prior;
- frozen 12-component batting profile.

Richer Challenger 1 failed development. Richer Challenger 2 passed development but failed its one-shot 2023 confirmation. Both are closed without rescue tuning.

Key records:

- `docs/current-talent-results-only-baseline-freeze.md`
- `docs/current-talent-contact-value-confirmation-result.json`
- `docs/current-talent-challenger2-postmortem.md`

### Projection v1 batting rate/profile — DONE / FROZEN

Primary question:

> Does a simple leakage-safe population age/development adjustment improve next-season batting-profile prediction beyond carrying frozen Current Talent B2 forward unchanged?

Binding answer: **no** under the pre-registered development gate.

Retained Projection v1 rate model:

`frozen_current_talent_carry_forward_v1`

The explicit age/development challenger was selected using only 2022 target outcomes:

- selected form: `projection_age_level_ilr_ridge_v1`;
- selected ridge lambda: `0.01`;
- 2022 held-out selection log-loss delta vs carry-forward B2: **-0.001507130**;
- 2022 Brier delta: **-0.000294739**.

It then underwent fixed rolling-origin validation without reselection:

#### 2023 OOT validation — PASS

- candidate log loss: `2.253775007`;
- carry-forward B2: `2.254254788`;
- delta: **-0.000479781**;
- Brier delta: **-0.000000686**.

#### 2024 OOT validation — FAIL

Same form/lambda, refit on all chronologically prior 2022 + 2023 training observations:

- candidate log loss: `2.256561150`;
- carry-forward B2: `2.256304269`;
- delta: **+0.000256881**;
- Brier delta: **+0.000156946**.

The frozen development contract required lower log loss in **both** 2023 and 2024. The 2024 reversal is therefore binding: Projection Baseline 1 is rejected and cannot be rescued by tuning on 2024.

**2025 outcomes were never accessed.** No confirmation is authorized for the rejected challenger. Preserve 2025 as untouched evidence for a future separately pre-registered Projection challenger if useful.

Projection v1 governing/results records:

- `docs/projection-batting-v1-development-contract.md`
- `docs/projection-v1-methodology-review.md`
- `docs/projection-batting-v1-selection-result.json`
- `docs/projection-batting-v1-validation-2023-result.json`
- `docs/projection-batting-v1-validation-2024-result.json`
- `docs/projection-batting-v1-development-result.json`
- `docs/projection-batting-v1-development-checkpoint.md`

## Projection implementation/source status — COMPLETE

Key successful evidence/implementation gates:

- `32095039114` — certified 2024 affiliated MiLB evidence, all levels;
- `32096473700` — certified 2024 MLB v2 evidence;
- `32097702869` — complete corrected 2021–2024 Projection development surfaces;
- `32098903850` — deterministic ILR geometry fast CI;
- `32099637866` — frozen B2 snapshot reproduction fast CI;
- `32099733186` — real three-fold B2 October snapshot materialization;
- `32099909188` — pre-registered ridge primitive CI;
- `32100066442` — ILR training-response plumbing CI;
- `32100142102` — real three-fold training-response materialization;
- `32100338522` — frozen selection-rule CI;
- `32100650512` — corrected 2022-only candidate selection.

The 2024 validation result is self-persisted in `docs/projection-batting-v1-validation-2024-result.json`; its failed primary gate closes the explicit age/development challenger without further diagnostics/rescue search.

## ACTIVE NEXT STAGE — playing time / role

Batting-rate skill and opportunity now have a clean boundary:

- **rate/profile:** frozen Current Talent B2 carried forward one year;
- **opportunity/role:** not yet modeled and must be estimated separately.

The next stage should answer questions such as:

- probability a player receives MLB/affiliated batting opportunities over the target horizon;
- expected PA conditional/unconditional on role as appropriate;
- probability of MLB role / bench / regular / minors / no affiliated opportunity;
- how current level, age, roster/organizational context, recent playing time, injuries where legally/publicly supportable, and talent state should influence opportunity without contaminating batting-rate skill.

### Immediate next batch

1. Inventory existing repo work for playing time/role and avoid creating a parallel architecture if one already exists.
2. Re-read public baseball playing-time/projection methodology and relevant survival/hazard/zero-inflated/count-model literature before freezing the first contract.
3. Define the exact estimand(s), chronology, target grain, baseline, and validation/confirmation periods **before fitting/scoring**.
4. Keep rate skill fixed while this channel is developed; do not reopen Current Talent or the rejected Projection aging challenger.

## Governing read order

1. `docs/project-status.md`
2. `docs/projection-batting-v1-development-checkpoint.md`
3. `docs/projection-batting-v1-development-result.json`
4. `docs/projection-batting-v1-development-contract.md`
5. `docs/projection-v1-methodology-review.md`
6. `docs/current-talent-results-only-baseline-freeze.md`
7. `docs/current-talent-contact-value-confirmation-result.json`
8. `docs/current-talent-challenger2-postmortem.md`
9. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent or Projection v1 selection/validation absent a concrete implementation failure.
- Do not tune the rejected Projection age/development model on 2024 or expose 2025 as a rescue set.
- Preserve 2025 Projection outcomes as untouched evidence until a future challenger has its own predeclared contract.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Keep opportunity separate from rate skill.
- Update this handoff whenever the active stage or binding result changes.
