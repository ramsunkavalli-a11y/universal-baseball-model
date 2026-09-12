# Current Talent 2025 era extension

Last updated: 2026-09-12  
Status: **TOPOLOGY PASSED; FULL-SEASON SOURCE GATE FAILED.**

The 2025 affiliated topology matches the existing post-reorganization Current Talent
contract, but 2025 cannot yet be enabled as a complete evidence season.

- Official MLB Stats API team records reproduce all 14 expected league IDs across
  Triple-A, Double-A, High-A, Single-A and rookie/complex ball.
- Each level has some reusable 2025 player-game and PBP data, but the PBP release is
  incomplete. Triple-A ends at filename period 5 versus period 9 in the complete 2024
  comparison; the other levels show the same early cutoff.
- The source check did not fit a model, calculate talent, or access future outcomes.

The allowed Current Talent evidence era remains 2021–2024. Do not treat the partial
2025 PBP release as a full-season talent input. A later refresh may extend the era only
after the bulk-source span and the existing player-game, outcome, contact, identity and
league-coverage checks all pass.

Reproduce with `scripts/audit_current_talent_2025_era_extension.py`. Machine-readable
detail is in `docs/current-talent-2025-era-extension-result.json`.
