# Minor-league runner to hitter-value bridge result

Date: 2026-09-22
Status: **keep as component evidence; do not change projected WAR**

## Question

The RE24 runner model can identify minor-league players whose advancement is likely
to remain better or worse than average. Does adding that history to the existing MLB
baserunning forecast improve next-season total hitter value?

## Test

For each 2022-25 target season, the model projected a player's minor-league runner
effect using only earlier seasons. It converted that rate to WAR using projected
plate appearances and the observed MLB frequency of advancement opportunities. The
test considered conservative blends with the existing MLB advancement forecast and
a fallback that changes only players without recent MLB advancement evidence.

Both the runner-effect regression and the bridge choice were selected using only
older folds. The comparison includes all 17,552 hitter rows, including players with
zero later MLB value. No 2026 result was used.

## Result

- Minor-league runner projection coverage: 15,272 of 17,552 rows
- Advancement-component RMSE: 0.042316 to **0.042252**
- Component RMSE change: **-0.000064**
- Player-clustered 95% interval: **-0.000122 to -0.000017**
- Whole hitter-value RMSE: 0.429098 to **0.429129**
- Whole-value RMSE change: **+0.000031**
- Player-clustered 95% interval: **-0.000008 to +0.000070**

After the first fold, every chronology-safe selection chose the full minor-league
fallback for players without current MLB advancement evidence. That improved the
specific advancement forecast, but the full hitter forecast was effectively flat and
slightly worse in each of the three seasons where the bridge was active.

## Decision

Keep the minor-league RE24 runner estimate as a useful player diagnostic and as the
best available advancement estimate when no MLB evidence exists. Do not let it alter
the official projected WAR yet. The signal is real, but baserunning is small relative
to the uncertainty in MLB arrival, playing time, and batting value, so a statistically
clear component gain did not produce a full-player gain.

This closes the current baserunning integration step. Revisit it only when the final
reconciliation model can combine correlated component uncertainty rather than simply
adding point estimates.
