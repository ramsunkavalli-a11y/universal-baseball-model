# ADR 004: Use official event semantics for PA accounting

- Status: Accepted for foundation work
- Date: 2026-08-15

## Context

The MLB Stats API `game/{gamePk}/playByPlay` endpoint exposes an `allPlays` array. It is tempting to treat each `allPlays` row as one plate appearance.

Live reconciliation proved that this is wrong. Recent MiLB games contain `allPlays` result rows whose structured `eventType` is a runner or game event such as `pickoff_1b`, `caught_stealing_2b`, `caught_stealing_3b`, `other_out`, or `game_advisory`. Those rows can still carry `result.type="atBat"`, so `result.type` is not a sufficient PA discriminator either.

The Stats API separately exposes `/api/v1/eventTypes`, which explicitly marks event codes with a `plateAppearance` flag. A reproducibility snapshot of those semantics retrieved on 2026-08-15 is stored in `src/universal_baseball/event_types.py`.

## Decision

1. Do not infer PA grain from the number of `allPlays` rows.
2. Do not infer PA status from `result.type` alone.
3. Use the official Stats API event-type `plateAppearance` semantics to decide which structured result events count as PAs.
4. Keep known non-PA result rows as evidence/debugging data but exclude them from batting PA accounting.
5. Treat any event code absent from the versioned reference snapshot as **unknown**. Do not silently classify it. Unknown or blank result event types fail the reconciliation certification gate until reviewed.
6. Reconstruct AB from auditable components using `PA - BB - HBP - SH - SF - CI`, then reconcile PA, AB, H, 2B, 3B, HR, BB, IBB, HBP, K, SH, SF, and CI to the official game boxscore.
7. Preserve the dated event-type reference because current metadata can change. Historical/as-of model validation must know which classification semantics were used.

## Evidence

The first PBP-to-boxscore attempt naively counted every `allPlays` row. MLB and Single-A control games happened to reconcile, but selected AAA, AA, High-A, and Rookie games were each high by one or more PAs/ABs. The extra rows were structured non-PA event types.

After switching to the official event-type flags, the test suite reconciled **all 22 home/away batting lines across 11 representative MLB/MiLB games** exactly for all 13 audited batting totals, with no blank or unknown result event types. The sample includes MLB, AAA, AA, High-A, Single-A, and Rookie-level games, plus a MiLB game whose irregular pitch-type payload breaks the stricter high-level `python-mlb-statsapi` PBP model.

This is a useful example of the project's source philosophy: reuse the upstream structured semantics and verify them against a second official representation rather than creating text heuristics or assuming the obvious row grain.

## Consequences

- The canonical PA layer can be built from structured result codes without parsing narrative descriptions.
- Runner/game events remain available for future baserunning or state reconstruction without contaminating batting PA counts.
- New Stats API event types become explicit schema-governance events rather than silent data drift.
- The event-type snapshot needs a controlled refresh process later; it should not be fetched dynamically during historical backtests.
