# Repair program following the deep methodological review

2026-09-25. Supersedes the immediate execution order, not historical scores or
the protected 2026 contract. Findings and source evidence:
[deep review](baseball-methodology-deep-review-2026-09-25.md).

## Goal

Resolve the confirmed measurement/estimand problems before claiming new player-
value gains: build a defensible minor-league defensive-opportunity ledger,
certify catcher event capture, test aligned participation/workload weights,
and distinguish component accuracy from compensating errors in whole value.
Deliver versioned evidence and narrow retain/reject/inconclusive decisions.
Preserve current forecasts until a separately justified release passes.

This is an ordered program, not permission to fit all branches simultaneously
or keep searching until every component improves.

## Milestone 1 — Defensive measurement and failed-test triage

Start here. No new skill learner until the ledger is certified.

1. Reproduce the old first-touch counts on an explicitly reconciled set of games.
   Keep hits, outs, errors and unknowns. Identify whether coordinates represent
   comparable ball locations across outcomes; document unavailable precision.
2. Build a separate Total-Zone-style candidate that assigns through-ground-ball
   hits to plausible infield responsibility shares, not to the recovering OF.
   Include 1B/pitcher/unknown accounting. Do not copy numerical shares from a
   modern MLB environment without testing historical transport; distinguish a
   fixed literature benchmark from any earlier-data-estimated allocation.
3. Verify per-play responsibility conservation; no event disappears because it
   was missed; record ambiguity rather than guessing a named fielder. Adding an
   outfield recovery must not erase the original infield chance. Check ID/position
   substitutions and duplicate/conflicting records.
4. For catchers, select a fixed source-validation sample before opening event
   results: completed pre-2026 regular-season games spanning old/new years and
   all supported levels. Reconcile SB/CS and PB/WP against same-game official
   records, distinguishing pickoffs, multiple events, inning-ending steals and
   unknown identities. Report recall by event type, not just total accuracy.
   Access public historical feeds only; no new 2026 results.
5. Fail the source gate if systematic outcome-dependent loss cannot be explained
   or bounded. This may conclude "cannot test reliably yet" rather than build
   another model. No catcher refit merely because extraction was changed.
6. Predeclare persistence/transport tests only after the source decision. Compare
   old versus repaired measurement on identical covered games and a complete-
   population sensitivity. Separate movement between parks/levels and returning
   players. Source gates are accounting/coverage requirements, not optimized
   against which version has the best future RMSE.

Deliver: source-validation report, versioned candidate opportunity data or an
explicit blocker, semantic regression tests, and exact claims withdrawn/reopened.

## Milestone 2 — A single controlled workload-weighting experiment

Before fitting, lock exact inputs and contrasts. Use the repaired F/D panel,
same eligible historical rows/features/engine settings/cutoffs, same activity
forecasts and same horizon tests as archived D. Primary change: retain activity-
fit identity weights when conditioning on positive PA, instead of recomputing
them among active rows. Do not change participation, feature selection policy,
clipping, COVID handling, roster dates or model hyperparameters in this comparison.

The experiment asks whether **this weighting change** improves conditional
workload and delivered prospect PA. It cannot fix missed arrivals by construction.
Use prospect three-year PA mean-squared error versus D as the primary comparison;
retain the stronger E reference and annual Years 1–3. Report equal-origin metrics,
paired player intervals, all origins separately, non-arrivers, actual-participant
conditional errors, current level/age/previous workload and totals. Preserve
2021 and report 2022 separately; no fitting to observed target-year arrival counts.

Reproduce D before a new fit. Freeze the detailed experiment contract and input
hashes before scoring. Any optional row-weighted alternative is a separately
declared diagnostic, not an after-the-fact replacement if the primary loses.
Predictive success is not guaranteed: common weights improve population coherence
but may trade bias against variance. Do not infer a uniform PA increase is correct.

Deliver: a single result, calibration and attribution report. If uncertain or
worse, keep the current forecast; retain the documented weighting semantics.
Do not immediately optimize a new set of weights.

## Milestone 3 — Return to value integration with identified comparisons

The [eight-cell batting diagnostic](hitter-value-factorial-v1-plan.md) remains
specified but unexecuted. It continues to use its **original archived** E/H
inputs; do not quietly substitute a successful new workload candidate into that
contract. It isolates rate block, workload and marginal/product accounting.
If Milestone 2 justifies a new workload candidate, give its subsequent transfer
comparison a separate named contract rather than enlarging the old grid.

For each position/running/defense/catcher addition, report component MSE change,
other-component cross-error contribution and total MSE change on identical rows.
Separate changed-player and unchanged-player contributions. Cross-errors are
diagnostics, not a new coefficient-fitting objective. Old qualified-only or
future-trained conversion claims cannot certify this stage.

For transferable talent, distinguish neutral hitting/contact targets from raw
future MLB outcomes. Use same-park/mover and level-transition diagnostics before
reopening broad park/opponent variants. Pitcher soft-contact value needs a target
that can measure it; the existing defense-independent label cannot serve as the
sole negative test.

Deliver: a coherent research candidate only if it improves the declared decision
target without hiding measurement or subgroup failures. No "best-looking cell"
promotion. At most one justified next experiment after each result.

## Milestone 4 — Future value, not just next season

Once the mean/measurement interfaces are credible, return to calibrated multi-
year joint production and opportunity paths, including minor leaguers and
late arrivals; separate future entrants from today's assets. Validate service,
contracts/options/costs and tail support before economic value. Calendar sums
are not six years of control. No dollars or FV quota is a calibration target.

## Completion and reporting rules

Each milestone ends in a source/decision record, tests, unchanged-forecast
verification and a repository checkpoint. A completed negative test must say
what narrower hypothesis was rejected and whether its measurement was adequate.
Do not call the program complete until the measurement gates and declared tests
have an evidence-backed resolution; unsupported data can remain an explicitly
bounded blocker, not a fabricated zero or a claim that the baseball skill fails.

Current status: [Milestone 1 source decision](defensive-event-source-repair-v1-result.md)
complete, with 18 new semantic tests. Old catcher capture fails; replacement
sample event accounting passes. Battery timeline and ex-ante fielding
responsibility remain uncertified, so no defensive skill fitting is justified.
The [Milestone 2 weighting contract](hitter-workload-common-weight-v1-plan.md) is
locked and in legacy replay. Production forecasts remain unchanged.
