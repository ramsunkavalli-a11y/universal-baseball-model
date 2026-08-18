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
- Keep Performance, Current Talent, Projection, playing time, position/role, defense, WAR/value, and final ranking separate.

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

**Outcome boundary:** 2025 batting-rate/profile outcomes remain untouched for Projection v1. Later Playing Time and Position/Role confirmations opened only their separately frozen 2025 opportunity or position-role targets.

Key records:

- `docs/projection-batting-v1-development-contract.md`
- `docs/projection-v1-methodology-review.md`
- `docs/projection-batting-v1-selection-result.json`
- `docs/projection-batting-v1-validation-2023-result.json`
- `docs/projection-batting-v1-validation-2024-result.json`
- `docs/projection-batting-v1-development-result.json`

### Playing Time v1 — DONE / FROZEN / CONFIRMED

Production model:

`playing_time_recent_opportunity_40man_b2_hurdle_v1`

Architecture:

- L2 logistic `P(next-season MLB PA > 0)`;
- zero-truncated NB2 positive MLB PA;
- unconditional expected opportunity from the two-part hurdle model.

The candidate was selected on 2022, passed fixed 2023 and 2024 OOT validation, was refit on all authorized 2022–2024 development responses, and had exact parameters/package versions frozen **before** 2025 source access.

2025 confirmation was split into isolated gates:

1. pre-2025 frozen predictor/input gate — run `32144363818`;
2. completed-2025 MLB-PA source/target materialization with no model parameters loaded — run `32144918922`;
3. one-shot frozen confirmation score — run `32146445795`.

Binding 2025 result on 3,759 snapshot players:

- candidate full hurdle NLL: `1.283609009` vs B0 `1.339572023`;
- candidate PA MAE: `30.6525` vs B0 `39.0475`;
- candidate participation log loss: `0.152517438` vs B0 `0.192781040`;
- all six predeclared confirmation gates passed.

No 2025 refit, reselection, recalibration, threshold change, or rescue tuning occurred.

Key records:

- `docs/playing-time-role-current-status.md`
- `docs/playing-time-v1-confirmation-contract.md`
- `docs/playing-time-v1-confirmation-result.json`

### Position / Role v1 — DONE / FROZEN / CONFIRMED

Production model:

`primary_share_thresholded_transition_mean_v1`

Output is a portable nine-position batting-role profile across C, 1B, 2B, 3B, SS, LF, CF, RF, and DH. Pitcher usage stays outside the batting-role channel.

Source foundation:

- official Stats API `fielding` supplies explicit player × team × position games, games started, and innings, including explicit DH rows;
- 2021–2024 historical source certification passed **64/64 season × league pairs** with 100,166 canonical rows — run `32148467330`;
- 2025 confirmation source was materialized separately, **16/16 leagues**, 24,662 canonical rows, zero source errors — run `32153492066`.

Development path:

- raw year-to-year carry-forward was materially imperfect: pooled exact primary-position repeat `61.2%`, median full-profile TV distance `0.286`;
- a broad transition smoother improved SSE but worsened TV in both development folds and failed;
- its pre-specified postmortem showed smoothing was harmful below 0.65 current primary-position share and helpful at/above 0.65;
- final challenger froze exactly one change: carry forward when `s < 0.65`; otherwise use `s × current_profile + (1-s) × prior-history mean next profile by current primary position`;
- final challenger passed both development folds with no additional challenger authorized.

Before 2025 source access, all confirmation parameters were frozen from 2021–2024 evidence. Parameter hash:

`sha256:6b6cc7dd5cc7acb7d4396e60dccab12420fdb1828936a318383362d53a9e3def`

One-shot 2025 confirmation — run `32154031433`, 2,891 players:

- mean TV: `0.325526526` → `0.324624904` (**0.277% improvement**);
- mean summed squared error: `0.226924779` → `0.216389159` (**4.643% improvement**);
- primary-position match: `0.59530` → `0.59806` (diagnostic only);
- smoothing active for 1,403 / 2,891 players (`48.53%`);
- both binding gates passed.

No fitting function was called during confirmation; parameters were not refit; threshold/candidate were not changed or reselected. Additional 2025 tuning is prohibited.

Key records:

- `docs/position-role-historical-source-result.json`
- `docs/position-role-batting-profile-stability-result.json`
- `docs/position-role-transition-challenger-result.json`
- `docs/position-role-transition-challenger-diagnostic.json`
- `docs/position-role-selective-transition-result.json`
- `docs/position-role-2025-confirmation-contract.md`
- `docs/position-role-confirmation-parameters.json`
- `docs/position-role-2025-confirmation-source-result.json`
- `docs/position-role-2025-confirmation-result.json`

## ACTIVE NEXT STAGE — defense / defensive value design

The project now has three frozen portable player channels needed downstream:

- batting rate/profile;
- individual MLB opportunity;
- batting position/role profile.

A team allocator is **not** currently authorized or required merely to make those player-level channels coherent. The next unresolved value dependency is defensive contribution/quality: position/role tells us *where* a player is expected to play, not *how well* he fields there.

### Immediate next batch

1. Inventory mature public defensive datasets/packages already usable across MLB and affiliated minors before building any raw defensive-event parser.
2. Define the minimum downstream defensive output actually required for WAR/value, including how coverage gaps below MLB should be represented rather than guessed away.
3. Freeze source scope, chronology, positional grain, uncertainty/fallback rules, and validation gates before fitting a defensive projection.

Do **not** reopen Playing Time or Position/Role, and do not introduce team-level allocation unless a later WAR/value requirement demonstrates that it is necessary.

## Governing read order

1. `docs/project-status.md`
2. `docs/position-role-2025-confirmation-result.json`
3. `docs/position-role-2025-confirmation-contract.md`
4. `docs/position-role-confirmation-parameters.json`
5. `docs/position-role-historical-source-result.json`
6. `docs/playing-time-role-current-status.md`
7. `docs/playing-time-v1-confirmation-result.json`
8. `docs/projection-batting-v1-development-result.json`
9. `docs/current-talent-results-only-baseline-freeze.md`
10. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent, Projection v1, Playing Time v1, or Position/Role v1 selection/validation/confirmation absent a concrete implementation failure.
- Do not tune the rejected Projection age/development model on 2024 or expose 2025 batting-rate outcomes as a rescue set.
- Do not refit/rescore Playing Time v1 or Position/Role v1 against their 2025 confirmation targets; those one-shot decisions are binding.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Keep batting-rate skill, opportunity, position/role, defense, and value separate.
- Update this handoff whenever the active stage or binding result changes.
