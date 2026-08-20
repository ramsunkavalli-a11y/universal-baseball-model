# Workflow lifecycle after the v1 freeze

Status: **FROZEN — INTEGRATION/SECURITY CHECKS AUTOMATIC; HISTORICAL WORKFLOWS MANUAL-ONLY**

Player Value v1 and every upstream v1 gate are complete. The repository keeps
its historical source, diagnostic, development, confirmation, and
materialization workflows as executable audit evidence, but ordinary branch
changes must not rerun them or rewrite frozen result documents.

## Automatic workflows

Exactly two non-writing workflows are automatic:

- `.github/workflows/ci.yml` runs for pull requests into `main` and pushes to
  `main`, installs `.[dev]`, runs Ruff, and executes the complete test suite;
- `.github/workflows/codeql.yml` runs CodeQL for pull requests and pushes to
  `main`, plus a weekly scheduled scan.

Both can also be dispatched manually. Neither workflow may materialize or
commit scientific results.

## Historical workflows

Every historical workflow is `workflow_dispatch` only. Manual execution is allowed
for an explicit audit, source diagnostic, or reproduction attempt. A manual run:

- does not by itself supersede a frozen result;
- must not be described as a refreeze when it reads a live or mutable source;
- must be compared with the binding artifact and contract before any output is
  accepted;
- requires a new versioned, pre-outcome contract before it may change a binding
  model, population, parameter, source, or Player Value result;
- must preserve the prior binding document and artifact as provenance.

## Why automatic writers were disabled

During the 2026-08-20 integration audit, cleanup-only edits triggered eight
completed workflows that committed regenerated historical documents. The most
important case was Defense run `32391048359`: its nominal parameter freeze still
called live Savant leaderboard functions. The response differed from the
original run `32198603779` artifact and changed fitted coefficients. Other
workflows rewrote source-run metadata or introduced small solver-level numerical
drift despite unchanged decisions.

The regenerated documents were therefore rejected and the binding files were
restored. Keeping historical workflows manual preserves reproducibility evidence
without allowing unrelated maintenance to redefine v1.
