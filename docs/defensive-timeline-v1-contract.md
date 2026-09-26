# Defensive timeline validation — before opening new validation games

2026-09-25. Continue the repair goal; no skill fitting or frozen forecast changes.
The previous 128-game sample is now development evidence, not validation.

## Development

Reconstruct nine defensive positions from official game starters and chronological
substitution/switch actions. Apply changes at their event index, never to earlier
events in the PA. Team membership must be grounded in box records. Do not use
English names to infer identities. Pinch hitters/runners remove the replaced
player but do not inherit his defensive position until an explicit assignment.
Unknown/conflicting positions or incomplete starting lineups fail the relevant
game's certification, rather than carry a last-known fielder silently.

Compare event-time identities with scoring credits, terminal historical defender
IDs, pitcher matchup, and per-player official WP/PB/SB/CS records where semantics
are comparable. Pitcher counts and catcher credits are separate from simply
being present during a pickoff. Verify substitution edge cases with synthetic
tests, including mid-PA changes and safe-on-error caught-stealing credits.

## Independent source-validation sample

Use the same 2016/2018/2021/2024 metadata strata and SHA256 ordering as the
original defensive-event sample. Select ranks 3–4 per season / level / league
(the original used ranks 1–2). Lock IDs, original selection hash and source hashes
before retrieving or opening their full feeds. No outcome-based replacements.
Missing games, missing events and conflicts remain explicit. Freeze timeline
implementation hashes after development and before scoring validation.

Require exact comparable per-game/player identities and event totals for a
certified slice. Report denominators, event families, levels, eras, positive
events, all discrepancies and omitted comparisons. Passing many zero counts is
not enough. First-touch credits only validate who handled a ball, not who should
have reached it. This is a source test, not predictive model validation.

## Fielding connection

Use the timeline for named fielders in a complete event ledger. Preserve balls
through the infield, unknown responsibilities, pitcher/1B chances, FC and errors.
Continue to separate observed handling from opportunity. Do not call a nearest-
fielder or equal-share allocation certified merely because it adds to one.
Outcome-comparable exposure can be coarser than a precise range estimate, but
must retain failed chances and document what skill it can actually measure.
