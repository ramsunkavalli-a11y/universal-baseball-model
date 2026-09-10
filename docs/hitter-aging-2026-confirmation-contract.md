# Hitter aging protected 2026 confirmation contract

**Frozen before reading 2026 targets:** 2026-09-10  
**Status:** Forecast freeze authorized; evaluation waits for final regular-season data

## Forecasts

Use the already frozen October 15, 2025 hitter opportunity and conditional-rate path.
Store two otherwise identical 2026 forecasts:

1. the incumbent standard Marcel hitter age multiplier; and
2. no age adjustment, obtained by exactly inverting that multiplier from the frozen
   event probabilities and recalculating batting runs and expected WAR.

Workload, participation probability, position, defense, baserunning, replacement,
run environment, player denominator and every non-age input stay identical. Do not
refit either forecast. No 2026 outcome, participant, team-depth or outside-FV field may
enter the freeze.

## Confirmation target

After the 2026 regular season is complete and official totals are final, join official
MLB hitter event counts to the frozen player IDs. A missing player receives zero MLB
PA and zero neutral WAR. Players outside the frozen denominator are not added.

## Fixed decision rule

No aging replaces Marcel aging only if all of these are true on identical rows:

1. hitter component log loss is lower;
2. zero-inclusive neutral-WAR MAE is lower and its paired player-bootstrap 95% upper
   bound for no-aging minus Marcel is at or below zero;
3. zero-inclusive neutral-WAR RMSE is no more than 1% worse;
4. absolute aggregate neutral-WAR bias is lower; and
5. no supported age band with at least 100 positive-PA players has WAR MAE more than
   5% worse.

Age bands are diagnostic guardrails, not separate selection opportunities. There is
no rescue tuning, clipping, blended age weight, threshold search or player exclusion
after targets are read. Failure retains Marcel pending a new predeclared candidate.

## Boundary

This test confirms only the uniform hitter age adjustment inside the 2026 one-year
path. It does not confirm the opportunity model, multi-year aging, prospect development,
defense, running, contract value or Model FV.
