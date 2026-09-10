# Pitcher role-probability 2025 audit plan

Status: frozen before score.

## Question

Are the existing starter, swingman, and reliever probabilities a major source of
pitcher-prospect value compression?

## Population and target

Use the saved March 27, 2025 historical forecast and completed official 2025 MLB
pitching totals. Score only pitchers with positive 2025 MLB BF, because role is
conditional on being active. Starter means at least half of games are starts, reliever
means zero starts, and swingman is the remainder—the same production definition.

Report all active pitchers and the subset with no MLB BF before 2025. The latter is
the prospect-facing audit; it is a diagnostic subgroup and cannot change the model by
itself.

## Scores

Report three-class log loss, multiclass Brier, exact role accuracy, predicted versus
observed role shares, and five-bin starter-probability reliability. Include counts by
forecast coverage tier and recent role.

This is a calibration audit, not a challenger selection. No current 2026 outcome,
outside FV, organization depth, contract, or subjective starter label is allowed.
