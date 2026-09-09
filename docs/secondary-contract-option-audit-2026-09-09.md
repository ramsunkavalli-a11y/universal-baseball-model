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

Five source disagreements are stored in
`config/secondary-contract-structure-reviews-2026-09-09.json` and joined to the annual
economics input. The calculator refuses to value those rows even if a later refresh
fills the missing dollar fields. This keeps the audit boundary in code, not only in
this document.

## Findings kept in review

The browser review exposed structural differences that are more important than the
remaining easy blanks:

- Kyle Tucker is a FanGraphs player option but Spotrac presents opt-outs in 2028–2029.
  Both rows are blocked.
- Julio Rodriguez's 2030–2032 option structure is a linked club-option/fallback-player-
  option decision, not three independent player options. All three rows are blocked.
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

## Reconciled differences

- A current official MLB report confirms that Nick Pivetta's 2027 player option
  converted to a club option after 131 consecutive IL days. The FanGraphs state is
  current; the older Spotrac structure is stale and is not a conflict.
- Official MLB reporting confirms Tatsuya Imai may opt out after both 2026 and 2027.
  A narrow official-source overlay corrects the 2027 and 2028 states to
  `player_opt_out`. It does not supply or assume a buyout.
