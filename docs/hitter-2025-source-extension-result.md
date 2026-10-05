# Verified sources for the new hitter forecast

2026-10-05. Three missing source families are now ready for the selected
candidate's input assembly: 2025 MLB contact measurements, December 31 rosters,
and an actual preseason 2026 Top 100 archive. This is a source milestone, not
an accuracy improvement or a completed forecast. The original protected package
still verifies across all 31 files and 3,907 players. No 2026 outcomes were opened.

## Tracking source and definition checks

The bounded 2025 capture has 124,899 raw rows. The unchanged measurement definition
retains 123,697 non-bunt contacts for 666 players, including 123,265 complete speed
and angle pairs. All retained contacts have a verified completed-game venue,
pitcher and handedness context. There are no invalid speed/angle values and no
conflicting completed venues requiring split-game assignment in this capture.
Missing measurements stay missing. Provider estimates and retrospective revisions
remain a qualification; this is not proven camera-only or original-vintage data.

All four hit counts match the official saved totals for all 765 players. The two
contact-denominator differences are fully explained in the
[denominator amendment](hitter-2025-contact-denominator-amendment.md):
Campbell's interference AB without a physical contact, and Canzone's actual
measured grounder awarded first without an AB. Corrected contact equality holds
separately for every player. No contact measurement was fabricated or discarded
merely to force the raw AB formula to match.

The separate cutoff-explicit adapter matches the old projection on the entire
preserved 2022 raw source and 4,746,150 tracking fields across all 63,282 historical
rows. Independently selecting contacts in Python and calculating summaries in
NumPy reproduces 10,656 annual fields across every 2025 tracked player. The 2025
availability flag is now one; a missing player measurement still has explicit
unknown metrics and zero measured sample, not a fake observed speed of zero.

## Player evidence

The six cases were fixed before retrieval. Their 2025 source measurements flow
into the same lagged normalization and sample definitions as the historical
model, without a new forecast or future result. Each has three comparison players
chosen by closest contact exposure, with ID as tie-breaker rather than later
success. Both residual cases and zero/single-measurement stress cases are added.

| Player | Raw contact rows | Retained non-bunts | Complete pairs | Mean speed mph | Source review finding |
| --- | ---: | ---: | ---: | ---: | --- |
| Aaron Judge | 388 | 388 | 387 | 95.42 | One missing pair stays missing; 2025 joins the prior two seasons |
| Nick Kurtz | 272 | 272 | 271 | 92.66 | Actual debut-season tracking is available, not silently omitted |
| Yordan Alvarez | 138 | 138 | 138 | 94.66 | Shorter 2025 exposure enters with its own sample-size inputs |
| Jung Hoo Lee | 493 | 490 | 489 | 87.08 | Three bunts are excluded; contact exposure is otherwise preserved |
| Junior Caminero | 484 | 484 | 483 | 92.44 | One missing velocity remains unknown |
| Rhys Hoskins | 194 | 194 | 194 | 90.23 | His complete 2025 contact sample enters despite shorter playing time |

Campbell and Canzone illustrate why official AB and measured physical contact
are different denominators. César Prieto has one retained contact but no speed
or angle; his source metrics remain unknown. Terrin Vavra has just one complete
contact; its 100.6 mph value is observed, but does not establish stable talent.
These are source reasonability checks, not examples of correct 2026 predictions.

## Dated rosters

Thirty official year-end endpoints provide 1,175 unique members, with plausible
team sizes and no duplicated player membership. Eight before/after checks for
Devers and Naylor match independently captured 2025 trades. Devers is on Boston
before June 15 and San Francisco at year-end; Naylor is on Arizona before July 24
and Seattle at year-end. These demonstrate date sensitivity for two unrelated
transitions; they do not certify every roster transaction in MLB.

Use this source only for the existing 40-man membership feature. Status codes
are not health, and membership does not guarantee playing time or establish
every minor leaguer's contractual rights. No prior-season roster was overwritten.

## Preseason rankings

Archive metadata located exact January 26 and February 1, 2026 captures of the
publisher's Top 100. Complete player IDs and ranks are identical. The initial
decoded HTML hashes differed from the archive index because the archived payload
was gzip-encoded. A separate transport check preserved those bytes, matched both
archive index digests exactly, verified both Memento timestamps, and reproduced
the saved decoded body hashes. No live ranking body, external script or updated
player biography was requested as an input.

The list is verified available by January 26, not necessarily first released
that day. This is a late-January preseason forecast with other performance
statistics through 2025, not a December-only forecast. Fourteen identity-to-input
walks verify complete-list absence versus listed rank, 2025/2024 lags and rank
normalization. Griffin, McGonigle, Made and De Vries are represented by actual
preseason ranks. A ranked pitcher such as McLean is not automatically a hitter;
dated-role reconciliation still belongs in population assembly.

## Disposition and next work

Seventeen focused tracking, ranking, pooled-input and historical measurement
tests pass. Source integrity, historical equivalence and source-player reviews
are complete for this milestone. No accuracy, workload, full WAR or trade-value
improvement is claimed. All three source families are qualified for input
assembly, not automatic candidate deployment.

Follow the [candidate preparation plan](hitter-candidate-freeze-preparation.md):
construct origin-known 2025 population and matching features, audit actual
training support, fit the unchanged selected route and independently replay its
intermediates. Freeze a new immutable package and build a separate team-filtered
explorer. Only then perform the user's authorized one-time 2026 evaluation.
Other input families, eligibility and the model replay still need their own checks.

Compact receipts and complete source cases are in
`reports/model-evidence/hitter-2025-source-extension/report.json`. Preserved raw
captures and detailed reviews remain under `reports/generated`; the public
report records their hashes without publishing raw downloaded payloads.
