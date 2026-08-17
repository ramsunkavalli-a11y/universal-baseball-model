# Current Talent batted-ball-quality challenger plan

Last updated: 2026-08-17  
Status: **PREDECLARED DESIGN; do not bulk-materialize or evaluate the challenger until deterministic implementation/source checks pass.**

## Purpose

This is the first richer-evidence Current Talent challenger after the universal results-only Baseline 2 freeze.

It asks one narrow baseball question:

> Among hitters for whom public tracking actually measures batted-ball quality, does pre-cutoff exit-velocity / launch-angle information improve the estimate of present batting talent beyond frozen Baseline 2?

This gate is intentionally narrower than a general Statcast model. It does not add swing decisions, pitch-level shape/location, bat speed, scouting grades, prospect rankings, projection/aging, playing time, defense, or WAR.

## Frozen comparator and fallback

Required comparator: **Baseline 2 `translated_multiseason_recency_empirical_bayes_v1`** from `docs/current-talent-results-only-baseline-freeze.md`.

Do not retune B2 in this gate.

Production architecture is explicitly tiered:

1. every eligible player receives the frozen B2 Current Talent estimate;
2. a richer adjustment may be applied only when observed tracking evidence passes the capability and sample rules below;
3. where tracking is structurally unavailable or insufficient, the richer model must return exactly the B2 estimate rather than synthetic/imputed Statcast features;
4. richer-model promotion therefore means "validated incremental value on the tracked-evidence tier," not a claim that tracking is universally available across affiliated baseball.

## Proven source capability

Use the official Baseball Savant Minor League Statcast detail CSV already certified by `docs/current-talent-savant-minors-source-checkpoint.md`.

The source probe established:

- direct `game_pk + batter` reconciliation to the existing MLBAM/player-game backbone;
- historical EV (`launch_speed`) and launch angle (`launch_angle`) availability;
- 2021 tracked MiLB evidence in the Florida State League;
- 2022 tracked evidence in the FSL plus only part of AAA coverage;
- 2023 tracked evidence in all AAA plus the FSL;
- structural rather than random missingness by league/venue;
- no defensible historical bat-tracking data merely from modern column names.

Reuse the proven request/filter semantics documented in that checkpoint. Retain exact raw response bytes plus an explicit projected schema. Do not build a second identity system.

## Capability tiers

Tracking eligibility is determined from observed/certified source capability, not from a blanket `level_group` assumption.

### Eligible historical MiLB capability

- **2021:** observed tracked FSL / Single-A games only;
- **2022:** observed tracked FSL plus observed tracked AAA games returned by the official tracked-data surface; do not mark all AAA as tracked;
- **2023:** observed tracked AAA plus FSL games, consistent with the source checkpoint;
- **AA / High-A / other Single-A / Rookie Complex / DSL:** B2 fallback unless a separate future source gate proves tracking capability.

For 2022 AAA in particular, preserve game-level/league/venue capability. The probe showed near-complete EV/LA in one AAA environment and only about 20% in another on the checked date, so `AAA` alone is not an acceptable capability flag.

### MLB

MLB Statcast may participate through the repository's existing Savant capture/identity path, provided the same as-of, raw-byte retention, and measurement-completeness rules are enforced. MLB and MiLB capability must remain separately reportable.

## Observed feature family

The first challenger uses only two player-level batted-ball-quality summaries derived from **complete observed EV + launch-angle batted balls strictly before the as-of cutoff**:

1. **recency-weighted mean exit velocity**;
2. **recency-weighted sweet-spot share**, where sweet spot is launch angle from 8 through 32 degrees inclusive.

Both use the same **180-day exponential half-life** as frozen B2. The intent is to capture one speed dimension and one vertical-contact-shape dimension without beginning a broad Statcast feature search.

Do not add hard-hit rate, barrel rate, xwOBA, max EV, EV90, launch-angle standard deviation, bat speed, or pitch-level features in this gate. They may become later challengers only after this one is resolved.

Why not xwOBA/barrels first: those are already modeled/composite outcomes of Statcast inputs and can import park/league/model assumptions that make attribution harder. Raw EV + launch angle are closer to the observed physical evidence.

## Evidence strength / eligibility

Primary richer-evidence eligibility threshold: **at least 20 complete tracked EV+LA batted balls before the cutoff**.

This is a predeclared gate threshold, not a claim that 20 is globally optimal or fully stabilized.

Report, but do not select the model from, sensitivity cohorts at:

- >=10 complete tracked BBE;
- >=20 complete tracked BBE (primary);
- >=30 complete tracked BBE.

Also report:

- raw complete tracked BBE;
- recency-effective complete tracked BBE;
- source capability tier;
- tracked-game count;
- observed EV+LA completeness among BBE-like rows.

No missing EV or launch angle may be filled from player, league, MLB, or population averages to make a player eligible.

## Modeling form

The first challenger changes only the **conditional shape of contact** in B2. It does not allow EV/LA to alter the player's B2 walk/HBP or strikeout probabilities.

Let the frozen 12-bin B2 profile be separated into:

- `BB_HBP`;
- `K`;
- 10 contact bins: `IFFB` plus Pull/Center/Oppo x OFFB/LD/GB.

For an eligible tracked player:

1. keep `P(BB_HBP)` and `P(K)` exactly at their B2 values;
2. condition the remaining B2 probability mass on a core contact event;
3. adjust the **10-bin conditional contact distribution** with a training-only regularized multinomial residual model using standardized mean EV and sweet-spot share;
4. normalize the adjusted 10-bin conditional probabilities to one;
5. multiply them by the original B2 contact probability mass;
6. recombine with unchanged B2 `BB_HBP` and `K` so the full 12-bin profile again sums to one.

Conceptually, for contact bin `j`:

`log(q_richer_j) = log(q_B2_j) + beta_EV_j * z_mean_EV + beta_SS_j * z_sweet_spot`

followed by a softmax across the 10 contact bins.

The B2 conditional contact profile is therefore an offset/reference, not discarded and refit from scratch.

### Regularization

Use one shared L2 penalty across all residual coefficients. Before any held-out evaluation, compare only a very small training-only penalty set if needed for numerical stability; if a penalty search is required, it must be predeclared and selected strictly inside training data. Do not use 2022 development or 2023 confirmation outcomes to choose the penalty after seeing challenger scores.

Prefer the simplest dependency-light implementation compatible with the repository. `pyproject.toml` currently has no sklearn/scipy runtime dependency, so do not add a large modeling dependency without first showing it materially reduces implementation risk versus a small deterministic optimizer.

## Why this model form

EV/LA is observed **conditional on a ball being put in play/contact being measured**. Allowing it to directly move walk or strikeout talent would blur evidence channels and can create selection artifacts.

The conditional-contact residual form instead tests whether physical contact evidence improves what B2 already estimates about contact shape. It also directly targets one documented weakness of the results-only models: overly dispersed calibration in several LD/OFFB directional components.

This gate does not claim mean EV / sweet-spot share exhaust the value of batted-ball quality. If they fail this narrow profile test, a later challenger may test a separate contact-quality/value latent target rather than silently changing this protocol.

## Chronology

Use the existing Current Talent as-of semantics and 90-day future event target.

### Training for 2022 development

Fit feature standardization and residual coefficients using only eligible **2021** tracked-evidence snapshots/outcomes available under the existing chronological validation rules.

A shared residual relationship may be learned across MLB and tracked MiLB rows, but capability tier/level must be retained for diagnostics. The model may not learn 2022 coefficients from the same 2022 future outcomes on which it is evaluated.

### 2022 development folds

Evaluate frozen B2 versus B2+richer on:

- 2022-07-15;
- 2022-08-01;
- 2022-09-01.

Only players meeting the primary >=20 tracked-BBE rule at each cutoff enter the **paired richer-evidence comparison**. Both B2 and richer must be scored on the exact same players, target environments, and future events.

Do not use 2023 to choose features, eligibility threshold, model form, or promotion decision from development.

### 2023 confirmation

If and only if the fixed challenger passes the 2022 development gate:

- refit the same frozen model form using eligible 2021-2022 training history only;
- confirm on 2023-07-15 / 2023-08-01 / 2023-09-01;
- evaluate only the fixed challenger versus frozen B2;
- do not search alternate features, thresholds, or model forms on 2023.

The expansion of AAA tracking in 2023 may increase confirmation coverage, but it must not alter the candidate selected from the earlier gate.

## Primary scoring / promotion rule

The primary comparison remains the existing 12-bin future Current Talent profile on the **identical richer-eligible cohort**.

Development passes only if:

1. richer has lower equal-fold mean event-weighted multinomial log loss than B2;
2. richer has no worse equal-fold mean event-weighted multinomial Brier score than B2;
3. richer wins log loss in at least 2 of 3 development folds;
4. scored player / target-environment / future-event coverage is identical within each paired comparison;
5. aggregate improvement is not solely an MLB artifact;
6. no meaningfully supported non-MLB capability tier is worse on both proper scores in at least 2 of 3 folds;
7. calibration intercept/slope does not show a broad new failure and all required fits converge.

For the hard non-MLB guardrail, call a capability tier meaningfully supported when it contributes at least **1,000 future core events across the three folds**. Lower-support tiers remain diagnostic rather than silently pooled away.

Confirmation requires the same conditions on 2023, including a lower equal-fold mean log loss than B2. If confirmation fails, retain B2 for all players and reject this richer challenger without reselection on 2023.

## Additional diagnostics

Always report:

- MLB versus MiLB tracked tiers separately;
- FSL separately;
- 2022 AAA tracked subsets separately from untracked AAA;
- current level / future target level;
- effective B2 results evidence bands;
- tracked-BBE evidence bands;
- players with/without prior MLB evidence;
- each of the 12 component proper-score contributions;
- conditional-contact (10-bin) proper-score diagnostics;
- calibration intercept/slope/ECE by component where supported;
- feature distributions and missingness/completeness by source capability tier.

A large aggregate gain caused by one tracked environment while another adequately supported tracked environment degrades materially does not qualify as a broadly transportable richer tier.

## Universal production behavior

Even if the richer challenger passes:

- players in tracked capability with sufficient pre-cutoff evidence receive B2+richer;
- players without sufficient or structurally available tracking remain exactly B2;
- outputs expose `current_talent_method`, richer-source capability, raw/effective tracked BBE, and fallback reason;
- the system must never present an imputed lower-level EV/LA feature as observed evidence.

This preserves a universal MLB-through-affiliated-minors ranking surface while allowing higher-resolution evidence where the public data genuinely supports it.

## Implementation / source sequence

Proceed in small gates:

1. **Request parity check:** compare the repository's thin Minor League Savant request against the proven public `baseball-stats-python` tracked-request semantics on tiny dates; freeze request fields/filters.
2. **Deterministic EV/LA projection:** add a canonical tracked-BBE table with explicit capability and raw completeness diagnostics; test identity, BBE definition, EV/LA completeness, duplicate pitch/contact keys, and strict pre-cutoff filtering.
3. **Feature builder:** implement 180-day recency-weighted mean EV / sweet-spot share plus evidence counts; test no future leakage and exact B2 fallback below threshold.
4. **Residual model:** implement/train the conditional-contact adjustment and tests proving BB/HBP and K remain exactly B2 while 10 contact bins normalize correctly.
5. Only after those pass, materialize the minimal 2021-2022 source needed for the predeclared development folds.
6. Run 2022 development; persist checkpoint before any 2023 challenger evaluation.
7. If development passes, run the fixed 2023 confirmation once and freeze/reject accordingly.

Do not bulk-download all Minor League Savant data before the deterministic source/feature contract passes.

## Explicitly deferred

Not part of this gate:

- hard-hit / barrel / xwOBA composites;
- EV90 / max EV;
- pitch-level swing/chase/whiff models;
- bat speed or swing length;
- scouting grades / public prospect rankings;
- component-specific results-only retuning;
- aging/development Projection;
- playing time / role;
- defense;
- WAR / final ranking.
