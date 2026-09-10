# Contract review visibility — 2026-09-10

**Status:** implemented for the private explorer; rankings remain fail-closed

The contract engine now keeps two results separate for every player:

- the complete contract value, which remains null and unranked if any annual right is
  unresolved; and
- a subtotal from annual rows the engine can calculate without using the unresolved
  right.

The subtotal is display context, not a lower bound and not a replacement value. An
unresolved option can add value or cost. The explorer labels the subtotal **Known
contract years only**, shows the number of calculated and unresolved years, and prints
each unresolved reason.

## Current result

The 2026-09-08 private preview still has 8,393 players, 8,370 usable values and 23
reviews. Eleven reviews are the known contract-option group: 16 annual rows consisting
of 12 future vesting decisions, three linked Julio Rodriguez years and Gary Sanchez's
2027 mutual option. The other 12 reviewed players have no joined economics path, so no
subtotal is invented for them. Those rows are now labeled separately as missing an
opening MLB service balance; they are not described as contract-option problems. The
[materiality audit](unresolved-service-review-materiality-2026-09-10.md) confirms all
twelve are off the 40-man roster and currently low-value.

All eleven option-review players now expose their calculable-year subtotal. Their full
value remains blank and they receive no rank. This preserves the existing fail-closed
rule while making the private result understandable.

## Gary Sanchez source check

No public dollar term was found for the 2027 mutual option. The Brewers' official
February 14, 2026 announcement states only that the one-year contract includes a 2027
mutual option. FanGraphs RosterResource reports the option salary as `TBD`, and
Spotrac's contract page does not provide an exercise price. The engine therefore keeps
the row in review instead of guessing.

Sources:

- https://www.mlb.com/brewers/press-release/press-release-brewers-sign-catcher-gary-sanchez
- https://www.fangraphs.com/roster-resource/payroll/brewers
- https://www.spotrac.com/mlb/player/_/id/16110/gary-s%C3%A1nchez/contract/

## Verification

- targeted contract/explorer tests: 24 passed;
- private-preview model laws: 46 passed; and
- full suite: 1,531 passed, with the same four older missing generated-artifact
  failures (S0 age input, S0 predictions, G0 predictions and stage2f H0 report).
