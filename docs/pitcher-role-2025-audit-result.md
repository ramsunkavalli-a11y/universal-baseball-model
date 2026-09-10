# Pitcher role-probability 2025 audit result

Status: role probabilities retained; not the main prospect-compression cause.

## All active pitchers

The saved March 27 forecast matched 801 pitchers with positive official 2025 MLB BF.
Three-class log loss is 0.689, multiclass Brier is 0.387, and exact role accuracy is
74.0%.

| Role | Predicted share | Observed share |
|---|---:|---:|
| Starter | 30.4% | 31.0% |
| Swingman | 14.5% | 15.0% |
| Reliever | 55.1% | 54.1% |

Starter reliability is strong across five bins. The highest bin predicted 81.6%
starters and observed 80.0%; the middle bin predicted 14.7% and observed 14.4%.

## No-prior-MLB group

Among 137 active pitchers with no MLB BF before 2025, predicted starter share is 27.5%
and observed share is 27.0%. Reliever share is 58.6% predicted versus 56.9% observed.
Log loss is 0.764, Brier is 0.431, and exact role accuracy is 69.3%. Individual bins
are noisier at 27-28 players, but there is no broad starter-probability suppression.

## Decision

Retain the role probabilities. They should not be raised merely to create more high-FV
pitcher prospects. The remaining compression is more likely in translated WAR rate,
career-quality/workload interaction, or the pitcher FV mapping. Test those separately.

No current 2026 outcome, outside FV, organization depth, contract, or subjective role
label was used. Machine-readable detail: `docs/pitcher-role-2025-audit-result.json`.
