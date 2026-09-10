# Pitcher affiliated component-calibration plan

Status: frozen before score.

## Question

Can one transparent calibration of the translated pitcher component mix remove the
shared run-rate bias without weakening player-level regression or using prospect
opinions?

## Method and chronology

Build the incumbent 800-BF translated profiles for pitchers with affiliated evidence
and no prior MLB BF. On the 2024 development target, calculate one additive
centered-log-ratio offset between the BF-weighted predicted five-part profile and the
observed MLB profile. Apply that frozen offset to every 2025 prediction and renormalize
the five probabilities together.

Translation fitting and player evidence for 2024 may use 2023 only. Translation
fitting and player evidence for 2025 may use 2023-2024, but the calibration offset
must remain the one learned from 2024 outcomes. Target membership is never a feature.

## Gate

Compare the calibrated candidate with the unchanged 800-BF incumbent on 2025
component log loss and component Brier score. Promote only if both improve. Report
player-bootstrap intervals, component calibration, and neutral runs-above-average
diagnostics. Do not tune the calibration strength after viewing 2025.

No current 2026 outcome, contract value, outside FV, subjective prospect label, or
target-year organization context is allowed.
