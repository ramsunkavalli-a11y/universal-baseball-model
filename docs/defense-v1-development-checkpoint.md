# Defense v1 development checkpoint

Last updated: 2026-08-18

Status: **FINAL PRE-2025 TRACKED CHALLENGER READY TO SCORE — SOURCE GATE PASSED.**

This is the active Defense-v1 development handoff. The tracked source has been materialized under the frozen contract, persisted with hashes, and independently completed successfully. No tracked challenger score has been accepted yet.

## Binding source result

Governing contract: `docs/defense-v1-tracked-challenger-contract.md`.

Binding source record: `docs/defense-v1-tracked-source-result.json`.

Successful source run:

- workflow: `Defense v1 tracked source materialization`;
- run id: `32182019495`;
- conclusion: `success`;
- source branch: `source-certification-poc`;
- source SHA: `5438e905d24e2167432a52253320ccbc978186b8`.

The source result explicitly records:

- `tracked_source_materialized = true`;
- `tracked_challenger_scoring_authorized_next = true`;
- `2025_confirmation_authorized = false`;
- `war_value_authorized = false`;
- no 2025 source access;
- no 2025 defensive-target access;
- no model fit during source materialization;
- no source-filter change from the frozen contract.

## Persisted tracked artifacts

### Range

`reports/generated/defense-v1-tracked-source/tables/tracked_range_proxy_2021_2023.parquet`

- rows: `6,872`;
- SHA-256: `a65cb6f7506d5e100c9f0b088fb276eecc1dab5599592dd477bfcc030d850a3e`.

### Framing

`reports/generated/defense-v1-tracked-source/tables/tracked_framing_proxy_2021_2023.parquet`

- rows: `579`;
- SHA-256: `1071b9d8209d6e9ba9d8c2b42ac7b99e3329387704e2910797b58f1a148cbc79`.

Materialized predictor scope remains exactly frozen:

- MLB regular seasons: 2021, 2022, 2023;
- tracked MiLB transfer input: 2023 regular season;
- MiLB transport: `minors=true` with client-side official level identity;
- SportsDataverse `0.0.75` range and framing implementations;
- no 2024 tracking predictor pull;
- no 2025 source or target access.

## Frozen challenger to run next

Scoring code is already staged at:

`scripts/audit_defense_v1_tracked_challenger.py`

Run it against the persisted, hash-verified tracked artifacts without re-querying or changing source filters.

### General range

Incumbent: selected universal **U1**, lambda `0.0`.

Challenger: **T1**, the exact U1 pipeline plus only `tracked_range_z`.

The frozen MLB gate compares U1 and T1 on identical tracked-eligible rows in 2022, 2023, and 2024 grouped leave-one-target-year-out folds. If T1 passes MLB, run only the predeclared 2023-MiLB -> 2024-MLB transfer diagnostic. Tier-B tracked range is accepted only if that transfer gate also passes.

### Catcher framing

Baseline: **F0**, neutral framing z = 0.

Challenger: **F1**, an unpenalized one-feature linear model from `tracked_framing_z` to next-year Savant `framing_target_z`.

If F1 passes the frozen MLB development gate, run only the predeclared 2023-MiLB -> 2024-MLB catcher transfer diagnostic. Tier-B framing is accepted only if that transfer gate also passes.

No incumbent universal feature/model reselection is authorized during this gate.

## Already settled Defense-v1 development

- Universal general range: **U1, lambda `0.0` selected**.
- Universal catcher blocking: **C2 selected**.
- Universal catcher throwing: **C1 selected**.
- Age challenger A1: **failed / closed**.
- Traditional feature search: **closed**.
- Catcher framing source feasibility: **passed**.
- Tracked MiLB transport/execution coverage: **passed**.
- Final tracked source materialization: **passed**.

After the tracked challenger score, there are no additional planned pre-2025 development challengers.

## Exact next sequence

1. Execute the frozen tracked challenger scorer using the persisted source artifacts and pinned hashes.
2. Accept or close tracked range and tracked framing exactly by the predeclared MLB and, when applicable, MiLB-transfer gates.
3. Refit only retained Defense-v1 component(s) on all authorized 2022–2024 development responses.
4. Freeze normalization moments, coefficients, coverage/fallback rules, package versions, parameter hashes, and the exact 2025 confirmation contract.
5. Only after that freeze may a separate source-only workflow materialize completed-2025 defensive targets for one-shot confirmation.

## Binding boundaries

- **Do not access 2025 defensive source/targets yet.**
- **Do not calculate WAR/value yet.**
- Do not change the frozen tracked source filters after seeing challenger results.
- Do not add a new Defense-v1 challenger after this gate.
- Do not rescue age or previously rejected traditional features.
- Do not infer proprietary MiLB OAA truth from public tracked proxies.
- Missing tracking remains missing evidence, not average/zero defensive skill.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.
