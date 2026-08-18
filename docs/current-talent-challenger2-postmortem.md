# Current Talent Challenger 2 Postmortem

Last updated: 2026-08-17

Status: **CLOSED AFTER BINDING 2023 CONFIRMATION FAILURE**

Candidate:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

Binding result:

`docs/current-talent-contact-value-confirmation-result.json`

## What the experiment established

### 1. Baseline 2 is a strong Current Talent foundation

The frozen results-only model:

`translated_multiseason_recency_empirical_bayes_v1`

proved difficult to beat even after adding certified batted-ball tracking and a separate conditional contact-value target.

Challenger 1 failed its fixed 2022 development gate. Challenger 2 passed every 2022 development gate but failed the single fixed 2023 confirmation.

The practical implication is diminishing returns to immediate Current Talent feature hunting. Baseline 2 remains the production Current Talent model.

### 2. Exit velocity contains real, stable forward information

The richer Challenger 2 prediction reduced conditional-contact-value MSE in every development and confirmation fold.

2022 development MSE deltas, richer minus baseline, were negative in all three folds. The equal-fold mean delta was:

`-0.00035678554449641853`

2023 confirmation MSE deltas were:

- 2023-07-15: `-0.0003622675752758264`
- 2023-08-01: `-0.0003697452826812164`
- 2023-09-01: `-0.00034878621837869384`

Equal-fold mean 2023 MSE improved from:

- baseline `0.2033816366639647`
- richer `0.2030213703051861`
- delta `-0.00036026635877858815`

The any-observed-MiLB confirmation cohort also improved across 190,043 fold contacts, with mean-MSE delta:

`-0.0002636068999496699`

This is strong evidence that the underlying EV signal is not merely an MLB artifact or a one-year development accident.

### 3. A real signal can still fail promotion

The same 2023 richer predictions worsened MAE in all three confirmation folds.

Equal-fold mean MAE:

- baseline `0.3561671497421868`
- richer `0.3569228787973761`
- delta `+0.0007557290551893359`

The most plausible interpretation is that the richer correction improved some larger misses enough to reduce squared error while making many smaller/typical errors slightly worse. MSE and MAE are measuring different parts of the error distribution; the frozen contract correctly required both to remain acceptable.

This is an inference from the joint metric behavior, not a claim that every individual error followed that pattern.

### 4. Calibration exposed a systematic weakness in the linear residual specification

The 2023 calibration-intercept guardrail failed.

Mean absolute calibration-intercept error:

- baseline `0.006149013705759256`
- richer `0.010010572857580608`

The allowed ceiling was `1.25 ×` the comparator error. The richer result exceeded it.

The frozen residual model had no intercept:

`beta_EV * z_EV + beta_SS * z_SS`

Even with fixed pre-2023 standardization, a later feature distribution can have non-zero average standardized values. That can create an average residual shift on the confirmation population. This is a useful mechanism to investigate in future research, but Challenger 2 may not be repaired using 2023 feedback.

### 5. EV dominated the two-feature residual; sweet-spot contributed little independently

Frozen 2021 development residual fit:

- beta EV `0.020808202510874292`
- beta sweet-spot `-0.0032619728296970248`

Frozen pre-2023 confirmation refit:

- beta EV `0.019444311355484883`
- beta sweet-spot `-0.0016659086163438607`

The EV coefficient remained similar after adding the authorized 2022 training snapshot. The independent sweet-spot coefficient moved closer to zero and remained slightly negative.

This does **not** prove sweet-spot has no baseball value. It says that in this specific conditional-value model, after EV and the frozen contact-bin/level baseline, its additional linear contribution was small.

### 6. Universal source/identity/value infrastructure succeeded

The modeling candidate failed, but the source work did not.

The project now has reusable production logic for:

- historical physical-contact resolution;
- actual same-game league identity;
- exception-only official batter identity authority;
- terminal-PA result classification;
- frozen nine-group terminal values;
- MLB and affiliated-MiLB target materialization;
- batted-ball tracking provenance/capability tiers;
- cutoff-safe additive contact baselines;
- paired prediction geometry and transport diagnostics.

2023 terminal target support was 595,619 / 595,794 core terminal contacts, or 99.9706%.

That infrastructure remains useful for future research and does not depend on promoting Challenger 2.

### 7. The frozen validation contract did its job

A result of:

- MSE better in 3/3 confirmation folds;
- MiLB MSE better;
- all meaningful exact non-MLB transport guardrails passing;

would have been easy to describe as a successful confirmation after the fact.

The predeclared MAE and calibration gates prevented that retrospective rationalization. The binding result is therefore:

`confirmed = false`

No Challenger-2 rescue tuning, coefficient adjustment, feature reselection, or threshold relaxation may use 2023 outcomes.

## Data-use consequence

The 2023 Challenger-2 confirmation set is no longer untouched. It may be used as development/diagnostic evidence for a genuinely new future research question, but it can never again serve as an independent confirmation surface for a Current Talent challenger derived from these findings.

A future Current Talent challenger must declare a new untouched confirmation period before development begins.

## Strategic decision

Do **not** begin Challenger 3 immediately.

The observed Current Talent incremental gain is real but small, while the project still lacks the larger downstream layers required for a universal ranking.

Proceed next to **Projection**, starting from frozen Baseline 2 and keeping future aging/development separate from present rate talent and from playing time.

Return to richer Current Talent only after Projection/Player Value foundations exist or if a materially different source/feature hypothesis emerges.
