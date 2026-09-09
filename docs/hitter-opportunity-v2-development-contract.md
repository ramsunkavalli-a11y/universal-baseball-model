# Hitter Opportunity v2 development contract

**Frozen before scoring:** 2026-09-09  
**Status:** authorized development test; not a production promotion

## Purpose

Replace the expired B2 scoring package with a reproducible, simpler opportunity model
built directly from official aggregate sources. This test does not claim to recreate
B2 and does not alter hitter skill rates.

## Population and predictors

Each October 15 snapshot uses the union of official `fullRoster` identity and players
with official MLB-through-rookie hitting statistics. Players with no next-season MLB
PA remain as zero outcomes. Inactive players, unknown levels and missing ages remain in
the model population.

Three nested forms are tested:

1. U0: broad level only, including inactive and unknown states;
2. UA: U0 plus age, missing-age indicator, current MLB PA and current MiLB PA;
3. U: UA plus exact-date official 40-man membership.

No team depth, future team, future level, name match, current-team blocking, B2 batting
skill, or 2026 outcome is allowed.

## Chronology

The valid snapshot/target pairs are 2018→2019, 2021→2022, 2022→2023, 2023→2024 and
2024→2025. The 2019→2020 and 2020→2021 pairs are excluded because the cancelled 2020
minor-league season breaks the normal affiliated denominator and opportunity process.

Four expanding-window evaluations are run. The first fit uses 2018→2019 and scores
2021→2022. Each later evaluation adds only earlier completed folds. All five folds are
used only after selection to create a development parameter package for a prospective
2026 forecast.

## Fixed decision rule

UA or U may replace U0 only if it:

1. has lower pooled full-distribution negative log likelihood;
2. has lower full-distribution negative log likelihood in at least three of four folds;
3. has pooled participation log loss no worse than U0; and
4. has pooled PA mean absolute error no more than 2% worse than U0.

If both candidates pass, select the simpler form when their pooled full negative log
likelihoods are within 0.001; otherwise select the lower-loss form. No rescue tuning is
allowed after results are read.

## Promotion boundary

This is development evidence, not an untouched confirmation. A selected package may
produce a labeled provisional 2026 forecast, but it cannot be called the confirmed B2
model or a final production model. Protected 2026 outcomes stay closed until the season
is complete and a separate confirmation contract authorizes their use.
