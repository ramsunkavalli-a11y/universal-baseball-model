# Prospect upper-tail calibration plan

Status: frozen before first score.

## Question

Do simple, chronology-safe probability recalibrations improve the deployed prospect
career hurdle, especially its high-probability tail?

## Frozen models and chronology

Test the deployed core models only: arrival, meaningful given arrival, and established
given meaningful for hitters and pitchers. Preserve the hitter established model's
existing `C=.1` and 50 PA rate regression; all other stages use `C=1`.

- Fit each base model on the 2018 origin cohort and score 2021.
- Fit calibration only on those 2021 predictions and completed outcomes.
- Refit the unchanged base model on 2018 plus 2021 and score the untouched 2023 origin
  cohort through completed 2025.
- Apply the frozen 2021 calibration to the 2023 probabilities. Do not refit calibration
  on 2023.

## Candidates and gate

Candidate 1 adjusts only the log-odds intercept. Candidate 2 is regularized Platt
calibration with one slope and intercept (`C=1`). Select on 2021 log loss with Brier as
a no-harm gate. On the 2023 outer check, require both log loss and Brier to improve.

Report proper scores, paired player bootstrap intervals, five equal-count reliability
bins, calibration coefficients, and the top-decile predicted versus observed rate.
No tail-only win can rescue worse full-cohort proper scores.

No outside FV, prospect rank, demographics, organization, or current outcome is used.
A passing stage authorizes a private current-probability sensitivity only.
