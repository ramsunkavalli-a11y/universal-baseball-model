# Position / role coherence — readiness checkpoint

Last updated: 2026-08-18

Status: **SOURCE FEASIBILITY ONLY — NO POSITION MODEL OR TEAM ALLOCATOR AUTHORIZED.**

Canonical broader handoff: `docs/project-status.md`.

## Why this layer exists

Two portable player channels are now frozen:

- batting rate/profile: `frozen_current_talent_carry_forward_v1`;
- individual MLB opportunity: `playing_time_recent_opportunity_40man_b2_hurdle_v1`.

Playing Time v1 predicts next-season MLB PA but intentionally does not assign those PA to a defensive position, DH role, or finite team roster allocation.

For a universal player ranking, the immediate downstream dependency is **position/defensive-role context**, because defense and positional value cannot be computed coherently without it.

A full team-allocation optimizer is **not yet justified**. It should remain deferred unless a later downstream contract demonstrates that individual position/role projections cannot support the required WAR/value calculation without team-total constraints.

## Existing repo support

### Available

1. `src/universal_baseball/player_game_stats.py`
   - game-grain affiliated player evidence already retains `team_id`;
   - useful for chronology-safe team/organization association;
   - does not expose defensive position usage.

2. `src/universal_baseball/playing_time_roster_source.py`
   - official Stats API roster rows expose `team_id`, `position_code`, and `position_abbreviation`;
   - only binary 40-man membership is currently certified for Playing Time v1;
   - roster position/status fields remain unvalidated for position-model use and cannot be promoted merely because they exist.

3. `src/universal_baseball/official.py`
   - official game-feed adapter exists and can be extended narrowly if needed;
   - current projection deliberately does not retain defensive alignment/position usage.

4. `src/universal_baseball/retrosheet.py`
   - existing adapter is intentionally limited to run-expectancy/contact-value transitions;
   - it is not a general defensive-position parser and should not be expanded unless a simpler mature source fails.

### Missing

- certified historical player × defensive-position usage;
- a DH/non-fielding opportunity treatment;
- a frozen position-share estimand;
- any defense projection;
- any team/position allocation optimizer.

## Architecture decision before source work

Prefer the smallest sufficient downstream architecture:

1. **portable PA** — already frozen in Playing Time v1;
2. **portable position/role profile** — next feasibility target;
3. **defense/positional value** — later, after position semantics are certified;
4. **team allocation constraints** — add only if required by a later team-specific product or if individual projections prove incoherent for value calculations.

Do not make current organization/team a mandatory part of the portable player forecast unless validation shows it adds necessary information. Trades and roster movement make team-specific allocation a distinct problem from player talent/opportunity.

## First source POC — 2024 only

Audit the official MLB Stats API bulk season endpoint for `group=fielding` on representative actual leagues already recognized by the repo:

- MLB AL: league `103`;
- Triple-A: `117`;
- Double-A: `113`;
- High-A: `118`;
- Single-A: `110`;
- Rookie/complex: `121`.

For each league, compare `group=fielding` with a same-league `group=hitting` identity surface and report:

- request success and pagination completeness;
- fielding split count and unique player count;
- hitting unique player count;
- hitters with no fielding split;
- whether `player.id`, `team.id`, and position fields are present;
- observed position codes/abbreviations;
- player/team/position duplicate grain;
- raw top-level split/stat key inventory;
- examples of hitters missing from fielding, retained only as diagnostics.

This is a **source-semantic audit**, not a claim that every hitting player lacking a fielding row is a DH.

## Acceptance to proceed beyond POC

The POC can authorize a broader historical position-source certification only if:

- all representative league requests succeed without future information;
- player identity is exact and reproducible;
- position labels have stable interpretable semantics;
- team association is present or can be joined from an already-certified chronology-safe source;
- missing-fielding hitters are explicitly measurable rather than silently dropped;
- no source behavior requires guessing a defensive position.

If the bulk fielding endpoint fails these checks, inspect mature alternatives before building a custom parser.

## Hard boundaries

- Do not reopen Current Talent, Projection v1, or Playing Time v1.
- Do not use 2025 Playing Time outcomes to select position-source semantics.
- Do not access 2025 batting-rate/profile outcomes.
- Do not infer DH from absence of fielding evidence until separately certified.
- Do not build a team allocator before the position-source audit establishes what downstream constraint is actually missing.
