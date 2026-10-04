# Employment information did not solve hitter playing time

2026-10-03. The added transaction information did not provide a useful overall
upgrade. Keep the corrected source work, but do not add these three inputs to
the chosen hitter candidate. Close the small employment-feature queue. The next
handoff will use the fresher preseason rankings with the established hitting
model and show the original model alongside it. This is a research choice, not
a claim that the hitter model is finished.

## What changed in the test

The comparison added capture-era coverage, known current employment evidence
and recorded free agency to both playing-time models. It retained all 30,506
historical forecasts, 35 chronological whole-player folds, exits and never-arrived
minor leaguers. Hitting estimates, other inputs, settings and scoring stayed
fixed. All 140 head checks were saved before fitting; 140 saved heads were
replayed afterwards. Thirteen actual player walkthroughs are completed in
[the review archive](../reports/model-evidence/hitter-employment-v71/player-walkthrough.md).
See [the locked comparison](hitter-employment-v71-contract.md).

## What the results say

| Forecast group | Original PA RMSE | Fresher rankings | Added employment | Actual PA total | Employment PA total |
| --- | ---: | ---: | ---: | ---: | ---: |
| All forecasts | 60.686 | 60.499 | 60.470 | 1,270,493 | 1,233,604 |
| Public matches | 138.488 | 138.330 | 138.271 | 660,776 | 651,771 |
| Documented unsigned current hitters | 142.522 | 142.587 | 142.670 | 83,028 | 82,878 |
| Upper minors without an earlier MLB debut | 56.242 | 55.127 | 54.955 | 92,891 | 75,742 |
| Lower minors without an earlier MLB debut | 7.828 | 7.966 | 7.955 | 5,194 | 7,189 |

RMSE is typical error with greater weight on large misses; scores give each target
year equal weight. Raw PA totals are not rescaled. Public matches retain the same
2,627 forecasts with both public providers. Steamer PA RMSE is 135.379 and average
absolute error is 92.083. The employment version has average absolute error
106.559, 15.72% worse; the fresher-ranking anchor is 106.411, 15.56% worse.
Neither meets the declared 15% working target. A small RMSE change does not
overrule that or establish a meaningful whole-model gain.

Overall expected-offense RMSE changes .453384 to .453326; public offense slightly
worsens, 1.060504 to 1.060577. Overall, public and unsigned paired development
intervals span zero. Upper-minor PA squared-error change is -18.852 versus the
fresher-ranking anchor, nominal interval -36.516 to -3.343; its offense interval
spans zero. Preserve that local evidence without calling the full addition a
winner. Offense here is custom batting plus replacement, not official WAR.

Appearance predictions improve a little: 4,426 expected versus 4,538 actual,
compared with 4,392 for fresher rankings. Unsigned hitters rise from 281 to 285
expected appearances versus 313 actual, yet their PA error worsens. Raising
appearance probability alone is not an adequate correction. Listed hitters
still get about 1,002,962 PA versus 1,037,360. For origin 2021 the new model
expects 590 appearances versus 686, and 166,208 PA versus 181,583; offense error
is slightly worse. COVID-era allocation is not fixed.

## What happened to actual players

| Source year and player | Fresher-ranking expected PA | Employment expected PA | Next-year actual PA |
| --- | ---: | ---: | ---: |
| 2023 Bader | 140 | 137 | 437 |
| 2018 Harper | 539 | 545 | 682 |
| 2016 Wieters | 267 | 267 | 465 |
| 2022 Bradley | 130 | 132 | 113 |
| 2022 Belt | 113 | 116 | 404 |
| 2023 Belt | 244 | 239 | 0 |
| 2023 Langford | 215 | 195 | 557 |
| 2024 Kurtz | 10 | 10 | 489 |

Bader's workload stays much too low even though his free agency is correctly
recorded. Wieters does not change: earliest training provides just one captured
origin, and the new information enters neither own saved path. Harper's group
has no closely matched earlier young-star examples. A modest adjustment cannot
be described as solving the roster interpretation.

Belt demonstrates why a blanket boost is unsafe: one return is badly missed,
then the same player receives substantial expected PA before he never plays.
Bradley's workload was already reasonable; his major miss was hitting. Chris
Davis likewise has plausible PA, but his talent collapses. Employment flags are
the wrong fix for those errors. Judge's breakout and Kurtz's immediate readiness
remain major misses in both workload and hitting.

The largest offense gain is Ohtani, 570 to 581 PA versus 731. Most of that change
comes from shared model refitting, not his own signing feature. The largest harm
is Alvarez, 547 to 556 versus 199. Bader and Rortvedt have close offense totals
only because favorable hitting estimates offset very low PA. The walkthroughs
retain failed peers and distinguish that cancellation from correct forecasting.

## Source limits and candidate choice

The broad assignment adapter also includes All-Star assignments. Alvarez's last
record is assignment to the American League All-Stars, not a contract. This is
the only latest-date assignment evidence for 86 source rows and 80 evaluation
forecasts. It can identify captured activity, but cannot establish current club
employment, a guaranteed deal or a healthy future season. Missing information
stays unknown; two independent roster/free-agency conflicts remain unknown.
Exact historical publication vintages remain unverified. Do not promote this
representation under a contract label or launch another tiny filter sweep.

Use the fresher-ranking model as the coherent next research candidate: it has
the clearer, already-reviewed upper-minor readiness improvement over the original
and does not rely on the questionable employment interpretation. Keep the original
comparison visible. Do not combine arms by player name or pick the best arm
after seeing each player's outcome. Graduation and employment challengers remain
documented but unadopted. The comparative team-filtered handoff is next, with
known immediate-arrival, workload, uncertainty and source limits plainly stated.

Protected 2026 outcomes, its frozen forecast and deployed explorers are unchanged.
The broader hitter goal remains active; a historical next-year offense candidate
is not a complete defense, six-year control or player-valuation system.
