# Prospect StatsAPI position-code correction plan

Status: frozen before re-running arrival, conditional-hurdle, or current-value results.

## Defect

The certified affiliated season-stat source stores hitter positions as StatsAPI numeric codes. The prospect feature adapter expected abbreviations. Thus `2` (catcher), `6` (shortstop), and the other numeric codes fell into `OTHER` during historical and current prospect probability modeling.

This is a source-contract defect, not a new feature search. The existing conditional WAR path independently uses position abbreviations, so its positional WAR adjustment was not removed. The defect specifically erased hitter role information from probability models.

## Fixed mapping

- `2` catcher;
- `3`/`5` corner infield;
- `4`/`6` middle infield;
- `7`/`8`/`9` outfield;
- `10` DH/other.

Abbreviations remain accepted for compatibility. Pitcher role logic is unchanged.
When a hitter has multiple position rows, primary position is the position with the
most summed games. Official numeric code is the deterministic tie-break. This avoids
the prior unordered `mode().first()` result and does not express a position preference.

## Required rerun

1. Unit-test every supported numeric code.
2. Re-run the nested arrival robustness audit on the identical grid and chronology.
3. Re-run the conditional career-hurdle audit without changing its candidate grid.
4. Rebuild current nested probabilities and the private value sensitivity.
5. Compare old and corrected values, role distributions, proper scores, calibration, threshold counts, and named examples.

Do not preserve a prior result merely because the correction changes it. Do not add catcher bonuses, quotas, outside FV, or post-result tuning.
