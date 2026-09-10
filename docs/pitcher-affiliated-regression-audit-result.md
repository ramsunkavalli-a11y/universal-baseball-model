# Pitcher affiliated-rate regression audit result

Status: retain the 800-BF prior.

The development fold selected 600 BF: its 2024 component log loss was 0.976576,
versus 0.976699 for the incumbent 800 BF, and its Brier score was also lower.
That choice was frozen before the 2025 confirmation was scored.

On 146 pitchers and 17,852 MLB BF in 2025, 600 BF failed confirmation. Relative
to 800 BF, component log loss worsened by 0.000080 while Brier improved by only
0.000007. Both player-bootstrap intervals cross zero. The candidate therefore fails
the predeclared requirement to improve both proper scores.

The run-rate diagnostic points to a different issue. The 800-BF model predicted this
arriving group at 10.3 neutral runs below average per 800 BF; it realized 6.4 below.
Reducing the prior to 600 BF moved the prediction farther away, to 12.1 below. The
top predicted quintile was close (2.4 below predicted, 1.8 below observed), while
the lower and middle groups were less orderly and noisier.

## Decision

Keep 800 BF. Do not inflate prospect pitching rates by weakening regression. Test a
single chronology-safe calibration of the translated five-component profile, because
the 2025 miss is shared across component rates and cannot be repaired defensibly by
changing FV cutoffs or role probabilities.

No 2026 outcome, contract value, outside FV, or subjective prospect label was used.
Machine-readable detail: `docs/pitcher-affiliated-regression-audit-result.json`.
