# Defense v1 development checkpoint

Last updated: 2026-08-18

Status: **DEFENSE V1 SKILL HIERARCHY FINAL AND FROZEN — RUN CONVERSION NEXT.**

This is the active Defense-v1 handoff. General range, catcher throwing, catcher blocking, and MLB catcher framing have completed their binding development/source/one-shot confirmation sequences. No further Defense-v1 skill tuning is authorized.

## Final production hierarchy

### General range

Binding original confirmation: `docs/defense-v1-2025-confirmation-result.json`.

1. eligible MLB + eligible certified tracking -> **T1**;
2. otherwise eligible MLB or affiliated MiLB -> **U1**;
3. insufficient U1 evidence -> explicit neutral B0.

2025 confirmation:

- U1 vs B0: n=161, MSE `1.01019 -> 0.97817`, MAE `0.81648 -> 0.79107`, Spearman `0.21670`;
- T1 vs U1 on identical tracked rows: n=135, MSE `0.91639 -> 0.91558`, MAE `0.76893 -> 0.75924`, Spearman `0.23750 -> 0.27474`.

Tracked MiLB T1 remains closed because the frozen transfer cohort was insufficient. Age and rejected traditional general-defense challengers remain closed.

General-range parameter package remains `docs/defense-v1-confirmation-parameters.json`, hash:

`sha256:cba6b7ebe4b2598db2c4d9ef360b0784f23a94ad61385f87149b08c46e0390d5`

Do not use the catcher portion of that old package after the catcher source repair.

## Corrected catcher source repair

Binding contract: `docs/defense-v1-catcher-source-repair-contract.md`.

The original Savant catcher throwing/blocking target source was not year-specific. The exact preregistered catcher development/search space was therefore rerun only after the current-UI snake_case `season_start` / `season_end` query semantics were certified and corrected 2022-2024 targets were materialized.

Prior invalid-source catcher results remain audit history and are not binding.

### Repaired catcher development

Binding result: `docs/defense-v1-catcher-repair-development-result.json`.

Throwing:

- C1 passed;
- C2 passed and had the lower pooled OOF MSE;
- selected **C2**;
- corrected training target folds had 77/74/79 scored rows;
- C2 pooled MSE `0.94531` vs B0 `1.00636` (about 6.1% better), with pooled Spearman about `0.291`.

Blocking:

- C1 passed;
- C2 passed and had the lower pooled OOF MSE;
- selected **C2**;
- corrected folds had 81/74/79 scored rows;
- C2 pooled MSE `0.85065` vs B0 `0.95330` (10.77% better), pooled Spearman `0.36154`.

No new catcher family, feature, threshold, or rescue was introduced.

### Repaired catcher parameter freeze

Binding package: `docs/defense-v1-catcher-repair-parameters.json`.

- parameter hash: `sha256:f4790bc1cb4df63d2ba65757455a4b6753e98d25fe552208d893958bdd19f328`;
- freeze run: `32206935150`;
- freeze SHA: `78c6eb74dcb3cd3b976c57d72d268d108457662c`;
- deterministic reproduction: passed;
- no repaired 2025 target was opened during fitting.

Frozen throwing C2:

- feature: `caught_stealing_pct`;
- global pre-2025 input mean/SD: `0.2512556726 / 0.0933814954`;
- coefficients `[0.0239271879, 0.3598147185]`;
- prior-season recency weight `0.5`;
- training rows: 230.

Frozen blocking C2:

- feature: `passed_balls_per_9`;
- global pre-2025 input mean/SD: `0.1724168589 / 0.1391379198`;
- coefficients `[-0.7000954223, -1.0240357909]`;
- prior-season recency weight `0.5`;
- training rows: 234.

**Throwing metadata audit note:** the package's `exposure` field says `fielding_outs`, but the preregistered `_catcher_matrix` implementation actually used `steal_attempts` as the C2 exposure weight for throwing, including the >=10 prior-season steal-attempt eligibility requirement. Those exact implementation semantics generated the frozen coefficients and were used in the 2025 confirmation. The frozen package/hash was not modified after 2025 access.

### Repaired 2025 catcher confirmation

Certified target source: `docs/defense-v1-catcher-repair-2025-source-result.json`.

Binding confirmation: `docs/defense-v1-catcher-repair-2025-confirmation-result.json`.

Run `32211517759`, scoring SHA `efa53c739e16f40a9de5797178d60a577dd744e8`.

Throwing C2 **confirmed**:

- n=79;
- B0 MSE `1.00000` -> C2 `0.88575`;
- B0 MAE `0.77838` -> C2 `0.70392`;
- Spearman `0.35827`.

Blocking C2 **confirmed**:

- n=78;
- B0 MSE `1.00000` -> C2 `0.83563`;
- B0 MAE `0.73114` -> C2 `0.67740`;
- Spearman `0.35975`.

Final catcher throwing/blocking hierarchy:

- eligible throwing -> **C2**, otherwise B0;
- eligible blocking -> **C2**, otherwise B0.

## Corrected catcher framing repair

The original framing development evidence was invalidated by the SportsDataverse 0.0.75 generic `year=...` framing query. The repair changed the target source only, using Baseball Savant's framing-specific `seasonStart` / `seasonEnd` semantics. The original F0/F1 family and all gates were unchanged.

### Repaired development and freeze

Binding development: `docs/defense-v1-framing-repair-development-result.json`.

Repaired MLB F1 passed the original development gate and was frozen. MiLB transfer evidence remained insufficient and was not accepted.

Binding package: `docs/defense-v1-framing-repair-parameters.json`.

- parameter hash: `sha256:e75ebd58d868b6cb6d51f2d0e48d49c1735a4cfa80661b6280269311a7875086`;
- freeze run: `32208751394`;
- freeze SHA: `fb7158e3a5e6048b12f7f42b4469560cfd767bfc`;
- coefficients `[-0.1287502167, 0.6904170177]`;
- training rows: 157;
- predictor: `tracked_framing_z`;
- tracked source feature requires >=500 takes and is standardized within source season x level, minimum cell n=15.

### Certified 2024 predictor source

Binding result: `docs/defense-v1-2024-framing-predictor-source-result.json`.

A segmented source-only recovery reconstructed the complete 2024 regular-season pitch set before deriving the frozen predictor:

- source run: `32208925985`;
- 711,898 regular-season pitch rows;
- 100 catcher framing proxies;
- 84 eligible 2024 MLB `tracked_framing_z` rows;
- no 2025 access, fitting, or scoring.

### Repaired 2025 framing confirmation

Certified target source: `docs/defense-v1-2025-framing-target-source-result.json`.

Binding confirmation: `docs/defense-v1-framing-2025-confirmation-result.json`.

Run `32211188620`, scoring SHA `9577d344fce305b158a852e9bb0d4366f01455dd`.

MLB F1 **confirmed**:

- n=48;
- F0 MSE `0.96655` -> F1 `0.63129`;
- F0 MAE `0.75272` -> F1 `0.66683`;
- F1 Pearson `0.59948`;
- F1 Spearman `0.55145`.

Final framing hierarchy:

1. eligible MLB catcher + eligible certified tracked framing -> **F1**;
2. MLB without eligible tracked framing -> **F0 neutral**;
3. affiliated MiLB -> **F0 neutral** because the frozen transfer sample was insufficient.

No additional framing tuning or confirmation rerun is authorized.

## What is closed

Defense-v1 skill development/selection/confirmation is complete.

Do not:

- reopen general U1/T1;
- reopen tracked MiLB range;
- refit/reselect catcher throwing or blocking;
- refit/reselect framing;
- use 2025 confirmation residuals for tuning;
- add another Defense-v1 skill challenger;
- alter Playing Time v1 or Position/Role v1;
- calculate WAR/value yet.

Preserve all invalid-source catcher/framing artifacts as audit evidence; do not use them for production decisions.

## Exact next sequence

1. Define one production Defense skill output contract that applies the final hierarchy without any fitting.
2. Audit frozen Playing Time and Position/Role outputs for defensive exposure construction.
3. Convert each retained Defense skill channel to defensible native run units using component-specific public methodology/exposure; no arbitrary `runs per z` constant.
4. Develop/freeze positional adjustment separately from position-relative Defense skill.
5. Only after run conversion and positional adjustment are frozen may replacement level / runs-per-win / WAR-value aggregation open.

## Binding boundaries

- **Defense v1 skill hierarchy is frozen.**
- **Run-conversion and positional-adjustment research are authorized next.**
- **WAR/value calculation remains unauthorized.**
