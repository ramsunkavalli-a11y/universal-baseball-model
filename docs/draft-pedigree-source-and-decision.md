# Draft pedigree source and decision

**Status:** source accepted; hitter challenger supported; no direct value change

The official StatsAPI Rule 4 endpoint supplied 22,621 draft records covering 19,329
players from 2006 through 2026. Structured fields retained are draft year, overall
pick, round pick, round, slot value, signing bonus, and school class. Free-text
scouting blurbs are intentionally excluded.

The model uses era-neutral evidence:

- overall pick becomes a bounded within-year log rank;
- signing bonus becomes a within-year percentile and carries a separate availability
  flag;
- high-school versus other draft class is explicit;
- a player's later draft cannot appear in an earlier snapshot;
- undrafted/international entry is a separate path, not an imputed late-round pick.

In the untouched 2023 outer cohort, adding pedigree to the same baseball-interaction
model improved hitter arrival and meaningful-role log loss with paired 95% intervals
fully below zero. Pitcher direction was favorable but uncertain. This supports using
pedigree in hitter arrival/role research, while pitcher use remains cautious. The
positive-component outcome did not pass its proper-score uncertainty gate, so draft
evidence must not become a fixed WAR bonus or FV floor.

This evidence estimates historical odds; it does not create a fixed WAR bonus or an
FV floor. International signing bonus is not present in this source and remains a
separate input need.
