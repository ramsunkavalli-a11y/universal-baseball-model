# Event-time fielders: supported coverage and one real source failure

2026-09-26. [Predeclared contract](defensive-timeline-v1-contract.md).
This repairs historical measurement, not a catcher skill forecast.

## What changed

We now reconstruct who was fielding at each event from the starting lineup and
chronological substitutions. A catcher entering halfway through a PA is not
credited with a steal or passed ball that occurred before he entered. Offensive
substitutes do not automatically inherit the replaced player's defensive position.
The terminal batter result is no longer our only opportunity to observe an event.

The first 128 games were development data. Two development edge cases required
explicit handling: a pre-first-pitch position change, and suspended-game players
appearing in both teams' box rosters. Neither is resolved by guessing a name.
All 128 development games then reconstructed and reconciled.

We locked a DISJOINT second 128-game sample, using the next two metadata-hash
ranks in each original season/level/league stratum. The implementation and tests
were frozen before fetching/scoring that sample. It spans 2016, 2018, 2021 and
2024, including rookie and short-season leagues. It is conditional on archived
PBP availability, not representative of games absent from the archive.

## Frozen validation result

**127 of 128 games reconstruct without an unresolved lineup.** On those games:

| Check | Result |
|---|---:|
| Event-time attributed SB / ordinary CS / pickoff-CS | 286 / 93 / 15 |
| Event-time attributed WP / PB | 218 / 50 |
| Comparable official per-player counts | 3,633 / 3,633 match |
| Runner-event scoring credits versus reconstructed fielders | 11,310 / 11,310 match |
| Final-PA pitcher matchup | 9,626 / 9,626 match |
| Archived terminal defender IDs | 86,634 / 86,634 match |
| Official team event totals | 1,016 / 1,016 match |

These counts are not only zero-event agreements. For example, 175 pitcher-WP
checks, 143 catcher-SB checks and 39 catcher-PB checks have positive official
counts. `verification.json` records all six metrics' positive denominators.
The box, event credits and archived feed are related scoring representations,
not independent human rescoring. The source sample is not a predictive holdout.

Pickoff-CS is retained separately. Its inclusion in official catcher CS totals
validates matching that accounting convention, not assigning the catcher all
causal credit. Throwing, pitcher holding, runner decisions and deterrence still
need separate models/denominators.

## The failed game is retained, not patched out of validation

Game **756445**, Lake Elsinore at Rancho Cucamonga, April 24, 2024:

- At PA 9/event 8, Wilman Diaz pinch-runs for left fielder Josue De Paula.
- At PA 10, the top of the second begins with no explicit new LF assignment.
- The feed records Diaz's LF assignment at PA 17, the top of the third.

The final box lists Diaz as PR/LF, but does not establish precisely when the
assignment took effect. Moving the later action backward would change the
validation rule after inspecting the failure. We do not do that. The whole game
fails this version's nine-fielder certification, even though the issue is LF,
not the battery. A future partial-lineup implementation could preserve certified
C/P while leaving LF unknown, but needs its own version/test; it is not silently
substituted into these scores.

The failed game's **11 events (3 SB, 2 PB, 6 WP)** still reconcile to all eight
team box counts. Thus event capture covers all 673 validation events; this
version certifies battery attribution for **662/673**, not 100%. No evidence
supports assuming the excluded events are representative. Scaling the decoder
must retain game-level failures and quantify event/exposure mass by level/year.

## Source decision

- Retain the event extractor and strict timeline as a **coverage-gated source
  implementation**. It has an independently selected validation sample, explicit
  failures, and seven synthetic substitution tests. Do not call every archived
  historical lineup certified.
- Earlier failed catcher throwing/deterrence/blocking tests remain unsuitable
  for rejecting the baseball skills because their event capture was biased.
- **Do not fit catcher rates yet:** pitch and runner-at-risk exposure must be
  reconciled, including incomplete PAs, inning-ending attempts, mid-PA changes,
  multiple runner advances, and interrupted/suspended games. Correct event
  numerators alone do not make a valid denominator.
- This is not framing or game-calling validation and adds no catcher WAR.

Reproduction: `audit_defensive_timeline_v1.py` supports development/validation
replays; frozen code hashes are checked. `verify_defensive_ledger_repairs_v1.py`
independently checks artifacts, positive counts, excluded event mass and the GB
ledger. Evidence is under `model_artifacts/defensive-timeline-v1-2026-09-25/`;
raw feed caches and detailed Parquet checks are local, hashed and reproducible.
No forecast or protected 2026 outcome changed/was used.
