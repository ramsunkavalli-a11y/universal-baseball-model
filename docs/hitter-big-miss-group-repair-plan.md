# Repair the major hitter forecast miss patterns

2026-10-05. Current goal checkpoint: in progress.

Goal: identify which large historical hitter misses come from missing known
facts, model logic, or an unsuitable test; repair supported defects and measure
the effect on actual next-year MLB playing time and delivered batting value.
Keep the stronger forecast unless a replacement earns its place. A more accurate
injury table or a smaller error on one player is not sufficient.

## Fixed audit before another model fit

Use the 30,519 saved historical forecasts in the completed nonmedical-opportunity
comparison, including the thirteen added diagnostic rows. Retain all identities,
cutoffs and outcomes, origins 2016–2018 and 2021–2024, and targets through 2025.
The current working anchor is `observation`; retain `repaired_domestic` as the
earlier selected architecture reference. Do not pretend these are independent
tests or use the failed medical subset refit as the project benchmark.

Rank the top fifty absolute PA errors and top fifty absolute delivered-value
errors, with row ID as the tie-breaker. Review both directions. Also score the
entire population by origin-known career stage, recent MLB exposure, age,
employment and captured medical/nonmedical state. Group definitions must not
depend on whether someone eventually succeeds. These diagnostic selections
generate repair hypotheses, not independent validation of them.

Separate signed value error into the effect of PA error at the forecast rate
and the remaining rate error at actual PA. This is accounting, not an oracle
forecast, a causal decomposition or additive shares of squared error. Show
whole-cohort scores and totals alongside the dramatic players. In particular,
many minor-league zero outcomes must not hide poor established-player accuracy.

Check apparent logic failures against the actual source joins and calculations:
known retirement versus mere release; finite suspension versus permanent exit;
observed medical return versus roster activation; recent small MLB samples
versus past established roles; unusually strong talent versus restricted training
support; prospects versus actual former MLB players classified as low minors.
Read cutoff-known primary reports when a baseball fact is uncertain.

## Repairs and comparison discipline

First reconcile retirement evidence, including the newly identified Martínez
miss and similarly classified players. Reuse the existing reversible retirement
state instead of building a competing one. Only dated affirmative evidence can
change eligibility; release, silence or next-year zero PA cannot. A later
documented return cancels an earlier retirement state. Preserve old ledgers and
forecasts and record where the added evidence came from.

Before any new fitted model, write its own fixed comparison contract using what
the group audit establishes. Preserve the stronger full-history training
backbone and explicit unknown medical coverage; do not repeat the rejected
source-covered standalone medical refit, change support thresholds until it
wins, or launch an algorithm contest. A deterministic source/status correction
can be compared without refitting; labels, population and hitting rate stay fixed.

For each repair, retain old forecasts and give corrected probability,
conditional PA, PA and delivered value. Score matched full cohorts, relevant
groups, public-projection rows when available, each origin and totals. State
development-data exposure honestly. Never delete difficult cases to improve a
score. Follow with actual prior-stat/input/forecast walks covering gains, harms,
false highs/lows, ordinary cases and outcome-blind peers. Unknown source support
or contradictory evidence prevents a factual hard-zero decision.

## Completion checkpoint

Finish when the major miss groups and test-design findings are recorded, at
least the highest-priority supported defect is implemented and replayed, player
walks are complete, and the repo records what changed, what did not work and
one justified next milestone. Do not claim the entire hitter/value project is
finished. No further 2026 outcome access, frozen forecast edit or explorer
promotion is authorized by this checkpoint. Preserve unrelated local changes
and commit/push exact milestone files.
