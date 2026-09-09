# Contract vesting trigger baseline — 2026-09-09

All 13 vesting-option rows now have sourced trigger definitions. The machine input
uses plate appearances, pitching outs, games pitched or seasons with 100 games caught.
These can be assembled from official StatsAPI results. Pitching outs avoid errors from
decimal innings notation.

- Aroldis Chapman: 120 pitching outs in 2026, plus a postseason physical condition.
- Kyle Freeland: 510 pitching outs in 2026.
- Yandy Diaz: 500 plate appearances in 2026; otherwise a $10M club option.
- Luis Castillo: 540 pitching outs in 2027, with a separate UCL/IL contract branch.
- Merrill Kelly: 510 pitching outs in 2027.
- Seth Lugo: 570 pitching outs in 2027 or 1,005 across 2026–2027.
- Carlos Correa: declining annual PA thresholds for 2029–2032, with awards alternatives.
- Tyler Rogers: 60 games pitched in 2028 or 110 across 2027–2028, plus a physical.
- Brent Rooker: 500 PA in 2029, 900 across 2028–2029 or two top-10 MVP finishes.
- Cal Raleigh: 100 games caught in four seasons during 2025–2030.

The evaluator is intentionally conservative. Reaching a simple counting threshold is
irreversible and can be marked vested. Missing a threshold is final only when that
season is complete. A satisfied stat threshold with a mandatory medical condition
stays pending. A missed primary threshold also stays pending when an unevaluated
multi-year or awards alternative could qualify. Missing observations never become zero.

The first live materialization reuses the retained 2026 official StatsAPI totals and
official schedule calendar. As of 2026-09-08 it finds:

- Yandy Diaz: 620 PA, so the 500-PA trigger is vested.
- Aroldis Chapman: 146 pitching outs, so the 120-out threshold is met; the required
  physical keeps the full contract outcome pending.
- Kyle Freeland: 373 of 510 pitching outs; the season is incomplete, so this remains
  pending.

The other ten rows are future-season clauses, not missing current observations. This
establishes the reusable StatsAPI calculation path but does not yet remove every row
from economics review. Yandy Diaz's final trigger now changes his 2027 control state
from vesting option to guaranteed contract before economics are calculated. The next
integration should add structured award, multi-season and catching-position
alternatives as those seasons become relevant.
