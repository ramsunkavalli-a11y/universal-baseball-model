# Current contract economics scenario — 2026-09-09

**Status:** complete Phase 1 research calculation; not a publishable ranking

The first full 2027–2032 economics pass now runs all 50,226 controlled player-years
through the same WAR, market, salary, option and discount rules. The exact-input pass
produces 50,167 available annual rows and 59 review rows. A named Phase 1 buyout
estimate then calculates buyout-only exceptions, producing 50,210 scenario rows and
16 review rows. At the six-year player aggregate, 8,360 players are complete and 11
have at least one review year.

The 16 remaining reviews are narrow and visible:

- 12 unresolved vesting options;
- three linked Julio Rodriguez option years;
- one mutual option missing its exercise salary.

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
- When no buyout is reported, Phase 1 uses the observed median buyout share for that
  option type: 13.0% for club, 18.75% for mutual and 11.9% for player options. The
  13.3% overall median is the player-opt-out fallback because that subgroup has no
  exact observations. All 43 uses are labeled estimates, not contract facts.
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

A dated, small Spotrac exception overlay supplies 14 explicit, non-conflicting
dollar facts that resolve 13 review rows. It never treats a displayed dash as a
zero and never overrides FanGraphs. Structural disagreements remain review items and
are recorded in [the secondary option audit](secondary-contract-option-audit-2026-09-09.md).
Three linked Julio Rodriguez years are machine-enforced: later term additions cannot
silently turn them into calculated rows until the structure is reconciled.
Two Tatsuya Imai seasons are corrected from player option to player opt-out using
official MLB reporting. The correction checks the prior status before applying.
Yandy Diaz's official 2026 total of 620 PA resolves his 500-PA vesting trigger. His
2027 row is therefore a guaranteed $13M season, not an unresolved vesting option.
MLB's official Tucker contract report also resolves two apparent source conflicts:
his 2028 and 2029 rights are player opt-outs, not player options.

Run `scripts/materialize_contract_economics_scenario.py --as-of-date 2026-09-08`
after rebuilding the current contract-economics inputs.
