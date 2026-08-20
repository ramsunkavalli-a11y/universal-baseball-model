# Playing time / role v1 development contract

Last updated: 2026-08-17

Status: **PRE-REGISTERED BEFORE PLAYING-TIME MODEL FIT/SCORING. 2025 TARGETS REMAIN UNTOUCHED.**

Governing methodology review:

`docs/playing-time-role-methodology-review.md`

Source/target checkpoints:

- `docs/playing-time-v1-target-surface-checkpoint.md`
- `docs/playing-time-historical-40man-membership-result.json`
- `docs/playing-time-roster-duplicate-diagnostic-result.json`

## Question

Can a transparent, chronology-safe two-part model improve next-season MLB batting-opportunity prediction beyond a simple as-of-level baseline, while keeping opportunity separate from frozen batting-rate skill?

Frozen batting-rate model remains:

`frozen_current_talent_carry_forward_v1`

No playing-time outcome may modify Current Talent or batting-rate Projection.

## Target / population

For every eligible frozen B2 October snapshot player:

`Y = next-calendar-year regular-season MLB plate appearances`

including explicit `Y = 0`.

Development folds:

1. `2021-10-15 -> 2022` — candidate selection only;
2. `2022-10-15 -> 2023` — out-of-time validation 1;
3. `2023-10-15 -> 2024` — out-of-time validation 2.

Untouched confirmation candidate:

4. `2024-10-15 -> 2025` — **do not materialize/open before development promotion and final refit are frozen.**

The universal snapshot population, identity rules, age, and as-of-level semantics reuse the frozen B2 snapshot contract.

## Why a two-part model is frozen

The already-materialized development target is about 84–85% zero MLB PA across all three folds. Among positive MLB-PA players, variance is roughly 165–171 times the mean.

Therefore v1 separates:

1. **participation:** `P(Y > 0)`;
2. **positive amount:** distribution of `Y | Y > 0`.

A player with `Y=0` contributes to the participation model but is never assigned artificial negative batting skill.

## Model family

Use mature library implementations; do not write a custom likelihood optimizer.

### Participation component

L2-regularized logistic regression with:

- natural class prevalence; no class reweighting;
- intercept;
- fixed regularization `C = 1.0`;
- deterministic solver/settings;
- training-only standardization for continuous predictors;
- no tuning of regularization on 2023/2024.

The L2 penalty is required to keep sparse low-level cells finite rather than relying on unstable complete-separation MLE behavior.

### Positive-PA component

Zero-truncated Negative Binomial P (`p=2`) fit only on rows with `Y > 0`.

Requirements:

- intercept included;
- same candidate predictor form as participation unless a field is structurally constant in the positive training sample;
- training-only standardization values reused on held-out data;
- dispersion estimated on authorized training rows;
- optimizer must converge under the fixed library contract; do not silently switch to Poisson or another family if a fit fails.

### Full predictive distribution

For held-out player `i`:

- `P(Y_i = 0) = 1 - p_i`;
- for `y > 0`, `P(Y_i = y) = p_i * f_TNB(y | x_i)`.

The primary score is the held-out mean negative log likelihood of that full hurdle distribution.

## As-of level tier

To avoid unstable tiny cells while retaining baseball meaning, map canonical as-of levels to exactly four tiers:

- `MLB`;
- `AAA`;
- `AA`;
- `A_OR_BELOW` = `HIGH_A`, `SINGLE_A`, `ROOKIE_COMPLEX`.

Use MLB as the reference category.

No target/future level is a predictor.

## Continuous predictor transforms

All are computed strictly from snapshot-available evidence.

- `age_centered = (age_years - 25) / 5`;
- `log_current_mlb_pa = log1p(current_season_mlb_pa)`;
- `log_current_milb_pa = log1p(current_season_milb_pa)`.

No prior-season PA feature is allowed in v1 because the 2021 selection snapshot lacks a certified pre-2021 universal season. Do not give later folds a predictor that could not be estimated/validated in the selection fold.

## Compact B2 talent summary

The final candidate may use only these four pre-target frozen-B2 probabilities:

1. `BB_HBP`;
2. `K`;
3. non-IFFB outfield-fly probability = `PULL_OFFB + CENTER_OFFB + OPPO_OFFB`;
4. line-drive probability = `PULL_LD + CENTER_LD + OPPO_LD`.

Do not use the full 11-D B2 ILR vector in v1. The four summaries are intended to test whether portable batting quality adds opportunity signal beyond current level, recent usage, and 40-man membership without turning this stage into another high-dimensional talent model.

## Certified roster feature boundary

Authorized:

- `on_40man`: binary official team 40-man set membership at the exact snapshot date.

Explicitly not authorized:

- active/minors status inferred from the `40Man` response;
- injured-list status inferred from the `40Man` response;
- option status;
- future team/role;
- row-level source status codes.

The official source can duplicate one player with conflicting row statuses while membership remains identical; the certified adapter preserves the conflict as provenance but exposes only binary membership to v1.

## Baseline / candidate forms

The feature search is exactly these four nested forms and no others.

### B0 — level-only hurdle

Method label:

`playing_time_level_hurdle_v1`

Predictors:

- as-of level tier only.

This is the required comparator.

### A — recent opportunity

Method label:

`playing_time_recent_opportunity_hurdle_v1`

B0 plus:

- `age_centered`;
- `log_current_mlb_pa`;
- `log_current_milb_pa`.

### B — recent opportunity + 40-man

Method label:

`playing_time_recent_opportunity_40man_hurdle_v1`

A plus:

- `on_40man`.

### C — recent opportunity + 40-man + compact B2 skill

Method label:

`playing_time_recent_opportunity_40man_b2_hurdle_v1`

B plus the four compact B2 talent summaries above.

No interactions, team fixed effects, organization depth chart, position, future role, prospect rank, scouting grade, injury signal, transaction sequence, or manual playing-time forecast is allowed in v1.

## 2022 candidate selection

Use only `2021-10-15 -> 2022` outcomes.

Run deterministic 5-fold player-held-out CV using the same hash contract already established in Projection:

`cv_fold = int(first_8_hex(SHA256(str(player_id))), 16) % 5`.

Every form B0/A/B/C is fit independently inside each training fold and scored on the held-out fold.

### Primary selection score

Lowest pooled held-out **full hurdle negative log likelihood per player**.

### Tie breaks

1. if full NLL differs by no more than `0.001`, prefer lower participation log loss;
2. if participation log loss differs by no more than `0.0005`, prefer lower unconditional MLB-PA MAE;
3. if still tied, prefer the simpler nested form in order `B0 < A < B < C`.

### Early development boundary

A/B/C may advance beyond 2022 only if the selected non-B0 form has lower full hurdle NLL than B0.

If B0 is selected, freeze B0 as playing-time v1 and do not inspect 2023/2024 to search for a richer form.

## Out-of-time validation

If A/B/C is selected on 2022, keep the exact selected feature form and all fixed model settings unchanged.

### 2023

- fit on all authorized 2022-response rows;
- predict the `2022-10-15` population;
- score 2023.

### 2024

Only if the 2023 primary gate passes:

- refit the same form on authorized 2022 + 2023 training observations;
- repeated players across years are separate fold+player observations, not identity predictors;
- predict the `2023-10-15` population;
- score 2024.

No model form, regularization, level tier, transform, or feature may be changed in response to 2023/2024 results.

## Required scores / diagnostics

For B0 and the selected challenger report:

### Full distribution

- mean full hurdle negative log likelihood per snapshot player — **primary**;
- unconditional expected MLB-PA MAE and RMSE — secondary;
- mean predicted MLB PA versus observed by predicted-decile.

### Participation

- binary log loss;
- Brier score;
- calibration intercept/slope where identifiable;
- reliability by probability band.

### Positive amount

On observed `Y > 0` rows:

- zero-truncated NB conditional negative log likelihood;
- positive-PA MAE/RMSE for predicted conditional mean;
- observed versus predicted positive mean by decile.

### Strata

At minimum:

- as-of level tier;
- `on_40man`;
- current-season MLB PA `0` versus `>0`;
- age bands `<22`, `22–25`, `26–29`, `30–33`, `34+`;
- compact B2-skill quartile diagnostic using training-only ranking if needed.

## Development promotion rule

A selected non-B0 challenger advances to 2025 confirmation only if **all** hold:

1. full hurdle NLL is lower than B0 in both 2023 and 2024 validation folds;
2. equal-fold mean participation log loss is no worse than B0;
3. equal-fold mean positive-count conditional NLL is no worse than B0;
4. equal-fold mean unconditional MLB-PA MAE is no more than 2% worse than B0;
5. scored snapshot-player coverage is exactly identical;
6. participation calibration fits converge where identifiable and show no structural failure;
7. for any as-of level tier with at least 100 snapshot players and 25 positive-MLB-PA outcomes in **each** validation fold, fail if the same tier has challenger minus B0 full NLL `> +0.02` in both folds;
8. no future team/level/role or 2025 target information entered predictors.

If the primary full-NLL gate fails on 2023, do not open 2024 as a rescue period. If any binding promotion rule fails after 2024, retain B0 and do not tune against the failed validation period.

## Confirmation refit / 2025 boundary

If and only if development promotion passes:

1. freeze selected form and library/model settings;
2. refit on all three authorized pre-2025 response folds (2022, 2023, 2024), using fold+player observation keys for repeated players;
3. persist coefficients/parameters, dispersion, standardization values, source artifact IDs/hashes, training row counts, and package versions;
4. verify deterministic reproduction;
5. only then materialize/open the `2024-10-15 -> 2025` opportunity target;
6. run one fixed 2025 confirmation using the same primary/secondary gates;
7. if confirmation fails, retain the simpler B0 playing-time model. Do not tune on 2025.

## Role / team allocation boundary

This contract forecasts an individual MLB-PA distribution. It does not yet force all player forecasts to sum to finite team positional PA.

After individual v1 is validated, role bands and/or a team-allocation coherence layer may be added as a separate downstream gate. Do not let current organizational depth suppress portable player skill inside the batting-rate model.
