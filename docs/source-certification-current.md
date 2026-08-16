# Current Source Certification State

Last updated: 2026-08-15

This is the current checkpoint for the foundation-layer source work. Detailed experiments remain in audit scripts, workflow artifacts, and ADRs; this document records the decisions that should govern the next implementation work.

## Governing source strategy

> **Canonical authority: MLB Stats API. Canonical working data: our normalized tables, built wherever practical from mature public parsers/datasets and continuously certified against official or independent representations.**

Raw authority does not mean rebuilding mature extraction work. Reuse cleaned history and parser logic where it survives certification; write custom ingestion only for a demonstrated gap.

## Accepted source roles

| Need | Preferred source / method | Status |
|---|---|---|
| Historical affiliated MiLB pitch + Gameday batted-ball bootstrap | `armstjc/milb-data-repository` pitch releases | Accepted with versioned normalization, provenance, and conflict handling |
| Reusable historical player/team/league/season outcome counts | `armstjc/milb-data-repository` season-player batting/pitching releases | Accepted for mutually available fields after completed-2024 certification; pitching sacrifice bunts remain absent upstream |
| Official PA/result/matchup authority | MLB Stats API | Accepted |
| Official state-transition evidence and MiLB RE24 calibration | MLB Stats API play-by-play | Accepted with frozen replay semantics |
| Independent MLB state/RE24 validation | Retrosheet | Accepted validation source |
| Official HTTP/retry utility | low-level `python-mlb-statsapi` transport | Accepted; exact successful response bytes are captured separately |
| PA / non-PA semantics | versioned MLB Stats API `/eventTypes` snapshot | Accepted |
| Cross-system player IDs | pinned Chadwick Register | Accepted versioned crosswalk |
| Universal spray direction | Gameday `hc_x/hc_y` + established Petti/pybaseball transform | Accepted |
| Richer Minor Statcast | Baseball Savant / helper logic | Later optional enrichment |

## Foundation gates passed

The following are no longer open architecture questions:

1. affiliated MiLB physical-pitch history is reusable across AAA, AA, High-A, Single-A, ACL, FCL, and DSL;
2. the reusable history remains structurally useful in tested 2005 and 2015 AAA samples;
3. official PA/non-PA semantics reconcile to official batting totals in the tested reconciliation set;
4. upstream pitch releases are overlapping mutable snapshots, not trustworthy calendar partitions;
5. exact duplicates and payload variants are preserved/compacted deterministically rather than silently dropped;
6. the lossless parent event grain is `play_sequence`, not plate appearance;
7. MLBAM is the primary modern event identity and Chadwick is a versioned crosswalk;
8. Gameday `hc_x/hc_y` provides a near-universal Pull/Center/Opposite direction signal;
9. source-only cross-snapshot resolution is field consensus, not inferred chronology;
10. structured official evidence can adjudicate specific source conflicts without selecting a whole source snapshot as the winner;
11. canonical provenance, typed schemas, quality issues, Parquet persistence, DuckDB querying, and event-cutoff/vintage semantics have working tests and POCs;
12. the multi-asset historical database POC passed;
13. the minimum universal Performance-event mapper is validated from 2005 AAA through recent DSL/complex ball, before foul-air screening;
14. state replay semantics are validated on affiliated games and independently against Retrosheet;
15. deterministic RE24 mechanics are validated on a complete independent MLB season;
16. the MiLB league-to-Performance-bin state/value pipeline works across AAA and Rookie/complex environments;
17. direct small-sample league-season bin means are noisy enough that pooling had to be validated rather than assumed;
18. reusable season-player batting/pitching aggregates are certified as the historical outcome-count backbone for mutually available fields;
19. AAA bin-value estimation uses an independently confirmed, same-level shrinkage rule with 25 prior-equivalent occurrences; Rookie/complex remains unpooled until conflicting evidence is resolved.

## Reusable MiLB pitch source: certified caveats

### Physical pitch sequence is strong

Representative recent samples across all current affiliated levels match official pitch-bearing sequence structure and physical-pitch counts closely. Older 2005/2015 AAA samples also passed structural gates. The reusable source remains the historical bootstrap rather than being replaced by a custom all-history Stats API parser.

### Release files are snapshots, not month partitions

Observed defects include exact 2x row duplication in some assets, cross-month game overlap, and revised values for the same natural pitch key. Asset creation/re-upload timestamps do not reliably order baseball truth.

The reusable-source natural pitch key is:

`game_pk + at_bat_number + pitch_number`

Raw observations retain asset/checksum/retrieval provenance. Canonical partitioning uses actual event date.

### The upstream `events` PA outcome is not reusable

The parser reads the PA result but later exports a pitch-event variable into `events`. PA/result semantics therefore come from the narrow official play-sequence layer.

### Upstream batter ID can be mutated by pinch-runners

The parser changes `batter_id` for every `offensive_substitution`, including pinch-runners. Canonical sequence participants therefore come from the official structured matchup. Raw source participant IDs remain provenance/debug evidence.

### The exported `type` field is MLB `details.code`

Positive in-play evidence is reconstructed from preserved hitData-derived fields or accepted in-play codes such as `{D,E,X}` rather than an X-only rule. Historical and recent audits showed that X-only interpretation creates false missing-contact records. See ADR 010.

## Canonical event and state grains

Two opposite edge cases are real:

1. a true PA can contain zero physical pitches, such as a signaled intentional walk;
2. a physical pitch can occur in a sequence that never becomes a PA, such as an inning-ending caught stealing after a pitch.

Therefore physical evidence uses:

`game -> play_sequence -> 0..N pitches`

and:

`plate_appearance = play_sequence where official is_plate_appearance = true`

For value/state evidence, runner actions can occur before the terminal PA result. The accepted state grain is therefore:

`game -> play_sequence -> 1..N state transitions`

The frozen replay rules are:

- group runner movements by `details.playIndex`;
- emit state-changing preterminal runner/action transitions before the terminal result;
- use individual playEvent outs for preterminal transitions;
- use top-level `allPlay.count.outs` for the terminal transition;
- reconstruct bases and runs from runner movements;
- use official post-state/score fields only as reconciliation targets, never silent repair inputs;
- allow reconstructed state to propagate so errors remain visible.

The affiliated replay POC produced **476 transitions from 439 true PAs**, including **34 preterminal runner/action transitions**, with **0 quality flags**, **0 continuity breaks**, and **75/75 reconstructed official runs**. See ADR 011.

Independent Retrosheet validation then matched **228/228 ordered candidate transitions across 3 MLB games**, with **3/3 exact games**, zero transition-count mismatch half-innings, and zero shared-position state mismatches. See ADR 012.

## RE24 mechanics and AAA bin-value estimator are frozen

The accepted run-expectancy mechanics are standard 24-state base/out RE:

- estimate expected remaining runs from start base/out state using completed three-out half-innings;
- exclude incomplete/walkoff half-innings from matrix estimation;
- value a transition as `runs_scored + RE(after) - RE(before)`;
- final transitions in a half-inning receive `RE(after)=0`;
- use league-typical event/bin value for Performance skill rather than crediting a player for contextual baserunner quality on one occurrence.

The full 2025 Retrosheet validation covered **2,478 games**, **193,080 candidate transitions**, **43,875 completed three-out half-innings**, all **24/24 base/out states**, and **100% RE24 coverage**. Empty-base and bases-loaded expectancy both declined monotonically as outs increased.

The first MiLB end-to-end value POC covered **75 games across five environments** (2024 ACL/FCL/DSL and 2025 PCL/IL). All environments observed **24/24 states**, and all **5,539 core pre-foul-screen PAs** joined to RE24.

The 45-game-per-environment stability audit then showed meaningful split-half noise. Alternating 23-vs-22-game bin-value MAE ranged from about **0.058 to 0.103 runs**, with larger errors in individual bins. That result motivated explicit predictive testing rather than blindly freezing direct small-sample means.

### AAA pooling rule

Three leakage-safe tests now support a modest same-level AAA regularizer.

**2025 split-half:** direct AAA MAE/RMSE/occurrence-weighted MAE were 0.0881 / 0.1112 / 0.0823. Strengths 5–100 prior-equivalent occurrences all improved the three principal summaries.

**2025 five-fold predictive validation:** direct AAA cell MAE/RMSE were 0.0563 / 0.0735 and event MAE/RMSE were 0.4304 / 0.5124. Strengths 5–100 again improved all four summaries. Strength 25 was the conservative candidate selected for independent confirmation.

**Independent 2024 confirmation:** before looking at 2024 results, strength **25** was pre-specified. A separate June 2024 AAA snapshot supplied 45 PCL and 45 IL games, each split into five nine-game holdouts. Direct cell MAE/RMSE were 0.080304 / 0.115283 and event MAE/RMSE were 0.324536 / 0.485045. With strength 25 they improved to 0.079219 / 0.111472 and 0.324451 / 0.484600. The secondary 2024 grid placed strengths 5, 10, 25, and 50 in the robust region.

Therefore, for an AAA league-season/bin with a certified same-season peer AAA estimate:

`pooled_mean = (league_mean * league_bin_n + peer_aaa_mean * 25) / (league_bin_n + 25)`

Rules:

- the peer prior is the same bin from the other AAA league in the same season;
- the target league never contributes to its own prior;
- no all-MiLB, Rookie, MLB, or adjacent-season fallback is substituted if same-season peer evidence is absent;
- the rule is for **bin-value estimation only**, not player-talent shrinkage;
- initial calibrated implementation should use at least the validated scale of **45 games per AAA league-season when available**; more certified games are allowed and naturally reduce the relative effect of the fixed prior count;
- fewer-game calibration is not certified by this gate.

See ADR 014.

### Rookie/complex values remain direct

The Rookie/complex split-half diagnostic found no positive strength that improved all principal metrics, while five-fold validation found only a small improvement at strengths 5–25. Because those tests disagree, positive Rookie/complex pooling is not frozen. The first production transform retains direct league-season estimates there and carries the weaker estimator evidence explicitly.

## Season-player aggregate reuse

The completed-2024 certification set is the newest uniform completed-season set across AAA/Rookie batting and pitching. The 2025 Rookie batting release is a one-byte placeholder and is rejected as unavailable rather than treated as a zero-stat season.

The 2024 gate covered **6,255** source rows:

- AAA batting: 965;
- Rookie batting: 1,762;
- AAA pitching: 1,377;
- Rookie pitching: 2,151.

All four files had zero duplicate groups at `season + league_id + team_id + player_id` grain.

For batting, all **2,727 rows** exactly satisfied `PA = AB + BB + HBP + SH + SF + CI`.

For official reconciliation, one deterministic high-volume player was selected from every actual league in every source class after excluding players who appeared in multiple actual leagues. The final gate produced **10/10 exact official samples**: five batting samples matched 14 mutual fields each and five pitching samples matched 13 mutual fields each, with zero differences.

Pitching sacrifice bunts are absent upstream, so full source-only BF decomposition is intentionally unavailable and no value is invented. See ADR 013.

The aggregate files may therefore supply mutually available player/team/league/season totals such as PA/BF, AB, hits, extra-base hits, BB/IBB, HBP, K, SF, games, and starts where present. They do **not** replace play/pitch evidence for direction, exact contact-event mapping, foul-air classification, state replay, or RE24 calibration.

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

Foul airborne outs remain real Performance events but are not to be forced into the FaBIO 12-bin skill view. The exact foul-air eligibility rule remains open.

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

Live/historical mapping audits found zero structural mapping failures in the validated samples after correcting D/E/X semantics. This validates event mapping and the pre-foul-screen bin assignment; the remaining eligibility issue is foul airborne outs.

## Cross-snapshot resolution and identity

The source-only policy remains `non_null_field_consensus_v1`:

- all non-null observations agree -> resolve;
- null plus one observed non-null value -> resolve the observed value;
- multiple distinct non-null values -> leave the canonical field null and flag a quality issue;
- never use retrieval time, asset creation time, filename period, or row order as a tiebreaker.

MLBAM is the canonical modern event identity. Chadwick is a pinned/versioned enrichment layer. Missing links remain `crosswalk_pending`; automatic fuzzy-name matching is not allowed.

## Provenance, storage, and temporal semantics

The canonical contract separates immutable `source_snapshot` identity from versioned `normalization_definition` identity. Parser changes therefore do not pretend upstream evidence changed.

Exact official response bytes are captured while reusing `python-mlb-statsapi` retry/session behavior. Canonical writes use atomic Zstandard Parquet with content/schema fingerprints; DuckDB round-trips are tested.

Temporal validation distinguishes **event-cutoff retrospective** backtests from true **vintage information-set** backtests. Current corrected history is not mislabeled as historical vintage evidence.

## Tracking remains enrichment, not universal evidence

Velocity, spin, EV/LA, and related sensor fields vary sharply by level, park, and season. Structural absence is not missing-at-random and must not be imputed as equal opportunity. Coverage mapping remains useful before Current Talent models consume tracking, but it does not block the universal outcome/profile foundation.

## Reproducibility rules

1. Preserve raw/reusable source evidence with checksums and provenance.
2. Treat release assets as mutable snapshots, not calendar truth.
3. Normalize at explicit baseball grains.
4. Keep source consensus separate from official adjudication.
5. Version parser logic, event semantics, identity crosswalks, and value definitions.
6. Unknown codes/conflicts/identities fail or remain explicitly unresolved; never silently guess.
7. Structural coverage is evidence quality, not player skill.
8. Reject empty/placeholder aggregate assets as unavailable data.
9. Fast deterministic tests run normally; expensive live-source audits become manual after their gate is passed.

## Next foundation milestone: foul-air eligibility and first production Performance transform

State reconstruction, RE24 mechanics, aggregate outcome-count reuse, and the initial AAA bin-value estimator are closed. The remaining Performance architecture gate is the exact **foul-air eligibility** rule for the 12-bin FaBIO-style skill view.

The next POC should determine, from structured official/reusable evidence rather than approximate foul-line geometry, which airborne outs are foul and therefore remain real exhaustive Performance events but are excluded from the 12-bin skill accounting. The rule should be tested across historical AAA and recent AAA/Rookie environments and must preserve one exhaustive Performance row per official true PA.

Once that gate is frozen:

1. emit both exhaustive Performance events and the screened 12-bin skill view;
2. apply the accepted RE24/bin-value estimator by league-season, including AAA lambda=25 same-level pooling and direct Rookie/complex values;
3. design the historical backfill so certified season-player aggregates supply standard outcome totals while reusable play/pitch evidence supplies trajectory/direction and official PBP is targeted to calibration/state needs;
4. attach explicit estimator/source/coverage quality metadata rather than silently filling unavailable evidence.

Tracking, defense, richer Statcast, Current Talent modeling, projection/shrinkage at the **player** level, and player ranking remain later layer-specific work.
