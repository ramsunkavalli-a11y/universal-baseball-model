# Universal Baseball Model

Public-data baseball research working toward a trade-value estimate for every
player, refreshed after each game and material transaction, beginning with MLB
organizations and affiliated players. The team-control/payroll foundation, first
every-player multi-year WAR input and static contract-economics engine are now
connected. Uncertainty and market-price fits are still required before dollar rankings.

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
targets. The official `fullRoster` source now supplies the broad player denominator;
the remaining 0.20% multi-team outliers stay explicit ownership reviews.

Phase 1 foundations now include a [rights-universe contract](docs/player-rights-universe-contract.md),
a censored [career-outcome panel](docs/career-outcome-panel-contract.md), a real
2015–2024 MLB outcome inventory, and a transparent pitcher-component baseline. See the
[current status](docs/project-status.md) for results and boundaries.
The [Contract Economics v0 methodology](docs/contract-economics-v0-methodology.md)
defines the new downstream valuation boundary and its remaining data gaps.
The [Projection v1 guardrails](docs/projection-v1-guardrails.md) define the common
multi-year hitter/pitcher path identity, universal coverage requirement and historical
plausibility checks that must be satisfied before those layers connect.
The [Hitter Opportunity v1](docs/hitter-opportunity-v1.md) implementation supplies
team-neutral multi-year MLB-arrival and PA paths with explicit inactive/no-history
fallbacks; its first certified league materialization is still pending.
The matching [Pitcher Opportunity v1](docs/pitcher-opportunity-v1.md) calculation keeps
arrival, BF and role probabilities separate and uses no current-team depth.
The [historical opportunity source result](docs/opportunity-history-source-result.md)
records the real 2018–2024 official cohort materialization and its 2020 exclusion.
The [remaining-rights timeline](docs/remaining-rights-timeline.md) prevents live value
from counting production already earned or salary already paid.
The [current opportunity result](docs/current-opportunity-paths-2026-09-08.md) supplies
complete team-neutral 2027–2032 hitter and pitcher workload paths.
The [current conditional WAR result](docs/current-conditional-war-paths-2026-09-08.md)
adds the first universal rate baseline, explicit population fallbacks and controlled
WAR coverage without promoting the output to a public ranking.
The [affiliated translation result](docs/affiliated-level-translation-result.md)
describes the provisional same-player/same-season bridge that replaces most pure
minor-league population priors while preserving a fallback.
The [current contract-economics input result](docs/current-contract-economics-inputs-2026-09-08.md)
connects whole-player expected WAR to all 50,100 future control rows while keeping
missing salaries, buyouts and market assumptions explicit.
The [current baserunning result](docs/current-baserunning-rates-2026-09-08.md)
reuses the frozen steal and advancement models in the live hitter path; defense is
now the remaining average-zero hitter component.
The [modern pitcher-aging test](docs/modern-pitcher-aging-result-2026-09-08.md)
rejected a newly fitted curve on 2022–2025 data and retained Tango's regressed curve.
The [current rest-of-season result](docs/current-rest-of-season-2026-09-08.md)
connects 2026 remaining WAR and day-prorated base salary to the rights interface while
rejecting unresolved payroll/ownership joins.

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
