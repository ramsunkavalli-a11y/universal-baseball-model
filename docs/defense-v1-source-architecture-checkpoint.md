# Defense v1 source / architecture checkpoint

Last updated: 2026-08-18

Status: **PRE-2025 SOURCE ARCHITECTURE CLOSED — TRACKED CHALLENGER SCORED.**

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

For MLB, prefer official public Savant Performance when directly available. Retain SportsDataverse's OAA implementation as the portable tracked implementation and independent check. Do not rebuild a public catch-probability model absent a concrete failure.

### Tracked MiLB transport

Accepted transport:

- Savant minors CSV with `minors=true`;
- bounded date chunks;
- no server-side `hfLevel` dependency;
- client-side official team/league classification.

Frozen 2024-06-10 through 2024-06-16 transport diagnostic passed execution/coverage:

- AAA: 27,749 pitches / 4,479 BIP / 3,986 OAA opportunities (`88.99%` usable);
- tracked non-AAA: 7,603 pitches / 1,196 BIP / 803 OAA opportunities (`67.14%` usable).

This establishes technical reuse, not proprietary MiLB OAA accuracy.

### Catcher framing

Frozen reuse POC passed source feasibility:

- MLB June 2024: 33 Savant-matched catchers, Pearson `0.5754` vs frozen `>=0.50`;
- AAA: 14,298 eligible takes / 72 catchers;
- tracked non-AAA: 3,183 takes / 20 catchers.

The later final tracked challenger nevertheless failed its frozen MLB stability guardrail, so tracked framing is **not retained** for Defense v1. Source feasibility is not equivalent to production promotion.

### Universal official fielding evidence

Certified 2021–2024 official fielding captures contain broad all-level traditional counts:

- 64/64 season × league pairs;
- 224 raw fielding pages;
- 100,166 raw fielding splits;
- putouts/assists/chances/errors/throwing errors/double plays;
- catcher caught stealing/stolen bases/passed balls/interference and related outcomes.

Availability was not treated as skill.

## Settled universal development

Governing contract: `docs/defense-v1-development-contract.md`.

Selected pre-2025 universal components:

- general range: **U1, lambda `0.0`**;
- catcher blocking: **C2**;
- catcher throwing: **C1**.

Age challenger A1 failed and is closed. Traditional feature search is closed.

## Frozen tracked source gate — PASSED

Governing contract: `docs/defense-v1-tracked-challenger-contract.md`.

Binding source result: `docs/defense-v1-tracked-source-result.json`.

Source workflow run `32182019495` succeeded from SHA `5438e905d24e2167432a52253320ccbc978186b8` with no 2025 source/target access and no model fit.

Hash-pinned artifacts:

- range: 6,872 rows, SHA-256 `a65cb6f7506d5e100c9f0b088fb276eecc1dab5599592dd477bfcc030d850a3e`;
- framing: 579 rows, SHA-256 `1071b9d8209d6e9ba9d8c2b42ac7b99e3329387704e2910797b58f1a148cbc79`.

## Final tracked challenger — COMPLETE

Binding result: `docs/defense-v1-tracked-challenger-result.json`.

Scoring workflow run `32196115227` completed successfully from SHA `ace1df97001b83b91a1a1021637c604ebdea6399` after verifying the pinned tracked-source hashes.

### Range

T1 (`U1 + tracked_range_z`) passed the MLB/Tier-A gate:

- MSE better than U1 in all 3 held folds;
- pooled MSE improvement **1.93%**;
- pooled Spearman delta **+0.01180**;
- all frozen guardrails passed.

The predeclared MiLB transfer diagnostic then had `0` eligible players and recorded `insufficient_transfer_evidence`. Under the frozen contract this is not a pass.

**Retain tracked range for Tier A MLB only. Tier B/C remain on U1.**

### Framing

F1 improved pooled MSE **9.37%** and beat F0 in 2 of 3 folds, but the 2022 fold was **8.35% worse** than F0, exceeding the frozen maximum 5.0% fold degradation.

**Tracked framing failed the Tier-A gate and is closed.** Its MiLB transfer diagnostic was not attempted.

## Coverage tiers entering parameter freeze

- **Tier A — MLB tracked:** T1 range; no tracked framing.
- **Tier B — tracked MiLB:** U1 universal range; no tracked framing. C2/C1 universal catcher components where eligible.
- **Tier C — untracked affiliated MiLB:** U1 universal range; C2/C1 universal catcher components where eligible.

Missing tracking is missing evidence, not observed average talent.

## Next authorized stage

Pre-2025 feature/model development is closed. The next authorized work is only:

1. refit retained components on all authorized 2022–2024 development responses;
2. freeze normalization moments, coefficients, coverage/fallback rules, package versions and parameter hashes;
3. freeze the exact 2025 confirmation contract;
4. only then materialize completed-2025 defensive targets in a separate source-only workflow.

## Binding boundaries

- Completed-2025 defensive targets remain untouched.
- No additional Defense-v1 challenger is authorized.
- No framing rescue, age rescue, or traditional-feature reopening.
- No Tier-B tracked range without a passing transfer gate.
- No catcher component-combination-to-runs rule is frozen yet.
- No WAR/value calculation is authorized.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.

## Evidence records

- `docs/defense-v1-development-checkpoint.md`
- `docs/defense-v1-tracked-challenger-contract.md`
- `docs/defense-v1-tracked-source-result.json`
- `docs/defense-v1-tracked-challenger-result.json`
- `docs/defense-v1-universal-development-result.json`
- `docs/defense-v1-age-challenger-result.json`
- `docs/defense-sportsdataverse-reuse-poc-result.json`
- `docs/defense-milb-statcast-transport-diagnostic-result.json`
- `docs/defense-catcher-framing-reuse-poc-result.json`
- `docs/defense-universal-fielding-source-audit-result.json`
- `docs/defense-traditional-fielding-stability-result.json`
- `docs/defense-traditional-to-savant-target-result.json`
