# Playing time / role — current status

Last updated: 2026-08-17

Status: **ACTIVE — PRE-REGISTERED DEVELOPMENT CHAIN LAUNCHED; 2025 REMAINS UNTOUCHED.**

Canonical broader handoff remains `docs/project-status.md`.

## Frozen upstream state

- Current Talent: `translated_multiseason_recency_empirical_bayes_v1`.
- One-year batting-rate Projection: `frozen_current_talent_carry_forward_v1`.
- Explicit Projection age/development challenger is closed and must not be rescued.
- Playing time is a separate opportunity channel; zero future MLB PA never changes batting-rate skill.

## Methodology

Governing review:

`docs/playing-time-role-methodology-review.md`

Key architecture:

1. model `P(next-season MLB PA > 0)` separately from positive PA amount;
2. use a zero-truncated NB2 positive-count component;
3. evaluate the resulting full hurdle distribution;
4. keep team/role allocation separate from individual portable opportunity;
5. use historical roster facts only when exactly reproducible.

## Target feasibility — PASS

Binding target result:

`docs/playing-time-v1-target-surface-result.json`

Target:

`next-calendar-year regular-season MLB PA`

including explicit zero for every frozen B2 October snapshot player.

Observed development distribution:

- `2021 -> 2022`: 4,702 players; 85.43% zero MLB PA; positive PA mean 264.7; positive variance/mean 170.7.
- `2022 -> 2023`: 4,040 players; 84.06% zero; positive mean 282.4; variance/mean 165.3.
- `2023 -> 2024`: 3,985 players; 83.81% zero; positive mean 280.9; variance/mean 166.8.

This is the empirical reason v1 uses a two-part/hurdle architecture instead of one all-player PA regression.

## Historical 40-man source — PASS FOR MEMBERSHIP ONLY

Initial raw-row audit exposed one exact source anomaly: team 121 (Mets) duplicated José Buttó in both 2022 and 2023 `40Man` responses with the same identity/team membership but conflicting row-level statuses (`Active` and `Reassigned to Minors`).

Diagnostic:

`docs/playing-time-roster-duplicate-diagnostic-result.json`

The source rule was therefore narrowed and certified as:

**authorized:** binary `on_40man` membership at the exact snapshot date.

**not authorized from the 40Man response:** active/minors assignment, IL status, option status, future role.

Final certification:

`docs/playing-time-historical-40man-membership-result.json`

It passed across all 30 MLB teams at all three Oct. 15 development snapshots, with historical date sensitivity proven and no cross-team membership conflict.

## Frozen development contract

`docs/playing-time-role-v1-development-contract.md`

Target folds:

- `2021-10-15 -> 2022`: candidate selection only;
- `2022-10-15 -> 2023`: OOT validation 1;
- `2023-10-15 -> 2024`: OOT validation 2;
- `2024-10-15 -> 2025`: untouched confirmation only after full development promotion + exact refit freeze.

Model family:

- participation: L2 logistic, fixed `C=1.0`;
- positive PA: zero-truncated NB2 (`p=2`);
- primary score: full hurdle negative log likelihood per snapshot player.

Frozen nested forms:

1. `playing_time_level_hurdle_v1` — level tier only (B0);
2. `playing_time_recent_opportunity_hurdle_v1` — + age/current MLB PA/current MiLB PA;
3. `playing_time_recent_opportunity_40man_hurdle_v1` — + certified binary 40-man membership;
4. `playing_time_recent_opportunity_40man_b2_hurdle_v1` — + compact frozen-B2 skill summary.

No prior-season PA feature is allowed because the 2021 selection snapshot lacks a certified pre-2021 universal season.

## Implementation

Pre-model/model primitives:

- `src/universal_baseball/playing_time_roster_source.py`
- `src/universal_baseball/playing_time_model.py`
- `src/universal_baseball/playing_time_selection.py`
- `scripts/materialize_playing_time_v1_target_surface.py`
- `scripts/materialize_playing_time_v1_predictor_surface.py`
- `scripts/materialize_playing_time_v1_candidate_selection.py`
- `scripts/materialize_playing_time_v1_validation_2023.py`
- `scripts/materialize_playing_time_v1_validation_2024.py`
- `scripts/fit_playing_time_v1_confirmation_refit.py`

Pinned modeling dependencies:

`requirements-playing-time.txt`

The synthetic model-contract gate self-persists to:

`docs/playing-time-v1-model-contracts-ci-result.json`

## Binding development workflow chain

1. `playing-time-v1-candidate-selection.yml`
   - refuses to run unless the synthetic model-contract gate is green;
   - rebuilds the source-safe predictor/target surfaces from pinned evidence;
   - re-certifies exact historical binary 40-man membership;
   - scores **2022 only** using deterministic five-fold player-held-out CV;
   - persists `docs/playing-time-v1-selection-result.json`.

2. `playing-time-v1-validation-2023.yml`
   - if B0 was selected, closes without 2023 candidate scoring;
   - otherwise fits the frozen selected form on 2022 responses and scores 2023 once;
   - persists `docs/playing-time-v1-validation-2023-result.json`.

3. `playing-time-v1-validation-2024.yml`
   - checks the binding 2023 result **before downloading any artifact containing 2024 candidate outcomes**;
   - if 2023 does not authorize 2024, writes a skipped closeout result with `2024_candidate_scores_accessed=false`;
   - otherwise runs the fixed rolling-origin 2024 gate and all predeclared promotion diagnostics;
   - persists `docs/playing-time-v1-validation-2024-result.json`.

4. `playing-time-v1-development-closeout.yml`
   - if development fails, freezes B0 and stops;
   - if development passes, refits the exact selected model on all authorized 2022–2024 response folds, verifies deterministic parameter reproduction, and freezes package versions/parameters before 2025;
   - persists `docs/playing-time-v1-development-result.json` and `docs/playing-time-v1-development-checkpoint.md`;
   - only a passed, frozen refit can authorize a later 2025 source/materialization gate.

## Hard boundary

**2025 opportunity outcomes have not been accessed.**

Do not create/materialize the 2025 playing-time target unless `docs/playing-time-v1-development-result.json` explicitly shows development promotion passed and the confirmation refit is frozen.

Do not tune a failed feature form on 2023/2024. Do not infer roster status beyond binary 40-man membership from the certified source.
