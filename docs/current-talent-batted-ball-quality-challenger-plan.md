# Current Talent batted-ball-quality challenger plan

Last updated: 2026-08-17  
Status: **PREDECLARED DESIGN; deterministic source/request, feature, application, standardization, reconciliation, diagnostics, and residual-fit contracts are implemented. A source-semantic correction was made before any richer development scoring: model BBE are result-producing, non-bunt in-play rows only. Do not bulk-materialize/evaluate MiLB tracking until the tracked-only tiny live-source probe is reverified.**

## Purpose

This is the first richer-evidence Current Talent challenger after the universal results-only Baseline 2 freeze.

It asks one narrow baseball question:

> Among hitters for whom public tracking actually measures batted-ball quality, does pre-cutoff exit-velocity / launch-angle information improve the estimate of present batting talent beyond frozen Baseline 2?

This gate is intentionally narrower than a general Statcast model. It does not add swing decisions, pitch-level shape/location, bat speed, scouting grades, prospect rankings, projection/aging, playing time, defense, or WAR.

## Frozen comparator and fallback

Required comparator: **Baseline 2 `translated_multiseason_recency_empirical_bayes_v1`** from `docs/current-talent-results-only-baseline-freeze.md`.

Do not retune B2 in this gate.

Production architecture is explicitly tiered:

1. every eligible player receives frozen B2 Current Talent;
2. a richer adjustment may be applied only when observed tracking evidence passes the capability and sample rules below;
3. where tracking is structurally unavailable or insufficient, the richer model returns exactly B2 rather than synthetic/imputed Statcast features;
4. richer promotion therefore means validated incremental value on the tracked-evidence tier, not universal tracking availability across affiliated baseball.

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

Reuse the frozen tracked-only request semantics in `src/universal_baseball/current_talent_savant_minors.py`. The manual probe must route through that helper rather than rebuilding an endpoint query independently. Retain exact raw response bytes plus explicit projected schema. Do not build a second identity system.

### Reuse existing MLB source bytes

For MLB, do not redownload Statcast merely for this challenger when certified historical source captures already exist.

The certified 2021–2023 historical MLB Current Talent artifacts retain the exact raw Savant CSV chunks under the historical quarantine/source tree. The richer materializer should reuse those bytes and their provenance. A new network capture is warranted only if a concrete missing-source or source-integrity problem is discovered.

## Capability tiers

Tracking eligibility is determined from observed/certified source capability, not from a blanket `level_group` assumption.

### Eligible historical MiLB capability

- **2021:** observed tracked FSL / Single-A games only;
- **2022:** observed tracked FSL plus observed tracked AAA games returned by the official tracked-data surface; do not mark all AAA as tracked;
- **2023:** observed tracked AAA plus FSL games, consistent with the source checkpoint;
- **AA / High-A / other Single-A / Rookie Complex / DSL:** B2 fallback unless a separate future source gate proves tracking capability.

For 2022 AAA in particular, preserve game/league/venue capability. The probe showed near-complete EV/LA in one AAA environment and only about 20% in another on the checked date, so `AAA` alone is not an acceptable capability flag.

Every model-eligible tracked BBE must reconcile by `game_pk + player_id` to one unambiguous already-certified Current Talent player-game environment. The emitted source-capability tier is descriptive provenance of an observed tracked environment; it is never permission to infer that every game at the same level was tracked.

### MLB

MLB Statcast participates through the repository's existing retained Savant capture/identity path, with the same as-of and measurement-completeness rules. MLB and MiLB capability remain separately reportable.

## Source-semantic correction before development

The first deterministic implementation initially treated every complete `launch_speed + launch_angle` contact row as a batted-ball event and keyed it at `game_pk + batter + at_bat_number`.

Inspection of the **exact retained certified 2021 MLB Savant source bytes**, before any richer development scoring, showed that this is not a defensible BBE definition:

- Savant can expose EV/LA on foul contacts inside a plate appearance;
- many PAs therefore have several complete EV/LA contact rows before the final in-play result;
- the pitch-grain source key is unique, while collapsing complete measurements to PA grain mixes foul contacts with the eventual result-producing ball.

Baseball Savant's standard BBE concept is a batted ball that produces a result. Accordingly, the challenger contract is corrected before development as follows.

### Canonical model BBE

A model-eligible tracked BBE must satisfy all of the following:

1. valid `game_date`, `game_pk`, `batter`, `at_bat_number`, and `pitch_number`;
2. Savant pitch result `type == X` after normalization;
3. nonblank terminal `events`;
4. observed `launch_speed`;
5. observed `launch_angle`;
6. the Savant play narrative does **not** explicitly identify a bunt.

Canonical key:

`game_pk + player_id + at_bat_number + pitch_number`

Fail closed if:

- the canonical pitch key appears more than once among result-producing complete EV/LA rows; or
- one player/PA contains more than one result-producing complete BBE after the filter.

### Why bunts are excluded

The frozen 12-bin Current Talent core profile treats bunt contact separately from the ten modeled non-bunt contact bins. The richer EV/LA residual is only allowed to move those ten non-bunt contact bins. Including bunt EV in the richer feature average would therefore let bunt frequency alter a non-bunt contact-shape estimate.

The same explicit Savant narrative rule already used by the repository's MLB adapter is reused here: an observed play description containing the word `bunt` is excluded from richer BBE evidence.

This is an evidence/target alignment rule, not a fitted feature choice.

### Broad tracking diagnostics remain broader than model BBE

The earlier source probe deliberately used a broad `BBE-like`/contact surface to measure whether tracking values existed. That remains useful for capability and completeness diagnostics and must not be retroactively reinterpreted as the model BBE definition.

Broad source diagnostics therefore operate at pitch grain and may include measured foul/contact rows. Their counts are explicitly named **observations**, not model BBE. Only the stricter result-producing, non-bunt projection enters EV/sweet-spot features or the >=20 richer eligibility threshold.

This source-semantic correction changes neither the predeclared feature family nor the validation protocol and occurred before any 2022 richer development score was observed.

## Observed feature family

The first challenger uses only two player-level summaries derived from **complete observed result-producing, non-bunt EV+LA BBE strictly before the as-of cutoff**:

1. **recency-weighted mean exit velocity**;
2. **recency-weighted sweet-spot share**, launch angle 8 through 32 degrees inclusive.

Both use the same **180-day exponential half-life** as frozen B2. The intent is one contact-speed dimension and one vertical-contact-shape dimension without beginning a broad Statcast feature search.

Do not add hard-hit rate, barrel rate, xwOBA, max EV, EV90, launch-angle SD, bat speed, swing length, or pitch-level swing/chase/whiff features in this gate.

Why not xwOBA/barrels first: they are modeled/composite outcomes of Statcast inputs and can import extra park/league/model assumptions. Raw EV + launch angle are closer to the observed physical evidence.

## Evidence strength / eligibility

Primary richer-evidence eligibility threshold: **at least 20 complete observed result-producing, non-bunt EV+LA BBE before the cutoff**.

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
- broad BBE-like/contact observation count;
- EV+LA completeness among broad source observations;
- source ambiguities/duplicates.

No missing EV or launch angle may be filled from player, league, MLB, or population averages to make a player eligible.

## Modeling form

The richer evidence changes only the **conditional shape of contact** in B2. It cannot alter B2 walk/HBP or strikeout probabilities.

Let the frozen 12-bin B2 profile be separated into:

- `BB_HBP`;
- `K`;
- 10 contact bins: `IFFB` plus Pull/Center/Oppo x OFFB/LD/GB.

For an eligible tracked player:

1. keep `P(BB_HBP)` and `P(K)` exactly at B2;
2. condition the remaining B2 probability mass on a core contact event;
3. adjust the **10-bin conditional contact distribution** with a training-only regularized multinomial residual model using standardized mean EV and sweet-spot share;
4. normalize adjusted 10-bin conditional probabilities to one;
5. multiply by the original B2 contact probability mass;
6. recombine with unchanged BB/HBP and K so the full 12-bin profile sums to one.

Conceptually, for contact bin `j`:

`log(q_richer_j) = log(q_B2_j) + beta_EV_j * z_mean_EV + beta_SS_j * z_sweet_spot`

followed by softmax across the 10 contact bins.

B2 conditional contact shape is the offset/reference, not discarded and refit from scratch.

### Training likelihood and environment translation

Residual coefficients are fit against **future contact outcomes only**, but the likelihood must respect the actual future league environment.

For each training player / realized target environment:

1. condition B2 on the ten contact bins in latent MLB-scale space;
2. add the already-fitted training-only target-level CLR environment effect for each contact bin;
3. renormalize across the ten contact bins;
4. add the EV / sweet-spot residual in latent logit space;
5. score the resulting conditional contact probabilities against future contact-bin counts.

Do not fit directly to raw future contact shares without target-environment translation. That would change the established universal-level observation model rather than isolate the richer evidence family.

The training table must carry/reconcile `as_of_date`, player, realized target environment, B2 latent conditional contact probability, target environment effect, standardized features, future contact counts, and future contact-event denominator. BB/HBP and K counts are excluded from residual coefficient fitting.

### Regularization — frozen before development

Use one shared fixed L2 penalty of **0.01** across all twenty residual coefficients, applied to **mean per-contact negative log likelihood**.

There is **no penalty search** in this challenger. The value is fixed before 2022 development and before any richer held-out score is observed.

Implementation remains dependency-light with a deterministic convex optimizer/backtracking line search. Do not add sklearn/scipy merely for this fit.

## Why this model form

EV/LA is observed conditional on a batted ball. Allowing it to directly move walk or strikeout talent would blur evidence channels and can create selection artifacts.

The conditional-contact residual instead asks whether physical batted-ball evidence improves what B2 already estimates about contact shape. It also directly targets one documented results-only weakness: overly dispersed calibration in several LD/OFFB directional components.

This gate does not claim mean EV / sweet-spot share exhaust the value of batted-ball quality. If they fail this narrow profile test, a later challenger may test a separate contact-quality/value latent target rather than silently changing this protocol.

## Chronology

Use the existing Current Talent as-of semantics and 90-day future event target.

### Training for 2022 development — frozen protocol

Fit feature standardization and residual coefficients from a **single 2021-07-15 training snapshot and its 90-day future outcomes**.

Reasons for one annual training snapshot rather than stacking Jul 15 / Aug 1 / Sep 1 2021:

- the 90-day target windows overlap heavily;
- stacking would count many same future events multiple times;
- Jul 15 is the earliest stable 2021 universal Current Talent validation date with required translation support;
- one fixed annual snapshot avoids hidden weighting choices.

Feature standardization is fit only on richer-eligible 2021-07-15 rows and frozen for all three 2022 development folds. Residual coefficients are fit only from the 2021-07-15 training table. No 2022 future outcomes enter fitting or standardization before development scoring.

### 2022 development folds

Evaluate frozen B2 vs B2+richer on:

- 2022-07-15;
- 2022-08-01;
- 2022-09-01.

Only players meeting the primary >=20 tracked-BBE rule at each cutoff enter the paired richer-evidence comparison. Both models must be scored on the exact same players, target environments, and future events.

Do not use 2023 to choose features, BBE semantics, eligibility threshold, model form, penalty, or promotion decision from development.

### 2023 confirmation

If and only if the fixed challenger passes 2022 development:

- refit the unchanged feature/model form using the union of **2021-07-15 and 2022-07-15** training snapshots/outcomes;
- refit feature standardization only on those training snapshot rows;
- keep L2 = 0.01;
- confirm on 2023-07-15 / 08-01 / 09-01;
- evaluate only fixed challenger vs frozen B2;
- do not search alternate features, BBE semantics, thresholds, penalties, dates, or model forms on 2023.

One July 15 training snapshot per completed season avoids duplicate weighting from overlapping within-season target horizons while allowing confirmation fitting to learn from development-year evidence after the development decision is closed.

The 2023 AAA tracking expansion may increase confirmation coverage but cannot alter the candidate selected from the earlier gate.

## Primary scoring / promotion rule

Primary comparison remains the existing 12-bin future Current Talent profile on the **identical richer-eligible cohort**.

Development passes only if:

1. richer has lower equal-fold mean event-weighted multinomial log loss than B2;
2. richer has no worse equal-fold mean event-weighted multinomial Brier than B2;
3. richer wins log loss in at least 2 of 3 development folds;
4. scored player / target-environment / future-event coverage is identical within each paired comparison;
5. aggregate improvement is not solely an MLB artifact;
6. no meaningfully supported non-MLB capability tier is worse on both proper scores in at least 2 of 3 folds;
7. calibration intercept/slope does not show a broad new failure and all required fits converge.

For the hard non-MLB guardrail, a capability tier is meaningfully supported at **>=1,000 future core events across the three folds**. Lower-support tiers remain diagnostic rather than silently pooled away.

Confirmation requires the same conditions on 2023, including lower equal-fold mean log loss than B2. If confirmation fails, retain B2 and reject this richer challenger without 2023 reselection.

## Additional diagnostics

Always report:

- MLB vs MiLB tracked tiers separately;
- FSL separately;
- 2022 AAA tracked subsets separately from untracked AAA;
- current level / future target level;
- effective B2 results evidence bands;
- tracked-BBE evidence bands;
- broad source measurement completeness;
- players with/without prior MLB evidence;
- each 12-component proper-score contribution;
- conditional-contact 10-bin proper scores;
- calibration intercept/slope/ECE where supported;
- feature distributions and missingness/completeness by source capability tier.

A large aggregate gain caused by one tracked environment while another adequately supported tracked environment degrades materially is not a broadly transportable richer-tier win.

## Universal production behavior

Even if the richer challenger passes:

- tracked-capability players with sufficient pre-cutoff evidence receive B2+richer;
- players without sufficient/structurally available tracking remain exactly B2;
- outputs expose `current_talent_method`, source capability, raw/effective tracked BBE, and fallback reason;
- the system never presents imputed lower-level EV/LA as observed evidence.

This preserves a universal MLB-through-affiliated-minors ranking surface while allowing higher-resolution evidence where public data genuinely supports it.

## Implementation / source sequence

Proceed in small gates:

1. **DONE — request semantics:** tracked-only Minor Savant helper is frozen/tested; bounded request-chunk planning exists for later materialization.
2. **DONE — source-semantic correction:** canonical model BBE is result-producing (`type=X`, terminal event), complete EV+LA, non-bunt, pitch-grain; measured fouls remain source diagnostics only.
3. **DONE — deterministic projection/features:** 180-day mean EV / sweet-spot share, evidence counts, cutoff exclusion, and B2 fallback are implemented/tested.
4. **DONE — source reconciliation/diagnostics:** observed tracked BBE must map to certified game/player environment; broad tracking completeness remains separate and pitch-grain.
5. **DONE — residual application/training contract:** contact-only application, training-only standardization, target-environment-aware training table, fixed-penalty fitter, and deterministic tests are implemented.
6. **NEXT — tiny tracked-only MiLB source recheck:** rerun the existing manual Minor Savant probe through the frozen tracked request helper. Retain raw bytes and capability diagnostics. The workflow first runs all deterministic richer-source/model tests. Do not bulk-materialize MiLB if this fails or materially changes source capability.
7. **MLB reuse path:** derive MLB EV/LA from retained certified historical MLB Savant source bytes; do not issue redundant MLB source requests.
8. Only after the MiLB recheck passes, materialize the minimum 2021–2022 tracked evidence needed for the fixed 2021 training snapshot plus three 2022 development folds.
9. Run 2022 development and persist the checkpoint before any 2023 challenger evaluation.
10. If development passes, refit on fixed annual training snapshots and run fixed 2023 confirmation once; freeze/reject accordingly.

Do not bulk-download Minor Savant before the tracked-only source recheck and corrected deterministic contract are both green.

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
