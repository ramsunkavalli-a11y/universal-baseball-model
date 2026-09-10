# Prospect post-arrival workload progression plan

Status: frozen before scoring.

## Question

After a prospect first reaches MLB, does prior-season MLB workload improve the next
career-state advancement forecast beyond age and elapsed time?

This is a one-year transition test for players already in the fringe or meaningful
MLB state. It does not use future workload in a multi-year forecast. Its purpose is to
test whether an annually updated, linked career simulator needs to carry realized MLB
workload forward.

## Frozen method

- Build monotone annual state rows from the 2018, 2019 and 2021 pre-MLB snapshots and
  deduplicate the same player/outcome year using the latest valid snapshot.
- Exclude 2020 outcome rows because the shortened MLB schedule changes the career-state
  opportunity available in that target year.
- Join only the immediately preceding MLB season's official PA or BF.
- Normalize workload by mean workload among active MLB hitters or pitchers in that
  same season; retain a separate prior-active indicator.
- Fit separate fringe-to-higher and meaningful-to-established logistic models.
- Compare age plus elapsed-time baseline with baseline plus normalized prior workload.
- Select regularization from `0.03, 0.1, 0.3, 1.0` on the 2023 outcome, then score
  2024 and 2025 unchanged.
- Report log loss, Brier score and deterministic player-paired 95% bootstrap intervals.

The workload candidate passes a player-type/origin cell only if both development point
scores improve and both later years have upper paired bounds below zero for both proper
scores. Current 2026 data, organization and outside FV are excluded. A pass supports
future linked simulation design only; it cannot directly change current values.

