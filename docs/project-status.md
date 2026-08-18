# Project status and handoff

Last updated: 2026-08-17 19:28 PT

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

Recent successful fast-CI gates:

- `32089050302` — next-year dataset contract
- `32089669934` — Projection development-evidence materializer compiles in CI
- `32090401492` — exact-game fallback contract
- `32090635490` — exact-game league fallback contract
- `32090687671` — combined exact-game outcome + league fallback tests

The deterministic chronology/dataset/fallback contracts are not the current blocker.

### 2024 MiLB historical evidence reuse/materialization — NOT CLEARED

The heavy live-source path needed for the 2024 Projection development fold has not yet completed successfully.

Failed runs:

- `32089284674` — certified historical Current Talent path for 2024 MiLB
- `32090307461` — exact-game official fallback rerun
- `32090635458` — exact-game league fallback rerun
- `32090668312` — both exact-game fallbacks rerun

These failures are being treated as a source/integration problem to isolate, not as permission to bypass certification.

### Exact-game source-gap recovery — CONCRETE BLOCKER IDENTIFIED

Original dedicated audit run `32091086460` failed before completing the intended source inspection because of an import-path issue.

Recovery run `32091704947` fixed that import path and reached the live source. It then failed closed on the first concrete unresolved game:

- `game_pk = 755829`
- requested official live feed: `https://statsapi.mlb.com/api/v1/game/755829/feed/live`
- official response: **HTTP 404 Not Found**
- failure occurs in `capture_official_json()` because official snapshots require a successful 2xx response
- the recovery artifact was still uploaded: artifact `9308582512`, digest `sha256:a5847628722d0ae12e80ed90e649d20fd24e6195bf17b96fb61e681b35d273d2`

This is now the current source-gap boundary. The immediate problem is no longer a generic workflow failure: the historical 2024 path contains at least one game whose expected `/feed/live` surface is unavailable at that game ID.

Machine-readable workflow snapshots:

- `docs/projection-status.json`
- `docs/projection-recovery-status.json`

## Immediate next action

1. Inspect game `755829` across the official schedule/game metadata surfaces and the retained certified source artifact.
2. Determine whether the 404 represents an invalid/obsolete game ID, a game type without a live-feed surface, a historical Stats API availability gap, or a recoverable alternate official endpoint/representation.
3. Make the narrowest evidence-backed source-wrapper/materialization rule; do not silently drop the game.
4. Add a deterministic regression for that exact source condition.
5. Rerun the dedicated source-gap audit so it can continue beyond `755829`, then rerun the full 2024 MiLB historical evidence path.
6. Require a clean certified 2024 artifact before promoting it into Projection development evidence.
7. Only after all 2022–2024 development surfaces are complete and chronology-verified should Projection Baseline 0 / Baseline 1 scoring begin.

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
