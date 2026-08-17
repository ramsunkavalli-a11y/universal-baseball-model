# Project status and handoff

Last updated: 2026-08-17

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is used only for small manual-workflow dispatchers when needed; model/source development remains on `source-certification-poc`.
- Inspect the current branch head before editing because parallel commits may have landed.

## Execution rules

- Work in small batches of roughly 2–3 steps and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding source cleanup.
- Surface source/model errors early rather than compounding them.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Never retune frozen Baseline 2 to rescue a richer challenger.
- Do not impute structurally unavailable tracking evidence merely to keep a richer model universal.
- Keep live-source acquisition separate from deterministic model evaluation.
- **Do not inspect 2023 richer performance for a challenger that failed 2022 development.**

## Current stage

The universal results-only **Current Talent Baseline 2 is frozen and remains the production comparator/fallback**.

The first richer-evidence challenger — mean EV + sweet-spot share reshaping B2's conditional contact profile — has now completed its fixed 2022 development gate and **FAILED**.

There is no authorization to run its 2023 confirmation. The candidate is closed.

The next modeling batch is to predeclare a genuinely new richer challenger before any further 2022 evaluation. The governing first-challenger plan had already identified the natural alternative: treat observed batted-ball quality as a **separate contact-quality/value latent target**, rather than forcing EV/LA to predict the ten direction/trajectory contact probabilities.

## Frozen Current Talent Baseline 2

Method:

`translated_multiseason_recency_empirical_bayes_v1`

- up to **1,095 days** of eligible player results history;
- **180-day** exponential recency half-life;
- **100 effective core events** of empirical-Bayes prior strength;
- fitted training-only MLB-anchored environment translation;
- frozen age + current-level Baseline 0 prior;
- frozen 12-component Current Talent profile;
- 90-day future Current Talent target.

B2 passed 2022 development and fixed 2023 confirmation. Across six folds it beat B1 **6/6 on log loss and 6/6 on Brier**.

Key freeze: `docs/current-talent-results-only-baseline-freeze.md`.

## Certified richer source layer — completed

The richer-source work is reusable even though challenger 1 failed.

### Corrected tiny Minor Savant source gate

Authoritative run: **`32044627608`**

Accepted reports:

- schema `0.5`;
- `request_semantics = tracked_only_helper_v1`;
- `canonical_model_bbe_contract = result_producing_non_bunt_pitch_grain_v1`;
- certified-game denominator present;
- 100% returned `game_pk + batter` identity reconciliation on all three probe dates;
- nonzero canonical BBE.

Source checkpoint:

`docs/current-talent-savant-minors-source-checkpoint.md`

### Historical tracking materialization V2

Authoritative run: **`32046012977`**, attempt 2 — passed.

Checkpoint contract:

- schema `0.3`;
- `workflow_contract = full_2021_prior_season_v2`;
- `tracking_source_epoch = 2021-01-01`;
- `prior_season_2021_complete = true`;
- 2021 capture through **2021-10-03**;
- 2022 development capture through **2022-08-31**;
- `development_tracking_ready = true`;
- zero unmatched returned source games in the final accepted materialization.

Combined canonical tracked BBE:

- **2021: 142,201**
- **2022: 164,689**

Historical coverage remains capability-limited, not universal:

- 2021 MiLB: tracked FSL / Single-A evidence;
- 2022 MiLB: tracked FSL plus observed partial AAA evidence;
- 2023 source capability is known from the probe but has **not** been used for richer modeling;
- AA / High-A / other Single-A / Rookie Complex / DSL remain B2 fallback absent a separate source gate.

The 2022 AAA evidence remains materially uneven. Do not convert `AAA` into a blanket tracking-capability label.

## Important source corrections discovered during execution

These were source-contract corrections made before accepting downstream model results, not outcome-driven feature tuning.

### 1. Result-producing BBE semantics

Raw Savant EV/LA also appears on foul contacts. Canonical richer model BBE is therefore:

- valid game / batter / PA / pitch identity;
- normalized Savant `type == X`;
- nonblank terminal `events`;
- observed `launch_speed` + `launch_angle`;
- explicit bunt narrative excluded;
- key = `game_pk + player_id + at_bat_number + pitch_number`;
- fail on duplicate pitch key or multiple result-producing BBE in one PA.

Broad source-completeness diagnostics remain wider and may include measured foul/contact observations.

### 2. MLB game-coverage denominator

Certified MLB player-game evidence legitimately carries both AL/NL league IDs within interleague games. Game-coverage diagnostics therefore collapse MLB games to one synthetic game-level MLB league bucket while preserving player-level AL/NL provenance everywhere else.

MiLB game/league ambiguity still fails closed.

### 3. MiLB regular-season request scope

The initial full-season 2021 capture returned 134 otherwise-valid BBE from exactly three `game_type = W` postseason/championship games that were not in the certified regular-season Current Talent universe.

The official/reused Minor Savant request semantics now explicitly include:

`hfGT=R|`

The capture also fails closed if the returned CSV contains a non-`R` game type.

## First richer challenger — CLOSED / REJECTED

Governing design:

`docs/current-talent-batted-ball-quality-challenger-plan.md`

Persisted result:

- `docs/current-talent-batted-ball-development-checkpoint.md`
- `docs/current-talent-batted-ball-development-result.json`

Development workflow run: **`32053829482` — success as an execution, failed as a model gate.**

### Frozen candidate

Comparator:

`translated_multiseason_recency_empirical_bayes_v1`

Challenger:

`baseline2_plus_ev_sweet_spot_contact_residual_v1`

Features:

1. 180-day recency-weighted mean exit velocity;
2. 180-day recency-weighted sweet-spot share, launch angle 8–32° inclusive.

Application:

- only the ten conditional non-bunt contact bins could move;
- BB/HBP and K remained exactly B2;
- missing/ineligible tracking returned exact B2;
- primary richer eligibility >=20 complete tracked BBE;
- L2 fixed at 0.01;
- standardization + residual fit from 2021-07-15 only;
- fixed development folds 2022-07-15 / 08-01 / 09-01;
- no 2023 input entered the evaluator.

### Development result

Equal-fold mean proper scores:

| Model | Log loss | Brier |
|---|---:|---:|
| B2 | 2.267336438 | 0.872739291 |
| EV/SS richer | 2.267363114 | 0.872744733 |

Richer minus B2:

- log loss: **+0.000026676** — worse;
- Brier: **+0.000005442** — worse;
- richer log-loss fold wins: **1/3**.

Fold log-loss deltas, richer minus B2:

- 2022-07-15: +0.000094
- 2022-08-01: +0.000085
- 2022-09-01: -0.000099

### Non-MLB transport

Any-observed-MiLB-evidence cohort:

- future core events: **168,030**;
- equal-fold mean log-loss delta: **+0.000038462**;
- required improvement: **FAIL**.

The exact capability tier `MILB_SAVANT_TRACKED:2022:117:AAA` had **21,520** future core events and was worse on both log loss and Brier in **3/3 folds**, triggering the predeclared transport failure rule.

### Calibration

The candidate did **not** fail because of broken fitting/calibration:

- all required calibration fits converged;
- intercept guardrail passed;
- slope guardrail passed;
- scored coverage matched exactly.

Training fit also converged and improved its 2021 training contact objective. The problem is lack of held-out 2022 transport/predictive gain.

### Decision

Retain B2. Close `baseline2_plus_ev_sweet_spot_contact_residual_v1`.

**Do not create or run a 2023 confirmation workflow for this candidate. Do not tune its threshold, L2, feature definitions, or contact-bin residual after seeing this result.**

## Interpretation of challenger 1 failure

The narrow hypothesis that mean EV + sweet-spot share should improve Current Talent by predicting a hitter's future **direction/trajectory contact mix** was not supported.

That does **not** show that EV/LA has no talent signal. The feature family is more naturally connected to **damage/value conditional on contact** than to whether future contact lands in Pull/Center/Oppo × GB/LD/OFFB bins.

Importantly, this alternative target was named in the governing challenger plan before the development result was observed:

> if the narrow contact-profile test fails, a later challenger may test a separate contact-quality/value latent target rather than silently changing the first protocol.

That is the recommended next model family.

## Next challenger boundary — design before code

The next candidate should reuse the already-certified EV/LA source layer but be a **new predeclared model**, not a rescue of challenger 1.

Recommended direction:

**B2 + observed batted-ball contact-value residual**

Conceptually:

- B2 remains the universal results-only Current Talent profile and exact fallback;
- tracked EV/LA is used only for hitters with sufficient observed pre-cutoff evidence;
- richer evidence estimates a separate player contact-quality/value latent term;
- do **not** force EV/LA to alter BB/HBP, K, or the ten directional contact probabilities;
- do not use xwOBA/barrel/hard-hit composites in the first version;
- reuse raw EV + LA and the existing certified contextual Performance/run-value machinery where possible;
- preserve target-environment handling and explicit MLB/MiLB capability reporting;
- evaluate incrementally against B2 on a predeclared future value target and, only if justified, define how that scalar later feeds Player Value / Overall Ranking.

Before implementation, freeze:

1. exact future contact-value target;
2. how environment/context is removed so the target represents player contact quality rather than league/park circumstance;
3. whether the richer term is residualized against B2's predicted contact mix/bin values or modeled independently;
4. minimum tracked-BBE threshold;
5. feature family — initially mean EV + sweet-spot only unless a new feature search is explicitly registered;
6. training chronology and fixed regularization;
7. primary proper loss / calibration metric;
8. non-MLB transport guardrail;
9. production semantics: separate Current Talent dimension vs any later Player Value use.

Do **not** evaluate another candidate on 2022 until this contract is committed.

## Reusable implementation from challenger 1

Keep and reuse unless a concrete bug is found:

- `src/universal_baseball/current_talent_savant_minors.py`
- `src/universal_baseball/current_talent_batted_ball_quality.py` for canonical BBE + feature construction
- `src/universal_baseball/current_talent_batted_ball_source_diagnostics.py`
- `src/universal_baseball/current_talent_batted_ball_game_coverage.py`
- `src/universal_baseball/current_talent_batted_ball_reconciliation.py`
- `src/universal_baseball/current_talent_batted_ball_materialization.py`
- `src/universal_baseball/current_talent_batted_ball_capability.py`
- historical tracking materialization artifact from run `32046012977`
- certified 2021/2022 results evidence already used by B2
- existing environment translation / calibration / Performance-bin value infrastructure where it fits the new target.

Do not reuse the rejected 20-coefficient conditional-contact residual as the new model form merely because the code exists.

## Workflows

Manual dispatchers currently exposed on `main`:

- `Current Talent Minor League Savant probe`
- `Current Talent batted-ball tracking materialization v2`
- `Current Talent batted-ball richer development`

They explicitly check out `source-certification-poc` where appropriate.

The development workflow is now historical evidence for challenger 1. Do not rerun it with altered candidate settings under the same method label.

## Exact next batch

Keep this small.

1. **Design and commit the second richer challenger contract** around a separate contact-quality/value latent target, reusing existing Performance/run-value work rather than inventing a new outcome definition unnecessarily.
2. Inspect the existing Performance-bin contextual RE24/value machinery and the Current Talent scoring boundary to choose the narrowest defensible future target and residualization.
3. Only after that contract is frozen, implement deterministic training/scoring code and tests. Do not touch 2023.

## Governing docs for a new chat

Read in this order:

1. `docs/project-status.md`
2. `docs/current-talent-batted-ball-development-checkpoint.md`
3. `docs/current-talent-batted-ball-development-result.json`
4. `docs/current-talent-batted-ball-quality-challenger-plan.md`
5. `docs/current-talent-batted-ball-development-execution-contract.md`
6. `docs/current-talent-batted-ball-tracking-history-contract.md`
7. `docs/current-talent-savant-minors-source-checkpoint.md`
8. `docs/current-talent-results-only-baseline-freeze.md`
9. `docs/current-talent-validation-contract.md`

Do not redo B1/B2 selection or challenger-1 development unless a concrete implementation failure is discovered.
