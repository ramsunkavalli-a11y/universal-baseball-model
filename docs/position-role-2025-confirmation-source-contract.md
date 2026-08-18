# Position / Role v1 — 2025 confirmation source materialization contract

Last updated: 2026-08-18

Status: **AUTHORIZED SOURCE-ONLY OPEN — SCORING STILL PROHIBITED.**

Upstream authorization:

- `docs/position-role-2025-confirmation-contract.md`
- `docs/position-role-confirmation-parameters.json`

The frozen pre-2025 parameter record authorizes opening the 2025 position source, but not scoring it.

## Purpose

Materialize the untouched completed-2025 batting position/role outcome source as an immutable artifact before any confirmation scorer can read it.

This workflow is source-only. It must not load model parameters, 2024 role profiles, development predictions, or any fitting/scoring code.

## Frozen source

Official MLB Stats API season surfaces only:

- `stats=season`
- `season=2025`
- `playerPool=ALL`
- `gameType=R`
- groups: `fielding`, `hitting`
- page size: 500 with complete pagination

Frozen actual-league map:

- MLB: 103, 104
- AAA: 112, 117
- AA: 109, 111, 113
- High-A: 116, 118, 126
- Single-A: 110, 122, 123
- Rookie/complex: 121, 124, 130

## Required retained evidence

For every league/group/page:

- raw response bytes;
- requested URL;
- HTTP status;
- response byte count;
- SHA-256 hash;
- returned split count;
- reported total split count;
- pagination offset.

Project fielding rows only through the already-certified deterministic `position_role_source` projector.

Persist:

1. canonical 2025 player × team × position fielding usage;
2. 16-row league coverage table using same-league hitting IDs as a coverage diagnostic;
3. source report with all capture records and errors;
4. raw capture pages.

## Fail-closed acceptance

The 2025 source is materialized successfully only if:

- all 16 league pairs complete both `fielding` and `hitting` requests;
- pagination is complete for every request;
- projected fielding grain is unique;
- no source exception occurs.

Partial evidence must still be uploaded on failure, but confirmation scoring remains unauthorized.

## Boundary

This source workflow must record:

- `2025_position_source_accessed = true`;
- `2025_position_outcomes_scored = false`;
- `model_parameters_loaded = false`;
- `model_fit = false`;
- `confirmation_scoring_authorized_next = true` only after a fully successful source materialization.

It must not import or download the frozen confirmation parameter artifact.
