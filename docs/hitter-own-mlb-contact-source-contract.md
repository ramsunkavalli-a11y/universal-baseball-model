# Recovering MLB contact history for the hitter model

2026-10-04. The practical candidate uses MLB result counts, but the reviewed
ninety-cell contact extension contains only minor-league contacts. Recover the
existing ordinary MLB contact evidence before testing adjusted hitting talent.
This is source construction, not another projection experiment or a claim that
contact will improve forecasts. Team-record testing stays closed.

## Scope and source

Reuse the complete cached 2023 and 2024 MLB captures in the August park-input
workspace. Verify the original capture hashes, official schedule and team
authority, accepted player-game profiles and their independent official-count
reconciliation. Read only a fixed list of ordinary pitch/result fields needed
by the existing source adapter. Do not project tracking metrics, estimated
contact values, future-game intervals or age fields from the raw files.

Reuse the accepted physical-contact classifier, true-PA outcome attribution
and two-strike substitution policy. Keep physical hitter identity distinct from
the player officially charged a strikeout. Add structured contact results and
the actual game's venue, not current park dimensions. Preserve missing geometry,
bunts, foul-air contacts and unsupported results outside the ninety cells.
No new network collection, source overwrite, 2026 outcome access or model fit.

## Checks before use

Reconstruct accepted player-game profiles and summaries exactly. Reconcile PA,
K, unintentional walks, HBP, hits split into 1B/2B/3B/HR against the current
official season-count backbone. Distinguish physical contact exposure from PA;
small certified physical-contact residuals must not be erased. Require unique
game/PA/pitch identities, valid dates, a one-to-one schedule match and actual
AL/NL assignment. Missing venues stay flagged rather than imputed.

Save an event ledger, player-season ninety-cell counts, classification exclusions
and context coverage. These are raw measurements, not park-neutral MLB ability.
No old two-fold park adjustment may enter five-fold forecast validation. A later
learned adjustment must exclude the entire outer player fold, respect each
feature row's own origin and account for opponent/personnel composition.

Count contact-bearing active training people separately in every existing outer
cell, using only source seasons available by each row's own origin. Current
origin predictors end at that origin; model-training labels end by the outer
cutoff and exclude 2020 and the entire held-player group. A newly recovered
test-season profile does not manufacture earlier training profiles. Report
historical gaps and do not fill 2016–2022 or 2020 with average measured contact.

## Player review and disposition

Fix Judge at origins 2023 and 2024, Soto 2023, Belt 2023, Torkelson 2023,
McLain 2023, Kurtz 2024 and Caceres 2024. Add the two largest missing-profile
fractions among MLB players with at least 200 PA, one per source season.
Select up to four same-origin/stage/debut peers using origin age, PA, recorded
position and current performance/rank inputs, never future success.

For each case save dated official histories, contact counts and exclusions,
nonzero cells, venues, both hands, unchanged current PA/hitting/value and observed
next-year MLB results. Show that absent minor-player MLB evidence is missing,
not average hitting. Trace what was omitted from the current input recipe;
do not fabricate a new contact forecast or a hypothetical improvement.
Complete a readable source walkthrough before approving these measurements.

Accept only as a source for further research if identity, count, profile and
provenance checks pass and exclusions remain explicit. Two recovered seasons
cannot support a claimed ten-year contact forecast comparison. The next source
decision must address the missing earlier history and clean park/opponent
measurement before fitting. Keep current forecasts and explorers unchanged.
