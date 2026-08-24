# Hitter v2 hit-distance source audit

Status: **SOURCE-ONLY AUDIT; NO CANDIDATE FIT OR SCORE**  
Date: 2026-08-24  
Machine record: `docs/hitter-v2-distance-source-result.json`

## Scientific conclusion

The repository does contain `hit_distance_sc`, but it is not a universal PBP
feature. It behaves as a tracking/enriched-feed field and must remain outside
the guaranteed PBP-only forecast.

Across 113 already-disclosed 2021-2024 affiliated PBP files, the audit found
distance on 360,929 of 1,954,502 classified batted-ball PAs (18.47%). Of those
distance-bearing PAs, 360,698 (99.936%) also had exit velocity. Coverage was
zero in every High-A season and essentially zero in AA; it rose to 98.39% in
2023 AAA and 96.97% in 2024 AAA, while Single-A remained near 26-28%. This is
capability-dependent tracking coverage, not an ordinary-scorekeeping fallback.

Therefore:

- distance cannot enter the universal Stage 2c PBP candidate;
- distance availability cannot be a talent predictor;
- missing distance cannot be imputed to zero;
- a later distance increment must be evaluated only after a PBP-only model is
  frozen, on identical overlap players and outcomes;
- removing distance/tracking must return the exact PBP prediction; and
- the increment must shrink smoothly to zero with evidence.

## Coverage by season and affiliated level

| season | level | classified BIP PA | distance PA | coverage |
|---:|---|---:|---:|---:|
| 2021 | AAA | 94,883 | 0 | 0.00% |
| 2021 | AA | 82,966 | 0 | 0.00% |
| 2021 | High-A | 83,316 | 0 | 0.00% |
| 2021 | Single-A | 83,415 | 22,701 | 27.21% |
| 2021 | Rookie/complex | 100,308 | 359 | 0.36% |
| 2022 | AAA | 112,293 | 41,244 | 36.73% |
| 2022 | AA | 100,465 | 0 | 0.00% |
| 2022 | High-A | 93,096 | 0 | 0.00% |
| 2022 | Single-A | 92,685 | 24,543 | 26.48% |
| 2022 | Rookie/complex | 106,324 | 481 | 0.45% |
| 2023 | AAA | 111,940 | 110,141 | 98.39% |
| 2023 | AA | 98,992 | 0 | 0.00% |
| 2023 | High-A | 93,530 | 0 | 0.00% |
| 2023 | Single-A | 92,899 | 24,847 | 26.75% |
| 2023 | Rookie/complex | 103,694 | 372 | 0.36% |
| 2024 | AAA | 112,874 | 109,450 | 96.97% |
| 2024 | AA | 100,641 | 47 | 0.05% |
| 2024 | High-A | 94,126 | 0 | 0.00% |
| 2024 | Single-A | 93,154 | 26,021 | 27.93% |
| 2024 | Rookie/complex | 102,901 | 723 | 0.70% |

The non-monotone level pattern is an additional warning: availability reflects
parks/leagues/source capability, not player quality or a simple level rule.

## Event semantics and integrity findings

The raw files contain 19,075,375 rows but only 3,126,822 canonical PAs. In
292,649 PAs, a distance value repeats on more than one raw record. The audit
therefore collapses to `(game_pk, at_bat_number)` before measuring coverage.
Only 15 PAs contain conflicting distance values, and no PA contains conflicting
batted-ball-type labels. The generated tables retain these conflicts for later
adjudication. No observed distance was outside the provisional 0-600 foot
plausibility screen; the raw observed range was 0-543 feet.

Distance is recorded across ground balls, line drives, fly balls, popups, and
bunts. It is not merely an old-style estimated fly-ball-distance field. A later
candidate must freeze an eligible contact definition before evaluation. The
historical public minor-league distance work that excluded non-HR hits because
their recorded location could reflect the fielder should be treated as a
semantic warning, not copied blindly onto this tracking-like field.

## Reuse decision

`hit_distance_sc` is accepted for a future **optional tracking residual source
audit**, not for Stage 2c's universal PBP base. Before modeling it, certify:

1. whether the field is measured/estimated identically across the underlying
   official and Savant-derived paths;
2. venue and season calibration;
3. the air-contact eligibility rule;
4. player-event evidence counts and reliability;
5. source-vintage drift; and
6. exact PBP fallback and identical-overlap evaluation invariants.

No offensive target, evaluation membership, player name, or protected 2026
outcome was loaded by this audit.

## Reproduction

```text
.venv\Scripts\python.exe scripts/audit_hitter_v2_distance_source.py
```

Generated report SHA-256:
`42f21f1f93ec85ce723e08d5cad07ed4c383be1187f7b0f5869e413fce40b5f4`.

