# Current fallback coverage result

**Status:** certified for the playable 2026-09-08 build; no production value changed.

Every one of **3,940 hitters** and **5,276 pitchers** has one traceable projection for
each of six seasons. No player-season has a blank opportunity, workload, talent, role,
defense or baserunning source where that source applies.

## Current ladder

1. Opportunity uses the selected universal model in year 1 and the selected direct
   horizon models in years 2–4.
2. Years 5–6 fall back to partially pooled age/level history. Pitchers also include
   role. Missing ages back off one step to level, or level plus role.
3. Conditional skill uses MLB history when present, translated affiliated performance
   otherwise, then a population prior.
4. Hitter running and defense retain separate evidence labels and neutral fallbacks.

## First-year skill coverage

| Component | MLB history | Translated affiliated | Population prior |
|---|---:|---:|---:|
| Hitters | 762 | 3,013 | 165 |
| Pitchers | 998 | 3,887 | 391 |

The population-prior rows are valid wide-uncertainty estimates, not zero talent. This
check should run after every materialization so new models cannot improve their score
by dropping difficult or sparse players.

[Machine-readable result](current-fallback-coverage-result.json)
