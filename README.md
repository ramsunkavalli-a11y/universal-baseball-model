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

## Foundation documents

- [`docs/source-audit.md`](docs/source-audit.md) — research and provisional assignment of public data sources/packages.
- [`docs/source-certification-plan.md`](docs/source-certification-plan.md) — empirical tests a reusable source must pass before it can feed canonical tables.
- [`docs/adr/001-reuse-first-source-strategy.md`](docs/adr/001-reuse-first-source-strategy.md) — architectural decision establishing the reuse-first, certification-gated strategy.

## Initial workflow

1. Audit reusable public data sources and packages.
2. Certify the most promising reusable inputs on deliberately varied small samples.
3. Define the narrow canonical contracts needed by the first Performance/Profile model using what the audit and certification reveal.
4. Reconcile the proof of concept against official totals and characterize data coverage.
5. Only then commit to the historical/incremental production pipeline.

Foundation work should favor correctness, reversibility, and explicit evidence over speed. We should pause for a decision when an unresolved source or modeling assumption could materially change downstream architecture rather than papering over it in code.
