# Research for multi-year player value

Reviewed: 2026-09-22. Implementation: [active plan](multiyear-player-value-plan-2026-09-22.md).

## Findings that change the approach

A good next-season forecast does not establish a good career forecast. We need to
predict both how well someone will play and when he will get the opportunity, retain
players who disappear, and evaluate annual and cumulative production separately.
The sources below support testable designs; none proves that a particular design
will win on our data. Our adaptations are explicitly proposals.

### 1. A simple baseline remains necessary

Tom Tango's [2004 Marcel discussion](https://tangotiger.net/archives/stud0346.shtml)
describes a deliberately simple forecast using weighted recent history, regression,
and age. It is a useful minimum standard for talent prediction, not a complete career
or prospect-value system.

**Application:** retain a transparent age/level/history forecast and a simple
participation/workload model. Extra model complexity must improve a declared future
target. Do not equate the quality of a player's observed season with underlying skill.

### 2. Comparable players can describe development, but skill is not opportunity

Dan Szymborski's [2025 ZiPS introduction](https://blogs.fangraphs.com/the-2025-zips-projections-are-imminent/)
describes estimating present ability from recent, context-adjusted evidence and then
using similar historical player baselines to forecast development. It also explicitly
distinguishes the basic full-time MLB performance projection from a playing-time
prediction; team forecasts need additional opportunity information.

**Application:** retain our validated older six-year prospect comparable model as a
benchmark and candidate prior. Audit annual donor paths using only follow-up known
at the cutoff. A 600-PA skill rating is not expected MLB WAR. Modern ZiPS includes
tracking inputs we have chosen to exclude; borrowing its structure does not require
those inputs or reproduce the proprietary system.

### 3. Long-term forecasts and attrition are longstanding baseball requirements

Baseball Prospectus's [2014 PECOTA announcement](https://www.baseballprospectus.com/news/article/23016/baseball-prospectus-news-10-year-projections-upside-percentiles-and-comparables/)
documents ten-year forecasts, comparables, percentiles, and separate MLB/attrition
diagnostics. Its [2004 A-Rod valuation article](https://legacy.baseballprospectus.com/article_legacy.php?articleid=2475)
describes long-term adjustments for reduced workload and no playing time.

**Application:** annual production, MLB participation, workload loss, and upside belong
in the same player report. A generic aging deduction from next-year WAR does not
cover delayed arrival or leaving MLB. Public descriptions demonstrate the scope of
the problem, not independent proof of PECOTA's accuracy or our implementation.
The 2014 page was available through indexed article text; direct retrieval failed.

### 4. Players who disappear change the apparent aging curve

Mitchel Lichtman's [aging analysis hosted by Tango](https://tangotiger.net/mgl/aging.pdf)
explains selection effects in adjacent-season comparisons. Nguyen and Matthews'
[Filling the Gaps](https://arxiv.org/html/2210.02383v3)
(published in the Journal of Sports Analytics, 2024,
[DOI](https://doi.org/10.3233/JSA-240744)) studies missing seasons and multilevel
multiple imputation. Its observed OPS sample uses at least 100 PA and an age range
of 21–39, so it does not directly validate teenage minor-league development.

**Application:** jointly examine participation and skill, and keep an aging-bias
sensitivity. Missing skill is not zero skill. Conversely, a certified season with
no MLB participation has zero realized MLB production: imputation must not invent
WAR for it. Prospective fitting may never impute a past feature using a later season.
We will not claim missing-not-at-random selection is solved by one imputation model.

### 5. Direct and repeated one-step forecasts have different failure modes

Ben Taieb and Hyndman's [Boosting multi-step autoregressive forecasts](https://proceedings.mlr.press/v32/taieb14.html)
(ICML, 2014) compares iterated one-step and horizon-specific approaches and proposes
direct corrections to recursive forecasts. Their result concerns time series,
not player careers, and motivates a comparison rather than a default winner.

**Application:** test direct Year 2/3 forecasts against linked annual transitions on
identical players and outcomes. Iterating a one-year model requires a declared way
to update future features and a separate long-horizon test; one-year accuracy alone
does not validate that recursion. A possible later hybrid
must learn corrections from earlier out-of-sample predictions. Direct cumulative
means are a check on the annual sum, not extra WAR to add to it.

### 6. Medical prognosis offers a model for performance and continuation together

Rizopoulos and colleagues' [joint modeling and landmarking paper](https://arxiv.org/html/1306.6479v1)
compares predictions based on information at a fixed decision time with models of
repeated measurements and event time together. Links can depend on current level,
change, or accumulated history. Joint models require more assumptions and computation;
landmark models are easier to extend to many predictors.

**Application:** first fit direct forecasts from each baseball cutoff. Then test a
shared player effect linking performance, workload, and MLB continuation. An absent
MLB season is not death: a baseball model must allow MiLB spells, injury and return.
Do not label an absence as injury or retirement without an observed source. Promotion,
demotion and return require recurrent states, not just first-event survival.

### 7. Customer lifetime value separates activity from value while active

Fader, Hardie and Shang's [discrete-time customer-base model](https://www.brucehardie.com/papers/020/)
(Marketing Science, 2010) models purchase behavior while active and unobserved dropout.
It illustrates why inactivity and permanent departure are different latent events.

**Application:** test time since last play and prior activity when projecting return
and opportunity. The direct analogy stops there: permanent customer dropout,
stationary purchase chances, and nonnegative revenue are poor assumptions for baseball
careers with returns, development, changing roles, and negative WAR. Do not import
BG/BB equations unchanged.

### 8. Score the distribution, not just an attractive middle estimate

Gneiting and Raftery's [proper scoring-rule paper](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf)
(JASA, 2007) provides a foundation for evaluating honest probability distributions,
including CRPS and multivariate energy scores.

**Application:** squared error for expected WAR, Brier/log loss for participation,
and CRPS plus coverage/width for future production. Score cumulative totals from
linked draws as well as annual marginals. A model predicting mostly zero can have
good MAE while missing the positive production that matters for value. Compare full
candidate distributions with full baseline distributions, not an uncertain challenger
against a point-mass baseline.

## What this means for our repo

The earlier claim that no multi-year work existed was incorrect. The repo contains
supported six-year partial prospect means, direct two-year skill experiments,
multi-year opportunity paths, service/cost work, and rejected linked-career models.
The missing deliverable is a current, consistently evaluated annual and cumulative
forecast that connects the improved one-year engines to these older foundations.

First establish the targets and feasible historical tests. Then compare a small set
of direct and linked models. Defer another broad algorithm tournament until we know
whether the main error is development, participation, workload, or the value target.
Framing, defense, parks, and opponent quality remain evidence inputs/components;
their one-year success or failure does not by itself answer the multi-year question.

No verified first-party Lau Sze Yui publication specifically on multi-year career
valuation was located in this search. Do not attribute a method or endorsement to him
from third-party social mirrors. This review does not depend on that attribution.
