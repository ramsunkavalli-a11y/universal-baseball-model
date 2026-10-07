# Recover older defensive components without pretending they are Statcast

2026-10-07. The missing pre-2016 MLB quality window prevents many older prospect
paths from supplying honest training labels. Audit public FanGraphs fielding
components from 2009–2021, including overlap with native Statcast, before choosing
an older target or learner. This is source and coverage work, not an accuracy win.

## Source and accounting checks

Retain compressed public leaderboard responses privately, with requested and
observed season, minimum exposure, pagination, retrieval time and hashes. Use
unauthenticated public page data; do not extract account cookies, bypass a
challenge/paywall, or publish bulk proprietary tables. Request all players with
qualification zero and verify returned count equals the reported total. Every
row must explicitly belong to the requested single season. Default current-year
date metadata is not permission to collect current-year outcomes. No 2026 data.

Inventory positions, MLBAM/FanGraphs identifiers, baseball innings, true decimal
innings, range/error/arm/DP credits, DRS components and actual BIZ/plays/OOZ fields.
Nulls remain unknown; catchers/pitchers or aggregate OF rows do not become a
measured range score. Check source uniqueness at player/position and component
additivity. Reconstruct defensive outs from baseball innings, not innings times
three on a decimal such as 884.1. Cross-check with decimal TInn where present and
the existing independent official season/player/position exposures.

The candidate older batted-ball conversion measurement is **RngR plus ErrR**,
kept in its own namespace. Total UZR additionally includes arms/DP; `Defense`
adds positional value. None is interchangeable with native range. Native and
older measurements have different definitions, adjustments and error structures.
Do not silently splice or rescale them, treat correlation as prediction accuracy,
or choose whichever metric makes a favored player look good.

## Coverage and effect on player evidence

Compare same-year/same-position overlap in 2016–2021 against certified native
range and official exposure. Count identities and complete field availability,
including tiny stints and all-null placeholders. Report discrepancy magnitudes
and definition differences without fitting a bridge. Collection availability
does not certify the vendor model or vintage publication/adjustment information.

Preserve the existing minor origins and three/five-calendar-year range windows.
Inventory which currently unknown **pre-2016 positive-exposure** paths could gain
older measurement support if a later bridge is accepted. No new skill labels are
authorized by this audit: older conversion coverage stays distinct from native
quality, and remaining gaps/position moves/non-arrivals stay unknown. Show
distinct earlier people whose entire future window would have ended at the
actual 2021/2022 cutoffs under every held-ID-fold exclusion; count origin level,
age/position and modern versus combined-rookie scope separately. More old rows
alone do not certify transport to current DSL or complex baseball.

Fixed source cases include 2015 Simmons, Trout, Arenado, Belt, Miguel Rojas and
Castellanos, resolved by MLBAM identity, plus their same-position 2015 peers
chosen by cutoff-known age/official-outs distance. Prospect walks use Trout's
earliest eligible minor CF origin and Simmons/Rojas's earliest eligible minor SS
origins, plus three same-origin/level/position peers. Preserve actual minor
counts and annual later position paths. Gains/harms are not applicable because
no forecasting comparison is fitted. Source/support and player walkthroughs
must be independently checked before disposition or another learner.

## Practical limits and next decision

Keep captures compressed and bounded to eight MiB total on the nearly full
drive; pause collection before exceeding its reserve, retaining completed exact
captures rather than restarting. No unrelated/raw-data deletion. The bounded
public source audit may advance even if a page/browser tool fails. If coverage
is usable, contract a measurement bridge or a clearly separate older-quality
validation target. If not, name the precise source/definition gap and continue
with reviewed fallback and value assembly. Do not convert unavailable targets
into zeros or reopen the closed raw-count/DP weight sweeps.

[FanGraphs UZR definitions](https://library.fangraphs.com/defense/uzr/) distinguish
range, errors, arms and double plays. The
[DRS clarification](https://blogs.fangraphs.com/defensive-runs-saved-clarification/)
compares rPM to range plus errors, not total UZR. These source definitions justify
the separate accounting, not a universal scale or reliability coefficient.
