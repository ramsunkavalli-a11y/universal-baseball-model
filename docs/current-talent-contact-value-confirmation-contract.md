# Current Talent Challenger 2 — fixed 2023 confirmation contract

Status: **FROZEN BEFORE 2023 PERFORMANCE SCORING**  
Date frozen: 2026-08-17

This document resolves the final acceptance semantics for the one fixed 2023 confirmation authorized by the governing Challenger-2 plan.

No 2023 Challenger-2 MSE, MAE, calibration coefficient, transport score, fold win, or promotion/confirmation decision had been computed when this contract was frozen.

## Candidate and comparator

Candidate:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

Comparator:

frozen conditional contact-value baseline

`terminal_value ~ contact_bin + level_group`

with fixed references `IFFB` and `MLB`, fit separately at each confirmation cutoff using accepted valued contacts strictly before that cutoff.

## Frozen confirmation model state

Use exactly the accepted refit in:

`docs/current-talent-contact-value-confirmation-refit-result.json`

Training snapshots:

- `2021-07-15`
- `2022-07-15`

Frozen feature standardization:

- mean EV: `87.56765458046604`
- EV scale: `3.087267010464925`
- mean sweet-spot share: `0.34421856089476915`
- sweet-spot scale: `0.0629687444393524`

Frozen residual coefficients:

- beta EV: `0.019444311355484883`
- beta sweet-spot: `-0.0016659086163438607`

**Documentation correction, 2026-08-17:** the first version of this contract transcribed stale numerical values in the bullets above. The authoritative refit was already fixed by successful workflow run `32079555373` before any 2023 source workflow began; its artifact and the persisted refit result both contain the values shown here. This correction changes documentation only. It does not refit, select, tune, or use any 2023 performance result; no 2023 Challenger-2 loss or confirmation decision had been computed at correction time.

No coefficient, standardization moment, feature, threshold, target group, value scale, baseline form, or capability grouping may be changed using 2023 evidence.

## Fixed confirmation folds

Exactly:

- `2023-07-15`
- `2023-08-01`
- `2023-09-01`

At each cutoff:

- features use only tracked BBE with `game_date < cutoff`;
- the additive comparator baseline uses only accepted valued contacts with `event_date < cutoff`;
- future target is exactly `[cutoff, cutoff + 90 calendar days)`;
- comparator and richer are scored on identical richer-eligible target events;
- the frozen confirmation residual coefficients are applied unchanged.

## Scoring

Reuse the development scoring definitions exactly:

- primary: event-weighted MSE on `terminal_value`;
- secondary guardrail: event-weighted MAE;
- fold selection statistic: arithmetic mean of the three fold scores, not pooled-event loss;
- calibration per model/fold: `terminal_value = intercept + slope * predicted_terminal_value`;
- transport: overall, any-observed-MiLB evidence, and each exact non-MLB `source_capability_tier` represented in the paired cohort.

## Confirmation acceptance rule

To avoid introducing a new post-development standard, **reuse all ten frozen 2022 promotion checks unchanged** on the three 2023 confirmation folds.

The candidate is confirmed only if all are true:

1. richer has lower equal-fold mean event-weighted MSE than comparator;
2. richer equal-fold mean MAE is no worse than comparator, tolerance `1e-12`;
3. richer MSE wins at least **2 of 3** confirmation folds;
4. comparator and richer have identical paired event coverage in every fold;
5. any-observed-MiLB-evidence cohort has at least **1,000 total fold target contacts** and lower equal-fold mean MSE for richer;
6. for every exact non-MLB capability tier with at least **1,000 total fold target contacts**, fail if richer is worse on **both MSE and MAE in at least 2 of 3 folds**;
7. frozen richer coefficient fit remains finite/full-rank;
8. all required confirmation calibration fits are finite/identifiable;
9. richer mean absolute calibration-intercept error is <= `1.25 ×` comparator;
10. richer mean absolute calibration-slope error is <= `1.25 ×` comparator.

No ECE threshold is used.

## One-shot boundary

The confirmation is one-shot.

If any check fails:

- Challenger 2 fails confirmation;
- do not change features, eligibility, source-capability grouping, outcome groups, value scale, baseline formula, standardization, coefficients, thresholds, or acceptance rules;
- do not rerun a modified candidate against 2023 as a rescue.

If all checks pass:

- Challenger 2 is confirmed as a **separate Current Talent contact-quality dimension** only;
- it still does not automatically alter B2's 12-bin profile or enter Performance, Projection, defense, playing time, WAR, Player Value, or Overall Ranking;
- a later integration contract is required before any such use.

## Required source/pre-scoring gates

Before the one confirmation score is run, require:

1. accepted 2023 contact-value target source with the same frozen terminal semantics;
2. accepted confirmation tracking chronology with exact observed capability provenance and no imputation;
3. frozen terminal values attached unchanged;
4. all three 2023 cutoff baselines full-rank and cutoff-safe;
5. confirmation features standardized with the frozen 2021+2022 moments;
6. exact richer eligibility and paired-event coverage proved before loss calculation;
7. confirmation predictions finite and use the frozen confirmation coefficients;
8. no prior 2023 Challenger-2 performance score exists.
