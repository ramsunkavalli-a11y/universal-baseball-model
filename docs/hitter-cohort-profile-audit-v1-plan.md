# All-cohort expectation and missed-profile audit

2026-09-23. Diagnostic only: no fits, feature selection, model change, remote
update, or protected 2026 outcome access. Define groups before scanning their errors.

Audit the retained research combination: F participation and D conditional PA
for never-debuted minor leaguers, unchanged B probabilities/conditional PA for
everyone else. This is not a claim that the live explorer uses the research
candidate. Use every archived Year 1–3 fold, plus complete cumulative totals.
Add the available 2023/2024-origin F participation forecasts for prospects only;
no D workload forecasts exist for those origins, so do not invent them. Earlier
training snapshots are not out-of-sample cohorts. Pitchers and six-year/value
endpoints are outside this playing-time diagnostic.

Keep 2021 origin separate. Show pre-COVID origins and later origins individually;
"non-2021" includes 2022 and does not mean completely untouched by COVID.

Fixed cutoff-known profiles: stage/debut, level, age, current PA, roster protection,
promotion/repeat/partial-promotion history, low/high K, walks and HR, detail coverage,
Mexican League exposure, draft match/pick quality and historical predicted talent.
Use a limited list of baseball-motivated intersections (young upper minors,
protected upper minors, protected productive upper minors, upper-minor repeaters,
older MLB regulars). No arbitrary tree search over subgroup definitions.
Talent quintiles use each snapshot's cross-fitted rate forecasts; they are not
future realized talent or public FV. Position-specific diagnosis is not supported
by the present joined panel; do not invent a position or missing injury history.

Report expected/observed participation, expected/observed PA, equal-origin mean
bias and RMSE, per-origin consistency and sample support. Positive signed residual
means underprediction. Exact PA accounting:

    actual_PA - p*q = q*(active-p) + active*(actual_PA-q)

The first term is participation-weighted error; the second is conditional workload
error among observed participants. They sum exactly but are not a causal allocation
or permission to use future participation in a forecast. Cumulative annual marginal
probabilities sum to participant-seasons, not distinct players who ever arrive.

Descriptive recurring-profile flag: at least three non-2021 origins with >=100
rows and >=5 positive outcomes each, and >=75% share of supported origins with
the same signed PA bias. Report all bins, not only flagged ones. This is a screen,
not a multiple-testing-adjusted discovery or independent validation; overlapping
profiles cannot be summed as distinct explanations. Rate profiles use >=200
current PA and are raw observed rate bins, not park/level-neutral talent labels.

Inspect largest positive and negative player residuals only after group tables;
these examples do not define a new group or justify a player override. Retain
all non-arrivers in profile denominators. Keep prediction/source hashes, tests
of the accounting and cohort partition, and a plain-language report locally.
