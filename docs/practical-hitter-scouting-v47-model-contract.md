# Test historical prospect rankings against future MLB opportunity

2026-10-03. The source review is complete before fits. Test whether the publisher's
historical prospect rank adds meaningful next-year MLB opportunity information
to the reviewed games/count/draft model. This is not a test of full scouting
grades, text, fresh post-draft reports, conditional talent or six-year value.

## Fixed comparison

Use the same 63,282-row source panel, 30,506 outer forecast identities and 35
chronological held-player folds as the games comparison. Keep target 2020 out;
only complete future labels through the cutoff enter training. Preserve the
completed 2020 source extension, all non-arrivals/exits and unverified roster-
only rows. No cohort deletion, new college collection or protected 2026 access.

Add twelve deterministic inputs to the same 239 games/count predictors: source
availability, capacity, listing and rank score for each of three origin/history
years. Rank score is (101 minus rank)/100; it is not a WAR grade. Complete-list
absence gives a not-listed flag and score zero, not zero hitting ability. For
the partial 2020/2021 lists, an absent player's listing and score stay missing.
Years before 2011 stay missing. No future ranking fills a past slot. Annual
preseason lists can be stale for new draftees and fast movers; the existing draft
and production inputs are not removed. No publisher ETA, grade, text, position,
current age, current team or current level enters the learner.

The existing finite-input preflight requires a numeric missing representation.
Encode unknown listing/score as -1, distinct from zero for certified non-listing
and accompanied by source availability/capacity. Source records retain nulls.
This is an explicit category/sentinel, not a negative talent grade or imputation
from future information. The unchanged learner can split these categories.

Fit one squared-error histogram boosting head with unchanged settings: 250
iterations, depth three, minimum leaf 30, learning rate .05, L2 ten, seed 31,
no early stopping, equal-origin weights and two threads. Preserve PA bounds
[0,800] and the same reversible retirement/permanent availability policy. All
actual preflights and distinct-player rank/stage/debut support must be saved
before any fit. Sparse support warns; it does not delete forecasts.

Hold the games model's batting rate exactly fixed. Contribution is expected PA
times (batting wins/600 plus origin replacement per PA), not full WAR. Compare
the entire working model separately, without mixing its different batting head
into an incremental rank effect. No parameters, thresholds or rank transforms
are selected from outer scores.

## Evaluation and decision

Primary: equal-origin PA squared error and fixed-head delivered contribution.
Report MAE, paired player-cluster intervals, identical public matches, origins,
stages, never-debut upper minors, recent debuts, ranked/unranked/source-unknown
profiles and totals. Check 2021 and the known lower-minor excess explicitly.
The practical public tolerances remain unchanged. A better ranked-prospect slice
does not establish an adequate full hitter model; a weak result does not reject
all scouting information.

Fixed player cases: Judge 2016, Bellinger 2016, Volpe 2022, Kurtz 2024, Concepcion
2024, Brinson 2016, Frazier 2016 and Seager 2016. Add the largest PA improvement,
deterioration, false high, false low and an ordinary case where not already
covered. For each show actual counts, all added inputs, exact fitted path,
training support, baseline/candidate/value arithmetic and outcome-blind peers
including failed prospects. Finish the review before disposition or another
modeling experiment. Working/frozen/explorer promotion requires separate review.
