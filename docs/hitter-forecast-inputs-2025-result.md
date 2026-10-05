# The hitter input builder now accepts verified 2025 production

Source player walkthrough complete. A separate forecast-input builder preserves
the tested arithmetic while accepting an explicit source cutoff through 2025.
It rejects future counts and duplicate identities and preserves fractional
recency even after many initial zero rows. Historical builders and their seals
are unchanged. This is a source repair, not a claim of better projection accuracy.

On all 63,282 historical rows, 125 fields per row agree with the corrected
historical definition: 7,910,250 checked values. Pooled fields and draft elapsed
also agree with the actual saved numeric incumbent. Five focused boundary tests
pass. No model is fitted and no new forecast is produced.

## Six actual source walks

These are 2025-origin inputs for a future forecast, not 2026 outcomes or predictions.
Source records are actual 2023–25 counts. New exposure is 2025 PA plus 0.8 times
2024 PA plus 0.6 times 2023 PA, with the existing 100-opportunity rate prior.
The old-helper column demonstrates what happens if its 2024 filter is reused
unchanged; it is not a previously published 2026 forecast.

| Player | Actual 2025 MLB PA | MLB precision with old helper | Correct MLB precision |
| --- | ---: | ---: | ---: |
| Judge | 679 | 838.0 | 1,517.0 |
| Kurtz | 489 | 0.0 | 489.0 |
| Yordan | 199 | 805.6 | 1,004.6 |
| Lee | 617 | 126.4 | 743.4 |
| Caminero | 653 | 163.2 | 816.2 |
| Hoskins | 328 | 413.6 | 741.6 |

Each machine-readable walk keeps raw PA, K, BB and HR by year/level, the origin
quality inputs, all corrected pooled rates and pedigree, the old-cutoff diagnostic
and its exact source-weight sum. A zero old-helper MLB input for Kurtz would be
an assembly error, not evidence he lacked a 2025 MLB season. Lee's 617 PA must
count more than his 158-PA 2024 MLB sample. Yordan's reduced 199-PA 2025 season
still enters alongside the older evidence; it is not omitted or treated as 2026
health. Hoskins's actual 2025 workload enters without inventing a future job.
No origin age, source role or talent forecast is inferred from these checks.

## Readiness is not yet a freeze

Domestic batting and dated source metadata extend through 2025. Draft data has
2025 picks. Three dependencies do not yet meet the new forecast boundary:

- Reviewed MLB launch features end in 2024 and need a verified 2025 extension.
- The reconstructed December-31 roster table ends in 2024 and needs dated 2025
  membership, not an unchanged prior-year list.
- The reviewed scouting tables end in 2025; coming-season 2026 ranks require
  verified preseason vintage. Do not use live season-updated rankings.

The [freeze preparation plan](hitter-candidate-freeze-preparation.md) controls
these extensions, membership/support checks, model assembly and independent
replay. Only after an immutable candidate freeze may authorized 2026 outcomes
be opened. The original protected forecast remains unchanged.
