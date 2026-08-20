# Player Value v1 advancement source recertification contract

Status: **AUTHORIZED, NARROW SOURCE-DRIFT ADJUDICATION**

## Purpose

Recover deterministic numerical centering after Baseball Savant regenerated its historical baserunning-run-value CSVs following the original advancement certification. This gate may freeze a new immutable copy of the model-relevant history only when the correction is demonstrably immaterial to the already-frozen model decision.

## Frozen decision that may not change

- non-steal advancement model: `A2_k25`;
- history family, recency weights, and prior strength are unchanged;
- no candidate may be added, removed, refit, or promoted;
- no 2025 data may be accessed;
- realized 2024 advancement remains confirmation-only and may not enter the 2024 projection history.

Candidate scoring is replayed solely as an invariance audit. It is not a new selection gate.

## Authorized source and frozen output

Query the existing certified Baseball Savant baserunning-run-value endpoint for 2019–2024 using the exact existing query builder and parser. Freeze only these projection-relevant columns, sorted by `season, player_id`:

- `season`;
- `player_id`;
- `runs_xb` from `runner_runs_xb`;
- `opportunities_xb` from `n_runner_moved_xb`.

The workflow must upload the resulting Parquet table as an immutable GitHub Actions artifact and record the run ID, artifact ID, artifact digest, row count, and a canonical model-input SHA-256 in the committed result document.

## Required invariance gates

All must pass:

1. Each 2019–2024 row count equals the original certified row count.
2. Development scoreable counts and opportunity totals for 2022 and 2023 are unchanged.
3. Confirmation scoreable count and opportunity total for 2024 are unchanged.
4. The frozen `A2_k25` remains the unique development winner under the existing scoring code.
5. The frozen `A2_k25` still beats `A0_neutral` in 2024 confirmation.
6. No development or confirmation primary-score relative drift may exceed `0.001` (0.1%).
7. Every emitted value is finite; opportunities are nonnegative; player-season keys are unique.

If any gate fails, do not upload or freeze a replacement source.

## Downstream boundary

Passing this gate authorizes the numerical-centering materializer to consume the newly frozen advancement-history artifact while retaining `A2_k25`. It does not authorize changes to steal models, batting, defense, position, membership, replacement, park adjustment, or WAR. Park-neutrality remains closed until the centering residual passes `1e-10` and `docs/player-value-v1-mlb-centering-2024.json` is frozen.
