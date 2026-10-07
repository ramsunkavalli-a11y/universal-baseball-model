# Count support for later MLB arm and receiving quality

Before scoring a predictor, count what the completed historical records can
actually test. The target is difficulty-adjusted later MLB runs per 100 real
opportunities, pooled over the next three calendar seasons through 2025. It is
not next-year defense, total WAR, service years or minor-league talent validation.

Use origins 2016–2024 for arms and 2021–2024 for receiving, omitting the shortened
2020 forecast origin but retaining its actual MLB chances in other windows.
Origin eligibility requires a source observation in the preceding three seasons.
For arms require some native outfield exposure in that origin history; keep
mixed-position and invalid observations in eligibility, but only genuinely
outfield-only, reconciled records provide isolated arm-quality inputs or labels.
For receiving retain every origin-known record, including limited exposures.
Historical observations use fixed recency weights 1, 0.5 and 0.25. Unmeasured
histories remain visible; origin eligibility never depends on later success.

A measured target requires a complete three-calendar-year window, observations
in at least two later seasons and at least 600 advancement opportunities for
arms or 1,000 received throws. These are reliability restrictions roughly
requiring multiple substantial seasons, not optimized thresholds. A positive
later source opportunity with invalid credit or mixed arm scope invalidates the
isolated-quality window. Native nonzero component credit without a source record
is also a coverage gap. Never assign zero skill to an exit or non-arrival. Keep
unknown and incomplete windows in coverage counts rather than delete them.

The primary ordinary origin is 2022, with later 2023–2025 MLB quality. Earlier
complete origins are development/stress evidence, not extra independent players.
For every origin and held-player group `player_id % 5`, training labels must end
by the origin and exclude that group's players. Count distinct people, not just
rows. Show joint age bands at most 24, 25–29, 30 plus and unknown, crossed with
weighted origin samples below 50, 50–299 and 300 plus arm chances, or below 100,
100–499 and 500 plus received throws. Fewer than 20 profile people is a support
warning, not an automatic reason to omit forecasts.

Walk all eligible fixed source cases at 2022, the two smallest histories per
component and three age/exposure/ID peers each, including unknown future quality.
Trace dated raw source records, weighted inputs, actual later records and gaps.
This audit must precede any separate locked neutral-versus-history scoring
contract. In particular, receiving's 2021 start may supply no mature training
examples at 2022; a learned age curve must not be fitted simply because rows exist.
No 2026 results, frozen forecasts or explorer changes.
