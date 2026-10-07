# Related position history helps some defenders but is not a settled upgrade

2026-10-06. The range model now has a tested way to use a player's history at
related positions instead of discarding it. This improves the ordinary-origin
average error by 2.8%, but uncertainty includes no gain, second-base transfers
can be overconfident, and young development remains missed. Keep the existing
practical range baseline and this additional research representation; neither
is promoted to the frozen hitter forecast or explorer.

## What was compared

All 13,402 player-position forecasts, native measurements and quality labels
are unchanged. The ordinary 2022 test has 261 players and 317 position records;
its target pools actual same-position MLB range in 2023–2025, in runs per 500
defensive innings. Non-survivors and insufficient samples retain unknown quality.
This is not minor-league talent validation or a next-year delivered-runs test.

The candidate adds shrunk other-position history within 2B/3B/SS or LF/CF/RF.
It attenuates that information as the target-position sample grows, and learns
direction/context rather than equating a CF rating with an LF or SS rating.
It does not transfer between infield and outfield or import catcher history.
No parameter search, cohort changes or 2026 outcomes were used.

Ordinary-origin error falls from **2.291 to 2.228 runs per 500 innings**.
The paired difference is −0.0635, with a person-cluster 95% interval from
−0.1352 to +0.0041. Mean absolute error falls from 1.787 to 1.734. Six of seven
positions improve; 2B worsens from 2.490 to 2.508. The 2021 stress check barely
changes, 2.316 to 2.313, and remains uncertain. Earlier origins use the same
transparent history fallback because mature training support is insufficient.

## Players explain both the benefit and the danger

The review reconstructs ten focal players and 30 origin-selected peers, including
25 peers with unknown future quality. Every trace includes annual native sources,
recency, same/other exposures, fitted terms, future position paths and exact
prediction arithmetic. The table uses the ordinary-origin, future-pool units.

| Player and target position | Previous estimate | Related-history estimate | Later measured quality | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Travis Jankowski LF | −1.712 | −0.569 | +2.359 | His positive CF/RF record now matters, but the estimate remains too low. |
| Rob Refsnyder LF | −1.802 | −1.793 | −3.690 | Other-outfield evidence is slightly negative; he does not get Jankowski's boost. |
| Enrique Hernández SS | +0.243 | −1.089 | −7.970 | Negative 2B evidence makes the SS estimate more cautious; his good CF history is deliberately not borrowed. The miss remains large. |
| Jorge Mateo 2B | +0.031 | +3.645 | −1.444 | Good SS history transfers too generously to 2B. This is the largest deterioration. |
| Daulton Varsho LF | −0.678 | +5.042 | +4.030 | Strong other-outfield evidence fixes a major omission, although the new forecast overshoots. Largest gain. |
| Bobby Witt Jr SS | −0.697 | −1.216 | +4.893 | A poor rookie record at both IF positions strengthens the wrong conclusion. This model still misses development. |
| Mookie Betts 2B | −0.242 | −0.604 | −0.417 | No related IF record; positive OF defense is not treated as a 2B grade. |
| Kevin Kiermaier CF | +1.807 | +2.007 | +5.797 | No other-position signal; the small change comes from joint refitting, not a borrowed-history effect. |
| Alec Burleson RF | −0.270 | −0.270 | −7.634 | Thirty-three weighted LF outs add little. Very poor future RF quality remains unidentified. |
| Christian Walker 1B | +1.426 | +1.393 | +2.789 | Ordinary median-error case; first base retains its own measured history. |

Jankowski's own LF history contains just 172 weighted outs and +0.149 runs.
His other-outfield record contains 864.5 weighted outs and +2.002 runs. Shrinkage
reduces the latter to +0.777 runs/500 innings before the fitted transfer. Removing
all other-history inputs with the coefficients fixed changes his new estimate
by −1.143. Refsnyder has 1,202.25 other-outfield outs but −0.557 runs; the same
probe changes his grade by only +0.003. This is a real differentiation of evidence,
not a named-player exception or an automatic reward for playing CF.

Mateo has 3,992.5 weighted other-IF outs, almost all SS, and +6.550 runs; the
direct fitted other-history effect is +3.998 at 2B. His future measured 2B pool
disagrees. Varsho's corresponding effect is +5.874 at LF and substantially
improves that forecast. These opposing examples show why successful transfers
cannot be generalized to every position switch. Fixed-fit probes explain the
saved model; they are not causal effects or approved substitute forecasts.

## Remaining support and value limits

The intended beneficiary group, small target samples with at least 300 weighted
other-position outs, contains 75 people/93 rows. Error improves 2.692 to 2.571,
but its mean overprediction rises from +0.012 to +0.571. The interval is wide,
−0.381 to +0.133. Its actual-exposure predicted runs are +113.7 versus +43.9
observed. An average error gain has not settled allocation or calibration.

The detailed support audit includes the other-history sample, so **313/317**
ordinary-origin position rows have fewer than 20 matching training people,
versus 221/317 under the coarser old profile. That difference is a better warning,
not disappearing training data. Overall training has 309–332 people; nonzero
added-feature support has 27–125 people depending on feature/fold. Every ordinary
fold clears the predeclared 20-person feature guard, but that is not full-profile
certification. Jankowski and Refsnyder each have only one closely profiled person.

Player-balanced mean bias increases +0.132 to +0.229. Across all scored position
records, predicted runs using actual future exposure change +104.6 to +220.8,
against +180.8 actual. This is an oracle-exposure diagnostic, not a playing-time
forecast or full WAR improvement. The young group does not improve, and the
strong-own-history group barely changes. No universal positional coefficients,
young-development curve or defense-value rollout has been established.

The independent verifier reconstructs all source histories, preserves every old
anchor field, solves 20 fits with a separate augmented least-squares method,
replays all forecasts, support counts, intervals and player/peer arithmetic.
Eleven focused range/transfer unit tests pass. These execution checks support
the evidence; they do not turn the uncertain predictive result into deployment.

Next within the defense goal: complete native catcher talent and other component
baselines, then separately audit position exposure and contribution integration.
Keep the transfer representation available with its limits; do not launch another
position/shrinkage sweep against Mateo, Varsho or Jankowski.

Evidence: [full scores](../reports/model-evidence/defense-position-transfer-v4/report.json),
[player calculations](../reports/model-evidence/defense-position-transfer-v4/player-walkthrough.json)
and [independent review](../reports/model-evidence/defense-position-transfer-v4/final-review.json).
