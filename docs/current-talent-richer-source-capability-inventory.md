# Current Talent richer-evidence source capability inventory

Last updated: 2026-08-16  
Status: **SOURCE / COVERAGE GATE — FIRST PASS COMPLETE; SMALL ENDPOINT PROBE STILL REQUIRED BEFORE MODEL CONTRACT.**

## Purpose

The universal results-only Current Talent comparator is now frozen as Baseline 2 (`translated_multiseason_recency_empirical_bayes_v1`). The next question is which genuinely richer batting evidence can be added without pretending that MLB-quality tracking exists everywhere in the minors.

This inventory comes **before** a richer-model contract. It separates:

1. evidence we know is publicly available;
2. evidence whose historical league/park coverage is explicitly documented;
3. mature reusable collection/parsing work we can borrow;
4. evidence that is attractive in baseball terms but cannot support the 2021–2023 validation chronology.

No model result is evaluated in this document.

## Governing architecture

The next tier should be **coverage-aware**, not a single dense universal feature matrix.

Default architecture unless a later source audit disproves the need:

- **Baseline 2 remains the universal fallback** for every eligible hitter;
- richer features enter only when they were genuinely observed before the as-of date;
- missing lower-level tracking fields are never imputed from MLB distributions merely to make the matrix rectangular;
- source capability / tracked-event coverage is explicit model metadata;
- incremental validation compares B2 with B2+richer evidence on identical richer-evidence-eligible players / future targets;
- results are reported separately by league / source-capability tier so an MLB-only win cannot be described as a universal win.

This follows the existing Current Talent validation contract, which already forbids inferring structurally unavailable lower-level tracking/process features from MLB distributions.

## 1. Official MLB / MiLB Statcast surface

### Major League Baseball

Baseball Savant exposes the official Statcast CSV/search surface used by the existing repo MLB adapter. Official CSV documentation includes, among many other fields:

- `launch_speed` — exit velocity;
- `launch_angle`;
- `hit_distance`;
- `launch_speed_angle` contact-quality class;
- expected metrics based on speed/angle;
- pitch velocity / movement / location fields;
- newer bat-tracking fields.

Primary sources:

- Baseball Savant Statcast CSV documentation: `https://baseballsavant.mlb.com/csv-docs`
- Major League Statcast search: `https://baseballsavant.mlb.com/statcast_search`

The repo already has a thin official-Savant adapter in `src/universal_baseball/savant.py`. It deliberately follows the mature pybaseball query shape while retaining exact source bytes and projecting only explicitly required fields.

### Minor League Baseball — official documented historical coverage

Baseball Savant has a separate official **Minor League Statcast Search**:

`https://baseballsavant.mlb.com/statcast-search-minors`

MLB's page states that Minor League Statcast tracking is available since 2021 only for certain levels and ballparks. For the validation years relevant to the current project, the documented coverage is:

| season | documented tracked MiLB coverage |
|---|---|
| 2021 | Florida State League (Single-A) games |
| 2022 | Florida State League games; Pacific Coast League Triple-A games; Charlotte home Triple-A games |
| 2023 | all Triple-A games; Florida State League games |

The official page does **not** describe complete Statcast coverage for AA, High-A, other Single-A leagues, Rookie Complex, or DSL in these years.

This is the most important constraint for the next model layer. A historical 2021–2023 EV / launch-angle challenger cannot honestly be universal across affiliated baseball.

The Minor League search UI exposes batting / batted-ball and pitch-process filters or outputs including EV, launch angle, hard-hit/contact-quality measures, whiffs/swings, expected outcomes, pitch velocity/movement, and location. The exact CSV-detail export contract still needs a small source probe before being treated as production input.

## 2. Reuse audit — do not rebuild what already exists

### Existing repo Savant adapter — preferred base

`src/universal_baseball/savant.py` already provides the desired source-engineering pattern:

- official Baseball Savant source;
- stable mature Statcast query shape borrowed from pybaseball;
- exact response-byte retention at capture time;
- explicit typed projection rather than silently accepting changing upstream columns;
- canonical MLBAM batter / pitcher IDs and game IDs;
- source-specific terminal-event safeguards.

For MiLB tracking, prefer extending this thin adapter pattern after the endpoint probe rather than creating a second unrelated collection stack.

### pybaseball

Primary repository: `https://github.com/jldbc/pybaseball`

`pybaseball.statcast` is mature public work for Major League Baseball Savant downloads and is already the query-shape reference used by this project. Its current Statcast implementation uses the Major League `/statcast_search/csv` surface.

Usefulness here:

- excellent reference for resilient Savant request construction and date chunking;
- not currently established by this audit as a ready-made Minor League Statcast client.

Do **not** add pybaseball as a runtime dependency merely to reproduce behavior the repo already implements cleanly.

### baseballr

Primary repository: `https://github.com/BillPetti/baseballr`

`baseballr::statcast_search()` is another mature public implementation of the Major League Baseball Savant CSV surface. Its current code is useful as a second independent reference for handling evolving Savant columns and payload quirks.

This audit did not find primary-package evidence that baseballr provides a mature Minor League Statcast-search client for the separate MiLB search surface.

### Reuse conclusion

There is mature reusable work for the **MLB** Savant request / parsing problem. There is not yet enough evidence to justify adopting a third-party package for the **MiLB** endpoint specifically.

Therefore the lowest-cost path is:

1. keep the existing repo Savant capture/projection architecture;
2. prove the official MiLB detail CSV endpoint and schema with a tiny live probe;
3. extend only the small source-specific request/projection layer needed for MiLB;
4. do not bulk-download seasons until that probe is reconciled to existing certified player/game identity.

## 3. Candidate richer evidence families

### A. Batted-ball quality — **recommended first family**

Candidate raw evidence:

- exit velocity;
- launch angle;
- hard-hit indicator / rate (EV >= 95 mph under the official Statcast definition);
- launch-angle sweet-spot indicator / rate;
- possibly EV50 or a compact upper-tail EV summary;
- possibly raw EV × launch-angle distribution summaries.

Why first:

- directly measures quality of contact beyond B2's result/contact-shape profile;
- official Savant support exists for MLB and a documented MiLB tracked subset during 2021–2023;
- substantially simpler to validate than a full pitch-by-pitch swing-decision model;
- raw EV/LA is cleaner for this first test than importing an MLB-trained xwOBA transformation into the universal latent-talent model.

Avoid making xwOBA the first richer feature. It combines tracking with an MLB value model and can blur the question of whether raw contact quality itself adds talent information after our own environment translation.

### B. Swing / contact process — **second family**

Candidate evidence:

- swings / takes;
- whiffs;
- contact rate;
- chase / zone swing where trustworthy plate-location data exist;
- pitch-type / velocity context if later justified.

Pros:

- directly targets plate-discipline / bat-to-ball process;
- may help known K calibration defects.

Cons:

- requires trustworthy physical pitch sequences and location fields;
- source capability is more demanding than terminal batted-ball EV/LA;
- existing repo audits already show that a row sequence in an official feed does not automatically mean a physically faithful pitch sequence at every lower level.

Do after batted-ball quality unless the small source probe unexpectedly shows the latter is unusable.

### C. Bat tracking / bat speed — **defer**

Baseball Savant now exposes bat-speed / swing-path fields for MLB, but this evidence family is too new to support the already-frozen 2021–2023 Current Talent validation chronology.

It may become valuable for a later-era challenger, but it should not drive the first richer gate merely because it is exciting current data.

### D. Public scouting / rankings — **separate later evidence family**

Scouting / prospect rankings can eventually be tested, but they introduce publication timing, vintage-information-set, evaluator-source, and coverage issues that are distinct from tracking data. Do not combine them with the first EV/LA challenger.

## 4. Historical validation implications

### MLB

MLB batted-ball quality is the cleanest historically tracked tier for the 2021–2023 chronology.

### Florida State League

The official Minor League Statcast page gives FSL tracked coverage beginning in 2021, making it the only documented MiLB environment with tracked data spanning all three years of the current validation window.

This is useful because it gives at least one lower-minors population on which richer evidence can be evaluated chronologically without pretending that all Single-A was tracked.

### Triple-A

AAA coverage changes materially by year:

- no complete AAA coverage documented for 2021;
- 2022 = PCL + Charlotte home games only;
- 2023 = all AAA games.

Therefore `AAA` alone is **not** a sufficient capability label for a 2022 development fold. Venue / league tracking eligibility must be carried at event grain or an equivalent proven capability key.

Do not treat 2022 untracked International League games as ordinary random missingness.

### AA / High-A / other Single-A / complex / DSL

No 2021–2023 complete tracking entitlement has been established from the official Savant coverage statement. These players remain on the B2 fallback unless a separate source can be proven.

## 5. Proposed first-richer-tier validation architecture

Do not finalize feature/model math until the source probe passes, but the comparison structure should be:

### Universal output

Every player always has B2.

### Richer eligible tier

For a player × as-of snapshot, richer evidence is usable only if:

- the player's pre-cutoff events occurred in a league/venue/time range with proven Statcast tracking capability;
- enough actual tracked batted balls exist to construct the predeclared feature(s);
- those observations precede the as-of date;
- source identity reconciles to the certified Current Talent evidence surface.

### Evaluation

On richer-eligible rows compare:

- **B2** using exactly the same player / target sample;
- **B2 + batted-ball-quality challenger**.

Required breakout:

- MLB;
- FSL Single-A;
- AAA tracked tier, with 2022 partial-coverage status kept explicit;
- evidence-volume bands;
- prior-MLB-evidence status;
- promotion / demotion future target transition where existing diagnostics permit.

A tracked-tier challenger can be useful even if it cannot replace B2 universally. Promotion language must be scoped correctly:

- `universal Current Talent comparator` = B2;
- `richer tracked-data tier` = optional enhancement where observed and validated.

## 6. Small source probe required before challenger contract

Before writing the richer model contract or downloading full seasons, perform a tiny reproducible official-source probe.

Minimum probe goals:

1. verify the current official Minor League detail-CSV request endpoint / query shape rather than relying on a tutorial or guessed URL;
2. capture exact raw response bytes for a very small date slice;
3. confirm presence / semantics of at least:
   - game date;
   - game PK;
   - batter MLBAM ID;
   - plate appearance / pitch identifiers sufficient for deduplication;
   - `launch_speed`;
   - `launch_angle`;
   - `bb_type` / contact result where available;
4. prove that one tracked 2023 AAA sample and one FSL sample reconcile by player/game to the existing certified Current Talent evidence;
5. quantify missing EV/LA among otherwise eligible BBE in the sample rather than assuming 100% measurement;
6. preserve an explicit capability status for untracked / unavailable events.

Do not bulk materialize 2021–2023 MiLB Statcast until this probe passes.

## 7. Decision after inventory

**Recommended first richer evidence family: raw batted-ball quality (EV + launch-angle-derived compact summaries).**

Reason: it has the best combination of baseball relevance, incremental information beyond B2, historical MLB support, some documented lower-minors support, and manageable source complexity.

However, it should be implemented as a **tracked-data tier over B2**, not as a fake universal model.

Next repo step: implement the tiny official MiLB Savant source probe and reconcile it to certified evidence. Only after that succeeds should we predeclare the exact EV/LA feature set, evidence minimums, chronology, and promotion rule.