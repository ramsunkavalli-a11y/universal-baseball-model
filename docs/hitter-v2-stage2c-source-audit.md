# Hitter v2 Stage 2c contact-shape source audit

Status: **COMPLETE WITHOUT OFFENSIVE TARGET ACCESS OR CANDIDATE SCORING**  
Date: 2026-08-24  
Generated evidence: `reports/generated/hitter-v2-stage2c-shape-stability/report.json`  
Generated report SHA-256: `c6b358a98483b39588232107ebf72df53b7cf7f125183f9935cac6215faafd44`

## Scientific conclusion

The source supports a narrowly shrunk contact-shape experiment, not another
ten-bin outcome adjustment. Outfield-fly frequency and pulled-outfield-fly
frequency are noisy in small samples but become meaningfully persistent with
evidence. Ground-ball tendency and opposite-field share within ground balls
are also persistent, but are a different mechanism and must not be pooled with
the power hypothesis.

No offensive outcome, forecast candidate, tracking field, or protected 2026
record was opened by this audit.

## Exact semantics

- Trajectory is Gameday `hitData.bb_type`, mapped to `IFFB`, `OFFB`, `LD`, or
  `GB`.
- Direction uses the Petti/pybaseball transform of `hc_x` and `hc_y`. Center is
  the inclusive interval from -15 through +15 degrees.
- Pull and opposite are batter-relative, using the event's batting side.
- Missing/invalid coordinates or a batting side other than `L`/`R` fail closed
  to null direction.
- MLB and MiLB pass through the same classifier code. That establishes a common
  implementation, but does **not** prove that the upstream raw coordinate and
  trajectory systems have identical measurement semantics.
- The player-season artifact does not retain batting side. Switch-hitter
  side-specific shape cannot be recovered from it and is explicitly deferred.

The audited input is the frozen 2021-2024 ten-bin player-season surface:
2,328,735 events, SHA-256
`ff963a63d2651f917f0ada23c12e46380a1cce001655d8df24249f90bc5225b0`.

## Observed stability

Across all same-level adjacent-season pairs, unfiltered player correlations are
modest because the population includes small samples and every supported
affiliated level. The exact pulled-fly components were:

| Component | Pairs | Pearson | Spearman |
|---|---:|---:|---:|
| `OFFB / contact` | 9,031 | 0.187 | 0.297 |
| `pulled OFFB / OFFB` | 8,683 | 0.182 | 0.258 |
| `GB / contact` | 9,031 | 0.267 | 0.365 |
| `opposite GB / GB` | 8,896 | 0.271 | 0.321 |

Evidence materially changes the interpretation:

| Component | Minimum evidence | Pairs | Pearson | Spearman |
|---|---:|---:|---:|---:|
| `OFFB / contact` | 100-199 contacts | 1,591 | 0.497 | 0.473 |
| `OFFB / contact` | 200+ contacts | 956 | 0.652 | 0.635 |
| `pulled OFFB / OFFB` | 50-99 OFFB | 983 | 0.519 | 0.491 |
| `pulled OFFB / OFFB` | 100-199 OFFB | 171 | 0.546 | 0.501 |
| `opposite GB / GB` | 50-99 GB | 1,488 | 0.566 | 0.538 |
| `opposite GB / GB` | 100-199 GB | 680 | 0.576 | 0.569 |

The `pulled OFFB / OFFB` 200+ band has too few adjacent-season pairs to report
as a stable subgroup. This is a warning against hard thresholds: the production
feature must shrink smoothly with opportunity count.

## Level transport

Primary-level transitions retain signal, but means can shift. For example,
`pulled OFFB / OFFB` Pearson correlations were 0.493 for MLB-to-MLB, 0.355 for
AAA-to-AAA, 0.443 for AAA-to-MLB, and 0.573 for AA-to-AAA. Rookie-to-A was only
0.281 and its mean fell from 0.268 to 0.224. Therefore raw universal shares
cannot be treated as exchangeable. Features must be centered by historical
league-season-level and shrunk before transport; lower-level results require
explicit subgroup guardrails.

## Plan changes

This audit changes the next design in four ways:

1. model `OFFB / contact` and `pulled OFFB / OFFB` as separate nested skills;
2. target only future HR and extra-base-hit conditional nodes with the power
   increment, rather than all contact outcomes;
3. keep `GB / contact` and `opposite GB / GB` in a separate ground-ball
   challenger that cannot rescue a failed power candidate; and
4. require smooth evidence shrinkage and exact outcome-only fallback.

Switch-hitter side splits, raw-source cross-system calibration, finer spray
angles, park geometry, tracking, and bat-speed/exit-velocity information are
deferred. None is needed for the universal PBP fallback.
