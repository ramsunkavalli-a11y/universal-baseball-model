# Current Talent batted-ball-quality challenger plan

Last updated: 2026-08-17  
Status: **PREDECLARED DESIGN; deterministic source/request, feature, application, standardization, and residual-fit contracts are implemented. Do not bulk-materialize or evaluate the challenger until the tracked-only tiny live-source probe is reverified.**

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

Reuse the frozen tracked-only request semantics in `src/universal_baseball/current_talent_savant_minors.py`. The manual probe script must route through that helper rather than rebuilding an endpoint query independently. Retain exact raw response bytes plus an explicit projected schema. Do not build a second identity system.

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

### Training likelihood and environment translation

Residual coefficients are fit against **future contact outcomes only**, but the likelihood must respect the actual future league environment.

For each training player / realized target environment:

1. condition B2 on the ten contact bins in latent MLB-scale space;
2. add the already-fitted training-only target-level CLR environment effect for each contact bin;
3. renormalize across the ten contact bins;
4. add the EV / sweet-spot residual in latent logit space and score the resulting conditional contact probabilities against future contact-bin counts.

Do not fit directly to raw future contact shares without the target-environment translation. That would change the established universal-level observation model rather than isolate the richer evidence family.

The training table must carry and reconcile `as_of_date`, player, realized target environment, B2 latent conditional contact probability, target environment effect, standardized features, future contact counts, and future contact-event denominator. BB/HBP and K counts are excluded from the residual coefficient fit.

### Regularization — frozen before development

Use one shared fixed L2 penalty of **0.01** across all twenty residual coefficients, applied to **mean per-contact negative log likelihood**.

There is **no penalty search** in this challenger. The value is fixed before 2022 development and before any richer held-out scores are observed. This avoids turning regularization into another development hyperparameter while providing mild identification/stability control for the multinomial residual.

The implementation remains dependency-light and uses a deterministic convex optimizer with backtracking line search. Do not add sklearn/scipy merely for this fit.

## Why this model form

EV/LA is observed **conditional on a ball being put in play/contact being measured**. Allowing it to directly move walk or strikeout talent would blur evidence channels and can create selection artifacts.

The conditional-contact residual form instead tests whether physical contact evidence improves what B2 already estimates about contact shape. It also directly targets one documented weakness of the results-only models: overly dispersed calibration in several LD/OFFB directional components.

This gate does not claim mean EV / sweet-spot share exhaust the value of batted-ball quality. If they fail this narrow profile test, a later challenger may test a separate contact-quality/value latent target rather than silently changing this protocol.

## Chronology

Use the existing Current Talent as-of semantics and 90-day future event target.

### Training for 2022 development — frozen protocol

Fit the feature standardization and residual coefficients from a **single 2021-07-15 training snapshot and its 90-day future outcomes**.

Reasons for using one annual training snapshot rather than stacking the July 15 / August 1 / September 1 2021 targets:

- the three 90-day target windows overlap heavily;
- stacking them would count many of the same future events multiple times in the residual likelihood;
- July 15 is already the earliest stable 2021 universal Current Talent validation date with the required translation support;
- a single fixed annual snapshot keeps the richer fit interpretable and prevents hidden weighting choices.

Feature standardization is fit only on richer-eligible 2021-07-15 rows and then frozen for all three 2022 development folds. Residual coefficients are fit only from the 2021-07-15 training table. No 2022 future outcomes enter coefficient fitting or standardization before development scoring.

### 2022 development folds

Evaluate frozen B2 versus B2+richer on:

- 2022-07-15;
- 2022-08-01;
- 2022-09-01.

Only players meeting the primary >=20 tracked-BBE rule at each cutoff enter the **paired richer-evidence comparison**. Both B2 and richer must be scored on the exact same players, target environments, and future events.

Do not use 2023 to choose features, eligibility threshold, model form, penalty, or promotion decision from development.

### 2023 confirmation

If and only if the fixed challenger passes the 2022 development gate:

- refit the same unchanged feature/model form using the union of the **2021-07-15 and 2022-07-15** training snapshots/outcomes;
- refit feature standardization only on those training snapshot rows;
- use the same fixed L2 penalty = 0.01;
- confirm on 2023-07-15 / 2023-08-01 / 2023-09-01;
- evaluate only the fixed challenger versus frozen B2;
- do not search alternate features, thresholds, penalties, training dates, or model forms on 2023.

Using one July 15 training snapshot per completed season avoids duplicate weighting from overlapping within-season target horizons while allowing the confirmation fit to learn from development-year evidence after the development decision is closed.

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

1. **DONE — request semantics:** thin tracked-only Minor League Savant helper is frozen and unit-tested.
2. **DONE — deterministic EV/LA projection:** canonical complete tracked BBE grain and strict no-imputation behavior are implemented/tested.
3. **DONE — feature builder:** 180-day recency-weighted mean EV / sweet-spot share, evidence counts, cutoff exclusion, and B2 fallback are implemented/tested.
4. **DONE — residual application / training contract:** contact-only application, training-only standardization, target-environment-aware training table, fixed-penalty residual fitter, and deterministic tests are implemented.
5. **NEXT — tiny tracked-only source recheck:** rerun the existing manual Minor Savant probe after routing it through the frozen tracked request helper. Retain raw bytes and capability diagnostics; do not bulk-materialize if this fails or materially changes the certified source picture.
6. Only after that passes, materialize the minimum 2021-2022 tracked evidence needed for the fixed 2021 training snapshot plus three 2022 development folds.
7. Run 2022 development; persist checkpoint before any 2023 challenger evaluation.
8. If development passes, refit on the fixed annual training snapshots and run the fixed 2023 confirmation once; freeze/reject accordingly.

Do not bulk-download all Minor League Savant data before the tiny tracked-only source recheck and deterministic contract are both green.

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
