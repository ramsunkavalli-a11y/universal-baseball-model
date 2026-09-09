# Current contract-economics inputs — 2026-09-08

Status: **Phase 1 annual inputs built; dollar rankings are not publishable**

The future hitter and pitcher paths now feed the team-control and payroll layer at a
common player-season grain. Hitting and pitching expected WAR are added, so a two-way
player keeps both sources of value. No market or salary assumption is hidden in this
step.

## Materialized result

- 55,164 whole-player projection rows for 2027–2032;
- 50,100 control rows and 50,100 matched economics-input rows;
- zero control rows without a projection;
- 5,064 projection rows without resolved control, retained in the projection source
  and excluded from incumbent-rights economics;
- 604 player-year salaries attached from accepted payroll terms;
- 86 potential buyouts linked to stable player IDs from the same payroll source;
- 83 of 151 projected option rows now carry a buyout, leaving 68 unresolved; and
- zero duplicate player/organization/season keys.

The output contains 8,350 players in each of six seasons. All 50,100 rows now carry
the Phase 1 moment-based WAR lower and upper sensitivities in addition to the unchanged
mean. These are not calibrated probabilities or correlated career paths. Free agents
remain in the table with zero incumbent rights downstream, rather than disappearing
from the talent universe.

Buyout descriptions are linked by exact team and player name within the same FanGraphs
workbook identity table; no fuzzy or cross-source name match is used. Non-contingent
buyouts already owed to former players are not attached to transferable option rights.
The ten projected 2027 Super Two cases now advance through arbitration classes 1–4
instead of being reset to class 1 when they cross three service years.

## Honest boundary

This table is ready to feed the existing contract-economics engine. It is not yet a
defensible dollar ranking. The remaining large inputs are:

1. historical arbitration salary shares and salary-lag behavior;
2. the post-2026 CBA minimum-salary rules;
3. the remaining 68 buyouts and unresolved option triggers; and
4. Phase 2 empirical coverage calibration and correlated career paths for option
   decisions.

The 2026 FanGraphs tiered market reference is now implemented separately. Its future
growth remains a named scenario and does not resolve the missing CBA cost rules.

Until those exist, the engine may be tested only with clearly named scenarios. A
scenario must not be presented as the model's estimate.

## Reproduction

Run `scripts/materialize_contract_economics_inputs.py --as-of-date 2026-09-08` after
the dated WAR and league-control builds. It writes a canonical Parquet table and a
coverage report under `reports/generated/current-contract-economics-inputs/2026-09-08`.
