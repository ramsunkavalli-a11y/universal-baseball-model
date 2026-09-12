# Current Talent 2024 source exceptions

Last updated: 2026-09-12  
Status: **SEVEN NARROW GAME EXCLUSIONS CERTIFIED; ROOKIE IDENTITY REVIEW REMAINS.**

The first full 2024 talent-evidence build exposed seven source-only game records that
cannot enter the model:

- game 755829 (2024-06-16, High-A) is `Cancelled: Rain` in the official Stats API,
  but the reusable player-game source contains positive-PA evidence;
- game 754395 (2024-05-05, Single-A) is `Cancelled: Rain` officially, but the reusable
  source contains positive-PA evidence;
- game 774353 (2024-07-09, DSL) exists officially, but its feed has no player records
  and the reusable PBP game has no same-game player-game league/participant authority.
- game 774292 (2024-07-09, DSL) is `Cancelled: Rain` officially, but the reusable
  source contains positive-PA evidence.
- games 774039 and 774458 (2024-07-09, DSL) are `Cancelled` officially, but the
  reusable source contains positive-PA evidence;
- game 774578 (2024-07-09, DSL) is `Cancelled: Lightning` officially, but the
  reusable source contains positive-PA evidence.

A full official-schedule comparison found many additional games currently labeled
`Postponed`. They are not excluded: the reusable player-game evidence may represent
rescheduled play, and a status label alone is insufficient authority to erase it.

The source adapter now excludes only these exact game/date/type fingerprints and
records every removed row. Any date or game-type drift fails closed. This is not a
general cancelled-game rule and does not authorize filename-level league guessing.

Triple-A and Double-A passed the unmodified full-season gate. High-A and Single-A
passed after the exact cancelled-game corrections. The final rookie/complex rerun
cleared the registered games, then stopped on a different source identity residual:
player 800230 has a four-PA line in game 773890 but no official player game log.
Rookie/complex remains unavailable until that identity class is audited together; do
not add another one-off correction merely to finish the run.
