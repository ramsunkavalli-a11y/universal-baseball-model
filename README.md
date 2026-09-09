# Universal Baseball Model

Public-data baseball research working toward a trade-value estimate for every
player, refreshed after each game and material transaction, beginning with MLB
organizations and affiliated players. The team-control/payroll foundation, first
every-player multi-year WAR input and static contract-economics engine are now
connected, including named uncertainty and market-price assumptions. Historical
end-to-end replay is still required before dollar rankings.

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
targets. Its form was later confirmed on the untouched 2025 test, but the temporary
scoring-parameter artifact expired; current forecasts therefore retain the labeled
historical fallback. The official `fullRoster` source supplies the broad player
denominator, while dated 40-man and transaction evidence now resolves all current
multi-team ownership conflicts.

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
The [Hitter Opportunity v2 development result](docs/hitter-opportunity-v2-development-result.md)
adds a reproducible universal one-year candidate using recent MLB/MiLB opportunity and
exact-date 40-man membership. It won all four rolling tests, while remaining explicitly
unconfirmed until protected 2026 outcomes are available.
The matching [Pitcher Opportunity v1](docs/pitcher-opportunity-v1.md) calculation keeps
arrival, BF and role probabilities separate and uses no current-team depth.
The [historical opportunity source result](docs/opportunity-history-source-result.md)
records the real 2018–2024 official cohort materialization and its 2020 exclusion.
The [remaining-rights timeline](docs/remaining-rights-timeline.md) prevents live value
from counting production already earned or salary already paid.
The [current opportunity result](docs/current-opportunity-paths-2026-09-08.md) supplies
complete team-neutral 2027–2032 hitter and pitcher workload paths.
The [current organization resolver](docs/current-organization-resolution-2026-09-09.md)
closes season-wide roster conflicts with dated 40-man membership and exact official
transactions while keeping broad one-team assignments labeled provisional.
The [current conditional WAR result](docs/current-conditional-war-paths-2026-09-08.md)
adds the first universal rate baseline, explicit population fallbacks and controlled
WAR coverage without promoting the output to a public ranking.
The [affiliated translation result](docs/affiliated-level-translation-result.md)
describes the provisional same-player/same-season bridge that replaces most pure
minor-league population priors while preserving a fallback.
The [current contract-economics input result](docs/current-contract-economics-inputs-2026-09-08.md)
connects whole-player expected WAR to all 50,058 future control rows while keeping
missing salaries, buyouts and market assumptions explicit.
The [current baserunning result](docs/current-baserunning-rates-2026-09-08.md)
reuses the frozen steal and advancement models in the live hitter path.
The [current defense result](docs/current-defense-rates-2026-09-08.md) connects frozen
general-range skill, MLB position outs and native run conversion for 2027 while
keeping unsupported catcher and later-year defense neutral.
The [modern pitcher-aging test](docs/modern-pitcher-aging-result-2026-09-08.md)
rejected a newly fitted curve on 2022–2025 data and retained Tango's regressed curve.
The [current rest-of-season result](docs/current-rest-of-season-2026-09-08.md)
connects 2026 remaining WAR and day-prorated base salary to the rights interface while
rejecting unresolved payroll/ownership joins.
The [integrated current-and-future economics result](docs/current-and-future-contract-economics-2026-09-08.md)
now values those 2026 remaining rights and the 2027–2032 control path together, with
discounted point and sensitivity totals while retaining a research-only boundary.
The [provisional current hitter opportunity v2 integration](docs/current-hitter-opportunity-v2-2026-09-08.md)
scores every current hitter and carries the selected development model through the same
pipeline without overwriting the retained baseline.
The [combined universal opportunity v2 integration](docs/current-universal-opportunity-v2-2026-09-08.md)
adds the selected pitcher and direct horizon 2–4 models and records the full WAR and
contract-value sensitivity. Horizons 5–6 remain labeled historical fallbacks.
The [protected 2026 confirmation contract](docs/opportunity-v2-2026-confirmation-contract.md)
now has immutable 2025-snapshot forecasts for selected and benchmark models; evaluation
waits for final 2026 regular-season outcomes.
The [Phase 1 replay checkpoint](docs/phase1-sequential-replay-current-checkpoint.md)
retains all 8,393 current rights-universe players in one dated value interface, with
8,369 available records and 24 explicit reviews. It proves current coverage and
accounting, not historical accuracy or ranking readiness.
The [control source capture](docs/control-source-capture.md) retains and hash-verifies
the 230 parsed official responses behind that checkpoint while clearly separating
parsed-value reproducibility from original HTTP-byte fidelity. The same build can now
run offline from those captures and reproduced all core control outputs byte for byte.
The [historical Opening Day control source](docs/historical-opening-day-control-source.md)
adds MLBAM-keyed 2024 and 2025 service/options snapshots for retrospective replay while
keeping later-retrieved pages distinct from true vintage evidence. Private member
workbooks validate those snapshots, add projected PA/IP, and extend coverage to 2023.
The [2025 historical contract source audit](docs/historical-contract-source-audit-2025.md)
now includes a fail-closed annual valuation gate that separates guaranteed salary,
calculated arbitration, free agency and unresolved options.
The [first historical projection path](docs/historical-projection-paths-2025.md)
scores the 2025 Opening Day universe with models trained only through 2024, keeps
FanGraphs PA/IP as an external scale check and leaves weak fallbacks visible.
The [2025 historical control/value join](docs/historical-control-value-2025.md)
then connects 7,998 owners and calculates 39,648 of 39,990 owned annual rows while
retaining missing owners, service, Super Two and contract exceptions as reviews.
The [scored 2025 replay](docs/historical-replay-result-2025.md) shows nearly exact
league workload, lower large-error RMSE but worse individual MAE than simple
carry-forward, modest component-skill gains and a 6.6% high neutral-WAR point total.
Its historical checkpoint and the current checkpoint pass the mechanical sequence.
The [same-model October update](docs/same-model-projection-update-2025.md) permanently
stores the March opportunity fits, reuses them without refitting, and separates
shared-player projection movement from player-universe turnover.
The [current availability boundary](docs/current-availability-status-2026-09-08.md)
zeroes only official season-out cases and carries unresolved injury returns as an
availability sensitivity rather than an invented recovery forecast.
The [current multi-year uncertainty result](docs/current-war-uncertainty-2026-09-08.md)
uses historical workload spread and player evidence strength to supply all future
contract rows with honest Phase 1 WAR sensitivities.
The [free-agent market source checkpoint](docs/free-agent-market-source-2026-09-08.md)
accepts public FanGraphs contract facts for 2020–2026 and maps every sampled row to
MLBAM without names. Historical projected-WAR cells are absent, so signing-time
forecasts are rebuilt from dated official history before any market price is promoted.
The [free-agent market result](docs/free-agent-market-result-2026-09-08.md) accepts
FanGraphs' published 2026 three-tier curve as the main reference, independently checks
the one-year scale, and keeps future growth separate as an explicit scenario.
The [arbitration cost baseline](docs/arbitration-cost-baseline-2026-09-09.md) applies
the current FanGraphs class shares to prior-season WAR value, preserving salary lag
and the four-year Super Two progression.
The [full contract-economics scenario](docs/current-contract-economics-scenario-2026-09-09.md)
calculates 50,058 future annual rows and isolates 16 contract exceptions while
keeping the unsigned successor CBA explicitly hypothetical.

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
