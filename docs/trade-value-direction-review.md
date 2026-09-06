# Direction review: continuously updated trade value

Reviewed 2026-09-06 against the user's clarified goal: trade value for every player,
updated with each passing game. This is a repo/literature review and design
recommendation, not a fitted valuation model. Existing failed experiments remain
failed; protected 2026 player outcomes were not accessed for modeling.

## Verdict

We have useful ingredients, but the active plan has become too narrow. Improving
next-season batting and participation moves toward trade value; it does not by
itself deliver it. The architecture needs an explicit destination now, while
component validation continues. Repeated component-only experiments without a
career, contract, coverage, and update plan risk continuing the project's drift.

KATOH is a useful prospect-production reference, not the whole trade-value target.
Mitchell's 2016 revision lengthened projection windows for lower-level players to
capture more of their eventual controlled MLB production. A one-year arrival
target would miss much of a young low-minors player's value. His published method
was itself an approximation to team-control value, not a contract-rights engine.
[KATOH methodology](https://blogs.fangraphs.com/an-improved-katoh-top-100-list/).

## Recommended definition

Use **expected remaining surplus value of the player's transferable team rights,
in present-day dollars**, as the common reference measure. Show expected remaining
MLB wins and forecast uncertainty alongside it. Keep a separately labeled estimate
of likely market return for later, when transaction evidence supports it.

Conceptually, for each simulated future career/contract path:

`surplus = discounted remaining MLB production value - discounted remaining costs`

Then average across paths. Production is valued only while the acquiring club
holds relevant rights; contractual obligations may survive injury, release, or
the end of useful production. Include salary, options/buyouts, retained salary and
other material obligations without subtracting historical sunk acquisition costs.
Model exercise/non-tender/opt-out decisions explicitly where material. Guaranteed
negative-value obligations must not disappear through a universal zero floor.

This is a proposed economic reference, not a claim that every club pays the same
price. Baseball Trade Values publicly uses surplus value plus market adjustments;
FanGraphs' trade rankings incorporate contracts, future production, and which
buyer is most motivated. That supports separating reproducible player-rights
value from deal-specific price. Do not import BTV's historical dollars-per-win or
arbitration assumptions as current constants without testing.
[BTV major-league approach](https://www.baseballtradevalues.com/valuing-major-leaguers),
[FanGraphs trade-value approach](https://blogs.fangraphs.com/2025-trade-value-introduction-and-honorable-mentions/).

Service time governs arbitration and free-agency eligibility; track it separately
from seasons with batting appearances.
[MLB service-time definition](https://www.mlb.com/glossary/transactions/service-time).

## Repo evidence and reuse

| Required part | Evidence in the reviewed branch | Assessment |
|---|---|---|
| Identity and dated evidence | `canonical-data-contract-v0.2.md` separates event time, source bytes, and defensible knowledge availability | Useful foundation for historical replay; not proof of an operating update service |
| MLB batting skill | T2026B conditional component improves historical minor-origin MLB batting error; C2026C fixes failed | Keep developing the useful component; no career-value claim |
| MLB opportunity | O2026D gives certified batting-PA zeros and a transparent benchmark | Relevant, but one-year prior-active population only |
| Existing richer opportunity work | `playing_time_model.py` already implements logistic participation plus positive-PA count distributions, with age, prior PA, 40-man and B2 variants; `playing-time-v1-development-checkpoint.md` records a development pass | Reuse and compare on repaired inputs before building another model; B2-dependent features need revalidation |
| Historical roster evidence | `playing_time_roster_source.py` supports dated 40-man membership, explicitly limits unreliable row status/team fields | Reuse membership adapter; do not infer historical injury/role from diagnostic fields |
| Aging/development | `projection-batting-v1-validation-2024-result.json` rejects the old age/level candidate | We do not have validated career paths simply because aging code exists |
| Whole-player production | `player-value-v1-final-aggregation-contract.md` and final result assemble batting, running, defense, position and replacement into WAR | Useful accounting machinery; upstream v1 batting problems prevent treating the assembled ranking as sound |
| Coverage | That final contract excludes 940 incomplete-component players and appends six outside-snapshot MLB players as zero rows | Incompatible with universal value coverage as a permanent policy |
| Pitchers | Pitching source inventory, performance primitives and one-year development contract exist | Valuable start; no integrated pitcher career-value model located |
| Uncertainty | `player-value-v1-uncertainty-contract.md` simulates next-season WAR around frozen inputs | Reusable mechanics, not validated multi-year trade-value uncertainty |
| Financial/control layer | No implemented salary, service-time, arbitration, surplus-value or trade-value layer found in the searched source tree | Essential missing layer |
| Continuous updates | Dated sources and snapshot machinery exist; searched workflow schedules show security scanning, not game-driven valuation | End-to-end update/replay behavior remains unimplemented or unproven |

The recent opportunity batch partly revisits an area already developed in v1.
Its contribution is an independently checked simple reference and source boundary,
not the invention of MLB opportunity modeling. Next work must inventory and
reuse the richer model and roster evidence, not silently replace them.

## Research implications

**Estimate career paths, including failure and delayed arrival.** Baseball-specific
aging research treats dropout as missing data rather than assuming observed
survivors represent everyone. That supports jointly addressing development and
opportunity, including injuries, release, role changes and return from inactivity.
It does not prove any particular imputation method will win here.
[Nguyen and Matthews](https://arxiv.org/abs/2210.02383).

**Use pooling for sparse players.** Hierarchical baseball work combines past
performance with age/position and shares information across players and time.
This supports population-based forecasts with wide uncertainty for sparse or
no-history players, rather than excluding them or calling them zero talent.
[Jensen, McShane and Wyner](https://arxiv.org/abs/0902.1360).

**Avoid counting risk twice.** My modeling recommendation is to put non-arrival,
injury and attrition into career-path probabilities. Any additional economic risk
premium must be separately justified, not another automatic haircut for failures
already included. Also, expected skill times expected playing time is generally
not expected production when they are correlated. Joint path simulation or an
explicit conditional model should address that dependence before final assembly.

**Prospect evidence must cover the long tail.** Edwards' historical prospect
valuation research connects prospect tiers and future value while emphasizing
nonlinear development. BTV also describes highly uneven prospect outcomes and
scouting-update lag. Those are useful comparisons, but top-100/FV-grade evidence
alone does not validate every unranked player. Scouting can be a dated input or
benchmark where usable; it need not become a prerequisite for every row.
[Edwards](https://blogs.fangraphs.com/an-update-to-prospect-valuation/),
[BTV minor-league approach](https://www.baseballtradevalues.com/valuing-minor-leaguers).

## What every-game updating requires

Updating a forecast after a game is different from refitting the entire model.
Use versioned fitted models to incorporate new evidence and regenerate remaining
career/value forecasts. Retrain at a separately chosen cadence. FanGraphs' Depth
Charts illustrate the distinction between performance projections and changing
playing-time expectations; our exact update design still needs validation.
[Depth Charts explanation](https://library.fangraphs.com/depth-charts/).

Each update should incorporate completed games, corrected data, promotions,
injuries, transactions, contracts and the passage of time. A player's remaining
control can become less valuable even without a game. Past production informs
the forecast but is no longer production a buyer can acquire.

Persist one dated value record with player/rights owner, source cutoff, last game,
model version, expected remaining WAR, surplus estimate/range, coverage tier and
the main reasons for change. Distinguish model revisions from new evidence. A
replayed source must not double-count a game; late corrections must be traceable.
Freshness cannot exceed the source's actual availability.

Historical validation needs both event-time and information-availability checks.
Do not use corrected end-of-season information as if it were known in April.
First prove game-by-game replay on completed development seasons. No scheduler or
live publication is created by this review.

## Revised sequence and materiality

1. **Define the player-rights universe and value contract.** Start implementation
   with MLB organizations and all affiliated/reserve players, including injured,
   inactive, unranked and newly signed players. The ultimate scope can extend to
   other leagues using explicit rights/translation adapters. Free agents can have
   a talent/free-agent value without an incumbent MLB club owning trade rights.
   Unknown data gets a flagged prior/range, never a silent zero or dropped row.
2. **Inventory and reuse existing components.** Compare the old opportunity model
   and O2026D on identical repaired targets and dated rosters; isolate invalid B2
   dependencies. Map defense/position fallbacks and pitcher gaps. Continue only
   batting fixes that materially affect projected production or uncertainty.
3. **Build the financial/control source table and career-label inventory.** Record
   contracts and rights as of date. Use mature historical career cohorts or
   explicitly censored outcomes: a recent prospect's unobserved future is not
   zero. The recent one-year evaluation seasons cannot supply mature long-term
   labels for every player.
4. **Build a simple integrated research model.** Connect skill, development,
   participation/workload, whole-player wins and control/cost paths. Include
   hitters and pitchers on a common win/value scale, avoid two-way double-counting,
   and keep each component replaceable. No public deployment until coherent.
5. **Replay sequential updates and validate the end goal.** Assess production and
   participation calibration, cumulative controlled production, interval coverage,
   and stability across levels/ages/roles. Separately compare pre-trade estimates
   with later trades and free-agent prices; deals are noisy observations, not an
   assumption of equal package value. Reserve independent time periods for final
   confirmation; protected 2026 remains closed to new model evaluation.

The stopping rule should be driven by material impact on player value and
uncertainty. Fix identity, coverage, leakage, denominator, rights/cost and scale
errors. Bound small event-classification discrepancies and move on when their
effect is immaterial. Preserve reproducibility, but do not make a perfectly
reconciled batting component a prerequisite for defining the missing valuation
layers. Website work remains paused.
