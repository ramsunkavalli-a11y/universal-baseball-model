# All-level hitter-pitcher profile matchup challenger v1

## Plain-language answer

There is a real but small matchup effect in the minor-league data. Knowing that
a hitter is, for example, a high-contact left-handed batter and that a pitcher
is a high-strikeout or ground-ball pitcher improves the expected result of an
individual plate appearance. It does **not** yet improve next-season player
talent estimates broadly enough to replace the current hitter or pitcher model.

The useful pieces are narrow:

- Heavily regressed left/right histories improve event forecasts, particularly
  strikeouts and whether contact is on the ground.
- Explicit hitter-profile × pitcher-profile interactions add a smaller,
  consistent event gain for strikeouts, walks/HBP, and home runs.
- Those gains remain for advancing players and for hitter-pitcher pairs that
  have never faced each other, so this is not disguised batter-vs-pitcher data.
- When plate appearances are rolled up to next-season player rates, most gains
  become tiny or reverse. Hitter strikeout and hit-on-contact projections are
  the most repeatable positive interaction results; pitcher strikeout gets
  slightly worse.

The decision is to keep this as a compact matchup/context component for later
integration tests, not make it the new foundation of the projection system.

## Goal and question

The test asked whether the system should go beyond separately estimating hitter
talent and pitcher talent. In baseball terms: does a high-power or high-contact
left- or right-handed hitter have a predictably different result against a
pitcher's strikeout, control, home-run, contact-quality, or ground-ball profile?

The protected 2026 outcome season was not read or changed.

## What the literature says

The literature points away from raw career batter-vs-pitcher records and toward
partial pooling of broader player profiles:

- The hierarchical Bayesian Log5 work combines batter, pitcher, and league
  rates and reports better chronological forecasts than unpooled Log5 variants.
  This supports shrinking sparse individual histories rather than taking them
  literally: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0204874
- The Book's practical conclusion, reflected in Tango's public work, is that
  direct batter-vs-pitcher samples are mostly too small to trust. Platoon and
  extreme ground-ball/fly-ball tendencies are more plausible repeatable
  exceptions, but platoon splits still require heavy regression.
- FanGraphs' split guidance likewise places hitter platoon stabilization around
  1,000-2,000 plate appearances and pitcher platoon stabilization around
  500-700, which argues for strong shrinkage in the minors:
  https://blogs.fangraphs.com/batter-pitcher-splits-crib-sheet/
- Generalized linked matrix factorization was motivated by the fact that most
  possible MLB hitter-pitcher pairs never meet. It gains information through
  shared latent player traits rather than requiring direct meetings:
  https://arxiv.org/abs/2402.01914
- SEAM similarly synthesizes broader batter and pitcher profiles because direct
  head-to-head samples are sparse: https://arxiv.org/abs/2005.07742
- Prior ground-ball matchup research gives a specific baseball reason to test
  hitter and pitcher batted-ball profiles together:
  https://journals.sagepub.com/doi/10.3233/JSA-160025

This challenger follows those ideas but judges them by UBM's actual objective:
future player performance, not only one plate appearance.

## Data and chronology

- 6,957,632 completed affiliated minor-league plate appearances.
- Rookie through Triple-A.
- Seasons 2016-2019 and 2021-2024; the nonexistent 2020 MiLB season is absent.
- Evaluation seasons: 2019, 2021, 2022, 2023, and 2024.
- Every player profile for a target season uses only the prior three seasons.
- Tuning for a fold uses only earlier folds.
- The test separately marks advancing hitters, advancing pitchers, and new
  hitter-pitcher pairs.

## Player profiles

Both hitters and pitchers receive the same prior-only profile:

- strikeout rate;
- walk/HBP rate;
- home-run rate;
- hit and extra-base-hit rate on contact;
- ground-ball, air-ball, line-drive, and popup rate.

Each rate is first centered on its season and level, then recency weighted and
empirical-Bayes regressed. A second set measures hitters separately versus left-
and right-handed pitchers and pitchers separately versus left- and right-handed
batters. These splits are regressed back toward the player's overall profile.

The test intentionally does not use raw batter-vs-pitcher history. It also does
not use pitch type, velocity, movement, or Statcast.

Park is not explicitly estimated inside this challenger. Season-level effects
are removed, and every compared model sees the same remaining park noise. The
existing contact-neutralization experiment already showed that park adjustment
substantially improves fair description of batted-ball outcomes but did not
improve following-year player WAR. If this component is integrated, its contact
inputs should come from that park-neutral event layer rather than rebuilding a
second park model here.

## Models compared

1. **Additive:** overall hitter profile + overall pitcher profile + level +
   handedness cell + history and level-change controls.
2. **Handed additive:** adds heavily regressed hitter-vs-hand and
   pitcher-vs-side histories, but no profile interactions.
3. **Baseball interactions:** adds 15 predeclared products such as power ×
   home-run tendency, contact × strikeout tendency, and damage × ground-ball
   tendency.
4. **Handed interactions:** applies those same interactions to the regressed
   left/right profiles.
5. **Full bilinear and rank-2 bilinear:** exploratory models that either fit
   every profile pairing or retain two latent interaction patterns.

The broad bilinear models are controls against both underfitting and wishful
feature selection. They were not allowed to choose interactions after seeing a
future fold.

## Event-level result

Negative numbers are improvements in log loss. The most useful comparisons are:

| Outcome | Handed additive vs additive | Handed interactions vs handed additive | Interaction fold wins |
|---|---:|---:|---:|
| Strikeout | -0.00010577 | -0.00003271 | 5/5 |
| Walk or HBP | -0.00000045 | -0.00005107 | 5/5 |
| Home run | +0.00000688 | -0.00005104 | 5/5 |
| Ground ball on contact | -0.00020363 | -0.00000358 | 4/5 |
| Extra-base hit on contact | -0.00002773 | -0.00000258 | 4/5 |
| Hit on contact | -0.00000627 | -0.00000219 | 4/5 |

This is a consistent but small signal. The exhaustive full interaction model
hurt both hit and contact-damage forecasts, while the 15 baseball interactions
did not. That is evidence for constrained baseball structure, not an invitation
to multiply every available variable together.

For never-before-seen hitter-pitcher pairs, the handed interaction model
improved all six event targets. It also improved strikeout, walk/HBP, and
home-run event forecasts for advancing hitters and advancing pitchers. The
model therefore learned transferable profile relationships rather than merely
memorizing opponents.

## Next-season player result

The player test groups each future season's plate appearances into observed and
predicted hitter and pitcher rates, requires at least 100 opportunities, and
scores RMSE. This is much closer to projection value than event log loss.

The strongest handedness-only result was walk/HBP rate:

- hitter RMSE improved by 0.000174, or 0.43%, but only three of five folds;
- pitcher RMSE improved by 0.000150, or 0.32%, in four of five folds.

The explicit matchup interactions had smaller and mixed player effects:

- hitter strikeout RMSE improved in four of five folds;
- hitter hit-on-contact RMSE improved in four of five folds;
- pitcher hit-on-contact, contact damage, and home-run rate each improved in
  three of five folds;
- pitcher strikeout RMSE worsened in four of five folds;
- the remaining outcomes were mixed or effectively flat.

The plate-appearance result is credible; the player-projection promotion case
is not yet strong. Schedule averaging removes much of a true matchup effect,
and the remaining changes are very small.

## Decision and integration plan

1. Do not replace the current hitter or pitcher base model.
2. Retain the 15 predeclared interaction block and the regressed left/right
   profiles as development features.
3. In the next full hitter-model tournament, test only three compact additions:
   regressed walk/HBP splits, interaction-derived hitter strikeout expectation,
   and interaction-derived hit-on-contact expectation.
4. Feed those as lagged player features or as a projected-opponent-mix
   adjustment; do not feed raw batter-vs-pitcher records.
5. Use the existing park-neutral contact layer for the contact outcomes, then
   require improvement in next-season value—not merely event scoring—before
   promotion.
6. Keep the full and rank-2 bilinear models rejected for production. Their
   contact overfit is exactly the failure mode the literature warns about.
7. Leave the frozen 2026 forecast unchanged and use 2026 only under the existing
   confirmation contract after the season is complete.

## Reproduction

- Core profile construction: `src/universal_baseball/historical_matchup_profiles.py`
- Evaluation: `scripts/evaluate_all_level_matchup_challenger_v1.py`
- Unit tests: `tests/test_historical_matchup_profiles.py`
- Machine-readable outputs: `reports/generated/all-level-matchup-challenger-v1/`

