# Model player-type source correction

Status: corrected in the private Model FV build.

The Model FV assembly previously chose hitter or pitcher by whichever projected WAR
was numerically larger after missing paths were filled with zero. An exclusive
pitcher with negative projected WAR could therefore become a hitter despite having
no hitter path. During the pitcher-demographic on/off replay, this caused 161 player
types to change solely because a small rate adjustment crossed zero.

The corrected rule is source-first:

- pitcher path only means pitcher;
- hitter path only means hitter;
- only a player with both real paths uses the larger projected component to choose
  the primary valuation type.

The same-input replay now has zero player-type switches. A regression test covers an
exclusive negative-WAR pitcher. This correction does not add a player opinion, grade
target, position preference, or value floor; it preserves the role asserted by the
actual projection path.
