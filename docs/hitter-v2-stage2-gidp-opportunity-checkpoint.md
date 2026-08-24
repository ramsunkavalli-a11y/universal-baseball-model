# Hitter v2 Stage 2 GIDP-opportunity checkpoint

Recorded: 2026-08-23  
Implementation commit: `68c244fe88a8bb35bdbc0485122bf7d82baf54b7`  
Candidate fit/scored: **no / no**  
Protected 2026 opened: **no**

## Scientific outcome

The C1 GIDP-opportunity input is source-ready on a failed-closed subset of the
2021–2024 universal player-game table. It contains 932,024 exactly reconciled
player-games and 3,672,168 official PA, covering 97.2844% of model-ready
player-games and 97.2954% of their PA. These rows contain 809,854 observed GIDP
opportunities and 59,577 official GIDP.

No candidate was fit or scored. This checkpoint changes neither fold
membership nor any batting prediction.

## Capability-specific state semantics

The audit found that the same field name has different certified semantics:

- MLB Savant `on_1b` is the direct pre-PA state.
- The affiliated MiLB PBP export repeats the post-play `on_1b` state across
  pitch rows. MiLB PA-start occupancy is therefore reconstructed from the
  preceding PA's post-play state within the same half-inning; the first PA in
  a half-inning starts empty.

The adapter requires an explicit capability declaration. Tests prove that a
current post-play state cannot erase an opportunity that existed when the PA
began and that ambiguity in the preceding post-play state fails closed.

## Reconciliation and exclusions

Every eligible player-game has exact PBP-to-canonical PA agreement and
`official GIDP <= reconstructed opportunity`. The retained exclusions are:

- 25,550 player-games with PBP/canonical PA or identity disagreement;
- 437 canonical player-games without a matching PBP batter identity;
- 29 MiLB player-games whose official GIDP exceeds the reconstructed
  opportunity count;
- one player-game affected by an ambiguous cross-asset state.

No exclusion is imputed as zero. The machine-readable result is
`docs/hitter-v2-stage2-gidp-opportunity-result.json`. The ignored generated
report is `reports/generated/hitter-v2-stage2-gidp-opportunities/report.json`,
SHA-256
`c3714fa2718b74d3d86c0cb2e2cf8969dbd1f7341d09171abad39acb6c06f4f5`.
The canonical Parquet artifact SHA-256 is
`d45b73a4e7b41ddd5c3def41c65f5953754abc895d7108f5288cbb9dc0f4bf8a`.

## Validation and gate state

- Ruff passed across `src`, `scripts`, and `tests`.
- All 847 tests passed in 9.48 seconds.

GIDP-opportunity enrichment is complete. C1 remains unfit and unscored because
chronology-safe park context is still open. Tracking, protected 2026 outcomes,
Stage 3+, playing time, and WAR remain closed.
