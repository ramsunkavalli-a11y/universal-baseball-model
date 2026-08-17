# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active branch / PR

- Working branch: `source-certification-poc`
- Open draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind. Inspect current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly **2–3 steps** and verify before expanding.
- Prefer mature public datasets, parsers, packages, and prior public work over rebuilding raw cleanup.
- When raw play-by-play is necessary, deliberately evaluate reusable options first.
- Surface early errors rather than compounding them.
- Heavy live-source certification workflows should return to **manual-only after their gate passes**; deterministic tests belong in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate until their contracts justify combination.

## Current project stage

The data/source foundation and first batting Performance layer are mature enough to support modeling work. Historical Current Talent evidence and chronological validation plumbing are functioning. The project is now finishing the **MLB historical evidence / environment-translation bridge** before fitting the first Current Talent baselines.

There is **no promoted Current Talent estimator yet**.

## Completed milestones

### 1. Reuse-first canonical foundation

Source roles, provenance, canonical schemas, identity handling, event semantics, contact reconstruction, state replay, RE24, level/season capability gates, contextual bin-value policies, and typed persistence are implemented and tested.

Primary references:

- `docs/source-audit.md`
- `docs/source-certification-current.md`
- `docs/canonical-data-contract.md`
- `docs/adr/`

### 2. 2024 affiliated-MiLB batting Performance

Production-shaped batting Performance is certified across **14 actual leagues / 5 affiliated level groups**.

Checkpoint: `docs/performance-2024-affiliated-checkpoint.md`  
Certified workflow: `31948208695`

Key totals:

- 4,995 player × actual-league × season rows
- 784,285 PA
- 494,884 reusable contact events
- 764,713 screened core Performance events
- 97.50% core-profile PA coverage
- 156 unknown contacts
- 0 unvalued core events

### 3. Historical affiliated-MiLB Current Talent evidence, 2021–2023

All five post-reorganization affiliated level groups are certified for **2021, 2022, and 2023**.

Full-season runs:

- 2021: `31979609553`
- 2022: `31971662070`
- 2023: `31971923778`

2021 combined evidence:

- 180,523 player-game rows
- 4,214 players
- 14 actual leagues / 5 level groups
- 704,360 PA
- 438,970 expected result contacts
- 439,034 observed physical contacts
- +64 net contact residual
- 686,903 core profile events

Checkpoint: `docs/current-talent-historical-milb-checkpoint.md`  
Governing evidence distinction: ADR 024 keeps PA/result opportunity separate from observed physical contact/profile evidence.

### 4. Leakage-safe Current Talent snapshot / future-target surface

Implemented modules:

- `src/universal_baseball/current_talent_evidence.py`
- `src/universal_baseball/current_talent_validation.py`
- `src/universal_baseball/current_talent_validation_dataset.py`
- `src/universal_baseball/current_talent_universal_evidence.py`

Frozen chronology:

- predictor evidence: `game_date < as_of_date`
- future target: `game_date >= as_of_date` and before the exclusive horizon end
- no fake within-day ordering from game PK or row order
- actual as-of and future environments are preserved

Real five-level 2021-08-01 → 90-day validation run: `31980820797`

- predictor players: 3,828
- target players: 3,631
- players present on both sides: 3,245
- scoring environment rows: 3,882
- SAME_LEVEL: 3,144
- PROMOTION: 523
- DEMOTION: 212
- AMBIGUOUS_AS_OF_ENVIRONMENT: 3

This proved that real promotion/demotion outcomes can be scored in the environment where they occurred.

### 5. Candidate environment-translation foundation

`src/universal_baseball/current_talent_translation.py` implements candidate training-only matched-player translation infrastructure. It is **not yet a frozen final translation model**.

Current policy:

- training games strictly before cutoff;
- chronological player environment stints;
- same-day multi-environment ambiguity breaks continuity;
- only adjacent observed stints are paired;
- sparse intermediate stops cannot be dropped to manufacture a cleaner transition;
- 12-component core profile uses symmetric-pseudocount CLR representation;
- candidate pair weight = `n1*n2/(n1+n2)`;
- first fitter uses within-player weighted graph least squares;
- fit fails closed unless every fitted level connects to requested reporting anchor, normally `MLB`.

Real 2021 pre-August MiLB support diagnostic: `31982728210`

- 100,152 training player-games / 3,828 players
- 4,967 observed environment stints
- 1,124 adjacent stint pairs
- 441 eligible pairs across 398 players
- 303 promotions / 127 demotions / 11 same-level changes

All five MiLB level groups are connected. Before the MLB historical gate, MLB was the only missing structural anchor.

### 6. Historical MLB Current Talent evidence — 2021 certified

The first historical MLB season is now certified on the same universal player-game evidence contract.

Checkpoint: `docs/current-talent-historical-mlb-checkpoint.md`  
Certified workflow run: **`31986504169`**  
Workflow: `.github/workflows/current-talent-historical-mlb-season.yml` — manual-only after certification.

2021 MLB evidence:

- 1,049 players
- 51,476 player-game rows
- 147,053 profile rows
- 181,818 PA
- 17,906 BB+HBP
- 42,145 K
- 121,705 expected result-contact opportunities
- 121,707 observed physical contacts
- +2 physical-contact residual, diagnostic only
- 62 special non-contact outcomes
- 0 PA-accounting residual

Independent official MLB season reconciliation at player × actual AL/NL × season grain is **exact**:

- PA mismatches: 0
- BB/HBP mismatches: 0
- K mismatches: 0
- expected-contact mismatches: 0
- special-noncontact mismatches: 0
- exact outcome mismatch rows: 0

Historical source semantics frozen by this gate:

- `two_strike_mid_pa_substitution_v1`: 7 strikeout PAs reassign official PA/K outcome identity from a substitute who entered with two strikes back to the original batter, using game-grain pitch sequence only.
- `known_event_or_field_error_interference_narrative_v2`: only terminal `field_error` + explicit interference-error result text is treated as the historical interference special outcome; a `fielders_choice` whose narrative later mentions interference remains a normal result-contact PA.
- physical contact remains separate from result attribution under ADR 024.
- Savant historical Oakland display alias `ATH -> OAK` is explicit and season-scoped for 2021–2024.
- bounded Savant 429/5xx retries and chunk caching were added after a live 502; transport resilience does not alter acceptance semantics.

## Important boundaries / not complete

Still not frozen or validated:

- **2022 and 2023 historical MLB evidence**;
- a real MLB-connected translation fit across certified MLB + MiLB evidence;
- whether level-only translation is sufficient or actual league/season residual effects add out-of-time value;
- age/environment priors;
- Baseline 0 (environment prior);
- Baseline 1 (Marcel-style empirical Bayes player evidence);
- rolling-origin proper-score/calibration validation;
- final uncertainty model;
- richer process/tracking/scouting inputs;
- Projection, playing time/role, WAR/value, defense integration, or final ranking.

The 90-day future target currently uses complete future player-game evidence. The contract's exact **200-PA aggregate diagnostic cap is not yet applied** because the certified historical backbone is player-game aggregate. Do not invent within-game PA order to force exactly 200; use a certified complete-game cap policy or true PA-grain target surface first.

## Governing Current Talent contract

`docs/current-talent-validation-contract.md` remains authoritative:

- Current Talent = latent rate/profile ability **now**, conditional on opportunity.
- Preserve component profile first; scalar value is secondary.
- Environment effects are learned from training-period data only.
- Primary target = next 90 calendar days; secondary 30/180/~365.
- Zero future PA is not poor talent.
- Promotions/demotions are scored in actual future environment.
- Validation is chronological / rolling-origin, never random split.
- Proper scoring and calibration outrank prettier correlation.
- Richer evidence must beat simple results-only baselines out of time.

## Recommended next batch

1. **Certify 2022 historical MLB evidence** independently using the now-frozen 2021 rules; if green, repeat for 2023.
2. Combine certified MLB + affiliated-MiLB training evidence and fit the first real **MLB-connected translation surface** inside chronological training data only.
3. Inspect translation support, offset stability, residuals, and actual league/season effects before freezing the form.
4. Then fit **Baseline 0 / Baseline 1 only** and validate out of time before adding richer evidence.

Do not skip directly to a complicated talent model.

## Useful workflows / scripts

Manual live/reuse workflows:

- `.github/workflows/current-talent-historical-milb-one-level.yml`
- `.github/workflows/current-talent-historical-mlb-season.yml`
- `.github/workflows/current-talent-validation-snapshot-one-level.yml`
- `.github/workflows/current-talent-validation-snapshot-multilevel.yml`
- `.github/workflows/current-talent-translation-support.yml`

Key materializers:

- `scripts/materialize_current_talent_historical_milb_game_evidence.py`
- `scripts/materialize_current_talent_historical_mlb_game_evidence.py`
- `scripts/materialize_current_talent_validation_snapshot.py`
- `scripts/materialize_current_talent_validation_snapshot_multilevel.py`
- `scripts/materialize_current_talent_translation_support.py`

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-historical-mlb-checkpoint.md` for the current MLB bridge and `docs/current-talent-historical-milb-checkpoint.md` only as needed.
4. Inspect current `source-certification-poc` head before editing.
5. Continue with **2022 MLB certification** in a small verified batch; do not re-audit already-closed source questions.
