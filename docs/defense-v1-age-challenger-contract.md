# Defense v1 age challenger contract

Last updated: 2026-08-18

Status: **PRE-REGISTERED INCREMENTAL DEVELOPMENT — 2025 DEFENSIVE TARGETS UNTOUCHED.**

## Question

Does a minimal age adjustment improve the already-selected universal general-range Defense-v1 model enough to retain before the tracked-evidence challenger?

Frozen incumbent from `docs/defense-v1-universal-development-result.json`:

- general family `U1`;
- ridge lambda `0.0`;
- four current-season normalized traditional features only.

Catcher blocking/throwing are outside this challenger and remain frozen at their development-selected forms (`C2` blocking, `C1` throwing) until later confirmation.

## Source

Reuse the same certified 2021-2024 official fielding source and 2022-2024 Savant targets used by the universal development gate.

For only the player ids needed by the general development sample, fetch immutable `birthDate` from the official MLB Stats API person endpoint. Persist source URL/status and birth date for audit. Birth date is timeless identity metadata, not a defensive target.

No 2025 defensive target may be opened.

## Age definition

For each input season:

`age_years = (July 1 of input season - birth_date) / 365.2425`

Require finite age between 15 and 45. Rows with unresolved birth date are excluded from both incumbent and challenger scoring for the age comparison so the comparison population is identical.

Frozen age terms:

- `age_c = (age_years - 27.0) / 5.0`
- `age_c2 = age_c ** 2`

No spline knots, age bins, position interactions, or alternate age anchors may be searched.

## Challenger A1

Use the exact U1 training/normalization pipeline and append only `age_c` and `age_c2`.

Fit unpenalized linear regression (`lambda = 0.0`), matching the selected U1 penalty.

No other feature, history window, interaction, or threshold changes are allowed.

## Development scoring

Repeat the exact grouped leave-one-target-year-out development CV over target years 2022, 2023, and 2024.

On each held fold score U1 and A1 on the **same age-resolved rows**.

Report:

- player count;
- MSE;
- MAE;
- Pearson;
- Spearman;
- calibration slope/intercept;
- A1 relative MSE vs U1;
- fitted coefficients.

## Frozen promotion gate

Promote age only if all are true:

1. A1 MSE is lower than U1 in at least 2 of 3 target-year folds;
2. pooled OOF MSE improves on U1 by at least **0.5%**;
3. no fold MSE is more than **2.5% worse** than U1;
4. pooled Spearman is no more than **0.005 lower** than U1;
5. all coefficients/predictions/metrics are finite;
6. each fold retains at least 100 age-resolved players.

If the gate fails, age is closed for general-range Defense v1 without rescue tuning.

## Boundary

- no catcher age model;
- no tracked evidence;
- no 2025 defensive targets;
- no production refit or confirmation authorization from this gate alone;
- no run conversion / WAR/value;
- Playing Time v1 and Position/Role v1 remain untouched.
