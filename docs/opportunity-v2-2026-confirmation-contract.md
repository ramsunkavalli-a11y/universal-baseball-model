# Opportunity v2 protected 2026 confirmation contract

**Frozen before reading 2026 targets:** 2026-09-09  
**Status:** forecast freeze authorized; evaluation waits for the completed season

## Forecast being confirmed

The confirmation forecast uses only the official 2025-10-15 hitter and pitcher
snapshots, completed 2025 MLB/minor-league PA or BF, and exact-date 2025 40-man
membership. The frozen one-year hitter and pitcher v2 packages produce the selected
forecast. The matching U0/P0 level baseline and incumbent historical cohort forecast
are also fit and frozen now from the same pre-2026 evidence.

The forecast artifact must contain player ID, participation probability, conditional
positive PA/BF mean, expected PA/BF, model ID, dispersion and input hashes. It must not
read, join, summarize or hash any 2026 outcome file.

## Target

After the 2026 regular season is complete and official totals are final, retrieve full
regular-season MLB hitting PA and pitching BF from StatsAPI. Join by MLBAM player ID and
fill absence with zero for every player in the frozen forecast universe. Do not add
players who were absent from the 2025 snapshot.

## Fixed component decision rule

Evaluate hitters and pitchers separately on identical rows. The selected model is
confirmed only if it:

1. has lower full-distribution negative log likelihood than U0/P0;
2. has participation log loss no worse than U0/P0;
3. has opportunity MAE no more than 2% worse than U0/P0;
4. has participation Brier error no worse than the incumbent historical cohort;
5. has opportunity MAE no worse than the incumbent; and
6. has absolute league-mean opportunity error no worse than the incumbent.

There is no rescue tuning, player exclusion, cap or subgroup override after targets are
read. Subgroups may diagnose a result but cannot change it. A failed component retains
its prior production baseline. A passing component may be called confirmed only for
the one-year opportunity task; multi-horizon packages remain development evidence.

## Timing and boundary

Do not run the target join on partial 2026 totals. Run it only after the scheduled MLB
regular season is complete and official totals have stabilized. Postseason statistics
are excluded. Team depth, future team and names are forbidden.

