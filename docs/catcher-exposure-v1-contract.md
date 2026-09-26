# Catcher exposure source gate v1

2026-09-26. Follow the completed repair checkpoint. No new skill model, forecast
replacement, protected 2026 performance, or shrinkage search.

## Question and scope

Can the historical feed supply event-time pitcher/catcher, true pitch counts,
and runners/outs BEFORE each event, including non-attempts? Correct event totals
alone cannot validate blocking or steal-deterrence denominators.

Use the prior 256 selected 2016/2018/2021/2024 games as DEVELOPMENT data. Lock a
new disjoint 128-game sample using metadata-hash ranks 5–6 per original stratum
before fetching outcomes. Freeze code after development, before validation.
Preserve all selected games and failed comparisons; no outcome-based replacement.
Report coverage by year/level, positive events, and excluded pitch/event mass.
These samples are conditional on archived PBP availability, not all scheduled games.

## Separate source quantities

1. Physical-pitch candidate: official `isPitch` event, unique game/PA/event key.
   Reconcile per-pitcher counts to official box pitches. Record pitch IDs/call
   codes and duplicates; automatic/admin actions are not extra thrown pitches.
   A mismatch fails pitch-count certification, not an invitation to drop a pitch.
2. Blocking: keep ALL pitches, with pre-pitch runners, outs and strike count.
   Also retain a pre-outcome risk flag: runner aboard OR two strikes with batter
   eligible to reach on an uncaught third strike (1B empty or two outs). The broad
   all-pitch denominator remains available. Do not select only observed dirt
   pitches or terminal-PAs containing a failure. WP/PB may let a batter reach
   with empty bases; one pitch moving multiple runners is still one failure.
3. Throwing: keep all scored SB, ordinary CS and pickoff-CS separately. Reconcile
   event-time runner/base/battery; preserve safe-on-error CS and double steals.
4. Deterrence exposure: preserve pre-event runner state and runner-pitch rows,
   including an occupied next base (possible coordinated steals). These are
   **pitch exposures**, not a claim that every attempt happens on a pitch. Keep
   between-pitch/nonpitch events explicitly. Do not divide all attempts by a
   pitcher-selected subset of pitches or admin-action count and call it deterrence.
   A later model must declare a runner-PA/risk-spell or event-time estimand that
   covers both attempts and nonattempts without conditioning on eventual PA length.

## Source reconstruction

Process half innings and actions chronologically. Begin each half empty; an
explicit automatic-runner placement changes the state before subsequent pitches.
Apply all same-event runner moves together, not one at a time so forced advances
collide. Handle pinch runners by explicit replacement IDs/base. Never use a later
outcome to fill a pre-event runner. Check movement starts against carried state;
reconcile post-PA occupancy to official postOn* and outs to official play counts.
Reset on half transitions; interrupted PAs and inning-ending steals remain.

Build a separately versioned C/P-only timeline from the existing starting-lineup
and action rules. Unknown LF must not silently certify LF, but does not by itself
erase known C/P. Require distinct, known C/P at the event. Validate C/P scoring
credits, final pitcher matchup and player event totals. The previous full-nine
validation result remains unchanged; this is a new coverage contract.

Link WP/PB and steals to a physical pitch only with an exact event or unique
`actionPlayId`/`playId` match within the PA. No nearest/previous-pitch fallback.
Unlinked events stay in the ledger. Compare pitcher/catcher at the action and
linked pitch; don't silently credit a later substitute. Multi-action movements
must be reflected before the next pitch; don't apply an action twice.

## Gates and conclusions

Require exact comparable player pitch counts, event totals, runner continuity,
post-PA states and source identities for a certified game slice. Keep failures
and their event/pitch denominators visible. Unknowns are neither zeros nor
successes. Sources are related representations of official scoring, not human
rescoring. A bounded source failure can end this run without fitting.

After validation, state separately whether (a) pitch exposure, (b) scored-event
linkage, (c) runner risk state, and (d) a specified statistical opportunity
denominator are ready. Passing a/b/c is not proof of catcher talent or causal
credit. The next model contract must separate pitcher/runner/catcher effects,
level/era and park, avoid outcome-conditioned features, and test later-season
prediction rather than in-sample catcher rankings. No new model is fitted here.

## Primary-source motivation

MLB's [WP definition](https://www.mlb.com/glossary/standard-stats/wild-pitch)
and [PB definition](https://www.mlb.com/glossary/standard-stats/passed-ball)
include uncaught-third-strike advances. Their scoring definitions are not a
physical count of every ball a catcher failed to stop.
Baseball Prospectus's [2015 catching overview](https://www.baseballprospectus.com/news/article/28193/prospectus-feature-catching-up/)
separates attempt frequency, success conditional on an attempt, and blocking.
Its indexed primary description also reports useful PBP-only blocking/throwing
work; absence of tracking alone is not grounds to abandon these skills.
The [blocking-method article](https://www.baseballprospectus.com/news/article/27849/prospectus-feature-passed-balls-and-wild-pitches-getting-it-right/)
emphasizes pitcher context. Direct BP pages returned 403; these limited claims
come from primary search-indexed descriptions, not a claimed full-text reading.
