# Player-rights universe contract v0.1

**Status:** Implemented foundation; certified 40-man adapter connected; other sources incomplete
**Roadmap step:** Phase 1, Step 1

## Purpose

This table is the mandatory denominator for projections and valuation. It prevents the
historical pattern of excluding incomplete players or appending unexplained zero rows.
Every downstream model must join back to this grain and report its coverage tier.

## Grain and fields

Exactly one row per `as_of_date + player_id`. Each row records player name, rights
state, controlling organization when applicable, roster scope, evidence tier, source
snapshot IDs, last observation date and a coverage reason.

Allowed rights states are:

- `organization_controlled` — requires exactly one controlling organization;
- `free_agent` — has no incumbent rights owner;
- `unknown` — has no asserted rights owner and must receive a prior/range downstream.

The builder begins from a separately supplied required-player denominator. Rights
evidence cannot silently add or remove players. Players without rights evidence remain
as `unknown / prior_only / missing_rights_evidence` records.

Candidate discovery is a separate audited layer. It unions dated sources into one row
per player while retaining all candidate scopes and snapshot IDs, then projects the
required denominator. Candidate presence never asserts an owner. This allows a broad
but ownership-ambiguous source to prevent omission without converting ambiguity into
false organization control.

## Conflict and chronology rules

- Evidence after the requested cutoff is rejected.
- Conflicting rights states or organizations fail closed.
- Multiple sources agreeing on state and owner are retained as corroboration.
- Overlapping roster scopes use a fixed descriptive priority; scope never overrides a
  rights-owner conflict.
- Only organization-controlled rows may name an organization.
- Free-agent state and scope must agree.

## Source boundary and next work

The existing dated official 40-man adapter now supplies one evidence family and maps
only presence, organization control and `mlb_40man` scope. It deliberately ignores
uncertified row-level status and parent-team fields. A 40-man roster alone is not
universal. Reserve-list, injured/inactive, newly signed, transaction
and free-agent sources still require explicit dated adapters and a reconciliation audit.
Until those exist, missing rows remain honest `prior_only` records rather than inferred
free agents or zero-value players.

The official `fullRoster` endpoint was audited and rejected as direct dated rights
evidence: its 2024-10-15 responses contained 16 cross-organization player conflicts.
It may supply candidates only after transaction-based ownership reconciliation; see
`affiliated-full-roster-source-result.md`.

Implementation: `src/universal_baseball/player_rights_universe.py`
Tests: `tests/test_player_rights_universe.py`
