# V40: which earlier contact evidence actually transfers to future MLB hitting?

2026-10-03. Source/design audit only; no forecast fits or protected outcomes.
V39 player review is complete. The objective is a practical future-MLB model,
not rebranding a positive next-year minor-league contact test as that model.

Read the existing gradient dataset's source features, benchmark membership and
target-level metadata, its source/hash registry, and the existing universal
2021–24 ten-bin contact-shape aggregate located in the earlier workspace.
Verify exact pinned hashes, keys, counts, seasons and source levels. Do not use
the old target rows for our eligibility or any predictors; preserve every broad
forecast/source row and treat missing context as unknown. Do not load 2026,
tracking exit velocity/launch angle or new college/bonus evidence.

Questions before any transfer fit:

1. Did the earlier positive gradient tests predict future MLB batting, or contact
   outcomes in the minor leagues among players with future observed contacts?
2. Does their feature table contain current MLB contact evidence, or only minor
   evidence for hitters who may also now play MLB? Mixing these is a source-label
   error even when a player/year join succeeds.
3. How many broad/current-MLB/source-stage rows have these features at origin,
   versus how many have the wider universal shape source? Count per actual
   training fold, including active future-MLB labels; missing historical seasons
   cannot be neutral or zero contact skill. No survivor-conditioned cohort.
4. Which per-league counts/context are pooled away in the old feature table?
   Can source bins/context be reconstructed before a new MLB-target test rather
   than importing fitted weights selected for a different target?

Fixed source walks: Judge 2016/2024, Winn 2023, Steer 2022, Kurtz 2024, Lux 2023,
Meidroth 2024 and Bellinger 2016. Show actual three-year league batting counts,
old contact-feature evidence, universal shape counts separately at MLB/minors,
and three same-origin/stage/debut exposure/draft peers selected without target
success. This source checkpoint makes no new forecast, gain or failure claim.

Disposition: reusable raw measurements may advance to a newly specified MLB
target test; older weights/scores cannot certify that target. State the precise
usable years/levels and training-support limitations. A source-only gap is not
a rejection of contact information or a reason to start another library search.
