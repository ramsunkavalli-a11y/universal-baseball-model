# Broad minor-league catcher blocking result

Source check now completed: [128-game reconciliation](defensive-event-source-repair-v1-result.md)
finds at most 3/28 PB and 21/230 WP in the old terminal narratives, before
additional blocking filters. Reopen event/exposure construction, not a shrinkage
grid on the same biased data. No new blocking skill result has yet been fitted.

Review qualification (2026-09-25): narrative failure capture and dirt/continuity
selection still need an independent coverage check; broadening the PA sample did
not supply one. The [deep review](baseball-methodology-deep-review-2026-09-25.md)
narrows the conclusion to this extractor and test, not all possible use of the
available feeds for blocking. Existing scores and no-deployment decision stand.

Date: 2026-09-22
Status: **reject current form**

## Question

The first blocking test kept only plate appearances with exactly one dirt-ball pitch.
That threw away useful evidence whenever a plate appearance contained several pitches
that a catcher might need to block. Does a broader plate-appearance target reveal a
repeatable catcher skill?

## Test

Every continuous plate appearance with a runner aboard and at least one dirt-ball
candidate was included. A failure was charged when the plate appearance contained a
passed ball or wild pitch. Because the catcher and pitcher do not change within the
plate appearance, this avoids pretending that the data identify the exact responsible
pitch while retaining multi-pitch sequences.

The expected failure rate accounted for level, runner count, number and depth of dirt
pitches, pitcher and batter handedness, and park. Catcher and pitcher effects were
then separated. Only earlier seasons selected the amount of regression and predicted
each later season.

- Runner-on dirt-ball plate appearances: **240,201**
- Failures: **1,080**
- Failure rate: **0.45%**
- Catcher seasons: **5,309**
- Later catcher-season tests: **1,806**

## Result

- Neutral RMSE: **0.00169348** failure-rate residual
- Projected catcher RMSE: **0.00169284**
- RMSE change: **-0.00000064**
- Prediction/actual correlation: **0.033**
- Player-clustered 95% interval: about **-0.00000435 to +0.00000274**

Every chronological fold chose the largest available regression—10,000
opportunities. In plain language, the model needed to shrink observed catcher
differences almost completely to average. The tiny apparent improvement is not
statistically reliable or large enough to matter for player value.

## Decision

Do not add this blocking estimate to catcher WAR. The broader target fixes the old
sample-selection problem, but it confirms that the available all-level data do not
separate portable catcher blocking skill well enough. Revisit only if the feed gains
more reliable pitch-level runner movement, pitch location, and official passed-ball
and wild-pitch attribution.
