# Project status and handoff

Last updated: 2026-08-18

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active development branch: `source-certification-poc`
- `source-certification-poc` contains newer work than the latest integration into `main`.
- Work in small verified batches.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, playing time, role/position allocation, defense, WAR/value, and final ranking separate.

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

Retained Projection v1 rate model:

`frozen_current_talent_carry_forward_v1`

The explicit age/development challenger was selected on 2022, passed fixed 2023 OOT validation, then failed the pre-registered 2024 OOT primary gate. That failure is binding; the challenger is closed without rescue tuning.

**Important outcome boundary:** 2025 batting-rate/profile outcomes were not accessed for Projection v1 and remain unavailable as a rescue set for the rejected challenger. The later Playing Time confirmation accessed only completed-2025 MLB plate-appearance opportunity outcomes under its own separately frozen contract.

Key Projection records:

- `docs/projection-batting-v1-development-contract.md`
- `docs/projection-v1-methodology-review.md`
- `docs/projection-batting-v1-selection-result.json`
- `docs/projection-batting-v1-validation-2023-result.json`
- `docs/projection-batting-v1-validation-2024-result.json`
- `docs/projection-batting-v1-development-result.json`
- `docs/projection-batting-v1-development-checkpoint.md`

### Playing Time v1 — DONE / FROZEN / CONFIRMED

Production model:

`playing_time_recent_opportunity_40man_b2_hurdle_v1`

Architecture:

- L2 logistic `P(next-season MLB PA > 0)`;
- zero-truncated NB2 positive MLB PA;
- unconditional expected opportunity from the two-part hurdle model.

The candidate was selected on 2022, passed fixed 2023 and 2024 OOT validation, was refit on all authorized 2022–2024 development responses, and had exact parameters/package versions frozen **before** 2025 source access.

2025 confirmation was then split into isolated gates:

1. pre-2025 frozen predictor/input gate — run `32144363818`;
2. completed-2025 MLB-PA source/target materialization with no model parameters loaded — run `32144918922`;
3. one-shot frozen B0-vs-candidate confirmation score — run `32146445795`.

Binding 2025 result on 3,759 snapshot players:

- candidate full hurdle NLL: `1.283609009`;
- B0 full hurdle NLL: `1.339572023`;
- delta: **`-0.055963014`**;
- candidate PA MAE: `30.6525` vs B0 `39.0475`;
- candidate participation log loss: `0.152517438` vs B0 `0.192781040`;
- candidate positive-count NLL: `6.422618149` vs B0 `6.511763297`;
- candidate participation Brier: `0.0451916` vs B0 `0.0593648`;
- calibration converged with finite parameters for both;
- **all six predeclared confirmation gates passed**.

No 2025 refit, reselection, recalibration, threshold change, or rescue tuning occurred.

Key records:

- `docs/playing-time-role-current-status.md`
- `docs/playing-time-role-v1-development-contract.md`
- `docs/playing-time-v1-development-result.json`
- `docs/playing-time-v1-confirmation-refit-result.json`
- `docs/playing-time-v1-confirmation-contract.md`
- `docs/playing-time-v1-confirmation-inputs-result.json`
- `docs/playing-time-v1-confirmation-target-result.json`
- `docs/playing-time-v1-confirmation-result.json`

## ACTIVE NEXT STAGE — role / position / team-allocation coherence

The model now has two frozen portable player channels:

- **batting rate/profile:** frozen Current Talent B2 carried forward one year;
- **individual MLB opportunity:** confirmed Playing Time v1 hurdle model.

Playing Time v1 intentionally does **not** force all individual expected PA forecasts into finite team/position totals. The next layer must address role/position/team coherence without reopening either frozen channel.

### Immediate next batch

1. Inventory existing repo/source support for chronology-safe player position, role, and team/organization association.
2. Define the exact coherence problem and downstream need: e.g. whether WAR/value requires a deterministic position/role allocation layer first, or whether a new statistical model is actually necessary.
3. Freeze inputs, outputs, chronology, constraints, and validation checks before fitting or allocating against future outcomes.
4. Prefer a transparent deterministic/coherence layer over a new predictive model if the downstream requirement can be satisfied without another statistical estimation problem.

Do **not** jump directly to WAR/value until the position/role assumptions required by defense and replacement-level/value calculations are explicit.

## Governing read order

1. `docs/project-status.md`
2. `docs/playing-time-role-current-status.md`
3. `docs/playing-time-v1-confirmation-result.json`
4. `docs/playing-time-v1-confirmation-contract.md`
5. `docs/playing-time-role-v1-development-contract.md`
6. `docs/projection-batting-v1-development-result.json`
7. `docs/projection-batting-v1-development-contract.md`
8. `docs/current-talent-results-only-baseline-freeze.md`
9. `docs/current-talent-contact-value-confirmation-result.json`
10. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent, Projection v1, or Playing Time v1 selection/validation/confirmation absent a concrete implementation failure.
- Do not tune the rejected Projection age/development model on 2024 or expose 2025 batting-rate outcomes as a rescue set.
- Do not refit/rescore Playing Time v1 against 2025; the one-shot confirmation is binding.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Keep batting-rate skill, opportunity, role/position allocation, defense, and value separate.
- Update this handoff whenever the active stage or binding result changes.
