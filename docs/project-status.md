# Project status and handoff

Last updated: 2026-08-18

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active development branch: `source-certification-poc`
- `source-certification-poc` contains newer work than the latest integration into `main`.
- Work in small verified batches.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, playing time, position/role, defense, WAR/value, and final ranking separate.

## Stage summary

### Performance — DONE for current batting pipeline

Completed-2024 affiliated batting Performance materialization is production-shaped and retained.

Primary checkpoint: `docs/performance-2024-affiliated-checkpoint.md`.

### Current Talent — DONE / FROZEN

Retained universal model: `translated_multiseason_recency_empirical_bayes_v1`.

Frozen core design: 1,095-day history, 180-day exponential half-life, EB prior strength 100 effective core events, training-only MLB-anchored level translation, frozen age/current-level prior, frozen 12-component batting profile.

Richer Challenger 1 failed development. Richer Challenger 2 passed development but failed its one-shot 2023 confirmation. Both are closed without rescue tuning.

Key records:

- `docs/current-talent-results-only-baseline-freeze.md`
- `docs/current-talent-contact-value-confirmation-result.json`
- `docs/current-talent-challenger2-postmortem.md`

### Projection v1 batting rate/profile — DONE / FROZEN

Retained model: `frozen_current_talent_carry_forward_v1`.

The explicit age/development challenger was selected on 2022, passed fixed 2023 OOT validation, then failed the pre-registered 2024 OOT primary gate. That failure is binding and the challenger is closed without rescue tuning.

**Outcome boundary:** 2025 batting-rate/profile outcomes remain untouched for Projection v1. Later Playing Time and Position/Role confirmations opened only their separately frozen 2025 targets.

Key records:

- `docs/projection-batting-v1-development-contract.md`
- `docs/projection-v1-methodology-review.md`
- `docs/projection-batting-v1-development-result.json`

### Playing Time v1 — DONE / FROZEN / CONFIRMED

Production model: `playing_time_recent_opportunity_40man_b2_hurdle_v1`.

Architecture: L2 logistic `P(next-season MLB PA > 0)` plus zero-truncated NB2 positive MLB PA. Selected on 2022, passed 2023 and 2024 OOT validation, then passed its isolated one-shot 2025 confirmation on 3,759 snapshot players. No 2025 refit, reselection, recalibration, threshold change, or rescue tuning occurred.

Key records:

- `docs/playing-time-role-current-status.md`
- `docs/playing-time-v1-confirmation-contract.md`
- `docs/playing-time-v1-confirmation-result.json`

### Position / Role v1 — DONE / FROZEN / CONFIRMED

Production model: `primary_share_thresholded_transition_mean_v1`.

Portable nine-position batting-role profile across C, 1B, 2B, 3B, SS, LF, CF, RF, and DH. Pitcher usage remains outside the batting-role channel.

Historical source certification passed 64/64 season × league pairs. The final selective transition model passed both development folds, its parameters were frozen before 2025 source access, and the untouched 2025 confirmation passed on 2,891 players:

- mean TV `0.325526526` -> `0.324624904`;
- mean SSE `0.226924779` -> `0.216389159`;
- no confirmation refit, threshold change, or reselection.

Key records:

- `docs/position-role-historical-source-result.json`
- `docs/position-role-selective-transition-result.json`
- `docs/position-role-confirmation-parameters.json`
- `docs/position-role-2025-confirmation-result.json`

## ACTIVE NEXT STAGE — Defense v1 design / source gates

The project now has frozen player-level batting-rate, MLB-opportunity, and position/role channels. The unresolved downstream dependency is defensive quality.

A team allocator remains unnecessary unless a later value requirement demonstrates otherwise.

### Defense source architecture established so far

Primary checkpoint: `docs/defense-v1-source-architecture-checkpoint.md`.

#### Range / OAA — LEADING REUSE CANDIDATE

Pinned reusable implementation: SportsDataverse `0.0.75`, upstream commit `1dafadb38c5240d8e29a0f818efbabe04cd6c417`.

MLB frozen reuse POC:

- June 2024: 116,355 pitches / 20,623 BIP;
- 18,820 usable OAA opportunities (`91.26%`);
- 263 players matched to 2024 Savant OAA;
- Pearson `0.3045`, passing the upstream month-vs-season oracle floor `>=0.30`;
- SportsDataverse's own full-season 2024 test reports about `0.605` Pearson vs Savant OAA.

**Binding architecture decision:** do not build a new public catch-probability/OAA model from scratch unless a later implementation failure requires it.

#### Tracked MiLB range — EXECUTION / COVERAGE FEASIBLE

SportsDataverse's default minor-search parameters initially returned zero rows. The OAA implementation was not the problem.

Follow-up transport diagnostic added the raw Savant `minors=true` parameter, fetched the tracked MiLB pool, and classified Triple-A client-side from official team identity.

2024-06-10 through 2024-06-16:

- tracked pool: 35,352 pitches;
- AAA: 27,749 pitches / 4,479 BIP / 3,986 OAA opportunities (`88.99%` usable);
- tracked non-AAA: 7,603 pitches / 1,196 BIP / 803 OAA opportunities (`67.14%` usable);
- required trajectory and responsible-fielder fields present;
- both frozen execution/coverage gates passed.

Observed non-AAA home teams were Clearwater, Daytona, Dunedin, Fort Myers, and Jupiter, consistent with the public Florida State League tracking tier.

**Important boundary:** this proves technical reuse on tracked MiLB data, not MiLB OAA accuracy; there is no public proprietary MiLB OAA oracle.

For future MiLB Statcast materialization, use `minors=true`, bounded date chunks, and client-side official team/league classification. Do not rely on server-side `hfLevel` filtering.

#### Catcher defense — CANDIDATES, NOT ACCEPTED YET

SportsDataverse exposes separate framing, blocking, and throwing components and explicitly supports MiLB pitch frames technically.

Current evidence:

- framing: full-2024 public-data Pearson about `0.468` vs Savant; live floor `0.40`; promising reuse candidate;
- blocking: implementation exists, but inspected offline oracle is mainly a wiring/coverage check rather than strong numeric validation;
- throwing: full-2024 Pearson only about `0.073`, with severe public SB/CS attempt-recovery limitations; treat as weak evidence unless a better source is found.

Do not combine catcher components simply because reusable code exists.

#### Untracked affiliated MiLB — UNRESOLVED

No tracked range signal exists universally below the documented Savant coverage tiers. Missing tracking must not be converted to a neutral defensive score by accident.

A heavily shrunk/neutral fallback is a baseline candidate to test, not a production rule. First inventory whether official fielding outcomes or another mature public source provides a chronologically useful universal signal.

### Minimum eventual Defense v1 output

Before WAR/value, Defense v1 should expose at least:

- player id;
- position;
- projected defensive-quality value/rate on a clear run-value or equivalent scale;
- opportunity basis;
- evidence/coverage tier;
- uncertainty / source-coverage metadata;
- component provenance (range, framing, blocking, throwing where applicable).

Positional adjustment belongs to the later value layer, not inside fielding-quality skill.

### Immediate next batch

1. Run a frozen catcher feasibility POC on MLB plus the now-proven tracked MiLB transport, prioritizing framing and keeping blocking/throwing separate.
2. Inventory universal non-tracking defensive evidence already available from official fielding stats / mature public sources and test whether any Tier-C signal deserves development.
3. Only after those source gates, freeze Defense v1 chronology, shrinkage, age/projection choices, uncertainty rules, and OOT validation before fitting a production defensive forecast.

Do **not** jump to WAR/value, reopen Playing Time/Position Role, or impute defense for untracked players yet.

## Governing read order

1. `docs/project-status.md`
2. `docs/defense-v1-source-architecture-checkpoint.md`
3. `docs/defense-milb-statcast-transport-diagnostic-result.json`
4. `docs/defense-sportsdataverse-reuse-poc-result.json`
5. `docs/position-role-2025-confirmation-result.json`
6. `docs/playing-time-v1-confirmation-result.json`
7. `docs/projection-batting-v1-development-result.json`
8. `docs/current-talent-results-only-baseline-freeze.md`
9. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent, Projection v1, Playing Time v1, or Position/Role v1 absent a concrete implementation failure.
- Do not tune rejected models against their held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Keep batting skill, opportunity, position/role, defensive skill, positional adjustment, and value separate.
- Treat source coverage/missingness as information, not as zero skill.
- Update this handoff whenever the active stage or binding result changes.
