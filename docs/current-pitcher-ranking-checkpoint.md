# Current pitcher ranking checkpoint

Last updated: 2026-09-12  
Status: **USEFUL FOR PLAYER REVIEW; EXACT ORDER REMAINS PROVISIONAL**

## What is now working

The pitcher peak estimate combines translated strikeout, walk, hit-batter and home-run
outcomes with age, level and evidence. Where the official pitch sequence is certified,
it now also uses strongly regressed level-season-relative whiff, strike, swing and
pitches-per-batter rates. Missing process evidence produces the prior forecast exactly.

The current board exposes both whether the process layer was used and its runs-per-800-BF
effect. The results explorer shows the same information. Public rank and FV remain
post-model audit fields only.

## Top-of-board check

The rebuilt top four are Anthony Eyanson, Braylon Doughty, Miguel Sime Jr. and Ryan
Sloan. Eyanson, Doughty and Sloan are also in the external overall top 50. Sime is the
important model-only case: he is 19 at High-A, has a strongly positive regressed
pitch-call profile and a high projected strikeout rate, but also a very high projected
walk rate. That is an explainable high-ceiling/command-risk disagreement, not a clean
claim that he is the third-best pitching prospect.

Among external top-50 pitchers who are eligible for the same board, none now falls
outside the model top 100. The meaningful remaining gaps include Thomas White (model
82; walk and pitch-process concerns), Gage Wood (94; home-run result concern despite a
positive process profile), and Seth Hernandez (45; limited evidence and walk risk).

The headline count of 22 model-top-25 pitchers outside the external top 50 overstates
the conflict: an overall top-50 list contains only a small number of pitchers, while the
model board is pitcher-only. Those players remain cases to inspect, not confirmed hits.

## Limits and next decision

Aggregate pitch calls help separate pitchers with similar results, but cannot identify
fastball velocity, pitch shape, pitch mix or command location. Those are the clearest
reasons a public evaluator may prefer one young pitcher over another. Do not compensate
with public FV or a hand-written bonus.

Next, create a pitcher-only historical top-tail replay using the same mean and upside
outputs. Test whether an uncertainty-aware presentation can identify elite outcomes
without changing the validated mean or tuning to a public list. If it fails, retain the
current mean order and label the top as a review queue until physical pitch traits are
available.
