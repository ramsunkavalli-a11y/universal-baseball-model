# Project status and handoff

Last updated: 2026-08-19

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active branch: `source-certification-poc`
- Work in small verified batches and inspect the active branch head before editing.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Keep Performance, Current Talent, Projection, Playing Time, Position/Role, Defense skill, defensive exposure, run conversion, positional adjustment, replacement level, WAR/value, and final ranking separate.

## Frozen upstream stages

- **Performance:** completed-2024 affiliated batting materialization retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.

Do not reopen these stages absent a concrete implementation failure.

## Defense v1 skill — DONE / FROZEN

Defense skill selection/confirmation is complete. The repaired Savant catcher-source path is binding; old invalid-source artifacts remain audit history only.

Final hierarchy:

- **General range:** T1 for eligible certified tracked MLB players; otherwise U1 for eligible MLB/affiliated MiLB; otherwise neutral B0.
- **Catcher throwing:** repaired C2 when eligible; otherwise neutral B0.
- **Catcher blocking:** repaired C2 when eligible; otherwise neutral B0.
- **Framing:** MLB F1 when eligible for certified tracked framing; otherwise F0 neutral. MiLB framing remains F0 neutral.

Key binding records:

- `docs/defense-v1-development-checkpoint.md`
- `docs/defense-v1-2025-confirmation-result.json` — binding for general range only
- `docs/defense-v1-catcher-repair-2025-confirmation-result.json`
- `docs/defense-v1-framing-2025-confirmation-result.json`
- `docs/defense-v1-catcher-repair-parameters.json`
- `docs/defense-v1-framing-repair-parameters.json`

Important throwing implementation note: the repaired parameter JSON contains a metadata-only `exposure: fielding_outs` label, but the fitted/confirmed C2 implementation weights its two-season feature by **steal attempts** and requires >=10 prior-season steal attempts. Production code must follow fitted `_catcher_matrix` semantics.

**Do not refit, rescue, recalibrate, or reopen Defense skill.**

## Player Value v1 architecture

Architecture contract: `docs/player-value-v1-architecture-contract.md`.

Binding boundaries:

- reuse the existing Performance RE24/bin-value infrastructure for batting;
- Defense skill and defensive runs are separate layers;
- no arbitrary `runs per z` conversion;
- positional adjustment is separate from position-relative Defense skill;
- replacement level and runs per win remain later decisions;
- preserve each component separately in outputs.

## Defensive exposure — V1 BRIDGE SELECTED / FROZEN

Canonical observed exposure is official Stats API `fielding_outs` over `C, 1B, 2B, 3B, SS, LF, CF, RF`.

### Total defensive outs

Binding development result: `docs/player-value-v1-defensive-exposure-diagnostic-result.json`, workflow run `32261447127`.

Selected form: **`B0_raw_persistence`** = prior-season MLB defensive outs.

Equal-fold means on 2022->2023 and 2023->2024:

- B0: MAE `151.8143`, RMSE `473.4592`;
- P1 projected-PA global scale: MAE `180.2195`, RMSE `427.4569`;
- H1 fixed 50/50 hybrid: MAE `152.5628`, RMSE `430.7028`.

Neither challenger satisfied the predeclared MAE gates. Do not retune the 2% guardrail or 50/50 weight.

### Defensive position allocation

Predeclared contract: `docs/player-value-v1-defensive-position-allocation-contract.md`.

Binding result: `docs/player-value-v1-defensive-position-allocation-result.json`, workflow run `32266007594`.

Selected form: **`S0_prior_defensive_share_persistence`** = prior-season position fielding outs divided by prior-season total defensive outs.

The frozen total volume remained B0 for every allocation candidate. The two challengers were a deterministic normalization of the frozen Position/Role forecast (R1) and a fixed 50/50 S0/R1 hybrid (H1).

Equal-fold allocation metrics:

- S0: position-out cell MAE `164.8437`, RMSE `472.8779`, share TV `0.275841`, primary-position match `0.66025`;
- R1: MAE `167.4807`, RMSE `466.5794`, share TV `0.280707`, primary match `0.65041`;
- H1: MAE `165.4973`, RMSE `468.6990`, share TV `0.272824`, primary match `0.66121`.

H1 improved RMSE/share TV but did not improve the binding equal-fold position-out MAE. R1 failed additional share-TV/primary-position guardrails. No challenger passed, so S0 is binding.

### Frozen v1 general exposure mapping

For the general defensive-out bridge:

- projected total defensive outs = prior-season MLB defensive outs;
- projected defensive position shares = prior-season defensive-out shares;
- projected position outs = frozen total outs x frozen position shares;
- the position-out totals must reconcile to projected total defensive outs.

This closes **general defensive-out volume and position allocation**. Component-native catcher opportunities (throws, blocking denominator, framing pitches) remain separate research gates and are not implied by fielding outs.

## ACTIVE STAGE

**Defense native-unit run conversion and component-native opportunity mapping; positional adjustment remains separate.**

The next work must determine principled native conversions separately for:

1. general range / Success Rate Added;
2. catcher throwing / `cs_aa_per_throw` plus projected throw opportunities;
3. catcher blocking / `blocks_above_average_per_game` with its actual source denominator;
4. framing / run value per 1,000 pitches plus projected catcher pitch exposure.

The existing diagnostic `docs/player-value-v1-defense-native-scale-audit.json` is evidence only; it did **not** freeze a run scale. Do not turn its standard deviations into a universal arbitrary `runs per z` constant.

### Immediate next batch

1. Audit each frozen Defense target and parameter artifact to identify the exact raw native unit, standardization/back-transform metadata, and exposure denominator.
2. Prefer direct native-unit back-transforms where the frozen source target already has baseball/run meaning.
3. For components requiring future opportunity counts, predeclare and validate the simplest exposure bridge using certified pre-2025 evidence; do not refit Defense skill.
4. Keep positional adjustment independent from Defense skill/run conversion.
5. Only after Defense runs and positional adjustment are frozen should replacement level / runs per win / WAR-value aggregation open.

## Binding boundaries

- Defense skill models are frozen.
- General defensive exposure volume is frozen at `B0_raw_persistence`.
- General defensive position allocation is frozen at `S0_prior_defensive_share_persistence`.
- Do not retune rejected exposure challengers after result access.
- Do not use 2025 confirmation residuals to tune run conversion.
- Do not refit Current Talent, Projection, Playing Time, Position/Role, or Defense.
- Preserve invalid-source artifacts as audit history.
- No arbitrary universal `runs per z` conversion.
- Positional adjustment remains a separate layer.
- **Replacement level, runs per win, WAR/value aggregation, and final ranking are not authorized yet.**

## Governing read order

1. `docs/project-status.md`
2. `docs/player-value-v1-architecture-contract.md`
3. `docs/player-value-v1-defense-exposure-contract.md`
4. `docs/player-value-v1-defensive-exposure-diagnostic-result.json`
5. `docs/player-value-v1-defensive-position-allocation-contract.md`
6. `docs/player-value-v1-defensive-position-allocation-result.json`
7. `docs/player-value-v1-defense-native-scale-audit.json`
8. `docs/defense-v1-development-checkpoint.md`
9. `docs/defense-v1-catcher-repair-parameters.json`
10. `docs/defense-v1-framing-repair-parameters.json`
11. `docs/defense-v1-catcher-repair-2025-confirmation-result.json`
12. `docs/defense-v1-framing-2025-confirmation-result.json`
13. `docs/defense-v1-2025-confirmation-result.json` — general range only
14. `docs/position-role-2025-confirmation-result.json`
15. `docs/playing-time-v1-confirmation-result.json`
16. `docs/projection-batting-v1-development-result.json`
17. `docs/current-talent-results-only-baseline-freeze.md`
18. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled work absent a concrete implementation failure.
- Repair only the scope affected by a verified implementation failure.
- Do not tune rejected models against held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening any genuinely unopened confirmation period.
