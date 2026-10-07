# Populate recent assignments for the full historical role comparison

2026-10-07. The reviewed examples exposed real assignment mistakes, but a model
cannot be repaired using only those names. Extend the certified dated fielding
source to every current-season player and sport represented in the existing
2021–2024 role-feature population. Preserve all forecast identities, including
those with no current annual source. This supplies shared inputs for one role
repair; it does not estimate defensive talent or improve accuracy by itself.

## Source population and cutoff

Take the 16,674 existing origin-year feature rows for 2021–2024, with player IDs
and origins fixed by `defense-jobs-v14/features.parquet`. Training uses mature
same-DH-policy labels and the old reference keeps its saved inputs. Evaluation
remains the same 12,432 origins for 2022–2024. Current role inputs stop at the
origin year; future position outcomes are not used to choose requests or define
the population. No 2026 query, result-based exclusion or explorer update.

Use the existing reviewed annual position source to enumerate the declared
player-season-sport scopes. Rookie complex and DSL share sport 16, so request
each player/sport once and retain its returned league distinctions. Scope counts
come from the actual source manifest rather than a guessed number. Current
source absences are unknown, not observed pure DH or zero talent. Keep original
annual rows and their usage/team/level qualifications.

## Bounded batch probe before expansion

Probe the official multiple-person hydration route on Ohtani/Buxton in MLB 2024
and Eldridge/Isaac in AA 2024. Each request declares one singular sportId and
the historical regular-season calendar. Compare every player, position, league,
inning total, start and appearance with the already verified single-person game
logs. Unexpected players, dates, sport scope, truncation or incomplete groups
fail. Preserve failures. Do not silently use a failed batch or the previously
rejected plural-sport and date-range routes.

After a successful probe, freeze a manifest using sorted groups of at most 32
player IDs for each origin/sport. Capture exact bytes and metadata. Reuse saved
captures only when request identity and hashes match. Allow up to three requests
in flight. Retain the process handle and receipts; a timeout is not a completed
or failed capture. Retrying resumes the same manifest without overwriting data.

## Certification and feature construction

Parse explicit sport and origin, regular-season dates, exact position-game grain,
baseball innings, starts and appearances. Compare the entire position inventory
with the old annual scope. Mark any mismatch unknown; do not delete the forecast
or fill the mismatch with zero. Preserve the source response and all comparison
details for diagnosis before using it. Propagate already certified simultaneous
P/DH starts by game date exactly once; pitching outs never become hitter fielding
outs and DH never gets invented innings.

Keep full-year assignment, before-August and August-onward use separate, with
their own exposures and dates. These two periods are source descriptors, not
chosen recency weights. Retain all current minor levels and the full older
repertoire from the existing annual source; a six-game AAA assignment cannot
erase a large AA record. No automatic current-team, biography, transaction or
newspaper feature is taken from hydrated person metadata.

An independent verifier must reconstruct requests, population, source totals,
dated corrections, period features and unknowns. The nineteen existing focal
and 57 peer records remain mandatory traces, including failures/non-arrivals,
plus existing contributor and prior-year contrasts. Do not close the source
milestone without those checks. Agreement within one official provider certifies
construction, not independent truth of every box score.

## Subsequent role test

Once population readiness is established, declare one coherent current-assignment
and full-repertoire comparison with fold-specific support and fallbacks before
fitting. Keep batting, defensive-quality recipes, predicted PA, physical caps
and missing-player reserves fixed. Position use, positional value, defense
delivery and expanded value must be checked separately and walked through
players before disposition. There is no algorithm/recency/prior-strength sweep,
no automatic promotion and no claim that assignment predicts lower-minor talent.
The broader defense and player-value goal remains active.
