# Project status and handoff

Last updated: 2026-08-17

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind.
- Inspect the current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly 2–3 steps and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding raw-source cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests stay in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Do not retune a frozen baseline in response to a richer challenger; a baseline change is itself a new challenger.
- Do not fabricate or impute structurally unavailable tracking evidence merely to keep a richer model universal.
- Pause at meaningful project junctures to update this handoff before continuing.

## Current stage

The **universal results-only Current Talent baseline is frozen at Baseline 2**, and the first richer-evidence challenger is now explicitly designed.

Frozen universal comparator / fallback:

**Baseline 2 — `translated_multiseason_recency_empirical_bayes_v1`**

- up to **1,095 calendar days** of eligible player results history;
- **180-day** exponential recency half-life;
- **100 effective core events** of empirical-Bayes prior strength;
- fitted training-only MLB-anchored level translation;
- frozen leave-one-out age + current-level Baseline 0 prior;
- frozen 12-component Current Talent profile and 90-day future event target.

The first richer challenger is **B2 + observed batted-ball quality**, limited to source-capability tiers where public tracking genuinely exists. Players without sufficient observed tracking remain **exactly B2**.

Predeclared richer plan: `docs/current-talent-batted-ball-quality-challenger-plan.md`.

Current implementation state: **source/request contract, complete EV+LA projection, leakage-safe feature construction, training-only feature standardization, and deterministic B2 contact-residual application are implemented and unit-tested. The richer coefficients have NOT been fit, no 2022 richer development run has occurred, and no bulk historical EV/LA pull has been done.**

## Results-only model ladder — closed

Core batting profile: **12 components** — BB/HBP, K, IFFB, and Pull/Center/Oppo × OFFB/LD/GB.

### Baseline 0 — `loo_age_level_population_prior_v1`

- no player-specific recent Performance;
- exact age-as-of + current unambiguous level;
- leave-one-out age+level population prior;
- 2-year age band;
- minimum 12 preferred age+level peers;
- same-level then global fallback only when needed.

### Baseline 1 — `translated_recency_empirical_bayes_v1`

Frozen simple season-to-date reference:

- season-to-date player core-profile evidence;
- 180-day recency half-life;
- fitted training-only environment translation;
- empirical-Bayes shrinkage toward B0;
- prior strength = 100 effective core events.

Frozen B1 candidate ID: `hl180_ps100_fitted`.

### Baseline 2 — `translated_multiseason_recency_empirical_bayes_v1`

Frozen universal results-only comparator:

- same estimator/translation/prior machinery as B1;
- only modeling addition = eligible prior-season player results history;
- maximum lookback = 1,095 days;
- same continuous 180-day decay across season boundaries;
- same 100-event prior strength;
- same B0 prior and fold-specific translation as B1.

For players without eligible prior-season evidence, B2 collapses to B1 to numerical tolerance.

Authoritative B2 plan: `docs/current-talent-baseline2-plan.md`.

`docs/current-talent-baseline2-selection-plan.md` is only a deprecated redirect created during a parallel-work collision. Do not use it as a governing protocol.

## Baseline 2 validation — complete

### 2022 development

Folds: 2022-07-15 / 08-01 / 09-01.

B2 vs frozen B1:

- log loss: **2.253898 vs 2.256520**, delta **-0.002622**;
- Brier: **0.869252 vs 0.869743**, delta **-0.000491**;
- B2 wins **3/3** folds on log loss and **3/3** on Brier;
- component wins: **26/36** log loss, **36/36** Brier;
- every meaningfully supported non-MLB target level improved on both proper scores in every available fold;
- mean absolute calibration intercept: **0.5242 -> 0.3857**;
- mean absolute calibration slope: **0.1927 -> 0.1473**;
- ~**82.6%** of model-eligible players had positive prior-season effective evidence;
- mean added history ~**45.2 effective core events/player**.

Workflow: **31998668697**.

### Fixed 2023 confirmation

Folds: 2023-07-15 / 08-01 / 09-01. No 2023 B2 search/reselection.

B2 vs frozen B1:

- log loss: **2.249308 vs 2.252313**, delta **-0.003005**;
- Brier: **0.869079 vs 0.869653**, delta **-0.000574**;
- B2 wins **3/3** folds on log loss and **3/3** on Brier;
- component wins: **25/36** log loss, **36/36** Brier;
- every meaningfully supported non-MLB target level improved on both proper scores;
- mean absolute calibration intercept: **0.5223 -> 0.3496**;
- mean absolute calibration slope: **0.1907 -> 0.1300**;
- fixed-bin ECE slightly worsened **0.002615 -> 0.002734**, without proper-score or intercept/slope deterioration;
- ~**82.5%** had positive prior-season effective evidence;
- mean added history ~**56 effective core events/player**.

Workflow: **31998882475**.

Across all six B2 folds: **6/6 log-loss wins, 6/6 Brier wins**, mean log-loss delta **-0.002814**, mean Brier delta **-0.000532**.

Baseball interpretation: season-to-date B1 was throwing away useful signal at the season boundary. Prior-season K/BB/contact-shape results still improve present-talent estimates after level translation, regression, and current-season evidence are accounted for.

Freeze: `docs/current-talent-results-only-baseline-freeze.md`.

## Richer source capability — certified enough to start a narrow challenger

Source inventory: `docs/current-talent-richer-source-capability-inventory.md`.
Minor Savant checkpoint: `docs/current-talent-savant-minors-source-checkpoint.md`.

Official Baseball Savant Minor League Statcast detail CSV was probed and reconciled directly to the existing MLBAM/player-game backbone.

Historical tracking availability is structurally uneven:

- **2021:** tracked Florida State League / Single-A evidence;
- **2022:** tracked FSL plus **partial AAA** tracking; do not mark all AAA as tracked;
- **2023:** tracked AAA plus FSL with near-complete EV/LA on the checked date;
- **AA / High-A / other Single-A / Rookie Complex / DSL:** no proven complete historical tracking for this 2021–2023 validation period; use B2 fallback unless a later source gate proves otherwise.

The 2022 AAA probe is especially important: one AAA environment was ~99.6% complete for EV/LA while another was ~19.9% on the checked date. Capability therefore must remain game/league/venue aware rather than level-wide.

The source exposed modern bat-tracking columns but historical values were null. Do **not** infer historical bat-speed availability from column names.

A mature public package (`baseball-stats-python`) was useful as a request-semantics reference for the same Minor Savant endpoint / tracked flags, but there is no reason to add it as a runtime dependency just to duplicate the repository's thin request layer.

## First richer challenger — predeclared

Plan: `docs/current-talent-batted-ball-quality-challenger-plan.md`.

### Evidence family

Only two physical-contact features in the first gate:

1. **180-day recency-weighted mean exit velocity**;
2. **180-day recency-weighted sweet-spot share**, launch angle **8–32 degrees inclusive**.

Primary eligibility: **>=20 complete observed EV+LA batted balls before the cutoff**. Report >=10 / >=20 / >=30 sensitivity cohorts but do not tune the threshold from held-out results.

Explicitly deferred from this gate: hard-hit rate, barrel rate, xwOBA, max EV, EV90, bat speed, swing length, chase/whiff/pitch-process data, scouting grades, and prospect rankings.

### Model form

The richer evidence changes only the **conditional contact shape** of B2.

- Keep B2 `BB_HBP` probability exactly unchanged.
- Keep B2 `K` probability exactly unchanged.
- Treat the remaining 10 bins as the conditional contact distribution.
- Apply a training-only regularized multinomial residual adjustment using standardized mean EV and sweet-spot share.
- Renormalize the 10 contact bins and multiply by the original B2 contact mass.
- Recombine with unchanged BB/HBP and K.
- Missing/ineligible tracking => **exact B2 fallback**, no imputation.

This separation is deliberate: EV/LA is observed conditional on contact and should not be allowed to create artificial walk/strikeout signal in this first test.

### Chronology

- Fit standardization / residual relationship only from eligible 2021 tracked training evidence for the 2022 development gate.
- Evaluate paired B2 vs richer on 2022-07-15 / 08-01 / 09-01, exact same richer-eligible players/targets/events.
- Only if development passes: refit the unchanged form using eligible 2021–2022 training history and confirm once on 2023-07-15 / 08-01 / 09-01.
- No 2023 feature, threshold, penalty, or model-form search.

The aggregate gain must not be merely an MLB artifact. Meaningfully supported non-MLB tracking tiers remain hard guardrails where sample permits.

## Richer deterministic implementation — complete so far

### Minor Savant tracked request helper

`src/universal_baseball/current_talent_savant_minors.py`

- freezes the official Minor Savant CSV endpoint/query for batter detail;
- explicitly uses tracked filters (`hfFlag=is..tracked|`, `chk_is..tracked=on`);
- does no network I/O itself;
- unit tests verify exact request semantics and date validation.

### Complete tracked-BBE projection / feature builder

`src/universal_baseball/current_talent_batted_ball_quality.py`

Canonical complete tracked BBE grain:

`game_pk + player_id + at_bat_number`

Behavior:

- require observed `launch_speed` + `launch_angle`;
- drop incomplete measurement rows rather than imputing;
- reject multiple complete EV+LA rows at the same canonical BBE key instead of silently deduplicating;
- strictly use `game_date < as_of_date`;
- compute raw/effective tracked BBE, weighted mean EV, weighted sweet-spot share, first/last tracked evidence dates, eligibility.

### B2 contact-residual application

Same module implements deterministic application of already-fitted coefficients:

- exact B2 fallback for missing/ineligible features;
- BB/HBP and K remain exactly B2;
- only the 10 contact bins move;
- total B2 contact mass is preserved;
- zero residual coefficients reproduce B2 exactly;
- full 12-bin profile remains normalized.

Method label: `baseline2_plus_ev_sweet_spot_contact_residual_v1`.

### Training-only feature standardization

`src/universal_baseball/current_talent_batted_ball_standardization.py`

- fits means/scales on eligible **training rows only**;
- requires >=2 eligible training players and nonzero feature variance;
- exposes fitted state explicitly;
- evaluation rows reuse frozen training parameters without refitting;
- ineligible/null rows receive null standardized features and remain B2 fallback.

Tests:

- `tests/test_current_talent_batted_ball_quality.py`
- `tests/test_current_talent_batted_ball_standardization.py`
- `tests/test_current_talent_savant_minors.py`

Normal CI is green through the latest deterministic standardization batch. Latest verified run: **32035198680**.

## What has intentionally NOT happened yet

- no bulk 2021–2023 Minor Savant download;
- no fitted richer-model coefficients;
- no regularization penalty selected from development/confirmation outcomes;
- no 2022 richer development scoring;
- no 2023 richer confirmation scoring;
- no richer model promoted/frozen.

This is intentional. The source and deterministic feature/model contract are being proven before expensive historical materialization or held-out evaluation.

## Known Current Talent diagnostics

Earlier results-only calibration work found:

- K mean-rate bias / slopes often above 1;
- several LD/OFFB directional components too dispersed, slopes below 1.

B2 improves overall calibration substantially. The EV/LA challenger is allowed to target **contact-shape** defects, but must not use EV/LA to patch K/BB retrospectively.

The exact 200-PA player-aggregate diagnostic cap is still not applied because the certified backbone is player-game aggregate. Do not invent within-game PA order. Event-likelihood scoring correctly uses all eligible future events in the 90-day target horizon.

## Key governing docs

Read in this order for the active gate:

1. `docs/project-status.md`
2. `docs/current-talent-validation-contract.md`
3. `docs/current-talent-results-only-baseline-freeze.md`
4. `docs/current-talent-richer-source-capability-inventory.md`
5. `docs/current-talent-savant-minors-source-checkpoint.md`
6. `docs/current-talent-batted-ball-quality-challenger-plan.md`
7. `docs/current-talent-baseline2-confirmation-checkpoint.md`
8. `docs/current-talent-baseline2-development-checkpoint.md`
9. `docs/current-talent-baseline2-plan.md`

Historical B1 and source checkpoints remain provenance. Do not reopen closed gates without a concrete failure.

## Next verified batch

Do **not** jump straight to a full historical run.

1. Add the deterministic **training-table / residual-fit contract** that joins frozen B2 conditional-contact predictions, standardized tracked features, and future contact outcomes without leakage. Decide/freeze the very small L2-penalty protocol using training data only.
2. Add a tiny/manual live-source capture workflow using the frozen tracked request helper, retaining raw response bytes and source/capability diagnostics; verify request parity on tiny dates before larger materialization.
3. Only after those pass, materialize the minimum 2021–2022 tracked evidence needed for the three 2022 development folds and run the predeclared paired B2-vs-richer gate.
4. Persist a 2022 development checkpoint **before** any richer 2023 evaluation. If the development gate fails, stop and retain B2.

Do not begin Projection, playing time, defense, WAR, or final ranking inside this gate.

## Still unresolved

- first richer batted-ball-quality challenger fit/development/confirmation;
- later swing/contact-process or pitch-level challengers;
- final Current Talent uncertainty model;
- component-specific shrinkage/recalibration unless separately validated;
- Projection / aging and development;
- playing time / role;
- defense;
- WAR / value conversion;
- final cross-player ranking.

## If starting a new chat

1. Read this file and the six active-gate docs above.
2. Inspect the current `source-certification-poc` head before editing.
3. Verify normal CI is green.
4. Continue with the **training-table / residual-fit contract**, not B1/B2 revalidation and not bulk tracking downloads.
5. Preserve the tiered architecture: B2 universal fallback, richer estimate only where observed tracking passes capability/sample rules.
