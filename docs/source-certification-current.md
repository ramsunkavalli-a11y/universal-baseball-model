# Current Source Certification State

Last updated: 2026-08-17

This is the **current source-foundation checkpoint**, not the live project roadmap. The source architecture recorded here remains the governing foundation for Performance, Current Talent, and Projection evidence reuse. For the active model stage, blocker, and next task, read `docs/project-status.md` first.

Detailed experiments remain in audit scripts, workflow artifacts, and ADRs; this document records source decisions that should continue to govern downstream implementation.

## Governing source strategy

> **Canonical authority: MLB Stats API. Canonical working data: our normalized tables, built wherever practical from mature public parsers/datasets and continuously certified against official or independent representations.**

Raw authority does not mean rebuilding mature extraction work. Reuse cleaned history and parser logic where it survives certification; write custom ingestion only for a demonstrated gap.

## Accepted source roles

| Need | Preferred source / method | Status |
|---|---|---|
| Historical affiliated MiLB pitch + Gameday contact bootstrap | `armstjc/milb-data-repository` PBP releases | Accepted with versioned normalization, snapshot consensus, provenance, and quality controls |
| Historical player/team/league/season outcome counts | armstjc season-player batting/pitching releases | Accepted for mutually available fields after completed-2024 certification |
| Player-game broad-contact control | armstjc player-game batting releases | Accepted after exact-dedup + component-wise snapshot resolution |
| Official PA/result/matchup authority | MLB Stats API | Accepted |
| Exception contact participant authority | MLB Stats API top-level matchup batter | Accepted only for games triggered by player-game residual controls |
| State-transition evidence / MiLB RE24 calibration | MLB Stats API PBP | Accepted with frozen replay semantics |
| Independent MLB state/RE24 validation | Retrosheet | Accepted validation source |
| Official HTTP/retry utility | low-level `python-mlb-statsapi` transport | Accepted; exact response bytes captured separately |
| PA / non-PA semantics | versioned MLB Stats API `/eventTypes` snapshot | Accepted |
| Cross-system player IDs | pinned Chadwick Register | Accepted versioned crosswalk |
| Universal spray direction | Gameday `hc_x/hc_y` + established Petti/pybaseball transform | Accepted |
| Richer Minor Statcast | Baseball Savant / helper logic | Optional enrichment; not universal evidence |

## Foundation gates passed

The following are no longer open architecture questions:

1. armstjc MiLB PBP is the historical affiliated bootstrap, but release assets are overlapping mutable snapshots rather than month partitions;
2. exact duplicates and payload variants are handled deterministically and raw provenance is preserved;
3. the lossless parent grain is `play_sequence`, not plate appearance;
4. official `/eventTypes` semantics define true PAs and non-PAs;
5. MLBAM is primary modern identity; Chadwick is a versioned crosswalk;
6. source-only cross-snapshot resolution is non-null field consensus, never inferred chronology;
7. Gameday `hc_x/hc_y` supports near-universal Pull/Center/Opposite direction from tested 2005 AAA through recent Rookie/DSL;
8. reusable source in-play evidence uses accepted D/E/X codes plus preserved hitData evidence rather than X-only logic;
9. the exhaustive Performance event taxonomy and screened FaBIO-compatible 12-bin view are implemented;
10. foul-air core exclusion is the exact official/source narrative phrase `foul territory`, not spray geometry;
11. state replay is validated on affiliated games and independently against Retrosheet;
12. RE24 mechanics are independently validated over the complete 2025 Retrosheet season;
13. league-season Performance-bin value pooling has level-specific certified policies;
14. season-player aggregates are accepted as the historical standard outcome-count backbone;
15. pitch-process evidence is explicitly gated by league × season where official feeds are synthetic;
16. player-game batting releases are accepted as broad-contact controls after snapshot resolution;
17. source contact physical keys are reusable while batter attribution is corrected through an exception-only official overlay triggered by player-game residuals;
18. canonical provenance, typed schemas, quality issues, Parquet persistence, DuckDB querying, and event-cutoff/vintage semantics have working tests and POCs.

## Canonical grains and source semantics

Physical evidence uses:

`game -> play_sequence -> 0..N pitches`

and:

`plate_appearance = play_sequence where official is_plate_appearance = true`

A true PA can contain zero pitches (for example, a signaled IBB), and a physical pitch can occur in a sequence that never becomes a true PA (for example, a pitch before an inning-ending caught stealing).

For state/value evidence:

`game -> play_sequence -> 1..N state transitions`

Preterminal runner actions are split into their own state transitions. Individual playEvent outs are used for preterminal actions; top-level `allPlay.count.outs` is used for terminal outs. State propagates without silent repair.

The affiliated replay POC produced **476 transitions from 439 true PAs**, including **34 preterminal transitions**, with zero quality flags/continuity breaks and **75/75 runs** reconstructed. Independent Retrosheet validation matched **228/228 ordered transitions across three MLB games** with zero state mismatches. See ADRs 011–012.

## Reusable PBP caveats

### Mutable snapshots

Release filenames do not establish baseball chronology. Assets can overlap, be re-uploaded, contain exact duplication, and revise values for the same natural pitch key.

Natural pitch key:

`game_pk + at_bat_number + pitch_number`

Resolve source fields by non-null consensus. Multiple distinct non-null values remain unresolved and generate quality evidence. Do not use retrieval time, asset creation time, filename month, or row order as a baseball-truth tiebreaker.

### Upstream PA `events` is not authoritative

The parser reads PA result information but exports a pitch-event variable into its `events` field. PA/result semantics therefore do not come from that column.

### In-play semantics

The exported `type` is MLB `details.code`. Contact rows legitimately use `D`, `E`, and `X`; X-only interpretation incorrectly loses a large share of contact events. See ADR 010.

### Batter identity mutation

The upstream parser mutates batter ID for every `offensive_substitution`, including pinch-runners. Physical contact geometry remains reusable, but per-pitch source batter identity is not canonical authority. See ADRs 019–020.

## Pitch-process evidence is league × season capability

PA/outcome/BIP/state evidence and physical pitch-sequence/process evidence are separate capabilities.

The fixed 20-games-per-league audit found:

- **2023 ACL/FCL/DSL:** strongly outcome-minimal/synthetic pitch sequences; do not use for pitches/PA, count paths, swing/whiff opportunities, sequencing, or similar process features;
- **2024 ACL/FCL:** normal-looking relative to Single-A control and eligible under the current capability policy;
- **2024 DSL:** still synthetic/outcome-minimal and process-ineligible;
- **Single-A control:** normal in both audited seasons.

Do not downgrade reliable DSL PA/outcome/BIP/state evidence merely because pitch-process evidence is unavailable. See ADR 016 and `pitch_process_coverage.py`.

## Batted-ball Performance evidence

Direction uses:

- Gameday `hc_x/hc_y`;
- Bill Petti / pybaseball spray-angle transform including the `0.75` calibration factor;
- direction relative to batter handedness.

No production `hit_location` fallback and no approximate foul-line geometry are used.

Trajectory families:

- `popup -> IFFB`;
- `fly_ball -> OFFB`;
- `line_drive -> LD`;
- `ground_ball -> GB`;
- `bunt_* -> BUNT` special family.

The screened core bins are:

- `BB_HBP`;
- `K`;
- `IFFB`;
- Pull / Center / Opposite × OFFB / LD / GB.

Bunts and special outcomes remain explicit outside the core. Confirmed airborne foulouts are excluded from the core only when the structured result narrative contains exact phrase `foul territory`; missing relevant narrative means unknown/ineligible rather than assumed fair. See ADRs 008 and 015.

## RE24 and league-season bin-value policy

RE24 is:

`event_runs + RE(after) - RE(before)`

Expected runs are estimated from completed three-out half-innings; incomplete/walkoff halves are excluded from matrix estimation. The 2025 Retrosheet gate covered **2,478 games, 193,080 transitions, all 24 states, and 100% RE24 coverage**.

Direct small-sample league-season bin means were noisy, so pooling was accepted only where pre-registered held-out validation survived an independent season.

Current production policy (`bin_value_policy.py`):

| Level | Policy | Prior-equivalent occurrences |
|---|---|---:|
| AAA | same-level, same-season peer-bin pooling | 25 |
| AA | same-level, same-season leave-target-environment-out pooling | 75 |
| High-A | direct | 0 |
| Single-A | same-level, same-season leave-target-environment-out pooling | 25 |
| Rookie/complex | direct | 0 |

These are **bin-value regularizers**, not player-talent shrinkage. No adjacent-level or all-MiLB prior is substituted when certified same-level peer evidence is unavailable. See ADRs 014 and 017.

## Season aggregate outcome backbone

Completed 2024 is the newest uniform certification year; the 2025 Rookie batting asset is a one-byte placeholder and is treated as unavailable.

The initial completed-season audit covered **6,255 AAA/Rookie batting/pitching rows** with zero duplicate source grain. All **2,727 batting rows** satisfied exact PA accounting. Ten deterministic one-league official samples matched every mutually available field.

A later all-level audit supports standard outcome totals across AAA, AA, High-A, Single-A, and Rookie. GO/AO and pitch-count convenience fields can be retained where explicitly certified, but detailed trajectory hit/out columns are not valid substitutes for directional contact-event counts, and swing/whiff aggregates do not override league-season pitch-process capability gates. See ADRs 013 and 018.

## Player-game broad-contact control and exception-only identity overlay

The player-game layer provides a cheap independent contact-count control.

For 2024 AAA:

- raw projected player-game rows: **267,934**;
- exact duplicate rows removed: **138,410**;
- resolved player-games: **128,641**;
- 45 conflicting player-games across three games were partial→complete snapshots with a unique component-wise dominant observation;
- resolved player-game contact total: **111,878**;
- certified season aggregate `ballsInPlay`: **111,878**;
- exact player-league rows: **893/893**.

Reusable PBP contained **111,884** broad contact rows and player-game controls flagged **244 games** with attribution/count residuals. A tempting strict +1/-1 source-only repair was wrong in **1 of 182** official validations and therefore is **not** a production mutation.

Official PBP over all 244 flagged games showed:

- source contacts: **12,725**;
- official contacts: **12,725**;
- matched physical keys: **12,725**;
- source-only keys: **0**;
- official-only keys: **0**;
- source-vs-official batter mismatches on matched keys: **254**.

After official participant overlay, the remaining net +6 player-game count residual exactly matched the independent difference between official `isInPlay` contacts and boxscore `AB - SO + SF + SH` contact accounting. It is preserved as a definition difference, not repaired away.

A deterministic evenly spaced sample of **120 unflagged games** then produced **6,039/6,039 physical keys and zero hidden batter mismatches**, supporting player-game residuals as a high-recall trigger.

Production contact-participant policy:

1. reuse source physical contact evidence by default;
2. resolve player-game snapshots conservatively;
3. compare source vs player-game contact counts at game/player grain;
4. if any player residual exists, fetch official PBP for that game and overlay top-level matchup batter on matching physical contact keys;
5. preserve original source batter and overlay provenance;
6. never auto-apply inferred +1/-1 reassignments;
7. preserve PBP-vs-boxscore contact-definition differences separately.

See ADR 020.

## Identity

MLBAM is canonical modern event identity. Chadwick is a pinned/versioned crosswalk. Missing links remain explicitly pending; automatic fuzzy-name matching is not allowed.

## Provenance, storage, and temporal semantics

The canonical contract separates immutable `source_snapshot` identity from versioned `normalization_definition` identity. Exact successful official response bytes are captured separately from parsed objects. Canonical writes use atomic Zstandard Parquet with content/schema fingerprints and tested DuckDB round trips.

Temporal validation distinguishes **event-cutoff retrospective** backtests from true **vintage information-set** backtests. Current corrected history is not mislabeled as historical vintage evidence.

## Reproducibility rules

1. Preserve raw/reusable evidence with checksums and provenance.
2. Treat release assets as snapshots, not calendar truth.
3. Normalize at explicit baseball grains.
4. Keep source consensus separate from official adjudication.
5. Version parser logic, event semantics, identity crosswalks, capability rules, and value definitions.
6. Unknown codes/conflicts/identities remain explicit; never silently guess.
7. Structural coverage is evidence quality, not player skill.
8. Empty/placeholder aggregate assets are unavailable data, not zero-stat seasons.
9. Fast deterministic tests run normally; expensive live-source audits become manual after their gate passes.

## Downstream status

The source/event/value architecture described above is no longer waiting for its first Performance implementation.

Since this source checkpoint was originally written:

1. the completed-2024 affiliated **Performance** player-season layer was built and is production-shaped;
2. universal **Current Talent Baseline 2** was developed, confirmed, and frozen as `translated_multiseason_recency_empirical_bayes_v1`;
3. two richer Current Talent challengers were evaluated under chronological gates and closed without promotion;
4. **Projection v1** is now the active stage, using frozen Current Talent as its starting state;
5. the current Projection implementation is reusing this certified source stack to assemble 2022–2024 development evidence while keeping 2025 outcomes quarantined.

Projection exposed a 2024 historical-reuse edge case when `game_pk 755829` returned HTTP 404 from the expected official `/feed/live` surface. Follow-up source-only audit run `32092166134` localized the observed mismatch to two exact source-only residual rows:

- High-A player `669233`, game `755829`: one extra `PA=1, AB=1` row;
- Single-A player `686541`, game `754395`: one extra `PA=1, AB=1, SO=1` row.

A fail-closed quarantine is now implemented in `current_talent_source_residual_quarantine.py` under policy `single_source_only_exact_season_and_official_residual_v1`. It applies only when there is exactly one source-only positive-PA game and both independent ledgers agree exactly: the row must equal the season-player residual, and removing its full outcome vector must make the remaining player-game totals equal official gameLog totals. Anything less remains unresolved; no source values are reassigned. Fast CI run `32092505104` passed the helper and its regression tests.

This remains a narrow source-quality exception, not a reason to replace the reuse-first architecture. The current next source gate is a clean rerun of the full 2024 MiLB historical evidence path with this policy active.

For live status and next actions, use:

- `docs/project-status.md`
- `docs/projection-batting-v1-plan.md`
- `docs/projection-status.json`
- `docs/projection-recovery-status.json`

Do not use this source-certification document as a model-stage work queue.
