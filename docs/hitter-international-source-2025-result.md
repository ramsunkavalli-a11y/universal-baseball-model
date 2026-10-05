# Japan and Korea batting coverage through 2025

2026-10-05. The official first-team batting collections now extend through 2025.
This repairs a missing season of evidence, not the model's foreign-player
forecasts. Neither frozen 2026 forecast nor its completed final evaluation changes.
The [eight player reviews](hitter-international-source-2025-player-review.md)
are complete. No new model was fitted and no predictive improvement is claimed.

## What was recovered

| Source | Clubs | Source rows | PA | Zero PA rows |
| --- | ---: | ---: | ---: | ---: |
| NPB 2025 first team | 12 | 725 player club rows | 64178 | 240 |
| KBO 2025 first team | 10 | 398 player season rows | 55996 | 99 |

These are not 1,123 distinct eligible hitters. The tables include pitcher batting,
zero-PA appearances and identities without an MLB link. All remain in the source.
Every normalized count was reconstructed from archived table cells: 20,541
fields. Sixteen summable KBO fields reconcile to the ten official team totals;
player games are not summed as club games. Selected English renderings agree
on 115 shared count fields. They are another view of the same provider, not
independent-provider confirmation. The source dates and raw bytes are retained.

| Player | 2025 PA | HR | K | Recorded games |
| --- | ---: | ---: | ---: | ---: |
| Munetaka Murakami | 224 | 22 | 64 | 56 |
| Kazuma Okamoto | 293 | 15 | 33 | 69 |
| Tyler Austin | 246 | 11 | 45 | 65 |
| Sung Mun Song | 646 | 26 | 96 | 144 |
| Patrick Wisdom | 486 | 35 | 142 | 119 |

The collection was league-wide, not selected from successful MLB entrants.
These five known coverage cases and three mechanically selected controls show
what the new season adds. Their raw overseas rates are not MLB talent estimates.

## Two execution problems were repaired without changing the cases

NPB's 2025 tables use a different row layout and embed batting handedness in the
name cell. The old parser stopped rather than returning plausible wrong counts.
A separate year-specific parser checks headers, count arithmetic, handedness and
first-team scope. The old 2005–2024 parser and source package remain sealed.
See the [layout amendment](hitter-npb-2025-layout-amendment.md).

The ordinary Korean control, Cheon Seong Ho, has two 2025 English rows after a
trade. The first review stopped because it expected one annual row. The corrected
review sums the two stints' counts, validates explicit total rows when present
and never averages or sums rates. The original selection and failed receipt are
preserved. See the [trade review amendment](hitter-kbo-2025-traded-player-review-amendment.md).
Neither correction constitutes a change to forecast weights.

The completion test run initially passed 58 cases but could not initialize two
temporary-file tests in the shared Windows temp folder. A new empty, validated
workspace scratch directory resolves that execution limitation. It is not a
source/count failure, and the interrupted run is not claimed as a full pass.

## Remaining source limits

One NPB player identity, Seibu's displayed Davis with 131 PA, has no qualified
NPB key from the available listing. It remains unresolved. There are 421 NPB
rows without MLBAM keys, including 273 positive-PA rows. Korea has 329 rows
without MLBAM keys; 94 have at least 100 PA. Missing MLB keys are not missing
batting records and do not imply poor talent. Twenty-nine new Korean static
profiles were collected; some names cannot be matched and 189 low-priority
profiles remain uncollected. No fuzzy identity guesses were made.

NPB's PA accounting has no residual. KBO retains one unexplained PA for source
54795. It is not turned into an invented out. KBO's bulk counts do not include
steals or caught stealing. English traded-player rows lack PA, so a displayed
last club or AB cannot silently supply full-season park exposure.

Counts and today's static names/DOB do not establish historical position,
injury, MLB employment, contract status or park exposure. Low games do not
prove injury. Zero PA does not prove inactivity. Historical publication vintage
is not independently certified. This extension covers 2025, not 2026 overseas
results or every international league; a 2027 forecast would need newer data.

## What this permits next

Retain these qualified batting counts for a later foreign-entry/returner route.
Do not repeat the failed complete pooled representation merely because another
season is available. Earlier component translation improved event prediction
in a small selected mover sample, but the full-model integration did not improve
delivered batting value. That remains the predictive evidence, not a rejection
of all overseas information. See
[the completed integration comparison](hitter-evidence-representation-result.md).

The next integration must keep the useful domestic routes unchanged, separate
dated MLB employment from foreign talent evidence and compare on historical
entrants, returners and non-arrivals. It must not backfill or tune predictions
on the now-exposed 2026 results. Source coverage passes with the qualifications
above; universal identity coverage, predictive gain and deployment do not.

The bounded receipt is
`reports/model-evidence/international-hitter-source-2025/report.json`.
Bulk provider tables and raw responses remain private. Earlier pending review
receipts are preserved and superseded by a separate completion receipt.
