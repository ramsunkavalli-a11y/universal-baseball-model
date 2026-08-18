# Defense v1 development checkpoint

Last updated: 2026-08-18

Status: **PRE-2025 DEVELOPMENT CLOSED — TRACKED GATE COMPLETE; FINAL REFIT / PARAMETER FREEZE NEXT.**

This is the active Defense-v1 development handoff. The final pre-2025 tracked challenger has been scored under the frozen contract. No additional Defense-v1 development challenger is authorized.

## Binding tracked challenger result

Governing contract: `docs/defense-v1-tracked-challenger-contract.md`.

Binding result: `docs/defense-v1-tracked-challenger-result.json`.

Successful scoring run:

- workflow: `Defense v1 tracked challenger scoring`;
- run id: `32196115227`;
- conclusion: `success`;
- scoring SHA: `ace1df97001b83b91a1a1021637c604ebdea6399`;
- frozen tracked source run: `32182019495`;
- frozen tracked source SHA: `5438e905d24e2167432a52253320ccbc978186b8`.

The workflow downloaded the already-certified historical fielding artifact and frozen tracked-source artifact, verified the pinned tracked parquet SHA-256 values, and executed the staged scorer without changing its statistical gates.

## General tracked range — TIER A PASSED / TIER B NOT ACCEPTED

Incumbent: selected universal **U1**, lambda `0.0`.

Challenger: **T1 = exact U1 + tracked_range_z**.

### MLB / Tier A gate

T1 beat U1 on MSE in all three frozen held folds:

- 2022: `0.83749 -> 0.80983` — **3.30% improvement**, 140 held players;
- 2023: `0.86863 -> 0.85218` — **1.89% improvement**, 133 held players;
- 2024: `0.97975 -> 0.97191` — **0.80% improvement**, 141 held players.

Pooled:

- U1 MSE `0.89594`;
- T1 MSE `0.87864`;
- **1.93% pooled MSE improvement**;
- pooled Spearman `0.23611 -> 0.24791`, delta **+0.01180**;
- all count, fold guardrail, direction, rank-correlation, and finite-value gates passed.

**Binding decision: Tier-A tracked range PASSED.** MLB tracked Defense v1 may retain T1.

### MiLB -> MLB / Tier B transfer gate

The predeclared transfer diagnostic was attempted only after Tier A passed. The exact frozen eligibility join produced `0` transfer players, so the result is:

`insufficient_transfer_evidence`

Under the frozen contract, insufficient evidence is not a pass and there is no rescue/reselection path.

**Binding decision: Tier-B tracked range NOT ACCEPTED.** Tracked MiLB remains on universal U1 range for Defense v1.

### Independent Tier-B cohort sanity check

Diagnostic result: `docs/defense-v1-tier-b-cohort-audit.json`.

A separate diagnostic implementation reproduced the frozen 2023-MiLB -> 2024-MLB eligibility path without calling the scorer's transfer-subset function. It matched the binding transfer count exactly and showed where the cohort disappears:

- 164 players had 2023 U1-eligible evidence plus a matching-position 2024 Savant OAA target;
- 161 had already reached MLB in 2023 and were excluded by the frozen Tier-B definition;
- only 3 remained non-MLB: Leo Jiménez (AAA, SS), Trey Sweeney (AA, SS), and Trey Lipscomb (AA, 3B);
- Jiménez was the only one with any 2023 tracked MiLB range row, and it was at the exact U1 position, but it did not meet the frozen raw `>=100` OAA-opportunity requirement;
- Sweeney and Lipscomb had no 2023 tracked MiLB range row in the frozen source;
- therefore 0 players reached an eligible `tracked_range_z`, independently reproducing the binding `0` transfer population.

This confirms that the Tier-B result is driven by sparse overlap under the predeclared eligibility contract rather than a player/position join mismatch. It does **not** convert insufficient evidence into a pass or authorize changing the frozen thresholds.

## Tracked catcher framing — FAILED / CLOSED

Baseline: **F0 = neutral framing z = 0**.

Challenger: **F1**, the frozen one-feature unpenalized `tracked_framing_z -> framing_target_z` model.

Fold results:

- 2022: F1 MSE `1.22360` vs F0 `1.12932` — **8.35% worse**, 24 held catchers;
- 2023: `0.96052` vs `1.13651` — **15.49% better**, 30 held catchers;
- 2024: `0.86047` vs `1.02263` — **15.86% better**, 41 held catchers.

Pooled:

- F0 MSE `1.08554`;
- F1 MSE `0.98380`;
- **9.37% pooled MSE improvement**;
- F1 pooled Spearman `0.24101`;
- F1 beat F0 in 2 of 3 folds.

However, the frozen gate allowed no fold to be more than 5.0% worse. The 2022 fold was **8.35% worse**, so the guardrail fails despite the favorable pooled result.

**Binding decision: Tier-A tracked framing FAILED and is CLOSED for Defense v1.** The MiLB transfer diagnostic was correctly not attempted after the MLB failure; Tier-B tracked framing is therefore also not accepted. No framing rescue or retuning is authorized.

## Retained pre-2025 Defense-v1 component set

### General range

- **Tier A — MLB tracked:** T1 (`U1 + tracked_range_z`).
- **Tier B — tracked MiLB:** U1 only; tracked range transfer was insufficient.
- **Tier C — untracked affiliated MiLB:** U1 only.

### Catcher components

- blocking: selected universal **C2**;
- throwing: selected universal **C1**;
- tracked framing: **closed / not retained** for Defense v1.

### Closed development paths

- age challenger A1: failed / closed;
- rejected traditional features: closed;
- tracked framing F1: failed / closed;
- Tier-B tracked range: not accepted for insufficient transfer evidence;
- additional pre-2025 challenger search: not authorized.

Missing tracking remains missing evidence, not observed average/zero defensive skill.

## Exact next sequence

The binding result explicitly authorizes **final refit and parameter freeze next** while keeping 2025 confirmation and WAR/value unauthorized.

Next batch:

1. Refit only the retained Defense-v1 components on all authorized 2022–2024 development responses.
2. Freeze exact normalization moments, coefficients, coverage/fallback rules, package versions, parameter hashes, and component provenance.
3. Freeze the one-shot 2025 Defense-v1 confirmation contract before any completed-2025 defensive source/target is opened.

Only after that freeze may a separate source-only workflow materialize completed-2025 defensive targets for confirmation.

## Binding boundaries

- **Do not access 2025 defensive source/targets yet.**
- **Do not calculate WAR/value yet.**
- Do not add another Defense-v1 development challenger.
- Do not rescue tracked framing, age, or rejected traditional features.
- Do not promote tracked range to Tier B without the failed/insufficient frozen transfer gate.
- Do not infer proprietary MiLB OAA truth from the public tracked proxy.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.
