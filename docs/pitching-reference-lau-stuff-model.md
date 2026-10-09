# Lau Sze Yui pitching model reference

Saved 2026-10-08 for the later pitching review. The user supplied
[Lau's March 11 2026 thread](https://x.com/903124S/status/2031762564062036010).
Its useful contribution is a warning about selection bias and a simple physical
baseline to compare with flexible pitch models. It does not establish an
improvement in UBM projections and does not change the hitter work plan.

## Ideas from the thread

MLB survivors with weaker physical pitches may compensate with command. A
comparison across pitchers can therefore mix pitch quality with survival and
other abilities. Lau suggests examining velocity differences within the same
pitcher, following the Tango example he links. That reduces between-pitcher
confounding but does not automatically isolate a causal velocity effect.
[Selection discussion](https://x.com/903124S/status/2031762567153254546),
[within-pitcher proposal](https://x.com/903124S/status/2031762570257084880).

His proposed simpler model judges speed and spin relative to expectations for
pitch shape. Spin relationships vary across pitch families, especially changeups.
He describes an empirical-Bayes linear approach by pitch type and explicitly
assumes speed drives the speed/spin correlation in that simplified construction.
That assumption needs testing rather than adoption as a physical fact.
[Shape-relative proposal](https://x.com/903124S/status/2031762578628870369),
[estimation and assumption](https://x.com/903124S/status/2031762583934632439).

He also asks how pitch type, starter/reliever role, sample size and rating units
should enter a stuff model, and how pitch run value connects to actual pitcher
results. His illustrated 2023–2025 results are explicitly beta. The charts and
quoted formula have not been independently reconstructed here.
[Beta caveat](https://x.com/903124S/status/2031762586467987862),
[type and role](https://x.com/903124S/status/2031762589785661673),
[sample size and value](https://x.com/903124S/status/2031762592327463210).

## How this could help UBM later

The following are UBM hypotheses, not findings from this thread or approved tests:

- Keep a transparent velocity/movement/pitch-type baseline beside any tree-based
  stuff model. Separate physical quality, location/control, usage and role;
  do not assume a score trained on pitch outcomes is pure physical talent.
- Compare within-pitcher changes as well as differences between pitchers.
  Account for pitch type, count, location, handedness, opponents, role and time
  where measured. Within-pitcher variation still mixes fatigue, injury,
  deliberate intent and other changes, so it is not automatically causal.
- Shrink sparse pitch-family evidence and check both established MLB pitchers
  and young entrants. Future MLB talent, participation/role, workload and
  delivered value need separate evaluation; explaining past pitch run values
  is not sufficient for the project's player-value goal.
- Audit actual historical tracking coverage first. Use tracking only where
  certified, retain the all-level component baseline, and compare additions on
  identical people and outcomes. No missing velocity/spin becomes observed
  average stuff, and tracked survivors must not silently define all prospects.

The [earlier pitching checkpoint](current-pitcher-ranking-checkpoint.md)
identified missing velocity, shape, mix and location as limits of its aggregate
pitch-call layer. That is a useful connection, not a current source inventory
or proof that the same pipeline remains selected. Before any experiment, review
the actual current pitcher construction, existing tests and coverage, then
freeze one comparison under the methodological and player-walkthrough gates.
Do not restart the old contact-bin/regression searches from this reference.

This note captures the thread's textual argument through its concluding post;
it does not reproduce all charts, assess every reply, endorse its coefficients,
or adopt a new pitching direction.
