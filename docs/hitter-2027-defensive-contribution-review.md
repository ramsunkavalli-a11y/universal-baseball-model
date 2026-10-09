# Defensive skill now connects to 2027 playing time

2026-10-09. Twelve skill channels now cover all 4,851 hitters and connect to
their own projected positions/native opportunities. This is a component layer,
not a finished full-WAR or dollar ranking. It preserves the previously selected
history recipes and adds the qualified minor profile only where its inputs are
within the old fit's observed ranges. No new skill coefficients were fitted.

The profile supplies 3,860 player/position estimates. Another 3,047 current minor
position records fall outside support and retain explicit position-comparable
priors; missing current-position evidence does not manufacture a measured grade.
MLB-history defenders never have their measured range overwritten by the minor
profile. Generic position priors are estimates, not claims that each player has
exactly average talent.

Roster fallback now completes 109 formerly unknown position records using
already captured biographies, without changing anyone with usable actual
position history. The remaining 68 generic/unknown/two-way records total only
22.6 expected MLB PA, but remain visibly unresolved rather than complete zero-
fielding players. No new model fitting or manual player-position overrides.

## What is actually awarded

- Bailey: 677 projected catching innings produce +6.71 framing runs, +1.96
  throwing and -0.45 blocking. Separate native opportunity rates produce each
  amount; a single generic catcher grade is not multiplied three times.
- Lindor: 1,103 projected SS innings at +0.769 runs per 500 innings produce
  +1.70 range runs. The SS positional adjustment remains a separate term.
- Judge: RF/CF/LF range totals approximately +0.49 runs and OF arm +0.80.
  His RF skill is not awarded for a whole season on top of CF time.
- Tatis: observed RF/2B usage produces +2.87 range runs and +0.73 OF arm.
  Only RF time receives OF arm opportunities; 2B does not.
- Eldridge: 476 projected first-base innings produce -0.35 range runs and
  +0.41 receiving runs. The 68 DH starts receive neither. Positive measured
  receiving does not force range positive.
- Ohtani: all twelve hitter-defense contributions are zero because he has no
  projected position-defense opportunities. This says nothing about pitching.
- Lovich: the translated grades are +0.548 at 3B, -0.120 at SS and -0.034 in
  CF per 500 innings. With roughly one expected MLB PA, they award negligible
  2027 runs. This distinguishes a skill estimate from immediate MLB value.
- Concepcion: his current complex-league profile is outside the old training
  support. Position priors remain disclosed; the source is not turned into
  precise measured MLB talent.

The fixed cases and input-selected peers, plus both extremes of the translated
grades, are saved and replayed from native histories, profile coefficient terms,
position references, workload and unit conversions. Profile extremes include
Adrian Santana at 2B (-1.35 per 500 innings) and Ryan McCarty in LF (+2.37);
their tiny projected MLB opportunities keep those coarse conditional grades
from becoming large immediate awards. They are not scouting rankings.

**Review complete for these twelve channels.** The production table explicitly
identifies profile versus individual versus comparable evidence. DP, non-OF
arm, ABS challenge, GIDP and full league/position/replacement accounting remain
separate decisions. Existing failed DP carry-forward is not revived merely to
fill a cell. Framing is still a stated rules scenario. Historical full-value
checks, control/cost paths and the final explorer remain open.
