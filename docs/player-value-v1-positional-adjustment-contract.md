# Player Value v1 — positional adjustment contract

Last updated: 2026-08-19

Status: **BINDING V1 POSITIONAL-ADJUSTMENT METHOD FROZEN.**

## Purpose

Freeze a transparent positional-difficulty adjustment that can be added to position-relative Defense runs without reopening Defense skill, defensive exposure, Position/Role, or Playing Time.

This contract fixes both:

1. the positional run schedule; and
2. the exposure used to prorate that schedule.

It does not select replacement level, runs per win, or WAR/value aggregation.

## 1. Public run schedule

Player Value v1 uses the fixed FanGraphs positional-adjustment convention documented by the official FanGraphs Library:

- https://library.fangraphs.com/war/war-position-players/
- https://library.fangraphs.com/the-beginners-guide-to-the-positional-adjustment/

Full-season values per 1,458 defensive innings / 162 nine-inning games:

| Position | Runs / full season |
|---|---:|
| C | +12.5 |
| 1B | -12.5 |
| 2B | +2.5 |
| 3B | +2.5 |
| SS | +7.5 |
| LF | -7.5 |
| CF | +2.5 |
| RF | -7.5 |
| DH | -17.5 |

The schedule is fixed for v1. Do not empirically retune individual position constants after this freeze.

### Why this convention

The methodology audit `docs/player-value-v1-positional-adjustment-public-methodology-audit.md` compared FanGraphs with Baseball-Reference's current public convention.

FanGraphs is selected for v1 because its fixed schedule:

- is deterministic across forward projection runs;
- naturally prorates multi-position exposure;
- is directly compatible with position-relative Defense skill;
- can be calculated for an individual player without requiring a complete projected MLB population;
- keeps any future league-wide balancing adjustment separate rather than embedding it inside positional value.

This is an architecture choice, not a claim that the historical FanGraphs constants are more empirically current than Baseball-Reference's values.

Baseball-Reference's current raw schedule remains the required sensitivity convention before WAR/value aggregation.

## 2. Non-DH positional exposure — already frozen

For `C, 1B, 2B, 3B, SS, LF, CF, RF`, use the already-frozen Player Value v1 projected position fielding outs from:

- `docs/player-value-v1-defense-exposure-contract.md`;
- `docs/player-value-v1-defensive-exposure-diagnostic-result.json`;
- `docs/player-value-v1-defensive-position-allocation-result.json`.

Selected v1 forms are:

- total defensive outs: `B0_raw_persistence`;
- position allocation: `S0_prior_defensive_share_persistence`.

Therefore projected position fielding outs equal prior-season MLB position fielding outs algebraically.

A nine-inning position-game equivalent is:

`projected_position_game_equivalent[p] = projected_position_fielding_outs[p] / 27`.

Do not use frozen batting-role probability as defensive innings/share.

## 3. DH positional exposure — FROZEN

Contract: `docs/player-value-v1-dh-positional-exposure-selection-contract.md`.

Binding result: `docs/player-value-v1-dh-positional-exposure-selection-result.json`.

Workflow run: `32270141291`.

The pre-2025 development gate compared raw persistence with frozen Position/Role and Playing Time challengers on 2022->2023 and 2023->2024.

Selected form: **`B0_raw_dh_role_event_persistence`**.

Thus:

`projected_DH_role_events = prior_DH_role_events`.

DH role-event semantics remain those frozen by `build_batting_role_profiles`:

- when the player-season has positive total starts, use DH games started;
- otherwise use DH games played fallback.

This is a role-equivalent game count. It is not defensive innings.

Do not retune the rejected Position/Role / Playing Time challengers.

## 4. Production positional-adjustment formula

For each defensive position `p`:

`Rpos[p] = FG_full_season_runs[p] * projected_position_fielding_outs[p] / 4374`.

Because `4374 = 1458 * 3`, this is exactly the FanGraphs full-season rate prorated by defensive outs.

For DH:

`Rpos[DH] = -17.5 * projected_DH_role_events / 162`.

Total raw positional adjustment:

`Rpos = sum(Rpos[C], Rpos[1B], Rpos[2B], Rpos[3B], Rpos[SS], Rpos[LF], Rpos[CF], Rpos[RF], Rpos[DH])`.

For multi-position players, calculate each component separately and sum. Do not assign one primary-position multiplier to all exposure.

## 5. No player-level renormalization

Do not renormalize defensive position shares to make room for DH.

Defensive fielding outs and DH role events are separate observed exposure quantities. A player can accumulate both during a season because roles can change across games. The production formula therefore simply adds the prorated defensive-position terms and the DH term.

## 6. League centering remains separate

No league-wide centering is performed inside v1 positional adjustment.

If Player Value later requires a league-average balancing adjustment, it must be a separately named, documented layer. Do not silently modify the positional constants or distribute a centering residual through `Rpos`.

## 7. Required production fields

Persist at least:

- projected fielding outs by defensive position;
- projected DH role events;
- positional schedule identifier = `fangraphs_fixed_162_game_v1`;
- full-season positional multiplier by position;
- positional runs by position;
- total positional adjustment runs;
- defensive-exposure provenance;
- DH-exposure provenance;
- sensitivity-schedule version when sensitivity is later calculated.

## 8. Required pre-WAR sensitivity

Before replacement level / runs-per-win / WAR aggregation is finalized, calculate the same projected exposure surface under the Baseball-Reference current raw schedule documented in `docs/player-value-v1-positional-adjustment-public-methodology-audit.md`.

Report at minimum:

- player-level selected-schedule Rpos;
- player-level Baseball-Reference-sensitivity Rpos;
- difference;
- distribution of differences;
- largest absolute differences.

This sensitivity must not be used to cherry-pick a schedule based on favored players.

## Binding boundaries

- Positional difficulty remains separate from position-relative Defense skill.
- FanGraphs fixed positional schedule is frozen for v1.
- Non-DH exposure remains frozen fielding outs by position.
- DH exposure remains raw DH role-event persistence.
- No league-wide centering inside positional adjustment.
- No Current Talent, Projection, Playing Time, Position/Role, Defense, or exposure refit.
- No 2025 outcome tuning.
- Replacement level remains closed.
- Runs per win remains closed.
- WAR/value aggregation and final ranking remain closed until the remaining upstream value layers are frozen.
