# Defense catcher-framing reuse POC contract

Last updated: 2026-08-18

Status: **DEVELOPMENT / REUSE FEASIBILITY ONLY — NO PRODUCTION CATCHER VALUE.**

## Question

Can SportsDataverse `0.0.75`'s public catcher-framing implementation be reused as the leading framing Performance candidate for MLB and technically executed on the already-established tracked MiLB Statcast tiers?

Blocking and throwing are explicitly outside this gate.

## Frozen upstream implementation

- package: `sportsdataverse==0.0.75`
- upstream commit: `1dafadb38c5240d8e29a0f818efbabe04cd6c417`
- function: `sportsdataverse.mlb.mlb_catcher_framing.mlb_catcher_framing`

The implementation fits a smooth called-strike probability model over public pitch location and scores framing only on shadow-zone takes.

## MLB oracle slice

Use 2024-06-01 through 2024-06-30 regular-season MLB Statcast pitches and compare with the full-season 2024 Savant catcher-framing leaderboard.

This deliberately mirrors the upstream committed offline oracle.

Frozen MLB pass rule:

1. framing output is non-empty;
2. restrict the reusable output to catchers with at least 500 takes;
3. at least 20 catchers match the Savant leaderboard;
4. Pearson correlation between reusable `framing_runs` and Savant `rv_tot` is **>= 0.50**.

Do not lower this floor after observing our result.

## MiLB source window

Use 2024-06-10 through 2024-06-16, regular season, with the already-proven Savant minors transport semantics:

- `minors=true`;
- explicit `season=2024`;
- no server-side level filter;
- client-side AAA classification using official Stats API 2024 Triple-A team abbreviations;
- remaining tracked rows retained separately as the tracked non-AAA tier.

## Required framing fields

Require:

- `description`
- `plate_x`
- `plate_z`
- `sz_top`
- `sz_bot`
- `stand`
- `balls`
- `strikes`
- `fielder_2`

Also report coverage of `delta_run_exp`, although the framing code's count run-value logic must determine its own usable path.

## Frozen MiLB execution/coverage rule

For AAA and tracked non-AAA separately, pass only if:

1. all required fields are present;
2. at least 1,000 called-strike/ball takes are available;
3. at least 10 catchers receive positive take counts in the framing output;
4. framing output values are finite;
5. `fielder_2` is non-null on at least 90% of eligible takes.

This is **not** an accuracy validation because there is no public proprietary MiLB framing leaderboard oracle.

## Interpretation

- MLB pass + MiLB execution pass: framing is a strong reuse candidate for a tracked catcher-defense evidence tier, but projection/shrinkage/chronology must still be developed before production.
- MLB pass + MiLB execution failure: retain MLB framing reuse and treat MiLB framing as coverage-limited.
- MLB failure: do not promote this framing implementation; diagnose implementation/source behavior without lowering the gate.

Regardless of outcome:

- catcher blocking remains separate;
- catcher throwing remains separate;
- universal defense is not authorized;
- Defense v1 projection is not authorized;
- WAR/value is not authorized.
