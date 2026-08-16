# ADR 016 — Gate pitch-process evidence by league-season fidelity

**Status:** Accepted  
**Date:** 2026-08-15

## Context

A correct official plate-appearance result does not prove that the intermediate `playEvents` are a physical pitch-by-pitch record. Lower-level games can be entered as outcome-minimal sequences: a strikeout as three strike events, a walk as four ball events, or a batted-ball PA as one terminal pitch.

That distinction matters because the universal Performance layer can still use reliable PA outcomes, terminal batted-ball evidence, identities, and state transitions, while pitch-process features such as pitches/PA, swing/whiff rates, called strikes, count paths, sequencing, and count-conditioned pitch usage would be fabricated if the feed is outcome-minimal.

A dedicated audit therefore uses armstjc PBP only as a deterministic game/league inventory and computes the fidelity diagnostic from current official MLB Stats API `game/{gamePk}/playByPlay`. Each actual league is sampled with 20 games spread across the source asset. Single-A is the control.

The pre-specified synthetic signatures are:

- strikeout with exactly 3 recorded pitch events;
- walk with exactly 4 recorded pitch events;
- batted ball with exactly 1 recorded pitch event;
- official `pitchNumber` gaps are checked separately to determine whether omitted physical pitches remain recoverable from numbering.

## Evidence

### August 2023 replication

The 2023 Rookie asset required only the already-certified spelling aliases `leauge_id -> league_id` and `leauge_name -> league_name`; the diagnostic itself was unchanged.

Pooled Single-A control (20 games per actual league):

- K: 1,133 PAs, mean 4.781 recorded pitches, 16.9% exactly 3;
- BB: 515 PAs, mean 5.472, 21.2% exactly 4;
- BIP: 2,935 PAs, mean 3.145, 18.8% exactly 1;
- pitch-number-gap rate: 0%.

Rookie/complex leagues were dramatically different:

| League | K exactly 3 | BB exactly 4 | BIP exactly 1 | Interpretation |
|---|---:|---:|---:|---|
| Arizona Complex League | 92.7% | 98.8% | 91.0% | outcome-minimal / synthetic |
| Florida Complex League | 93.0% | 96.7% | 91.4% | outcome-minimal / synthetic |
| Dominican Summer League | 90.1% | 98.8% | 89.9% | outcome-minimal / synthetic |

Pitch-number-gap rate was 0% in all three leagues. The official numbering therefore does not preserve a hidden physical pitch count in these sampled sequences.

### June 2024 audit

Using the identical diagnostic against 2024 Rookie/complex and Single-A inventories:

- ACL and FCL sequence distributions looked like the Single-A control rather than the 3/4/1 synthetic pattern;
- DSL remained strongly outcome-minimal/synthetic;
- no evidence supported treating all Rookie leagues as one fidelity class.

The combined 2023/2024 evidence therefore identifies a real league×season/era boundary: ACL/FCL improved between the tested 2023 and 2024 feeds, while DSL did not.

## Decision

Pitch-process evidence is **capability-gated by league and season**.

Certified initial matrix:

| Season | ACL | FCL | DSL |
|---|---|---|---|
| 2023 | ineligible — synthetic | ineligible — synthetic | ineligible — synthetic |
| 2024 | eligible | eligible | ineligible — synthetic |

Any league-season not explicitly certified defaults to `uncertified`, never to eligible.

This capability applies only to intermediate pitch-process evidence. An ineligible pitch-process status does **not** invalidate otherwise certified:

- official PA existence and outcome;
- K/BB/HBP/BIP Performance accounting;
- terminal batted-ball trajectory/direction where present;
- participant identity after official reconciliation;
- runner/base-out state transitions;
- RE24 calibration at the event/state level.

Features requiring genuine intermediate pitches must require `pitch_process_is_eligible(...) == true`, including at minimum:

- pitches per PA;
- swing / take / whiff / called-strike rates;
- count progression and count-based splits;
- chase or zone-process estimates derived from pitch opportunities;
- pitch sequencing;
- count-conditioned pitch usage or execution models.

Single-A served as a normal control in both tested years, but A-ball and higher levels should still be certified before a production process model assumes universal pitch-sequence fidelity.

## Consequences

1. The model can remain universal MLB-to-DSL without pretending evidence quality is uniform.
2. 2023 ACL/FCL players retain outcome/profile Performance evidence but cannot receive pitch-process features from those feeds.
3. 2024 ACL/FCL pitch-process evidence may be used subject to the normal field-coverage rules.
4. DSL pitch-process evidence remains unavailable in both certified years; later seasons require new certification rather than extrapolation.
5. Coverage status becomes model evidence metadata, not player skill and not a missing-value imputation target.
6. The expensive fidelity audit is manual-only after this gate; deterministic capability behavior remains unit-tested.
