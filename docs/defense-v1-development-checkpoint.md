# Defense v1 development checkpoint

Last updated: 2026-08-18

Status: **PRE-2025 PARAMETERS FROZEN — CONFIRMATION CONTRACT LOCKED; SOURCE MATERIALIZATION NEXT.**

This is the active Defense-v1 handoff. Pre-2025 model development is closed, the retained components have been refit on all authorized 2022–2024 development responses, and the one-shot 2025 confirmation rules were frozen before any new confirmation source was opened.

## Binding tracked challenger result

Governing contract: `docs/defense-v1-tracked-challenger-contract.md`.

Binding result: `docs/defense-v1-tracked-challenger-result.json`.

Successful scoring run:

- workflow: `Defense v1 tracked challenger scoring`;
- run id: `32196115227`;
- scoring SHA: `ace1df97001b83b91a1a1021637c604ebdea6399`;
- frozen tracked source run: `32182019495`;
- frozen tracked source SHA: `5438e905d24e2167432a52253320ccbc978186b8`.

### General tracked range

**Tier A / MLB passed.** T1 = exact U1 + `tracked_range_z`.

- 2022: U1 MSE `0.83749` -> T1 `0.80983` — 3.30% better, n=140;
- 2023: `0.86863 -> 0.85218` — 1.89% better, n=133;
- 2024: `0.97975 -> 0.97191` — 0.80% better, n=141;
- pooled MSE improvement: **1.93%**;
- pooled Spearman delta: **+0.01180**.

**Tier B / tracked MiLB was not accepted.** The frozen 2023-MiLB -> 2024-MLB diagnostic produced `0` eligible transfer players and therefore `insufficient_transfer_evidence`.

Independent diagnostic: `docs/defense-v1-tier-b-cohort-audit.json`.

That audit independently reproduced the `0` and showed the funnel was 164 U1/2024-target matches -> 3 non-MLB players -> 1 with any matching tracked MiLB row -> 0 meeting the frozen >=100 OAA-opportunity rule. This is a sparse-overlap limitation, not evidence that tracked MiLB range failed and not a reason to reopen the gate.

### Tracked catcher framing

**Failed / closed.** F1 improved pooled MSE 9.37% and beat F0 in two folds, but the 2022 fold was 8.35% worse than F0, breaching the frozen 5% maximum fold-degradation guardrail. No rescue or transfer test is authorized.

## Frozen pre-2025 parameter package

Confirmation contract: `docs/defense-v1-2025-confirmation-contract.md`.

Binding parameter package: `docs/defense-v1-confirmation-parameters.json`.

Successful freeze:

- workflow: `Defense v1 pre-2025 parameter freeze`;
- binding successful run: `32198466409`;
- freeze SHA: `38c751b044ed994b3a0f5aebf437a8e732c76699`;
- parameter hash: `sha256:cba6b7ebe4b2598db2c4d9ef360b0784f23a94ad61385f87149b08c46e0390d5`;
- confirmation-contract SHA-256: `5229fb29730f29ab5421978dfe580f5a426e9f6c7b4740d3ab7ffad54bb831aa`;
- deterministic reproduction: passed exactly;
- SportsDataverse: `0.0.75`;
- NumPy: `2.5.2`;
- Polars: `1.43.2`;
- Python: `3.12.13`.

The freeze reused certified historical fielding run `32148467330` and frozen tracked source run `32182019495`; no 2024 confirmation tracking source and no 2025 defensive target was accessed during parameter fitting.

### Frozen retained forms

General universal U1, lambda `0.0`:

- training rows: 490;
- coefficient vector including intercept: `[0.02039840, -0.32498386, 0.29206770, -0.36164372, -0.06792589]`;
- features: `fielding_pct_z`, `range_factor_per_9_z`, `errors_per_9_z`, `throwing_errors_per_9_z`.

MLB tracked T1, lambda `0.0`:

- training rows: 414;
- coefficient vector including intercept: `[0.01625615, -0.39320465, 0.27778113, -0.45775108, -0.04063339, 0.14944763]`;
- exact U1 feature set plus `tracked_range_z`;
- retained for eligible MLB tracking only.

Catcher throwing C1:

- training rows: 197;
- coefficient vector including intercept: `[-0.05004551, 0.22111291]`;
- frozen catcher input mean/SD for CS%: `0.25125567 / 0.09338150`.

Catcher blocking C2:

- training rows: 193;
- coefficient vector including intercept: `[-0.25623850, -0.52647108]`;
- frozen catcher input mean/SD for PB/9: `0.17241686 / 0.13913792`;
- prior-season recency weight remains `0.5`, exposure-weighted by fielding outs.

The package also persists all general position × level normalization moments, position/global fallbacks, exact training rows, development targets, historical tracked-range moments, table hashes, source manifests, and coverage rules.

## Frozen production/confirmation fallback hierarchy

### General range

1. eligible MLB row + eligible MLB tracking -> T1;
2. eligible MLB row without eligible tracking -> U1;
3. eligible affiliated MiLB row -> U1, regardless of public tracking availability;
4. insufficient U1 evidence -> explicit `insufficient_evidence` / neutral position-relative B0 for this component.

Tracked MiLB T1 remains closed for v1.

### Catcher

- throwing: C1 when eligible; otherwise neutral/insufficient B0;
- blocking: C2 when eligible; otherwise neutral/insufficient B0;
- tracked framing: closed / absent, not fabricated as observed average talent.

## Frozen one-shot 2025 confirmation hierarchy

The governing rules are now immutable in `docs/defense-v1-2025-confirmation-contract.md`.

1. Confirm U1 against neutral B0 on the untouched 2024-input -> 2025 Savant range population.
2. Only if U1 confirms, test T1 incrementally against U1 on identical eligible 2024 MLB tracked rows. Fewer than 75 tracked rows is insufficient evidence, not a pass.
3. Confirm C1 throwing against B0 on the frozen catcher population; fewer than 30 is insufficient evidence.
4. Confirm C2 blocking against B0 on the frozen catcher population; fewer than 30 is insufficient evidence.
5. Failed/insufficient components fall back exactly as predeclared; there is no 2025 refit, rescue, family substitution, threshold movement, or recalibration.

## Exact next sequence

Parameter fitting is finished. The next work is source-only and then one-shot scoring:

1. Materialize **2024 MLB tracked-range predictor evidence only** under the frozen T1 source rule. No 2025 target and no scorer in that workflow.
2. Materialize completed-2025 Savant range/throwing/blocking targets in a separate source-only workflow. No model parameters or scorer in that workflow.
3. Only after both source artifacts certify successfully, score the one-shot 2025 confirmation from the frozen parameter package with no fitting.
4. Freeze the final confirmed/fallback Defense-v1 component set.
5. Only after Defense v1 is final may the later run-conversion / positional-adjustment / WAR-value work begin.

## Binding boundaries

- **Pre-2025 parameter selection and refit are closed.**
- **2025 defensive targets have not yet been accessed.**
- Do not refit or reselect against 2025.
- Do not add another Defense-v1 development challenger.
- Do not rescue tracked framing, age, rejected traditional features, or Tier-B tracked range.
- Do not infer proprietary MiLB OAA truth from the public tracked proxy.
- **Do not calculate WAR/value yet.**
- Playing Time v1 and Position/Role v1 remain frozen and untouched.
