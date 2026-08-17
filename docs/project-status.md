# Project status and handoff

Last updated: 2026-08-17

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind.
- Inspect the current branch head before editing; parallel work can land independently.

## Execution rules

- Work in small batches of roughly 2–3 steps and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding source cleanup.
- Surface source/model errors early rather than compounding them.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Do not retune a frozen baseline in response to a richer challenger.
- Do not fabricate/impute structurally unavailable tracking evidence merely to keep a richer model universal.
- Keep live-source acquisition separate from deterministic model evaluation.
- Do not inspect 2023 richer performance unless the 2022 development checkpoint is reviewed, committed, and explicitly passes every frozen gate.

## Current stage

The universal results-only **Current Talent Baseline 2 is frozen**. The first richer-evidence challenger is fully predeclared and its source, feature, fit, scoring, and workflow contracts are now implemented.

**The only open execution gate is the corrected tiny tracked-only Minor League Savant probe.**

Do not skip it. Nothing in the current branch authorizes bulk historical MiLB tracking capture or 2022 richer scoring until that probe is rerun successfully under the corrected BBE contract.

Frozen universal comparator / fallback:

**Baseline 2 — `translated_multiseason_recency_empirical_bayes_v1`**

- up to **1,095 days** of eligible player results history;
- **180-day** exponential recency half-life;
- **100 effective core events** of empirical-Bayes prior strength;
- fitted training-only MLB-anchored environment translation;
- frozen age + current-level Baseline 0 prior;
- frozen 12-component Current Talent profile and 90-day future target.

B2 passed 2022 development and fixed 2023 confirmation. Across six folds it beat B1 **6/6 on log loss and 6/6 on Brier**.

Key freeze: `docs/current-talent-results-only-baseline-freeze.md`.

## First richer challenger — frozen design

Governing plan: `docs/current-talent-batted-ball-quality-challenger-plan.md`.

Execution definitions: `docs/current-talent-batted-ball-development-execution-contract.md`.

Source-semantic checkpoint: `docs/current-talent-batted-ball-source-semantics-checkpoint.md`.

### Evidence family

Only two richer features in this gate:

1. **180-day recency-weighted mean exit velocity**;
2. **180-day recency-weighted sweet-spot share**, launch angle **8–32 degrees inclusive**.

Primary richer eligibility:

**>=20 complete observed result-producing, non-bunt EV+LA BBE before the cutoff.**

Sensitivity cohorts at >=10 / >=20 / >=30 are diagnostic only. Do not tune the threshold from development or confirmation results.

Explicitly outside this gate:

- hard-hit / barrel / xwOBA composites;
- EV90 / max EV;
- bat speed / swing length;
- chase / whiff / pitch-process models;
- scouting grades / prospect rankings;
- Projection / aging;
- playing time;
- defense;
- WAR / final ranking.

### Model form

EV/LA may change only B2's **ten conditional non-bunt contact bins**.

- B2 `BB_HBP` stays exactly unchanged.
- B2 `K` stays exactly unchanged.
- Condition B2 on the ten contact bins.
- Add the standardized EV / sweet-spot residual in latent logit space.
- Renormalize the ten bins.
- Preserve total B2 contact probability mass.
- Missing/ineligible tracking => **exact B2 fallback**.

Method label:

`baseline2_plus_ev_sweet_spot_contact_residual_v1`

### Target-environment-aware fitting

The residual is fit against future contact outcomes only, but the likelihood respects the environment where those outcomes occurred:

1. start from B2 latent conditional-contact probabilities;
2. add the already-fitted training-only target-level CLR environment effect;
3. renormalize across the ten contact bins;
4. add EV / sweet-spot residual coefficients;
5. score against future contact-bin counts.

Do not fit directly to raw future contact shares without target-environment translation.

### Regularization

- shared fixed L2 = **0.01** on mean per-contact negative log likelihood;
- no penalty search;
- deterministic dependency-light optimizer;
- no development/confirmation outcome-driven tuning.

## Important source-semantic correction — closed before development

The first implementation incorrectly treated every complete Savant EV+LA contact row as a model BBE and keyed it at:

`game_pk + player_id + at_bat_number`

Inspection of the **exact retained certified 2021 MLB Savant raw source cache**, before any richer development scoring, showed that Savant also reports EV/LA on foul contacts. Many plate appearances therefore contain several complete EV/LA contact rows before the eventual in-play result.

The corrected model-BBE contract is now frozen:

- valid game / batter / PA / pitch identity;
- normalized Savant `type == X`;
- nonblank terminal `events`;
- observed `launch_speed`;
- observed `launch_angle`;
- explicit bunt narratives excluded because the frozen ten-bin contact target is non-bunt contact;
- canonical key = **`game_pk + player_id + at_bat_number + pitch_number`**;
- fail on duplicate result-producing pitch key;
- fail on multiple result-producing BBE in one player/PA.

This was a source-semantics/evidence-target correction, **not** a feature search. It happened before any 2022 richer proper score was observed and did not change the feature family, >=20 threshold, model form, chronology, L2, or promotion rules.

Broad source-capability diagnostics remain intentionally wider than model BBE and may include measured foul/contact rows. They operate at pitch grain and call those rows **observations**, not model BBE.

## Source-only feasibility under corrected semantics

A reproducible source audit exists at:

`scripts/audit_current_talent_batted_ball_source_semantics.py`

Using retained certified MLB source bytes only, with **no richer fitting or scoring**:

### 2021-07-15

- corrected model BBE: **65,578**
- hitters with any BBE: **797**
- hitters >=20 BBE: **497**
- median raw BBE among eligible: **116**
- median 180-day-effective BBE: **94.47**
- result bunts excluded: **776**
- complete EV/LA foul contacts observed: **60,493**
- duplicate corrected pitch keys: **0**
- multiple result BBE in one PA: **0**

### 2022 development cutoffs

| Cutoff | Corrected BBE | Hitters >=20 | Median raw BBE | Median effective BBE | Duplicate pitch keys |
|---|---:|---:|---:|---:|---:|
| 2022-07-15 | 67,923 | 491 | 130 | 110.04 | 0 |
| 2022-08-01 | 77,516 | 504 | 145 | 114.23 | 0 |
| 2022-09-01 | 98,823 | 542 | 164 | 127.57 | 0 |

These numbers establish source/feature feasibility only. They are **not evidence that EV/LA improves B2**.

Detailed checkpoint: `docs/current-talent-batted-ball-source-semantics-checkpoint.md`.

## Source capability boundary

Historical public MiLB tracking is structurally uneven:

- **2021:** observed tracked Florida State League / Single-A;
- **2022:** FSL plus **partial AAA**;
- **2023:** all AAA plus FSL in the certified source picture;
- **AA / High-A / other Single-A / Rookie Complex / DSL:** B2 fallback unless a later source gate proves otherwise.

The prior 2022 probe showed one AAA environment near-complete EV/LA and another around 20% on the checked date. Never promote `AAA` itself to a blanket tracked capability flag.

Every model-eligible tracked BBE must reconcile by `game_pk + player_id` to one unambiguous certified Current Talent player-game environment.

Capability provenance is retained through player feature aggregation:

- model-BBE count;
- tracked-game count;
- MLB BBE count;
- MiLB BBE count;
- source family group: MLB-only / MiLB-only / mixed;
- exact observed source capability tokens;
- observed levels;
- observed league IDs.

A source capability token describes **observed source evidence only**. It never implies unobserved games at the same level were tracked.

## MLB reuse decision

Do **not** redownload MLB Statcast for this challenger unless a concrete source-integrity gap is discovered.

The certified historical MLB Current Talent artifacts already retain exact raw Savant chunks.

Known source artifacts:

- 2021 run: `31986504169`
- 2022 run: `31988255280`
- 2023 run: `31989561396`

The richer pipeline reuses those exact bytes and the same certified MLB player-game environment.

## Frozen development chronology

### Training

Fit from exactly one snapshot:

**2021-07-15**

- standardization fit from richer-eligible B2 players at that snapshot only;
- residual coefficients fit from the same snapshot + its 90-day future contact outcomes;
- no 2022 future outcomes enter fitting;
- no overlapping Aug/Sep 2021 target windows are stacked.

### 2022 development folds

Evaluate fixed B2 vs fixed B2+richer on:

- 2022-07-15
- 2022-08-01
- 2022-09-01

Both models are scored on the exact same richer-eligible players, realized target environments, and future events.

### Confirmation

**No richer confirmation workflow exists yet, intentionally.**

Only if the 2022 development artifact passes every hard check and the generated checkpoint/result files are reviewed and committed may the project implement/run the already-fixed 2023 confirmation protocol.

The future confirmation fit, if authorized, is already frozen to:

- annual training snapshots 2021-07-15 + 2022-07-15;
- same corrected BBE semantics;
- same features;
- same >=20 threshold;
- same L2 = 0.01;
- confirmation on 2023-07-15 / 08-01 / 09-01 only;
- no 2023 search/reselection.

## Development promotion rules — operationalized before scoring

Full execution contract: `docs/current-talent-batted-ball-development-execution-contract.md`.

Development passes only if **every** check passes:

1. richer lower equal-fold mean event-weighted log loss than B2;
2. richer no worse equal-fold mean Brier;
3. richer log-loss wins at least 2/3 folds;
4. identical player / target-environment / future-event coverage in each pair;
5. any-observed-MiLB-evidence cohort contributes >=1,000 future core events across folds **and** richer has lower equal-fold mean log loss in that cohort;
6. no exact non-MLB capability-tier exposure cohort with >=1,000 future core events is worse on **both** proper scores in at least 2/3 folds;
7. all required component calibration fits converge;
8. richer mean absolute calibration-intercept error <= 1.25 × B2;
9. richer mean absolute calibration-slope error <= 1.25 × B2.

Equal-fold selection means event weighting occurs inside each fold, then the three fold scores receive equal weight.

Capability-tier diagnostics are overlapping **exposure cohorts**, not causal attribution. A mixed MLB/MiLB player can appear in multiple source-tier diagnostics; this does not duplicate the primary model score.

## Deterministic implementation now present

### Request / source acquisition

`src/universal_baseball/current_talent_savant_minors.py`

- frozen tracked-only Minor Savant request semantics;
- deterministic bounded date-chunk planning;
- no network I/O.

`scripts/probe_savant_minors_tracking.py`

- tiny manual official-source probe;
- tracked-only request helper;
- exact raw bytes + hashes;
- broad source completeness;
- corrected canonical model-BBE projection + certified environment reconciliation;
- report schema **0.4**;
- required marker: `result_producing_non_bunt_pitch_grain_v1`.

`scripts/capture_current_talent_savant_minors_tracking.py`

- manual historical tracked-MiLB capture, only after corrected probe passes;
- date bounds derived from certified MiLB evidence;
- bounded request chunks;
- exact raw byte/hash manifest;
- broad environment-level completeness diagnostics;
- canonical result-BBE materialization.

### Shared raw materialization

`src/universal_baseball/current_talent_batted_ball_materialization.py`

- one raw Savant parser/materializer for retained MLB and captured MiLB;
- one corrected BBE projection;
- one certified environment reconciliation path;
- broad source-completeness audit;
- MLB/MiLB combined-season overlap validation.

`scripts/materialize_current_talent_tracked_bbe_from_raw.py`

- offline retained-raw -> reconciled-BBE CLI.

`scripts/combine_current_talent_tracked_bbe.py`

- combines reconciled MLB + MiLB BBE into the exact per-season richer input.

### Features / provenance

`src/universal_baseball/current_talent_batted_ball_quality.py`

- corrected result-producing non-bunt pitch-grain BBE projection;
- 180-day mean EV / sweet-spot feature builder;
- >=20 eligibility;
- deterministic residual application;
- exact B2 fallback.

`src/universal_baseball/current_talent_batted_ball_source_diagnostics.py`

- broad pitch-grain completeness observations, deliberately separate from model BBE.

`src/universal_baseball/current_talent_batted_ball_reconciliation.py`

- fail-closed game/player environment reconciliation;
- source family / capability provenance.

`src/universal_baseball/current_talent_batted_ball_capability.py`

- preserves observed player-level source exposure after EV/LA aggregation.

### Model fit / scoring

`src/universal_baseball/current_talent_batted_ball_standardization.py`

- training-only feature standardization with explicit as-of provenance.

`src/universal_baseball/current_talent_batted_ball_residual_fit.py`

- target-environment-aware residual training table;
- fixed L2 deterministic optimizer;
- future BB/HBP and K excluded from fit.

`src/universal_baseball/current_talent_batted_ball_scoring.py`

- maps B2 vs richer into the existing pair-oriented Current Talent scorer;
- primary comparison includes only players with richer adjustment applied;
- fallback players cannot dilute/inflate the incremental test.

`scripts/materialize_current_talent_batted_ball_development.py`

- **offline 2022 development evaluator**;
- accepts no 2023 input;
- reuses frozen B2 construction, target-environment projection, proper scoring, calibration and strata machinery;
- fits only from 2021-07-15;
- evaluates only three 2022 folds;
- emits explicit pass/fail promotion checks.

`scripts/render_current_talent_batted_ball_development_checkpoint.py`

- deterministic artifact renderer;
- emits Markdown checkpoint + JSON result;
- refuses confirmation contamination;
- does not auto-commit.

## Workflow chain — prepared but not executed past current gate

### 1. Corrected tiny source probe

`.github/workflows/current-talent-savant-minors-probe.yml`

Manual only.

Before probing, it runs deterministic tests for:

- request semantics/chunking;
- capture helpers;
- corrected BBE projection;
- source diagnostics/audit;
- reconciliation/materialization;
- capability provenance;
- scoring adapter;
- residual fit;
- offline development contract.

A successful new run must produce **three** 2021/2022/2023 probe reports with:

- `report_schema_version = 0.4`
- `request_semantics = tracked_only_helper_v1`
- `canonical_model_bbe_contract = result_producing_non_bunt_pitch_grain_v1`
- nonzero canonical model BBE.

The old pre-correction probe run cannot satisfy these markers.

### 2. Historical tracking materialization

`.github/workflows/current-talent-batted-ball-tracking-materialization.yml`

Manual only.

Requires `source_probe_run_id`.

It refuses to run past its gate unless the downloaded probe artifact contains all three corrected 0.4 reports above.

Then it:

- reuses certified 2021/2022 MLB raw Savant caches;
- captures tracked-only 2021 MiLB full-season history;
- captures tracked-only 2022 MiLB history through 2022-08-31 for development;
- writes raw manifests and broad completeness diagnostics;
- materializes canonical reconciled MLB/MiLB BBE;
- emits combined 2021/2022 tracking parquets;
- stops without model scoring.

### 3. Fixed 2022 richer development

`.github/workflows/current-talent-batted-ball-development.yml`

Manual only.

Requires `tracking_materialization_run_id`.

It validates the corrected tracking checkpoint, downloads the same certified 2021/2022 results artifacts used by B2, fetches the pinned Chadwick snapshot **outside** the evaluator, then runs the offline evaluator.

It uploads:

- training features;
- frozen standardization state;
- target-environment-aware training table;
- residual coefficients + optimizer metrics;
- per-fold proper scores;
- component/calibration diagnostics;
- ordinary + source-capability strata;
- any-MiLB-evidence transport metrics;
- player feature/provenance surfaces;
- source tracking reports;
- generated development checkpoint Markdown;
- generated development result JSON.

It does **not** auto-commit the checkpoint and does **not** run 2023.

## Verification boundary right now

The most recent CI run successfully inspected before this newer richer-source batch was:

**32035481694 — passed.**

The connected GitHub app is currently returning `Resource not accessible by integration` for Actions/check-run reads. Repository reads/writes and historical artifact retrieval still work.

Therefore:

- do **not** call the newest commits CI-green yet;
- do **not** call the corrected 0.4 Minor Savant probe passed yet;
- do **not** call historical MiLB tracking materialized yet;
- do **not** call a real richer residual fit completed yet;
- do **not** claim any 2022 B2-vs-richer performance result;
- do **not** inspect 2023 richer performance.

The current environment also cannot dispatch the manual workflow: the connector exposes no workflow-dispatch action, `gh` is unavailable, and direct local networking to Savant is blocked.

## What has intentionally not happened

- no corrected tiny live-source rerun;
- no bulk historical Minor Savant capture;
- no real-data richer residual fit;
- no 2022 richer development proper scores;
- no persisted richer development checkpoint;
- no 2023 richer confirmation workflow;
- no richer model promotion.

## Exact next steps

**Do not write more modeling complexity before executing the prepared gates.**

1. Run `.github/workflows/current-talent-savant-minors-probe.yml` manually.
2. Inspect all three corrected 0.4 probe artifacts. If any source/schema/identity/model-BBE check fails, stop and fix the source contract before historical capture.
3. If the probe passes, run `.github/workflows/current-talent-batted-ball-tracking-materialization.yml` with that new probe run ID.
4. Inspect the 2021/2022 source checkpoint, especially broad MiLB completeness/capability by observed league/environment.
5. If source materialization is sound, run `.github/workflows/current-talent-batted-ball-development.yml` with the tracking-materialization run ID.
6. Inspect the development report and generated checkpoint/result.
7. Commit the development checkpoint/result to this branch **before** any 2023 richer work.
8. If and only if every frozen development check passed, implement/run the already-fixed 2023 confirmation. Otherwise retain B2 and close this challenger.

## Governing docs for a new chat

Read in this order:

1. `docs/project-status.md`
2. `docs/current-talent-batted-ball-quality-challenger-plan.md`
3. `docs/current-talent-batted-ball-development-execution-contract.md`
4. `docs/current-talent-batted-ball-source-semantics-checkpoint.md`
5. `docs/current-talent-validation-contract.md`
6. `docs/current-talent-results-only-baseline-freeze.md`
7. `docs/current-talent-savant-minors-source-checkpoint.md`
8. `docs/current-talent-richer-source-capability-inventory.md`

Do not redo B1/B2 selection/confirmation unless a concrete implementation failure is discovered.
