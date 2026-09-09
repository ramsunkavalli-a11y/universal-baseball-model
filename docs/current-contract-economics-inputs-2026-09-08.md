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
- 151 option rows still missing player-linked buyouts; and
- zero duplicate player/organization/season keys.

The output contains 8,350 players in each of six seasons. All 50,100 rows now carry
the Phase 1 moment-based WAR lower and upper sensitivities in addition to the unchanged
mean. These are not calibrated probabilities or correlated career paths. Free agents
remain in the table with zero incumbent rights downstream, rather than disappearing
from the talent universe.

## Honest boundary

This table is ready to feed the existing contract-economics engine. It is not yet a
defensible dollar ranking. The remaining large inputs are:

1. a chronological free-agent dollars-per-WAR fit;
2. historical arbitration salary shares;
3. the post-2026 CBA minimum-salary rules;
4. player-linked option buyouts and unresolved option triggers; and
5. Phase 2 empirical coverage calibration and correlated career paths for option
   decisions.

Until those exist, the engine may be tested only with clearly named scenarios. A
scenario must not be presented as the model's estimate.

## Reproduction

Run `scripts/materialize_contract_economics_inputs.py --as-of-date 2026-09-08` after
the dated WAR and league-control builds. It writes a canonical Parquet table and a
coverage report under `reports/generated/current-contract-economics-inputs/2026-09-08`.
