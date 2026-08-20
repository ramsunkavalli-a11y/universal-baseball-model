# Pitching v1 methodology review

Last updated: 2026-08-20

Status: **COMPLETE — design implications frozen before Pitching v1 outcome scoring**

## Question

What is the smallest transparent pitching model that can cover MLB through the
lowest affiliated levels, remain separable from fielding and workload, and earn
promotion through chronological evidence rather than descriptive sophistication?

This review is upstream of candidate scoring. It does not authorize opening the
2025 confirmation surface, selecting a model from final rankings, or treating
tracking availability as universal.

## Existing project evidence

The repository already supplies most of the source and run-value foundation:

- certified season-player pitching aggregates expose BF, G, GS, K, BB, IBB,
  HBP, HR and other standard outcomes at player/team/league/season grain;
- completed-2024 source certification found unique source grains and exact
  agreement on 13 mutually available fields in five deterministic official
  pitching comparisons;
- missing pitching sacrifice-bunt counts remain explicitly missing and are not
  manufactured;
- state replay and RE24 mechanics are independently validated against
  Retrosheet and frozen;
- pitch-process fidelity is explicitly capability-gated by league and season;
- the batting project already provides chronological translation,
  empirical-Bayes, projection, workload, replacement, centering, uncertainty,
  artifact and CI patterns that should be reused rather than re-invented.

The remaining methodology questions are pitcher responsibility, a universal
rate representation, role/workload separation, minor-league translation and
pitcher-specific replacement accounting.

## Public methodology reviewed

### Defense-independent pitching and pitcher WAR

- FanGraphs, [WAR for Pitchers](https://library.fangraphs.com/war/calculating-war-pitchers/)
- FanGraphs, [FIP](https://library.fangraphs.com/pitching/fip/)
- FanGraphs, [DIPS](https://library.fangraphs.com/principles/dips/)
- FanGraphs, [xFIP](https://library.fangraphs.com/pitching/xfip/)
- Baseball-Reference, [WAR Explained](https://www.baseball-reference.com/about/war_explained.shtml)

FanGraphs separates pitcher value from fielding with a FIP-based core, places
that estimate on a runs-allowed scale, distinguishes starter and reliever
replacement, treats leverage as a reliever value adjustment and applies a
league correction to meet the intended pitcher WAR pool. Its published formula
also makes clear that workload is a multiplier, not the pitching-rate talent
estimate itself.

Baseball-Reference instead begins from actual runs allowed and adjusts for
defense, opponent, park and role context. The disagreement is informative:
there is no uniquely mandatory pitcher-responsibility allocation. A new model
must state whether it estimates observed team run prevention, pitcher-owned
outcomes or forecast talent.

FIP and DIPS support beginning with outcomes most directly assigned to the
pitcher: strikeouts, walks, hit batters and home runs. xFIP is useful predictive
context but its league-average HR/FB substitution requires a consistently
certified fly-ball denominator that the universal source does not yet provide.

### Contact/process models

- MLB, [Expected ERA](https://www.mlb.com/glossary/statcast/expected-era)
- FanGraphs, [PitchingBot Pitch Modeling Primer](https://library.fangraphs.com/pitching/pitchingbot-pitch-modeling-primer/)
- FanGraphs, [Stuff+, Location+ and Pitching+](https://library.fangraphs.com/pitching/stuff-location-and-pitching-primer/)

xERA and public pitch-quality models demonstrate that contact quality, pitch
shape and location can add pitcher-owned information beyond aggregate outcomes.
They also depend on tracking fields that are structurally absent in many
affiliated league-season environments. The project therefore treats them as
later capability-gated challengers, not the universal v1 backbone.

PitchingBot also provides an important design warning: combining several
estimators built from substantially the same outcomes adds less independent
information than combining genuinely distinct evidence families. Pitching v1
will not average FIP, xFIP and SIERA merely to appear more sophisticated.

### Minor-league forecasting and projection

- Chris Mitchell, [KATOH: Forecasting Major League Pitching with Minor League Stats](https://tht.fangraphs.com/katoh-forecasting-major-league-pitching-with-minor-league-stats/)
- Existing project review: `docs/projection-v1-methodology-review.md`
- Nguyen and Matthews, [Filling the Gaps](https://arxiv.org/abs/2210.02383)

KATOH found age, starter share, strikeout rate, walk rate, home-run rate and
handedness informative for minor-league pitchers, with lower-level evidence
carrying much greater uncertainty. That supports explicit age/level context,
role separation and stronger shrinkage for distant or sparse evidence. It does
not justify using future level or future role as predictors.

The existing project projection review already establishes the relevant
general rules: recency weighting, regression, translation to a common
environment, held-out future scoring and explicit handling of survivor/opportunity
bias. Those rules apply to pitching without repeating a broad projection search.

## Binding Pitching v1 implications

### 1. Separate Performance, talent, Projection and workload

Pitching v1 has four distinct estimands:

1. observed pitcher outcome Performance;
2. current pitcher rate talent;
3. one-year projected rate talent conditional on future BF;
4. future opportunity and starter/reliever workload.

No rate model may use realized future BF as a predictor. No workload model may
reinterpret zero future BF as poor rate talent.

### 2. Use an exhaustive universal BF profile

The first universal Performance representation is:

- `K`;
- `UBB = BB - IBB`;
- `HBP`;
- `HR`;
- `OTHER_BF = BF - K - UBB - HBP - HR`.

These five counts must be nonnegative and sum exactly to BF. Intentional walks
remain observable inside `OTHER_BF`; v1 does not treat a manager-issued IBB as
pitcher walk skill. Missing sacrifice-bunt counts do not prevent this identity
and are not guessed.

This is a responsibility-oriented talent profile, not a claim that pitchers
have zero influence on non-HR balls in play. The neutral residual is the
universal baseline until richer contact/process evidence wins a predeclared
out-of-time challenger gate.

### 3. Translate and shrink components, not ERA

League/level effects are estimated on the five-part compositional scale from
chronologically prior matched pitcher evidence. Player evidence is recency
weighted and empirically shrunk toward a leave-one-player-out age/level/role
prior. Independent rate clipping is forbidden because it can break the BF
composition.

### 4. Score rates before run conversion

Primary selection evaluates future BF-weighted multinomial log loss on the
complete five-part profile. Component calibration and Brier diagnostics are
secondary. A run-value diagnostic may translate the future profile into a
common MLB reference environment, but candidate selection cannot be rescued by
one favorable aggregate run score after losing the primary profile gate.

### 5. Keep pitcher run conversion explicit

Projected pitcher runs above average will be calculated from differences
between projected and fixed MLB-reference outcome rates using frozen public or
empirically calibrated event run weights. The pitcher-positive sign convention
must be explicit. Fielding, park, opponent, role, workload, centering,
replacement, leverage and runs-to-wins adjustments remain separate columns.

### 6. Treat role as both context and opportunity, never hidden talent

Starter share can enter a prior or a predeclared rate challenger because the
starter/reliever run environments differ. Future starter probability, BF and
outs are projected separately. Mixed-role players retain a share rather than
being forced into one label.

### 7. Defer tracking and scouting challengers

Velocity, movement, location, pitch mix, xERA, Stuff+ analogues, scouting grades
and injury information are outside the universal baseline. Any future
challenger must prove source capability, chronology, incremental information
and held-out improvement without deleting universal fallback rows.

## Resulting order of work

1. Freeze this review and the Pitching v1 development contract.
2. Implement and test the universal BF Performance profile on synthetic data.
3. Inventory exact frozen 2021–2024 pitching source artifacts and coverage.
4. Materialize chronological development folds without opening 2025.
5. Fit/select the smallest translated empirical-Bayes Current Talent model.
6. Test one-year rate movement around Current Talent.
7. Freeze role/workload projection.
8. Freeze run conversion, MLB centering, replacement, leverage and pitcher WAR.
9. Add uncertainty and two-way-player aggregation.

## Explicit non-decisions

This review does not freeze numerical prior strength, recency half-life,
translation coefficients, role thresholds, event run weights, replacement
allocation, leverage treatment, park adjustment or runs per win. Those values
must be predeclared or selected only from authorized development folds.
