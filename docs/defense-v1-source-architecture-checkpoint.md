# Defense v1 source / architecture checkpoint

Last updated: 2026-08-18

Status: **PRE-2025 SOURCE ARCHITECTURE CLOSED — FINAL TRACKED SOURCE GATE PASSED.**

## Downstream need

Defense must produce player × position defensive-quality forecasts that can later combine with frozen Position/Role and Playing Time. Defensive skill, positional adjustment, opportunity, team allocation, and WAR/value remain separate.

Active development handoff: `docs/defense-v1-development-checkpoint.md`.

## Settled source architecture

### Range / OAA

Pinned reusable implementation: SportsDataverse `0.0.75`, upstream commit `1dafadb38c5240d8e29a0f818efbabe04cd6c417`.

MLB June-2024 reuse POC passed the upstream month-vs-season Savant oracle:

- 116,355 pitches / 20,623 BIP;
- 18,820 usable OAA opportunities (`91.26%`);
- 263 Savant-matched fielders;
- Pearson `0.3045` vs frozen `>=0.30` gate.

SportsDataverse's own full-season 2024 test reports about `0.605` Pearson vs Savant OAA.

For MLB, prefer official public Savant Performance when directly available. Retain SportsDataverse's OAA implementation as the portable tracked implementation and independent check. Do not rebuild a public catch-probability model absent a concrete failure.

### Tracked MiLB transport

SportsDataverse's default minor-search parameters returned zero rows; its OAA code was not the problem. The accepted transport is:

- Savant minors CSV with `minors=true`;
- bounded date chunks;
- no server-side `hfLevel` dependency;
- client-side official team/league classification.

Frozen 2024-06-10 through 2024-06-16 diagnostic:

- tracked pool 35,352 pitches;
- AAA 27,749 pitches / 4,479 BIP / 3,986 OAA opportunities (`88.99%` usable);
- tracked non-AAA 7,603 pitches / 1,196 BIP / 803 OAA opportunities (`67.14%` usable);
- required fields present; both execution/coverage gates passed.

This establishes technical reuse, not proprietary MiLB OAA accuracy.

### Catcher framing

Frozen reuse POC passed:

- MLB June 2024: 33 Savant-matched catchers, Pearson `0.5754` vs frozen `>=0.50`;
- AAA: 14,298 eligible takes / 72 catchers, execution passed;
- tracked non-AAA: 3,183 takes / 20 catchers, execution passed.

SportsDataverse framing is the leading portable tracked framing implementation. Production framing remains contingent on the frozen tracked challenger.

### Universal official fielding evidence

The already-certified 2021–2024 official fielding captures contain broad all-level traditional counts:

- 64/64 season × league pairs;
- 224 raw fielding pages;
- 100,166 raw fielding splits;
- general putouts/assists/chances/errors/throwing errors/double plays;
- catcher caught stealing/stolen bases/passed balls/interference and related outcomes.

Availability was not treated as skill.

## Traditional evidence gates — CLOSED

### Reliability screen

Eight predeclared rates had enough adjacent-year repeatability to justify a stronger next-year Savant target test. High raw correlations were explicitly treated as position-signature contamination rather than skill proof.

### Next-year Savant target test

Development targets were 2022, 2023, 2024; no 2025 source/target was accessed.

Supported first-challenger features:

- `range_factor_per_9`: pooled position-adjusted Spearman `0.2277`;
- `fielding_pct`: `0.1291`;
- `throwing_errors_per_9`: pooled signed `0.0991`;
- `errors_per_9`: pooled signed `0.0841`;
- catcher `caught_stealing_pct`: `0.2033` vs next-year Savant throwing rate;
- catcher `passed_balls_per_9`: signed `0.1524` vs next-year Savant blocking rate.

Closed:

- `double_plays_per_9`: pooled `0.0372`, zero directional-fold passes;
- `catcher_interference_per_9`: no direct frozen target.

Do not reopen the traditional feature universe for Defense v1.

## Universal Defense v1 development — PASSED / SELECTED

Governing contract: `docs/defense-v1-development-contract.md`.

All 2022–2024 defensive targets are development evidence because they were already opened during feature screening. Completed-2025 defensive targets remain the untouched confirmation period.

### General range

Selected: **U1, lambda `0.0`** — current-season four-feature universal linear model.

Development result:

- 2022 MSE `1.10657` vs B0 `1.10142` — `0.47%` worse, inside frozen 5% guardrail;
- 2023 MSE `0.91584` vs `0.96342` — better;
- 2024 MSE `0.92537` vs `0.99816` — better;
- pooled MSE `0.97744` vs B0 `1.02188` — **4.35% improvement**;
- pooled Spearman `0.2330`;
- all promotion gates passed.

The two-season U2 family was considered under the frozen contract but did not beat the selected U1 on pooled OOF MSE.

### Catcher blocking

Selected: **C2**, fixed two-season recency/exposure model using passed-ball rate.

- pooled MSE improvement vs neutral about **9.84%**;
- promotion gate passed.

### Catcher throwing

Selected: **C1**, current-season CS% model.

- pooled MSE improvement vs neutral about **2.46%**;
- promotion gate passed.

The universal Tier-C path therefore has actual pre-2025 predictive support; it is not an assumed-zero/average fallback.

## Age challenger — FAILED / CLOSED

Governing contract: `docs/defense-v1-age-challenger-contract.md`.

A1 added only quadratic age terms to the exact selected U1 incumbent. Official Stats API birth dates resolved for all 551 development players.

Binding result:

- A1 MSE worse than U1 in all 3 folds;
- U1 pooled MSE `0.97744`;
- A1 pooled MSE `0.99915` — **2.22% worse**;
- pooled Spearman fell `0.23303 -> 0.20878`.

Age is closed for Defense v1. No age rescue or alternate curve is authorized.

## Final pre-2025 tracked source gate — PASSED

Governing contract: `docs/defense-v1-tracked-challenger-contract.md`.

Binding result: `docs/defense-v1-tracked-source-result.json`.

Workflow run `32182019495` completed successfully from source SHA `5438e905d24e2167432a52253320ccbc978186b8`.

The source-only gate preserved every frozen boundary:

- MLB predictor inputs: 2021, 2022, 2023 regular seasons;
- tracked MiLB transfer input: 2023 regular season;
- SportsDataverse `0.0.75` range/framing implementations;
- MiLB transport `minors=true` plus client-side official level identity;
- no 2024 tracking predictor pull;
- no 2025 source or target access;
- no model fit;
- no source-filter change from contract.

Persisted artifacts:

- `tracked_range_proxy_2021_2023.parquet`: 6,872 rows, SHA-256 `a65cb6f7506d5e100c9f0b088fb276eecc1dab5599592dd477bfcc030d850a3e`;
- `tracked_framing_proxy_2021_2023.parquet`: 579 rows, SHA-256 `1071b9d8209d6e9ba9d8c2b42ac7b99e3329387704e2910797b58f1a148cbc79`.

The result explicitly authorizes tracked challenger scoring next and does **not** authorize 2025 confirmation or WAR/value.

## Final tracked challenger — READY TO SCORE

Scorer: `scripts/audit_defense_v1_tracked_challenger.py`.

Frozen comparisons:

- general range: exact selected U1 incumbent vs **T1 = U1 + `tracked_range_z`**;
- catcher framing: **F0 = neutral zero-z baseline** vs **F1 = one-feature unpenalized tracked-framing model**.

No additional feature/model search is authorized. If a tracked component passes its MLB gate, run only its predeclared 2023-MiLB -> 2024-MLB transfer diagnostic. Tier-B use requires that transfer gate to pass; insufficient transfer evidence is not a pass.

## Coverage tiers entering final selection

- **Tier A — MLB tracked:** U1 universal evidence, with tracked range/framing only if the frozen tracked gates pass.
- **Tier B — tracked MiLB:** U1 universal evidence; tracked additions only if both their MLB development gate and predeclared MiLB->MLB transfer diagnostic pass.
- **Tier C — untracked affiliated MiLB:** selected universal U1 general range plus selected universal catcher components where eligible.

Missing tracking is missing evidence, not observed average talent.

## After tracked scoring

There are no further planned pre-2025 development challengers.

Next sequence must be:

1. accept/close tracked range and framing exactly by the frozen gates;
2. refit retained Defense-v1 component(s) on all authorized 2022–2024 development responses;
3. freeze exact normalization moments, coefficients, coverage/fallback rules, package versions, parameter hashes, and confirmation contract;
4. only then materialize completed-2025 defensive targets in a separate source-only workflow;
5. run one-shot 2025 confirmation with no refit, reselection, or rescue tuning.

## Binding boundaries

- No production Defense v1 parameters are frozen yet.
- Completed-2025 defensive targets remain untouched.
- Age is closed.
- Traditional feature search is closed.
- No Tier-B tracked component is accepted without its transfer gate.
- No catcher component-combination-to-runs rule is frozen yet.
- No WAR/value calculation is authorized.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.

## Evidence records

- `docs/defense-v1-development-checkpoint.md`
- `docs/defense-sportsdataverse-reuse-poc-result.json`
- `docs/defense-milb-statcast-transport-diagnostic-result.json`
- `docs/defense-catcher-framing-reuse-poc-result.json`
- `docs/defense-universal-fielding-source-audit-result.json`
- `docs/defense-traditional-fielding-stability-result.json`
- `docs/defense-traditional-to-savant-target-result.json`
- `docs/defense-v1-development-contract.md`
- `docs/defense-v1-universal-development-result.json`
- `docs/defense-v1-age-challenger-result.json`
- `docs/defense-v1-tracked-challenger-contract.md`
- `docs/defense-v1-tracked-source-result.json`
