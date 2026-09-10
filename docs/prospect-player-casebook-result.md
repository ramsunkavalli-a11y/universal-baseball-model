# Prospect player-by-player casebook result

**Status:** first casebook complete; no formula promoted

The generated top-50 audit now contains 72 disagreement rows. Each row shows the raw
evidence, model adjustment, opportunity, workload, WAR, value, main reason and issue
priority. Public rank and FV remain diagnostics only.

## What repeated across players

| Priority | Players | Finding |
|---|---:|---|
| P0 pitcher translation | 10 | Strong public-list pitchers are pushed down by translated run rate. |
| P0 position persistence | 11 | Every case is a shortstop whose position value offsets weak modeled offense. |
| P1 proximity versus upside | 20 | Advanced-level workload and arrival odds drive the model-only ranking. |
| P1 sparse evidence | 12 | Young or newly drafted players have little performance evidence. |
| P2 cumulative review | 19 | No single component explains the difference. |

The position issue is not current catcher crowding. The 11 flagged players are all
shortstops. Standard position runs contribute about 0.6 to 1.2 expected WAR for these
players, often 30% or more of their projection, while their modeled batting is below
average. Do not apply a shortstop quota or penalty; test player-level position
persistence.

## Pitcher findings

The ten current cases show the same mechanism. Level translation plus an 800-BF prior
substantially lowers raw strikeout rates and raises raw home-run rates. Examples include
Thomas White, Ryan Sloan, Jarlin Susana, Christian Zazueta and Gage Wood. This is not a
source-count error: the casebook exposes the underlying BF, strikeouts, walks and home
runs.

A historical dominance-tail diagnostic then evaluated only pitchers who reached MLB,
keeping arrival separate from conditional skill. In the prior-input top K-BB quartile,
the model was too pessimistic by 4.27 runs per 800 BF in 2024 and 3.97 in 2025. A more
restrictive dominant/low-HR group was unstable: five 2024 players were projected too
favorably, while 22 2025 players were projected too poorly.

Two simple corrections were rejected:

- Preserving more raw K-BB failed both 2024 component probability scores, so the
  selected adjustment was zero.
- Reducing the HR level translation to 25% improved 2025 log loss but worsened Brier.
  It failed the two-score confirmation gate and remains at full strength.

The result supports a real pitcher-tail problem but does not authorize a simple rate
boost. The next pitcher step is the already-frozen linked performance-path confirmation
after final 2026 outcomes, or a new universally available skill input. Until then,
pitcher prospect ranks remain provisional.

## Roadmap from the casebook

1. Keep pitcher ranks visibly provisional; do not manufacture a hitter/pitcher quota.
2. Test player-level shortstop retention and defensive evidence, not a position haircut.
3. Run a current-value sensitivity using the already-supported official Rule 4 hitter
   arrival evidence; never use it as a WAR bonus or FV floor.
4. Test whether advanced-level workload crowds out lower-level upside on historical
   cohorts.
5. Repeat the same casebook after every promoted structural change.

Machine-readable diagnostics are in
`docs/pitcher-dominance-tail-audit-result.json`,
`docs/pitcher-dominance-residual-audit-result.json`, and
`docs/pitcher-hr-translation-strength-audit-result.json`.

## Draft sensitivity decision

The current build now evaluates official draft pedigree alongside every normal arrival
candidate. For hitters it improves both log loss and Brier against the current
level-exposure model in all three historical folds. A temporary current-value
sensitivity nevertheless exposed an unsafe interaction: the constant conversion from
two-year odds to six-year odds pushed several drafted players near 100% arrival and
systematically lowered prominent international players whose entry path is absent from
the Rule 4 source. Top-50 overlap remained 10.

That direct production change was rejected and the prior playable values were restored.
The next version must model drafted and international entry paths safely and validate
the six-year horizon; historical two-year improvement alone is insufficient.
