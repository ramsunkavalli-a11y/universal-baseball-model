# ADR 022 — Do not use Savant `delta_run_exp` as canonical Performance RE24

**Status:** Accepted  
**Date:** 2026-08-16

## Context

Baseball Savant's public Statcast CSV exposes `delta_run_exp`, documented by MLB as the change in run expectancy before and after the pitch. Because Savant is already certified as the reusable MLB contact/profile source, reusing that field for MLB contextual Performance value could avoid replaying official game state solely to estimate bin values.

The universal Performance layer, however, already has a fixed contextual value definition across affiliated baseball:

`RE24 = runs_on_transition + RE24(after 24-state base/out state) - RE24(before 24-state base/out state)`

The question is therefore not whether Savant's number is a useful baseball metric; it is whether it is the **same value object** we use elsewhere strongly enough to become the MLB canonical Performance value source.

## Decision audit

A 2024 audit compared Savant terminal-PA `delta_run_exp` with the project's independently validated state-transition machinery valued by a full-season 2024 Retrosheet 24-state matrix.

Sample:

- three dates spanning April, June, and September;
- four deterministic MLB games per date;
- **12 games** total;
- full-2024 Retrosheet matrix built from **2,473 games / 192,358 candidate transitions / 24 of 24 states**.

Results:

- Savant true-PA terminals: **846**;
- official valued PA terminals: **846**;
- paired non-null values: **842**;
- official values missing Savant delta: **4**;
- Savant values missing official transition value: **0**.

All four missing Savant values were **intentional walks**. Thus the field is structurally incomplete for at least one core Performance outcome family.

Among the 842 paired events:

- event MAE versus the fixed Retrosheet-matrix RE24: **0.14692 runs**;
- event RMSE: **0.23987**;
- mean bias (Savant minus fixed RE24): **+0.00958**;
- Pearson correlation: **0.84840**.

More decisively, events were grouped by the exact canonical transition signature:

`start outs + start bases + end outs + end bases + runs scored`

There were **96** observed signatures. **53 of 96** had nonconstant Savant `delta_run_exp` values for the same canonical state/run transition, with a maximum within-signature range of **0.757 runs**.

Therefore `delta_run_exp` is not simply a differently estimated lookup table over our fixed 24-state transition definition.

At the universal Performance-bin level, all 12 core bins were represented. Occurrence-weighted absolute difference in bin means was **0.03055 runs per event**, with some bins differing more materially, including approximately:

- Pull OFFB: **-0.0731** Savant minus fixed RE24;
- Opposite LD: **-0.0605**;
- BB/HBP: **-0.0458**;
- Pull LD: **+0.0438**;
- Center GB: **+0.0411**.

Those differences are large enough to matter when MLB and MiLB players are supposed to share one Performance value definition.

## Decision

1. **Do not use Baseball Savant `delta_run_exp` as the canonical MLB Performance RE24 value.**
2. Keep the universal contextual value definition fixed at the explicit 24-state transition formula already validated against Retrosheet.
3. MLB Performance contact/profile evidence may still come from Savant; value calibration must use the same fixed-state methodology as MiLB, via Retrosheet and/or sampled official state replay.
4. Do not force Savant's missing intentional-walk values to zero or impute them from nearby pitches.
5. Preserve `delta_run_exp` as an optional MLB-only contextual/process feature for later Current Talent experiments if it provides incremental out-of-time predictive value.
6. Such later use must treat `delta_run_exp` as a distinct feature with its own source/coverage semantics, not as an alias of canonical RE24.
7. This is a methodological rejection of interchangeability, not a claim that Savant's metric is wrong. MLB documentation defines it on Savant's own run-expectancy system; our universal Performance layer requires one explicit cross-level value definition.

## Consequences

- MLB and MiLB remain directly comparable in the Performance value layer.
- The system does not trade definitional consistency for an attractive ingestion shortcut.
- Savant remains the preferred reusable MLB contact/profile source.
- The next MLB implementation step is to obtain fixed-definition contextual bin values without wholesale Stats API replay, preferably from Retrosheet state evidence joined to Savant profile evidence or a certified sampled official calibration.

## Supporting evidence

- `scripts/audit_savant_delta_run_expectancy.py`
- workflow run `31949729250`
- artifact `savant-delta-run-expectancy`
- `src/universal_baseball/run_expectancy.py`
- `src/universal_baseball/state_transitions_v2.py`
