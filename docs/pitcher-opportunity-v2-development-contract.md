# Pitcher Opportunity v2 development contract

**Frozen before scoring:** 2026-09-09  
**Status:** authorized development test; not a production promotion

## Purpose

Build the pitcher counterpart to the universal hitter opportunity model. The target is
next-season MLB batters faced, including zero for every pitcher in the dated affiliated
snapshot who does not pitch in MLB the following season.

## Population and predictors

Each October 15 snapshot uses the union of official `fullRoster` identity and players
with official MLB-through-rookie pitching statistics. Inactive players, unknown level,
unknown role and missing age remain in the population.

Three nested forms are tested:

1. P0: broad level and current starter/swingman/reliever/unknown role;
2. PA: P0 plus age, missing-age indicator, current MLB BF and current minor-league BF;
3. P: PA plus exact-date official 40-man membership.

No team depth, future team, future level, future role, name match, pitch quality, or
2026 outcome is allowed. The existing historical role-transition probabilities remain
separate; this gate replaces only MLB participation probability and conditional BF.

## Chronology

The valid pairs are 2018→2019, 2021→2022, 2022→2023, 2023→2024 and 2024→2025.
The two pairs crossing the cancelled 2020 minor-league season are excluded. Four
expanding-window evaluations are run, then all five folds are used only to fit the
selected development package for a prospective current forecast.

## Fixed decision rule

PA or P may replace P0 only if it has lower pooled full-distribution negative log
likelihood, wins that metric in at least three of four folds, has no worse pooled
participation log loss, and has BF mean absolute error no more than 2% worse. If both
pass, choose the simpler form within a pooled-loss tie of 0.001; otherwise choose the
lower-loss form. No rescue tuning is allowed after the results are read.

## Promotion boundary

This is development evidence. A selected model can be used only as a clearly labeled
provisional current input. Completed 2026 outcomes remain protected for a separately
frozen confirmation test.

