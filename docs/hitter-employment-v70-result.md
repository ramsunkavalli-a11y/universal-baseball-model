# Unsigned hitters need context, not a blanket playing-time boost

2026-10-03. This is a source/diagnostic checkpoint, not a new fitted model.
All 63,282 inputs and 30,506 forecasts retain their original fields and values.
Nine source-to-saved-model player reviews and eighteen existing-head replays
are complete. No protected 2026 or deployed changes.

## What the source audit repaired

The first adapter incorrectly delayed some employment announcements until a
later effectiveDate. Bour's December 2018 signing carried a May 2019 date;
Aoki's December 2015 signing carried a June 2016 date. Official announcements
confirm December knowledge; see the [date repair](hitter-employment-v70-date-repair.md).
Plain MLB activations also resolve recorded free agency in some cases.

The source-only repair changes 242 state labels, preserves unknown older
free-agency histories instead of carrying them indefinitely, and reduces
eight roster/state conflicts to two. Keep those two flagged. Records before
2015 and exact historical publication vintages are not certified. This rule
is specific to explicit employment announcements; older medical models are
not silently rewritten. Initial source outputs remain preserved.

## Why a blanket boost would fail

| Existing forecast group | Forecasts | Expected MLB appearances | Actual appearances | Expected PA | Actual PA |
| --- | ---: | ---: | ---: | ---: | ---: |
| Documented unsigned current hitters off roster | 458 | 280.6 | 313 | 82,189 | 83,028 |
| Other current hitters off roster | 953 | 358.0 | 327 | 46,093 | 36,468 |
| Current hitters on roster | 3,130 | 2,909.2 | 2,956 | 1,001,415 | 1,037,360 |

Unsigned hitters have too little appearance probability, but their expected
total PA is approximately right. Probability and conditional-workload errors
offset: raising only the probability could overallocate PA. Other unlisted
players are already overallocated; listed hitters have a much larger aggregate
shortfall. These are diagnostic observed groups, not causal comparisons or
proof that a free-agent feature improves a forecast.

Bader gets 140 PA versus 437; roster absence hurts both heads, and his near-exact
offense prediction hides component errors. Wieters gets 267 versus 465, Harper
539 versus 682, Martinez 512 versus 649. But Bradley gets 130 versus 113—a
reasonable workload—while older Zimmerman and Donaldson get modest comeback
expectations before playing none. Most importantly, Belt gets 113 before 404
PA, then 244 before zero the following year. The same player illustrates both
the opportunity miss and the danger of assuming a return.

Every case includes unsuccessful origin-selected peers. Actual earlier exposed
active people range from 25 for the earliest Wieters fold, all in one captured
year, to 197 for Bader's. Those counts are not matched elite-star or injury-return
support. Source review completion is not statistical validation.

## Next coherent comparison

Test one employment-evidence representation in both opportunity heads, with
capture coverage, unknown/conflict states and unchanged independent roster
listing. Preserve the two forecast anchors and successful/failed cases; keep
hitting fixed. Judge probability, mean PA and offense together, not a probability
win multiplied by unchanged conditional workload. No automatic jobs, overrides,
penalty tuning or new college collection.

Also keep the information-cutoff limitation explicit: current ranks are
preseason, while employment/health evidence remains December. The qualified
public comparison does not yet have equal known-job information. Do not waive
the practical benchmark or claim it is fully controlled. After the bounded
contrast, select a coherent practical candidate and finish the comparative
handoff rather than extending a rare-feature queue. Goal active.

Evidence, raw employment dates, actual inputs and saved paths are in
`reports/model-evidence/hitter-employment-v70/`. The source repair has not yet
changed any player projection.
