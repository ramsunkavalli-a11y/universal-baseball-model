# Hitter pulled-air matched recheck

**Status:** active design review; no production change  
**Priority:** P0 within hitter talent

## Why reopen this narrowly

Stage 2c correctly found that its pulled-air increment did not improve future HR
log loss beyond the existing outcome model. The implementation tests still pass,
so there is no demonstrated coding error. That result does not settle the more
specific baseball question: among otherwise similar hitters, does a higher rate of
pulled outfield flies per contact predict more future power?

The old candidate can hide that relationship because it:

- represented `OFFB / contact` and `pull / OFFB` as separate additive terms instead
  of directly testing `pulled OFFB / contact`;
- shrank the inputs with one fixed 100-event prior and then penalized the fitted
  coefficients again;
- required one coefficient to work across every affiliated level; and
- used annual summaries that lose switch-hitter side, pitch context, and contact
  quality.

## Diagnostic question

On disclosed historical seasons only, match or adjust players for age, batting side,
level, prior contact volume, K, walk, prior HR, extra-base-hit, and outfield-fly rates.
Then ask whether the directly measured, chronology-safe `pulled OFFB / contact` rate
has a monotonic relationship with next-season:

1. HR per contact;
2. extra-base hits per contact; and
3. neutral offensive value per PA.

Report the relationship overall, by level, and by evidence band. Include players who
lose playing time; playing time is not the target. This is a talent-component test.

## Guardrails

- Use no public FV, rankings, names, or hand-selected player adjustments.
- Separate descriptive batted-ball value, repeatability, and incremental forecast
  value.
- Fit and score out of time; use equal-player and event-weighted views.
- Estimate reliability from prior seasons instead of choosing a favorable shrinkage
  constant after viewing forecast results.
- Treat contact quality as a later interaction where coverage exists, never as a
  requirement for the universal fallback.
- The disclosed-season audit is diagnostic only. Freeze one simple candidate before
  any genuinely later confirmation is opened.

## Decision

If the matched residual is monotonic, stable across supported levels, and improves
future power scores, test a partially pooled direct pulled-OFFB candidate against the
outcome-only baseline. If it is stable but not incrementally predictive, retain it as
an explanatory trait only. If neither holds, exclude it rather than assigning a
subjective bonus.
