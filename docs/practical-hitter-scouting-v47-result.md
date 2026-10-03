# Historical prospect rankings improve readiness but need a fallback

2026-10-03. Rankings add useful information about next-year MLB playing time
for highly regarded prospects. They are not a satisfactory replacement for the
whole hitter forecast. Newly drafted and rapidly rising players can be harmed
when an old preseason absence competes with their newer production and draft
evidence. All fifteen model walkthroughs and nine source walkthroughs are
complete; the next decision is based on those cases as well as scores.

## What was compared

The same 30,506 next-calendar-year forecasts and 35 chronological held-player
fits as the reviewed count/games model. Twelve ranking inputs join 239 existing
count, age, level, games and draft inputs; model settings, membership, availability
rules and hitting estimates stay fixed. Contributions are batting plus
replacement wins, not full WAR or six years of club control. No 2026 outcomes,
new college data or frozen forecast changes.

Historical tables cover 2011–2024. Only ID, year, rank and list coverage enter
the model; present-day biographies and mixed-vintage grades/ETA/text are excluded.
The 2020/2021 lists return 99 entries: verified positive rankings are retained,
while absence stays unknown. Tables are retrospective reproductions, not
independently certified archived editions. A documented 2016 Brinson rank
disagreement qualifies the source. The separate 9,175-report scouting dataset
was reviewed, but grades and text were not imported without adequate dating and
deduplication. This is a rank-only experiment, not rejection of richer scouting.

## Results on the same people

| Population | Count and games PA RMSE | Ranking PA RMSE | Interpretation |
|---|---:|---:|---|
| All eligible forecasts | 61.149 | 60.874 | Small point improvement; incremental interval includes no gain |
| Never-debut upper minors | 57.089 | 55.685 | Better individual error; incremental interval narrowly includes no gain |
| Listed prospects | 167.981 | 157.871 | Favorable development interval |
| Top 20 prospects | 214.524 | 176.055 | Clearer readiness signal, not guaranteed success |
| Matched public sample | 143.191 | 142.797 | Still behind Steamer 135.019 |

The nominal player-cluster interval for the broad PA-MSE change is -72.52 to
+6.82; batting-plus-replacement MSE change is -0.001464 to +0.000323. The
top20 PA-MSE change interval is -24,468 to -5,128 and contribution-MSE interval
-0.51035 to -0.06746. These are exposed development results, not final-test
evidence. The entire candidate also beats the different working assembly's
pooled RMSE, but that contrast includes earlier source/rate changes and cannot
all be attributed to rankings.

Public PA mean absolute error remains 110.553 versus Steamer 92.399, about
19.6 percent higher, failing the predeclared 15 percent tolerance. The public
sample has 1,789 matches, not every MLB hitter; snapshot timing and batting-value
environment qualifications from the public benchmark still apply.

Upper-minor expected PA total is 95,576 versus 102,951 actual, farther below
actual than the games control's 100,089 despite better individual error. Lower-
minor expected PA is 10,509 versus 6,072 actual. Origins 2017 and 2024 worsen
on PA versus games. The 2021 origin improves on PA but contribution totals
remain 629 versus 568 actual. Pooled improvement does not erase these problems.

## What the player reviews show

Volpe rises from 166 to 416 expected PA versus 601 actual. Rodriguez rises
103 to 284 versus 560. These are genuine readiness improvements, but Volpe's
contribution worsens because his unchanged hitting estimate is too optimistic;
Rodriguez's elite hitting remains underestimated. Judge rises 150 to 208 versus
678, while his fixed rate still misses the breakout by a large margin.

Brinson rises 121 to 254 versus only 55 PA; Frazier rises 145 to 236 versus
142. Their unsuccessful and delayed peers remain in the comparison. Seager's
PA gets worse while contribution improves through offsetting component error.
Hechavarria's near-exact contribution is also an offset, not exact workload.

Kurtz drops 30 to 3 PA versus 489, Langford 217 to 116 versus 557, Bellinger
8 to 3 versus 548 and Alonso 215 to 155 versus 693. Their actual draft,
power and advancement evidence exists; stale preseason absence does not describe
their end-of-year standing. New draftees were not even professionals when those
lists were published. This is a representation gap, not a reason to delete
non-arrivals or assume every promising prospect will become a star.

Rank-specific training profiles for Brinson, Volpe and Rodriguez contain only
9, 15 and 16 distinct people despite large broad-stage samples. That limits
confidence and is retained as a warning, not hidden by row counts. Alvarez and
Andujar remain major exposure collapses; the source record alone cannot establish
which injury or job information was genuinely knowable at origin.

## Decision and next work

Retain the qualified historical ranking source and evidence that reputation
helps prospect readiness. Do not adopt the unmodified whole-population candidate
or change the working/frozen/deployed forecast. Next evaluate an explicit
positive-evidence fallback: use the ranking head when a current positive rank
is known, and otherwise preserve the count/games forecast rather than allowing
stale absence to overwrite it. This post-review design change is development
work, not a predeclared independent confirmation or new information about an
unlisted player's talent. It must keep all players, show calibration and named
harms, and cannot substitute for a better conditional hitting model.

The practical hitter goal remains incomplete. See the full
[player walkthrough](../reports/model-evidence/practical-hitter-scouting-v47/player-walkthrough.md)
and [machine-readable scores](../reports/model-evidence/practical-hitter-scouting-v47/scores.json).

