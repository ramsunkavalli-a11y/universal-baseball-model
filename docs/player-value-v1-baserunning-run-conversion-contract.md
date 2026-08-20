# Player Value v1 baserunning run-conversion contract

Status: **BINDING FOR BASERUNNING v1 — GIDP RESIDUAL OMITTED — WAR STILL CLOSED**

This contract freezes the run conversion and production scaling for the two baserunning skill channels that have passed chronological selection:

- portable stolen-base behavior;
- MLB Statcast non-steal advancement.

It also closes the separate GIDP residual for Player Value v1 rather than inventing a new play-by-play reconstruction after the preferred direct source failed its opportunity-denominator audit.

## 1. Frozen upstream skill models

Do not refit in this gate.

### Portable steal behavior

From `docs/player-value-v1-steal-projection-selection-result.json`:

- attempt propensity: `B2_k5`;
- success skill: `B2_k45`.

Both use three-season recency evidence with fixed `1.00 / 0.50 / 0.25` annual weights and were selected on 2022–2023 before confirming on 2024.

### Non-steal advancement

From `docs/player-value-v1-advancement-projection-selection-result.json`:

- advancement rate: `A2_k25`.

It uses up to three prior MLB Savant seasons with fixed `1.00 / 0.50 / 0.25` annual weights and shrinks source-defined `runner_runs_xb / n_runner_moved_xb` toward zero with a prior of 25 non-steal advancement opportunities. It was selected on 2022–2023 and confirmed on held-out 2024.

## 2. Common 2024 MLB reference environment

Production exposure is tied to the same fixed certified 2024 MLB reference population used elsewhere in Player Value v1, not to each player's projected batting quality.

Required certified inputs:

- MLB PA: `182449`;
- MLB runs: `21343`;
- MLB outs: `129349`;
- portable steal opportunity proxy: `42342`;
- MLB steal attempts: `4578`;
- MLB stolen bases: `3617`;
- MLB caught stealing: `961`;
- Savant non-steal advancement opportunities: `12931`.

Derived reference rates are materialized rather than hard-coded downstream.

## 3. Stolen-base run conversion

Use the public FanGraphs wSB linear-weight convention because the already-frozen portable steal model deliberately uses the same portable opportunity proxy:

`steal_opportunity_proxy = 1B + BB + HBP - IBB`

FanGraphs defines:

`runSB = 0.2`

`RunsPerOut = MLB_runs / MLB_outs`

`runCS = -(2 * RunsPerOut + 0.075)`

`lg_steal_runs_per_opportunity = (MLB_SB * runSB + MLB_CS * runCS) / MLB_steal_opportunity_proxy`

This preserves an average-relative steal run component instead of awarding a neutral runner positive raw runs simply for receiving opportunities.

### 3.1 Production opportunity scaling

For player `i`:

`projected_steal_opportunities_i = projected_expected_mlb_pa_i * reference_steal_opportunities_per_pa`

`reference_steal_opportunities_per_pa = MLB_steal_opportunity_proxy / MLB_PA`

`reference_attempt_rate = MLB_steal_attempts / MLB_steal_opportunity_proxy`

The frozen attempt model produces `attempt_multiplier_i`, so:

`projected_steal_attempts_i = projected_steal_opportunities_i * reference_attempt_rate * attempt_multiplier_i`

The frozen success model produces a player log-odds residual. Apply it to the fixed MLB reference success probability:

`reference_success_probability = MLB_SB / MLB_steal_attempts`

`projected_success_probability_i = logistic(logit(reference_success_probability) + success_logodds_residual_i)`

Then:

`projected_SB_i = projected_steal_attempts_i * projected_success_probability_i`

`projected_CS_i = projected_steal_attempts_i * (1 - projected_success_probability_i)`

and:

`Rsteal_i = projected_SB_i * runSB + projected_CS_i * runCS - projected_steal_opportunities_i * lg_steal_runs_per_opportunity`

A player with neutral attempt and success skill therefore produces zero `Rsteal` apart from floating-point tolerance.

Do not use the player's projected singles, walks, HBP, or IBB to create steal opportunities. Those offensive outcomes are already handled inside batting value; using them again would make batting quality leak into the baserunning component.

## 4. Non-steal advancement run conversion

The Savant source already expresses extra-base advancement outcomes in runs relative to its opportunity model. Do not replace that with a new event-value model.

For player `i`, let `advancement_rate_i` be the frozen `A2_k25` projected source-defined rate.

Use one common MLB advancement-opportunity rate:

`reference_advancement_opportunities_per_pa = MLB_n_runner_moved_xb / MLB_PA`

`projected_advancement_opportunities_i = projected_expected_mlb_pa_i * reference_advancement_opportunities_per_pa`

`Radvance_i = advancement_rate_i * projected_advancement_opportunities_i`

Players without eligible prior MLB Savant advancement evidence receive `advancement_rate_i = 0` for this channel. MiLB-only advancement is not inferred from speed, steals, batting outcomes, or a hand-built translation.

Do not separately subtract the small realized 2024 aggregate Savant advancement rate. The Statcast source is already an expected-value run metric, and final Player Value has a separate fixed-reference MLB centering gate specifically to reconcile any non-zero aggregate remaining across independently built above-average components.

## 5. GIDP decision for v1

### 5.1 Raw GIDP remains prohibited

A raw GIDP penalty is non-additive. Frozen batting values each projected event bin using PA-level RE24, so the extra out/base-state cost of double-play ground balls is already present in the league mean value of the ground-ball bins.

### 5.2 Opportunity-adjusted residual is omitted for v1

A residual similar in concept to FanGraphs wGDP could be additive because it measures a player's double-play tendency relative to opportunity rather than charging the full double-play cost again.

However, the source audit found:

- official MLB season-player hitting output supplies `groundIntoDoublePlay` but not `gidpOpp` in the audited bulk rows;
- Savant's public custom leaderboard exposes GIDP counts but not a direct season-player GIDP-opportunity field on the inspected surface;
- deriving opportunities from Statcast pitch/play rows would require a new custom base-state/event reconstruction solely for this small residual component;
- the affiliated MiLB source has a direct GIDP-opportunity field, but promoting a MiLB-only denominator while reconstructing a different MLB denominator would create an avoidable cross-source comparability problem.

**Binding v1 decision:**

`Rgidp_residual_i = 0`

for every player.

This is an explicit omission, not an assumption that GIDP skill is nonexistent. Reopen only if a mature, reproducible direct opportunity source or reusable implementation is certified first and a new chronological persistence gate is predeclared before player-level outcome inspection.

## 6. Final baserunning component

For Player Value v1:

`Rbr_i = Rsteal_i + Radvance_i`

`Rgidp_residual_i = 0`

Persist `Rsteal`, `Radvance`, and the explicit zero-valued GIDP residual separately even if a downstream output also provides `Rbr`.

## 7. Required 2024 reference materialization

Persist a machine-readable 2024 record containing at least:

- all certified source counts above;
- `runs_per_out`;
- `runSB`;
- `runCS`;
- steal opportunity rate per PA;
- steal attempt rate per portable opportunity;
- steal success probability;
- league steal runs per portable opportunity;
- advancement opportunity rate per PA;
- frozen steal and advancement candidate IDs;
- explicit `gidp_residual_authorized = false`;
- exact upstream artifact paths.

The materializer must fail closed if the expected frozen candidate IDs or source counts are absent/inconsistent.

## 8. Mechanical verification

Tests must prove at minimum:

1. a neutral steal player produces zero `Rsteal` within floating tolerance;
2. better attempt behavior helps only when the resulting success mix has positive run value relative to the league baseline;
3. a positive success residual improves `Rsteal` holding opportunity and attempt propensity fixed;
4. `Radvance` scales only with projected MLB PA, the common reference opportunity rate, and frozen player advancement rate;
5. zero projected MLB PA produces zero baserunning runs;
6. no GIDP runs are added in v1.

## 9. Downstream boundary

Completing this contract closes the baserunning component definition but does **not** authorize final WAR.

Next required gates remain:

1. fixed-reference MLB centering across the frozen above-average components;
2. park-neutrality audit;
3. required sensitivities and final aggregation QA.

No final universal ranking may be used to revise this baserunning conversion.
