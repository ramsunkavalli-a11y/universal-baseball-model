# Player Value v1 — Defense native source-semantics audit contract

Last updated: 2026-08-19

Status: **PRE-2025 SOURCE-SEMANTICS DIAGNOSTIC ONLY; NO RUN CONVERSION SELECTED.**

This audit establishes the raw public source semantics needed before Player Value v1 can
convert frozen standardized Defense skill predictions into native seasonal value. It is not a
model-development gate and may not refit or rescore Defense skill.

## Scope

Use only 2022-2024 historical target seasons. Do not query or inspect 2025.

Audit the four frozen Defense target channels:

1. general range — Savant Outs Above Average leaderboard target
   `diff_success_rate_formatted` / Success Rate Added;
2. catcher throwing — repaired Savant catcher-throwing target `cs_aa_per_throw`;
3. catcher blocking — repaired Savant catcher-blocking target
   `blocks_above_average_per_game`;
4. catcher framing — repaired Savant catcher-framing target
   `1000 * rv_tot / pitches`.

## Source transport

- General range must reuse the same pinned `sportsdataverse==0.0.75`
  `mlb_statcast_leaderboard_outs_above_average(year=...)` transport used by frozen
  pre-2025 Defense development.
- Throwing/blocking must use the repaired direct Baseball Savant current-UI CSV semantics with
  `season_start` / `season_end` and the frozen minimum source filters.
- Framing must use the repaired direct Baseball Savant framing-specific CSV semantics with
  `seasonStart` / `seasonEnd`.
- No 2025 request is authorized.

## Required diagnostics

For each component and year, persist:

- full returned source-column inventory;
- source and eligible row counts;
- exact raw target mean, population SD, median, min, max, and the raw mean divided by SD;
- native exposure columns used by the frozen target source;
- source-query provenance.

Additionally test only identities that are directly supported by returned columns, without
inventing missing fields:

### General range

Record candidate source columns related to success rate, opportunities, outs above average,
runs, and fielding value.

If an OAA-total column and an opportunity-count column are both present, test whether
Success Rate Added equals either:

- `100 * OAA / opportunities`; or
- `OAA / opportunities`.

Report absolute-error diagnostics for both identities. Do not select a run conversion from this
audit.

If a public run-valued field is present, record its name and descriptive scale but do not fit a
calibration.

### Catcher throwing

If a total caught-stealing-above-average field is present, test whether:

`total_cs_aa = cs_aa_per_throw * sb_attempts`.

Record any public run-valued fields but do not infer a conversion if none is returned.

### Catcher blocking

If total blocks-above-average and catcher-games fields are present, test whether:

`total_blocks_aa = blocks_above_average_per_game * games`.

Record any public run-valued fields but do not infer a conversion if none is returned.

### Catcher framing

Verify the frozen raw target identity:

`target_raw = 1000 * rv_tot / pitches`.

Because `rv_tot` is already a run-valued seasonal total, explicitly record that this component
has a direct native run-total field in the certified source.

## Interpretation boundaries

- This audit may identify algebraic/native-unit identities only.
- It may not select a future standardization mean or SD.
- It may not choose a component opportunity forecast.
- It may not fit a z-to-native calibration.
- It may not use 2025 confirmation residuals.
- It may not change any Defense model, threshold, family, or eligibility rule.
- It may not calculate positional adjustment, replacement level, runs per win, WAR, or final
  Player Value.

Any later conversion selection must be separately predeclared after this audit is read.
