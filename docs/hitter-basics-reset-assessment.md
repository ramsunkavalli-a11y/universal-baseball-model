# What makes sense, what does not, and what we should work on

2026-10-05. The useful core should survive this reset; the sprawling experiment
history should not dictate the next model. The next-year hitting model is not
worthless. Its opportunity model and the leap from batting to universal player
value are much less satisfactory. AI assistance does not make those assumptions
correct or substitute for information the model does not receive.

This assessment follows the [reset goal](hitter-basics-reset-plan.md). The new
[basic competence check and ten player walks](hitter-basics-floor-result.md)
use only already exposed historical years, without a new fit. Prior reports
below are reviewed evidence, not new experiments or retroactive certification
of every result in the repository.

## The working hitter model in baseball language

First it estimates how well the player would hit in MLB next year. It uses
the last three seasons' strikeouts, walks, home runs and other hit outcomes,
the levels where those happened, age, position and draft history. Prospects
also get dated rankings and a level-translated production profile. Previously
debuted players with MLB contact measurements get a Statcast branch instead.
These hitting models are regularized linear regressions, not chat-model guesses.

Separately it estimates the chance the player will appear in MLB, then how many
PA he will get if he appears. Those are two shallow boosted-tree models, using
production and workload history, MLB experience, roster evidence, position,
age and dated prospect standing. Chance multiplied by conditional PA gives
expected PA. That arithmetic is sensible; the underlying estimates can be bad.

Finally it combines expected PA with estimated batting rate and a replacement
allowance. That is batting-plus-replacement contribution, NOT full WAR, six years
of team control, a trade price or a prospect's upside distribution. Multiplying
mean rate by mean PA is a working approximation: who earns playing time can
depend on hitting and future health. It is not automatically the mean of their
joint value distribution.

| Actual working part | Evidence it uses | Evidence NOT established in this selected construction |
| --- | --- | --- |
| Never-debuted hitting, 220 inputs | Numeric three-season history, draft/profile, dated ranks, translated events/exposure | Fully park/opponent-neutral translation; supported eventual MLB talent for every DSL player |
| Previously debuted hitting, 262 with tracking or 199 without | Numeric history and seven MLB event profiles; tracked route adds measured MLB contact and sample/known flags | Smooth scouting/translation handoff after a brief debut; approved broad foreign/minor-Statcast integration |
| MLB appearance and conditional PA, 251 inputs each | Annual level PA, MLB career/absence/regular history, games/workload, roster and ranking evidence | Reliable temporary-absence/exit distinction, actual future jobs, detailed usable medical prognosis |
| Contribution | Those PA and hitting estimates, fixed replacement reference | General defense, catcher defense, baserunning, positional runs, salary/control and trade valuation in THIS evaluated batting forecast |

Collected weather, game-feed, battery, park, opponent, fielding and running data
do not automatically enter this model. Position as a predictive input is not a
positional WAR bonus. Older component explorers and successful component reports
are not proof those components are integrated into this selected forecast. The
[saved-input audit](hitter-incumbent-representation-review.md) and
[recipe reconciliation](hitter-candidate-readiness-review.md) establish this map.

## What the useful successes actually establish

1. **The selected hitting model beats carrying forward a regressed past profile.**
   On the same players and PA, hitting error falls 1.9092 to 1.8048 and contribution
   error .45469 to .43513. Both favor selected in every origin. That is a real
   competence check, not a new projection gain or proof of individual feature value.
2. **[MLB Statcast](hitter-statcast-next-year-result.md) earns a modest role.**
   Measured contact improves the linear hitting branch beyond coverage flags.
   It recognizes more of Judge/Soto power, while sometimes overrating Torkelson.
   The gain is small, not a solved star or health forecast.
3. **[Fresher rankings](hitter-preseason-readiness-v68-result.md) help prospect
   opportunity.** Langford gets 215 rather than 43 PA, before 557 actual; Kurtz
   still gets ten before 489. Rankings can express readiness before a long pro
   sample. They do not guarantee an immediate job, and graduation is not a demotion.
4. **[Translation plus scouting](hitter-talent-bridge-v74-result.md) adds modest
   future MLB hitting information.** It improves debutant hitting about 1.2%;
   delivered contribution is still uncertain because opportunity remains weak.
5. **[Reliability-weighted minor history](post-arrival-handoff-v13-result.md)
   helps the matched post-arrival rate estimator.** Its hitting error improves
   versus its own MLB-only control. The annual replacement loses to a richer
   incumbent because it also discards separate MLB histories. Do not discard
   the useful minor information or repeat that same integration unchanged.

These are not additive percentages. Populations, endpoints and references differ;
summing them or turning .4534 into .4351 by changing the score reference would
invent progress. All are heavily exposed historical development evidence.

## Failed tests that should NOT kill the broader baseball idea

| Family | What the reviewed test really says | Correct disposition |
| --- | --- | --- |
| Raw contact type × outcome | Ninety pooled raw minor bins do not beat the translated prospect anchor in this fixed linear comparison; parks/opponents remain unadjusted | Close that exact trial. Do not conclude adjusted contact is useless. [Review](hitter-repaired-contact-information-result.md) |
| Count/event reconstruction | Removing separate MLB quality/event detail while compressing inputs loses value; restoring detail recovers much of the loss | A representation/integration problem, not evidence detailed outcomes do not predict hitting. [Review](hitter-mlb-events-restoration-result.md) |
| Trees for hitting | A fixed shallow replacement compresses elite power and loses despite useful measurement values | Reject that replacement, not all trees or Statcast. Preserve the linear extrapolation benchmark. |
| Foreign integration | Routing, scaling, weighting and source representations changed together; sparse foreign coefficients produced extreme forecasts | Failed construction, not evidence that NPB/KBO results are irrelevant. [Review](hitter-incumbent-representation-review.md) |
| Temporary-absence observations | Corrected source fields change but predictions are identical: the trees never use them | Uninformative predictive test. The new information was not exercised. [Review](hitter-nonmedical-opportunity-result.md) |
| Employment-source correction | Source definitions are genuinely repaired, but no convincing matched forecast gain | Retain correct facts. Stop parser variants; inspect the opportunity mechanism, not another synonym for signing. [Review](hitter-employment-comparison-v2-result.md) |
| Playing-time shortfall as health | A two-year MLB proxy adds little beyond existing role/history; shortfall also includes platooning/demotion | Not a test of next-year minor-league medical prognosis. [Review](hitter-availability-gap-v1-result.md) |
| Six-year career projections | Some earlier long-horizon tests lacked relevant elapsed-career training examples | Unsupported extrapolation, not a clean architecture failure. Later support checks do not retroactively approve the older models. |

There are legitimate negative results too: deeper conditional-workload models,
separate entrant training and the exact offset-removal comparison did not earn
replacement. More flexibility or a simpler equation is not automatically better.
They remain closed unless a newly demonstrated design defect changes the question.

## Why the public gap is not “AI loses by 20%”

The clear current public comparison is playing time: mean absolute PA error
106.41 versus Steamer 92.08, about 15.6% worse. PA squared-error-based error
is much closer, 138.33 versus 135.38, about 2.2% worse. Those are different
summaries, not contradictory findings. The custom common-event hitting comparison
is close, but archive dates and park/environment treatment prevent a clean claim
of named-system superiority. There is no matched full-WAR result demonstrating
the whole UBM is 20% worse.

The completed [public review](practical-hitter-public-units-v51-result.md) locates
an important workload discrepancy: Steamer gives one PA to 386 forecasts, of
which 302 actually get zero. UBM gives that group 22,283 PA versus 5,354 actual.
Outside that group, the older comparison's mean PA error gap is 8.7%, not 16%.
Do not remove those rows, copy public forecasts, or assume all one-PA estimates
were correct. Exact vintage is unknown; more current roster/injury knowledge is
a plausible explanation, not proven for every row. Both source timing AND our
mechanism matter. Preseason depth-chart PA is not the same product as talent-only
ZiPS exposure or a December generic opportunity forecast.

There is nothing surprising about experienced humans building a better system.
They can specify a better prior, preserve useful MLB/minor evidence, understand
league translation and use better job information. Giving an AI more algorithms
does not replace those things. The literature links in the reset plan support
those basics, not a promise that one library will recover the public gap.

## The priority is the opportunity mechanism, not another batting rebuild

Two established-career absence cases make the problem obvious: Tatis gets .134
participation × 296 conditional PA = forty before 635; Hoskins gets .101 × 261
= 26 before 517. Talent survives in both. A different contact bin cannot fix
that near-exit probability. They are not ordinary prospects without MLB evidence.
But Belt's unexpected non-signing shows that “previously good means guaranteed
return” is not a defensible universal rule either.

Prospect underallocation is also real: substantial highest-level experience,
not promotion cameos, accounts for about 83% of the shortage in the completed
[exposure audit](hitter-prospect-exposure-allocation-audit-result.md). Upper
never-debut players total 74,239 PA versus 92,891; lower players instead get
7,055 versus 5,194. A blanket prospect boost is wrong. Pedigree and all 42 level
exposures already enter; saying “add more detail” without following its path
would repeat completed work.

Next work must retain the selected hitting predictions and separate career
continuity from current-season absence in opportunity. First use the COMPLETED
source/input/path receipts to identify which influential employment-linked
workload, roster and recent-work signals produce these near-exit probabilities.
Do not repeat source inventory or the unused-status-feature fit. Contrast all
eligible formerly established absent players with origin-known comparable exits,
not minor fringe players matched only on current zero PA. Distinguish genuinely
dated current job evidence from historical assignment or a tentative return.

Then permit ONE mechanism-level correction only if those paths identify a
specific defect: preserve demonstrated MLB career evidence through a temporary
interruption, without interpreting it as a guaranteed job. Its comparison must
retain current opportunity and the completed employment arm, fixed hitting,
all non-arrivals, prospect guardrails and the public cohort. No named-player
overrides or data-dependent gate/penalty sweep. An explicit model equation and
matched predecessors must precede any new fit. If the same correction was already
tested, use that result rather than rebrand it.

This is a bounded work order, not authorization to promise an improvement before
the mechanism is established. International roles and long-horizon/full-WAR
integration remain separate requirements; do not bolt them on to conceal these
next-year mistakes. Keeping the unchanged incumbent as a benchmark does not
certify its known weak forecasts as acceptable production behavior.

## Rules that replace the previous loop

- Fix incorrect source facts whether or not a score improves. Preserve old
  results as historical anchors, not as a reason to keep erroneous facts live.
- Never call a new component a win merely because it beats a deliberately weaker
  new control; it must also be compared with the strongest relevant incumbent.
- Never call a component a failure if its information was removed, never used,
  misweighted, evaluated at the wrong level/horizon or unsupported in training.
- Split ability error, participation error and conditional-workload error before
  congratulating a close contribution total. Keep ordinary cases and missed stars.
- A model doesn't have to predict every surprising outcome. It does have to avoid
  systematic implausibility in established profiles and show uncertainty honestly.
- One primary baseball question at a time. A completed negative closes its exact
  comparison; no repeated sweep without a concrete new defect. Unit tests and
  source collections are not accuracy gains.

The reset delivers a coherent map, a reviewed decision ledger and a new simple
competence check. Forecasts have not improved during this reset. Both freezes,
the completed once-only 2026 evaluation and the explorer remain unchanged. The
broader practical hitter/player-value goal is unfinished.
