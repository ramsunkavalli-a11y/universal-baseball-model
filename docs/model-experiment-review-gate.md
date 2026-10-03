# Required methodological review before model experiments

2026-09-27. This gate addresses the repeated distinction between correctly
executing an experiment and designing an experiment that answers the question.
It is required for new modeling work. It does not retroactively certify older
work or claim every legacy executable has been retrofitted.

## Before fitting: a short, explicit experiment contract

1. **Question and target:** what outcome, units and horizon? Is it future MLB
   performance? Which people have zero outcomes? What cannot this target tell us
   about final player value? A six-calendar-year batting target is not six years
   of club control or full WAR.
2. **Eligibility and coverage:** who is eligible at the forecast origin, how is
   that knowable then, and who is excluded? Track left truncation, missing
   histories, right censoring, cancellation and league reorganization. Actual
   zero participation requires certified target coverage, not just no file row.
3. **Training support:** for every actual held-player/time fold, and internal
   subsets if used, count distinct players by relevant origin-known profiles.
   For hitters include career stage, age, recent workload and quality and their
   plausible intersections. Show range extrapolation and absent/sparse groups.
   A large pooled training set or four populated outcome classes is insufficient.
4. **Fair contrast:** lock the evaluation identities and outcomes. When fixing
   data requires changed features, use matched feature definitions in both arms
   and retain old anchors. State which differences cannot be causally attributed
   to the change of interest. Do not replace the cohort with whichever passes.
5. **Leakage and nested learning:** every transformation/adjustment must have a
   declared cutoff and held-player provenance. Generated features need the same
   scrutiny as outcomes. Describe fallbacks; a failed join is not a zero signal.
6. **Scoring and baseball checks:** predeclare primary loss, weighting, uncertainty,
   group/origin tolerances, totals, major stress years and physical/empirical
   constraints. Separate an empirical training-range warning from a physical
   impossibility. Name predictable failure modes before looking for a win.
7. **Disposition:** define stop conditions and allowed claims. Execution pass,
   profile-support pass, predictive improvement and deployment approval are
   different questions. Support plus positive development scores still does not
   authorize deployment or certify all unmeasured assumptions.

## Implementation gate

The new post-arrival runner requires `forecast_validation.preflight` before
every fit and persists ALL arm/fold checks before any second-stage fit. Invalid
chronology, evaluation membership, identities, label pairing or required feature
coverage raises an error. Profile gaps tag predictions and block an unqualified
full-cohort claim, while retaining every difficult player in the headline score.
Twenty matching players is only a sparse-support warning threshold, not proof
of sufficiency. Different applications need appropriate checks, not blind reuse
of these bins or thresholds.

The machine-readable decision keeps separate integrity, profile, predictive and
reasonability fields and always requires separate deployment approval. Future
runners must use this gate or a documented equivalent; a new script is not an
exemption. Current implementation is V17, not a claim that every legacy script
has been changed. Re-running legacy V15/V16 code does not erase their documented
support qualifications or restore promotion eligibility.

## Required regression tests and review evidence

- Reproduce the original failure: elapsed 0–1 training versus elapsed 5 test
  cannot pass support merely because the code is correct or rows are repeated.
- Count distinct people, not repeated seasons masquerading as independent support.
- Changing future results must not change origin eligibility or support flags.
- Unavailable historical seasons remain missing; certified absences become zero.
- Keep inactive/retired players without conditioning on a future return.
- Stop leakage, duplicate populations, moved horizons and silent test-row drops.
- A code/score pass must not become automatic deployment approval.
- Verify source hashes, reconstruct inputs, replay selected fits, recompute
  proper probability scores, paired uncertainty and cumulative totals.

## How to explain a result

**Mandatory post-test checkpoint:** follow
[the required player walkthrough](required-player-walkthrough.md) after every
model/component test, whether it improves scores or fails. Trace a handful of
players from dated stats through actual model inputs and intermediate forecasts
to reality, including gains, deteriorations, false highs/lows and ordinary cases.
Use outcome-blind comparisons and keep cohort evidence alongside cases. A list
of names/errors is insufficient. Until this is done, the experiment's disposition
is provisional and the next modeling experiment must not begin. Record the
walkthrough status/artifact separately from predictive success. This is now a
required workflow; legacy runners are not claimed to enforce it automatically.

Use this order: what changed; what the experiment can establish; exact matched
effect and uncertainty; baseball/cohort failures; what remains unsupported;
adopt/reject/retain-as-research. Include representative gains and misses. Never
turn a weakly supported negative test into a blanket rejection of an idea, or
a small pooled gain into certification of an integrated player-value model.

For current limitations and permitted next work, see `project-status.md` and
`prospect-model-execution-plan.md`. V11–V16 recent-arrival experiments are
development evidence; V15/V16 long-horizon architecture comparisons have the
documented stage-support limitation. Earlier, unrelated model components have
not been globally recertified by this repair.
