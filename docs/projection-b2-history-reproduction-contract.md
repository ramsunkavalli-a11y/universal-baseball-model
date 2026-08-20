# Projection Baseline 0 / Current Talent B2 history reproduction contract

Status: **FROZEN BEFORE PROJECTION MODEL SCORING**

## Decision

Projection Baseline 0 must reproduce the already-validated Current Talent Baseline 2 history policy; it must **not** extend that policy into a new pre-2021 source era merely because the numerical lookback cap is 1,095 days.

Frozen B2 is:

`translated_multiseason_recency_empirical_bayes_v1`

Its history rule is:

- current-season eligible evidence;
- plus **prior certified seasons where available**;
- capped at 1,095 calendar days;
- weighted continuously with the frozen 180-day half-life.

The certified universal Current Talent bundle begins in **2021**. The predeclared B2 plan explicitly states that no new raw source is required, that 2022 development uses certified 2021 + pre-cutoff 2022 evidence, and that 2023 confirmation uses certified 2021–2022 + pre-cutoff 2023 evidence. It also states that a 2021 fold collapses to the season-to-date comparator when no prior certified season exists.

Primary governing records:

- `docs/current-talent-baseline2-plan.md`
- `docs/current-talent-baseline2-development-checkpoint.md`
- `docs/current-talent-baseline2-confirmation-checkpoint.md`
- `docs/current-talent-results-only-baseline-freeze.md`

## Projection reproduction by fold

For the frozen Projection development snapshots:

- `2021-10-15`: use eligible certified 2021 evidence only; there is no authorized prior certified universal season, so B2 must obey its no-prior-history invariant.
- `2022-10-15`: use eligible certified 2021 + 2022 evidence, subject to the 1,095-day cap and 180-day decay.
- `2023-10-15`: use eligible certified 2021 + 2022 + 2023 evidence, subject to the same cap and decay.

The absence of pre-2021 universal evidence is recorded as **calendar left-censoring of the theoretical maximum lookback**, but it is not a missing-input defect under the frozen B2 contract.

## Why pre-2021 backfill is not authorized

Adding 2018–2020 results would not merely fill a neutral storage gap. It would change the information set on which B2 was developed and confirmed while crossing meaningful source/environment boundaries:

- the universal certified bundle was intentionally started in the post-reorganization affiliated era;
- 2020 has no affiliated minor-league season;
- pre-2021 MiLB structure/source semantics differ from the validated universal surface;
- the B2 validation explicitly tested prior **certified** seasons available in the 2021–2023 bundle, not arbitrary older history.

Therefore pre-2021 backfill would be a new Current Talent challenger/source-extension question, not faithful reproduction of the frozen comparator.

## Implementation invariant

Projection development evidence must continue to report:

- requested 1,095-day calendar-window start;
- earliest actual certified event available;
- calendar left-censoring days;
- certified seasons available before each snapshot.

But the gate for Baseline-0 reproduction is whether the expected **certified-source history** is present, not whether every calendar day back to the maximum cap is represented.

`history_extension_required_before_frozen_b2` must therefore remain `false` when the authorized 2021-source-epoch seasons are complete. `pre_2021_backfill_authorized` is `false`.

## Leakage boundary

This decision uses only the already-frozen B2 design and pre-2025 source/evidence structure. It does not inspect Projection scores and does not access 2025 outcomes.
