# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Core principles

- Separate **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** instead of collapsing them into one opaque score.
- Use a common evaluation language across levels while allowing different evidence and models where data coverage differs.
- Prefer mature public datasets, parsers, and packages over rebuilding source cleanup from scratch.
- Treat MLB/official sources as the authority for reconciliation, not necessarily as the first working dataset.
- Preserve uncertainty, data coverage, provenance, and measurement quality in model outputs.
- Validate chronologically and prevent hindsight leakage.
- Keep production logic in `src/`; notebooks are for exploration only.

## Initial workflow

1. Audit reusable public data sources and packages.
2. Define the minimum canonical data needed for the first Performance model.
3. Run a small proof of concept and reconcile it against official totals.
4. Only then design the historical/incremental pipeline.

The project will proceed in small, verified implementation batches rather than large scaffolding changes.
