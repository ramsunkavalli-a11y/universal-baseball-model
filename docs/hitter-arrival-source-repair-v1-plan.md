# Historical arrival source repair v1

Fixed before fitting, 2026-09-23. Research only; do not alter the original 2026
forecast, explorer, previous experiment inputs, or previously frozen manifests.

## Why

The player-error audit found incomplete pre-2009 debut coverage, October 15
40-man flags in year-end forecasts, and Mexican League experience pooled with
affiliated Triple-A. Fix source semantics consistently, not individual misses.
These are valid data concerns even if predictive improvement is not established.

## Sources and chronology

- Reconstruct MLB debut evidence from explicit completed-season MLB player
  censuses, 1960–2025, requesting only identity and debut date. Verify 1960 is
  before the inferred birth year of every panel player. Reject missing dates,
  conflicting dates and dates after the requested census season. Cross-check
  existing 2004–2009 and 2009–2025 inventories. Absence is meaningful only after
  the complete census is collected. Features use debut dates <= each origin.
- Recollect all 30 MLB clubs' 40-man lists at December 31 for every study origin
  (2009–2019, 2021–2024). Use endpoint membership only, never returned status,
  jersey, position or parent-team metadata. Audit team counts, empty rosters,
  duplicate identities and cross-team conflicts. Retrospective dated endpoints
  are not contemporaneously archived snapshots; preserve this limitation.
- From already captured season/team batting splits, identify league 125
  (Mexican League) at that season. Join to canonical stint records, verify PA
  agreement, retain source-coverage flags. Add current and two prior calendar
  years' Mexican League PA shares and coverage. Do not remove players, reinterpret
  missing evidence as affiliated play, or rewrite existing level translations.
- Use no 2026 outcomes or endpoints. Preserve all original targets and rows.

## Fixed experiment

Use the existing R LightGBM recipe, identity weights, features, seed and
chronological eligibility without retuning. Four arms:

- R: archived original inputs/predictions.
- C: corrected debut/cohort metadata plus six league-context features; original
  roster flags. This bundles two source repairs and cannot separate their gains.
- T: year-end roster flags only; original training cohort metadata.
- F: both source families, primary candidate.

Six annual origins: 2017, 2018, 2021–2024. Three-year arrival and regular-workload
origins: 2021 and 2022. Thirty new fits, plus two future-mutation replays and one
unmodified R replay. Training targets must mature by the query cutoff; exclude
target windows spanning the canceled 2020 season. Do not invent a 2020 MiLB year.

Report all arms on identical keys and **corrected** cohort labels, including the
archived predictions. Publish cohort membership changes separately. Primary:
never-debuted minor leaguers; also all players, returners, levels, age, current PA,
and Mexican League exposure. Include player examples as illustrations only.

Use equal-origin Brier/log loss, annual expected/observed counts, paired
player-cluster intervals and annual directions. For a promising next-year
candidate require both pooled intervals below zero versus R, improvement in
at least 4/6 origins on each score, no >10% relative harm in an annual/stage
slice with >=200 rows and >=30 positives, and both scores better than the
matched earlier ensemble and accepted C2 references. The primary decision is F;
do not promote a favorable diagnostic arm after F fails. Report AE and B2 as
additional references. Three-year tests are exploratory: only two overlapping
origins, not independent confirmation. No whole-value claim from probabilities.

Freeze code, source hashes, repaired panel and feature contract before any fit.
Verify unchanged forecasts. Preserve predictions, score reports and manifests
in a compact versioned research package. Semantic repairs can be retained for
future rebuilds even when the current forecast replacement fails its gates.
