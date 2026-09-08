# Universal Baseball Model

Public-data baseball research working toward a trade-value estimate for every
player, refreshed after each game and material transaction, beginning with MLB
organizations and affiliated players. The valuation/update system is not yet built.

**Current priority: get the model right before building a public tool.** The
[authoritative product roadmap](docs/product-roadmap.md) defines the active Phase 1
and Phase 2 sequence. Read it first, then the
[status and handoff](docs/project-status.md). Component-specific plans are historical
records when they conflict with that sequence.

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
no-history player coverage remains incomplete. The recovered richer opportunity
forecast improves 2024 participation Brier by 12.6% and PA RMSE by 12.5% on identical
targets. The next blocking task is a dated affiliated-player/rights denominator beyond
the 40-man roster; the official `fullRoster` source failed its ownership-conflict gate.

Phase 1 foundations now include a [rights-universe contract](docs/player-rights-universe-contract.md),
a censored [career-outcome panel](docs/career-outcome-panel-contract.md), a real
2015–2024 MLB outcome inventory, and a transparent pitcher-component baseline. See the
[current status](docs/project-status.md) for results and boundaries.

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
