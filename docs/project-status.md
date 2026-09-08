# Project status and handoff

Updated 2026-09-07. This is the current start-here document.

## Active plan

The user has prioritized model quality and paused interface development. Read the
[authoritative product roadmap](product-roadmap.md) first. It supersedes narrower
component-specific next-experiment lists for prioritization while preserving their
results and frozen decisions.

The clarified end goal is every-player trade value updated with each game.
The [direction review](trade-value-direction-review.md) finds useful foundations
but missing career/control/cost and continuous-update integration. It also identifies
older opportunity/roster models to reuse before building another challenger.
The broader roadmap now includes pitcher and whole-player value integration;
website work remains paused. No new valuation model has been promoted.

This work builds on the recovered-opportunity commit `7c2a874`. It contains model
foundations, experiment records, and the plan. It does not change a website or
promote a model. Protected main and the v1 release remain unchanged until integration.

## Phase 1 foundation progress

- The player-rights universe contract now preserves every required player, represents
  missing evidence as `unknown / prior_only`, rejects future observations and fails
  closed on ownership conflicts. Certified dated 40-man membership is connected as
  one narrow evidence family. A separate candidate inventory unions broad discovery
  sources with provenance while preventing candidate presence from asserting an owner.
- The official `fullRoster` source is the primary player-discovery source: 7,891
  players, with 99.80% having one candidate organization. Its 16 cross-organization
  outliers prevent using it alone as final rights proof, not using it as the denominator.
  A chronology-safe official transaction ledger is now implemented for reconciliation;
  ownership-changing state transitions remain a separate, not-yet-authorized gate.
- The career-outcome panel makes completed-season absence an observed zero and later
  seasons right-censored. A real official 2015–2024 inventory contains 10,585 batting
  player-seasons, 8,095 pitching player-seasons and 3,777 distinct MLB players.
- A transparent pitcher component baseline now separates K, UBB, HBP, HR and other-BF
  rate skill from opportunity. It beat a global population comparator in every rolling
  2018–2024 fold; equal-fold log loss was 0.98044 versus 0.98500.
- Team-control arithmetic and the conservative StatsAPI replay are implemented. A
  Padres working sample plus Giants holdout confirms FanGraphs as the dated
  service/options baseline, StatsAPI for forward changes and Rule 5, and transactions
  as a bounded exception layer. Broad comparison coverage is 95.2% and 98.4%; Rule 5
  year agreement is 180/186 where both values are available.
- All 30 payroll workbooks normalize into 915 player records, 3,720 annual terms, 180
  clauses and 417 other payments. Stable IDs attach 870 players; current official
  roster entries corroborate the remaining 45 exact-name identities. Payroll identity
  review is now zero, while liabilities for former roster members remain separate from
  current team control.
- The 2026-09-08 league build contains 8,399 affiliated players, 8,335 future-path rows
  through 2031 and a complete 133-player Super Two pool. The calculated cutoff is
  `2.144` (488 days), with 30 selected because the cutoff is tied. FanGraphs supplies
  the 2026 opening balance; StatsAPI supplies in-season service through the as-of date.

Contracts and results: [rights universe](player-rights-universe-contract.md),
[full-roster source decision](affiliated-full-roster-source-result.md),
[transaction ledger](rights-transaction-ledger-contract.md),
[career panel](career-outcome-panel-contract.md),
[career inventory](career-mlb-outcome-inventory-result.md),
[pitcher baseline](pitcher-component-baseline-result.md).

## Completed research

- Recovered the original 2024 opportunity forecast and verified exact IDs and
  official targets against O2026D. Its lower errors support reuse of the older
  model, with documented subgroup limits. [Comparison](recovered-opportunity-comparison.md).

- Tango-focused review executed: saved translation forecasts still improve
  common-MLB-centered absolute error; historical-support subgroups remain
  descriptive and selection risk remains. The old richer opportunity model has
  promising recorded results and should be recovered for an identical-target
  comparison. [Evidence and next work](tango-focused-model-work.md).

- C2026A: two all-level output-calibration candidates failed.
  [Result](hitter-v2-C2026A-result.md).
- T2026B: one competition-normalized history candidate failed its prospective
  all-level gate. Its presaved MLB-conditional component materially improves
  prediction for prior-minor players but still needs calibration and confirmation.
  [Result](hitter-v2-T2026B-result.md).
- C2026C: two MLB-specific calibration candidates failed. The error audit shows
  much larger optimism among brief MLB call-ups than among players with 100+ PA.
  Future exposure is a diagnostic label, never a preseason predictor or exclusion
  rule. [Result and next step](hitter-v2-C2026C-result.md).

## Next modeling task

The main candidate denominator and phase-one control/cost path are now built. Phase two
should resolve only the 21 multi-organization ownership cases and the bounded opening-
state/transaction exceptions, then add granular fourth-option, suspension and special
CBA rulings. Unresolved paths stay unknown. The completed denominator can now support
real non-arrival, inactivity and attrition labels rather than survivor-only modeling.

In parallel, reconnect the recovered opportunity pipeline and its frozen B2 inputs,
then declare population-prior fallbacks for inactive/no-history players. Retain O2026D
as the simple benchmark and the unchanged T2026B MLB-conditional transport component
as a developmental hitter reference. Stop global calibration searches. Do not convert
the component outputs to career value before participation, pitcher workload, aging,
rights and cost paths are integrated.

The 2022–2024 seasons are disclosed development evidence. Protected 2026 remains
closed. Do not claim long-term value or publish a model from these findings.
Preserve original G0/C0/Marcel benchmarks and all failed decisions.

## Reproduction

New model primitives have chronology, gradient, probability-conservation, and
player-cluster resampling tests. The runners require existing generated research
artifacts; hashes bind the inputs. They reject overwriting an inspected candidate
run. The local implementation passed its tests before this branch was prepared;
branch-specific verification is recorded in the pull request.

Current verification: Ruff passes across `src`, `scripts` and `tests`; 1,087 tests
pass. Four pre-existing contract tests fail only because their hash-bound ignored
research artifacts are absent in this checkout. No new test failure was observed.

The prior long status file is preserved in
[project history through August 26](project-history-through-2026-08-26.md).
