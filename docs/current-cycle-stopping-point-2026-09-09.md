# Current cycle stopping point — 2026-09-09

Status: clean handoff; private preview works, publication remains blocked.

## What is now in place

- One playable local explorer for 8,393 rights-universe players, guarded by 18 model
  identity checks.
- A nested pre-MLB career model: arrival, meaningful given arrival, and established
  given meaningful. Probabilities are ordered by construction.
- Workload-only prospect P10/P50/P90 outcomes for all 6,719 pre-MLB paths. Their means
  exactly match current point WAR and do not alter value.
- Clear player detail for skill rate, expected workload, batting/running/defense/
  position components, pitcher RAA, and the source-limited workload range.
- Current contract/control economics using the downloaded FanGraphs depth-chart and
  payroll workbooks as private reference inputs, with bounded reviews left explicit.

## Accepted or retained

- Hitter conditional workload distribution is usable as a labeled empirical reference;
  it is not historically confirmed.
- The translated hitter and pitcher component baselines remain.
- Hitter component regression remains 1,200 PA: a 400-PA challenger improved point
  scores but missed the predeclared bootstrap gate.
- Pitcher role probabilities remain; broad suppression and hard role caps were not
  supported.
- The private pitcher age/hand adjustment remains provisional, with its weak evidence
  and left-handed warning preserved.

## Rejected or blocked

- No catcher preference, position quota, manual prospect floor, or outside player FV.
- Hitter age-for-level and batting-side component bonuses reversed on 2025.
- Separate/pooled pitcher extra-base-hit components worsened proper scores.
- Simple pitcher workload recency weighting and always pooling roles did not jointly
  improve accuracy and coverage.
- Component-plus-workload prospect ranges are research-only, not calibrated intervals.
- Platoon is source-ready but waits for the certified sidecar to be rematerialized.
  Lineup slot and universal times-through-order are not yet certified.

## Main finding to carry forward

Pitcher workload is the most important open modeling issue. In a descriptive cohort
comparison, nominal 80% workload coverage was only 66.3%; this was not a chronology-
safe forecast test. From 2015-2019 to 2021-2024, active MLB pitchers increased 13.2%,
mean/median BF per pitcher fell about 13%, and P90 BF fell 16.3%. More pitchers recording
a start partly reflects openers and bullpen games, not more traditional starters.

The next model should forecast the league-wide pitcher usage environment separately,
then place a player within it using rotation-start share, BF per start, relief/bulk
usage and role-transition evidence. Never raise workload simply to create familiar
prospect values.

## Verification and known limitation

Latest full suite: 1,408 passed. Four older research-contract tests fail because their
hash-bound generated artifacts are intentionally absent from this checkout; no new
failure is present. The private build passes all 18 structural model-law checks.

Protected partial-2026 outcomes remain closed. The next clean statistical stopping
gate is a frozen pitcher environment/role candidate or a later complete historical
cohort—not more tuning against the already inspected cohort-stability comparison.
