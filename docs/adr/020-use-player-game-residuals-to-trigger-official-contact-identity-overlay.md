# ADR 020 — Use player-game residuals to trigger an exception-only official contact identity overlay

**Status:** Accepted  
**Date:** 2026-08-15

## Context

ADR 019 established that reusable armstjc PBP preserves physical contact evidence well but can export the wrong batter when an `offensive_substitution` is actually a pinch-runner. A broad official-PBP replay would repair that identity defect, but it would defeat the reuse-first architecture if a much narrower trustworthy trigger exists.

The armstjc repository also publishes player-game batting boxscore files. Those files can independently control how many broad contact events (`AB - SO + SF + SH`) each player owns in a game, allowing us to localize participant-attribution defects without inspecting official PBP for every game.

## Player-game snapshot certification

The published player-game files contain two upstream snapshot quirks that must be handled before they can act as controls:

1. exact duplicated rows are common because the upstream monthly builder appends successful games twice; and
2. suspended/resumed or re-scraped games can appear as partial and complete player-game snapshots.

For 2024 AAA:

- raw projected player-game rows: **267,934**;
- exact duplicate rows removed: **138,410**;
- resolved player-games: **128,641**;
- conflicting player-games: **45**, concentrated in three games.

All 45 conflicts were component-wise partial→complete updates. Selecting a unique component-wise dominant observation when every relevant counting field moves monotonically forward resolved those snapshots; non-monotonic conflicts remain unresolved by policy.

After this rule:

- resolved player-game broad contacts: **111,878**;
- independently certified season aggregate `ballsInPlay`: **111,878**;
- exact player-league rows: **893 / 893**;
- absolute discrepancy mass: **0**.

Thus the resolved player-game layer is accepted as an independent contact-count control.

## Full-season reusable-PBP localization

The resolved 2024 AAA reusable PBP contained **111,884** contact keys, six more than the player-game broad-contact definition. Comparing source player/game contact counts to the resolved player-game control flagged **244 games** with at least one participant/count residual.

A source-only +1/-1 reassignment heuristic appeared highly attractive: it produced 182 strict candidates and mapped each candidate to exactly one source contact. However, independent official validation contradicted **1 of 182** candidates. A 99.45% repair is not acceptable for a production identity mutation, so the heuristic remains diagnostic only.

## Final official exception gate

Official PBP was fetched for all **244 flagged games**. Across those games:

- source contacts: **12,725**;
- official `isInPlay` contacts: **12,725**;
- matched physical contact keys: **12,725**;
- source-only physical keys: **0**;
- official-only physical keys: **0**;
- matched keys with source-vs-official batter mismatch: **254**.

Therefore the reusable source is not losing physical contact events in these flagged games; the dominant defect is participant attribution.

After replacing participant identity with official top-level matchup batter on the matching physical contact keys, only **12 player-game residual rows in 12 games** remained. Their residual mass was +9 / -3, net **+6**.

That +6 exactly matched the independent contact-definition difference:

- official PBP `isInPlay` contacts: **12,725**;
- official team-boxscore `AB - SO + SF + SH`: **12,719**;
- net difference: **+6**;
- games with a definition mismatch: **12**.

Those residuals are therefore preserved as a semantic difference between PBP `isInPlay` and broad boxscore contact accounting, not treated as missing/extra physical source contacts.

## False-negative check

A game-level residual trigger could theoretically miss two compensating wrong attributions that leave every player count unchanged. To test this, a deterministic evenly spaced sample of **120 unflagged 2024 AAA games** was frozen across the season and compared with current official PBP.

Results:

- official games returned: **120 / 120**;
- source contacts: **6,039**;
- official contacts: **6,039**;
- source-only physical contact keys: **0**;
- official-only physical contact keys: **0**;
- matched contact keys with batter mismatch: **0**.

This is not a mathematical proof that a cancelling attribution error can never occur outside the sample, but it is strong evidence that player-game residuals are a high-recall trigger for the observed source defect.

## Decision

1. **Reuse source PBP physical contact evidence by default.** Preserve natural contact keys, trajectory, coordinates, and original source participant ID.
2. Resolve reusable player-game boxscore snapshots with exact-deduplication plus the certified component-wise dominance rule. Never choose among non-monotonic conflicting snapshots automatically.
3. Compare reusable PBP contact counts with resolved player-game broad-contact counts at game/player grain.
4. **If any player residual exists in a game, fetch official PBP for that game only** and overlay the official top-level matchup batter on matching physical contact keys.
5. Do not automatically apply source-only +1/-1 reassignment heuristics, despite their high observed accuracy.
6. Preserve the original source batter ID and the authority source used for any overlay so participant corrections are auditable.
7. Do not force official PBP `isInPlay` totals to equal `AB - SO + SF + SH`; store/report semantic definition residuals separately.
8. Games with no player-game residual use reusable source participant identity by default, backed by the zero-error 120-game false-negative sample. Future certification can expand that sample or add periodic checks without changing the model interface.
9. This policy governs **contact-profile participant identity**. Standard outcome counts continue to come from the certified season aggregate backbone.

## Consequences

- Historical Performance contact profiles do not require official PBP for every game.
- Official PBP becomes a narrow authority overlay driven by a reusable-data quality control.
- The policy avoids both silent pinch-runner corruption and a costly all-history official replay.
- Physical source contact coverage and participant identity are treated as separate quality dimensions.
- Production materialization must expose whether a contact batter is `source_default` or `official_exception_overlay` and preserve the original ID.

## Supporting artifacts

- `src/universal_baseball/player_game_stats.py`
- `scripts/audit_player_game_contact_localization.py`
- `scripts/audit_official_contact_policy_final.py`
- `scripts/audit_contact_identity_false_negative.py`
- successful final contact workflow run `31928276587`
- successful false-negative workflow run `31928454614`
