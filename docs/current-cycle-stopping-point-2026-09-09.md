# Current cycle stopping point — updated 2026-09-10

Status: clean handoff; private preview works, publication remains blocked.

## September 10 continuation

- The playable prospect-arrival model now distinguishes highest level touched from
  workload-weighted primary level. The combined exposure model beat the old core on
  both pooled proper scores without losing either score in any required time-ordered
  fold for hitter and pitcher arrival and meaningful-role outcomes. See
  `docs/prospect-primary-level-exposure-result.md`.
- A primary-level-only replacement was rejected because it made aggregate historical
  accuracy worse. Highest level remains evidence; it no longer stands alone.
- Advancement, stagnation, inactivity gap, and accumulated affiliated history were
  tested together. They improve only pitcher established-role probability under the
  fixed gate; the other five outcome models remain simpler. See
  `docs/prospect-development-path-result.md`.
- A predeclared declining-hazard/exit-risk test selected the existing constant hazard
  for all six hitter/pitcher outcomes on 2019 and did not lose on the completed 2021
  four-year check. Do not add an arbitrary long-horizon decay. The third two-year
  window remains an explicit extrapolation; see
  `docs/prospect-declining-hazard-result.md`.
- Official 2021-2025 home/road results now provide a reproducible minor-league park
  source. A 50-game pooled venue factor improved both MAE and RMSE in 2024 selection
  and untouched 2025 confirmation. This promotes the source only; player rates and
  values remain unchanged until a cutoff-safe player-level forecast test passes.

- The repo plan now includes lessons from comparable GitHub projection systems:
  component-specific reliability must earn its complexity, attrition belongs in the
  score, and downstream WAR matters more than an isolated component gain.
- The complete next-season denominator is implemented and tested. It retains 5,018
  observed non-returners instead of silently removing them from aging evaluation.
- Component-specific pitcher shrinkage failed 2025 stability; keep 800 BF.
- Component-specific hitter shrinkage improved point scores but missed the fixed
  uncertainty gate; keep 1,200 PA.
- Tango pitcher aging beat no aging in the frozen 2025 joint replay. Retain it.
- The generic Marcel hitter age adjustment lost to no aging in the same type of replay.
  No current value changed; no aging is the frozen 2026 challenger.
- Both 2026 aging comparisons are stored as immutable, hash-checked forecasts. Do not
  open partial 2026 results or alter their gates.

Next: after the completed regular season, run the already frozen opportunity and aging
confirmations. Before then, useful model work requires broader historical affiliated
data or a genuinely new cutoff-safe process source; do not mine more 2024–2025
shrinkage combinations.

## What is now in place

- One playable local explorer for 8,393 rights-universe players, guarded by 46 model
  identity checks.
- A nested pre-MLB career model: arrival, meaningful given arrival, and established
  given meaningful. Probabilities are ordered by construction.
- Workload-only prospect P10/P50/P90 outcomes for all 6,719 pre-MLB paths. Their means
  exactly match current point WAR and do not alter value.
- Clear player detail for skill rate, expected workload, batting/running/defense/
  position components, pitcher RAA, and the source-limited workload range.
- Current contract/control economics using the downloaded FanGraphs depth-chart and
  payroll workbooks as private reference inputs, with bounded reviews left explicit.
- A separate dependent career simulation for all 6,719 pre-MLB players. It keeps
  arrival, whole career workload, skill uncertainty, annual noise, control, cost and
  value in the same path and appears only as a research comparison in player detail.

## Accepted or retained

- Hitter conditional workload distribution is usable as a labeled empirical reference;
  it is not historically confirmed.
- The translated hitter and pitcher component baselines remain.
- Hitter component regression remains 1,200 PA: a 400-PA challenger improved point
  scores but missed the predeclared bootstrap gate.
- Pitcher role probabilities remain; broad suppression and hard role caps were not
  supported.
- The private pitcher age/hand adjustment was provisional at this stopping point. It
  was removed on September 10 after the full funnel audit exposed its disproportionate
  current top-end effect relative to its weak validation.

## Rejected or blocked

- No catcher preference, position quota, manual prospect floor, or outside player FV.
- Hitter age-for-level and batting-side component bonuses reversed on 2025.
- Separate/pooled pitcher extra-base-hit components worsened proper scores.
- Simple pitcher workload recency weighting and always pooling roles did not jointly
  improve accuracy and coverage.
- Component-plus-workload prospect ranges are research-only, not calibrated intervals.
- Birth country and its age/hand combinations failed five-fold pitcher development
  scoring. Current height/weight cannot be used in historical tests without dated
  measurements.
- Platoon is source-ready but waits for the certified sidecar to be rematerialized.
  Lineup slot and universal times-through-order are not yet certified.

## Main finding to carry forward

Pitcher projection remains the most important modeling issue, but the valid as-of
conditional workload replay passed: its nominal 80% range covered 81.1%. The deeper
problem is top-end pitcher production before value mapping. The old pre-MLB top 100
already had 99 hitters and one pitcher, so the dependent simulator did not cause the
imbalance. Earlier tests retained role probabilities and 800-BF regression and
rejected simple recency weighting, role pooling and birth-country adjustments.

The next performance challenger should add genuinely new, chronology-safe process or
pitch-quality evidence. Minor-league Statcast is allowed only as a coverage-limited
tier. Its accepted materialization artifact and required upstream workflow artifacts
have expired, so the source chain must be rebuilt first. Never raise workload, change
FV cutoffs or add a manual pitcher bonus to create a familiar ranking.

## Verification and known limitation

Latest full suite: 1,501 passed. Four older research-contract tests fail because their
hash-bound generated artifacts are intentionally absent from this checkout; no new
failure is present. The private build passes all 46 structural, statistical and accounting model-law checks.

The September 10 official-debut correction is also active: 104 hitter and 154 pitcher
historical cohort records were removed, the arrival model was refit without retuning,
and the downstream value/explorer lineage is hash-checked.

Protected partial-2026 outcomes remain closed. The next clean statistical stopping
gate is a frozen pitcher environment/role candidate or a later complete historical
cohort—not more tuning against the already inspected cohort-stability comparison.
