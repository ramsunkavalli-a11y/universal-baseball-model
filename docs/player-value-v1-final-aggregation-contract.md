# Player Value v1 final WAR aggregation contract

Last updated: 2026-08-20

## Status

**PRE-OUTCOME FINAL AGGREGATION METHOD AND POPULATION FROZEN.**

The required upstream components, park decision, and sensitivities are complete
or have been explicitly closed under their predeclared availability condition.
This contract authorizes the first final Player Value v1 point-estimate WAR
materialization. It does not authorize refitting or reselecting any upstream
model after rankings are visible.

## Frozen scoring population

Use the exact intersection of the frozen 2024 surfaces:

1. `projection_2023_to_2024/frozen_b2_profile.parquet`;
2. Playing Time `candidate_2024_scored.parquet`;
3. defensive-position allocation `current_season=2023, next_season=2024`;
4. DH exposure `source_year=2023, target_year=2024`.

That complete-component intersection contains **3,045** players. Do not add the
940 B2/Playing Time rows outside the frozen Position/Role scoring population,
and do not add the one Position/Role row without B2/Playing Time evidence.
Those rows do not have a complete authorized component surface, and neutralizing
their missing positional exposure would invent a new fallback after development.

Append the six official 2024 MLB members outside the B2/Playing Time snapshot:

`543518, 593934, 622491, 656555, 666158, 808982`.

They remain explicit all-zero component/exposure/WAR rows. The final table
therefore contains **3,051** unique players. This rule preserves the completed
651-player MLB-reference cohort while keeping the universal ranking restricted
to players with a complete frozen upstream surface.

## Binding component formulas

For each scored player, consume without refitting:

- `Rbat`: frozen B2 projected batting profile and certified 2024 MLB run reference;
- `Rbr`: frozen `B2_k5` steal-attempt, `B2_k45` steal-success, and `A2_k25` advancement machinery;
- `Rdef`: frozen T1/U1/B0 general range plus repaired C2 throwing/blocking and F1/F0 framing, each converted with its native frozen opportunity rate;
- `Rpos`: binding FanGraphs schedule over frozen S0 position-outs allocation and B0 DH-role exposure;
- `Rlg = projected_expected_mlb_pa * 0.0010024718324441579` from the corrected verified 2024 MLB centering record;
- `Rpark = 0.0` from the verified park-neutrality audit;
- `Rrep = projected_expected_mlb_pa * 0.030237643566893475` from the refrozen replacement record.

No separate GIDP residual is authorized for v1. Do not add one.

Final arithmetic:

`RAR = Rbat + Rbr + Rdef + Rpos + Rlg + Rpark + Rrep`

`WAR = RAR / 9.682629939156854`

Every component must remain a separate persisted field. Defense must additionally
persist general-range, catcher-throwing, catcher-blocking, and catcher-framing run
subtotals whose sum reconciles to `Rdef`. Position outs, DH role events, model
family/fallback flags, projected PA, source provenance, RPW, and the additive
reconciliation residual must also be retained.

## Mechanical QA

The materialization must fail closed unless:

1. the population is exactly 3,051 unique player IDs;
2. the 651 official MLB reference rows reproduce the frozen numerical-centering
   component table within `1e-10` runs per component;
3. the six mandated outside-snapshot rows are all-zero rows;
4. every defense subtotal and every RAR/WAR identity reconciles within `1e-10`;
5. `Rpark` is zero for every row and no GIDP residual is present;
6. no 2025 outcome, refit, cap, floor, or ranking-driven parameter is used.

The frozen ranking order is descending unrounded WAR, then ascending MLBAM
`player_id` as the deterministic tie-break. Reported decimal rounding must never
be used to order players.

## Sensitivity boundary

The Baseball-Reference positional and PythagenPat outputs and replacement
alternatives remain diagnostic sidecars. They do not replace any binding field
in the final v1 ranking.
