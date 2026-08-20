# Projection v1 methodology review gate

Status: **QUEUED — COMPLETE AFTER DEVELOPMENT SURFACES ARE VERIFIED, BEFORE MODEL SCORING**

## Purpose

Projection v1 should not simply reproduce familiar baseball projection conventions, and it should not select new methods in reaction to development scores.

After the complete 2022–2024 Projection development surfaces are materialized and chronology/coverage/censoring checks pass, but **before any Projection candidate is scored**, perform a fresh methodology review and use it to freeze the candidate architecture.

The review asks:

> Given a frozen, common-scale estimate of a player's present batting talent, what is the best leakage-safe way to model how that latent batting profile changes over approximately one year?

This is narrower than rebuilding a full ZiPS/PECOTA/Steamer-style system from raw statistics. Frozen Current Talent already handles recency, empirical-Bayes shrinkage, MLB-anchored level translation, and the common MLB-through-complex-league batting profile.

## Baseball literature / practitioner review

Start with the major public projection and aging traditions and their primary or closest-available methodological sources, including:

- Tom Tango / MGL work on regression, reliability, aging, weighting, and projection;
- Clay Davenport / PECOTA methodology and comparable-player ideas where publicly documented;
- Dan Szymborski / ZiPS methodology and published explanations of aging, similarity, uncertainty, and component projection;
- Steamer methodology and Jared Cross's public/academic work;
- relevant FanGraphs, Baseball Prospectus, The Book-era, SABR, and academic baseball aging/projection research;
- newer public work that materially changes the state of the art.

Do not treat brand descriptions as sufficient when primary technical work, papers, code, talks, or detailed methodological explanations are available.

## Outside-baseball methods to examine

Search adjacent fields for methods that map to this specific longitudinal forecasting problem, especially:

- hierarchical / multilevel Bayesian partial pooling;
- empirical-Bayes and shrinkage methods for noisy repeated measurement;
- longitudinal growth and development models;
- dynamic latent-state / state-space models;
- mixed-effects models and individual trajectories;
- probabilistic / distributional forecasting and calibration;
- compositional-data forecasting for probability profiles;
- censoring, missing-not-at-random, survivorship, and selection-bias methods;
- transition models for subjects moving between environments or competition levels;
- direct multi-horizon forecasting methods, for later Projection extensions.

Useful domains may include sports beyond baseball, epidemiology/biostatistics, educational growth modeling, labor/productivity trajectories, reliability engineering, actuarial work, and other repeated-measurement forecasting settings.

Complexity is not itself a reason to promote a method. Prefer methods with a clear causal/statistical reason to help given the actual evidence volume, chronology, uncertainty, and level-transition structure in this repository.

## Required output before scoring

Turn the review into a small predeclared candidate menu:

1. retain Projection Baseline 0: frozen Current Talent carry-forward;
2. retain a transparent simple age/development Baseline 1;
3. add at most a small number of literature-supported challengers whose extra complexity is justified by the data/problem;
4. freeze predictors, transformations, model forms, pooling/smoothing structure, search ranges, promotion thresholds, calibration tolerances, and the 2025 refit/confirmation rule before development scoring begins.

The review may simplify the candidate set as well as expand it.

## Leakage boundary

**2025 regular-season outcomes remain untouched confirmation data throughout this review.**

The literature review may use public methodological information available today, but no 2025 outcome table from this project may be opened, summarized, or used to choose features, model forms, thresholds, or hyperparameters.

## Sequence

1. certify the required historical evidence;
2. materialize and chronology-verify the complete 2022–2024 Projection development surfaces;
3. inspect only development-surface structure/coverage/censoring needed to understand the modeling problem;
4. perform this baseball + cross-domain methodology review;
5. freeze the candidate menu and numeric gates;
6. score fixed candidates on the three authorized development folds;
7. freeze/refit the selected candidate under the predeclared rule;
8. only then open the untouched 2025 confirmation period.
