# Current Talent batted-ball tracking-history contract

Last updated: 2026-08-17  
Status: **FROZEN BEFORE 2022 RICHER DEVELOPMENT SCORING.**

This document closes one source-window ambiguity in the first EV/launch-angle Current Talent challenger. It supplements `docs/current-talent-batted-ball-quality-challenger-plan.md` and `docs/current-talent-batted-ball-development-execution-contract.md` without changing the feature family, decay rate, eligibility threshold, residual form, or promotion rules.

No 2022 richer proper score had been observed when this boundary was frozen.

## Tracking source epoch

For this challenger, eligible tracking history begins on:

**2021-01-01**

No pre-2021 Statcast / tracking evidence may enter the richer feature, standardization fit, residual fit, development scoring, or later fixed confirmation for this challenger.

## Why this boundary is fixed

MLB has public Statcast history before 2021, while the certified universal validation/source-capability program for this challenger begins in 2021 and historical affiliated-MiLB tracking capability is first established in 2021.

Allowing pre-2021 MLB tracking while lower-level players cannot have comparable pre-2021 tracked history would create an implicit source-family advantage that was not part of the predeclared challenger design.

The 2021 epoch therefore keeps the richer evidence family aligned to the certified universal validation era rather than silently giving MLB players extra historical tracking depth.

This is a source-scope rule, not a fitted hyperparameter.

## 2021 training snapshot

At the fixed `2021-07-15` training cutoff:

- only model-eligible tracked BBE dated **2021-01-01 through 2021-07-14** may contribute;
- the 180-day exponential decay is applied continuously inside that evidence;
- no 2020 MLB Statcast is used;
- no tracking row on or after the cutoff is used.

Because affiliated MiLB had no 2020 season and the richer source gate begins in 2021, this is the cleanest common source epoch for the first universal challenger.

## 2022 development folds

For each 2022 development cutoff, tracking history may include:

- eligible 2021 tracked BBE; and
- eligible 2022 tracked BBE strictly before the cutoff.

The same **180-day exponential decay continues across the season boundary**. There is no January 1 reset.

Thus the fixed 2022 development folds use one common source epoch but still test whether prior-season physical contact evidence retains useful signal after recency decay.

## Materialization versus feature cutoff

A retained source/materialization artifact may contain rows later than a particular model cutoff for reuse and auditability. That does not make those rows eligible.

The model feature builder must always enforce strict `game_date < as_of_date` semantics. Development artifacts are additionally season-scoped so no pre-2021 rows can enter the evaluator.

## Future fixed confirmation

If the 2022 development gate passes and its checkpoint is committed, the already-fixed 2023 confirmation must retain the same **2021-01-01 source epoch**.

The confirmation refit may use eligible tracked evidence from 2021 and 2022 at its fixed annual training snapshots, but it may not backfill pre-2021 MLB Statcast after seeing development results.

## Decision boundary

Changing the tracking source epoch after development scoring would constitute a new challenger. In particular, a later model that deliberately uses longer MLB-only Statcast history must be separately predeclared and validated rather than silently substituted into this gate.
