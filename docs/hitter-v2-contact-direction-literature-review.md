# Hitter v2 contact-direction literature review

Recorded 2026-08-24 after the frozen Stage 2b disclosed-development result.
This is a documentation-only review. It does not reopen a failed candidate,
change a score, access protected 2026 outcomes, authorize tracking, or specify a
new model contract.

## Question

Does the literature support treating contact direction conditional on
trajectory—especially pulled air contact—as persistent hitter talent, and where
did the Stage 2b implementation differ from that evidence?

## Bottom line

The baseball hypothesis is partly supported, but its strongest defensible form
is narrower than “all direction bins are talent.”

1. **Pulled air contact is unusually valuable.** Descriptive MLB work finds
   much greater production on pulled fly balls and line drives than on air
   contact to center or the opposite field. A radar-tracking study in Japanese
   professional baseball also found lower flyout probability for pulled low
   fly balls than comparable opposite-field low fly balls, with a physical
   explanation involving different and more variable deflection.
2. **Fly-ball pull tendency is repeatable, but noisy.** One 2008-2017 study of
   2,346 paired player-seasons reported year-to-year correlation `0.616` after
   requiring 60 fly balls in both seasons. A later Statcast analysis of
   95-105 mph fly balls reported that year-one pull rate explained `31.6%` of
   year-two variation. Large changes still regressed materially toward the
   mean.
3. **Repeatability is not the same as incremental projection value.** A study
   of 539 player-season pairs found only `R² = 0.05` between changes in fly-ball
   pull rate and changes in wOBA and noted survivor-selection concerns. Other
   public analysis reports that adding continuous spray angle to an expected
   contact model can make future prediction worse even when it improves
   description of the completed play.
4. **Direction must be conditioned on trajectory and contact quality.** The
   biomechanics differ between ground balls and fly balls. A pulled fly ball
   and pulled ground ball are not two levels of one generic “pull” skill.
   Exit velocity and launch angle also change the benefit: a truly crushed fly
   ball can succeed to any field, while direction matters more for intermediate
   air contact.
5. **Opposite-field ground-ball value is real descriptively but is not yet a
   demonstrated universal forecasting skill.** A 2023 MLB infield-hit analysis
   reported batting averages of `.407` on opposite-field grounders, `.310` up
   the middle, and `.141` on pulled grounders. Those results depend on batter
   side, sprint speed, fielding alignment, rule era, and selection into a rare
   batted-ball location. They do not by themselves show that a player's
   opposite-grounder rate improves future offensive projection.

The evidence therefore supports testing a heavily shrunk **pulled-air skill**
as a narrow incremental predictor of future power. It does not support freely
letting all ten direction/trajectory shares adjust every terminal outcome.

## Evidence reviewed

### Value and physical mechanism

- Kato and Yanai, *Pulled fly balls are harder to catch* (Sports Engineering,
  2022), analyzed 25,413 radar-tracked NPB fly balls. For low fly balls, the
  reported flyout probability was `0.41` on the pull side and `0.49` on the
  opposite side. Pulled balls also showed more variable deflection and smaller
  modeled flyout zones. This establishes a plausible physical and fielding
  mechanism, not player-level forecast persistence.
  <https://link.springer.com/article/10.1007/s12283-022-00373-6>
- Kidokoro and Yanai's controlled hitting study found that grounders and fly
  balls use direction-generating impact mechanisms differently. Horizontal bat
  angle and the interaction between vertical bat inclination and impact point
  contributed differently to same- and opposite-field contact. This argues
  against a trajectory-agnostic direction coefficient.
  <https://www.jstage.jst.go.jp/article/jjpehss/62/2/62_16005/_article/-char/en>
- A PLOS One elite-softball experiment likewise found asymmetric mechanics and
  different spin/launch behavior by intended field. Softball is not a direct
  MLB forecasting result, but it reinforces the interaction rather than a
  generic pull effect.
  <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0260520>
- A SABR review reports a 2008-2022 slash line of `.612/.603/1.356` for pulled
  fly balls and line drives versus `.388/.379/.640` for center/opposite air
  contact. This is strong descriptive value evidence, but it combines outcome,
  contact quality, park geometry, and hitter selection.
  <https://sabr.org/journal/article/plummeting-batting-averages-are-due-to-far-more-than-infield-shifting-part-one-fielding-and-batting-strategy/>

### Persistence and regression

- Podhorzer's 2008-2017 FanGraphs study reported `r = 0.616` year-to-year for
  fly-ball pull percentage with at least 60 fly balls in consecutive seasons.
  Three-year cohorts showed that large gains and losses partially reverted the
  next year. This supports empirical-Bayes shrinkage and an event-count
  reliability surface rather than raw rates.
  <https://fantasy.fangraphs.com/getting-to-know-fly-ball-pull-percentage-fb-pull/>
- Clemens' Statcast analysis of 95-105 mph fly balls found year-one pull rate
  explained `31.6%` of year-two variation among qualifying consecutive
  seasons. It also showed why direction's value depends on exit velocity: pull
  mattered greatly in the intermediate band, while truly crushed contact was
  productive to any field.
  <https://blogs.fangraphs.com/an-meandering-examination-of-fly-ball-pull-rate-featuring-stars-of-the-game-and-also-isaac-paredes/>
- Luciani's counteranalysis found only a weak relationship (`R² = 0.05`)
  between year-over-year changes in pulled-fly rate and changes in wOBA, with a
  warning that players who lost MLB opportunity could be omitted. This is not a
  definitive null result, but it separates a sticky process statistic from a
  reliably useful projection increment.
  <https://pitcherlist.com/going-deep-the-myth-behind-pulled-fly-balls/>

### Expected-contact models and overfitting risk

- MLB's official Statcast definition says xwOBA uses exit velocity, launch
  angle, and sprint speed for certain batted balls; horizontal direction is not
  listed as an input. That design choice is not proof that direction has zero
  hitter signal, but it is a warning that observed spray can encode fielders,
  parks, pitch location, and small-sample variance.
  <https://www.mlb.com/glossary/statcast/expected-woba>
- MLB separately defines horizontal vector/attack direction, confirming that
  direction is observable even though it is not part of the published xwOBA
  input contract.
  <https://www.mlb.com/news/major-league-baseballs-statcast-glossary-of-terms-of-state-of-the-art-tracking-technology/c-150784778>
- Chamberlain reports that including spray angle made his xwOBA-style measure
  less predictive, while pulled-air tendencies can still explain persistent
  player-specific departures. This distinction—event value versus stable
  player talent—is central to Hitter v2.
  <https://blogs.fangraphs.com/the-pulled-fly-ball-revolution-was-always-underway/>

### Ground-ball direction

- A SABR model of 2023 MLB infield hits reported `.407` batting average on
  opposite-field grounders, `.310` up the middle, and `.141` on pulled
  grounders. The same study emphasizes favorable zones and defensive
  positioning. This supports separate ground-ball treatment, not transferring
  an air-contact coefficient to grounders.
  <https://sabr.org/journal/article/an-infield-hit-model-from-the-2023-mlb-season-hit-em-where-they-aint/>
- The 2023 shift restriction changed the environment, especially for
  left-handed pulled ground balls. Any historical or cross-level model must
  therefore condition ground-ball direction value on batter side and rule era,
  and must not assume MLB defensive alignment applies across affiliated levels.

## What the literature does **not** establish

- It does not establish that pulled fly balls are universally the “hardest”
  contact type to produce. It establishes high value, asymmetric mechanics, and
  meaningful but imperfect player persistence.
- It does not show that increasing pulled-air rate causes better offense for
  every hitter. A player may trade contact rate, launch quality, or plate
  discipline to change direction.
- It does not show that opposite-field ground-ball frequency is a stable skill
  after controlling for speed, handedness, pitch location, defense, and player
  selection.
- It does not justify valuing contact shape with realized target-season run
  values in a forecast. Descriptive event value and forecastable player talent
  remain separate estimands.
- It does not justify using tracking availability as a talent feature or
  requiring Statcast for a universal forecast.

## Gaps in the failed Stage 2b design

### 1. The estimator was broader than the hypothesis

D1/D2 allowed shape features to adjust six contact-conditional multinomial
nodes: HR/non-HR, reach/non-reach, hit/non-hit reach, 1B/2B/3B, ROE/FC, and
SF/multi-out/other-out. The baseball hypothesis is narrower: pulled air should
primarily add evidence about future HR/XBH production, while ground-ball
direction should be evaluated separately for reach probability.

### 2. It mixed “what happened” with “repeatable skill”

The ten-bin distribution describes a player's contact portfolio. It does not
separate:

- opportunity to make contact and elevate;
- repeatable ability to pull an air ball;
- exit velocity/launch quality of that pulled air ball;
- park and defensive consequences after contact.

The result can be descriptively correct yet add little future information after
prior HR, 2B, and 3B outcomes are already in the backbone.

### 3. It did not encode the key conditional sequence

The literature suggests an interpretable hierarchy:

`P(air | contact) → P(pull | air) → P(HR/XBH | pulled air)`

with a separate ground-ball branch. Stage 2b instead supplied centered shares
to multiple terminal nodes simultaneously. That makes it harder to identify
which physical skill is contributing and increases variance.

### 4. Contact quality was unavailable in the universal feature

PBP trajectory bins combine weak, medium, and crushed fly balls. Public
Statcast analysis indicates that direction matters differently across exit-
velocity bands. The universal model must retain a PBP-only pulled-air estimate,
but the optional tracking channel should test whether EV/LA explains or
interacts with that estimate on identical overlap rows.

### 5. Pooling was not component- or level-specific enough

All shape groups used the same 200-event prior, two-season half-life, and
reliability constant. The literature gives no reason to expect IFFB, pulled-air
rate, line-drive direction, and rare opposite-grounder rates to stabilize at
the same event count. The V2023 AAA reversal is direct evidence that a single
cross-level residual was not safe.

### 6. Batter side and switch-hitter context were not modeled explicitly

The stored bins are batter-relative pull/center/opposite categories, which is
better than raw left/right field. But coefficients were not conditioned on
batting side, and season aggregates cannot distinguish a switch hitter's two
sides. Ground-ball value, throwing distance, shift exposure, and park geometry
are side-dependent.

### 7. Pitch-location opportunity was absent

Direction partly reflects where and how a hitter was pitched. Without credible
pitch-location coverage at every affiliated level, the universal feature cannot
fully distinguish a hitter's intent/timing skill from the opportunity mix
offered by pitchers. This argues for more shrinkage and uncertainty, not for
dropping the feature.

### 8. Classification and translation drift need direct audit

The source fuses MLB and affiliated PBP-derived classifications. Even with high
event coverage, fly-ball/line-drive and direction labels may not be calibrated
identically across source systems, leagues, parks, or seasons. Coverage alone
does not prove semantic transportability.

### 9. The target was too diffuse for the first shape test

The broad multinomial target spends degrees of freedom on ROE, FC, sacrifices,
and multi-out structure. A first-principles pulled-air test should ask whether
the feature improves future HR/XBH or neutral contact value beyond outcome
history on the same rows. Only after that passes should it be allowed to affect
the complete outcome simplex.

## Statistically sensible next research design

This is a research recommendation, not an authorized candidate contract.

1. **Audit semantics before modeling.** Verify batter-relative direction by
   side, switch-hitter handling, trajectory labels, and MLB/MiLB agreement.
2. **Estimate persistence by component and level.** Measure chronology-safe
   year-to-year reliability for `air/contact`, `pull/air`, pulled LD, pulled FB,
   and opposite GB. Include players who lose opportunity to reduce survivor
   bias.
3. **Separate value from talent.** First report descriptive future-neutral
   outcome value for direction×trajectory cells. Then estimate the player-level
   residual that persists after prior terminal HR/XBH history.
4. **Use a nested empirical-Bayes feature.** Project air-contact rate and
   pulled-air rate with separate priors, half-lives, level pools, and evidence
   counts. Keep an exact zero increment when shape evidence is absent.
5. **Use a narrow first target.** Test whether pulled-air talent incrementally
   improves future `P(HR | contact)`, `P(XBH | non-HR hit)`, proper event scores,
   and neutral wOBA/runs on identical cohorts. Treat opposite-grounder skill as
   a separate BABIP/reach experiment.
6. **Model level heterogeneity explicitly.** Require level-specific or
   partially pooled coefficients and protect against the observed AAA reversal.
7. **Add tracking only as an interaction/residual.** On identical supported
   rows, compare PBP outcome history, PBP plus pulled-air, and PBP plus
   pulled-air×EV/LA. Tracking must shrink smoothly to zero and never redefine
   the universal target or cohort.
8. **Pre-register stabilization and gates.** No constants should be chosen from
   the already-seen Stage 2b result. A new versioned contract needs a fresh
   development boundary and must leave protected 2026 closed until a candidate
   and confirmation scorer are frozen and reviewed.

## Plan impact

Ideas that should change the next plan:

- replace broad ten-bin multinomial offsets with a nested pulled-air skill;
- separate air and ground direction mechanisms;
- estimate component-specific stability and shrinkage by level;
- explicitly handle batter side, switch hitters, source semantics, and rule era;
- target future power/contact value narrowly before the full simplex;
- test EV/LA as an optional interaction on identical overlap rows;
- treat the V2023 AAA reversal as a structural transportability problem.

Ideas deferred until a PBP-only candidate passes:

- production Statcast fusion;
- bat-speed or attack-direction features;
- protected 2026 confirmation;
- baserunning, defense, opportunity, and WAR assembly.

