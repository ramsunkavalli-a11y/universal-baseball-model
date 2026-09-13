# Prospect position-history confirmation contract

**Frozen:** 2026-09-13, before scoring the 2020 prospect snapshot  
**Confirmation target:** 2020 snapshot, complete 2021–2024 MLB outcomes

## Question

Does official minor-league position history improve expected prospect value once MLB
arrival risk and conditional position value are kept separate?

## Fixed candidate

1. Use the player's most-used official 2020 MiLB position, with defensive outs as
   exposure and one DH start equal to 27 defensive outs.
2. Estimate conditional four-year MLB positional WAR from chronology-safe 2008 and
   2013 reference cohorts at the same minor-league level and position.
3. Shrink each level/position mean by 25 arrived players toward that level's arrived-
   player mean.
4. Multiply conditional position WAR by the existing historical-comparable MLB
   arrival probability.
5. Add this expected position value to the unchanged batting-plus-replacement
   prediction. The baseline uses the same arrival and batting predictions but only
   the level-wide conditional position mean.

The positional schedule, runs-per-win source, four-year horizon, 2020 scaling and all
comparable settings remain unchanged.

## Decision rule

The product target is mean expected WAR/value, so paired squared error is the primary
point-forecast score under `docs/expected-war-validation-law.md`. MAE is reported but
cannot veto a mean forecast because it targets the conditional median and rewards
zero in this mostly-zero population.

Promote only if, on the untouched 2020 cohort:

- official origin-position coverage is at least 95%;
- the position candidate has lower mean squared error than the level-only baseline;
- position-adjusted partial WAR has lower mean squared error than its baseline; and
- absolute aggregate bias does not worsen for either comparison.

Otherwise withhold the component. Public FV, public rank, player names, current-player
results and 2026 outcomes are forbidden.
