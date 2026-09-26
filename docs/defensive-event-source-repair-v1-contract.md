# Defensive event source repair v1 — locked source check

2026-09-25. Implements milestone 1 of the methodology repair program. No skill
fit, forecast replacement, or protected 2026 outcome access is authorized here.

## Selection, before reading event outcomes

Use terminal-foundation game metadata only for 2016, 2018, 2021, 2024. These cover
old short-season baseball, the incomplete-history era, reorganization, and a
recent mature season. Within each season / filename level / observed league ID,
choose the first two distinct regular-season games ordered by SHA256 of
`defensive-source-repair-v1:<game_id>`. Preserve missing league ID as its own
stratum. Exclude conflicting game metadata with an explicit count. Save the
selected IDs and input hashes before fetching or opening selected event records.
Do not replace games whose official feeds are missing, incomplete, or non-final.

This is a diagnostic sample conditional on archived PBP coverage, not proof that
all scheduled games are covered. Report exact counts and strata; do not infer
whole-league prevalence from two games per league. If rare events are absent,
their source gate is untested, not passed. An expanded validation sample requires
a new contract before inspecting its results.

## Catcher source checks

Retrieve full official historical feeds for these IDs, cache and hash them. Keep
runner advances and pitch/play events, including multiple runner events within
one PA and inning-ending events. Compare SB/CS with official team batting totals;
compare WP with pitching totals and PB with fielding totals. Missing box fields
are unknown, not zero. Show pickoff-caught-stealing separately and how it enters
official totals. Reconcile within game/side, not just pooled counts.

Compare old terminal-narrative detection on the SAME games/plays with the full
event ledger. Match runner/base/event identities where available; simple count
agreement is not recall. Distinguish narrative-detection limitations from missing
battery IDs and source conflicts. Preserve runner IDs; do not infer them from
names. Do not assign every event in a PA to the terminal pitcher/catcher when
substitutions could intervene. Battery attribution is separately gated.

## Defensive responsibility checks

Retain every ground ball, including FC, errors, hits, and unknown outcomes.
Separate the player who retrieved the ball from who might have had an opportunity.
Inspect coordinate coverage and official-feed agreement by outcome, recognizing
that numerical agreement cannot establish interception-location semantics.

Build a candidate accounting ledger, not a certified range rating: through-GB
hits to LF have candidate 3B/SS responsibility, CF SS/2B, RF 2B/1B (the Total Zone
principle cited in the deep review). An explicit equal-share benchmark is an
assumption, not an estimated probability. Include a fully unassigned alternative
for sensitivity; ambiguous positions/IDs remain unresolved. Direct first-touch
outs are observed conversions, not proof of sole ex-ante responsibility. Do not
train a future-range model on this ledger before outcome-comparable opportunity
assignment is certified. P/1B/unknown events must remain in accounting.

## Decision

The old catcher-source gate fails if systematic missed outcomes are demonstrated.
A replacement can pass EVENT accounting only on exact same-game reconciliation;
that does not certify battery assignment, exposure, or predictive skill. Fielding
conservation alone cannot certify range measurement. Report unresolved gates and
no new model gain if nothing has yet been fairly tested.
