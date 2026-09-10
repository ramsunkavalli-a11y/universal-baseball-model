# Prospect broad-history skill-tail plan

**Status:** frozen before scoring

## Question

Do simple, regressed affiliated performance rates add stable information about a
pre-MLB player's chance of producing at least `0.25` component WAR in the next two
seasons, conditional on reaching MLB?

## Chronology and population

- Fit once on 2008–2010 snapshots and two-year outcomes. All training outcomes end in
  2012, before the first evaluation snapshot.
- Apply both frozen models unchanged to 2013–2017 and 2021–2023.
- Use the same pre-MLB, age 16–30, observed-arrival cohorts and component-WAR target as
  the corrected basic-tail test. Keep negative WAR.
- Give every training player equal total weight across repeat snapshots.
- Evaluate old and modern eras separately; do not select an era.

## Fixed models

The incumbent is the corrected basic model: age, current and prior affiliated
workload, prior seasons, broad level and broad role, with logistic `C=0.1`.

The only candidate adds four current-season component rates:

- hitters: unintentional walks, strikeouts, home runs and extra-base hits per PA;
- pitchers: strikeouts, unintentional walks, hit batters and home runs per BF.

Each rate is regressed toward its player-type 2008–2010 training mean with `200`
opportunities: `(events + 200 × training mean) / (opportunities + 200)`. The means,
scaler and model are fitted on training only and then frozen. The candidate also uses
logistic `C=0.1`. There are no interactions, searches, class weights, clipping, level
translations, demographics, organization, rankings, outside FV, or depth inputs.

## Fixed evaluation and decision

Report log loss, Brier error, calibration and paired player bootstrap differences for
every type/origin. Pool each era with player-clustered uncertainty. Review age, level
and role groups only when they contain at least 100 rows, 20 positives and 20
negatives.

The skill candidate is supportive only if it improves both scores against the basic
incumbent in at least four of five old origins and two of three modern origins; both
pooled paired intervals favor it in both eras; no supported group reverses on both
scores; and its pooled scores also beat the constant training-rate baseline in both
eras. A pass remains research-only pending a complete conditional-WAR path and fresh
confirmation. A failure closes this aggregate component-rate form on these disclosed
years.
