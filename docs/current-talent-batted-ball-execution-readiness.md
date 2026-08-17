# Current Talent batted-ball execution readiness

Last updated: 2026-08-17  
Status: **AUTHORITATIVE EXECUTION NOTE FOR THE FIRST RICHER CHALLENGER.**

This note exists because the failure-mode review caught one workflow-level history truncation after the original tracking-materialization workflow had already been created. The model plan itself did not change.

## Use this workflow chain

1. `.github/workflows/current-talent-savant-minors-probe.yml`
2. `.github/workflows/current-talent-batted-ball-tracking-materialization-v2.yml`
3. `.github/workflows/current-talent-batted-ball-development.yml`

Do **not** run `.github/workflows/current-talent-batted-ball-tracking-materialization.yml` for the development gate. It is superseded by the V2 workflow below.

## Why V2 is required

The first tracking-materialization workflow was briefly narrowed to capture 2021 MiLB only through `2021-07-14`, on the theory that this was sufficient for the fixed `2021-07-15` residual-training snapshot.

That is insufficient for the full development protocol because the 2022 folds are explicitly allowed to use **prior-season 2021 tracking evidence** with continuous 180-day recency decay. A July-only 2021 MiLB capture would discard legitimate second-half 2021 MiLB evidence while retained MLB tracking still contains the full 2021 season, creating an unintended source-family asymmetry.

The V2 workflow corrects this before any richer development score is observed.

## V2 source gate

`current-talent-batted-ball-tracking-materialization-v2.yml`:

- requires a successful corrected Minor Savant probe artifact with report schema `0.5`;
- requires `tracked_only_helper_v1` request semantics;
- requires corrected model-BBE contract `result_producing_non_bunt_pitch_grain_v1`;
- requires a certified-game coverage denominator from the tiny probe;
- reuses retained certified 2021/2022 MLB Savant raw caches;
- captures the **full certified 2021 MiLB season**;
- captures 2022 MiLB through `2022-08-31`, sufficient for the final `2022-09-01` development cutoff;
- measures returned source games against the certified game universe by league/level;
- keeps broad measurement completeness separate from canonical model BBE;
- emits the same artifact name expected by the existing development workflow;
- writes checkpoint schema `0.3` with:
  - `workflow_contract = full_2021_prior_season_v2`;
  - `tracking_source_epoch = 2021-01-01`;
  - `prior_season_2021_complete = true`;
  - corrected canonical BBE marker;
  - combined 2021/2022 MLB + tracked-MiLB source surfaces.

## Tracking history boundary

The richer challenger source epoch is frozen at `2021-01-01` in `docs/current-talent-batted-ball-tracking-history-contract.md`.

- 2021 training uses only pre-`2021-07-15` rows because the feature cutoff is strict.
- 2022 development may use all eligible 2021 tracked evidence plus 2022 evidence strictly before each cutoff.
- The 180-day decay continues across the season boundary.
- No pre-2021 MLB Statcast enters this challenger.

Capturing full 2021 source history does **not** leak later 2021 rows into the 2021 training snapshot because `build_batted_ball_quality_features` enforces `game_date < as_of_date`.

## Partial-league coverage denominator

A tracked-only request can look nearly complete among returned rows while omitting many untracked games. The source materialization now reports, by certified season/league/level:

- certified game count;
- returned tracked-source game count;
- unreturned certified game count;
- returned-source game share;
- games with at least one canonical model BBE;
- canonical model-BBE game share.

This is the required denominator for 2022 partial AAA coverage. Capability remains an observed-source property; an entire level is never promoted merely because tracked rows were returned.

## Development workflow input

Run `.github/workflows/current-talent-batted-ball-development.yml` only with a `tracking_materialization_run_id` produced by the **V2** tracking workflow.

The development evaluator itself remains offline and unchanged:

- fixed 2021-07-15 training snapshot;
- fixed L2 = 0.01;
- fixed 2022-07-15 / 08-01 / 09-01 folds;
- same frozen B2 comparator;
- same target-environment projection and scoring machinery;
- no 2023 input or confirmation scoring.

## Verification boundary

These workflows are prepared but have not been executed in the current session. Actions/check reads and workflow dispatch remain unavailable through the connected integration here.

Do not call any new source gate, real richer fit, or 2022 richer proper-score result complete until the manual workflow chain above actually runs and its artifacts are reviewed.
