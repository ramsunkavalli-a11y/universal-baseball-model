# Expected value and risk are related, but not the same modeling question

2026-10-03. Interpretation note during V43 execution, before its results.
No forecast, estimand, feature, setting or training membership changes.

It would be wrong to say that separate PA and batting heads necessarily assume
independence, and therefore must lose to a joint model. The working batting head
is weighted by actual future PA. That matters.

Within a common conditional population and compatible training weights, minimizing
PA-weighted squared batting-rate error targets
E[PA × rate | inputs] / E[PA | inputs]. Multiplying that rate by expected PA
recovers expected batting contribution, even when performance and playing time
are related. An unweighted mean batting rate generally does not have that property.

For example, two equally likely seasons are 100 PA at 4 batting wins/600 and
600 PA at 1 win/600. Average PA is 350. The unweighted average rate is 2.5,
which gives 1.458 batting wins when multiplied by average PA. Actual expected
batting contribution is 0.833. The PA-weighted rate is 1.429; 350 × 1.429 / 600
gives the correct 0.833. Independence is not required.

Our finite model remains imperfect: the PA and rate families differ, chronology/
origin weighting and active-only normalization are not identical between heads,
the conditional functions are regularized approximations, and origin replacement
differs from future actual environment. These are actual qualifications, not
proof of a universal covariance bias. The current source and score limitations
still need investigation on their own merits.

V43's paired forest tests a different architecture and supplies a distribution.
It is not guaranteed to improve the means simply because it preserves pairs.
Its implied rate from mean contribution/mean PA is an arithmetic yield, not
a newly validated talent grade. The useful additional questions are whether
non-arrival, regular use, bad outcomes and substantial upside have reasonable
held-out probabilities, and whether reported ranges actually cover outcomes.
Retaining a plausible upside path is not the same as correctly ranking prospects.

Likewise, a median PA forecast can improve average absolute error while worsening
the error of expected playing time or aggregate opportunity. Never relabel the
median as expected PA to pass the public benchmark. A reasonable uncertainty
layer may be useful without being a better point projection; report each claim
separately. This clarification prevents a structural experiment from being sold
on an incorrect criticism of its benchmark.
