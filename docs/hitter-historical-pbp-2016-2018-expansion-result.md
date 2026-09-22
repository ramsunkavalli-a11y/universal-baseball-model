# Hitter historical PBP expansion result

## Result

The detailed hitter contact data now forms a complete, park-ready 2016–2018
block. Every model-ready contact event in those three seasons can be tied to an
official game and exact venue. No model was fit and no 2026 result was opened.

| Season | Model-ready contact events | Contact games | Official game contexts | Contacts with venue | Missing contacts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2016 | 649,431 | 13,069 | 13,089 | 649,431 | 0 |
| 2017 | 637,638 | 12,940 | 12,949 | 637,638 | 0 |
| 2018 | 633,575 | 13,175 | 13,184 | 633,575 | 0 |
| **Total** | **1,920,644** |  | **39,222** | **1,920,644** | **0** |

The contact parser resolved 2,032,984 historical contact rows before the
model-ready full-ball-in-play filters. The table above reports the final event
surface that the hitter component model can consume.

## How the missing 2018 authority was recovered

The archived public player-game files were incomplete for parts of 2018, but
the underlying official game feeds were still available. The recovery uses the
public schedules to enumerate played regular-season games and then projects
player batting lines, league identity, game date, and venue directly from each
official feed. Raw responses are cached with content hashes so the result can
be reproduced and audited.

The completed 2018 authority contains:

- 13,184 of 13,184 scheduled played games;
- 258,767 player-game rows, including 250,129 with a positive plate appearance;
- 5,216 players, 203 venues, and 18 leagues;
- zero failed or missing games; and
- an exact 912-of-912 row match against a 50-game sample from an available
  archived player-game release, with zero field mismatches.

Old Short-Season A is retained as its own level. Official fractional historical
season labels such as `2018.1` are accepted only when their integer year agrees
with the official game date.

## Historical edge cases

The same reconstruction completed 13,089 games in 2016 and 12,949 games in
2017. Two 2016 feeds contained suspended-game player listings for both clubs.
The recovery now combines those official batting stints; it leaves team
identity blank only when a player actually recorded plate appearances for both
clubs. Four Dominican Summer League games were decided by ineligible-player
forfeit after recording play-by-play. They are retained because they contain
real contact events and official venue context.

Independent 50-game archive comparisons also passed exactly in 2016 (934
positive-PA rows) and 2017 (924 positive-PA rows), with no missing, new, or
mismatched rows.

## What this establishes—and what it does not

This closes the historical source gap for detailed 2016–2018 contact modeling
and gives the park-adjustment work exact venue identity rather than an inferred
park. It does not prove that detailed contact features improve next-season
player projections. The next experiment must build these seasons into the same
chronology-safe player-season feature surface used by the current gradient
challenger, then compare it with the mandatory simpler benchmarks on later
seasons.

The 2026 forecast remains frozen and untouched.

## Reproducible outputs

- `scripts/recover_hitter_v2_2018_game_authority.py` reconstructs any requested
  historical season through `--season` and records source provenance.
- `scripts/audit_historical_contact_context_coverage.py` verifies that every
  model-ready contact has official venue context.
- `reports/generated/historical-contact-context-coverage/report.json` is the
  machine-readable acceptance report for the 2016–2018 block.
