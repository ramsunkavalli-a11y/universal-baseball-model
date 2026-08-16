# ADR 012: Freeze validated state replay and RE24 mechanics; defer production bin weights

**Status:** Accepted for foundation architecture  
**Date:** 2026-08-15

## Context

ADR 011 accepted split runner/action transitions inside a play sequence and required an independent MLB validation before the state-transition schema could be treated as foundation infrastructure.

That validation is now complete.

The corrected Stats API replay was first exercised on six affiliated games spanning AAA and ACL/DSL/FCL. It produced 476 transitions from 439 official true PAs, including 34 preterminal runner/action transitions, with zero replay quality flags, zero state-continuity breaks, and 75 reconstructed runs against 75 official final-game runs.

The independent Retrosheet gate then compared the replay to a separate event-account source for three 2025 MLB games. Across 228 ordered candidate transitions:

- Stats API replay transitions: **228**;
- Retrosheet candidate plays: **228**;
- exact ordered state-match games: **3/3**;
- half-innings with transition-count mismatch: **0**;
- shared-position transitions with any state mismatch: **0**.

The comparison covered PA flag, start/end outs, start/end base occupancy, event runs, and batting-team score before/after the event.

A full-season independent RE24 audit on the 2025 Retrosheet play archive then produced:

- games: **2,478**;
- candidate state transitions: **193,080**;
- completed three-out half-innings used for estimation: **43,875**;
- incomplete/walkoff half-innings excluded from estimation: **228**;
- observed base/out states: **24/24**;
- RE24 coverage: **193,080 / 193,080 (100%)**;
- empty-base and bases-loaded run expectancy both declined monotonically as outs increased.

Finally, the same state/value architecture was exercised on 75 affiliated MiLB games across five league-season environments: 2024 ACL, FCL, DSL and 2025 PCL, IL. All five environments observed 24/24 states, and all 5,539 core pre-foul-screen Performance PAs joined to an RE24 value.

A larger 45-game-per-environment stability audit showed that this validates the mechanics but does not justify freezing direct sampled league-season bin means. Alternating 23-vs-22-game split-half bin-value MAE ranged from roughly 0.058 to 0.103 runs across the five environments, with individual-bin differences materially larger.

## Decision

The following foundation mechanics are frozen:

1. canonical state grain is `game -> play_sequence -> 1..N state transitions`;
2. preterminal runner/action transitions are split by runner `details.playIndex`;
3. individual playEvent outs are used for preterminal transitions;
4. top-level `allPlay.count.outs` is used for the terminal transition;
5. bases and runs are reconstructed from runner movements and allowed to propagate without silent repair;
6. official matchup post-base state and result scores are reconciliation targets, not repair inputs;
7. run expectancy is estimated from the 24 start base/out states using completed three-out half-innings;
8. event RE24 is `runs_scored + RE(after) - RE(before)`, with terminal half-inning `RE(after)=0`;
9. Performance bins receive **league-typical event values**, not the batter's contextual baserunner outcome as a skill credit.

The following is explicitly **not** frozen:

- direct 15-, 25-, 35-, or 45-game league-season FaBIO-bin means as production weights;
- a pooling/shrinkage rule;
- the amount of historical official PBP required per league-season;
- the final foul-air eligibility screen for the 12-bin skill view.

## Consequences

- State reconstruction and RE24 mechanics are no longer open architecture questions.
- Retrosheet remains an independent MLB validation source rather than a replacement for MiLB official state evidence.
- The next Performance-value gate is statistical: compare direct league-season estimates with explicit pooling/shrinkage and/or larger certified samples using out-of-sample or split-half error.
- No player score or projection should depend on sampled bin weights until that estimator decision is frozen separately.
