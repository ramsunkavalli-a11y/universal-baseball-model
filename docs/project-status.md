# Project status and handoff

Last updated: 2026-08-17 19:25 PT

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

Primary checkpoint:

`docs/performance-2024-affiliated-checkpoint.md`

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

Governing plan:

`docs/projection-batting-v1-plan.md`

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

The Projection contract layer has advanced beyond pre-development planning. Recent successful fast-CI gates include:

- run `32089050302` — next-year dataset contract
- run `32089669934` — Projection development-evidence materializer compiles in CI
- run `32090401492` — exact-game fallback contract
- run `32090635490` — exact-game league fallback contract
- run `32090687671` — combined exact-game outcome + league fallback tests

This means the deterministic chronology/dataset/fallback contracts are not the current blocker.

### 2024 MiLB historical evidence reuse/materialization — NOT YET CLEARED

The heavy live-source path needed to reuse certified historical Current Talent evidence for the 2024 Projection development fold has not yet completed successfully.

Recent failed runs:

- `32089284674` — certified historical Current Talent path for 2024 MiLB
- `32090307461` — exact-game official fallback rerun
- `32090635458` — exact-game league fallback rerun
- `32090668312` — both exact-game fallbacks rerun

The failures are being treated as a source/integration issue to isolate, not as permission to bypass certification.

### Exact-game source-gap audit / recovery — CURRENT LIVE BLOCKER

The first dedicated audit run `32091086460` failed before completing the intended source inspection. A narrow recovery workflow corrected the interrupted import path and launched run:

`32091704947` — **Projection 2024 exact-game source-gap audit recovery**

As of this handoff timestamp, that run is **in progress**.

Machine-readable snapshots:

- `docs/projection-status.json`
- `docs/projection-recovery-status.json`

These workflow snapshots are generated status evidence; use this file for the human interpretation and next action.

## Immediate next action

1. Inspect the completed result/artifact from recovery run `32091704947`.
2. Identify the exact 2024 MiLB games/source surfaces that still fail the certified historical reuse path.
3. Make the narrowest source-wrapper/materialization correction supported by that evidence, with fast regression coverage.
4. Rerun the 2024 MiLB historical evidence path and require a clean certified artifact before promoting it into Projection development evidence.
5. Only after the 2022–2024 development evidence surfaces are complete and chronology-verified should Projection Baseline 0 / Baseline 1 development scoring begin.

Do not jump ahead to the age curve or 2025 confirmation while the 2024 evidence surface is unresolved.

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
