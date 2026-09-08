# Rights transaction ledger contract v0.1

**Status:** Implemented source projection; rights-state transitions not yet authorized

## Purpose

Official transactions are the leading reconciliation source for candidates that appear
under multiple organizations in broad roster histories. The ledger preserves event
identity, player, transaction/effective/resolution dates, type, from/to teams,
description and source snapshot without immediately asserting current ownership.

## Hard rules

- Transaction and player IDs must be positive and transaction IDs unique.
- Transaction, effective and resolution dates cannot cross the requested cutoff.
- Missing structured identities, dates or type codes fail closed.
- Missing from/to teams remain null; descriptions are evidence, not parsing authority.
- The ledger emits no `rights_state` field.

The last rule is substantive. The official type catalog includes assignment, option,
status-change, suspension and other events that do not transfer organization rights,
alongside signing, trade, claim, release and free-agency events. Team IDs can also name
minor-league affiliates and need dated parent-organization resolution.

## Next gate

Define and test a small state-transition table only for ownership-changing codes. Map
minor-league teams to their dated parent organizations, replay events in effective-date
order, and compare the resulting owner against conflict-free 40-man snapshots. Unknown
or conflicting paths must remain unknown; description-text heuristics cannot silently
become production authority.

Implementation: `src/universal_baseball/rights_transactions.py`
