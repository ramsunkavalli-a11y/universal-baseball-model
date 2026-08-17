# Project status and handoff

Last updated: 2026-08-17

This is the **start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is used only for small manual workflow dispatchers when needed; source/model development remains on `source-certification-poc`.
- Inspect the current branch head before editing.

## Working rules

- Work in small batches of roughly 2–3 steps and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding raw-source cleanup.
- Surface source/model errors early.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Never retune frozen Baseline 2 to rescue a richer challenger.
- Do not impute structurally unavailable tracking evidence.
- Keep live-source capture separate from deterministic evaluation.
- **Do not inspect 2023 richer performance unless the exact candidate first passes its frozen 2022 development gate.**

## Current stage

The universal results-only **Current Talent Baseline 2 is frozen and remains the production comparator/fallback**.

Richer challenger 1 completed its fixed 2022 development gate and **failed**. It is closed; no 2023 confirmation is authorized.

Richer challenger 2 has now been **predeclared and frozen before any new 2022 score exists**:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

Governing plan:

`docs/current-talent-batted-ball-contact-value-challenger-plan.md`

The immediate gate is **2021 pre-cutoff Retrosheet contact-value-scale source feasibility**. Do not implement or run the 2022 challenger-2 evaluator until that source/value-scale gate passes and deterministic fitting primitives are tested.

## Frozen Current Talent Baseline 2

Method:

`translated_multiseason_recency_empirical_bayes_v1`

- up to 1,095 days of eligible results history;
- 180-day exponential recency half-life;
- empirical-Bayes prior strength 100 effective core events;
- fitted training-only MLB-anchored environment translation;
- frozen age/current-level Baseline 0 prior;
- frozen 12-component Current Talent profile;
- 90-day future target.

B2 beat B1 on all six frozen development/confirmation folds for both log loss and Brier.

Key freeze:

`docs/current-talent-results-only-baseline-freeze.md`

## Certified richer source layer — complete and reusable

### Minor Savant probe

Authoritative run: **`32044627608`**

Accepted contract:

- report schema `0.5`;
- `request_semantics = tracked_only_helper_v1`;
- canonical BBE contract `result_producing_non_bunt_pitch_grain_v1`;
- certified-game denominator present;
- 100% returned game+batter identity reconciliation on all three fixed probe dates;
- nonzero canonical BBE.

Checkpoint:

`docs/current-talent-savant-minors-source-checkpoint.md`

### Historical tracking materialization V2

Authoritative run: **`32046012977`**, attempt 2.

Checkpoint:

- schema `0.3`;
- `workflow_contract = full_2021_prior_season_v2`;
- source epoch `2021-01-01`;
- full 2021 prior season through `2021-10-03`;
- 2022 development history through `2022-08-31`;
- `prior_season_2021_complete = true`;
- `development_tracking_ready = true`;
- zero unmatched returned source games.

Combined canonical tracked BBE:

- 2021: **142,201**
- 2022: **164,689**

Coverage remains capability-limited. In particular, do not convert 2022 `AAA` into a blanket tracked capability flag; league/venue coverage is materially uneven.

## Source-contract corrections already resolved

### Canonical tracked BBE

- valid game/batter/PA/pitch identity;
- Savant `type == X`;
- nonblank terminal `events`;
- complete EV + launch angle;
- explicit bunt exclusion;
- key `game_pk + player_id + at_bat_number + pitch_number`;
- duplicate pitch key or multiple result BBE in one PA fails closed.

Broad source-completeness diagnostics may include measured foul/contact observations; model BBE do not.

### MLB game coverage

Interleague games legitimately carry both AL/NL player-level league IDs. Game-coverage diagnostics collapse MLB to one game-level MLB bucket while player-level league provenance remains intact elsewhere. MiLB ambiguity still fails closed.

### MiLB regular-season scope

The first full 2021 capture revealed exactly 134 otherwise-valid BBE from three `game_type = W` postseason/championship games. Historical Minor Savant requests now include `hfGT=R|`, and the capture fails if returned rows are not regular-season type `R`.

## Richer challenger 1 — CLOSED / REJECTED

Method:

`baseline2_plus_ev_sweet_spot_contact_residual_v1`

Development workflow run: **`32053829482`**

Persisted result:

- `docs/current-talent-batted-ball-development-checkpoint.md`
- `docs/current-talent-batted-ball-development-result.json`

Frozen features were 180-day weighted mean EV + 8–32 degree sweet-spot share, >=20 tracked BBE, fixed L2 0.01, 2021-07-15 training only, and 2022-07-15 / 08-01 / 09-01 development folds.

Equal-fold means:

| Model | Log loss | Brier |
|---|---:|---:|
| B2 | 2.267336438 | 0.872739291 |
| richer 1 | 2.267363114 | 0.872744733 |

Richer 1 was worse on both means and won log loss only 1/3 folds.

Any-observed-MiLB cohort also worsened. Exact tier `MILB_SAVANT_TRACKED:2022:117:AAA` had 21,520 future core events and was worse on both log loss and Brier in 3/3 folds, triggering the frozen transport failure rule.

Calibration and optimizer checks passed, so this was a predictive/transport rejection rather than a pipeline failure.

**Do not tune or rerun this candidate and do not create its 2023 confirmation.**

## Richer challenger 2 — FROZEN, NOT YET SCORED

Governing plan:

`docs/current-talent-batted-ball-contact-value-challenger-plan.md`

Method label:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

### Interpretation

B2's 12-component probability vector remains unchanged. The new candidate tests whether the same observed EV + sweet-spot features predict a **separate scalar contact-value residual after conditioning on contact shape and level**.

This is a new candidate, not a repair of challenger 1.

### Frozen features

- 180-day recency-weighted mean EV;
- 180-day recency-weighted sweet-spot share, LA 8–32 degrees;
- >=20 complete canonical tracked BBE;
- source epoch `2021-01-01`;
- no imputation and no new feature search.

### Frozen terminal groups

- `1B`
- `2B`
- `3B`
- `HR`
- `ROE`
- `FC_REACH`
- `SF`
- `MULTI_OUT`
- `OUT`

Bunts and unsupported/special outcomes are outside the target. Mapping must fail closed before scoring.

### Frozen MLB-scale value table

Use Retrosheet 2021 MLB regular-season state transitions **strictly before 2021-07-15**:

1. estimate the project's canonical 24-state run-expectancy matrix from that pre-cutoff sample;
2. attach contextual RE24;
3. take event-weighted mean RE24 within each frozen terminal group;
4. freeze those nine group values for all 2022 development folds.

Actual per-event RE24 is not treated as player talent; RE24 is used only to create a context-neutral terminal-outcome value scale.

### Frozen conditional comparator

At each snapshot, fit pre-cutoff-only additive OLS:

`terminal_value ~ contact_bin + level_group`

- reference bin `IFFB`;
- reference level `MLB`;
- intercept;
- no interactions, player terms, shrinkage, regularization or search.

This is a controlled evaluation baseline, not a replacement for B2.

### Frozen richer fit

Training snapshot: `2021-07-15` only.

`player_contact_value_residual = beta_EV * z_EV + beta_SS * z_SS`

- no intercept;
- no interactions;
- no regularization/search;
- player-weighted least squares with weight = supported future target contacts;
- finite full-rank solution required.

Evaluate unchanged on 2022-07-15 / 08-01 / 09-01.

Primary score is event-weighted MSE; MAE is the secondary guardrail. The full promotion and MiLB transport rules are frozen in the challenger plan.

**No 2022 challenger-2 score exists yet. No 2023 data may enter.**

## Retrosheet feasibility implementation now in progress

Retrosheet's parsed play table already contains the exact narrow surface needed for the value-scale gate: date/game type, PA result flags, BIP/bunt flags, and explicit pre/post base-out states. The repo now has a chronology-aware projection rather than parsing raw Retrosheet event strings.

Implemented:

- `src/universal_baseball/retrosheet.py`
  - pre-cutoff regular-season contact-value transition projection;
  - frozen nine-group mapping from parsed outcome flags;
  - unsupported target contacts remain visible/fail-closed;
- `tests/test_retrosheet.py`
  - cutoff and game-type checks;
  - frozen group mapping checks;
  - unsupported and bunt handling;
- `scripts/audit_current_talent_contact_value_scale.py`
  - downloads only the public 2021 Retrosheet parsed-play archive;
  - uses no 2022/2023 input;
  - requires all 24 states;
  - requires zero unsupported target contacts and complete RE24 coverage;
  - emits the frozen nine-value table only on success;
  - performs no player/model scoring.

Manual dispatcher exposed on `main`:

`Current Talent contact-value scale audit`

## Reuse inventory for challenger 2

Prefer:

- existing Retrosheet state-transition adapter and `run_expectancy.py`;
- existing B2/Performance core contact-bin classification;
- public `armstjc/milb-data-repository` historical 2021/2022 PBP assets rather than rebuilding MiLB raw-source cleanup;
- tracking materialization run `32046012977` for EV/LA features and capability provenance;
- existing certified 2021/2022 Current Talent results evidence;
- current Performance bin-value/state logic where semantics match.

Do not reuse challenger 1's rejected 20-coefficient contact-probability residual as challenger 2's model form.

## Exact next batch

1. Run and inspect **Current Talent contact-value scale audit**. If it fails, diagnose source/mapping coverage before changing the frozen target contract.
2. If the scale gate passes, persist its exact nine values + source digest and implement deterministic additive `contact_bin + level_group` OLS plus two-feature no-intercept weighted residual fitting and tests.
3. Only after those deterministic tests pass, build the offline 2022 challenger-2 evaluator. **Do not touch 2023.**

## Governing docs for a new chat

Read in this order:

1. `docs/project-status.md`
2. `docs/current-talent-batted-ball-contact-value-challenger-plan.md`
3. `docs/current-talent-batted-ball-development-checkpoint.md`
4. `docs/current-talent-batted-ball-development-result.json`
5. `docs/current-talent-batted-ball-quality-challenger-plan.md`
6. `docs/current-talent-batted-ball-development-execution-contract.md`
7. `docs/current-talent-batted-ball-tracking-history-contract.md`
8. `docs/current-talent-savant-minors-source-checkpoint.md`
9. `docs/current-talent-results-only-baseline-freeze.md`
10. `docs/current-talent-validation-contract.md`

Do not redo B1/B2 selection or challenger-1 development absent a concrete implementation bug.
