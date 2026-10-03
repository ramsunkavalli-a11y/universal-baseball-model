# Separate current-MLB workload training does not improve this assembly

2026-10-03. **Not adopted.** Same historical cohorts and unchanged batting rate,
future exits retained, all noncurrent-MLB forecasts bit-exact. V33b stays the
working model; V38 stays a research workload challenger. Goal is not complete.

The [pre-fit contract](practical-hitter-v39-contract.md) changes one thing:
positive origin MLB PA selects a dedicated direct workload learner trained
only on similarly origin-active players. It does not use future participation.
Same tree settings and 239 inputs as V38. All 35 subset preflights preceded fits.

| Population | Shared games PA RMSE | Dedicated MLB PA RMSE | Shared games PA MAE | Dedicated MLB PA MAE | Shared games value RMSE | Dedicated MLB value RMSE |
|---|---:|---:|---:|---:|---:|---:|
| All 30,506 | 61.237 | 61.418 | 21.335 | 21.447 | 0.43976 | 0.44051 |
| Public active 1,789 | 143.191 | 143.668 | 111.320 | 111.774 | 1.01598 | 1.01667 |
| Old V24 matches 4,396 | 124.321 | 124.890 | 83.090 | 83.604 | 0.90859 | 0.91041 |

Equal-year losses, nominal player-clustered paired uncertainty. Public PA MSE
difference +136.74, 95% interval [−208.39,+464.09]; value MSE +0.001406,
interval [−0.006713,+0.009190]. There is no useful established win. Steamer
public PA RMSE/MAE remain 135.019/92.399. Converted batting value is not a
clean talent-superiority comparison; contribution is not full WAR.

Brief-debut PA RMSE rises 132.358→132.481, regular-player 153.449→153.935.
The 2023-origin total grows 192,114→192,731 against actual 182,194. Noncurrent
MLB totals and the continuing lower-minor excess cannot improve by construction.
Current-MLB players who later have zero PA retain forecasts in the evaluation:
their expected PA increases slightly, not a solved exit process.

## What actual player paths show

Seventeen reviews include raw yearly/level PA, games, HR/K/walks, actual inputs,
saved split-path accounting, unchanged batting rate and product, actual outcomes,
origin-only peers and distinct-person subset support. All heads replay.

- Story improves 149→247 expected PA versus actual 654; preserved regular use
  matters, but talent/workload still both miss the eventual rebound.
- Steer improves 233→270 versus 665, while Vientos loses a nearly exact workload
  forecast: 233→135 versus 233 actual. His value looks better only because the
  unchanged batting rate was too optimistic.
- Torkelson falls 425→335 versus 684. A poor young debut does not necessarily
  remove the organization's incentive to give him another full opportunity.
- Votto falls 609→564 versus 707; the branch does not fix established regular
  conservatism. Alvarez's future absence still creates a large false high.
- Lux and Kurtz remain exactly unchanged because they did not play MLB at
  origin. This branch must not be described as solving return or first arrival.
- Langford's PA becomes almost exact, but Turner’s near-exact delivered value
  still combines excess workload with understated batting talent.

One questioned source flag was not a confirmed bug: Bellinger was a non-roster
spring invitee in 2017. His zero listing is not contradicted by this record.
[MLB report](https://www.mlb.com/news/dodgers-promote-top-prospect-cody-bellinger-c226418212)
No retroactive flag change or known-result tuning was made.

See [player walkthrough](evidence/practical-hitter-v39/player-walkthrough.md)
and [full matched scores](evidence/practical-hitter-v39/scores.json).

## Next meaningful work, not more branches

Close this workload architecture batch. Reassess whether prior park/opponent-
adjusted contact and play-by-play winners have compatible targets and proper
chronological provenance for the broad batting population. Integrating those
sources is more substantive than changing another PA cutoff or event prior.
Source compatibility must be checked before claiming an old winner transfers.
Protected 2026 and frozen/deployed forecasts remain unchanged.
