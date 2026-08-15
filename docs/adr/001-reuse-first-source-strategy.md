# ADR 001: Reuse-first source strategy

- **Status:** Accepted for foundation/POC
- **Date:** 2026-08-15

## Context

The project needs reproducible data from MLB through the lowest affiliated levels. The official MLB game feed is rich enough to support much of the work, but reconstructing a complete historical PBP database directly from raw nested JSON would require substantial effort in collection, caching, retries, schedule edge cases, event parsing, identity handling, and historical schema drift.

Multiple public projects have already solved meaningful parts of that work. Reusing them can reduce engineering time, but importing their outputs without verification would transfer their bugs and assumptions into every downstream model.

The project also needs to remain maintainable if an upstream package changes or disappears.

## Decision

We will use a **reuse-first, certification-gated source architecture**.

### 1. Separate authority from working input

An official source can be the reconciliation authority without being the historical dataset we ingest directly.

For modern affiliated baseball, MLB Stats API / Baseball Savant are the primary official authorities for the data they expose. Certified public datasets may serve as working inputs when they reproduce those sources adequately.

### 2. Upstream packages do not define our schema

All external packages/datasets sit behind source adapters or normalization steps. Downstream canonical tables and model code depend only on our contracts.

This allows a source to be replaced without redesigning the model layers.

### 3. Historical MiLB PBP starts with reuse

`armstjc/milb-data-repository` is the first historical MiLB PBP candidate to certify because it already performs the expensive collection and flattening work over a long time span.

It remains quarantined until the tests in `docs/source-certification-plan.md` pass for explicit level/season scopes.

### 4. Direct official access remains available

We will retain a reliable path to official schedules, boxscores, person metadata, and individual game feeds for:

- reconciliation;
- debugging;
- gap filling;
- current incremental updates;
- detecting upstream-source drift.

SportsDataverse and `python-mlb-statsapi` are the leading Python adapter candidates and will be compared empirically before committing to one for each task.

### 5. Tracking is an enrichment source

Baseball Savant Minor League Statcast is not universal across levels/parks/seasons. Tracking fields therefore enrich higher-evidence tiers rather than defining the minimum canonical player record.

### 6. Identity is source-independent

The canonical system will use its own immutable internal player identifier. MLBAM IDs remain critical source identifiers for modern affiliated data, while the Chadwick Register supplies a public cross-source identity mapping and additional external IDs.

### 7. Reconciliation remains production behavior

Certification is not a one-time research notebook. Production ingestion should retain lightweight checks for duplicates, aggregate reconciliation, schema drift, and coverage drift.

### 8. Raw-data redistribution is not assumed

The project will keep source data private during development. A later public-release decision will distinguish derived model outputs from redistribution of bulk normalized/raw source data and will trigger a separate source-terms review.

## Consequences

### Positive

- Avoids spending weeks rebuilding mature data collection before knowing it is necessary.
- Makes upstream parser defects detectable before they contaminate training data.
- Keeps the model architecture independent of any one package.
- Makes historical coverage achievable sooner.
- Preserves the option to replace or repair a source locally.
- Treats data-quality uncertainty as a first-class part of the model foundation.

### Costs

- We must write and maintain certification/reconciliation tests.
- Some data will exist in multiple representations during development.
- Provenance/version metadata is required from the beginning.
- A source may be certified for one scope and rejected for another, which complicates coverage bookkeeping.

## Rejected alternatives

### Build everything directly from MLB Stats API first

Rejected because it front-loads substantial parsing/collection work that credible public projects have already done, without improving the modeling question we are trying to answer.

### Treat a public cleaned dataset as truth

Rejected because code review already demonstrates that mature-looking public collectors can contain plausible parser defects or ambiguous level/coverage assumptions.

### Standardize on one baseball package for every source

Rejected because the best historical PBP source, direct Stats API client, identity crosswalk, MLB historical benchmark, and tracking source are different tools. Forcing one dependency to own everything would increase rather than reduce coupling.

## Related documents

- `docs/source-audit.md`
- `docs/source-certification-plan.md`
- Governing project charter: Universal Public Baseball Player Ranking Model PDF
