# Refresh the hitter population to the preseason forecast date

2026-10-04. Recover a systematic dated player population through each existing
preseason ranking information date. The [returner audit](hitter-returner-coverage-result.md)
showed that ranking-only refreshes leave some known signings outside eligibility.
This source milestone does not fit, tune or score a new projection. Keep every
original forecast and protect 2026 outcomes and the frozen forecast.

## Scope and date authority

Use the existing ranking release evidence for 2012–2025, covering the 2011–2024
origin feature panel. Retain the special March 18, 2022 date after the lockout;
do not pretend the list or March transactions were known in January. Keep date
granularity explicit; an end-of-day source is not an intraday forecast archive.
Collect official MLB teams and roster responses with explicit season and date.
Only date-bounded transactions from October 1 of the prior year through cutoff
are requested. No 2026 season, player game outcomes, college or private data.

Retain original JSON, exact URLs/parameters, capture time, bytes and hashes.
These are current-provider reconstructions, not contemporaneous archives. A date
parameter alone does not prove that every returned field is historical. Do not
hydrate present-day player primary positions or silently use current team IDs.

## Test the source before collecting the complete panel

Probe 40Man and fullRoster separately. Positive controls: Conforto/Giants at
January 26, 2023; Alfaro/Brewers at January 24, 2025; Ohtani/Angels at January
27, 2018. Inspect Sanó/Angels at January 26, 2024 without asserting presence:
reported agreement and February official transaction are different evidence.
Negative team/date controls: Pollock/Giants January 2023, Canha/Giants January
2024 and Devers/Giants January 2025, before their later in-season acquisitions.
Preserve failures. A fullRoster response is at most a broad candidate list, never
proof of organization ownership, current health, guaranteed playing time or
cutoff-known employment. If temporal controls fail, do not use that endpoint to
admit new origins; restrict collection/use to the source that survives or dated
transaction evidence. Record that restriction before full materialization.

For 40Man collapse duplicate identity-consistent rows, preserve conflicting status
and parent-team diagnostics, and check cross-team conflicts. For transactions
preserve date, effectiveDate and resolutionDate, using their maximum available
date conservatively. Later resolutions remain unavailable even if backdated.
Capture totals and split date windows if the response advertises incomplete
pagination; do not assume every record or reported agreement exists in the API.

## Population materialization and future-label boundary

After source review, union justified cutoff-known candidates with all current
origin identities. Keep current rows and their original forecasts unchanged.
Candidate role/position and ownership are separate questions. Keep two-way and
unknown-role cases visible, including foreign entrants with no own MLB history.
Do not filter new rows using subsequent MLB participation. Preserve free-agent
ambiguity and non-returners rather than treating an absent roster as retirement.

Do not yet substitute blanket recent-MLB membership, infer contract dollars,
backdate reported agreements to official records or add three named exceptions.
Any conversion from source candidates to model eligibility needs explicit dated
authority and a separate integration contract. No fabricated zero predictions
for missing players; no public benchmark gain claimed by changing its population.

## Required checks and review

Reconstruct all accepted source rows, uniqueness, request dates, identity unions,
status conflicts and temporal controls independently. Record unresolved source
fields. Walk Conforto, Sanó, Alfaro, Ohtani and foreign newcomers if recovered,
the negative controls, a retained old hitter, an ordinary candidate and a
non-returner. Use prior-known statistics and outcome-blind peers where available;
no made-up translated talent for missing foreign history. Actual next-year PA may
be attached only after eligibility is fixed, as diagnosis, not selection.

Execution/source review is not predictive or deployment approval. A qualified
historical population can support the next fixed comparison only after fitting
inputs, mature training support and current-anchor replays are specified. Existing
talent/workload misses remain the main modeling task; this collection must not
become an endless rare-returner research branch.
