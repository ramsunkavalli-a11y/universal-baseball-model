# Defense v1 catcher source repair contract

Last updated: 2026-08-18

Status: **CATCHER CHANNEL QUARANTINED — SOURCE REPAIR ONLY.**

## Why this repair is authorized

The post-Defense Player Value native-scale audit found that supposed 2022, 2023, and 2024 Savant catcher-throwing target distributions were exactly identical, and matched the subsequently materialized 2025 target distribution. The historical catcher-blocking source likewise returned the same 70-row payload across requested years.

A direct source diagnostic then confirmed that both Savant catcher leaderboards ignore the legacy/generated query forms used by the pinned SportsDataverse wrapper (`year=...`) and the tested camelCase season forms. Those query forms returned byte-identical/canonically identical payloads for 2022-2025.

The current Savant UI uses a different query contract: snake_case `season_start` / `season_end` together with the current leaderboard parameters (`game_type=Regular`, `type=Cat`, `split=no`, etc.). That query shape must itself certify as year-specific before any repaired source is used.

This is a concrete source implementation failure. It authorizes repair of the **catcher target source only**. It does not authorize new model families, new features, threshold changes, or reopening general range.

## Unaffected frozen Defense components

These remain binding and must not be refit or rescored:

- universal general range;
- tracked MLB range increment;
- tracked MiLB range closure;
- tracked framing closure;
- age closure;
- rejected traditional general-defense features.

The 2024 MLB tracking predictor and 2025 general-range confirmation remain valid and frozen.

## Quarantined results

Until this repair completes, do not treat these prior catcher decisions as binding evidence:

- prior catcher-throwing development selection;
- prior catcher-blocking development selection;
- prior catcher-throwing 2025 confirmation result;
- prior catcher-blocking 2025 confirmation result;
- catcher portions of the pre-2025 parameter package.

The files remain historical audit evidence and must not be deleted or overwritten.

## Frozen source repair sequence

### Gate 1 — certify year-specific query semantics

The direct-source diagnostic must show, for **both** catcher throwing and catcher blocking:

1. the repaired query shape returns four distinct canonical payloads for 2022, 2023, 2024, and 2025;
2. each payload reports/contains the requested season in the returned `start_year` / `end_year` fields where those fields are supplied;
3. the source is a CSV player leaderboard, not a team leaderboard or HTML fallback;
4. the query requests regular-season catcher rows and does not silently pool years.

If this gate fails, stop. Find another year-specific public source before touching catcher development.

### Gate 2 — materialize repaired 2022-2024 development targets only

After Gate 1 passes, persist immutable raw CSV/Parquet evidence for 2022, 2023, and 2024 from the certified query shape.

Use the same target definitions already frozen in `docs/defense-v1-development-contract.md`:

- throwing target: `cs_aa_per_throw`, target `sb_attempts >= 10`, finite value, standardized within target year;
- blocking target: `blocks_above_average_per_game`, target `pitches >= 500`, finite value, standardized within target year.

No 2025 repaired target may be materialized in this development-source workflow.

### Gate 3 — rerun the original catcher development gate exactly

Use the same certified historical fielding predictor evidence and the exact original candidate/search space from `docs/defense-v1-development-contract.md`.

Throwing candidates:

- C1 = current-season `caught_stealing_pct_z` single-feature unpenalized linear model;
- C2 = same feature with the frozen two-season recency/exposure construction and 0.5 prior-season weight.

Blocking candidates:

- C1 = current-season `passed_balls_per_9_z` single-feature unpenalized linear model;
- C2 = same feature with the frozen two-season recency/exposure construction and 0.5 prior-season weight.

Eligibility, normalization, grouped CV, and selection rules are unchanged:

- leave-one-target-year-out across 2022/2023/2024;
- at least 30 scored catchers in each fold;
- MSE below B0 in at least 2 of 3 folds;
- pooled OOF MSE improvement >=2.0%;
- no fold >7.5% worse than B0;
- pooled Spearman >=0.10;
- all metrics finite;
- among eligible candidates choose lower pooled OOF MSE; tie -> C1.

This is a deterministic rerun of the originally preregistered search, not a new challenger search. If neither family passes for a component, that component freezes at neutral B0.

### Gate 4 — repaired pre-2025 catcher parameter freeze

For each catcher component that survives repaired development:

- refit the selected frozen form on all authorized repaired 2022-2024 target responses using 2021-2023 predictor evidence;
- persist coefficients, input normalization, training rows, repaired target-source hashes, package versions, and deterministic reproduction checks.

Do not access the repaired 2025 target during this freeze.

A component that fails repaired development receives no fitted production parameter and remains neutral B0.

### Gate 5 — materialize repaired 2025 catcher targets separately

Only after Gate 4 is frozen, materialize 2025 catcher throwing/blocking targets from the exact same certified year-specific query semantics.

Persist raw source, canonical target rows, moments, hashes, query parameters, and source provenance.

No fitting or scoring in the source workflow.

### Gate 6 — one-shot repaired catcher confirmation

Use the original catcher confirmation rules already frozen in `docs/defense-v1-2025-confirmation-contract.md`:

- each retained catcher component vs neutral B0 on identical eligible coverage;
- fewer than 30 scored catchers -> insufficient evidence;
- candidate MSE must be below B0;
- candidate MAE may be at most 7.5% worse than B0;
- Spearman must be >=0.10;
- predictions/metrics must be finite.

No refit, reselection, recalibration, threshold movement, or rescue after repaired 2025 outcomes are opened.

## Source query rule

The repaired source must use the query semantics certified by Gate 1. The expected current-UI shape is:

- `game_type=Regular`;
- `season_start=<year>`;
- `season_end=<year>`;
- `split=no`;
- `type=Cat`;
- `team=`;
- `with_team_only=1`;
- an all-player minimum setting that preserves the frozen downstream target thresholds;
- catcher throwing additionally uses `target_base=All`;
- CSV output enabled.

Do not use the pinned SportsDataverse catcher leaderboard wrapper unless its emitted request is independently shown to match the certified year-specific source behavior.

## Player Value boundary during repair

- General-range run-conversion research may continue using the valid frozen general Defense path.
- Catcher run conversion is blocked until the repaired catcher confirmation is complete.
- Positional-adjustment research may continue because it is separate from catcher skill.
- WAR/value aggregation remains unauthorized.

## Binding boundaries

- Do not alter or rerun general range.
- Do not add catcher features or model families.
- Do not change the original development or confirmation thresholds.
- Do not use repaired 2025 targets during development/refit.
- Do not use prior invalid catcher confirmation residuals for tuning.
- Preserve all prior invalid-source artifacts as audit evidence.
- Do not calculate WAR during this repair.
