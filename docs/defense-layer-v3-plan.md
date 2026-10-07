# Build defense that contributes to player valuation

2026-10-06. The active goal is a coherent defensive-ability and value layer,
not another tournament of tiny changes to the same minor-league play-share stat.
The selected hitter package still omits general defensive value. Its batting
forecast and the frozen 2026 evaluation remain unchanged.

## What comes first

1. Recover a component ledger from the already captured 2016–2025 MLB position
   measurements: range, arms, double plays, first-base receiving, catcher framing,
   throwing and blocking. Verify run additivity and actual defensive exposure.
   Preserve missing components; do not mistake a shorter historical measurement
   definition for a worse defender. Complete a source/player walkthrough.
2. Establish a defensible MLB range baseline across infield and outfield. Compare
   neutral defense, a transparent recent-history estimate, and a small learned
   reliability/age model. Use later, pooled MLB quality as the target and count
   actual mature, held-player training examples. This is a much broader population
   than the previous minor-league ground-ball cohort.
3. After the range walkthrough, use the same ledger to qualify arms and receiving.
   For catchers, first certify pitches/steal opportunities and distinguish ability
   from the battery's opportunity mix. An innings-based catcher run rate can be
   a value descriptor, but cannot be mislabeled an isolated framing/arm skill.
4. Assemble the defended components with independently forecast defensive
   innings/positions. Positional adjustment is separate from fielding quality;
   a catcher label alone must not supply full-time catcher value. Test delivered
   runs with the unchanged playing-time forecast, and then total player value on
   an identical expanded target. Keep talent and integration verdicts separate.
5. For players without MLB evidence, keep an explicit uncertain fallback and
   position-development distribution. Inspect actual minor opportunities and
   traditional fielding/role history for transfer to MLB; do not reopen the
   closed adjusted ground-ball share or call non-arrivals poor defenders. Lower
   minors require older joint input/MLB-outcome support before a transfer claim.

Every fitted comparison gets full player calculations and origin-known peers,
including losses and exits, before another model is selected. Completed milestone
code, contracts, reports and limitations are committed; neither the production
forecast nor the explorer changes automatically.

## Why small losses have not settled the question

The last adjusted-share comparison was narrow: just 89 people in its ordinary
test origin, with most detailed profiles sparsely represented in training. It
used team ground balls, not each fielder's reachable chances. Its small loss
does not invalidate defensive information generally. Nor does it validate that
particular feature: its player review found both gains and false positives.

Older work contains positive MLB defensive-history evidence, but some targets
were standardized scores or runs divided by batting PA, and integration could
confound quality with future position/exposure. Another positional test rejected
a candidate partly over a mean-bias deterioration of roughly 0.00008 WAR per
player. That is not a sensible standalone practical veto. Keep the old verdict
as history, but do not use microscopic differences as blanket conclusions.

The new comparison has a simpler purpose: does a trustworthy, appropriately
shrunk defensive record identify later good and poor MLB defenders better than
assigning everyone neutral defense? A small learned-model loss to that baseline
will retain the useful baseline, not send us back to square one.

## Literature used for design, not copied coefficients

[Mitchel Lichtman's UZR primer](https://blogs.fangraphs.com/the-fangraphs-uzr-primer/)
argues for regression of noisy observations, multiple years with recency weights,
and attention to aging. Those principles motivate the baseline, not a claim that
UZR reliability equals Statcast reliability.

[FanGraphs' 2024 WAR update](https://blogs.fangraphs.com/2024-fangraphs-war-update/)
describes native Statcast range, arms and catcher components. Its removal of the
older UZR double-play component is a reminder that a native component ledger is
not automatically identical to FanGraphs WAR. Any final WAR bridge must specify
which components are included and avoid duplicate credit.

## Completion standard

An audited, reproducible defense forecast with usable tested baselines; separate
quality, position and opportunity outputs; clear sparse-player fallbacks; a fair
integration test and readable player examples. Tracking availability, rule changes
such as ABS, and unsupported lower-minors transfer remain visible limitations.
One successful range comparison alone does not complete the whole active goal.
