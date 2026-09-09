# Current contract economics scenario — 2026-09-09

**Status:** complete Phase 1 research calculation; not a publishable ranking

The first full 2027–2032 economics pass now runs all 50,100 controlled player-years
through the same WAR, market, salary, option and discount rules. It produces 50,029
available annual rows and 71 review rows. At the six-year player aggregate, 8,290
players are complete and 60 have at least one review year.

The 71 reviews are narrow and visible:

- 36 club options missing a stated buyout;
- 17 player options missing a stated buyout;
- 13 vesting options needing trigger logic; and
- three mutual options missing a stated buyout;
- one mutual option missing its exercise salary; and
- one club option missing its exercise salary.

## Named assumptions

- FanGraphs' 2026 market tiers are $6.74M, $8.51M and $12.84M per WAR for
  under-1, 1–2 and 2+ full-season projected WAR.
- Market prices grow 3% annually.
- Arbitration uses 15%/35%/50%/75% of prior-season free-agent WAR value for classes
  1–4, with known salaries taking priority.
- A fully specified mutual option uses the normal expiration outcome and charges its
  stated buyout. This conservative Phase 1 rule does not invent a negotiated extension.
- Nominal value and cost are discounted 10% annually. Because the market scenario
  grows 3%, this is roughly a 7% net rate before interaction.
- The unsigned post-2026 CBA is represented only by a planning scenario: the 2026
  $780,000 minimum grows 3% annually and the current service rules remain unchanged.

The final item is not an official CBA interpretation. Its ruleset ID and kind state
that it is a research scenario. A signed successor agreement must replace it with a
new official ruleset; historical rules cannot be silently edited.

## Interpretation

This result proves the full calculation path works and isolates the remaining contract
exceptions. It does not promote the current top-player order. The WAR surface still
uses Phase 1 population fallbacks, future market/minimum growth is assumed, and option
decisions do not yet use correlated career paths.

Run `scripts/materialize_contract_economics_scenario.py --as-of-date 2026-09-08`
after rebuilding the current contract-economics inputs.
