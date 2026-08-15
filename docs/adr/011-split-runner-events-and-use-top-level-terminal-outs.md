# ADR 011: Split runner events by playIndex and use top-level allPlay outs for terminal transitions

**Status:** Accepted for external-validation POC  
**Date:** 2026-08-15

## Context

The Performance value layer will eventually estimate league-typical run values for the accepted FaBIO-style event bins. A naive plate-appearance-wide state transition is not sufficient because runner actions can occur while the same batter is still at the plate.

The reuse audit identified two mature public precedents:

- Chadwick `cwevent` defines explicit start/end bases, start outs, event outs, and event runs;
- `baseballquery` reconstructs the same style of state from MLB Stats API data by splitting runner movements according to `runners[*].details.playIndex` before emitting the terminal PA/result event.

A six-game AAA + ACL/DSL/FCL audit confirmed that this is not a theoretical edge case. Among 439 official true PAs, 32 (7.29%) had at least one runner movement before the terminal playEvent. Observed event types included wild pitches, stolen bases, caught stealings, passed balls, balks, defensive indifference, field/pickoff errors, and a stolen base of home.

The first replay POC correctly reconstructed all 75 game runs and preserved state continuity, but produced 56 sequence-end base mismatches. Investigation showed that the terminal physical playEvent's `count.outs` is not the terminal result's end-outs state. It can remain at the pre-result outs count.

A conservative attempt to patch only inning-ending third outs failed immediately on a non-third-out case where the terminal playEvent had 0 outs while the top-level `allPlay.count.outs` was 1.

This exactly matches `baseballquery`'s public implementation pattern: use the individual playEvent count for runner subevents, but use the top-level plate-appearance/allPlay count for the terminal event.

## Decision

The state-transition replay uses the following semantics:

1. maintain a live base/out/score state through each half inning;
2. group official runner movements by `details.playIndex`;
3. emit state-changing preterminal runner/action transitions before the terminal result;
4. compact multiple same-runner movements at one playIndex into one origin -> final destination movement, following the baseballquery precedent;
5. use the individual `playEvent.count.outs` for a preterminal runner/action transition;
6. use top-level `allPlay.count.outs` for the terminal sequence result;
7. use runner movements to reconstruct bases and runs;
8. use official `matchup.postOn*` and result scores only as reconciliation targets, never as silent repair inputs;
9. do not reset a bad reconstructed state to the official end state between sequences. A real replay error must be allowed to propagate and fail later reconciliation.

The canonical conceptual grain is:

`game -> play_sequence -> 1..N state transitions`

A transition may be a preterminal runner event, a terminal PA result, or another official state-changing non-PA action.

## Validation

Using the corrected terminal-outs semantics on six recent affiliated games (three AAA plus ACL/DSL/FCL):

- state transitions: **476**;
- official true PAs: **439**;
- true-PA terminal transitions: **439**;
- preterminal runner/action transitions: **34**;
- replay quality-flag transitions: **0**;
- state continuity breaks: **0**;
- replayed runs: **75**;
- official final game runs: **75**.

Every sampled game individually had zero quality flags and zero continuity breaks.

This validation is intentionally stronger than copying official sequence-end state: reconstructed bases and scores are allowed to propagate, so a runner movement error can contaminate later state and become visible.

## Consequences

- PA-wide RE24 is rejected as the universal Performance-value input.
- The source MiLB `on_1b/on_2b/on_3b` fields remain useful post-sequence reconciliation evidence, not start-state inputs.
- Source `outs_when_up` remains useful evidence of physical playEvent count state, not terminal event outs.
- The accepted replay semantics now require an **independent MLB check against Retrosheet/Chadwick** before the state-transition schema is frozen for production.
- No run-expectancy matrix or player run-value score should be promoted until that external validation passes.
