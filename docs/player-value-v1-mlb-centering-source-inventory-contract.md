# Player Value v1 MLB-centering source inventory contract

Status: **DIAGNOSTIC / PRE-MATERIALIZATION.**

This gate inventories immutable upstream artifacts before numerical centering. It may not fit, select, rescore, or alter an upstream model.

The inventory must record, for each downloaded artifact:

- workflow run ID, artifact name, and expected digest where already frozen;
- every file path and SHA-256;
- row count and ordered columns for readable Parquet/CSV tables;
- player identifier, season/fold, and candidate projected-component columns where present;
- nested provenance keys from JSON reports.

The authoritative batting snapshot is the successful named artifact from run `32099733186`. Artifact ID `9294645751` is stale/unresolvable as of 2026-08-19; the current run/name artifact is `9311172007` with digest `sha256:40430b67a492aec81e570cd67e74ae3ca7b809cb3ce538082237be244c450d44`. This is an artifact-retention identity repair, not a model or source change.

The inventory is descriptive evidence only. Numerical centering remains blocked until a later materializer explicitly maps the certified columns to `Rbat`, `Rbr`, `Rdef`, and `Rpos`, retains all 651 official members, and passes the `1e-10` residual tolerance.


