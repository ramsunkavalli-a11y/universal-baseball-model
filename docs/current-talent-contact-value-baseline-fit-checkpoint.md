# Current Talent challenger 2 — baseline fit checkpoint

Status: **ACCEPTED FOR RICHER-FEATURE PRE-SCORING ASSEMBLY**  
Date accepted: 2026-08-17  
Authoritative workflow run: **`32075112279`**  
Tested commit: **`6d01fe09ccebefda6e9e4e7498103ccf0d18ba64`**

This checkpoint accepts the implementation and real-source fits of the already-frozen Challenger-2 baseline:

`terminal_value ~ contact_bin + level_group`

with fixed references `IFFB` and `MLB` and one weight per accepted target contact.

No future predictions, MSE/MAE, richer-feature fit, or 2023 evidence were computed.

## Exact implementation equivalence

The original frozen implementation constructed the normal equations one contact at a time. The accepted efficient implementation uses the exact sufficient statistics for categorical additive OLS:

- one row per `contact_bin × level_group` cell;
- `event_count` supplies the event weight in `X'X`;
- `terminal_value_sum` supplies the exact contribution to `X'y`.

Module:

`src/universal_baseball/current_talent_contact_value_baseline.py`

Contract CI run **`32075021763`** passed. Tests directly compare the sufficient-statistics coefficients to the original event-wise fitter under unequal cell weights and require the same rank-deficiency failure behavior.

This is an implementation optimization only. It does not change the frozen formula, references, event weights, target values, or development hypothesis.

## Real-source fits

Source: accepted combined valued chronology run `32074805618`.

Every cutoff fit:

- contains all 10 frozen contact bins;
- contains all 6 level groups;
- contains all 60 `contact_bin × level_group` cells;
- has 15 parameters: intercept + 9 non-reference contact-bin effects + 5 non-reference level effects;
- is full rank;
- ends strictly before the cutoff;
- has event count exactly equal to the accepted chronology baseline count.

| Cutoff | Events | Max training date | Cells | Parameters | Full rank |
|---|---:|---|---:|---:|---|
| 2021-07-15 | 238,119 | 2021-07-14 | 60 | 15 | yes |
| 2022-07-15 | 886,940 | 2022-07-14 | 60 | 15 | yes |
| 2022-08-01 | 949,651 | 2022-07-31 | 60 | 15 | yes |
| 2022-09-01 | 1,072,288 | 2022-08-31 | 60 | 15 | yes |

## Coefficient sanity

The fit is an environmental control, not a talent model. Values are on the frozen MLB RE24 terminal-value scale.

Selected coefficients:

| Cutoff | Intercept (MLB IFFB) | PULL_LD | PULL_OFFB | CENTER_LD | AAA level effect |
|---|---:|---:|---:|---:|---:|
| 2021-07-15 | -0.23061 | 0.62145 | 0.65506 | 0.52398 | 0.02605 |
| 2022-07-15 | -0.23812 | 0.62477 | 0.62456 | 0.53510 | 0.02803 |
| 2022-08-01 | -0.23846 | 0.62573 | 0.62257 | 0.53564 | 0.02790 |
| 2022-09-01 | -0.23934 | 0.62586 | 0.61903 | 0.53663 | 0.02860 |

The 2022 coefficient sets move only modestly as additional pre-cutoff evidence is added. No coefficient was selected/tuned from future model performance.

## Boundary flags

The authoritative report records:

- `network_requests_performed = false`
- `model_scoring = false`
- `future_predictions_computed = false`
- `richer_features_attached = false`
- `richer_residual_fitted = false`
- `accessed_2023 = false`
- `baseline_fitted = true`

Artifact digest:

`sha256:d5a3ec03afd3244407fac82bc74c7ef28a3d2e45d29dba69ab30f38d96bb79dd`

## Decision

**Frozen baseline implementation passes.**

Next allowed work is richer-feature attachment only:

1. reuse the already-certified tracking history/snapshots;
2. attach the frozen 180-day recency-weighted mean EV and sweet-spot share to player snapshots;
3. preserve the >=20 complete tracked-BBE eligibility rule and exact source-capability provenance;
4. standardize features using the frozen training-snapshot moments only;
5. enforce exact zero residual fallback for ineligible/untracked players;
6. prove comparator and richer candidate share identical future target event keys;
7. only after that gate is accepted may the offline 2022 development evaluator compute MSE/MAE.

Still forbidden: 2023 access or any change to the frozen outcome/value/baseline/feature/evaluation rules based on development performance.
