# Current Source Certification State

Last updated: 2026-08-15

This is the current checkpoint for the foundation-layer source work. Detailed experiments remain in the audit scripts, workflow artifacts, and ADRs; this document records the decisions that should govern the next implementation work.

## Governing source strategy

> **Canonical authority: MLB Stats API. Canonical working data: our normalized tables, built wherever practical from mature public parsers/datasets and continuously certified against official representations.**

Raw authority does not mean rebuilding mature extraction work. Reuse existing cleaned history and parser logic where it survives certification; write custom ingestion only for a demonstrated gap.

## Accepted source roles

| Need | Preferred source / method | Status |
|---|---|---|
| Historical affiliated MiLB pitch + Gameday batted-ball bootstrap | `armstjc/milb-data-repository` | Accepted with versioned normalization, provenance, and conflict handling |
| Official PA/result/matchup authority | MLB Stats API | Accepted |
| Official HTTP/retry utility | low-level `python-mlb-statsapi` transport | Accepted; exact successful response bytes are captured separately |
| PA / non-PA semantics | versioned MLB Stats API `/eventTypes` snapshot | Accepted |
| Cross-system player IDs | pinned Chadwick Register | Accepted versioned crosswalk |
| Universal spray direction | Gameday `hc_x/hc_y` + established Petti/pybaseball transform | Accepted |
| Richer Minor Statcast | Baseball Savant, likely through SportsDataverse/helper logic | Later optional enrichment |
| Historical MLB validation | Retrosheet + Chadwick | Planned separately from MiLB bootstrap |

## Foundation gates passed

The following are no longer open architecture questions:

1. affiliated MiLB physical-pitch history is reusable across AAA, AA, High-A, Single-A, ACL, FCL, and DSL;
2. the reusable history remains structurally useful in tested 2005 and 2015 AAA samples;
3. official PA/non-PA semantics reconcile to official batting totals in the tested reconciliation set;
4. upstream releases are overlapping mutable snapshots, not trustworthy calendar partitions;
5. exact duplicates and payload variants are preserved/compacted deterministically rather than silently dropped;
6. the lossless parent grain is `play_sequence`, not plate appearance;
7. MLBAM is the primary modern event identity and Chadwick is a versioned crosswalk;
8. Gameday `hc_x/hc_y` provides a near-universal Pull/Center/Opposite direction signal;
9. source-only cross-snapshot resolution is field consensus, not inferred chronology;
10. structured official evidence can adjudicate specific source conflicts without selecting a whole source snapshot as the winner;
11. canonical provenance, typed schemas, quality issues, Parquet persistence, DuckDB querying, and event-cutoff/vintage semantics have working tests and live POCs;
12. the multi-asset historical database POC passed;
13. the minimum universal Performance-event mapper is validated from 2005 AAA through recent DSL/complex ball, before foul-air screening.

## Reusable MiLB source: certified caveats

### Physical pitch sequence is strong

Representative recent samples across all current affiliated levels match official pitch-bearing sequence structure and physical-pitch counts very closely. Older 2005/2015 AAA samples also passed the structural gates. This is why the reusable source remains the historical bootstrap rather than being replaced with a custom all-history Stats API parser.

### Release files are snapshots, not month partitions

Observed defects include exact 2x row duplication in some assets, cross-month game overlap, and revised values for the same natural pitch key. GitHub asset creation/re-upload timestamps also do not reliably order baseball truth.

The reusable-source natural pitch key is:

`game_pk + at_bat_number + pitch_number`

Raw observations retain asset/checksum/retrieval provenance. Canonical partitioning uses actual event date.

### The upstream `events` PA outcome is not reusable

The parser reads the PA result but later exports a pitch-event variable into `events`. PA/result semantics therefore come from the narrow official play-sequence layer.

### Upstream batter ID can be mutated by pinch-runners

The parser changes `batter_id` for every `offensive_substitution`, including pinch-runners. Targeted live comparison found three batter mismatches and all three had this cause. Canonical sequence participants therefore come from the official structured matchup. Raw source participant IDs remain provenance/debug evidence.

### The exported `type` field is MLB `details.code`, not merely B/S/X

This was a material adapter bug discovered by the first Performance audit. In six recent AAA/Rookie games, 283 BIP-expected PAs all had reusable-source batted-ball evidence, but their contact rows used:

- `X`: 150;
- `D`: 77;
- `E`: 56.

An X-only interpretation falsely labeled all 133 D/E contacts as missing. Historical release checks confirmed the same vocabulary:

- 2005 September AAA batted-ball rows: D=1,478, E=731, X=3,696, zero unexpected codes;
- 2015 September AAA: D=1,991, E=984, X=5,221, zero unexpected codes.

The canonical adapter therefore reconstructs positive in-play evidence from `{D,E,X}` or any preserved hitData-derived field. See ADR 010.

## Canonical event grain and official semantics

Two opposite edge cases are real:

1. a true PA can contain zero physical pitches, such as a signaled intentional walk;
2. a physical pitch can occur in a sequence that never becomes a PA, such as an inning-ending caught stealing after a pitch.

Therefore:

`game -> play_sequence -> 0..N pitches`

and:

`plate_appearance = play_sequence where official is_plate_appearance = true`

Stats API `allPlays` also contains runner/game actions. A frozen dated `/eventTypes` snapshot determines PA semantics; unknown result codes fail certification until reviewed.

The reconciliation suite matched **22/22 team batting lines across 11 representative MLB/MiLB games on all 13 audited totals**: PA, AB, H, 2B, 3B, HR, BB, IBB, HBP, K, SH, SF, and CI.

## Batted-ball evidence and universal direction

The accepted direction transform is:

- Gameday `hc_x/hc_y` coordinates;
- established Bill Petti / pybaseball spray-angle transform including the `0.75` calibration factor;
- Pull/Center/Opposite relative to batter handedness;
- no production `hit_location` fallback;
- no approximate foul-line geometry as a fair/foul classifier.

Coordinate coverage is approximately 99% in tested 2005/2015 AAA trajectory-bearing balls and essentially complete in tested recent levels including Rookie/DSL.

Accepted trajectory families are:

- `popup -> IFFB`;
- `fly_ball -> OFFB`;
- `line_drive -> LD`;
- `ground_ball -> GB`;
- `bunt_* -> BUNT` special family.

Foul airborne outs remain real Performance events but are not to be forced into the FaBIO 12-bin skill view. The exact foul-air eligibility rule remains a small open definition gate.

## Minimum universal Performance-event mapper

The descriptive mapper preserves exactly one row per official true PA. Official sequence data supply PA existence/result/participants; resolved reusable pitch evidence supplies physical contact, trajectory, and direction.

Core candidate bins before foul-air screening are:

- BB/HBP;
- K;
- IFFB;
- Pull / Center / Opposite OFFB;
- Pull / Center / Opposite LD;
- Pull / Center / Opposite GB.

Bunts and special non-BIP outcomes remain explicit outside the core rather than being coerced into a bin.

After correcting D/E/X semantics, the live audit produced:

- 2025 AAA: 209/211 PAs (99.05%) core eligible before foul-air screening; the two exclusions were bunts; zero structural mapping failures;
- 2024 ACL/DSL/FCL: 228/228 PAs (100%) core eligible; zero structural failures;
- 2005 AAA: 159/161 PAs (98.76%) core eligible; two bunts excluded; zero structural failures;
- 2015 AAA: 146/146 PAs (100%) core eligible; zero structural failures.

This validates **event mapping**, not a run-value model. No player score, shrinkage, or projection belongs here yet.

## Cross-snapshot resolution

The source-only policy remains `non_null_field_consensus_v1`:

- all non-null observations agree -> resolve;
- null plus one observed non-null value -> resolve the observed value;
- multiple distinct non-null values -> leave the canonical field null and flag a quality issue;
- never use retrieval time, asset creation time, filename period, or row order as a tiebreaker.

In the 2023 July/August Rookie overlap test, 5,524 pitch keys resolved with only 16 pitches (0.29%) retaining any canonical conflict. These collapsed to seven unique sequence/field hand disputes, and current structured official matchup data matched exactly one source value in all seven cases.

## Identity

MLBAM is the canonical modern event identity. Chadwick is a pinned/versioned enrichment layer. The first pinned snapshot contained 518,743 public people rows, 129,658 MLBAM-linked identities, and zero duplicate MLBAM IDs. Representative AAA/DSL/FCL official IDs matched Chadwick 83/83. Missing links remain `crosswalk_pending`; automatic fuzzy-name matching is not allowed.

## Provenance, storage, and temporal semantics

The canonical contract separates immutable `source_snapshot` identity from versioned `normalization_definition` identity. Parser changes therefore do not pretend the upstream evidence changed.

Exact official response bytes are captured while still reusing `python-mlb-statsapi`'s public retry/session behavior. Canonical writes use atomic Zstandard Parquet with content/schema fingerprints; DuckDB round-trips are tested.

The multi-asset historical POC used the awkward `2025_3_aaa` + `2025_4_aaa` pair and successfully materialized:

- three games spanning left-only, overlap, and right-only source coverage;
- 1,123 canonical pitch observations -> 861 pitch-consensus rows;
- 206 official play-sequence observations;
- one preserved source-field conflict -> one canonical quality issue;
- 6/6 official batting lines reconciled exactly;
- zero positive-pitch PA gaps, pitch-count mismatches, or orphan records;
- event-date Parquet partitions queryable through DuckDB.

Temporal validation distinguishes **event-cutoff retrospective** backtests from true **vintage information-set** backtests. Current corrected history is not mislabeled as historical vintage evidence.

## Tracking remains enrichment, not universal evidence

Velocity, spin, EV/LA, and related sensor fields vary sharply by level, park, and season. Structural absence is not missing-at-random and must not be imputed as equal opportunity. A park/league/season coverage map remains useful before Current Talent models consume tracking, but it does not block the universal outcome/profile foundation.

## Reproducibility rules

1. Preserve raw/reusable source evidence with checksums and provenance.
2. Treat release assets as mutable snapshots, not calendar truth.
3. Normalize at explicit baseball grains.
4. Keep source consensus separate from official adjudication.
5. Version parser logic, event semantics, and identity crosswalks.
6. Unknown codes/conflicts/identities fail or remain explicitly unresolved; never silently guess.
7. Structural coverage is evidence quality, not player skill.
8. Fast deterministic tests run normally; expensive live-source audits are manual after their gate is passed.

## Next foundation milestone: run-value / base-out-state reuse audit

Before assigning values to the FaBIO-compatible events, evaluate what mature public work already solves for:

1. start/end outs and base occupancy at the PA/play-sequence grain;
2. runs scored during the sequence;
3. run-expectancy / RE24 construction and league-season normalization;
4. whether the reusable MiLB files already preserve the necessary state fields reliably enough to avoid re-fetching every historical game;
5. whether baseballr, SportsDataverse, Retrosheet/baseballquery, or another established implementation supplies reusable state/reconciliation logic;
6. how Collier/FaBIO-style league-average event run values should be estimated without conflating the batter/pitcher event with contextual baserunner quality.

Only after that audit should the first **Performance value** transform be frozen and a production-scale historical backfill begin. The foul-air core-eligibility rule can be closed in parallel. Tracking, defense, richer Statcast, and Current Talent modeling remain later layer-specific gates.
