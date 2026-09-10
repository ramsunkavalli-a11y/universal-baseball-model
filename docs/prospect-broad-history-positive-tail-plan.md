# Prospect broad-history positive-tail plan

**Status:** frozen before scoring

## Question

Can basic evidence available throughout the 2008–2023 StatsAPI history distinguish
which pre-MLB players who reach MLB will produce at least `0.25` component WAR over
their next two seasons? This tests the valuable tail conditional on arrival. It does
not change the existing arrival model.

## Fixed data and chronology

- Use dated end-of-season pre-MLB snapshots and affiliated workload history.
- Fit once on snapshot origins 2008–2012, whose outcomes end by 2014.
- Apply the unchanged fit separately to 2013–2017 origins, whose outcomes end before
  the shortened 2020 season, and to the existing 2021–2023 origins.
- Use the certified 2009–2025 MLB component outcome tables for the target.
- Keep negative MLB component WAR and every arrived player. Non-arrivals are outside
  this conditional question and cannot enter its probability score.
- Weight each training row by the inverse of that player's number of training
  snapshots so a long minor-league stay does not count as several independent people.

The old and modern eras must be reported separately. A cross-era difference is
evidence about transport, not permission to pick the friendlier era.

## Fixed candidate

The baseline is the weighted 2008–2012 positive-tail rate. The one candidate is a
strongly regularized logistic model with fixed `C=0.1` using only:

- age;
- current affiliated PA or BF;
- prior affiliated PA or BF and number of prior seasons;
- broad level; and
- catcher/middle-infield/outfield/corner role for hitters or
  starter/swingman/reliever role for pitchers.

Continuous fields are log-transformed where appropriate and standardized on training
rows only. Categories are fixed before fitting. There are no interactions, searches,
class weights, outcome clipping, organization effects, publication FV, rankings,
birth-country effects, height/weight, or current-team depth.

## Fixed evaluation

For every player type and origin, report log loss, Brier error, calibration, paired
player bootstrap differences, sample size and positive count. Also report pooled old
and modern eras using player-clustered uncertainty so repeat snapshots do not create
false precision.

This is supportive development evidence only if both proper scores improve in at
least four of five old origins and two of three modern origins, both pooled-era paired
intervals are favorable for both scores, and no supported level/age/role group has a
material reversal. Even a pass cannot alter production until the complete conditional
WAR path and fresh confirmation are tested. A failure closes further tuning of this
basic feature family.
