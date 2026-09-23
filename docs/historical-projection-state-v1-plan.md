# Historical projection-state archive: fixed reconstruction

2026-09-23. Freeze before reconstruction. This is an input/archive milestone,
not a candidate-selection experiment, forecast upgrade or completed career simulator.
Follow `projection-path-anchor-rebuild-checklist.md`.

## Scope and recipes

Retain the complete starting population for origins 2012–19, 2021, 2022 and 2025,
with separate Years 1–3 records. Backfill 2012–15; reuse verified later archives.
Do not invent 2009–11 forecasts, a 2020 origin, or outcomes after 2025.
Historical coefficients are refitted at their own cutoff, using the frozen current
recipe. These are retrospective out-of-time forecasts, not forecasts actually
published in those years; recipe choices used already-exposed development data.

Reconstruct the delivered opportunity recipe: PT_FORM_U hurdle model, with the
accepted established-MLB participation-only logistic update (C=1, seed 417) and
the C2 never-debuted rookie-ball correction. Preserve its positive-count mean;
do not substitute the rejected Poisson workload update. The rookie correction
uses the unchanged level/age prior of strength 100 and its LightGBM conditional
PA/rate heads (seeds 417/427, balanced settings, PA-weighted rate, original clips).
All these opportunity/head training windows exclude pandemic-crossing paths.

For unrepaired mean value before 2016, reproduce the existing fixed_mean recipe:
Year 1 base-feature Ridge fallback; Years 2/3 full-77-feature Ridge, alpha 20.
The rich panel starts in 2015, so none of the backfill origins has the two earlier
rich origins required for the modern Year-1 stack. Reuse later delivered means,
retaining per-player Year-1 feature-coverage labels. Apply only the existing C2
scope to form the retrospective current-recipe value. Raw early means must match
the already archived quantile-file mean column, not its quantiles.

Keep three different rate/value objects separate:

- the independently fitted, vintage H1 conditional rate anchor (existing seed-417
  recipe; its original training rule includes known pandemic outcomes);
- the horizon-specific conditional rate head from the rookie correction (research
  input outside its accepted rookie scope, never called universal latent talent);
- unconditional delivered batting/replacement value, including zero-play cases.

Never infer hitting talent from expected value / expected PA. Conditional PA may
be recovered from the documented identity expected PA = participation × positive
PA, where archived component means were not saved. Mark that provenance. Zero
participation with positive expected PA is an error, not a number to patch.

## Reconstruction checks before backfill

Refit opportunity and rookie PA/rate heads at 2016 and 2022, each horizon; refit
H1 anchors at both origins. Compare keyed output to the immutable archives at
rtol=1e-7, atol=1e-7. Refit the unrepaired 2016 value baseline; later rich-stack
means are reused, not falsely claimed to be independently refitted. Stop on a
substantive mismatch. Any necessary correction must be documented separately.

Backfill H1 anchors must reproduce their existing 2012–15 archive. Backfill raw
means must reproduce existing means on each horizon. No tuning or accuracy-based
choice of reconstruction. Rebuild all 12 early origin/horizon cells if checks pass.
The stronger five-member PA ensemble remains an archived outer comparator; it is
not relabeled as delivered or silently converted to a coherent conditional mean.
It is not backfilled in this bounded accepted-recipe reconstruction.

## Safety and completion

Freeze source/code hashes and model versions before running. Save training row,
active-player and origin counts, latest label years, missingness and clipping
counts. All joins are keyed and validated. No-play, inactive and never-debuted
rows remain; missing/unobserved rates remain null, never zero talent.
The value-label year is a conservative certified upper bound for reused rich
stacks, not a claim that every submodel used a label in that year. Reused inputs
and cached mean files are hashed too.

Test future-label and future-predictor mutation at the 2016 cutoff: alter only
information unavailable then, refit and require unchanged results. Test the H1
anchor and the horizon-specific opportunity/rate path. Also test malformed keys,
future vintages, absent rate observations, and population/PA product identities.

Build a separately labeled residual ledger from observed complete outcomes and
the archived unconditional forecasts. Actual active-player rates are null at
zero PA. Entire residual vectors must mature before a later fit cutoff; filter
pandemic paths for the normal-path inventory. This ledger describes realized
outcome errors, not latent-talent changes or an accepted joint distribution.

Inventory eligible support at cutoffs 2012–16, 2019, 2021, 2022 and 2025; include
age/stage cells, never-debuted, recent-debut and young brief-MLB (age <=23, 1–99 PA)
groups. Weight identities equally over eligible snapshots, separately at each
cutoff; exclude a future query identity when computing its own donor pool.
Report counts without using newly scored outcomes to choose an architecture.

Stop with the verified archive, source/coverage report and C1 readiness decision.
No new path model is fitted in this milestone: it needs a separate numeric
contract for dependence, opportunity transitions, development and persistent
uncertainty. Archive readiness alone is not predictive validation. Live forecasts,
the explorer, six-year control/dollar outputs and protected 2026 results stay fixed.
