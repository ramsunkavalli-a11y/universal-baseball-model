# Prospect probabilistic-position value sensitivity plan

Status: frozen before first value comparison.

## Question

How much does private prospect WAR and FV change when future position is treated as
a probability distribution instead of permanent current position?

## Method

Use the already selected minor-to-MLB transition matrix. Estimate each destination
group's positional runs per 600 from 2021 and 2022 origin cohorts only, weighted by
their actual MLB games by exact position in the following two years. This preserves
the frozen FanGraphs positional-run schedule while allowing real position mixtures.

For each current pre-MLB hitter:

1. retain batting, baserunning, defense, replacement, aging, career-hurdle
   probabilities, and tier workload unchanged;
2. subtract the current fixed positional runs from each conditional WAR rate;
3. add the transition-weighted positional runs using the frozen runs-per-win value;
4. multiply the mean adjusted WAR rate by the existing nested expected workload.

## Checks

Require all transition rows to sum to one, all players to retain six annual rate rows,
and exact identity when a one-hot transition points to the current position schedule.
Report WAR/FV changes overall and by origin group, threshold-count changes, the top
20 movers, and Josuar Gonzalez. This is a sensitivity, not a fitted value target.

## Boundaries

No outside FV, team depth, organization, current outcome, subjective catcher penalty,
or new skill input is allowed. Do not replace the playable default until the movement
is understood and the arithmetic tests pass.
