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
- Prefer mature public datasets/parsers/packages over rebuilding raw-source cleanup.
- Surface source/model errors early rather than compounding them.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Do not retune a frozen baseline in response to a richer challenger.
- Do not fabricate/impute structurally unavailable tracking evidence merely to make a richer model universal.
- Heavy live-source workflows remain manual-only after their source gate.

## Current stage

The universal results-only **Current Talent Baseline 2 is frozen**. Active work is the first richer-evidence challenger: **B2 + observed batted-ball quality**, with exact B2 fallback when tracking is unavailable or insufficient.

Frozen comparator / fallback:

**Baseline 2 — `translated_multiseason_recency_empirical_bayes_v1`**

- up to 1,095 days of eligible results history;
- 180-day exponential recency half-life;
- 100 effective core events of EB prior strength;
- fitted training-only MLB-anchored environment translation;
- frozen age+current-level Baseline 0 prior;
- frozen 12-component Current Talent profile and 90-day target.

B2 passed 2022 development and fixed 2023 confirmation. Across the six folds it beat B1 **6/6 on log loss and 6/6 on Brier**. See `docs/current-talent-results-only-baseline-freeze.md`.

## Active richer plan

Governing protocol: `docs/current-talent-batted-ball-quality-challenger-plan.md`.

The first richer challenger adds only:

1. 180-day recency-weighted mean exit velocity;
2. 180-day recency-weighted sweet-spot share, launch angle 8–32° inclusive.

Primary richer eligibility: **>=20 complete observed result-producing, non-bunt EV+LA BBE before the cutoff**. Report >=10 / >=20 / >=30 cohorts diagnostically; do not tune the threshold from held-out results.

Hard-hit, barrel, xwOBA, max EV/EV90, bat speed, swing length, chase/whiff, scouting grades, projection, PT, defense and WAR are outside this gate.

## Important source-semantic correction — closed before development

The first implementation incorrectly assumed every complete Savant EV+LA contact row was a model BBE and keyed it at `game_pk + batter + at_bat_number`.

Inspection of the **retained certified 2021 MLB Savant raw CSV cache**, before any richer development scoring, showed that Savant also records EV/LA on foul contacts. Many plate appearances therefore contain several complete EV/LA contact rows before the eventual ball in play.

The corrected model-BBE contract is now frozen:

- Savant `type == X` after normalization;
- nonblank terminal `events`;
- complete `launch_speed` + `launch_angle`;
- valid game/player/PA/pitch identity;
- explicit bunt narratives excluded because the frozen ten-bin contact target is non-bunt contact;
- canonical key = **`game_pk + player_id + at_bat_number + pitch_number`**;
- fail on duplicate result-producing pitch key or multiple result-producing BBE inside one player/PA.

This is a source-semantics/evidence-target correction, not a feature search. It happened before any 2022 richer score was observed and does not change the feature family, threshold, model form, chronology or promotion rules.

Broad source-capability diagnostics remain intentionally wider and may include measured foul/contact rows. They now operate at pitch grain and call those rows **observations**, not model BBE.

## Source capability boundary

Historical public MiLB tracking is structurally uneven:

- **2021:** observed tracked Florida State League / Single-A;
- **2022:** FSL plus partial AAA; do **not** mark all AAA tracked;
- **2023:** all AAA plus FSL in the certified source picture;
- **AA / High-A / other Single-A / Rookie Complex / DSL:** B2 fallback unless a later source gate proves otherwise.

The prior 2022 probe showed one AAA environment near complete EV/LA and another around 20% on the checked date. Capability must therefore remain observed game/league/venue aware.

Every model-eligible tracked BBE is reconciled by `game_pk + player_id` to one unambiguous certified Current Talent player-game environment. `source_capability_tier` describes that observed source environment; it never promotes an entire level to tracked status.

Minor source checkpoint: `docs/current-talent-savant-minors-source-checkpoint.md`.  
Source inventory: `docs/current-talent-richer-source-capability-inventory.md`.

## MLB reuse decision

Do **not** redownload MLB Statcast for this challenger unless a concrete source-integrity gap appears.

The certified historical MLB Current Talent workflow artifacts for 2021–2023 already retain exact raw Savant CSV chunks in the historical quarantine/source cache. The richer MLB evidence path should reuse those bytes and their existing provenance.

Known certified MLB source artifact runs:

- 2021: `31986504169`
- 2022: `31988255280`
- 2023: `31989561396`

The 2021 artifact has already been retrieved in the current work session for source-only inspection; that does **not** constitute richer-model fitting or scoring.

## Richer model form — frozen before development

EV/LA may adjust only B2's **ten conditional non-bunt contact bins**.

- B2 `BB_HBP` remains exactly unchanged.
- B2 `K` remains exactly unchanged.
- Condition B2 on the ten contact bins.
- Apply standardized mean-EV / sweet-spot residual coefficients.
- Renormalize the ten bins and preserve total B2 contact mass.
- Missing/ineligible richer evidence => exact B2 fallback.

Method label: `baseline2_plus_ev_sweet_spot_contact_residual_v1`.

### Target-environment-aware fitting

The residual likelihood uses future contact outcomes only, but it must respect the environment where those outcomes occurred:

1. start from B2 latent conditional-contact probabilities;
2. apply the already-fitted training-only target-level CLR environment effect;
3. renormalize conditional contact probabilities;
4. add the EV / sweet-spot residual in latent logit space;
5. score against future contact-bin counts.

Do not fit directly to raw future contact shares without target-environment translation.

### Regularization

- fixed shared L2 = **0.01** on mean per-contact NLL;
- no penalty search;
- deterministic dependency-light optimizer;
- no 2022/2023 outcome-driven regularization tuning.

## Chronology — frozen before richer development

### 2022 development candidate

- fit feature standardization from richer-eligible **2021-07-15** snapshot rows only;
- fit residual coefficients using the same snapshot and its 90-day future contact outcomes;
- freeze fitted parameters;
- evaluate paired B2 vs richer on **2022-07-15 / 08-01 / 09-01**.

One annual 2021 training snapshot avoids duplicating many same future events through overlapping 90-day target windows.

### Fixed 2023 confirmation, only if development passes

- refit unchanged form using fixed annual **2021-07-15 + 2022-07-15** training snapshots/outcomes;
- same BBE semantics, feature family, threshold and L2 = 0.01;
- confirm once on **2023-07-15 / 08-01 / 09-01**;
- no 2023 search/reselection.

## Promotion gate

Development passes only if:

1. richer has lower equal-fold mean event-weighted multinomial log loss than B2;
2. richer has no worse equal-fold mean event-weighted multinomial Brier than B2;
3. richer wins log loss in at least 2/3 development folds;
4. B2/richer are scored on identical richer-eligible players, target environments and future events;
5. the aggregate gain is not solely an MLB artifact;
6. no meaningfully supported non-MLB capability tier is worse on both proper scores in at least 2/3 folds;
7. calibration does not show a broad new failure and required fits converge.

Meaningfully supported non-MLB tier threshold: **>=1,000 future core events across the three folds**.

Confirmation uses the same hard conditions. Failure means retain B2; do not reselect on 2023.

## Deterministic implementation now present

- `src/universal_baseball/current_talent_savant_minors.py`
  - frozen tracked-only Minor Savant request semantics;
  - deterministic bounded date-chunk planning;
  - no network I/O.
- `scripts/probe_savant_minors_tracking.py`
  - manual tiny source probe;
  - routes through frozen helper;
  - retains raw bytes/provenance/capability diagnostics.
- `src/universal_baseball/current_talent_batted_ball_quality.py`
  - corrected result-producing non-bunt pitch-grain BBE projection;
  - 180-day EV/sweet-spot features;
  - exact B2 residual application/fallback.
- `src/universal_baseball/current_talent_batted_ball_source_diagnostics.py`
  - broad pitch-grain measurement completeness diagnostics kept separate from model BBE.
- `src/universal_baseball/current_talent_batted_ball_reconciliation.py`
  - fail-closed join to certified game/player environment and capability provenance.
- `src/universal_baseball/current_talent_batted_ball_standardization.py`
  - training-only standardization with as-of provenance.
- `src/universal_baseball/current_talent_batted_ball_residual_fit.py`
  - target-environment-aware training table;
  - fixed-penalty deterministic residual fitter.

The manual workflow `.github/workflows/current-talent-savant-minors-probe.yml` now runs the deterministic richer-source/model tests before making the tiny live source probes.

## Verification state

The most recent CI run successfully inspected before this latest source-semantic batch was `32035481694`, which passed.

**Do not call the newest commits CI-green yet.** The connected GitHub app is currently returning `Resource not accessible by integration` for Actions/check-run reads, although repository reads/writes and artifact retrieval work.

The required tracked-only Minor Savant recheck also has **not** been rerun in this session: the available GitHub connector exposes no workflow-dispatch action, `gh` is unavailable here, and direct local networking to Savant is blocked. This is a real gate, not permission to assume success.

## What has not happened

- no bulk 2021–2023 Minor Savant materialization;
- no real-data richer residual fit;
- no 2022 richer development scores;
- no 2023 richer confirmation scores;
- no richer model promoted/frozen.

## Next verified batch

1. Verify current deterministic tests/normal CI when Actions access is available.
2. Rerun `.github/workflows/current-talent-savant-minors-probe.yml` manually under the corrected/frozen source contract.
3. If the probe passes, materialize only the minimum 2021–2022 MiLB tracking needed for the fixed 2021 training snapshot and three 2022 development cutoffs; reuse certified MLB raw source bytes.
4. Fit the real 2021 residual candidate and run the three paired 2022 B2-vs-richer folds.
5. Persist a 2022 development checkpoint **before any 2023 challenger evaluation**.
6. If development fails, retain B2. If it passes, run only the fixed 2023 confirmation protocol.

Do not begin Projection, playing time, defense, WAR or final ranking inside this gate.

## Governing docs for a new chat

Read in this order:

1. `docs/project-status.md`
2. `docs/current-talent-batted-ball-quality-challenger-plan.md`
3. `docs/current-talent-validation-contract.md`
4. `docs/current-talent-results-only-baseline-freeze.md`
5. `docs/current-talent-savant-minors-source-checkpoint.md`
6. `docs/current-talent-richer-source-capability-inventory.md`

Do not redo B1/B2 selection/confirmation unless a concrete implementation failure is discovered.
