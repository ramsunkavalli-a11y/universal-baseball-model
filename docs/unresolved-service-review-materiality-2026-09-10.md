# Unresolved prior-service review materiality — 2026-09-10

**Status:** bounded source gap; explicit private-preview labels implemented

Twenty-one players in the current rights universe debuted before 2026 but are absent
from the supplied FanGraphs opening service-time files. StatsAPI supplies current-
season roster time, not a complete official opening service balance, so the control
path correctly refuses to infer the missing amount.

- Nine have a later official release transaction and correctly carry zero incumbent
  rights.
- Twelve have a current organization but no resolvable future control path. All twelve
  are off the 40-man roster.
- Across those twelve, the largest current model projection is 0.302 six-year WAR and
  the largest separate talent benchmark is $2.02 million.

This makes the gap real but bounded. Manual service reconstruction is not a P0 use of
time. The twelve players remain unranked and the explorer now states the actual reason:
the opening MLB service balance is missing and no control path was guessed. This group
is kept separate from the eleven players blocked by future contract-option decisions.

Future resolution should use a dated, player-ID-linked opening service source. A player
returning to a 40-man roster or moving above the materiality threshold should trigger
priority review; current-season StatsAPI days alone must not be treated as career
service.

