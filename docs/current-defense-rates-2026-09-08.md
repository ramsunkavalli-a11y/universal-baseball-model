# Current general-defense rates

**Status:** frozen v1 method connected for the adjacent year
**As of:** 2026-09-08

The current build now reuses the defense work that had already passed development and
confirmation. It does not fit a new model.

Official StatsAPI fielding data supplied 13,192 player-team-position rows across all
16 MLB and affiliated leagues. The frozen U1 general-range model uses fielding
percentage, range factor, errors and throwing errors. The frozen exposure method uses
2026 MLB defensive outs at each position, and the frozen native conversion turns each
position-relative skill estimate into runs.

For 2027, 1,519 of 3,940 hitters have eligible general-defense evidence. The remaining
2,421 hitters receive the explicit neutral fallback. Individual conditional defensive
results range from -3.95 to +3.32 runs. Position-level expected-exposure
centering makes the league-wide expected result zero without clipping player values.

The model is only validated for the next season, so 2028–2032 remain neutral instead
of receiving an invented defense-aging curve. Current tracked range is not yet present,
so the T1 upgrade is not used. Catcher throwing, blocking and framing also remain
neutral because their required native opportunity inputs were not rebuilt. These are
clear Phase 1/2 improvements, not reasons to discard the supported general-range work.

The updated defense rates now flow through hitter WAR, whole-player WAR, contract
inputs and the 2026 rest-of-season proxy. Current-team depth is never used.
