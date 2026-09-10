# Prospect conditional career-hurdle audit plan

Status: frozen before outer scoring.

## Question

Can one coherent nested hurdle produce better-supported prospect career probabilities than three separately fitted unconditional models?

## Stages

The arrival stage retains the previously audited arrival model. This audit tests the next two stages separately:

1. `P(meaningful role | arrived within two years)` among observed arrivals only.
2. `P(established role | meaningful role within two years)` among observed meaningful players only.

Unconditional probabilities are later formed only by multiplication. Therefore arrival is always at least meaningful, and meaningful is always at least established, without clipping.

## Chronology

- Development selection: train the 2018 snapshot and score the 2021 snapshot.
- Outer test: train 2018 plus 2021 and score the 2023 snapshot.
- A two-year outcome is used only when its full window is complete before the relevant outer forecast year.
- 2026 remains closed.

## Candidate grid

Within each player type and stage, test only these already implemented, baseball-motivated feature families:

- core age, level, role, workload, history, production rates, and 40-man state;
- baseball development/role interactions;
- Rule 4 draft/signing pedigree;
- baseball interactions plus pedigree.

For each family test logistic shrinkage `C = 0.1` and `1.0`, and production-rate regression of `0` and `50` PA/BF. The incumbent is core, `C = 1`, no extra production regression. Select on development log loss only when Brier score is no worse.

Birth country, current physical measurements, outside FV, organization, catcher preference, and future team depth are excluded. International signing path may appear only as the existing entry-path indicator inside pedigree—not as a direct quality bonus.

## Required reporting

- Identical conditioned cohorts for every candidate.
- Proper scores, calibration, and paired bootstrap intervals.
- Sample size and positive count at every stage.
- Supported level, age, and workload diagnostics.
- No current value change unless both conditional stages are credible and the full multiplied path passes a separate value test.

Tiny conditional samples, unstable calibration, or outer-score reversal are rejection conditions, not invitations to tune on the outer result.

