# ADR 024: Separate Current Talent PA and contact-evidence denominators

- Status: Accepted for Current Talent evidence materialization
- Date: 2026-08-16

## Context

The first 2024 Current Talent player-game prototype tried to force every game into
one mutually exclusive PA partition:

`core profile + known non-core + unknown = PA`

That assumption passed the first AAA + MLB proof because those top-end slices did
not expose a player-game overage.  It failed when the same materializer was run
across AA, High-A, Single-A, and Rookie/complex.

The failure was useful: it occurred before any talent modeling and therefore
forced the evidence contract to confront the source grains instead of silently
clipping counts.

ADR 002 already establishes the governing principle: PA evidence and pitch/contact
evidence are separate canonical grains. ADR 006 further establishes that physical
pitches can belong to play sequences that are not themselves completed PAs. The
frozen Performance player-season transform also already preserves contact-count
residuals and explicitly flags cases where the core-profile event count exceeds
PA instead of forcing those counts to agree.

## Live 2024 audit evidence

A dedicated player-game accounting audit was run after applying the certified
metadata-aware boxscore resolver and play-sequence participant authority.

### Rookie / complex

Across 43,698 batting player-games:

- 195 games had any contact-vs-boxscore accounting residual;
- only 4 player-games caused the prototype core/non-core count to exceed PA;
- the maximum overage was +1 event;
- 20 player-games had one or more excess reusable contact observations;
- 175 had fewer reusable contact observations than boxscore-derived result contacts;
- total contact residual was -191;
- only 1 player-game contained more physical contact rows than unique contact play sequences;
- **0 player-games had duplicate core-contact rows within a play sequence**;
- PA identity residuals were 0 across the audited surface.

Therefore the overages are not explained by a broad duplicate-row problem. They
are principally unique play-sequence contact observations living on a grain that
is not guaranteed to be a one-row-per-completed-PA result table.

Double-A independently showed the same architectural issue in the Current Talent
materializer, while its already-certified season Performance build retained a
small +9 reusable-contact residual versus the season aggregate backbone over
98,790 contacts.

## Decision

### 1. Do not force contact/profile observations into a PA partition

Current Talent game evidence will preserve two denominators:

- **PA/result opportunity evidence** from the independent game outcome backbone;
- **observed contact/profile evidence** from the certified reusable contact layer.

A core-profile count may exceed PA in an individual player-game. That is an
explicit source/evidence diagnostic, not a reason to delete or reassign an event.

### 2. Preserve explicit contact coverage fields

Each player-game summary must expose at least:

- `batting_plate_appearances`;
- `expected_contact_count` — result contacts implied by the independent PA/boxscore backbone;
- `observed_contact_count` — reusable physical contact observations after participant authority;
- `contact_count_residual = observed - expected`;
- `core_profile_event_count`;
- `bunt_contact_count`;
- `foul_air_excluded_count`;
- `unknown_contact_count`;
- `special_noncontact_count`;
- `pa_accounting_residual`;
- participant-authority and source-capability status.

The long-form 12-bin table remains the authoritative decomposition of
`core_profile_event_count`.

### 3. Validate each grain on its own terms

The generic Current Talent evidence validator must require:

- non-negative observed counts;
- exact long-form core-bin reconciliation;
- `contact_count_residual == observed_contact_count - expected_contact_count`;
- observed contact count equals classified core contacts plus bunt, foul-air, and
  unknown contacts;
- `pa_accounting_residual` equals PA minus the independently identified BB/HBP,
  K, expected-contact, and special-noncontact components.

It must **not** require `core_profile_event_count <= PA` or require profile evidence
counts to sum to PA.

### 4. Snapshot diagnostics must use named denominators

Avoid a generic `coverage_rate` whose denominator is ambiguous. Predictor
snapshots should expose separately:

- core profile events per PA;
- observed / expected contact coverage;
- core share among profile observations;
- signed PA-accounting residual;
- raw and recency-weighted evidence counts.

The 12-bin conditional profile continues to normalize over eligible core evidence.

### 5. Frozen Performance reconciliation becomes stricter, not weaker

Game evidence must still roll up exactly to the frozen season Performance surface
for PA, core-profile events, every core-bin occurrence, and source-derived contact
classification counts where the frozen summary exposes them.

No clipping, row deletion, imputation, or denominator repair is allowed merely to
make player-game counts look mutually exclusive.

## Consequences for modeling

The first results-only Current Talent baseline should not pretend the public
contact layer is a perfect one-observation-per-PA multinomial table. It can still
estimate the 12-bin latent profile from the preserved evidence, but likelihoods
and coverage diagnostics must respect the actual observation denominators.

If a later source or transformation can prove a one-result-contact-per-true-PA
history across all affiliated levels, it can be evaluated as a richer/cleaner
observation layer. It does not retroactively justify discarding certified physical
contact evidence in the current foundation.

## Non-decision

This ADR does not choose the final statistical form of Current Talent, level
translation, recency, age prior, or projection. It only fixes the evidence grain
so those later choices are made on auditable chronology-safe inputs.
