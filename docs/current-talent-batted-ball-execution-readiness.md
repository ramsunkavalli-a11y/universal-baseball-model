# Current Talent batted-ball execution readiness

Last updated: 2026-08-17  
Status: **AUTHORITATIVE EXECUTION NOTE FOR THE FIRST RICHER CHALLENGER.**

This note records workflow-level corrections discovered before any richer 2022 development score was observed. The frozen feature family, model form, training chronology, regularization, comparator and promotion rules have not changed.

## Use this workflow chain

1. `.github/workflows/current-talent-savant-minors-probe.yml`
2. `.github/workflows/current-talent-batted-ball-tracking-materialization-v2.yml`
3. `.github/workflows/current-talent-batted-ball-development.yml`

Do **not** run `.github/workflows/current-talent-batted-ball-tracking-materialization.yml`. It is superseded by V2.

## Current live-gate state

Manual probe run `32043825707` completed successfully at the GitHub Actions level, but artifact inspection found that its reports were still schema `0.4` and did not contain the frozen certified-game coverage denominator.

Therefore **run 32043825707 is not an accepted source-gate artifact**.

The mismatch was caught before:

- historical MiLB tracking materialization;
- real EV/sweet-spot coefficient fitting;
- any 2022 richer proper-score result.

The corrected probe now emits schema `0.5` and must be rerun fresh.

A valid corrected probe artifact requires all three 2021/2022/2023 reports to contain:

- `report_schema_version = 0.5`;
- `request_semantics = tracked_only_helper_v1`;
- `canonical_model_bbe_contract = result_producing_non_bunt_pitch_grain_v1`;
- nonzero `certified_game_tracking_coverage.certified_game_count`;
- nonzero `certified_game_tracking_coverage.tracked_game_count`;
- nonzero canonical model BBE.

Only after that artifact is reviewed should V2 run.

## Why V2 is required

The first tracking-materialization workflow was briefly narrowed to capture 2021 MiLB only through `2021-07-14`, on the theory that this was sufficient for the fixed `2021-07-15` residual-training snapshot.

That is insufficient for the full development protocol because the 2022 folds are explicitly allowed to use **prior-season 2021 tracking evidence** with continuous 180-day recency decay. A July-only 2021 MiLB capture would discard legitimate second-half 2021 MiLB evidence while retained MLB tracking still contains the full 2021 season, creating an unintended source-family asymmetry.

V2 therefore captures the complete certified 2021 MiLB season.

## V2 source gate

`current-talent-batted-ball-tracking-materialization-v2.yml`:

- hard-requires the corrected schema-0.5 probe artifact;
- reuses retained certified 2021/2022 MLB Savant raw caches;
- captures the **full certified 2021 MiLB season**;
- captures 2022 MiLB through `2022-08-31` for the final `2022-09-01` development cutoff;
- uses bounded retries for transient GitHub artifact-download and Savant transport failures;
- retains exact raw Savant bytes, request URLs and hashes;
- keeps broad measurement completeness separate from canonical model BBE;
- measures returned tracked-source games against the certified game universe;
- emits checkpoint schema `0.3` with:
  - `workflow_contract = full_2021_prior_season_v2`;
  - `tracking_source_epoch = 2021-01-01`;
  - `prior_season_2021_complete = true`;
  - corrected canonical BBE marker;
  - combined 2021/2022 MLB + tracked-MiLB source surfaces;
- stops before model scoring.

The workflow dispatcher is present on `main`, but the job explicitly checks out `source-certification-poc`; this does not merge the project branch.

## Tracking history boundary

The richer challenger source epoch is frozen at `2021-01-01` in `docs/current-talent-batted-ball-tracking-history-contract.md`.

- 2021 training uses only rows strictly before `2021-07-15`.
- 2022 development may use all eligible 2021 tracked evidence plus 2022 evidence strictly before each cutoff.
- The 180-day decay continues across the season boundary.
- No pre-2021 MLB Statcast enters this challenger.

Capturing full 2021 source history does **not** leak later 2021 rows into the training snapshot because the feature builder enforces `game_date < as_of_date`.

## Certified-game coverage denominator

A tracked-only Savant query can look nearly complete among returned rows while omitting entire untracked games. Row-level EV/LA completeness is therefore insufficient to describe historical coverage.

The shared source diagnostic now compares:

- `certified_game_count`: unique games in the already-certified game universe for the relevant date window;
- `returned_source_game_count`: unique game PKs present anywhere in the tracked-only Savant response;
- `tracked_game_count`: returned source games that match the certified game universe;
- `unmatched_source_game_count`: returned source games absent from that certified universe;
- `tracked_game_share = tracked_game_count / certified_game_count`.

The same denominator is also emitted by certified season/league/level.

For the tiny probe, the certified universe is restricted to the exact probe date. For the 2022 historical development capture, it is restricted through `2022-08-31`; later certified September games are not incorrectly counted as missing tracking.

This diagnostic measures source capability only. It does not create an eligibility threshold and never promotes an entire level from partial tracked evidence.

## Development workflow input

Run `.github/workflows/current-talent-batted-ball-development.yml` only with a `tracking_materialization_run_id` produced by **V2**.

The development evaluator remains offline:

- fixed 2021-07-15 training snapshot;
- fixed L2 = 0.01;
- fixed 2022-07-15 / 08-01 / 09-01 folds;
- frozen B2 comparator;
- existing target-environment projection and proper-score machinery;
- no 2023 input or confirmation scoring.

## Exact next action

Run a **fresh** `Current Talent Minor League Savant probe` from GitHub Actions. Do not reuse or rerun run `32043825707` as the accepted artifact. After the fresh run completes, inspect its three reports for the schema-0.5 contract above. If and only if they pass, run `Current Talent batted-ball tracking materialization v2` using that new probe run ID.
