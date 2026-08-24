# Hitter v2 next research plan

Status: **DESIGN PLAN; NO NEW CANDIDATE SCORE AUTHORIZED**  
Date: 2026-08-24

## The next ten steps

1. **Preserve the outcome-only backbone.** Keep the nested empirical-Bayes
   terminal outcome model as the universal reference and exact fallback. Fix
   source/reconciliation defects before adding predictors.
2. **Replace the broad shape adjustment with one narrow power test.** Test
   shrunk `P(OFFB|contact)` and `P(pull|OFFB)` only against future
   `P(HR|contact)` first. Do not let them move every outcome node.
3. **Test extra-base shape separately.** Only if the HR-only pulled-air model
   passes, test a second ablation on `P(2B/3B|non-HR hit)`. It cannot rescue a
   failed HR test.
4. **Keep ground direction separate.** Test `P(GB|contact)` and
   `P(opposite|GB)` only against non-HR reach/BABIP, with batter side, speed,
   rule era, and level guardrails. It cannot rescue failed air evidence.
5. **Treat distance as optional tracking.** The repository audit shows
   `hit_distance_sc` is sparse and almost perfectly co-available with EV. After
   the PBP base freezes, test an air-distance residual conditional on prior HR
   history and pulled-air skill, with venue calibration and exact fallback.
6. **Improve competition and translation context.** Build chronology-safe
   league/level translations from movers and test opponent-strength summaries
   such as pitcher age relative to level and prior pitcher quality. Do not use
   pitcher identity or target-season results as shortcuts.
7. **Test role signals without confusing role and talent.** Prior batting-order
   slot may proxy organizational belief at lower levels, but must be lagged,
   team/level centered, shrunk, and ablated after objective performance. It
   must never define the forecast cohort.
8. **Keep durability in opportunity, not batting rate.** Games, PA continuity,
   missed time, and being young for a level may help future participation and
   PA distributions. They should not directly inflate neutral batting talent.
9. **Use physical/demographic fields conservatively.** Age and age-to-level are
   core. Height can be a low-weight, nonlinear prior/interaction if stable;
   stale weight is exploratory. Country of origin is not a talent predictor;
   any transition-context use requires a mechanism, fairness audit, and clear
   incremental value. Lineup slot, handedness, and opponent traits require
   explicit missing-source fallbacks.
10. **Freeze and score one ladder once.** Pre-register folds, exact cohorts,
    proper scores, future wOBA/runs metrics, calibration, evidence bands,
    promotions/demotions, level reversals, and missingness invariants. Score
    disclosed development folds only after implementation hashes are frozen;
    leave 2026 closed until an explicit one-shot confirmation review.

## Why this ordering

Tom Tango's predictive-wOBA work reinforces the distinction between describing
a completed play and estimating a player's future talent. Alex Chamberlain's
work shows both that expected contact quality can carry forward and that spray
angle can hurt future prediction despite improving completed-play fit. Jonathan
Judge's DRC work supports separately regularized outcome probabilities and
contextual mixed effects, while also warning that retrospective descriptive
metrics are not automatically projection systems. Direct PBP multinomial work
supports regularized batter/pitcher/park/platoon context, but the universal
forecast still needs a player-history projection layer rather than an
in-sample event estimator.

Public minor-league distance studies found useful year-to-year and AAA-to-MLB
signal after venue correction, but also raised the decisive test: does distance
add information after prior HR rate? The repository's own coverage audit makes
this a later capability-aware residual, not part of the universal PBP base.

## Inputs explicitly deferred from the batting-rate ladder

- durability and games played: MLB opportunity/playing time;
- defensive position and position transitions: exposure/defense;
- raw country labels: excluded absent a specific transition mechanism;
- current target-season lineup position: leakage;
- tracking availability: prohibited as a talent feature;
- broad black-box interactions: deferred until interpretable ablations pass.

## Research references that materially changed this plan

- Tom Tango, Predictive wOBA:
  <https://tangotiger.com/index.php/site/article/introducing-predictive-woba>
- Alex Chamberlain, spray angle and xwOBA:
  <https://fantasy.fangraphs.com/quantifying-the-benefit-of-spray-angle-to-xwoba/>
- Alex Chamberlain, launch angle:
  <https://fantasy.fangraphs.com/lets-talk-about-launch-angle-generally/>
- Alex Chamberlain, pitch location and launch angle:
  <https://fantasy.fangraphs.com/launch-angle-pitch-location-and-what-pitchers-cannot-control/>
- Jonathan Judge, DRC methodology discussion:
  <https://sabr.org/latest/judge-the-performance-case-for-drc/>
- Regularized PBP multinomial batting model:
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC6521856/>
- Jim Albert, component hitting measures:
  <https://arxiv.org/abs/1505.05557>
- Public minor-league distance study and venue correction:
  <https://tht.fangraphs.com/scouting-the-minors-pitch-by-pitch-power/>
- Public minor-league FB Dist+ exploration:
  <https://tht.fangraphs.com/using-fly-ball-distance-to-find-sleeper-prospects/>

