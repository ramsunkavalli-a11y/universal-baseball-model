# Japan and Korea batting coverage through the October snapshot

2026-10-05. The new official first-team batting snapshot is collected and
independently reconstructed. It extends source coverage beyond the completed
2025 collection; it does not change player forecasts or establish an accuracy
gain. Neither overseas season is certified complete. The frozen forecasts and
already completed one-time 2026 MLB evaluation remain unchanged.

## What was collected

| Source | Clubs | Player or player club rows | PA | Zero PA rows | Independently reconstructed count cells |
|---|---:|---:|---:|---:|---:|
| NPB | 12 | 742 | 63,607 | 261 | 14,098 |
| KBO | 10 | 362 | 55,095 | 72 | 6,154 |

These are not 1,104 eligible hitter forecasts or necessarily distinct people.
The official batting tables include pitchers and people with no batting PA.
All rows remain in the private source collection rather than being removed for
lacking an MLB identifier. Sixteen summable KBO count fields also reconcile to
the ten official team rows. Player games are deliberately not summed against
club games.

All twelve captured NPB tables and the captured index explicitly say October 5,
2026. The earlier source check saw October 4; this is a later dated capture,
not a revision of that historical observation. KBO has retrieval receipts but
no explicit provider snapshot date in this collection. The source scope is
regular-season first-team batting, not farm teams or postseason totals. See the
[NPB statistics](https://npb.jp/bis/2026/stats/) and
[KBO batting tables](https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx).
The [NPB October schedule](https://npb.jp/games/2026/schedule_10_detail.html)
was not a basis for calling this a completed overseas season.

## Identity and denominator limits remain visible

Eight NPB rows lack a qualified NPB identity. Another 457 NPB rows and 302 KBO
rows lack MLB keys; the latter is not missing batting history when a source ID
is known. Three NPB birth-date conflicts remain explicit with no chosen date.
Three NPB PA are not enumerated by the available count categories; they are
retained as residuals, not assigned an invented event. KBO has no PA residual.

The initial NPB collector stopped because the 2026 historical roster archive
was not available. The [identity amendment](hitter-npb-2026-identity-amendment.md)
permits current official listings for static keys only. The first recovery
then stopped on a manager row sharing the player-row class. A separately
versioned [staff clarification](hitter-npb-2026-staff-row-clarification.md)
excludes only explicitly labeled manager and coach sections. Both stopped
executables remain preserved. Missing identities are not guessed from a prior
name, and current position, rights or health are not used as historical inputs.

## Six source walks are complete

The [player review](hitter-international-2026-snapshot-player-review.md) traces
the fixed largest, smallest positive and first zero-PA controls in each league.
Kurihara's observed 2024–2026 exposure grows from 930 to 1,558 PA, including
40 HR in the new snapshot; Ishiguro adds only one PA. Ogata's unresolved source
key prevents a qualified history join, which is not a zero career. Choi
Won-joon's source history grows from 957 to 1,610 PA even without an MLB key.
Kim Si-ang has only eight observed PA across the selected window; Choi
Jun-yong's four games do not create a hitting denominator.

All six future-row mutation checks preserve the earlier 2025 cutoff subtotal.
The combined source and completion suite passes 79 tests. Its first run passed
77 but two fixture setups lacked access to the shared temporary directory;
using a fresh workspace test directory resolves those setup errors without
changing the test assertions or source data.
These are descriptive source calculations, without park/league translation,
recency weights, model heads, MLB outcomes or error rankings. The machine
receipt retains three source-selected comparison people per case, including
the limitations when age or identity is unavailable. Source consistency is not
predictive validation.

## Disposition and next boundary

Retain this dated source snapshot for later forecast preparation. Do not merge
it into the evaluated 2026 candidate, call raw foreign rates MLB ability, or
infer an MLB job from a crosswalk key. Bulk tables and capture bodies stay
private; the repository receives only code and bounded review evidence.

The next source boundary is a genuinely complete, dated later-forecast input
release with eligible player identities and explicit missing-history handling.
There is no justification here for another algorithm comparison or a repeat of
the completed exposure, role, public-coverage or 2025 source inventories. The
broader hitter goal is unfinished: foreign translation and employment, prospect
opportunity calibration, public benchmark gaps and full player value still
require their existing qualifications.
