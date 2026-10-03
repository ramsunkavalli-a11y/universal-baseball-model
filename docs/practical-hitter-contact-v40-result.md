# Earlier contact gains are not yet a future-MLB hitter result

2026-10-03. Source/design review complete; no new model fit, score or promotion.
This qualifies transfer of old evidence, not the original experiment's recorded
result. V33b remains working, V38 remains research. Protected 2026 unchanged.

## The important distinction

The earlier positive gradient-contact test's 9,157 benchmark rows predict
next-year **minor-league contact results**. Every target has observed contact;
target levels are A, High-A, AA, AAA and Rookie, with no MLB target. It is not
a test of future MLB hitting, MLB arrival or delivered player value. It can
show signal in contact measurements but cannot certify this project’s central
forecast. The earlier time folds also include repeat train/test players;
our current whole-player separation is a different validation design.

Its source table summarizes minor-league contact, even for players who also
played MLB that year. The probabilities shrink raw contact cells toward source-
level/bin priors; mean park and prior-opponent effects are additional inputs.
These are **not already fully park/opponent-neutralized player probabilities**.
The distinction must survive source labels, joins and explorer explanations.

## A useful source that had not entered the rebuilt batting model

A separately pinned universal ten-bin shape table contains **2,328,735 contacts**
in 2021–24, including **475,972 MLB** contacts. Exact actual-league identifiers
remain available. This is different from the minor-only gradient feature table.

| Origin year | Current MLB players | Players with old minor-contact features | Players with universal MLB shapes |
|---|---:|---:|---:|
| 2021 | 662 | 443 | 658 |
| 2022 | 688 | 482 | 683 |
| 2023 | 652 | 438 | 648 |
| 2024 | 649 | 424 | 647 |

For example, Judge's 2024 old-gradient row is absent, but the universal source
has 381 current MLB contacts. Winn has 353 old minor contacts, distinct from
95 current MLB shape contacts. Lux has no current contacts after a missed year,
but 248/324 prior MLB contacts remain in the universal history; the older
gradient source retains only a 52-contact minor/rehab record.

These measurements are not automatically model-ready or proven useful for our
MLB target. Shape counts do not provide a complete shape-by-terminal-result
cross-tab, direct park neutralization or cross-source measurement equivalence.
No launch-angle/exit-velocity tracking predictors were used in this audit.

## Chronology and support still matter

Both inspected contact tables begin in 2021. The 2016–18 evaluation rows have no
contact source here, although their official batting counts are present. The
2021-origin folds have **zero training examples with these measurements**.
Adding columns and fitting those folds would not magically create learned
contact relationships. In one 2022 fold there are only 556 future-active MLB
training rows with universal current-source shape, versus thousands of older
count-only examples. This limits a modern-only transfer experiment; it is not
proof that the raw 2016–20 PBP cannot be reconstructed elsewhere.

Do not silently drop earlier years, non-arrivals or unknown sources to claim a
near-decade model. Materialize the earlier compatible source, or keep exact
baseline fallbacks and label the narrower experiment honestly.

Eight player source walkthroughs cover actual batting histories, both source
joins and bin counts, null/absence distinctions, reliability/context, and
origin-only comparison players. Source hashes, membership and counts are pinned.
An initial case-sensitive MLB-label error in the new diagnostic was caught and
repaired before review or any fit; original diagnostic artifacts are preserved.
See [execution note](practical-hitter-contact-v40-execution-note.md).

## Next concrete assembly

Reconstruct contact measurements at actual league/source-season grain from the
certified historical PBP sources, rather than copying the old minor-target
weights. Preserve exposure, measurement coverage and missingness. Then test one
bounded broad future-MLB batting model against V33b/V34 with workload fixed and
both conditional rate and delivered-value checks. The first usable increment
may be universal shape; full shape×outcome/context requires its own compatible
source bridge. Keep failed first arrivals and brief-debut cases in the review.

See [audit and actual-fold coverage](evidence/practical-hitter-contact-v40/audit.json)
and [eight source walks](evidence/practical-hitter-contact-v40/source-walkthrough.md).
The practical hitter goal remains active, not completed by this source audit.
