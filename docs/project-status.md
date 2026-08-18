# Project status and handoff

Last updated: 2026-08-17

This is the **start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- Work in small verified batches; inspect current branch head before editing.
- Prefer certified/reusable public data + existing repo adapters over rebuilding raw-source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, and Player Value / Overall Ranking separate.

## Current stage

Universal results-only **Current Talent Baseline 2 remains frozen and retained**:

`translated_multiseason_recency_empirical_bayes_v1`

Richer Challenger 1 (`baseline2_plus_ev_sweet_spot_contact_residual_v1`) failed its fixed 2022 development gate and is closed.

Richer Challenger 2:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

passed every frozen 2022 development gate, but **failed the single fixed 2023 confirmation** under the predeclared acceptance contract. It is therefore **not confirmed and must not be integrated or rescued by tuning on 2023**.

Binding confirmation result:

`docs/current-talent-contact-value-confirmation-result.json`

### Immediate task

Challenger 2 is methodologically closed. Do not refit, loosen guardrails, alter features, or rerun a modified Challenger 2 against 2023.

Safe next work is repository/handoff cleanup and then selection of a genuinely new research question under a new predeclared development/confirmation design. Baseline 2 remains the production Current Talent model until a future challenger independently earns promotion.

## Frozen Baseline 2

- 1,095-day eligible results history
- 180-day exponential half-life
- EB prior strength 100 effective core events
- training-only MLB-anchored level translation
- frozen age/current-level Baseline 0 prior
- frozen 12-component profile
- 90-day future target

B2 beat B1 on all six frozen 2022-development / 2023-confirmation folds for log loss and Brier.

Freeze: `docs/current-talent-results-only-baseline-freeze.md`

## Challenger 2 governing contract

Plan: `docs/current-talent-batted-ball-contact-value-challenger-plan.md`

Fixed features:

- 180-day recency-weighted mean EV
- 180-day recency-weighted sweet-spot share, LA 8–32° inclusive
- eligibility >=20 complete canonical tracked BBE
- tracking epoch `2021-01-01`
- no tracking imputation/search

Fixed conditional-value design:

- nine-group MLB-scale terminal values
- additive control `terminal_value ~ contact_bin + level_group`
- references `IFFB` / `MLB`
- residual `beta_EV*z_EV + beta_SS*z_SS`, no intercept/no penalty
- primary MSE
- MAE no-worse hard guardrail
- exact paired target coverage
- MiLB/capability-tier transport checks
- calibration guardrails

Fixed confirmation acceptance contract:

`docs/current-talent-contact-value-confirmation-contract.md`

It reused the same ten promotion checks on the three 2023 folds. Confirmation was one-shot; failure prohibits 2023 rescue tuning/reselection.

## Completed Challenger 2 gates

### 1. Terminal value scale — PASSED

Run `32056682313`, attempt 5. Retrosheet evidence strictly before `2021-07-15`.

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

### 2. Historical terminal semantics — PASSED

MiLB uses one terminal pitch per PA plus conservative PA-result narrative fallback, reconciled to official structured semantics before freezing. Important distinctions: `force_out -> OUT`, `fielders_choice_out -> OUT`, plain `fielders_choice -> FC_REACH`. Exact duplicate release rows collapse; substantive conflicts fail closed.

### 3. 2021–22 MiLB target materialization — PASSED

Run `32070152452`:

- 901,015 terminal core contacts
- 900,742 supported targets (99.9697%)
- 273 explicit exclusions
- all 10 season/level slices passed

### 4. 2021–22 MLB target materialization — PASSED

Run `32074097045`:

- 236,599 core contacts
- 236,596 supported
- only 3 explicit 2021 exclusions

### 5. Combined chronology — PASSED

Run `32074805618`:

- 1,137,338 valued 2021–22 contacts
- zero duplicate target keys
- all 10 bins / all 6 levels
- all 60 bin×level baseline cells
- exact half-open chronology

### 6. Additive baseline — PASSED

Run `32075112279`. All four fits are 60-cell / 15-parameter / full-rank / cutoff-safe. Sufficient-statistics implementation is coefficient-equivalent to the original event-wise OLS.

### 7. Development feature/provenance attachment — PASSED

Run `32075892988`.

2021-only development standardization:

- 649 eligible players
- EV mean `88.09960095932205`; scale `2.887465116853261`
- sweet-spot mean `0.3470054876008983`; scale `0.06391355546209573`

Paired target contacts:

- 2021-07-15: 69,382 / 621 players
- 2022-07-15: 97,004 / 976
- 2022-08-01: 77,859 / 957
- 2022-09-01: 37,629 / 933

### 8. Frozen 2021 residual fit — PASSED

`docs/current-talent-contact-value-residual-fit-result.json`

- 69,382 contacts / 621 players
- beta EV `0.020808202510874292`
- beta sweet-spot `-0.0032619728296970248`
- determinant `3906075044.1483107`
- no 2022 future outcomes or 2023 accessed

### 9. 2022 prediction geometry — PASSED

`docs/current-talent-contact-value-prediction-geometry-result.json`

- paired counts unchanged: 97,004 / 77,859 / 37,629
- comparator/richer keys identical
- finite predictions
- no losses/calibration
- no coefficient refit
- no 2023

### 10. Fixed 2022 development — PASSED ALL GATES

`docs/current-talent-contact-value-development-result.json`

Equal-fold means:

- baseline MSE `0.19983482558337698`
- richer MSE `0.19947804003888056`
- delta `-0.00035678554449641853`
- baseline MAE `0.35317026840563903`
- richer MAE `0.3528114760321568`
- delta `-0.0003587923734822418`
- richer MSE wins **3/3**

Any-observed-MiLB:

- 107,048 total fold contacts
- baseline mean MSE `0.2017534561593921`
- richer mean MSE `0.20141942641402558`
- delta `-0.00033402974536653196`

Calibration mean absolute errors also improved:

- intercept: baseline `0.009059769936977567`, richer `0.008572858096503674`
- slope: baseline `0.0037337420889670034`, richer `0.003119243058711215`

All exact non-MLB capability-tier guardrails passed. This authorized exactly one fixed 2023 confirmation.

### 11. Authorized confirmation refit — PASSED / FROZEN BEFORE 2023

Run `32079555373`; artifact digest `sha256:07060a473fc71c8cce15f29e5a69ff68364cc721c4f3d1fe52a3d1c4e7728f44`.

`docs/current-talent-contact-value-confirmation-refit-result.json`

Training snapshots: `2021-07-15` + `2022-07-15` only.

Authoritative pooled confirmation standardization:

- 1,788 eligible player-snapshot rows
- EV mean `87.56765458046604`
- EV scale `3.087267010464925`
- sweet-spot mean `0.34421856089476915`
- sweet-spot scale `0.0629687444393524`

Frozen confirmation residual fit:

- beta EV `0.019444311355484883`
- beta sweet-spot `-0.0016659086163438607`
- determinant `18569017159.610256`
- 166,386 future-contact weight
- 1,597 fitted player-snapshots

This run completed before the first 2023 source workflow began. An earlier handoff/confirmation-contract transcription contained stale standardization literals; the contract was corrected to these run-backed values before any 2023 loss or confirmation decision was computed. This was documentation correction only, not a refit.

### 12. Confirmation tracking — PASSED SOURCE/MATERIALIZATION

Run `32079922837` completed all source/materialization steps; its workflow conclusion was failure only because a final branch-push raced later commits. The inspected artifact was accepted and checkpointed.

`docs/current-talent-batted-ball-tracking-confirmation-result.json`

Canonical BBE rows:

- 2021: 142,201
- 2022: 171,415
- 2023: 206,542

2023 MiLB tracking was captured through `2023-08-31`; no tracking imputation.

### 13. 2023 terminal target source — PASSED

Clean run `32082637028` after a narrow mojibake duplicate-identity normalization fix.

`docs/current-talent-contact-value-confirmation-source-result.json`

- 595,794 core terminal contacts
- 595,619 supported targets
- supported rate `99.9706%`
- all six MLB/MiLB source slices contain all nine terminal groups
- shared target schema
- no model scoring/refit

### 14. 2023 confirmation chronology — PASSED

Run `32086274717`.

`docs/current-talent-contact-value-confirmation-chronology-result.json`

- 1,732,957 combined valued 2021–23 contacts
- exact baseline `< cutoff` and future `[cutoff, cutoff+90d)` boundaries
- future targets: 248,081 / 176,853 / 58,639 for Jul 15 / Aug 1 / Sep 1
- no losses/features/refit

### 15. 2023 confirmation evidence/baselines — PASSED

Run `32086538491`.

`docs/current-talent-contact-value-confirmation-evidence-result.json`

All three additive baselines are 60-cell / 15-parameter / full-rank / cutoff-safe. The Sep. 1 future surface naturally has no Rookie Complex games remaining; Rookie Complex is present in the baseline history.

### 16. 2023 confirmation feature attachment — PASSED

Run `32086704821`.

`docs/current-talent-contact-value-confirmation-features-result.json`

Paired richer target contacts:

- 2023-07-15: 118,984 / 1,226 players
- 2023-08-01: 90,949 / 1,191
- 2023-09-01: 40,885 / 1,158

Any-observed-MiLB paired contacts: 89,957 / 69,153 / 30,933.

All target rows survive attachment; unavailable richer evidence gets exact zero fallback. Frozen confirmation standardization and coefficients match the pre-2023 refit exactly.

### 17. 2023 confirmation prediction geometry — PASSED

Run `32087405934`.

`docs/current-talent-contact-value-confirmation-prediction-geometry-result.json`

- paired rows unchanged: 118,984 / 90,949 / 40,885
- comparator/richer event keys identical
- all predictions finite
- frozen coefficients unchanged
- no MSE/MAE/calibration/decision computed in this gate

### 18. ONE-SHOT 2023 CONFIRMATION — FAILED / BINDING

Run `32087555990`; artifact digest `sha256:0dbc2de14cb17fd19ec5ac7a03acc04280c56f58ad67e9154365c2ec60ce80e7`.

`docs/current-talent-contact-value-confirmation-result.json`

Challenger 2 **improved MSE in all three folds**:

- Jul 15 delta `-0.0003622675752758264`
- Aug 1 delta `-0.0003697452826812164`
- Sep 1 delta `-0.00034878621837869384`
- equal-fold mean MSE: baseline `0.2033816366639647`, richer `0.2030213703051861`, delta `-0.00036026635877858815`

It also improved any-observed-MiLB mean MSE:

- 190,043 total fold contacts
- baseline `0.20089396260933756`
- richer `0.2006303557093879`
- delta `-0.0002636068999496699`

All meaningful exact non-MLB capability-tier transport guardrails passed.

However, **two hard predeclared confirmation checks failed**:

1. MAE no-worse failed. Richer MAE was worse in all three folds; equal-fold mean baseline `0.3561671497421868`, richer `0.3569228787973761`, delta `+0.0007557290551893359`.
2. Calibration-intercept guardrail failed. Mean absolute intercept error was baseline `0.006149013705759256` vs richer `0.010010572857580608`, above the allowed `1.25×` baseline error. The calibration-slope guardrail passed.

Final binding decision:

`confirmed = false`

Do **not** tune or rerun Challenger 2 on 2023. Do not integrate this scalar into Current Talent, Performance, Projection, WAR, Player Value, or Overall Ranking. Baseline 2 remains frozen.

## Governing docs for a new chat

Read in this order:

1. `docs/project-status.md`
2. `docs/current-talent-contact-value-confirmation-result.json`
3. `docs/current-talent-contact-value-confirmation-contract.md`
4. `docs/current-talent-contact-value-confirmation-prediction-geometry-result.json`
5. `docs/current-talent-contact-value-confirmation-features-result.json`
6. `docs/current-talent-contact-value-confirmation-evidence-result.json`
7. `docs/current-talent-contact-value-confirmation-chronology-result.json`
8. `docs/current-talent-contact-value-confirmation-source-result.json`
9. `docs/current-talent-batted-ball-tracking-confirmation-result.json`
10. `docs/current-talent-contact-value-confirmation-refit-result.json`
11. `docs/current-talent-contact-value-development-result.json`
12. `docs/current-talent-batted-ball-contact-value-challenger-plan.md`
13. `docs/current-talent-results-only-baseline-freeze.md`

Do not redo B1/B2 selection, Challenger 1, Challenger 2 development, or Challenger 2 confirmation absent a concrete implementation failure. Any future richer model must be treated as a new challenger with a new frozen design and a genuinely untouched confirmation surface.
