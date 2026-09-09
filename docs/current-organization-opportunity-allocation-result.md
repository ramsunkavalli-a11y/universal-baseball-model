# Current-organization opportunity allocation result

Status: **RESEARCH CAPACITY LAYER COMPLETE; ROLE ALLOCATION STILL MISSING**

The frozen
[`current-organization-opportunity-allocation-contract.md`](current-organization-opportunity-allocation-contract.md)
now has an executable current result. This is a separate team-context view; it does
not alter organization-neutral talent, WAR rates, Model FV or trade value.

## What it does

The fixed historical reference is 182,926 PA/BF per league season, or 6,097.53 per
team. Known controlled players keep their organization-neutral opportunity unless
their team total exceeds that capacity. An over-cap team is scaled down proportionally;
no player is ever scaled up. The remaining capacity is an explicit external,
replacement or future-acquisition share.

All 30 organizations and six future seasons close exactly on both the hitter and
pitcher sides after that unassigned share is included. Every controlled input row
attached successfully: 16,808 hitter player-seasons and 22,356 pitcher player-seasons.

## Current result

| Season | Controlled hitter PA | Open hitter share | Controlled pitcher BF | Open pitcher share | Teams scaled down |
|---|---:|---:|---:|---:|---:|
| 2027 | 159,894 | 12.6% | 150,467 | 17.7% | 2 hitter / 0 pitcher |
| 2028 | 151,071 | 17.4% | 143,897 | 21.3% | 2 / 0 |
| 2029 | 145,263 | 20.6% | 133,281 | 27.1% | 3 / 0 |
| 2030 | 132,563 | 27.5% | 121,956 | 33.3% | 0 / 0 |
| 2031 | 107,646 | 41.2% | 94,715 | 48.2% | 0 / 0 |
| 2032 | 6,641 | 96.4% | 2,433 | 98.7% | 0 / 0 |

Only seven of 180 team-seasons required a scale-down. The largest was organization
138 in 2028, scaled to 91.96% of its raw hitter total. No pitcher team-season exceeded
capacity.

The very large open share in 2032 is intentional: the current control path no longer
assigns most players to their present organization that far out. Filling that share
with current prospects would falsely assert future ownership.

## Decision

Retain this as the current-team capacity boundary. It prevents impossible overbooking
without creating playing time or confusing roster context with talent. It does not by
itself solve inflated prospect opportunity because most teams are below the broad
capacity.

The next useful layer is within-team competition:

1. hitter position groups, with catcher handled as a workload constraint rather than
   a talent bonus;
2. pitcher starter, swingman and relief workload;
3. an explicit flexible/DH and replacement share so rigid labels do not force false
   precision;
4. chronological validation against later team usage before integration.

Machine-readable detail:
[`current-organization-opportunity-allocation-result.json`](current-organization-opportunity-allocation-result.json).
