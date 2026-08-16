# ADR 021 — Overlay contact participant identity at play-sequence grain

**Status:** Accepted  
**Date:** 2026-08-16

## Context

ADR 020 established an exception-only official participant overlay for reusable contact evidence: resolved player-game boxscore residuals identify games where the armstjc pinch-runner substitution bug may have corrupted batter identity, and official MLB Stats API evidence supplies the authoritative batter.

The first AAA certification used the strictest possible join: current official `isInPlay` pitch keys (`game_pk + at_bat_index + pitch_number`) had to match the reusable historical contact keys exactly before participant identity could be overlaid.

That worked perfectly in 2024 AAA, but the 2024 all-level Performance POC exposed a distinction that matters for historical data architecture:

- **participant identity is a property of the play/matchup sequence**;
- **physical contact coding is a property of the historical contact observation**; and
- current corrected official `isInPlay` pitch coding can differ slightly from a historical reusable snapshot without making the official matchup batter ambiguous.

Requiring current official contact-pitch equality to establish participant authority therefore couples two evidence questions that should remain separate.

## Strict contact-pitch diagnostic

In residual-triggered games:

### Double-A

- exception games: **226**;
- reusable / current-official contacts: **11,301 / 11,301**;
- source-only / official-only exact pitch keys: **1 / 1**;
- exact-key mismatch games: **1**;
- source-only / official-only distinct contact-sequence keys: **0 / 0**;
- sequence matches with pitch-number drift: **9**.

### Rookie / complex

- exception games: **422**;
- reusable / current-official contacts: **19,191 / 19,194**;
- source-only / official-only exact pitch keys: **3 / 6**;
- exact-key mismatch games: **8**;
- current contact-status coding therefore differs on a handful of sequences.

These differences are small but real. They must not be erased by pretending the current official feed is an exact historical-data vintage.

## Sequence-authority gate

A separate gate then asked only the participant question: does every reusable source contact sequence in every residual-triggered game map to one unambiguous top-level official matchup batter at `game_pk + at_bat_index`?

### Double-A

- exception games: **226 / 226** returned official authority;
- reusable contact rows: **11,301**;
- distinct reusable contact sequences: **11,297**;
- source contact sequences covered by official matchup authority: **11,297 / 11,297**;
- missing source contact sequence authority: **0**;
- contact rows whose source batter differs from official matchup batter: **227** across **207 games**.

### Rookie / complex

- exception games: **422 / 422** returned official authority;
- reusable contact rows: **19,191**;
- distinct reusable contact sequences: **19,190**;
- source contact sequences covered by official matchup authority: **19,190 / 19,190**;
- missing source contact sequence authority: **0**;
- contact rows whose source batter differs from official matchup batter: **399** across **345 games**.

Thus participant authority is complete even where current official contact-pitch coding is not an exact historical mirror.

## Unified five-level confirmation

The completed-2024 Performance build then ran AAA, AA, High-A, Single-A, and Rookie/complex through the same production path using play-sequence participant authority.

Across the five level groups:

- player × actual-league × season rows: **4,995**;
- plate appearances: **784,285**;
- resolved/classified reusable contacts: **494,884**;
- weighted screened-core Performance coverage: **97.50% of PA**;
- player-game exception games: **1,325**;
- contacts in exception games receiving official matchup authority: **64,720**;
- source batter IDs actually changed by the official overlay: **1,293**;
- unflagged participant spot-checks: **40 games per level group**, all with zero hidden batter mismatches;
- contact-status source conflicts: **0** at every level;
- unresolved player-game contact controls: **0** at every level;
- unvalued core Performance events: **0**;
- player-season Parquet/DuckDB canonical-grain uniqueness: passed at every level.

Level-specific source-vs-season-aggregate broad-contact residuals remain explicit rather than normalized away:

- AAA: **+6 / 111,884** reusable contacts;
- AA: **+9 / 98,790**;
- High-A: **+28 / 93,221**;
- Single-A: **-44 / 91,612**;
- Rookie/complex: **-108 / 99,377**.

The largest absolute net difference is about **0.11%** of Rookie/complex contact rows. These are retained as coverage/definition evidence and are not converted into synthetic contact events.

## Decision

1. **Physical contact evidence remains source-authoritative after certified source snapshot consensus.** Preserve its historical natural pitch key, trajectory, coordinates, narrative, and source participant ID.
2. Player-game broad-contact residuals remain the trigger for official participant review.
3. For every triggered game, fetch official allPlays/play-sequence evidence and project the **top-level matchup batter at `game_pk + at_bat_index`**.
4. Require every reusable source contact sequence in the triggered game to map to exactly one non-null official matchup batter.
5. Overlay that batter identity onto every reusable contact row in the sequence. Preserve the original source batter and authority provenance.
6. **Do not require current official `isInPlay` pitch number or contact-status equality** in order to establish participant identity.
7. Keep the stricter current-official contact-pitch comparison as a diagnostic for source/contact-status revision, not as the production participant join.
8. Never use current corrected official contact coding to silently rewrite historical reusable physical contact evidence solely because the current feed differs.
9. Continue reporting source-vs-boxscore/aggregate contact residuals explicitly. Do not invent or delete contacts to force equality.
10. Unflagged games use the reusable source batter by default, backed by deterministic level-specific spot checks; future audits can expand those checks without changing the materialized schema.

## Consequences

- The participant overlay now follows the actual semantic grain of participant authority.
- AA and Rookie/complex no longer fail because today's official pitch/contact coding differs slightly from historical reusable snapshots.
- Historical source contact geometry remains stable and provenance-preserving.
- Current-official revisions remain visible as separate quality evidence instead of contaminating participant resolution.
- One production participant policy works across AAA, AA, High-A, Single-A, and 2024 Rookie/complex Performance evidence.
- This decision does not change the separate league × season pitch-process capability policy; synthetic DSL/older complex pitch sequences remain process-ineligible where previously certified.

## Supporting artifacts

- `src/universal_baseball/contact_identity_overlay.py`
- `scripts/audit_contact_key_alignment.py`
- `scripts/audit_contact_sequence_authority.py`
- `scripts/build_batting_performance_level_poc.py`
- `scripts/build_batting_performance_level_poc_v2.py`
- sequence-authority workflow run `31947413112`
- unified five-level Performance workflow run `31947735600`
