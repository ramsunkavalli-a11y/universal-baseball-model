# T2026B: normalize competition before combining history

Declared 2026-09-06 after C2026A failed and before T2026B fitting. One new candidate,
not a retuning of C2026A or H0. Website work is paused.

Question: does explicitly normalizing historical competition improve G0's next-year
batting estimates? Fit only four common nested components: strikeouts, unintentional
walks conditional on non-K, HR conditional on contact, and reach conditional on
non-HR contact. Leave the remaining nested branches unchanged.

For each training cutoff (2021/2022/2023), use the original G0 gap-aware history,
never a constructed 2020 MiLB season. Aggregate player-season-level stints. For
players with >=50 PA at each of two levels in the SAME season, regress the four
smoothed logit differences on destination-minus-source level indicators, with MLB
anchored at zero. Add .5 to each terminal count for this contrast fit only.
Pair weights are harmonic PA, divided by that player-season's number of pairs.
Use ridge 5,000 on the five free level effects and clip each fitted effect to [-1,1].
No age bands, further calibration, tracking, tuning, or player-name inspection.

Translate each historical row to MLB-reference competition using these effects,
preserve its total evidence and unmodified rare conditional branches, then rerun
the original G0 nested empirical Bayes with its frozen fold-specific parameters.
This estimates a conditional reference profile; it is not long-term value.

Before evaluation, transform each forecast into SIX level-conditional vectors.
For the primary next-year aggregate prediction, average those vectors with a
chronology-safe origin-to-next-year PA-share transition matrix learned only from
adjacent training seasons. Pool by last-season dominant origin. Average each
returning player's destination PA shares equally; shrink toward remaining at the
origin with 100 player-equivalents per origin. If there are no pairs, stay at origin.
This mixture is conditional on observed return, not a playing-time/attrition model.
Observed future level and PA never choose the prospective prediction.

Freeze all vectors before scoring. Evaluate identical G0-overlap players in all
three years against G0 and Marcel. Primary pooled PA-weighted RMSE improvement
must be >=1%, no fold may worsen >2%, pooled event log loss may not worsen >0.25%.
Calibration readiness: |mean bias|<=.010 and slope [.85,1.15] in both views each
year. Supported origin/movement subgroups (50 players AND 5,000 PA) must not worsen
RMSE >5%. Use 1,000 paired player-cluster bootstrap replicates, seed260906.

Also score presaved conditional vectors against actual player-level stints as a
DIAGNOSTIC conditional task, never substitute those scores for prospective scores.
Selection into within-season moves remains a limitation; test-year results may
reject this estimate of transport. Preserve every result, prohibit output overwrite,
and stop this candidate after the fixed decision. Protected 2026 remains closed.
