# Project status and handoff

Last updated: 2026-08-17

This is the **start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- Inspect the current branch head before editing.
- Source/model work stays on `source-certification-poc`; `main` is used only when a manual workflow dispatcher is necessary.

## Working rules

- Work in small verified batches.
- Prefer mature/certified public datasets and existing repo adapters over rebuilding raw-source cleanup.
- Fail closed on source ambiguity; do not silently drop/guess evidence.
- Keep Performance, Current Talent, Projection, and Player Value / Overall Ranking separate.
- Never retune frozen Baseline 2 or a frozen richer challenger after seeing development scores.
- Do not impute structurally unavailable tracking evidence.
- Keep live-source capture separate from deterministic/offline evaluation.
- **Do not inspect 2023 richer performance unless Challenger 2 passes every frozen 2022 development gate.**

## Current stage

Universal results-only **Current Talent Baseline 2 remains frozen** and is the comparator/fallback.

Richer Challenger 1 completed its fixed 2022 development gate and **failed**. It is closed; no 2023 rescue/tuning is authorized.

Richer Challenger 2 is frozen:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

All source, value-scale, chronology, additive-baseline, and richer-feature attachment gates are now **accepted**. No Challenger-2 2022 development loss has been computed.

**Active gate:** fit the frozen two-coefficient no-intercept residual once using only the 2021-07-15 training window, then freeze those coefficients before any 2022 MSE/MAE is calculated.

Implementation/workflow for that fit is committed:

- `scripts/fit_current_talent_contact_value_residual.py`
- `.github/workflows/current-talent-contact-value-residual-fit.yml`

## Frozen Current Talent Baseline 2

Method:

`translated_multiseason_recency_empirical_bayes_v1`

- up to 1,095 days eligible results history;
- 180-day exponential recency half-life;
- empirical-Bayes prior strength 100 effective core events;
- training-only MLB-anchored environment translation;
- frozen age/current-level Baseline 0 prior;
- frozen 12-component profile;
- 90-day future target.

B2 beat B1 on all six frozen development/confirmation folds for both log loss and Brier.

Freeze: `docs/current-talent-results-only-baseline-freeze.md`

## Richer Challenger 1 — CLOSED / REJECTED

Method:

`baseline2_plus_ev_sweet_spot_contact_residual_v1`

Development run: **`32053829482`**

Equal-fold means:

| Model | Log loss | Brier |
|---|---:|---:|
| B2 | 2.267336438 | 0.872739291 |
| richer 1 | 2.267363114 | 0.872744733 |

Richer 1 was worse on both means and won log loss only 1/3 folds. Any-observed-MiLB evidence also worsened. Calibration/optimizer checks passed, so this was predictive/transport rejection, not pipeline failure.

Persisted result:

- `docs/current-talent-batted-ball-development-checkpoint.md`
- `docs/current-talent-batted-ball-development-result.json`

## Richer Challenger 2 — FROZEN, NOT YET DEVELOPMENT-SCORED

Governing plan:

`docs/current-talent-batted-ball-contact-value-challenger-plan.md`

B2's 12-component probability vector is untouched. Challenger 2 tests a separate scalar contact-value residual after conditioning on realized contact shape and level environment.

Frozen richer features:

- 180-day recency-weighted mean EV;
- 180-day recency-weighted sweet-spot share, LA 8–32° inclusive;
- >=20 complete canonical tracked BBE;
- tracking source epoch `2021-01-01`;
- no imputation/search.

Frozen fit/evaluation:

- feature/residual training snapshot: `2021-07-15` only;
- evaluation: `2022-07-15`, `2022-08-01`, `2022-09-01`;
- future target: exact `[cutoff, cutoff + 90 calendar days)`;
- richer residual: `residual ~ z_EV + z_SS`, no intercept, no penalty;
- primary event-weighted MSE; MAE hard no-worse guard;
- comparator/richer use identical paired target rows;
- no 2023 unless all frozen 2022 gates pass.

## Gate 1 — MLB-scale terminal value table PASSED

Checkpoint: `docs/current-talent-contact-value-scale-checkpoint.md`  
Run: **`32056682313` attempt 5**

Frozen values:

| Group | Value |
|---|---:|
| `1B` | 0.4651970407443663 |
| `2B` | 0.7665843002990237 |
| `3B` | 1.0004100521698496 |
| `HR` | 1.3834396983847337 |
| `ROE` | 0.43273757678346964 |
| `FC_REACH` | 0.1558534038205505 |
| `SF` | -0.06260868067734615 |
| `MULTI_OUT` | -0.8151401718384932 |
| `OUT` | -0.24975231369042597 |

Retrosheet audit: 1,348 games, 103,534 transitions, 24/24 states, 65,572 target contacts, zero unsupported, zero missing RE24, strictly before `2021-07-15`.

## Gate 2 — terminal source semantics PASSED

Relevant contracts:

- `src/universal_baseball/current_talent_contact_value_source.py`
- `docs/current-talent-contact-value-source-checkpoint.md`

MiLB uses one terminal pitch per PA + conservative PA-result description mapping, with ambiguous FC/force-out semantics reconciled to official structured events before freezing. Exact duplicate release rows are harmless; substantive conflicts fail closed.

Frozen distinctions include `force_out -> OUT`, `fielders_choice_out -> OUT`, plain `fielders_choice -> FC_REACH`.

## Gate 3 — 2021–22 MiLB target materialization PASSED

Run: **`32070152452`**  
Checkpoint: `docs/current-talent-contact-value-source-materialization-checkpoint.md`

- all 10 2021/22 × AAA/AA/A+/A/Rookie slices passed;
- 901,015 terminal core contacts;
- 900,742 supported targets (99.9697%);
- 273 surfaced exclusions, never guessed;
- all nine groups in every slice;
- exact expected league coverage;
- no scoring / no 2023.

## Gate 4 — 2021–22 MLB target materialization PASSED

Run: **`32074097045`**  
Checkpoint: `docs/current-talent-contact-value-mlb-source-checkpoint.md`

Seeded offline from certified historical MLB source runs `31986504169` / `31988255280`.

- 236,599 core terminal contacts;
- 236,596 supported targets;
- only 3 2021 core-shaped exclusions: 2 structured sac-bunt double plays + 1 interference-error result;
- all nine terminal groups and all ten contact bins;
- same canonical target schema as MiLB;
- no fresh historical requests / no scoring / no 2023.

## Gate 5 — combined valued chronology PASSED

Run: **`32074805618`**  
Checkpoint: `docs/current-talent-contact-value-chronology-checkpoint.md`

Combined accepted MLB + MiLB:

- **1,137,338** valued 2021–22 target contacts;
- zero duplicate canonical target keys;
- all ten contact bins;
- all six levels: MLB/AAA/AA/HIGH_A/SINGLE_A/ROOKIE_COMPLEX;
- all 60 bin × level baseline cells at every cutoff.

Frozen chronology counts:

| Cutoff | Baseline | Future |
|---|---:|---:|
| 2021-07-15 | 238,119 | 300,398 |
| 2022-07-15 | 886,940 | 250,398 |
| 2022-08-01 | 949,651 | 187,687 |
| 2022-09-01 | 1,072,288 | 65,050 |

Baseline is strictly `< cutoff`; future is exactly `[cutoff, cutoff+90d)`. No network, scoring, richer fit, or 2023.

## Gate 6 — frozen additive contact baseline PASSED

Run: **`32075112279`**  
Checkpoint: `docs/current-talent-contact-value-baseline-fit-checkpoint.md`

Frozen formula:

`terminal_value ~ contact_bin + level_group`

References: `IFFB`, `MLB`.

An exact sufficient-statistics implementation in `src/universal_baseball/current_talent_contact_value_baseline.py` was proven coefficient-equivalent to the original event-wise OLS before real-source fitting (CI `32075021763`).

Every real cutoff fit is 60-cell / 15-parameter / full-rank / cutoff-safe and its event count exactly matches chronology.

## Gate 7 — richer feature/provenance attachment PASSED

Run: **`32075892988`**  
Checkpoint: `docs/current-talent-contact-value-feature-attachment-checkpoint.md`

Tracking input: certified run `32046012977`, 142,201 canonical BBE in 2021 + 164,689 in 2022.

Training-only standardization, fit once at `2021-07-15`:

- eligible players: **649**
- EV mean: **88.09960095932205**
- EV scale: **2.887465116853261**
- sweet-spot mean: **0.3470054876008983**
- sweet-spot scale: **0.06391355546209573**

Paired richer target surfaces:

| Cutoff | Paired contacts | Paired players | Any-MiLB paired contacts | Zero-fallback full-target rows |
|---|---:|---:|---:|---:|
| 2021-07-15 | **69,382** | **621** | 12,797 | 231,016 |
| 2022-07-15 | **97,004** | 976 | **49,247** | 153,394 |
| 2022-08-01 | **77,859** | 957 | **39,401** | 109,828 |
| 2022-09-01 | **37,629** | 933 | **18,400** | 27,421 |

Full future target keys remain unchanged after feature attachment. Ineligible/untracked rows encode exact `0.0` richer fallback. Exact source capability tiers are preserved, including sparse 2022 league-117 AAA.

No baseline predictions, residual coefficients, losses, calibration, or 2023 were used in this gate.

## Active Gate 8 — frozen 2021 residual fit

Committed implementation:

- `scripts/fit_current_talent_contact_value_residual.py`
- `.github/workflows/current-talent-contact-value-residual-fit.yml`

Required behavior:

1. read only accepted baseline-fit artifact `32075112279` and feature artifact `32075892988`;
2. read only `paired_future_contacts_2021-07-15.parquet` from the feature artifact;
3. apply the accepted 2021-07-15 additive baseline;
4. target residual = `terminal_value - baseline_contact_value`;
5. aggregate to player-level sufficient WLS table;
6. fit exactly `residual ~ z_EV + z_SS`, no intercept/no penalty, weighted by supported future contacts;
7. require finite/full-rank fit;
8. persist coefficients before any 2022 development score exists.

Expected training geometry from accepted upstream gate: **69,382 target contacts / 621 players**.

After Gate 8 passes, run one prediction-geometry gate applying the frozen fit unchanged to the three 2022 paired surfaces, with no losses. Only then create/run the offline 2022 development evaluator.

## Reusable richer tracking layer

Authoritative run: **`32046012977` attempt 2**.

- source epoch `2021-01-01`;
- 2021 complete through `2021-10-03`;
- 2022 history through `2022-08-31`;
- 2021 canonical tracked BBE 142,201;
- 2022 canonical tracked BBE 164,689;
- `development_tracking_ready = true`.

Coverage is capability-limited. Never generalize partial league coverage; preserve exact `source_capability_tier` provenance.

## Governing docs for a new chat

Read in this order:

1. `docs/project-status.md`
2. `docs/current-talent-batted-ball-contact-value-challenger-plan.md`
3. `docs/current-talent-contact-value-scale-checkpoint.md`
4. `docs/current-talent-contact-value-source-checkpoint.md`
5. `docs/current-talent-contact-value-source-materialization-checkpoint.md`
6. `docs/current-talent-contact-value-mlb-source-checkpoint.md`
7. `docs/current-talent-contact-value-chronology-checkpoint.md`
8. `docs/current-talent-contact-value-baseline-fit-checkpoint.md`
9. `docs/current-talent-contact-value-feature-attachment-checkpoint.md`
10. `docs/current-talent-batted-ball-development-checkpoint.md`
11. `docs/current-talent-results-only-baseline-freeze.md`
12. `docs/current-talent-validation-contract.md`

Do not redo B1/B2 selection or Challenger-1 development absent a concrete implementation bug. Do not touch 2023.
