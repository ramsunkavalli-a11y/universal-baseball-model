# Projection v1 methodology review

Last updated: 2026-08-17

Status: **REVIEW COMPLETE — academic + practitioner design implications frozen before Projection model scoring.**

## Question

Before fitting the first age/development Projection model, what does relevant baseball projection work plus longitudinal/compositional modeling literature imply for a transparent v1 design?

This review is intentionally narrow. It is not permission to add tracking, scouting, playing time, future level, or a high-capacity machine-learning model.

## Academic / general-method sources reviewed

### Baseball prediction / aging

1. Jensen, McShane & Wyner (2009), **Hierarchical Bayesian Modeling of Hitting Performance in Baseball**, arXiv:0902.1360.
   - Models future hitting from past performance plus age/context.
   - Uses smooth age trajectories and hierarchical information sharing to avoid unstable player-by-player fits.
   - Evaluates on a held-out future season.

2. Nguyen & Matthews (2024 revision), **Filling the Gaps: A Multiple Imputation Approach to Estimating Aging Curves in Baseball**, arXiv:2210.02383.
   - Treats player dropout / unobserved seasons as a missing-data problem.
   - Shows that aging curves estimated only from observed survivor seasons can be biased.

3. Schuckers, Lopez & Macdonald (2023 revision), **What does not get observed can be used to make age curves stronger**, arXiv:2110.14017.
   - Emphasizes that age affects both performance and whether opportunity is observed.
   - Simulation results favor methods that account for player skill and the observation/selection process.

4. Lee (2026), **Modelling Athletic Ageing Relative to an Estimated Performance Envelope**, arXiv:2608.06635. Recent preprint; used as a caution, not a governing method.
   - Sparse athletic careers limit the individual aging parameters that can be identified reliably.
   - Supports hierarchical population-level aging structure over rich player-specific timing/tempo models when trajectories are short.

### General longitudinal / compositional methods

5. Egozcue, Pawlowsky-Glahn, Mateu-Figueras & Barceló-Vidal (2003), **Isometric Logratio Transformations for Compositional Data Analysis**, Mathematical Geology 35:279–300.
   - ILR maps a composition from the simplex to an orthonormal Euclidean coordinate system while preserving compositional geometry.

6. Sørensen, Walhovd & Fjell (2020), **A recipe for accurate estimation of lifespan brain trajectories, distinguishing longitudinal and cohort effects**, NeuroImage 117596.
   - Longitudinal change should be modeled with smooth functions rather than arbitrary single-age cells or rigid high-order polynomials.
   - Flexible smooth trajectories are useful when change is nonlinear and repeated observations are sparse/irregular.

## Practitioner / public baseball-modeling pass

The practitioner pass was added before any Projection candidate scoring after an initial review leaned too heavily on academic work.

### Tom Tango / MARCEL / projection evaluation

MARCEL is intentionally simple: recent performance weighted more heavily, regression toward the mean, and an age adjustment. Its enduring competitiveness is a warning against adding complexity without demonstrated out-of-time value.

Tango-style forecast evaluation also reinforces three rules already compatible with this project:

- evaluate batting **rates separately from playing time**;
- neutralize or explicitly control league/run-environment assumptions when comparing forecast skill;
- weight errors by realized opportunity while keeping the skill and opportunity estimands separate.

### Jordan Rosenblum / OOPSY

OOPSY begins from the MARCEL family but adds league/level translations, recency weighting, statistic-specific regression, aging, park/run-environment adjustments, and newer process metrics only where they demonstrate value.

Most relevant design lessons:

- regression strength should reflect information quality rather than be identical for every statistic;
- age relative to level is useful context in prospect forecasting;
- component statistics can have genuinely different aging shapes/peak timing;
- generic population aging can remain competitive without forcing bespoke comparable-player aging curves;
- minor- and major-league evidence should first be placed onto a common competitive scale.

For this project, frozen Current Talent B2 already performs the recency/regression/common-scale work. Projection should therefore model incremental movement around B2 rather than recreate OOPSY end-to-end.

### Chris Mitchell / KATOH

KATOH is especially relevant because it asked what minor-league information actually predicts later major-league success rather than assuming every familiar statistic carries equal signal.

Important findings for our architecture:

- age matters more in the low minors than in the high minors;
- the predictive value of component statistics changes by level (for example, K% was much more informative than BB% for low-minors hitters in Mitchell's historical tests);
- being young for one's level contains real information;
- reliability and proximity to MLB matter when interpreting minor-league samples.

This strengthens the decision to retain **as-of level** in the candidate family and to make level-stratified validation a hard diagnostic. It does **not**, by itself, justify a large age × level interaction model once frozen B2 talent is already conditioned on age/current level.

### Clay Davenport / translations and component aging

Davenport's minor-league translations emphasize placing performance from different leagues onto a common standard before interpreting future value. His peak translations also recognize that offensive components do not age at identical rates, so a player's aggregate peak can differ according to skill mix.

That maps naturally onto our 12-component profile: v1 should permit different ILR coordinates/components to move differently with age rather than impose one scalar aging adjustment on total offense.

### ZiPS / Dan Szymborski and PECOTA lineage

ZiPS separates a present baseline estimate from future trajectory, then uses large historical cohorts of similar players to inform aging. PECOTA similarly combines a regressed baseline with career-path/comparable information.

Those systems justify a future comparable/hierarchical challenger, but not necessarily v1. With only three authorized development target seasons and a strong universal B2 starting state, bespoke player-level comparable aging is intentionally deferred until the simple pooled adjustment is tested.

### Steamer / Jared Cross

The Steamer/MARCEL tradition reinforces the value of a strong simple baseline: recent evidence, regression, age, then rigorous testing. Complexity is not assumed to improve forecast accuracy.

This supports keeping v1 incremental and interpretable rather than replacing frozen B2 with a second broad projection engine.

### Ariel Cohen / ATC

ATC's success is a reminder that model diversity can be valuable and that weighted ensembles can outperform any single system. Ensemble construction is not part of Projection v1, because we do not yet have multiple independently validated internal projection models. It is retained as a later option if genuinely different validated challengers exist.

### Derek Carty / THE BAT X

THE BAT X's public development process is useful methodologically: candidate process/Statcast features are screened for **stability, predictive value, aging behavior, and incremental value** before being blended into the production projection.

This is the standard we should use if/when richer process evidence enters Projection later. A descriptive expected statistic is not automatically a projection feature.

### Alex Chamberlain

Chamberlain's work on expected statistics provides an important caution. Hitter xwOBA can carry more forward-looking signal than raw wOBA, but the simple `wOBA - xwOBA` residual itself showed little general predictive usefulness in his out-of-sample half-season tests.

This supports two project decisions:

- do not treat an actual-minus-expected residual as an automatic "luck correction" feature;
- require genuinely independent out-of-time improvement before process residuals enter Projection.

This is particularly relevant after the richer Current Talent contact-value residual failed its own confirmation gate.

### Eli Ben-Porat

Ben-Porat's minor-league pitch-by-pitch work shows that granular public MiLB data can contain predictive signal unavailable in aggregate outcomes, but also that source quality, era, level, and sample size determine how much confidence is warranted.

The transferable principle is **use the richest reliable evidence actually supported by the source, and validate that signal against future MLB outcomes**. Do not force granular features into levels/eras where the collection quality cannot support them.

### Max Bay / Stuff+ work

The Stuff+/pitch-modeling tradition is not directly a batting-rate aging model, but it demonstrates a useful projection principle: upstream physical/process variables can stabilize more quickly and predict future outcomes better than noisy realized results when the model isolates a repeatable skill.

For this project that argues for a later process-feature challenger, not for adding pitch-model-like complexity to results-only Projection v1.

### Cameron Grove / PitchingBot

PitchingBot makes the same principle explicit: removing downstream outcome noise can produce more stable estimates of underlying process, and distinct information sources can be more valuable when combined than multiple estimators built from essentially the same outcomes.

That reinforces a modular future architecture: Current Talent/results, process/tracking, Projection/aging, and opportunity should remain separable channels whose incremental information is tested rather than blended by assumption.

### Lau Sze Yui

Public work located in this pass is primarily sports-physics / tracking / broader sports analytics rather than a directly documented baseball player-performance projection system. The useful methodological lesson is cross-domain rather than a specific aging formula: model the physical/process mechanism where the data support it, but do not manufacture a direct Projection-v1 feature merely to include a sophisticated method.

## Binding implications for Projection v1

### 1. Start from frozen Current Talent; do not rebuild player skill

Frozen Current Talent Baseline 2 already performs recency weighting, environment translation, and empirical-Bayes shrinkage. Projection v1 therefore models a **population expected one-year movement around that state**, not a second full player-talent model.

The player-specific current profile enters as the starting composition. V1 will not fit player-specific aging slopes, latent timing parameters, comparable-player clusters, or hidden states.

### 2. Model the 12-component profile as a composition

The 12 probabilities sum to one, so independent additive probability changes are not coherent.

Projection v1 will represent the profile in a fixed **11-dimensional ILR basis**, estimate a one-year delta there, and invert the ILR transform back to a valid probability composition.

This replaces the earlier tentative CLR wording for the Projection adjustment only. Existing Current Talent environment translation remains frozen on its CLR contract; the two representations are mathematically compatible through the probability composition and no Current Talent translation parameter is changed.

### 3. Use a smooth, low-dimensional population age function

Do not estimate one independent adjustment for every integer age. Do not fit high-order polynomials.

The first candidate family will use a continuous piecewise-linear age basis with ridge shrinkage. This gives a smooth pooled trajectory, allows different profile components to move differently with age, and remains inspectable.

### 4. Current level may add development context, but only as a pooled main effect

A second candidate form may add **as-of level-group main effects** to the same age curve. No age × level interaction is allowed in v1.

The practitioner review strengthens the reason to test level context: KATOH and OOPSY both find meaningful age/level information in prospect forecasting. But frozen B2 already conditions the present-talent estimate on age/current level, so v1 will first ask whether a simple additional level main effect improves *change conditional on B2* before introducing interactions.

### 5. Keep opportunity / survival selection separate from batting-rate skill

Observed future seasons are selected: weaker/older players are less likely to receive future opportunity.

Projection v1's estimand remains **future batting rate/profile conditional on receiving future batting opportunities**. Players with zero future PA are not assigned bad batting outcomes and are not given imputed pseudo-performance in the rate model.

Therefore:

- model fitting/scoring uses only observed future core events;
- predictor-without-target and target-without-predictor rates are reported by age and level;
- results are described as conditional-on-opportunity rate projections, not an unconditional career-aging curve;
- opportunity/role probability remains a separate later model channel.

### 6. Protect development evaluation from temporal leakage

A held-out future season is more informative than in-sample fit quality. The three authorized pre-2025 folds therefore have distinct roles:

- `2021-10-15 -> 2022`: **training / candidate-selection fold**;
- `2022-10-15 -> 2023`: **first out-of-time validation fold**;
- `2023-10-15 -> 2024`: **second out-of-time validation fold**;
- `2024-10-15 -> 2025`: untouched **confirmation**, still quarantined.

Hyperparameter selection may use only the 2022 target fold. The 2023 and 2024 outcomes may not choose the candidate form or grid.

For the second validation fold, the already-selected form/hyperparameters may be refit on all chronologically prior authorized data (2022 + 2023 outcomes), mimicking a rolling-origin production fit.

### 7. Process metrics must prove incremental predictive value

The Chamberlain, Ben-Porat, Bay, Grove, OOPSY, and THE BAT X work collectively supports using upstream/process information when it is more stable and independently predictive than outcomes.

It does **not** support adding every descriptive expected metric. Any later tracking/process Projection challenger must demonstrate:

1. stable/reliable measurement in the source population;
2. out-of-time prediction of future performance;
3. incremental gain beyond frozen Current Talent + simple Projection;
4. explicit missing-data behavior by level/source capability.

### 8. Keep v1 deliberately simpler than the literature permits

The literature and practitioner systems support richer hierarchical models, comparable-player curves, process/tracking features, ensembles, and missing-data models. Those are not the first gate.

V1 asks a smaller question: **does a transparent pooled age/development adjustment add predictive value beyond frozen Current Talent carry-forward?** If not, carry-forward remains the Projection baseline and richer Projection models can be proposed later as separately validated challengers.

## Practitioner-pass decision on the pre-registration

The practitioner review was completed **before candidate scoring**. It strengthens the existing two-form candidate design but does not justify expanding the search space now:

- keep Form A: smooth age-only ILR change;
- keep Form B: smooth age + as-of-level main effects;
- keep component/coordinate-specific age responses through the multi-output fit;
- keep age × level interactions, comparables, process metrics, ensembles, and richer tracking features out of v1;
- keep 2022 as the only candidate-selection target and 2023/2024 as out-of-time validation.

The exact candidate/search/promotion contract remains:

`docs/projection-batting-v1-development-contract.md`

No 2025 outcomes were accessed for this review.