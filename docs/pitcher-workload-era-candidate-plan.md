# Pitcher workload era candidate plan

Status: frozen before candidate scoring.

## Question

Can simple debut-cohort recency weighting improve six-year pitcher workload
distributions as pitcher usage changes over time?

## Forward folds

Evaluate debut years 2017, 2018, and 2019. Each fold may use only earlier debut
cohorts beginning in 2015. Career outcomes remain normalized for the shortened 2020
season by the already frozen `162/60` rule.

## Candidate grid

Cross four fixed cohort weighting rules with two role-pooling rules:

- equal weight on all earlier cohorts (incumbent);
- exponential recency weight with a one-year half-life;
- exponential recency weight with a two-year half-life;
- equal weight on only the latest two available debut cohorts;
- current role cell when it contains at least 30 earlier players, else pooled tier;
- always pooled within player type and outcome tier.

There are eight candidates. No other half-life, window, role threshold, tier boundary,
or transform may be tried in this run.

## Score and decision

Use weighted empirical CRPS, a proper distribution score, on identical player folds.
Also report P10-P90 coverage, P25-P75 coverage, median error, and results by career
tier. A challenger is research-preferred only if it lowers pooled CRPS and established-
pitcher CRPS versus the equal-weight/current-role incumbent, and does not worsen CRPS
by more than 1% in any tier with at least 30 evaluated players.

This is retrospective model development, not untouched confirmation. Even a winner
cannot replace the playable pitcher range until a later complete six-year cohort or
another predeclared external validation supports it.

No current player, name, value, contract, outside FV, or 2026 outcome is used.
