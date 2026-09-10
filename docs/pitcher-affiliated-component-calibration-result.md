# Pitcher affiliated component-calibration result

Status: reject the calibration; retain the current component profiles.

The 2024 development offset raised strikeouts and `other` while lowering HBP and HR
in centered-log-ratio space. It was frozen and applied without adjustment to the
2025 confirmation population of 146 pitchers and 17,852 MLB BF.

The candidate failed both required scores. Relative to the incumbent, component log
loss worsened by 0.000167 and Brier worsened by 0.000158. The player-bootstrap Brier
interval is entirely above zero; the log-loss interval spans zero.

The candidate moved the cohort's BF-weighted run estimate from 10.3 runs below
average per 800 BF to 4.3 below, closer to the observed 6.4 below. But that attractive
average hid worse probability accuracy and made the top predicted quintile too
optimistic: 3.0 runs above average predicted versus 2.9 below observed.

## Decision

Do not apply the component intercept. The proper-score failure takes precedence over
matching one aggregate run number. Keep the role model, translated component method,
and 800-BF prior. Audit the conversion from expected controlled WAR to pitcher FV
before changing pitcher talent estimates.

No 2026 outcome, contract value, outside FV, subjective prospect label, or target-year
organization context was used. Machine-readable detail:
`docs/pitcher-affiliated-component-calibration-result.json`.
