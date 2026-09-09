# Phase 1 replay: current integration checkpoint

**As of:** 2026-09-08  
**Status:** passed current mechanical integration; historical validation not yet run

The first value checkpoint now passes the frozen sequential-replay interface. It is
labeled `retrospective_event_cutoff`, not a vintage historical reconstruction.

## Result

- frozen rights-universe players: **8,393**;
- value records retained: **8,393**;
- available player values: **8,363**;
- review players: **30**;
- missing control/economics paths: **19**;
- contract-structure review players: **11**;
- last completed regular-season game represented: **2026-09-08**;
- expected remaining WAR on available paths: **4,649.93**;
- expected remaining cost on available paths: **$17.121 billion**;
- discounted transferable-rights value: **$5.893 billion**.

This is a coverage and accounting checkpoint, not validation of the dollar ranking.
The league total includes the named future-market and post-2026 CBA planning
assumptions already disclosed by Contract Economics.

## Service correction

The rebuild corrected one safe service-time omission. A player whose official first
MLB debut occurs during the current season necessarily had zero service entering that
season. Felix Reyes therefore receives zero opening service plus his 50 official 2026
days and now reaches the control/economics path. The rule does not apply to the other
19 missing players because they debuted in earlier seasons and lack a verified opening
balance.

## Remaining current reviews

The 19 missing paths are retained as reviews rather than dropped. Eighteen are broad
full-roster assignments for players with prior MLB service but no FanGraphs opening
balance; one prior-service case is also retained. Their current affiliation and opening
service require stronger evidence before value is calculated. The separate 11-player
contract queue remains the known vesting, linked-option and missing-salary work.

## Next replay input

The engine is ready for more than one checkpoint and produces an adjacent-checkpoint
delta ledger. The next honest build is a retrospective completed-season checkpoint.
Historical performance and roster evidence exist, but the repository does not yet
contain dated historical league-wide payroll/contract snapshots or a validated opening
service baseline for those dates. Those missing inputs must remain review fields; they
cannot be reconstructed from current FanGraphs files or StatsAPI performance alone.

Implementation: `src/universal_baseball/sequential_replay.py` and
`scripts/materialize_current_replay_checkpoint.py`.
