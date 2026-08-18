# Position / role v1 — untouched 2025 confirmation contract

Last updated: 2026-08-18

Status: **FROZEN BEFORE 2025 POSITION-SOURCE ACCESS.**

Development winner: `primary_share_thresholded_transition_mean_v1` from `docs/position-role-selective-transition-result.json`.

## Confirmation question

On untouched 2025 position-role outcomes, does the frozen selective transition smoother beat raw 2024 role-profile carry-forward on the same players?

This is a one-shot confirmation. No rescue tuning, threshold movement, parameter refit, candidate substitution, or re-selection is allowed after 2025 position-role data is opened.

## Frozen target

Observed 2025 batting-role profile across:

- C
- 1B
- 2B
- 3B
- SS
- LF
- CF
- RF
- DH

Use the exact deterministic role-profile construction already frozen in `src/universal_baseball/position_role_profile.py`:

1. aggregate across teams/leagues within player-season;
2. use games started when total starts are positive;
3. otherwise use games played as the explicit fallback;
4. exclude pitcher usage from the batting-role channel.

## Frozen source boundary

2025 source materialization must be its own workflow and artifact.

It may query only completed 2025 regular-season official Stats API `fielding` and same-league `hitting` surfaces for the frozen 16-league MLB/affiliated map.

The source workflow must:

- preserve raw response bytes;
- preserve response hashes and pagination evidence;
- persist canonical 2025 fielding usage;
- persist coverage diagnostics;
- contain no model parameters and no scorer.

The confirmation scorer may run only after the source artifact exists successfully.

## Frozen confirmation parameters

Before 2025 source is opened, persist a separate immutable parameter artifact using only the certified 2021-2024 role-profile evidence.

Fit the primary-position destination means on all three development transitions:

- 2021 -> 2022
- 2022 -> 2023
- 2023 -> 2024

For each current primary position `p`, persist the mean next-season nine-position role vector `mu_p` and the training transition count.

Also persist:

- primary-share threshold = `0.65`;
- exact position ordering;
- exact candidate formula;
- source artifact/run identifiers and hashes;
- a canonical parameter hash.

No 2025 source may be available to this parameter-freeze workflow.

## Baseline 0

For every player with both a 2024 and 2025 batting-role profile:

`baseline = 2024 role profile`

## Frozen candidate

Let:

- `x` = 2024 role profile;
- `s` = 2024 primary-position share;
- `mu_p` = frozen pre-2025 destination mean for the player's 2024 primary position.

Predict:

- if `s < 0.65`: `candidate = x`;
- if `s >= 0.65`: `candidate = s * x + (1 - s) * mu_p`.

The scorer must reconstruct these predictions from the persisted parameter artifact. It may not call a fitting function.

## Frozen confirmation population

Score every player who has:

- a valid frozen 2024 batting-role profile; and
- a valid observed 2025 batting-role profile.

No playing-time threshold, prospect status, organization, level, or MLB-only filter is allowed.

## Frozen metrics

Primary metric:

- mean total-variation distance over the full nine-position profile.

Secondary metric:

- mean summed squared error over the full nine-position profile.

Diagnostics only:

- scored player count;
- smoothing-active player count/rate;
- baseline and candidate exact primary-position match rates;
- results by 2024 primary position and primary-share band.

## Binding confirmation rule

The candidate confirms only if **both** are true on the single 2024 -> 2025 confirmation population:

1. candidate mean total-variation distance is strictly lower than Baseline 0;
2. candidate mean summed squared error is strictly lower than Baseline 0.

No diagnostic can rescue a failed primary or secondary metric.

## Binding decision

If confirmed:

- freeze Position / Role v1 as `primary_share_thresholded_transition_mean_v1`;
- future production projections may refit the same destination-mean estimator using all eligible completed historical transitions available before the projection date, while keeping the 0.65 threshold and formula frozen;
- proceed to the next value-layer dependency.

If not confirmed:

- freeze Position / Role v1 as raw role-profile carry-forward;
- close selective transition smoothing for v1;
- do not retune against 2025.

In either case:

- Playing Time v1 is unchanged;
- batting Projection v1 is unchanged;
- no team allocator is authorized;
- no defensive-quality model is authorized by this gate.
