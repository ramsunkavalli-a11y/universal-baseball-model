# Hitter gradient 2026 confirmation plan

Status: **locked before evaluation**

The final decision is now defined before 2026 results are opened. The evaluator
will refuse to read a target file unless the caller explicitly declares the season
complete, the date is at least October 1, 2026, and the frozen forecast hash matches
the contract.

The comparison remains the gradient forecast versus the contact-only forecast for
the same players. A player enters the conditional-performance evaluation with at
least 30 completed 2026 terminal contacts. This test does not evaluate arrival or
playing time; those remain separate model components.

Production promotion requires all of the following:

1. Better overall player-rate RMSE, multinomial log loss, and Brier score.
2. A paired player-bootstrap 95% interval below zero for RMSE.
3. No workload, level-transition, or source-level group with at least 100 players
   that is materially worse on RMSE by more than 0.0005 and also worse on log loss.
4. No individual outcome with an RMSE deterioration greater than 0.002.

The workload groups are fixed at 30-74, 75-149, and 150-plus source contacts. The
level-transition groups are advancing, same-level, and demoted. All nine outcomes
will also be reported separately whether or not they affect the final gate.

These rules can be made stricter after evaluation but cannot be relaxed to rescue a
failed candidate.
