# Current and future contract economics

**Status:** Phase 1 research scenario; not a publishable ranking  
**As of:** 2026-09-08

The current remaining-season rights row and the 2027–2032 control path now run through
one economics calculation. This closes the prior accounting break between “what remains
in 2026” and “what the club controls afterward.”

## Coverage

- 51,070 annual rows: 844 current-season and 50,226 future rows.
- 8,373 player/organization paths.
- 8,362 paths calculate completely.
- 11 paths remain in review because of the same 16 known contract rows: 12 future
  vesting decisions, three linked Julio Rodríguez option years, and one missing mutual-
  option salary.

No new contract or projection gap appeared when the current and future paths were
combined.

## Value method

The 2026 remaining-season WAR is priced at FanGraphs' published 2026 overall market
rate of $11.23 million per WAR. A partial-season WAR figure is deliberately not placed
into FanGraphs' full-season player tiers. Future full seasons use the published 2026
three-tier curve, grown 3% annually as a named scenario. Future value and cost are
discounted 10% nominally. Arbitration uses the accepted FanGraphs class shares.

For complete paths, the point scenario contains 4,074.66 remaining and future WAR,
$33.48 billion of free-agent-equivalent production, $16.58 billion of calculated cost,
and $1.66 billion of discounted contract-control value. The latter is not the simple
difference of the preceding totals because option decisions and discounting are applied
at the annual-rights level.

The 2026 component contributes 80.08 WAR and $396.39 million of contract-control value
after $508.08 million of matched remaining salary.

## Uncertainty boundary

Discounted player totals now preserve the annual Phase 1 lower and upper WAR
sensitivities. The league-wide extreme sums are -$7.62 billion to $55.91 billion. These
are deliberately broad sensitivity bounds, not probability-calibrated confidence
intervals; they should not be interpreted as a likely league-total range. Correlated
career simulation and empirical interval coverage remain Phase 2 work.

## Publication boundary

This output is a coherent research surface, not a player ranking. It still uses:

- the labeled historical hitter-opportunity fallback while the confirmed B2 scoring
  package is unavailable;
- a planning assumption for post-2026 CBA rules and minimum salaries;
- named option-buyout estimates; and
- simple Phase 1 WAR sensitivities rather than calibrated career distributions.

The calculation is produced by
`scripts/materialize_current_and_future_contract_economics.py`. Generated Parquet files
remain outside Git; this document records the method and aggregate result.
