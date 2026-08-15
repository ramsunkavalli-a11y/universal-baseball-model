# ADR 009: Separate retrospective event-cutoff and true vintage backtests

- Status: Accepted
- Date: 2026-08-15

## Context

The project requires strict chronological validation and wants to compare model outputs with contemporary public rankings without hindsight leakage.

There are two different leakage questions that are easy to conflate:

1. **Did the model use baseball events that happened after the forecast cutoff?**
2. **Did the model use a corrected/revised representation of an older event that was not literally the data vintage available at the forecast cutoff?**

The historical MiLB bootstrap files are current public release snapshots. Certification has already shown that snapshots can overlap and later values can change. The current MLB Stats API can likewise contain corrections to older games.

A model trained only on games through June 30, 2023 can therefore be free of future-player-performance leakage while still using a 2026-corrected representation of those pre-July games.

Calling that exact information set “as of June 30, 2023” would overstate what the data provenance proves.

## Decision

The validation framework will use two explicitly named modes.

### Retrospective event-cutoff

Eligibility is governed by baseball event time:

`event_date <= cutoff`

The model may use the project's current certified representation of those historical events.

This is the default practical mode for:

- model development;
- rolling-origin validation of future MLB outcomes;
- calibration and feature selection;
- comparing alternative model structures when the target occurs after the cutoff.

It prevents future **performance** from entering predictors, which is the main causal/forecasting requirement.

Outputs must be labeled `retrospective_event_cutoff` (or equivalent), not strict “as-of vintage.”

### Vintage / information-set backtest

Eligibility additionally requires a defensible source vintage that was available by the cutoff:

`knowledge_available_at_utc <= cutoff`

This mode is used when the claim is specifically about reproducing what could have been known at the time, for example:

- benchmarking against a prospect ranking published on a specific date;
- reconstructing a historical projection-system snapshot;
- measuring whether a current method would have identified a player before a public re-ranking.

A vintage backtest is only permitted when the relevant source snapshot/publication timing is actually archived or otherwise defensible.

## What we will not do

We will not set `knowledge_available_at_utc` equal to an old game date merely because the underlying play happened then.

We will not describe a backtest using a current corrected historical file as a literal historical data vintage.

We will not reject all retrospective historical modeling merely because exact historical source bytes are unavailable. Event-cutoff validation remains rigorous for future-performance forecasting as long as target construction and feature windows are chronological.

## Provenance fields

The source registry therefore distinguishes:

- `event_date` / event time;
- `source_published_at_utc`;
- `retrieved_at_utc`;
- `knowledge_available_at_utc`.

`knowledge_available_at_utc` is nullable. Null means “the exact historical public availability of this representation is not established,” not “available since the event occurred.”

## Reporting rule

Every model-card/backtest result must identify its temporal mode.

At minimum:

- `retrospective_event_cutoff`
- `vintage_information_set`

If external public rankings are used only as a secondary benchmark against a retrospective model, the report must say so rather than implying both systems consumed identical historical source vintages.

## Consequences

- We preserve strong chronological forecasting tests without making an impossible demand for archived bytes from every minor-league game.
- Truly historical information-set comparisons remain available where archived snapshots exist.
- Source corrections can be studied rather than silently treated as though they were known immediately.
- Future model improvements can add archived vintages without changing the canonical event schema.
