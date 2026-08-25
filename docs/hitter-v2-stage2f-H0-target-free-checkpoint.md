# Hitter v2 Stage 2f H0 target-free checkpoint

## Scientific outcome

The authorized target-free `H0_NEUTRAL_HIERARCHICAL_OUTCOMES` foundation is
implemented. Synthetic tests establish that the terminal probability tree is
coherent, level translations are chronology-safe and anchored to MLB, missing
transition evidence falls back to a nonzero pooled path with wider uncertainty,
forward development can depend on age relative to level, and removing every H0
increment returns the input outcome forecast exactly.

This checkpoint does **not** show that H0 is useful on real players. No real
source was materialized, no candidate was fit, no disclosed validation target
was opened, and no model score was computed.

## Implemented primitives

- Exact conversion between the 12-outcome simplex and the frozen nested links.
- Adjacent-level mover translations, partially pooled by component and broad
  frozen age band, anchored to a neutral MLB reference level.
- A global component fallback for an unobserved adjacent edge; it preserves a
  nonzero estimated translation and records wider path uncertainty.
- Weighted, regularized forward-development effects using age relative to level
  and the frozen absolute-age knots at 20, 24, 28, and 32.
- Earlier-origin calibration shrunk toward intercept zero and slope one.
- An exact unmodified outcome fallback when translation, age/development, and
  calibration inputs are absent.
- The same reference-level wrapper for all permanent baseline families.

## Synthetic scientific checks

The focused suite covers simplex normalization, link round trips, exact missing-
input fallback, synthetic translation recovery, the MLB no-op anchor, global
fallback behavior, chronology rejection, forward-development direction,
calibration shrinkage, retention of distinct HR histories, and monotonic value
when coherent mass moves from an out to 1B, 2B, 3B, and HR.

All rows used by these tests are invented. Player names and identities are not
present.

The canonical lint command passed, and the complete repository test suite
passed with 968 tests. A workspace-local temporary directory was used because
the Windows system temporary directory is not accessible in this environment.

## Gate status

The implementation must stop here for review. Real source materialization and
fit require a new explicit authorization. Candidate scoring, H1 contact shape,
tracking, protected 2026 outcomes, Stage 3, and WAR remain closed.
