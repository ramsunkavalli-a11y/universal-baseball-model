# Position evidence is ready for the full role comparison

Current assignments are now available for the full historical comparison,
not just its selected examples. All 23,412 player-season-level fielding totals
match the annual source. Starts match in 23,406 scopes; six unresolved DH-start
disagreements remain unknown. This fixes source coverage and representation,
not prediction accuracy. No new forecast has been fitted or deployed.

## What changed

The [source contract](defense-role-v16-source-contract.md) keeps 16,674 existing
2021–2024 feature rows and the same 12,432 later evaluation rows. A checked
multiple-player route captured 745 historical requests. Its exact bytes remain
local; the public evidence includes request identities, hashes, totals and
player reviews. No 2026 statistics were requested.

The first audit rejected two opposing-team position records and therefore lost
the other players in their batches. The [scope correction](defense-role-v16-scope-amendment.md)
isolates each person's validation and preserves team identity. It recovers
4,324 position records while reproducing all 981,330 previously accepted
records unchanged. The corrected inventory contains 985,654 player/game/team/
position records and retains all 51 previously certified simultaneous P/DH
start additions. Pitching innings never become hitter fielding innings.

Innings, starts and appearances are checked separately. A disputed DH
appearance does not erase matching innings or starts. Danny Jansen has two
catcher segments in the same resumed game; their innings and starts reconcile,
but counting team segments versus player-game appearances differs by one.
His appearance-count field stays qualified rather than changing his innings.
The other nine discrepancies involve DH counts; six lack one DH start in the
game log and three concern appearances only. No name-based repair was applied.

Among the original feature rows, 15,793 have matching current full-season
innings and starts, six retain partial start coverage, and 875 have no current
annual role record. Those 875 remain in the population with unknown current
assignment, not observed pure DH or zero defensive talent.

## Calendar checks changed the treatment of recent use

The official schedule's broad `Final` state also covers postponed listings.
The [calendar correction](defense-role-v16-calendar-amendment.md) uses detailed
completed-game states to distinguish a game played later from a game partly
played and then resumed. All annual role vectors stay unchanged.

This matters for Witt and Buxton. Their postponed games were played wholly
in August, so they have 1,346 known late SS outs and 484 known late CF outs,
respectively. Jansen's June 26/August 26 game and Jose Perez's July 13/August 5
DSL game actually span the boundary. Both team segments count toward annual
innings, but combined log innings cannot all be assigned to the original date.

In the final view, 47,496 of 20,841,401 hitter fielding outs have unresolved
early/late placement, about 0.23%. There are 102 position records without a
qualifying completed/date-matched schedule entry. These retain annual exposure
with unknown period. Across 2,327 player-season-level scopes, at least one
otherwise matching measurement has some uncertain date placement.

Known early exposure, known late exposure and unplaced exposure add to each
certified annual total. Separate bounds preserve useful recent evidence
without inventing a point date or erasing a whole season for one ambiguous game.
These are source descriptors, not fitted recency weights or projections.

## Player and numerical review

All nineteen focal players and 57 origin-blind peers retain their actual
histories, old inputs, fixed skill estimates, old forecasts and separate later
outcomes. The complete 684-line review and its corrected differences were read.
The two opposing-team cases and all ten measurement discrepancies were also
reviewed. Original failures and intermediate calendar results are preserved;
`calendar-repair/final-review.json` is the controlling completion receipt.

The independent replay verifies every capture hash, every annual measurement
flag, all calendar periods, nullable feature vectors, fixed identities and
period conservation. Period bounds are separately reconstructed. Fifty-seven
focused source, allocation and value tests pass. These checks establish source
construction within one official provider, not independent ground truth of
every box score or an accuracy gain.

## What the next comparison must fix

Witt's older 3B experience must not displace his current SS assignment. Buxton's
temporary DH year must not dominate his restored CF role. Ohtani's pure DH use
is observed, not an empty hitter role. Eldridge has current 1B/DH and older RF,
not the 2B/3B jobs borrowed from a broad first-base group. Carter, Chourio and
Dawson require full minor records as well as tiny higher-level stints. Simply
using the latest or highest level alone is not sufficient.

The next step is one contracted current-assignment/full-repertoire comparison
on the same population, holding batting, predicted PA, all twelve defensive
quality recipes, capacities and missing-player reserves fixed. Evaluate
individual role allocation, position credit, delivered defense and expanded
value separately, then walk through the same fixed cases and new gains/misses.
Do not repeat a generic-role, recency-weight or algorithm tournament.

This is the assignment part of the defense layer. Lower-minor defensive talent,
future position changes, multi-year exposure and cutoff-known assignment plans
remain unfinished. Frozen forecasts, the explorer and 2026 selection are
unchanged. Lovich's separate batting small-sample defect remains open.
