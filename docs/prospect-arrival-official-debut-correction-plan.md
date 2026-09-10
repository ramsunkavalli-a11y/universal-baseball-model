# Prospect arrival official-debut correction plan

**Status:** frozen before production re-fit

## Defect

The reusable historical arrival-cohort builder identifies prior major leaguers only
from MLB rows inside the supplied season-stat window. At the 2018 training origin this
misses players who debuted before 2018, had no 2018 MLB workload, and later returned.
The current cohort contains 91 such hitter rows and 137 pitcher rows; 12 hitters and 28
pitchers are incorrectly labeled as later MLB arrivals. They are not prospects.

## Mandatory correction

- Require an official StatsAPI debut-date table in every historical arrival-cohort
  build.
- Exclude a player when `mlb_debut_date` is on or before the snapshot date/year, in
  addition to the existing observed-MLB-stat exclusion.
- Fail closed on missing debut coverage for any player labeled as a future arrival.
- Keep the official debut date as an eligibility field only. It cannot enter the
  feature matrix.
- Re-fit the existing arrival, meaningful-role, established-role and nested hurdle
  models without changing features, penalties, targets, folds or selection rules.
- Bump the model lineage ID because the fitted population changes.

This correction is required even if a headline score worsens: the contaminated model
answers whether a player will *return* to MLB as well as whether a prospect will first
arrive. Report validation and current-value changes, but do not use them to decide
whether invalid rows remain.

## Verification

Every fitted historical cohort must contain zero official prior debuts. Current
predictors already require a null official debut and must remain unchanged in meaning.
The full model-law audit and explorer build must pass after re-materialization. No
outside FV, ranking, contract, demographic-talent, or 2026 outcome input is authorized
by this correction.
