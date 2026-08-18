# Project status and handoff

Last updated: 2026-08-17 19:38 PT

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Branch: `source-certification-poc`
- Draft PR: **#1**
- Do not infer project state from `main`; the active branch is substantially ahead.
- Work in small verified batches and inspect the current branch head before editing.
- Prefer certified/reusable public data plus existing repo adapters over rebuilding source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, and Player Value / Overall Ranking separate.

## Stage summary

### Performance — completed for current downstream needs

Completed-2024 affiliated batting Performance materialization is production-shaped and retained for downstream reuse.

Primary checkpoint: `docs/performance-2024-affiliated-checkpoint.md`.

Do not reopen Performance/source-foundation work unless Projection exposes a concrete implementation or coverage failure.

### Current Talent — DONE / FROZEN

Universal results-only **Current Talent Baseline 2** is frozen and retained:

`translated_multiseason_recency_empirical_bayes_v1`

Frozen design:

- 1,095-day eligible results history
- 180-day exponential half-life
- EB prior strength 100 effective core events
- training-only MLB-anchored level translation
- frozen age/current-level Baseline 0 prior
- frozen 12-component profile
- 90-day future target used for Current Talent validation

Richer Challenger 1 failed fixed development and is closed.

Richer Challenger 2 (`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`) passed all frozen 2022 development gates but **failed the one-shot 2023 confirmation**. It improved MSE in all three confirmation folds but failed the predeclared MAE no-worse and calibration-intercept guardrails. Binding result: `confirmed = false`.

Do **not** tune, rescue, reselect, or rerun Challenger 2 against 2023. Do not integrate its scalar into Current Talent, Performance, Projection, WAR, Player Value, or Overall Ranking.

Key Current Talent records:

- `docs/current-talent-results-only-baseline-freeze.md`
- `docs/current-talent-contact-value-confirmation-result.json`
- `docs/current-talent-contact-value-confirmation-contract.md`
- `docs/current-talent-challenger2-postmortem.md`

Older Current Talent development/checkpoint files are historical evidence, not active tasks.

### Projection v1 — ACTIVE STAGE

Governing plan: `docs/projection-batting-v1-plan.md`.

Primary question:

> Does a simple leakage-safe age/development adjustment improve next-season batting-rate/profile prediction over carrying frozen Current Talent forward unchanged?

Projection v1 remains rate/profile only. Playing time/role, defense, WAR/value, and final ranking remain separate future channels.

Chronological design:

- `2021-10-15` snapshot -> 2022 outcomes
- `2022-10-15` snapshot -> 2023 outcomes
- `2023-10-15` snapshot -> 2024 outcomes
- **2025 regular-season outcomes remain quarantined as the untouched confirmation period**

No 2025 outcome table may be opened for feature choice, hyperparameter selection, threshold setting, rescue tuning, or development scoring.

## Projection implementation status

### Deterministic contracts / fast CI — PASSING

Recent successful gates include:

- `32089050302` — next-year dataset contract
- `32089669934` — Projection development-evidence materializer compiles in CI
- `32090401492` — exact-game fallback contract
- `32090635490` — exact-game league fallback contract
- `32090687671` — combined exact-game outcome + league fallback tests
- `32092505104` — exact source-residual quarantine policy in fast CI

The deterministic chronology/dataset/source-authority contracts are not the current blocker.

### 2024 MiLB historical evidence reuse/materialization — NOT YET CLEARED

Earlier historical-path runs failed:

- `32089284674` — certified historical Current Talent path for 2024 MiLB
- `32090307461` — exact-game official fallback rerun
- `32090635458` — exact-game league fallback rerun
- `32090668312` — both exact-game fallbacks rerun

The discrepancy has now been diagnosed and a fail-closed correction policy has been implemented; the full historical path still needs a clean rerun.

### Source discrepancy diagnosis — COMPLETE

Official-feed recovery run `32091704947` showed that `game_pk 755829` returns HTTP 404 from the expected Stats API `/feed/live` surface.

Source-only residual audit `32092166134` then passed and localized the observed aggregate mismatch to two exact source-only rows:

1. **High-A** — player `669233`, game `755829`: extra `PA=1, AB=1` row.
2. **Single-A** — player `686541`, game `754395`: extra `PA=1, AB=1, SO=1` row.

For each row, removing the exact suspect eliminates the season mismatch and makes the remaining player-game totals match official gameLog totals. Audit artifact `9308734004`, digest `sha256:574f6f7bd6eb0278ea3a654cb97762ce7fbed07c912e32261f2da5883435a466`.

### Exact source-residual quarantine — IMPLEMENTED / CI PASSED

Production helper:

`src/universal_baseball/current_talent_source_residual_quarantine.py`

Policy:

`single_source_only_exact_season_and_official_residual_v1`

The helper removes a row only when all of the following hold:

1. there is exactly one source-only positive-PA game for the player/league;
2. its PA/BB/HBP/SO vector exactly equals the independent season-player residual;
3. removing its complete PA/AB/BB/HBP/SO/SF/SH/CI vector makes the remaining player-game totals exactly equal the official gameLog aggregate.

Anything less remains unresolved. No identity, league, or outcome value is guessed or reassigned.

Fast CI run `32092505104` completed **successfully** with this policy and its regression tests included.

Machine-readable workflow snapshots:

- `docs/projection-status.json`
- `docs/projection-recovery-status.json`

## Immediate next action

1. Rerun the complete 2024 MiLB historical evidence/materialization path with `single_source_only_exact_season_and_official_residual_v1` active.
2. Require exact post-quarantine aggregate reconciliation and verify no additional unresolved source-only residuals appear.
3. Persist the clean certified 2024 artifact with quarantine provenance/metrics.
4. Materialize and chronology-verify the full 2022–2024 Projection development snapshot/outcome surfaces with explicit opportunity/censoring accounting.
5. Only then begin Projection Baseline 0 / Baseline 1 development scoring.

Do not jump ahead to the age curve or 2025 confirmation before the 2024 historical evidence rerun passes.

## Projection v1 model boundary already frozen

Baseline 0:

- carry frozen Current Talent Baseline 2 forward unchanged to the next season.

Baseline 1 starting family:

- learn one-year change in the common Current Talent profile;
- predictors available only at the October 15 snapshot;
- age + current level/environment + frozen Current Talent profile + evidence strength/uncertainty as needed;
- transparent, low-dimensional smoothing/pooling;
- no future level, role, playing time, tracking, scouting grades, or prospect rankings.

Before any 2025 scoring, freeze and persist the exact candidate forms, hyperparameter/search grid, promotion thresholds, calibration tolerances, and confirmation refit rule.

## Governing read order for a new chat

1. `docs/project-status.md`
2. `docs/projection-batting-v1-plan.md`
3. `docs/projection-recovery-status.json`
4. `docs/projection-status.json`
5. `docs/current-talent-results-only-baseline-freeze.md`
6. `docs/current-talent-contact-value-confirmation-result.json`
7. `docs/current-talent-challenger2-postmortem.md`
8. `docs/performance-2024-affiliated-checkpoint.md`
9. `docs/canonical-data-contract.md`
10. `docs/source-certification-current.md`

## Working rules

- Do not redo settled Current Talent selection/confirmation work absent a concrete implementation failure.
- Do not treat workflow failure alone as evidence for a broad rewrite; inspect the exact failing source contract first.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where their scope matches the Projection fold.
- Keep confirmation data quarantined until all development decisions are frozen.
- Update this handoff whenever the live blocker or recommended next batch changes.
