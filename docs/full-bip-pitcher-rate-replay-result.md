# Full BIP pitcher-rate replay result

**Status:** rejected for production

## Question

The BIP contact-only candidate passed its active contact comparison. This replay asks
the stricter question: does the same frozen `0.7883` contact weight improve the
complete pitcher rate after strikeouts, walks, hit batters and home runs are included?

The test uses the active three-season, level-translated pitcher profile. Future
non-contact components and BIP outcomes are both translated to the MLB-neutral scale
using only information available at the forecast cutoff. The contact weight was not
refit during this replay.

## Result

| Test | Players | Baseline MAE | Candidate MAE | Baseline RMSE | Candidate RMSE |
|---|---:|---:|---:|---:|---:|
| 2021 → 2022 development | 2,548 | 81.27 | 78.21 | 96.05 | 94.47 |
| 2022 → 2023 confirmation | 2,512 | 74.23 | 74.88 | 87.43 | 89.90 |

Errors are pitcher runs per 800 batters faced. In confirmation, BF-weighted MAE
improves from `68.68` to `66.96`, but BF-weighted RMSE worsens from `80.63` to
`80.90`. Equal-player MAE worsens by `0.65` and RMSE by `2.47`.

High-A, AA and AAA improve on both equal-player errors in confirmation. A and Rookie
reverse on both. The same Rookie reversal was already visible in development, so the
failure is structured rather than a few named outliers.

## Decision

Do not change pitcher talent, WAR, FV or value. A contact component can forecast its
own target while failing to improve the complete rate; component success is necessary
but not sufficient.

Phase 2 may test whether level-specific BIP reliability repeats over additional
rolling origins. That requires more historical PBP seasons and a new rule frozen
before confirmation. Do not create a High-A/AA/AAA-only production rule from these
already-seen outcomes.
