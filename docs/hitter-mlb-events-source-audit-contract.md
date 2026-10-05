# Audit the removed MLB event summaries before another fit

2026-10-05, before the audit. The four-quality restoration is complete and not
adopted. This next task is source reconstruction only, not another fitted model
or reopening of the authorized final 2026 evaluation.

Question: what exactly would restoring the seven original pooled MLB event-rate
inputs restore, and are their numerators, denominators, shrinkage and cutoffs
correct? Inspect strikeouts, unintentional walks, HBP, HR, BABIP, doubles and
triples. These are past MLB observations, not future MLB performance, event
probabilities that must sum to one, full WAR or validated park-neutral talent.

Independently derive annual MLB counts from the dated stints: walks exclude
intentional walks; BABIP hits exclude HR; BABIP opportunities equal AB−K−HR+SF.
Compare these to the saved annual counts, then reconstruct each original pooled
input in all five 63,314-row matrices. Recency is 1/.8/.6. The original prior is
100 **relevant denominator opportunities**, not 100 actual PA for BABIP. Preserve
its fixed prior centers: .23 K, .08 BB, .01 HBP, .03 HR, .30 BABIP, .05 doubles,
.005 triples. No denominator substitution or future record joins are allowed.

Each shrunk rate is (weighted numerator+100×prior)/(weighted denominator+100).
The existing transformed model coordinate is (rate−prior)/.1. No covered MLB
history yields the prior and coordinate zero, not an observed average player;
retain existing exposure/presence flags. Unknown source-year coverage raises.
Actual 2020 counts remain actual shortened evidence. Require finite nonnegative
counts and numerator≤its denominator. Double/triple rates here are per PA, not
fractions of hits; BABIP overlaps those events and excludes HR. Do not pretend
the seven rates form an eight-category simplex.

Verify prior completed receipts and source hashes. Check annual aggregation,
all 2,215,990 saved column values, identical values across the five matrices and
cutoff invariance when post-origin records mutate for all seventeen fixed cases.
Record source/fold/cutoff, annual numerators and denominators, observed/prior
shares, pooled values and actual transformed coordinates for each case. The
readable source walkthrough must include young/non-arrivals, poor tiny debuts,
mature MLB, shortened 2020 and sparse foreign histories, not just stars.

No fit, forecast, evaluation membership, PA, source prior, algorithm, hyperparameter
or explorer changes in this task. A successful reconstruction establishes what
information the old columns contain, not that the fixed 100-opportunity prior is
optimal or that adding them will improve future prediction. Raw MLB summaries
are not opponent/park adjustments. All exposed historical years remain development
evidence. Only after the source review may a prospective same-learner restoration
be specified. Failures must be explained or repaired before fitting; a missing
join is not automatically zero evidence. Closed team-record tests remain closed.
