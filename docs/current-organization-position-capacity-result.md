# Current-organization hitter position-capacity result

Status: **USEFUL RESEARCH VIEW; NOT YET A PRODUCTION ALLOCATION**

The frozen
[`current-organization-position-capacity-contract.md`](current-organization-position-capacity-contract.md)
has been executed. It uses official 2021–2024 player/team/position evidence to define
broad workload capacity, then checks 2025 descriptively and applies the fixed shares
to the current-team view. It does not alter portable talent or trade value.

## Frozen broad shares

| Group | Team PA share | 2021–2024 team-season 10th–90th percentile |
|---|---:|---:|
| Catcher | 11.49% | 9.31%–14.15% |
| Middle infield | 22.86% | 18.43%–29.42% |
| Corner infield | 23.80% | 18.52%–30.11% |
| Outfield | 35.01% | 27.77%–39.73% |
| DH/flexible/unresolved | 6.84% | 0.45%–10.69% |

The 2025 mean team total-variation distance from those shares was 9.22%; the 90th
percentile was 14.33%. Catcher was the most stable group, with 1.96 percentage points
of mean absolute error. Corner infield was least stable at 5.29 points. These are broad
capacity guides, not exact lineup predictions.

## Current effect

The position layer identifies substantially more crowding than the total-team cap.

| Season | PA after team cap | PA after position cap | Additional reduction | Player rows reduced |
|---|---:|---:|---:|---:|
| 2027 | 159,894 | 151,714 | 8,179 | 1,034 |
| 2028 | 151,071 | 143,742 | 7,329 | 1,121 |
| 2029 | 145,263 | 136,392 | 8,870 | 1,184 |
| 2030 | 132,563 | 127,368 | 5,195 | 720 |
| 2031 | 107,646 | 106,116 | 1,530 | 328 |
| 2032 | 6,641 | 6,641 | 0 | 0 |

Across all six seasons, catcher was over capacity in **61 of 180 team-seasons** and
lost 10,915 expected PA. The strongest catcher group scale was 58.1%, meaning that
team's controlled catchers collectively had 41.9% more portable opportunity than the
historical catcher bucket could hold. This confirms the user's concern: catcher was
not receiving an explicit talent bonus, but independent player opportunity could
still overfill a team's catcher workload.

Other over-cap counts were 45 middle-infield, 26 outfield, seven corner-infield and 31
DH/flexible team-seasons. No player was ever scaled upward; all unused space remains
external/replacement/flexible.

## Decision

Keep this as a visible current-organization scenario and diagnostic. Do not feed it
into organization-neutral Model FV: a blocked player can be traded, and team crowding
is not lower talent. Before this becomes a production current-team forecast it needs:

1. historical replay showing whether the caps improve player/team PA error;
2. the confirmed multi-position role probabilities instead of primary position alone;
3. a flexible reassignment step, because MLB players can move among positions and DH;
4. an analogous starter/swingman/reliever pitcher layer.

The source materializations passed. Their GitHub runs were marked failed only after
artifact upload because an obsolete step still tried to persist results to the old
`source-certification-poc` branch. That workflow-maintenance defect is now fixed:
recovery runs `34418483096` and `34418485623` both completed successfully while
retaining the immutable binding results.

Machine-readable detail:
[`current-organization-position-capacity-result.json`](current-organization-position-capacity-result.json).
