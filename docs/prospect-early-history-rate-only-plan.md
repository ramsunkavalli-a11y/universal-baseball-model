# Prospect early-history rate-only plan

**Status:** frozen before source collection and scoring

## Purpose

The disclosed 2013–2023 tests suggest regressed component rates add information while
the basic age/level/workload effects can make the combined model worse than a constant.
Those years cannot validate a stripped model. This test uses previously untouched
2006 and 2007 snapshot outcomes.

## Fixed chronology

- Fit one model on the 2003 snapshot and its 2004–2005 outcomes.
- Leave 2004–2005 snapshot cohorts unused; they are neither training nor selection.
- Apply the unchanged fit to 2006 and 2007, using 2007–2008 and 2008–2009 outcomes.
- Source official StatsAPI affiliated component totals for 2003–2007 and completed MLB
  component outcomes for 2004–2009. If either source is incomplete or fails accounting,
  stop without scoring.
- Use the same pre-MLB age 16–30 arrived-player population, two-year component-WAR
  target, and `0.25` positive threshold. Retain negative WAR.

## Fixed candidate and baseline

The baseline is the player-weighted 2003 positive-tail rate. The candidate uses only
four current-season component rates: hitter UBB, strikeout, home-run and extra-base-hit
rates or pitcher strikeout, UBB, hit-batter and home-run rates. Regress each rate to
the 2003 population mean with `200` PA/BF, standardize on 2003 only, and fit logistic
`C=0.1`.

There are no age, level, role, workload, interaction, demographic, organization,
ranking, outside-FV, depth, clipping, tuning, or recalibration inputs.

## Fixed decision

For hitters and pitchers separately, the candidate must improve both Brier error and
log loss in both 2006 and 2007; both pooled player-bootstrap intervals must be below
zero; and no supported age/level/role group may reverse on both scores. Supported
means at least 100 players, 20 positives and 20 negatives.

A pass is old-era supporting evidence only and cannot change production without modern
fresh confirmation and a complete conditional-WAR path. A failure closes this simple
aggregate rate-only family. No alternate rate subset or regression amount may be tried
on these outcomes.
