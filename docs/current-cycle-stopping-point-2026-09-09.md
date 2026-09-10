# Current cycle stopping point — 2026-09-09

Status: clean handoff; private preview works, publication remains blocked.

## What is now in place

- One playable local explorer for 8,393 rights-universe players, guarded by 21 model
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

Latest full suite: 1,424 passed. Four older research-contract tests fail because their
hash-bound generated artifacts are intentionally absent from this checkout; no new
failure is present. The private build passes all 21 structural model-law checks.

Protected partial-2026 outcomes remain closed. The next clean statistical stopping
gate is a frozen pitcher environment/role candidate or a later complete historical
cohort—not more tuning against the already inspected cohort-stability comparison.
