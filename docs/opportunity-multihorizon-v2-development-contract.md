# Opportunity multi-horizon v2 development contract

**Frozen before scoring:** 2026-09-09; source-gate amendment before scoring  
**Status:** authorized development test; not a production promotion

## Purpose

Test direct team-neutral opportunity models for forecast horizons 2–6. A direct model
uses only the dated snapshot and predicts the target season. It never feeds a prior
forecast back as if it were observed evidence.

## Reproducible source extension

Official StatsAPI reproduced 44,900 hitter snapshots and 49,208 pitcher snapshots for
2008–2017. Exact-date 40-man pulls produced 12,308 memberships. The 2008 40-man result
has only 888 players, versus 1,247–1,284 in 2009–2017, and is excluded as visibly
incomplete. Source-status duplicates in 2011, 2014–2016 do not change binary membership
and row status remains unused.

The source audit also tested 2003–2007. It returned only 1,221–1,229 roster players in
2003–2004 and only 144–820 apparent 40-man members through 2007. Those seasons cannot
support a universal denominator or a false-zero 40-man feature and are excluded.

The eligible clean pairs are:

- horizon 2: 2009–2017 snapshots plus 2021–2023;
- horizon 3: 2009–2016 plus 2021–2022;
- horizon 4: 2009–2015 plus 2021;
- horizon 5: 2009–2014, but only one chronology-safe evaluation is possible;
- horizon 6: 2009–2013, with no chronology-safe evaluation possible.

Every target is a completed season no later than 2025. Pairs whose path crosses the
canceled 2020 minor-league season are excluded. Protected 2026 outcomes are not used.

## Models and evaluation

Each horizon independently tests the same nested hitter U0/UA/U or pitcher P0/PA/P
forms already frozen for the one-year gates. The target is zero-inclusive MLB PA or BF
in the direct target year. Pitcher role remains a snapshot predictor; future role
probabilities remain a separate historical transition.

For each component and horizon, a training pair is allowed only when its target season
is completed by the evaluation snapshot. The four evaluation folds are 2017→2019,
2021→2023, 2022→2024 and 2023→2025 for horizon 2; 2015→2018, 2016→2019, 2021→2024 and
2022→2025 for horizon 3; and 2013→2017, 2014→2018, 2015→2019 and 2021→2025 for horizon
4. All earlier eligible pairs are used for training as they become available.

Horizons 5 and 6 fail the source/chronology gate before model scoring. They retain the
incumbent historical fallback. All eligible pairs for horizons 2–4 are used to fit a
final development package only after selection.

The current age/level historical cohort method is scored on the same player rows as an
incumbent benchmark.

## Fixed decision rule

A richer form may replace the incumbent for one horizon only if it:

1. has lower pooled full-distribution negative log likelihood than U0/P0;
2. wins that loss in at least three of four folds;
3. has pooled participation log loss no worse than U0/P0;
4. has pooled opportunity MAE no more than 2% worse than U0/P0;
5. has pooled participation Brier error no worse than the incumbent cohort method;
6. has pooled opportunity MAE no worse than the incumbent; and
7. is not more than 10% worse than the incumbent MAE in any fold.

If both richer forms pass, choose the simpler form within a pooled-loss tie of 0.001;
otherwise choose the lower-loss form. If neither passes, retain the incumbent for that
horizon. No rescue tuning is allowed after results are read.

## Boundary

Passing horizons may enter only the separately labeled provisional scenario. Failing
horizons keep their existing historical fallbacks. No result is production-confirmed
until the one-year packages first pass their protected 2026 confirmation.
