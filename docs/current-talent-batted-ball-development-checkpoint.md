# Current Talent batted-ball richer development checkpoint

Status: **DEVELOPMENT FAILED**

This checkpoint summarizes the fixed 2022 development gate for the first richer Current Talent challenger. It does not contain 2023 confirmation data and does not permit 2023 reselection.

## Frozen candidate

- Comparator: Baseline 2 `translated_multiseason_recency_empirical_bayes_v1`
- Challenger: `baseline2_plus_ev_sweet_spot_contact_residual_v1`
- Features: 180-day weighted mean EV + 8–32° sweet-spot share
- Model BBE: result-producing, non-bunt, complete EV+LA, pitch-grain
- Primary richer eligibility: >=20 complete tracked BBE
- Residual L2: 0.01; no penalty search
- Training snapshot: 2021-07-15 only
- Development folds: 2022-07-15 / 2022-08-01 / 2022-09-01
- Development workflow run: `32053829482`
- Tracking materialization run: `32046012977`
- Corrected source probe run: `32044627608`

## Proper scores — equal-fold mean

- B2 log loss: **2.267336438**
- Richer log loss: **2.267363114**
- Richer − B2 log loss: **0.000026676**
- B2 Brier: **0.872739291**
- Richer Brier: **0.872744733**
- Richer − B2 Brier: **0.000005442**
- Richer log-loss fold wins: **1/3**

Fold-level log-loss deltas, richer minus B2:

- 2022-07-15: **+0.000094**
- 2022-08-01: **+0.000085**
- 2022-09-01: **-0.000099**

The challenger therefore lost both proper-score means and did not meet the required 2-of-3 log-loss fold-win rule.

## Calibration guardrail

- B2 mean absolute intercept error: 0.359341
- Richer mean absolute intercept error: 0.363384
- B2 mean absolute slope error: 0.138630
- Richer mean absolute slope error: 0.140038

All required calibration fits converged and both 25% calibration guardrails passed. This is therefore a predictive rejection rather than an evaluator/calibration failure.

## Non-MLB transport

- Any-MiLB-evidence future core events: **168,030**
- Any-MiLB-evidence equal-fold mean log-loss delta: **+0.000038462**
- Any-MiLB-evidence supported and improves: **FAIL**

Meaningfully supported exact non-MLB capability tiers:

- `MILB_SAVANT_TRACKED:2021:123:SINGLE_A`: worse on both scores in 1/3 folds
- `MILB_SAVANT_TRACKED:2022:112:AAA`: worse on both scores in 1/3 folds
- `MILB_SAVANT_TRACKED:2022:117:AAA`: **worse on both scores in 3/3 folds**; 21,520 future core events
- `MILB_SAVANT_TRACKED:2022:123:SINGLE_A`: worse on both scores in 0/3 folds

The 2022 league-117 AAA exposure cohort triggers the predeclared transport failure rule.

## Promotion checks

- `all_component_calibration_fits_converged`: **PASS**
- `calibration_intercept_within_25pct_guardrail`: **PASS**
- `calibration_slope_within_25pct_guardrail`: **PASS**
- `identical_scored_coverage`: **PASS**
- `log_loss_wins_at_least_2_of_3`: **FAIL**
- `lower_equal_fold_mean_log_loss`: **FAIL**
- `no_meaningful_non_mlb_capability_tier_worse_on_both_in_2_folds`: **FAIL**
- `no_worse_equal_fold_mean_brier`: **FAIL**
- `non_mlb_evidence_cohort_supported_and_improves_log_loss`: **FAIL**

## Training fit

- Training players: 621
- Training future contact events: 69,388
- Initial mean contact log loss: 2.165238931
- Final mean contact log loss: 2.164789338
- Optimizer iterations: 139
- Converged: **PASS**

The residual fit did improve its 2021 training objective, but that improvement did not transport to the fixed 2022 development folds.

## Decision

Retain Baseline 2. **Do not inspect or run 2023 richer confirmation for this candidate.**

The rejected interpretation is specifically: mean EV + sweet-spot share should improve Current Talent by reshaping B2's ten conditional contact-direction/trajectory probabilities. The source evidence itself remains certified and reusable for a separately predeclared richer challenger.

The governing challenger plan explicitly anticipated a later alternative that treats batted-ball quality as a separate contact-quality/value latent target rather than forcing EV/LA to predict directional contact shape. Any such alternative must be frozen as a new development candidate before another 2022 evaluation.

Source report SHA-256: `f74c2439772bc4e6d607920481fcf19666ed63382f861012a7ac075e7f4fc64e`
