# Project status and handoff

Last updated: 2026-08-18

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active development branch: `source-certification-poc`
- `source-certification-poc` contains newer work than the latest integration into `main`.
- Work in small verified batches.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, playing time, position/role, defense, WAR/value, and final ranking separate.

## Stage summary

### Performance — DONE for current batting pipeline

Completed-2024 affiliated batting Performance materialization is production-shaped and retained.

Primary checkpoint: `docs/performance-2024-affiliated-checkpoint.md`.

### Current Talent — DONE / FROZEN

Retained universal model: `translated_multiseason_recency_empirical_bayes_v1`.

Frozen core design: 1,095-day history, 180-day exponential half-life, EB prior strength 100 effective core events, training-only MLB-anchored level translation, frozen age/current-level prior, frozen 12-component batting profile.

Richer Challenger 1 failed development. Richer Challenger 2 passed development but failed its one-shot 2023 confirmation. Both are closed without rescue tuning.

Key records:

- `docs/current-talent-results-only-baseline-freeze.md`
- `docs/current-talent-contact-value-confirmation-result.json`
- `docs/current-talent-challenger2-postmortem.md`

### Projection v1 batting rate/profile — DONE / FROZEN

Retained model: `frozen_current_talent_carry_forward_v1`.

The explicit age/development challenger was selected on 2022, passed fixed 2023 OOT validation, then failed the pre-registered 2024 OOT primary gate. That failure is binding and the challenger is closed without rescue tuning.

**Outcome boundary:** 2025 batting-rate/profile outcomes remain untouched for Projection v1. Later Playing Time and Position/Role confirmations opened only their separately frozen 2025 targets.

Key records:

- `docs/projection-batting-v1-development-contract.md`
- `docs/projection-v1-methodology-review.md`
- `docs/projection-batting-v1-development-result.json`

### Playing Time v1 — DONE / FROZEN / CONFIRMED

Production model: `playing_time_recent_opportunity_40man_b2_hurdle_v1`.

Architecture: L2 logistic `P(next-season MLB PA > 0)` plus zero-truncated NB2 positive MLB PA. Selected on 2022, passed 2023 and 2024 OOT validation, then passed its isolated one-shot 2025 confirmation on 3,759 snapshot players. No 2025 refit, reselection, recalibration, threshold change, or rescue tuning occurred.

Key records:

- `docs/playing-time-role-current-status.md`
- `docs/playing-time-v1-confirmation-contract.md`
- `docs/playing-time-v1-confirmation-result.json`

### Position / Role v1 — DONE / FROZEN / CONFIRMED

Production model: `primary_share_thresholded_transition_mean_v1`.

Portable nine-position batting-role profile across C, 1B, 2B, 3B, SS, LF, CF, RF, and DH. Pitcher usage remains outside the batting-role channel.

Historical source certification passed 64/64 season × league pairs. The final selective transition model passed both development folds, its parameters were frozen before 2025 source access, and the untouched 2025 confirmation passed on 2,891 players:

- mean TV `0.325526526` -> `0.324624904`;
- mean SSE `0.226924779` -> `0.216389159`;
- no confirmation refit, threshold change, or reselection.

Key records:

- `docs/position-role-historical-source-result.json`
- `docs/position-role-selective-transition-result.json`
- `docs/position-role-confirmation-parameters.json`
- `docs/position-role-2025-confirmation-result.json`

## ACTIVE NEXT STAGE — Defense v1 final pre-2025 tracked challenger

Primary active handoff: `docs/defense-v1-development-checkpoint.md`.

Source/architecture checkpoint: `docs/defense-v1-source-architecture-checkpoint.md`.

The universal Defense-v1 development path is already selected:

- general range: **U1, lambda `0.0`**;
- catcher blocking: **C2**;
- catcher throwing: **C1**;
- age challenger: **failed / closed**;
- traditional feature search: **closed**.

The final planned pre-2025 challenger tests whether portable tracked range and catcher framing add enough next-season signal to the selected universal path.

### Final tracked source gate — PASSED

Governing contract: `docs/defense-v1-tracked-challenger-contract.md`.

Binding source record: `docs/defense-v1-tracked-source-result.json`.

Workflow run `32182019495` completed successfully from source SHA `5438e905d24e2167432a52253320ccbc978186b8`.

The source-only gate materialized and hash-pinned:

- `tracked_range_proxy_2021_2023.parquet`: 6,872 rows, SHA-256 `a65cb6f7506d5e100c9f0b088fb276eecc1dab5599592dd477bfcc030d850a3e`;
- `tracked_framing_proxy_2021_2023.parquet`: 579 rows, SHA-256 `1071b9d8209d6e9ba9d8c2b42ac7b99e3329387704e2910797b58f1a148cbc79`.

Frozen source scope was preserved exactly:

- MLB predictors: 2021, 2022, 2023 regular seasons;
- tracked MiLB transfer input: 2023 regular season;
- SportsDataverse `0.0.75` range/framing implementations;
- MiLB `minors=true` transport plus client-side official level identity;
- no 2024 tracking predictor pull;
- **no 2025 source/target access**;
- no model fit during source materialization;
- no source-filter changes after the contract was frozen.

The binding result explicitly sets:

- `tracked_source_materialized = true`;
- `tracked_challenger_scoring_authorized_next = true`;
- `2025_confirmation_authorized = false`;
- `war_value_authorized = false`.

### Frozen scorer to execute next

Scoring code: `scripts/audit_defense_v1_tracked_challenger.py`.

Run only against the persisted, hash-verified tracked artifacts. Do not re-query or change source filters.

Frozen comparisons:

- **General range:** selected U1 incumbent vs **T1**, which adds only `tracked_range_z` to the exact U1 pipeline.
- **Catcher framing:** **F0**, neutral framing z = 0, vs **F1**, the frozen one-feature unpenalized `tracked_framing_z -> framing_target_z` model.

If a tracked component passes its MLB development gate, run only its predeclared 2023-MiLB -> 2024-MLB transfer diagnostic. Tier-B tracked use requires that transfer gate to pass. Insufficient transfer evidence is not a pass.

There are **no additional planned Defense-v1 development challengers after this gate**.

### Defense coverage tiers

- **Tier A — MLB tracked:** U1 universal evidence, with tracked range/framing only if the final tracked gates pass.
- **Tier B — tracked MiLB:** U1 universal evidence; tracked additions only if both their MLB development gate and predeclared MiLB->MLB transfer diagnostic pass.
- **Tier C — untracked affiliated MiLB:** selected universal U1 general range plus selected universal catcher components where eligible.

Missing tracking is missing evidence, not observed average/zero skill.

## Immediate next batch

1. Execute the frozen tracked challenger scorer against the persisted source artifacts and verify their hashes.
2. Accept or close tracked range and tracked framing exactly by the frozen MLB and, when applicable, MiLB-transfer gates.
3. If scoring completes cleanly, update the Defense checkpoint with the binding retained component set. Do not introduce another development challenger.

After that, the next batch is to refit only retained Defense-v1 components on all authorized 2022–2024 development responses and freeze exact parameters/coverage rules plus the 2025 confirmation contract.

Only **after that freeze** may completed-2025 defensive targets be materialized for the one-shot Defense-v1 confirmation.

## Binding boundaries

- **No 2025 defensive source/target access yet.**
- **No WAR/value calculation yet.**
- No tracked-source filter changes after observing challenger results.
- No new Defense-v1 feature/model search after the frozen tracked challenger.
- No age rescue or reopening rejected traditional features.
- No proprietary MiLB validation claim.
- No accidental neutral/zero imputation for missing tracking.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.

## Governing read order

1. `docs/project-status.md`
2. `docs/defense-v1-development-checkpoint.md`
3. `docs/defense-v1-tracked-challenger-contract.md`
4. `docs/defense-v1-tracked-source-result.json`
5. `docs/defense-v1-source-architecture-checkpoint.md`
6. `docs/defense-v1-universal-development-result.json`
7. `docs/defense-v1-age-challenger-result.json`
8. `docs/position-role-2025-confirmation-result.json`
9. `docs/playing-time-v1-confirmation-result.json`
10. `docs/projection-batting-v1-development-result.json`
11. `docs/current-talent-results-only-baseline-freeze.md`
12. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent, Projection v1, Playing Time v1, or Position/Role v1 absent a concrete implementation failure.
- Do not tune rejected models against their held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Keep batting skill, opportunity, position/role, defensive skill, positional adjustment, and value separate.
- Treat source coverage/missingness as information, not as zero skill.
- Freeze exact model/source decisions before opening their held-out confirmation period.
- Update this handoff whenever the active stage or binding result changes.
