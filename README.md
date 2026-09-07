# Universal Baseball Model

Public-data baseball research working toward a trade-value estimate for every
player, refreshed after each game and material transaction, beginning with MLB
organizations and affiliated players. The valuation/update system is not yet built.

**Current priority: get the model right before building a public tool.** Read the
[current model plan](docs/current-model-plan.md) and
[status and handoff](docs/project-status.md).

The [trade-value direction review](docs/trade-value-direction-review.md) maps
existing model work to career production, team rights/costs, uncertainty and
continuous updates. Those layers define the destination; batting is one component.

Competition-normalized historical outcomes are a promising MLB-conditional batting
component. Among prior-minor players subsequently observed in MLB, that component
reduced pooled wOBA error by 29% relative to G0 in disclosed 2022–2024 tests. This
does not establish MLB arrival, playing time, career value, or production readiness.

The latest [MLB calibration experiment](docs/hitter-v2-C2026C-result.md) rejected
both proposed corrections. Errors concentrate among brief MLB call-ups. The new
[opportunity benchmark](docs/hitter-v2-O2026D-result.md) includes verified zero MLB
batting-PA outcomes and improves participation probability error by 10.0% over a
prior-exposure-only reference. Playing-time improvements are modest; inactive and
no-history player coverage remains incomplete. The next task is auditing those
omissions and prior-date role/age availability before a player-specific alternative.

The three questions stay separate: batting ability against MLB competition,
probability and amount of MLB opportunity, and development over the selected value
horizon. Website work is paused. Published v1 and all earlier failed gates remain
historical records, not current model-readiness claims. Protected 2026 outcomes
remain closed; repeatedly inspected years are development evidence.

## Development

Install the package with its development dependencies and run `pytest` and
`ruff check src scripts tests`. Tests import the current checkout. Older research
integration tests require the hash-bound generated artifacts named in their
contracts; these are not part of a fresh source-only clone.

The new runners and contracts preserve every tested result. Saved prediction
surfaces and input manifests provide reproducibility without rewriting source
certificates or tuning failed candidates. See each contract for exact scope.
