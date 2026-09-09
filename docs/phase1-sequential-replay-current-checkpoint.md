# Phase 1 replay: current integration checkpoint

**As of:** 2026-09-08  
**Status:** passed current mechanical integration; historical validation not yet run

The first value checkpoint now passes the frozen sequential-replay interface. It is
labeled `retrospective_event_cutoff`, not a vintage historical reconstruction.

## Result

- frozen rights-universe players: **8,393**;
- value records retained: **8,393**;
- available player records: **8,369**;
- controlled player values: **8,332**;
- talent-only players with no incumbent rights: **37**;
- review players: **24**;
- missing control/economics paths: **13**;
- contract-structure review players: **11**;
- last completed regular-season game represented: **2026-09-08**;
- expected remaining WAR on available paths: **4,652.63**;
- expected remaining cost on available paths: **$17.119 billion**;
- discounted transferable-rights value: **$5.888 billion**.

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

## Rights correction and remaining reviews

The official season `fullRoster` feed can retain released players. Exact releases now
override that broad candidate source. Releases by an affiliate are used only when the
official current-team record supplies one unambiguous MLB parent; 205 mappings pass and
three conflicted team IDs are ignored. Current affiliate mappings are never applied to
older-season releases. This resolves 37 players as having talent but no incumbent trade
rights. A later signing still supersedes a prior release.

The 13 missing paths remain reviews rather than being dropped: 12 players have prior
MLB service but no verified FanGraphs opening balance, and Adam Maier has conflicting
same-day ownership transactions. The separate 11-player contract queue remains the
known vesting, linked-option and missing-salary work.

## Next replay input

The engine is ready for more than one checkpoint and produces an adjacent-checkpoint
delta ledger. The next honest build is a retrospective completed-season checkpoint.
Historical performance and roster evidence exist, but the repository does not yet
contain dated historical league-wide payroll/contract snapshots or a validated opening
service baseline for those dates. Those missing inputs must remain review fields; they
cannot be reconstructed from current FanGraphs files or StatsAPI performance alone.

Implementation: `src/universal_baseball/sequential_replay.py` and
`scripts/materialize_current_replay_checkpoint.py`.
