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
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests belong in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate until their contracts justify combination.
- **Pause at meaningful project junctures to update repository documentation before continuing.** At minimum, refresh this file after a major gate passes, a material modeling/architecture decision is frozen, or the recommended next batch changes. The goal is that a new chat can resume from the repo without rediscovering conversation context.

## Current project stage

The project is now in **chronological Current Talent model validation**, not source plumbing.

Completed foundations include:

- canonical/reuse-first public-data architecture;
- first production-shaped batting Performance layer;
- certified 2021–2023 affiliated-MiLB and MLB Current Talent evidence;
- leakage-safe snapshot/future-target construction;
- training-only MLB-anchored environment translation;
- exact age-as-of enrichment;
- Baseline 0 / Baseline 1 estimator primitives;
- **the first real universal 2021-08-01 → 90-day predictive baseline gate**.

The first real gate is promising: **Baseline 1 beats Baseline 0 on both event-weighted log loss and multinomial Brier over 344,391 future core events**, and the improvement is broad across target levels, transition classes, age bands, evidence bands, and all 12 profile components.

However, **there is still no promoted/frozen Current Talent estimator**. This is one cutoff with candidate hyperparameters. Calibration is not uniformly better component-by-component, so the next gate is rolling-origin stability and hyperparameter/translation ablation, not richer features.

## Governing Current Talent contract

`docs/current-talent-validation-contract.md` remains authoritative.

Key boundaries:

- Current Talent = latent rate/profile ability **now**, conditional on opportunity.
- Preserve the 12-component profile first; scalar value is secondary.
- Environment effects are learned from training-period data only.
- Predictor evidence must be strictly pre-cutoff.
- Future outcomes are scored in the environment where they actually occur.
- Primary target = next 90 calendar days; secondary 30/180/~365.
- Zero future PA is not poor talent.
- Validation is chronological / rolling-origin, never random split.
- Proper scoring and calibration outrank prettier correlation.
- Richer evidence must beat simple results-only baselines out of time.

## Completed milestones

### 1. Reuse-first canonical foundation

Source roles, provenance, canonical schemas, identity handling, event semantics, contact reconstruction, state replay, RE24, level/season capability gates, contextual bin-value policies, and typed persistence are implemented and tested.

References:

- `docs/source-audit.md`
- `docs/source-certification-current.md`
- `docs/canonical-data-contract.md`
- `docs/adr/`

### 2. 2024 affiliated-MiLB batting Performance

Checkpoint: `docs/performance-2024-affiliated-checkpoint.md`  
Certified workflow: `31948208695`

- 14 actual leagues / 5 level groups
- 4,995 player × actual-league × season rows
- 784,285 PA
- 494,884 reusable contact events
- 764,713 screened core Performance events
- 97.50% core-profile PA coverage
- 156 unknown contacts
- 0 unvalued core events

### 3. Historical affiliated-MiLB Current Talent evidence, 2021–2023

Checkpoint: `docs/current-talent-historical-milb-checkpoint.md`

Certified runs:

- 2021: `31979609553`
- 2022: `31971662070`
- 2023: `31971923778`

All five post-reorganization affiliated level groups are certified independently for each season.

### 4. Leakage-safe snapshots / future targets

Implemented:

- `src/universal_baseball/current_talent_evidence.py`
- `src/universal_baseball/current_talent_validation.py`
- `src/universal_baseball/current_talent_validation_dataset.py`
- `src/universal_baseball/current_talent_universal_evidence.py`

Frozen chronology:

- predictor evidence: `game_date < as_of_date`;
- future target: `game_date >= as_of_date` and before the exclusive horizon end;
- no fake within-day ordering from game PK / row order;
- actual as-of and future environments preserved.

Five-level MiLB 2021-08-01 → 90-day integration run: `31980820797`.

### 5. Historical MLB Current Talent evidence — 2021–2023 certified

Checkpoint: `docs/current-talent-historical-mlb-checkpoint.md`  
Workflow: `.github/workflows/current-talent-historical-mlb-season.yml` — **manual-only**.

Certified runs:

- 2021: `31986504169` — 181,818 PA
- 2022: `31988255280` — 182,052 PA
- 2023: `31989561396` — 184,104 PA

Every season reconciles exactly to independent official MLB player × actual AL/NL × season totals for PA, BB/HBP, K, expected-contact opportunity, and special non-contact outcomes. The remaining +2 physical-contact residual per season is an ADR-024 diagnostic, not a repaired result count.

### 6. MLB-anchored environment translation — three-year stability gate passed

Implementation:

- `src/universal_baseball/current_talent_translation.py`
- `scripts/materialize_current_talent_translation_support.py`
- `.github/workflows/current-talent-translation-support.yml` — **manual-only**

Candidate method: `matched_adjacent_stint_clr_wls_v1`.

Policy:

- training games strictly before cutoff only;
- chronological player environment stints;
- same-day multi-environment ambiguity breaks continuity;
- adjacent observed stints only;
- sparse intermediate stops cannot be skipped to manufacture transitions;
- 12-component symmetric-pseudocount CLR (`0.5`);
- pair weight = `n1*n2/(n1+n2)`;
- weighted graph least squares with `MLB = 0` anchor;
- fail closed unless every fitted level connects to MLB.

Independent Aug. 1 fits succeeded in 2021, 2022, and 2023. K and BB/HBP recover a coherent level ladder across all three years; contact-shape effects are noisier and are **not** constrained to look monotonic.

Reference runs:

- 2021 readable-offset fit: `31992143231`
- 2022: `31992265175`
- 2023: see translation-support history / checkpoint notes

This is still a **candidate observation layer** until predictive ablation confirms that translation improves held-out scoring.

### 7. Exact age-as-of enrichment

Implementation:

- `src/universal_baseball/chadwick.py`
- `scripts/audit_current_talent_age_coverage.py`
- `.github/workflows/current-talent-age-coverage.yml` — **manual-only**

2021-08-01 audit run: `31992658592`.

- universal predictor players: **4,315**
- exact DOB / exact age-as-of: **4,315**
- coverage: **100.0%**
- missing exact age: **0**

Age is derived from the pinned Chadwick DOB at the explicit cutoff; a mutable current-age field is not stored.

### 8. Baseline 0 / Baseline 1 primitives

Checkpoint: `docs/current-talent-baseline-checkpoint.md`  
Implementation CI: `31992880494` — passed.

Implementation:

- `src/universal_baseball/current_talent_baselines.py`
- `tests/test_current_talent_baselines.py`

Baseline 0 — `loo_age_level_population_prior_v1`:

- no player-specific recent Performance in the predicted player's prior;
- exact age-as-of + actual unambiguous current level;
- default 2-year age band;
- same-level + same-age-band leave-one-out peers preferred;
- default minimum preferred peers = 12;
- fallback to same level, then global other-player pool only when necessary;
- player is explicitly excluded from every peer pool.

Baseline 1 — `translated_recency_empirical_bayes_v1`:

- recency-weighted player core-profile evidence;
- aggregate at player × level first;
- translate each level segment to MLB scale **before** multi-level pooling;
- empirical-Bayes shrinkage toward Baseline 0;
- current candidate prior strength = 100 effective core events.

### 9. First real chronological Baseline 0 / Baseline 1 predictive gate — passed

Primary diagnostic rerun: **`31993773737`**  
First successful scoring run: `31993534180`  
Workflow: `.github/workflows/current-talent-baseline-validation.yml` — **manual-only after bootstrap cleanup**.  
Artifact from diagnostic rerun: `current-talent-baseline-validation-2021-2021-08-01`.

Implementation added:

- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `tests/test_current_talent_scoring.py`
- `tests/test_current_talent_score_diagnostics.py`

#### Gate design

For `2021-08-01`:

1. combine certified MLB + five affiliated-MiLB level evidence;
2. fit the environment translation using **only games before the cutoff**;
3. derive exact age at the cutoff from pinned Chadwick;
4. build Baseline 0 / Baseline 1 using pre-cutoff evidence only;
5. map MLB-scale latent profiles into each **realized future target level** with the training-only level effect;
6. score all eligible future core events in the next 90 days;
7. retain aggregate, level, transition, age-band, evidence-band, component, and reliability diagnostics.

Current candidate predictor settings used for this gate:

- season-to-date evidence;
- 90-day recency half-life;
- Baseline 1 prior strength = 100 effective core events;
- Baseline 0 age-band width = 2 years;
- minimum preferred age-level peers = 12.

**None of these hyperparameters are frozen from this single cutoff.**

#### Coverage

- combined universal evidence: **4,715 players / 231,999 player-games / 886,178 PA**
- predictor players before cutoff: **4,315**
- exact-age coverage: **4,315 / 4,315**
- players receiving a Baseline 0/1 profile: **4,301**
- 14 predictor players were excluded because their current environment was ambiguous under the fail-closed as-of rule
- raw validation players with predictor + future target: **3,730**
- baseline-scored players: **3,722**
- therefore 8 otherwise-scoreable future players were among the 14 ambiguous-environment baseline exclusions
- scored target-environment rows: **4,634**
- future core events scored: **344,391**
- target players with no pre-cutoff predictor evidence remain coverage-only: **400**

Baseline 0 peer pools:

- same age-band + level: **4,256 players**
- same-level fallback: **45 players**
- global fallback: **0**

#### Aggregate proper scores

| Model | Event-weighted log loss | Multinomial Brier |
|---|---:|---:|
| Baseline 0 | 2.268828 | 0.872730 |
| Baseline 1 | **2.252931** | **0.868446** |

Baseline 1 minus Baseline 0:

- log loss: **-0.015896**
- Brier: **-0.004284**

Lower is better for both metrics.

#### Breadth of the Baseline 1 gain

The diagnostic rerun persists these comparisons directly in the artifact.

Baseline 1 improved **both log loss and Brier in all 21 separate diagnostic strata**:

- all **6 target levels**;
- all **5 aggregate transition classes** represented (`SAME_LEVEL`, `PROMOTION`, `DEMOTION`, `MLB_DEBUT`, `MLB_TO_MILB`);
- all **5 fixed age bands**;
- all **5 fixed effective-evidence bands**.

It also improved both proper-score contributions in **all 12 core profile components**.

The evidence-volume pattern is directionally sensible for empirical Bayes: the Baseline 1 advantage is smallest below 25 effective core events and grows as player evidence increases.

Do not over-interpret tiny level × transition cross-product cells; the broad claim above is about the separate fixed strata, not every sparse intersection.

#### Calibration caveat

Proper scoring improved broadly, but reliability calibration did **not** improve uniformly for every component.

Examples from the 2021 gate:

- BB/HBP reliability improved materially;
- several contact components improved slightly;
- K reliability ECE worsened slightly despite K proper-score contribution improving.

Therefore this gate supports continuing with Baseline 1, **not freezing or promoting it yet**. Calibration and hyperparameter selection remain active validation questions.

## Important boundaries / not complete

Still not frozen or validated:

- whether Baseline 1's 2021 win survives independent later cutoffs/seasons;
- selected recency window / half-life;
- 2-year age-band width, 12-peer threshold, and 100-core-event EB prior strength;
- whether the candidate environment translation itself improves future prediction versus a no-translation/simple alternative;
- whether level-only translation is sufficient or actual league/season residual effects add out-of-time value;
- calibration stability / calibration model, especially by component;
- final uncertainty model;
- Baseline 2 / richer process-tracking-scouting inputs;
- Projection, future aging/development, playing time/role, defense, WAR/value, or final ranking.

The 90-day future target currently uses complete future player-game evidence. The contract's exact **200-PA player-aggregate diagnostic cap is not yet applied** because the certified backbone is player-game aggregate. Do not invent within-game PA order to force exactly 200; use a certified complete-game cap policy or true PA-grain target surface first. This does not affect the event-likelihood scoring above, which intentionally uses all eligible future events in the horizon.

## Recommended next batch

**Do not add richer features yet.**

1. Extend the existing baseline-validation gate to **independent chronological cutoffs/seasons**, beginning with later certified 2022/2023 surfaces and additional in-season cutoffs where the 90-day target remains observable.
2. Compare a small predeclared set of simple predictor windows / EB prior strengths inside chronology rather than tuning on the 2021-08-01 result alone.
3. Add a clean **translation ablation** (candidate MLB translation vs simpler/no-translation observation treatment) so predictive value of the translation itself is measured rather than assumed.
4. Require stability in proper scores **and** acceptable calibration across years, levels, evidence bands, and promotion/demotion classes before freezing Baseline 1.
5. Only after that baseline is frozen should Baseline 2 or richer process/tracking/scouting evidence be tested.

## Useful workflows / scripts

Manual live/reuse workflows:

- `.github/workflows/current-talent-historical-milb-one-level.yml`
- `.github/workflows/current-talent-historical-mlb-season.yml`
- `.github/workflows/current-talent-validation-snapshot-one-level.yml`
- `.github/workflows/current-talent-validation-snapshot-multilevel.yml`
- `.github/workflows/current-talent-translation-support.yml`
- `.github/workflows/current-talent-age-coverage.yml`
- `.github/workflows/current-talent-baseline-validation.yml`

Key materializers / audits:

- `scripts/materialize_current_talent_historical_milb_game_evidence.py`
- `scripts/materialize_current_talent_historical_mlb_game_evidence.py`
- `scripts/materialize_current_talent_validation_snapshot.py`
- `scripts/materialize_current_talent_validation_snapshot_multilevel.py`
- `scripts/materialize_current_talent_translation_support.py`
- `scripts/audit_current_talent_age_coverage.py`
- `scripts/materialize_current_talent_baseline_validation.py`

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-baseline-checkpoint.md`.
4. Inspect current `source-certification-poc` head before editing.
5. Continue with **rolling-origin / multi-cutoff Baseline 0 vs Baseline 1 validation plus a translation ablation**. Do not re-audit closed source, historical certification, age coverage, translation-support plumbing, or the first 2021 scoring gate unless a regression specifically fails.
