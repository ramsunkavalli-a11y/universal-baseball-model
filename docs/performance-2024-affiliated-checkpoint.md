# 2024 Affiliated Batting Performance Checkpoint

Last updated: 2026-08-16

## Milestone

The first complete affiliated-MiLB batting **Performance** materialization is now production-shaped and validated for the completed 2024 season across AAA, AA, High-A, Single-A, ACL/FCL, and DSL actual leagues represented by the certified Rookie/complex source bundle.

This milestone is intentionally **not** Current Talent, Projection, WAR, or an overall player ranking. It is the contextual outcome/profile evidence layer on which those later stages can be built.

## Canonical output grain

Performance summary:

`season + actual league_id + player_id`

Long-form core profile:

`season + actual league_id + player_id + core_bin`

League contextual value table:

`season + actual league_id + core_bin`

A player who appears at more than one actual league/level remains in more than one Performance row. Cross-level synthesis is deferred to Current Talent.

## 2024 affiliated materialization

Workflow run: `31948208695`  
Artifact: `affiliated-batting-performance-2024`

Combined output:

- actual leagues: **14**;
- affiliated level groups: **5**;
- player × actual-league × season rows: **4,995**;
- plate appearances: **784,285**;
- classified reusable contact events: **494,884**;
- screened core Performance events: **764,713**;
- screened core-profile coverage: **97.50% of PA**;
- long-form player-bin rows: **52,634**;
- league-bin value rows: **168**;
- unknown contact rows: **156 (0.032%)**;
- contacts receiving official participant authority in residual-triggered games: **64,720 (13.08%)**;
- net reusable-contact residual versus season aggregate: **-109 (-0.022% of contacts)**;
- unvalued core events: **0**;
- player rows with uncertified/missing bin values: **0**;
- summary canonical-grain uniqueness: **4,995 / 4,995**;
- profile canonical-grain uniqueness: **52,634 / 52,634**;
- league-bin canonical-grain uniqueness: **168 / 168**.

The small contact residual is intentionally retained as quality/definition evidence rather than repaired with synthetic contacts.

## Level results

| Level group | Player-league rows | PA | Contacts | Core coverage | Contact residual | Exception games | Batter IDs changed |
|---|---:|---:|---:|---:|---:|---:|---:|
| AAA | 922 | 172,462 | 111,884 | 97.52% | +6 | 244 | 254 |
| AA | 761 | 152,819 | 98,790 | 97.29% | +9 | 226 | 227 |
| High-A | 776 | 147,059 | 93,221 | 97.17% | +28 | 221 | 212 |
| Single-A | 909 | 148,374 | 91,612 | 97.59% | -44 | 212 | 201 |
| Rookie/complex | 1,627 | 163,571 | 99,377 | 97.91% | -108 | 422 | 399 |

Every level produced:

- zero unresolved player-game contact controls;
- zero source contact-status conflicts;
- complete official matchup-batter coverage for every residual-triggered source contact sequence;
- zero hidden batter mismatches in a deterministic 40-game unflagged sample;
- zero unvalued core Performance events;
- unique Parquet/DuckDB canonical keys.

## Participant authority

ADR 021 supersedes the overly strict contact-pitch participant join from the original AAA proof.

Production rule:

1. reusable historical PBP remains the physical contact/geometry source;
2. resolved player-game boxscore contact residuals flag suspect participant games;
3. current official allPlays top-level matchup batter is joined at **play-sequence grain** (`game_pk + at_bat_index`) for those games;
4. every reusable contact sequence must receive one unambiguous official matchup batter;
5. current official `isInPlay` pitch equality is not required to establish participant identity;
6. current-vs-historical contact-status/pitch-number revisions remain separate diagnostic evidence.

The sequence-authority gate covered:

- AA: **11,297 / 11,297** source contact sequences across 226 exception games;
- Rookie/complex: **19,190 / 19,190** across 422 exception games;
- zero missing matchup-batter authority.

## Performance value policy

The frozen contextual bin-value policies remain:

- AAA: same-level peer shrinkage, λ = **25** prior-equivalent occurrences;
- AA: same-level peer shrinkage, λ = **75**;
- High-A: **direct**;
- Single-A: same-level peer shrinkage, λ = **25**;
- Rookie/complex: **direct**.

These are league-season bin-value regularizers, not player-talent shrinkage.

## Evidence boundaries preserved

- PA/BB/HBP/K denominators and standard totals come from certified season aggregates.
- Contact direction/trajectory comes from resolved reusable PBP.
- Confirmed airborne foulouts are screened by exact `foul territory` narrative evidence.
- Participant corrections use exception-only official sequence authority.
- DSL and older complex-league synthetic pitch sequences remain ineligible for pitch-process features where certified, while their PA/outcome/BIP Performance evidence remains usable.
- Coverage, unknowns, contact residuals, authority overlays, sample sizes, and value-estimator provenance remain explicit columns/metrics rather than being folded into player skill.

## Production modules now in place

- `armstjc_contacts.py` — reusable contact projection/consensus;
- `player_game_controls.py` — contact-control snapshot resolution;
- `contact_identity_overlay.py` — exception-only official participant authority;
- `contact_profile.py` — screened contact-bin classification;
- `bin_value_calibration.py` — direct contextual bin estimates;
- `bin_value_policy.py` / `bin_value_pooling.py` — frozen level-specific value regularization;
- `performance_season.py` — player × actual-league × season batting Performance transform;
- `performance_level_config.py` — frozen 2024 affiliated environment map;
- `performance_materialization.py` — multi-level affiliated combiner.

## Next development gate

The foundation is now strong enough to begin **Current Talent design**, but the next step should remain deliberately simple and validation-first.

Recommended sequence:

1. freeze the Performance materialization contract/schema and remove POC-only orchestration indirection;
2. define a Current Talent target and chronological validation harness before fitting anything complicated;
3. establish a simple baseline using recent Performance rates, age, level, recency, sample/evidence strength, and regression-to-environment;
4. separately define batting and pitching Current Talent inputs rather than forcing a premature universal feature vector;
5. require richer process/tracking features to beat the simple baseline out of time before they receive material weight;
6. keep playing-time/role inference separate from rate talent;
7. only after Current Talent is stable move to multi-horizon Projection and Player Value/WAR.
