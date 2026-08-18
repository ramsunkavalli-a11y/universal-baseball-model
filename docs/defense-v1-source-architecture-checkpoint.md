# Defense v1 source / architecture checkpoint

Last updated: 2026-08-18

Status: **PRE-2025 DEVELOPMENT NEARLY CLOSED — FINAL TRACKED-EVIDENCE GATE IN PROGRESS.**

## Downstream need

Defense must produce player × position defensive-quality forecasts that can later combine with frozen Position/Role and Playing Time. Defensive skill, positional adjustment, opportunity, team allocation, and WAR/value remain separate.

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

SportsDataverse framing is the leading portable tracked framing implementation. No production framing projection is frozen yet.

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

All 2022–2024 defensive targets are development evidence because they were already opened during feature screening. Completed-2025 defensive targets are the untouched confirmation period.

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

## Final pre-2025 challenger — TRACKED EVIDENCE

Governing contract: `docs/defense-v1-tracked-challenger-contract.md`.

This is the final planned development challenger. No additional feature/model search is authorized afterward.

Frozen questions:

1. Does portable tracked range improve U1 for MLB players with tracked evidence?
2. If yes, does that representation transfer acceptably from tracked 2023 MiLB evidence to 2024 MLB Savant outcomes?
3. Does portable tracked catcher framing predict next-year Savant framing?
4. If yes, does framing transfer acceptably for tracked 2023 MiLB catchers who reach the 2024 MLB target?

The tracked source is being materialized separately so scorer logic cannot change source filters after observing results.

Frozen tracked-source scope:

- MLB inputs: 2021, 2022, 2023 regular seasons;
- tracked MiLB transfer input: 2023 regular season;
- SportsDataverse `0.0.75` range/framing implementations;
- MiLB transport `minors=true` + client-side official level identity;
- **no 2024 predictor pull and no 2025 source/target access**.

Expected reusable artifact:

- `tracked_range_proxy_2021_2023.parquet`;
- `tracked_framing_proxy_2021_2023.parquet`;
- exact file hashes/query records persisted in `docs/defense-v1-tracked-source-result.json` when the source gate completes.

Scoring code is already staged at `scripts/audit_defense_v1_tracked_challenger.py` but must not run until the completed source artifact/run id is pinned.

## Coverage tiers entering final selection

- **Tier A — MLB tracked:** U1 universal evidence, with tracked range/framing only if final tracked gates pass.
- **Tier B — tracked MiLB:** U1 universal evidence; tracked additions only if both their MLB development gate and predeclared MiLB->MLB transfer diagnostic pass.
- **Tier C — untracked affiliated MiLB:** selected universal U1 general range plus selected universal catcher components where eligible.

Missing tracking is missing evidence, not observed average talent.

## After the tracked gate

No further development challengers are planned.

Next sequence must be:

1. accept/close tracked components exactly by the frozen gates;
2. refit retained Defense-v1 component(s) on all authorized 2022–2024 development responses;
3. freeze exact normalization moments, coefficients, coverage/fallback rules, package versions and parameter hashes;
4. only then materialize completed-2025 defensive targets in a separate source-only workflow;
5. run one-shot 2025 confirmation with no refit, reselection or rescue tuning.

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
