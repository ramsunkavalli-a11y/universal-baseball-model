# Recovering minor league Statcast for MLB projections

2026-10-04. This is a source recovery and support check, not a new predictive
experiment. Preserve the reviewed MLB-only candidate and all frozen forecasts.
The eventual question remains incremental future MLB hitting and delivered
offense, not prediction of minor league contact shape or same-level performance.

## Existing files cannot supply a complete season

The eleven retained 2023 pitcher-tracking weekly CSVs each contain exactly
25,000 rows. Ten start later than their requested start date; the first also
reaches that row count. They are capped extracts, not certified complete weeks,
and stop in June. Do not fill absent days or contacts with zero, reuse these as
full annual samples, or overwrite them. Preserve a byte-hashed inventory and
compare the overlapping contacts with a new bounded recovery. This finding
does not retroactively invalidate another experiment without checking whether
that experiment actually consumed these files.

## Fixed capture boundary

Recover regular-season 2021–24 Minor League Savant contact responses only.
Use the official minor CSV endpoint, batter detail, inclusive dated boundaries,
and the proven in-play pitch-result expression. Do not filter by measured EV,
angle, level, or result success. First compare the request with and without
the old tracked-game flag on 2022-07-01 and 2023-07-01. Retain both exact raw
responses; choose the broader response only after validating semantics. Also
probe 2021-07-01, 2023-04-07, 2023-06-09 and 2024-07-01 before the season capture.
These dates test the earlier capability findings and truncated week boundaries;
they are not a selection of players who later succeeded.

Start weekly windows within March through October. A response with at least
25,000 rows is suspect, even if its dates appear correct. Retain its compressed
bytes and rejection receipt, split the window into disjoint shorter intervals,
and accept only smaller children. A capped one-day response blocks that day.
At most two concurrent requests, three attempts for transient network failures,
bounded timeouts and a 500 MB free-space stop. Reuse verified new receipts on
resume; never silently overwrite a raw response. Preserve raw response SHA256,
URLs, timestamp, script/contract hashes, date range, schema, counts and exclusions.
No 2025/26 measurements, protected outcomes, expected-outcome metrics, current
bat speed, future game intervals, forecast fits or explorer changes are included.

## Identity and measurement checks

Attach actual league and level by game plus batter from retained certified
player-game summaries, hashing the summaries and their accepted source reports.
Record unresolved identities rather than assigning a guessed league. Audit
regular-season date ranges, unique game/batter/PA/pitch keys, unique terminal PAs,
returned games and player-game contacts against the independent official
AB minus K plus SF plus SH boundary. Distinguish genuine non-contact awards,
bunts, unusual pitch codes, missing measurements and incomplete game capture.
Record exact residuals; a league total cannot conceal player-game mismatches.
Use official historical schedules for game/venue authority before approving a
model-ready source. Suspended/split-venue conflicts require played-park review,
not a current team-to-park lookup.

Canonical launch evidence is a result-producing non-bunt type-X terminal contact,
excluding interference awards. Preserve all other rows in an exclusion ledger;
do not exclude a legitimate contact merely because interference occurs later.
Keep valid EV and angle separately, their joint count, invalid/missing flags,
homers without spray coordinates, batter/pitcher identity and handedness.
Use the reviewed MLB numeric bounds and quantile convention for descriptive
summaries, with distinct league-season provenance. These are raw provider
measurements, not park-neutral or MLB-equivalent talent. The provider's original
publication vintage and per-row imputation status remain unverified.

## Approval and next experiment

Count actual contact and game coverage separately by season, league, month and
venue. Record which source contexts are absent, partial or measured sparsely.
Trace fixed 2023 Caminero, De La Cruz and Langford; 2024 Kurtz and Eldridge;
2024 lower-level Caceres; and covered ordinary/opposite-risk players selected
from origin-known age, level, workload and contact counts. If a fixed player is
untracked, show the exact fallback instead of manufacturing a sample. Include
the old partial-file impact on those players and actual dated production.
Source cases do not demonstrate predictive improvement.

Before any predictive fit, freeze a separate contract with chronological
whole-player-held-out training, own-origin measurements, league-specific
calibration learned inside training, and profile support for tracked prospects
who actually produce future MLB labels. Lower-level coverage alone is not
adequate training support. Preserve all non-arrivals and exact untracked
forecasts. Compare against the reviewed MLB-only branch and retain the existing
positive prospect alternative as a separate benchmark. Do not rerun the older
closed contact-shape challengers or the MLB algorithm contrast.

Stop source approval for unexplained identity, truncation or contact-denominator
failures. A completed capture is not source approval; source approval is not
predictive validation or deployment. Save execution, source review, support and
player walkthrough status separately. Team-record testing stays closed.

Source semantics follow [the earlier minor capability check](current-talent-savant-minors-source-checkpoint.md),
[the Statcast integration plan](hitter-statcast-integration-plan.md) and
[Savant's CSV definitions](https://baseballsavant.mlb.com/csv-docs).
