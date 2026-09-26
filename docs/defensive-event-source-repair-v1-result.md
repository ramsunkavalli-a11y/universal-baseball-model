# Defensive source repair: catcher failures were not fair skill tests

2026-09-25. [Locked source contract](defensive-event-source-repair-v1-contract.md).
Milestone 1 has an evidence-backed source decision, not a new defensive forecast.

## What changed

We built an event-level replacement that retains runner events occurring before
the batter's final result. The old terminal-PA narrative loses, for example,
a successful steal followed by a groundout. This is outcome-dependent missing
data: successful steals generally allow the PA to continue, whereas an
inning-ending caught stealing becomes its final result.

The sample was selected from metadata before reading outcomes: 128 games across
64 season/filename-level/league strata in 2016, 2018, 2021, 2024, including
short-season and rookie leagues. All 128 official feeds were available and final.
The sample is conditional on archived PBP coverage, not all scheduled games.

| Event | Full event ledger | Maximum matched by old PA-narrative detection |
|---|---:|---:|
| Successful stolen bases | 268 | 18 (6.7%) |
| Caught stealing, excluding pickoffs | 90 | 30 (33.3%) |
| Passed balls | 28 | 3 (10.7%) |
| Wild pitches | 230 | 21 (9.1%) |

Another 16 pickoff-caught-stealing events are retained separately. They count
toward official CS totals, but were deliberately excluded by the old clean
throwing method. The ordinary-attempt caught share is 90/(268+90)=25.1% in this
sample, compared with 30/(18+30)=62.5% in maximum old narrative matches.
Neither percentage should be advertised as the population league rate.

The old column is a generous **upper bound**, matched by game/PA/family/base,
not identity-verified recall: the old ledger lacks runner IDs and further
blocking eligibility rules can remove additional events. We do not call it an
exact rerun of all old blocking restrictions. Twelve terminal keys conflict;
the comparison does not arbitrarily select their source version.

## Why the replacement counts are credible

All **1,024 game/side/stat checks match exactly**: SB/CS against official team
batting counts, WP against pitching counts, PB against fielding counts. This
includes zeros; event totals above show that the match is not only on negatives.
Multiple runners moving on one WP/PB count as one event, while double steals
retain separate credited runners. Another runner advancing during a CS does
not become a second caught stealing. Safe-on-error CS credits are not discarded
merely because the runner was safe. Unit tests preserve these distinctions.

These are different representations within the official scoring system, not
independent human re-scoring. Event accounting passes on this sample; it does not
prove every historical game, pitch exposure, or catcher attribution is correct.
The replacement deliberately leaves event-time pitcher/catcher IDs unresolved
rather than copy the terminal battery across possible substitutions. Reconstruct
and validate that timeline before fitting catcher skill or all-level battery
effects. The selected games are development evidence after this audit; further
validation should use a separately preselected sample.

## Infield range: accounting repaired, skill measurement still not certified

The candidate ledger preserves all 2,875 archived sample ground balls, including
FC, errors and unknowns. Responsibility shares sum to one for every ball. It
redirects 465 through-ground-ball hits/errors recovered by outfielders toward
adjacent infield candidate positions. Equal shares are an explicit benchmark
assumption, not learned truth. Eight balls remain wholly unresolved, including
five source conflicts; pitcher and first-base touches are retained.

This fixes missing-event accounting, but does **not** yet create a fair range
rating. A successful infielder's first touch does not tell us every fielder's
pre-play chance, and a retrieved hit does not reveal its exact interception
point. The all-unassigned sensitivity is preserved. No range learner was fitted.

For 6,255 batted-ball records with coordinates in both sources, all match the
official hit-data coordinates within 0.011 units. This certifies copying, not
that coordinates mean comparable interception locations on hits and outs.
The remaining opportunity-semantics problem is explicitly open, not patched
with confident but arbitrary fielding credit.

## Decision and next steps

- Reopen catcher throwing/deterrence/blocking after source repair. Prior negative
  results cannot reject those skills: the opportunity/event sample was biased.
- Retain the full-event extraction and source checks. Certify battery timeline
  and runner/pitch exposure before a catcher-model refit; do not add catcher WAR.
- Keep the infield candidate as an accounting diagnostic. Do not promote its
  equal-share assumptions into player range ratings without a defensible test.
- Proceed to the independent fixed workload-weight comparison while these
  specifically bounded attribution gates remain unresolved.

18 new semantic tests pass. Reproducible selections, capture hashes, detailed
event/coordinate/responsibility ledgers and reconciliation report are in
`model_artifacts/defensive-event-source-repair-v1-2026-09-25/`. Full historical
feed caches are local ignored quarantine data; the script can retrieve them.
No model was fitted and no frozen player projection changed in this milestone.
