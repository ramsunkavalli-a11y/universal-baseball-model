# Hitter v2 historical bridge-support audit contract

Date: 2026-08-26

Status: frozen before 2019 MLB source access and bridge computation

## Question

Does the newly certified history create enough connected same-player evidence to
justify a later historical C0 integration experiment, and which parts of the
level/age problem remain unidentified?

This is a support audit, not a predictive test. It cannot promote a candidate.

## Inputs

- accepted/model-ready 2019 MiLB player-season outcomes from the hash-pinned
  historical materialization;
- separately certified 2019 MLB player-game exposure, to be produced under the
  same source contract as 2020 MLB;
- certified 2020 MLB player-game exposure;
- frozen 2021 universal Hitter v2 player-season outcomes, filtered to
  `modeling_eligible == true`.

Identity is the integer MLB player ID already retained in every source. Player
names are not used. A player-season may contain multiple level groups; retain
each level stint and also compute a player-season total PA.

## Level ordering

For descriptive transition labels only:

`ROOKIE_COMPLEX < SINGLE_A < HIGH_A < AA < AAA < MLB`

Within-player transitions are classified as promotion, same level, demotion,
or multi-stint/ambiguous. This ordering is not a fitted translation value.

## Frozen comparisons

1. `2019 -> 2020`: adjacent calendar seasons, but destination support is MLB
   only because no affiliated 2020 MiLB season existed.
2. `2020 -> 2021`: adjacent calendar seasons, origin support is MLB only.
3. `2019 -> 2021`: two-year reappearance across the missing MiLB season. It is
   reported separately and may never be supplied to an adjacent-season fitter.

For each comparison report:

- origin players, destination players, matched players, and origin-player
  match rate;
- matched origin and destination PA;
- matched-player counts by origin and destination level group;
- transition matrix and promotion/same/demotion/ambiguous counts;
- evidence-band counts using total origin PA: `<100`, `100-299`, `300-599`,
  and `600+`;
- separate counts for 2019 MiLB players reaching 2020 or 2021 MLB; and
- players with evidence in all three seasons.

## Interpretation rules

- Presence proves support, not predictive usefulness.
- 2020 MLB's shortened schedule is represented by observed PA; no arbitrary
  season multiplier is applied in this audit.
- Missing 2020 MiLB is an observation gap, never a neutral season or a zero.
- The audit may recommend more source history when transition cells remain
  sparse, but cannot choose model coefficients or tune to disclosed outcomes.
- 2019 MLB must reconcile exactly to official outcome totals before it can enter
  the support table. A physical-contact residual may remain diagnostic under the
  already-certified MLB contract.

## Exact stop

After reporting support and limitations, stop for review. Any historical model
integration requires a new preregistration defining predictor construction,
gap handling, folds, baselines, metrics, and promotion tolerances before a fit
or score.
