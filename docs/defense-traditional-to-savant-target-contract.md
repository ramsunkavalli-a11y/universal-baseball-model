# Defense traditional-fielding -> Savant target test contract

Last updated: 2026-08-18

Status: **DEVELOPMENT-ONLY PREDICTIVE-SIGNAL TEST — NO DEFENSE v1 PROMOTION.**

## Question

After removing the large year-to-year position effect, do broadly available traditional fielding rates from the prior completed season predict any next-season MLB defensive quality measured by Baseball Savant strongly enough to deserve inclusion in a later Defense v1 challenger?

The preceding reliability screen authorized this target test for all eight screened rates. It did **not** establish defensive skill.

## Inputs

Reuse only the certified 2021–2024 official fielding captures from historical source run `32148467330`.

For each prior season, aggregate all affiliated team/league rows by player × defensive position, excluding P and DH. Determine the player's primary defensive position by most fielding outs, with deterministic position-code tie break.

No 2025 input or target may be accessed.

## Target seasons

Use the next-season Savant MLB leaderboards for:

- 2022 targets from 2021 fielding inputs;
- 2023 targets from 2022 fielding inputs;
- 2024 targets from 2023 fielding inputs.

Use SportsDataverse `0.0.75` only as a transport/parser for the public Savant leaderboards.

## General range target

Target: Savant OAA leaderboard `diff_success_rate_formatted`, a rate-style actual-minus-estimated success measure rather than total OAA.

General prior-year features and expected directions:

- `fielding_pct`: positive;
- `range_factor_per_9`: positive;
- `errors_per_9`: negative;
- `throwing_errors_per_9`: negative;
- `double_plays_per_9`: positive.

Eligibility:

- prior primary position is one of 1B, 2B, 3B, SS, LF, CF, RF;
- at least 300 prior-season fielding outs;
- for `fielding_pct`, at least 100 prior-season chances;
- next-season Savant OAA row exists;
- Savant `primary_pos_formatted` exactly matches the prior primary position;
- target value is finite.

To prevent position from masquerading as skill, standardize both the prior feature and target within position **inside each fold** before pooled correlation.

A general feature is `savant_target_support = true` only if:

1. at least 100 eligible player pairs exist in each of the three folds;
2. signed Spearman correlation is at least `+0.05` in the expected direction in at least two of three folds; and
3. pooled signed Spearman is at least `+0.08`.

No threshold may be changed after target access.

## Catcher throwing target

Prior feature: `caught_stealing_pct`.

Target: Savant catcher-throwing leaderboard `cs_aa_per_throw`.

Expected direction: positive.

Eligibility:

- prior catcher fielding outs >= 300;
- prior steal attempts (`caughtStealing + stolenBases`) >= 10;
- target `sb_attempts >= 10`;
- finite target.

Catcher target support requires:

1. at least 30 eligible catchers in each fold;
2. Spearman >= `+0.05` in at least two folds; and
3. pooled Spearman >= `+0.10`.

## Catcher blocking target

Prior feature: `passed_balls_per_9`.

Target: Savant catcher-blocking leaderboard `blocks_above_average_per_game`.

Expected direction: **negative** (more prior passed balls should predict worse future blocking).

Eligibility:

- prior catcher fielding outs >= 300;
- target `pitches >= 500`;
- finite target.

Use the same catcher support thresholds after multiplying the observed correlation by `-1` for the expected direction.

## Catcher interference

`catcher_interference_per_9` passed the reliability screen but has no direct Savant defensive target in this source set. It is therefore recorded as `direct_target_available = false` and cannot earn Defense-v1 support from this gate.

## Interpretation

Passing means only that a traditional fielding rate carries stable forward signal into a higher-quality next-season MLB defensive target. It authorizes that feature for a later Defense v1 challenger design.

Failing closes that feature for the first Defense-v1 traditional-stat challenger; do not rescue it by changing thresholds, targets, or folds.

## Boundaries

- no regression/model coefficients are fit;
- no feature weights are selected;
- no 2025 data are accessed;
- no Tier-C fallback is frozen;
- tracked range/framing components remain separate;
- no Defense v1 production projection or WAR/value is authorized.
