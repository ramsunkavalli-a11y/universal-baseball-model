# Historical 2025 control and value join

Status: Phase 1 retrospective replay, not a publishable ranking.

The March 27, 2025 projection paths now join to historical owner, service, contract
and cost evidence for 2025–2029.

## Result

- The whole-player projection universe contains 8,946 players and 44,730 annual
  rows.
- A defensible owner is available for 7,998 players. FanGraphs Opening Day supplies
  2,019 owners; official transactions resolve 165; official 40-man evidence resolves
  34; and 5,780 use a unique October 2024 official full-roster owner.
- The remaining 948 players, or 4,740 annual rows, stay outside economics because no
  owner is proven. They remain in the talent universe.
- FanGraphs supplies 1,610 opening service balances. Official MLB debut facts prove
  a zero pre-cutoff balance for 6,355 more players. Thirty-three owned players still
  lack a safe opening balance.
- The join produces 39,990 annual economics inputs. Of these, 39,648 value and 342
  remain review: 165 missing-service rows, 118 unresolved options, 52 uncertain 2025
  Super Two rows and seven unclear numeric contract rows.
- There are 1,308 accepted guaranteed-salary rows. Arbitration years use the existing
  prior-WAR share method; explicit free-agent years end incumbent control.
- There are 7,803 fully calculated player paths and 195 paths with at least one review.

The $15.19 billion aggregate discounted point estimate is a research sensitivity,
not a ranking result. It uses FanGraphs' later-reported 2025 overall market rate,
3% annual market growth, a 10% nominal discount rate and a clearly labeled post-2026
CBA planning scenario.

## Boundaries

Opening Day FanGraphs ownership overrides older evidence. Otherwise, the resolver
uses dated 40-man evidence, conclusive official transactions after the October 2024
snapshot and then a unique official full-roster owner. Multi-team and missing-owner
cases fail closed.

The source files were retrieved later, so this is event-cutoff reconstruction rather
than a true vintage-information replay. Ninety-seven Cot's source identities, covering
485 annual cells, did not pass the contract identity gate and are not applied. Exact
options and those identity exceptions are bounded follow-up work, not reasons to block
the large replay path.

Reproduce with:

```text
python scripts/materialize_historical_control_value_2025.py
```

Generated private outputs live under
`reports/generated/historical-control-value/2025-03-27/`.
