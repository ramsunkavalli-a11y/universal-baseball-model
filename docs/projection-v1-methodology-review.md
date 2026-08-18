# Projection v1 methodology review

Last updated: 2026-08-17

Status: **REVIEW COMPLETE — binding design implications frozen before Projection model scoring.**

## Question

Before fitting the first age/development Projection model, what does relevant baseball and longitudinal/compositional modeling literature imply for a transparent v1 design?

This review is intentionally narrow. It is not permission to add tracking, scouting, playing time, future level, or a high-capacity machine-learning model.

## Sources reviewed

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

5. Egozcue, Pawlowsky-Glahn, Mateu-Figueras & Barceló-Vidal (2003), **Isometric Logratio Transformations for Compositional Data Analysis**, Mathematical Geology 35:279–300, DOI 10.1023/A:1023818214614.
   - ILR maps a composition from the simplex to an orthonormal Euclidean coordinate system while preserving the compositional geometry.

6. Sørensen, Walhovd & Fjell (2020), **A recipe for accurate estimation of lifespan brain trajectories, distinguishing longitudinal and cohort effects**, arXiv:2007.13446 / NeuroImage 117596.
   - Longitudinal change should be modeled with smooth functions rather than arbitrary single-age cells or rigid high-order polynomials.
   - Flexible smooth trajectories are useful when change is nonlinear and repeated observations are sparse/irregular.

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

This tests whether a 21-year-old in Rookie/A-ball and a 21-year-old already in MLB should receive systematically different one-year development adjustments without turning current level into a large interaction model.

### 5. Keep opportunity / survival selection separate from batting-rate skill

The baseball aging literature is clear that observed future seasons are selected: weaker/older players are less likely to receive future opportunity.

Projection v1's estimand remains **future batting rate/profile conditional on receiving future batting opportunities**. Players with zero future PA are not assigned bad batting outcomes and are not given imputed pseudo-performance in the rate model.

Therefore:

- model fitting/scoring uses only observed future core events;
- predictor-without-target and target-without-predictor rates are reported by age and level;
- results are described as conditional-on-opportunity rate projections, not an unconditional career-aging curve;
- opportunity/role probability remains a separate later model channel.

### 6. Protect development evaluation from temporal leakage

A held-out future season is more informative than in-sample fit quality. The three authorized pre-2025 folds will therefore have distinct roles:

- `2021-10-15 -> 2022`: **training / candidate-selection fold**;
- `2022-10-15 -> 2023`: **first out-of-time validation fold**;
- `2023-10-15 -> 2024`: **second out-of-time validation fold**;
- `2024-10-15 -> 2025`: untouched **confirmation**, still quarantined.

Hyperparameter selection may use only the 2022 target fold. The 2023 and 2024 outcomes may not choose the candidate form or grid.

For the second validation fold, the already-selected form/hyperparameters may be refit on all chronologically prior authorized data (2022 + 2023 outcomes), mimicking a rolling-origin production fit.

### 7. Keep v1 deliberately simpler than the literature permits

The literature supports richer hierarchical/mixed models, missing-data models, and individualized aging trajectories. Those are not the first gate.

V1 asks a smaller question: **does a transparent pooled age/development adjustment add predictive value beyond frozen Current Talent carry-forward?** If not, carry-forward remains the Projection baseline and richer Projection models can be proposed later as separately validated challengers.

## Consequence

The exact candidate/search/promotion contract is frozen separately in:

`docs/projection-batting-v1-development-contract.md`

No 2025 outcomes were accessed for this review.