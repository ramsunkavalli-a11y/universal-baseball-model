# ADR 027 — Use season residuals only to trigger official game-log outcome adjudication

Status: Accepted  
Date: 2026-08-16

## Context

Current Talent requires game-grain batting evidence so historical as-of snapshots can exclude future games. The reusable armstjc player-game release is therefore the primary MiLB outcome-history source, while separately published season-player batting aggregates provide an inexpensive independent accounting check.

A full 2022 comparison at player × actual-league × season grain found that the two reusable release families are extraordinarily close but not literally identical. Across the five post-reorganization MiLB level groups, only six player-league rows disagreed on PA/BB/HBP/K:

- AAA: one player with equal PA/K totals but a one-event BB↔HBP classification difference;
- Single-A: three players short a total of three PA and two strikeouts in player-game history;
- Rookie/complex: two players short a total of one PA and one strikeout;
- AA and High-A: exact.

A season-total discrepancy cannot safely be pushed backward into a historical game because doing so would invent chronology. The project therefore needed a game-grain adjudication source rather than a rule such as "season aggregate wins."

Targeted current official MLB Stats API `gameLog` hitting evidence was queried only for the six residual players. This localized every discrepancy.

## Decision

For post-reorganization historical MiLB batting outcome evidence:

1. **Resolved player-game data remains the primary chronological outcome source.**
2. Standardized season-player aggregates are an **independent residual trigger/check only**. They never specify which historical game to mutate.
3. If the player × actual-league season comparison is exact, make **no official game-log call**.
4. If a player-league residual exists, fetch the current official Stats API hitting `gameLog` for that player, season, and official sport ID.
5. Filter official evidence to the target actual league and regular season, and require a unique complete eight-field batting vector per positive-PA game:
   - PA;
   - AB;
   - BB;
   - HBP;
   - SO;
   - SF;
   - SH;
   - catcher interference.
6. When current official gameLog agrees with the reusable player-game history, **retain the reusable game history unchanged**, even if the season aggregate disagrees.
7. When current official gameLog identifies a different vector for an existing reusable game, apply a field-level official overlay for that game only. Preserve the reusable source's conservative/latest safe game date rather than replacing chronology with the current official date.
8. When current official gameLog contains a positive-PA game absent from reusable player-game history, insert that specific official game row explicitly. Record that its event date comes from current official gameLog and therefore belongs to retrospective corrected-history semantics.
9. Official-only zero-PA appearances are not inserted into the batting evidence surface.
10. A positive-PA source game absent from current official gameLog, duplicate official game identity, incomplete official outcome vector, or failure of corrected target totals to equal official game-log totals **fails closed**.
11. Persist exact official response bytes, hashes, retrieval time, endpoint, long-form field adjudication evidence, and the original reusable observations. No correction is silent.

This policy is `residual_triggered_official_game_log_v1`.

## 2022 certification evidence

Workflow run `31969018027` applied the generalized production adjudicator across all five level groups.

### Before adjudication

The independent player-game vs season-player audit covered approximately 792 thousand PA and found only six residual player-league rows:

- AAA: 1;
- AA: 0;
- High-A: 0;
- Single-A: 3;
- Rookie/complex: 2.

### Official adjudication

- **AA / High-A:** zero residuals, therefore zero official calls.
- **AAA:** one residual player. Current official gameLog matched the reusable player-game history exactly (426 PA, 77 BB, 4 HBP, 116 K); no game was changed. The season aggregate's 76 BB / 5 HBP split remains an explicit stale/revision residual.
- **Single-A:** all three residual players were confirmed as stale/incomplete reusable player-game evidence:
  - one official-only game with 1 PA / 1 AB / 1 K was inserted;
  - two existing games received field-level overlays;
  - six changed/inserted field evidence rows in total.
- **Rookie/complex:** both residual players required an existing-game overlay;
  - three changed field evidence rows in total.

Across Single-A + Rookie, the five source corrections were fully localized to one inserted game plus four existing games. After adjudication those two level groups reconcile exactly to their season aggregates.

The remaining 2022 season-aggregate residual is only the AAA BB↔HBP case where current official gameLog confirms the reusable player-game side. It is retained rather than forced to zero.

## Why gameLog, not season totals

The official season endpoint is useful as a diagnostic but is not the mutation oracle. In the targeted check, a Rookie/DSL player returned multiple season splits whose naïve summation double-counted his season PA. The current official `gameLog` preserved unique game identity and cleanly localized his single-PA difference.

Game-grain authority also prevents a season-end residual from being arbitrarily assigned to an earlier date, which would contaminate event-cutoff snapshots.

## Temporal semantics

Official adjudication uses **current corrected historical evidence**. Therefore any Current Talent backtest built from these corrected game rows is labeled:

`retrospective_event_cutoff_corrected_history_not_vintage_information_set`

It is not a true historical information-set reconstruction unless source `known_at` availability is separately proven.

## Non-decisions

This ADR does not:

- make official gameLog the default source for every historical MiLB game;
- make season-player aggregates authoritative over game history;
- erase the reusable source observations;
- define environment translation, talent shrinkage, recency weighting, age effects, or projection;
- imply that a sparse residual is a player-skill signal;
- extend the policy to pre-2021 league topology without the ADR 025 historical-extension gate.

## Consequences / next gates

1. Full historical MiLB Current Talent materialization should run the inexpensive season residual check before official game-log calls.
2. Only residual player-league rows receive official outcome adjudication.
3. The adjudicated player-game table and separate long-form adjudication table become inputs/provenance for contact/game-evidence materialization.
4. Full 2022 contact evidence may now be materialized across all five level groups.
5. Apply the same outcome-backbone/adjudication gate independently to 2023 and 2021 before those seasons enter Current Talent training.
6. Keep the completed live certification workflows manual-only; deterministic unit tests remain in normal CI.
