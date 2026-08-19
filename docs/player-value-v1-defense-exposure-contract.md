# Player Value v1 — defensive exposure contract

Last updated: 2026-08-19

Status: **OBSERVED EXPOSURE SOURCE FROZEN; FORWARD EXPOSURE BRIDGE NOT YET SELECTED.**

This contract fixes what counts as observed defensive exposure and prevents Player Value from silently substituting batting playing time or start-share probabilities for defensive opportunities. It does not yet select the production mapping from frozen projected Playing Time / Position-Role outputs to future defensive exposure.

## 1. Canonical observed defensive exposure

The canonical observed exposure is **official fielding outs** from the already-certified Position/Role historical source:

- source workflow evidence: run `32148467330`;
- artifact: `position-role-historical-source-2021-2024`;
- artifact digest: `sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3`;
- source builder: `scripts/certify_position_role_historical_source.py`;
- deterministic projection: `src/universal_baseball/position_role_source.py`.

The source is official MLB Stats API regular-season `fielding` data for the frozen MLB/affiliated league map. Its canonical row grain is:

`season x league_id x team_id x player_id x position_code`.

Relevant canonical fields include:

- `season`;
- `league_id` / `level_group`;
- `team_id`;
- `player_id`;
- `position_code` / `position_abbreviation`;
- `games_played`;
- `games_started`;
- `source_innings`;
- `fielding_outs`.

`fielding_outs` is an exact nonnegative integer derived from baseball innings notation by `baseball_innings_to_outs`. The parser accepts only `.0`, `.1`, and `.2` fractional-out suffixes and converts them to `3 * full_innings + remaining_outs`.

For calculations, **outs are the canonical unit**. If defensive innings are displayed, they are the deterministic transform `fielding_outs / 3`; do not perform calculations on decimal baseball-notation strings.

## 2. Position scope

Player Value v1 position-player defensive exposure uses:

`C, 1B, 2B, 3B, SS, LF, CF, RF`.

DH has zero defensive outs by source validation and therefore receives no defensive-skill exposure. Pitcher defense is outside this position-player Defense v1 interface and may not be inferred from the existing Position/Role model.

When team rows are combined, fielding outs may be summed only across rows that are intentionally in the same downstream player/season/level/position scope. Multi-level evidence must remain identifiable; a future production bridge must not accidentally double-count a player who appeared at multiple affiliated levels.

## 3. Observed defensive share

Where a descriptive historical defensive position share is needed, use the already-defined quantity:

`defensive_probability = position fielding_outs / player total_defensive_outs`.

The existing `build_batting_role_profiles` implementation computes exactly this field separately from `role_probability`.

This is observed historical evidence only. It is **not** itself a frozen future-position forecast.

## 4. Frozen Position/Role semantics are different

The frozen Position/Role v1 candidate `primary_share_thresholded_transition_mean_v1` forecasts the nine-position batting-role vector:

`C, 1B, 2B, 3B, SS, LF, CF, RF, DH`.

Its underlying `role_probability` is constructed from:

1. `games_started` when the player-season has any starts;
2. otherwise `games_played` as the explicit fallback.

The 2025 confirmation scorer uses that `role_probability` vector. It does **not** score or freeze `defensive_probability` as the forward target.

Therefore Player Value must not relabel projected `role_probability` as projected defensive-out share without a separately validated mapping.

## 5. Frozen Playing Time semantics are different

Playing Time v1 forecasts batting opportunity / plate-appearance exposure. Projected PA is not defensive outs.

The following shortcut is explicitly **not frozen and not authorized**:

`projected defensive outs = projected PA x projected position role share`.

Projected Playing Time and Position/Role may be inputs or constraints in a separately validated exposure bridge, but their upstream parameters may not be refit inside Player Value.

## 6. Forward exposure bridge research gate

Before any Defense skill is converted to a seasonal run total, a forward bridge must be selected using predeclared evidence and persisted separately.

The bridge must answer two distinct questions:

1. **total defensive exposure** — how many defensive outs/opportunities a player is projected to receive;
2. **position allocation** — how that exposure is distributed across eligible defensive positions.

The bridge should prefer simple, interpretable constructions using already-certified sources, including historical fielding outs plus frozen Playing Time / Position-Role outputs where they add demonstrated value. It must not invent a new general playing-time or role model under another name.

At minimum, candidate evaluation must compare against simple persistence baselines from prior-season observed defensive outs/shares. Any fitted mapping must use only authorized pre-2025 development evidence and must document its training boundary, features, target, coverage, and fallback behavior.

Because 2025 Position/Role outcomes have already been accessed for the upstream confirmation, Player Value must not describe 2025 defensive-exposure outcomes as an untouched holdout. Any later confirmation sample must be genuinely unopened for this exposure-mapping question or the method must be frozen on development evidence without pretending otherwise.

## 7. Component-specific opportunity denominators remain separate

`fielding_outs` is the canonical general seasonal defensive-exposure source, but it does not automatically imply that every Defense component should be multiplied by outs.

Run conversion must respect each component's native target/opportunity unit:

- general range: determine the principled opportunity/exposure mapping for Success Rate Added;
- catcher throwing: native target is per throw (`cs_aa_per_throw`), so throwing opportunities must be handled explicitly;
- catcher blocking: native target is per game (`blocks_above_average_per_game`) in the repaired leaderboard, with source pitch eligibility; conversion must preserve the target's actual native denominator rather than blindly use fielding outs;
- framing: raw target is run value per 1,000 pitches before standardization, so catcher pitch exposure is the natural native interface to research.

Historical fielding outs may be used to estimate or constrain those opportunity counts if validated, but no component receives an arbitrary universal `runs per out` or `runs per z` constant.

## 8. Required future exposure output

The frozen production bridge, once selected, must persist at least:

- player identifier;
- projection season;
- level/scope;
- projected total defensive outs;
- projected defensive outs by eligible position;
- projected defensive position shares;
- frozen Position/Role share vector used as input, if used;
- frozen Playing Time exposure used as input, if used;
- component-specific projected opportunity counts required for run conversion (for example catcher throws/pitches) once those mappings are frozen;
- fallback/coverage flags;
- source/model provenance.

The by-position projected outs must reconcile to projected total defensive outs within deterministic numerical tolerance.

## Binding boundaries

- Official `fielding_outs` is the canonical observed defensive-exposure unit.
- `role_probability` and `defensive_probability` are distinct fields with distinct semantics.
- Do not use PA x role share as a production defensive-outs shortcut without validation.
- Do not refit Playing Time or Position/Role.
- Do not use 2025 as an allegedly untouched exposure holdout.
- Do not convert Defense skill to seasonal runs until the forward exposure bridge and component-native opportunity mappings are frozen.
- Positional adjustment remains a separate layer.
- Replacement level, runs per win, and WAR/value remain closed.
