# Secondary contract-option audit — 2026-09-09

**Decision:** use Spotrac only as a small, dated exception source. FanGraphs remains
the primary contract/control input. This audit does not redistribute Spotrac's bulk
table and does not assume a displayed dash means a zero-dollar buyout.

## Promoted facts

The public MLB option pages for 2027–2032 and individual contract-detail pages supplied
14 explicit, non-conflicting dollar facts: 13 buyouts and one missing option salary.
They resolve 13 annual economics review rows and reduce the review set from 71 to 58.
Each promoted fact has
an MLBAM player ID, organization, season, expected FanGraphs control status, page URL
and snapshot ID in `config/secondary-contract-terms-2026-09-09.json`.

The join fails closed when the secondary status conflicts with FanGraphs, when a
secondary dollar value conflicts with an existing primary value, or when provenance
is missing. Secondary data can only fill a null field.

## Findings kept in review

The browser review exposed structural differences that are more important than the
remaining easy blanks:

- Nick Pivetta is a FanGraphs club option but a Spotrac opt-out.
- Tatsuya Imai is a FanGraphs player option in 2027 but a Spotrac opt-out; Spotrac
  presents a player option in 2028.
- Kyle Tucker is a FanGraphs player option but Spotrac presents opt-outs in 2028–2029.
- Julio Rodriguez's 2030–2032 option structure is grouped differently by the sources.
- Kyle Freeland's 2027 vesting option is shown as voided by Spotrac.
- Isaac Paredes, Kodai Senga, Blake Snell, Edwin Diaz, Tanner Scott, Garrett Crochet,
  Yuki Matsui and Yariel Rodriguez have conditional terms that a simple option label
  does not fully describe.
- Tatsuya Imai and Ketel Marte have displayed option-dollar differences between sources.

These are not overrides. They remain an explicit reconciliation queue until the
underlying contract language or another reliable contract-detail source resolves the
structure. Vesting options also remain unavailable until their exact trigger and
current trigger state can be represented.

## Next boundary

Resolve exact contract structure before adding more pricing logic. Use an individual
contract detail or primary announcement when possible. Keep unresolved terms in
review; do not turn missing information into zero, free agency or a standard option.
