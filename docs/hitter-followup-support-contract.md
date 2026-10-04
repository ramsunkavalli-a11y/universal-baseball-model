# Checking how long minor league hitters need to reveal MLB performance

2026-10-03. Before replacing the hitting model, check which future MLB targets
the historical data can actually support. A sixteen-year-old's failure to
reach MLB next year is not evidence of poor eventual hitting. Conversely,
observing a few successful survivors does not measure every teenager's latent
MLB ability. This is a source and target-design audit, not a new fitted model.

## Questions and fixed population

Use the existing 63,282 source origins and retain the same 30,506 evaluation
identities from seven origins and five whole-player folds. Reuse certified MLB
outcomes through 2025 only. Compare one, three and six calendar years of
follow-up, keeping annual paths rather than reducing every future to a total.
Do not choose an age cap, learner or favorable label after inspecting losses.

Two distinct training designs need separate counts. Completed cumulative
windows require the entire window to end by the forecast cutoff. Pooled annual
targets can use an individually completed future year even if a longer window
is unfinished, but must identify its horizon. Neither can use an outcome beyond
the current origin or a held player's labels. Count distinct active people in
the actual age, dominant-level and prior-debut groups, with a refined
rank/draft/exposure intersection. Twenty people is a warning boundary, not a
claim of adequate talent comparability. Count support separately by annual
horizon so distant arrivals cannot masquerade as immediate-arrival support.

## Outcome construction and missingness

For an annual observation, MLB PA comes from the certified complete season
inventory. Batting rate is custom batting wins above that same season's MLB
average per 600 PA: 600 times (component value minus replacement rate times PA)
divided by PA. A zero-PA person has no observed batting rate, not a rate of zero.
This target is performance under observed selection and context, not park-neutral
latent ability, published WAR, trade value or six service years.

Years after 2025 remain censored and null. Do not read 2026 files or turn an
unfinished window into zero value. Include actual 2020 MLB activity in
descriptive calendar paths, mark its short schedule, and exclude its batting
labels from proposed model-training support just as the current comparison
does. The canceled MiLB season remains missing historical exposure; no new
minor production labels are invented. Reconcile annual inventory PA with the
current dated MLB count source and reproduce all current next-year PA/rates.

## Player checks and decision

Fix Renato Nunez and Jeimer Candelario at origin 2011, Edmundo Sosa and
Magneuris Sierra at 2013, Rafael Devers at 2014, Ronald Acuna Jr. at 2015,
Kevin Maitan at 2017, Pete Alonso at 2018, established Aaron Judge at 2024,
Nick Kurtz at 2024 and Juneiker Caceres at 2024. Assert names against IDs.
Select four peers from the same origin, dominant level, age band and debut
state using only origin age, PA, position and rank; do not select successful
peers. Save actual dated stats, origin inputs, certified annual outcomes,
window maturity, actual-fold support where evaluation exists and existing
forecasts where available. No invented candidate forecasts or loss gains.

The audit can determine whether extending the target supplies enough relevant
examples to justify a bounded new comparison. It cannot establish that any
new model will improve. Finish the player review before selecting that test.
Keep the current full-history model and reviewed translated/ranking alternative.
Do not promote an explorer, change the protected forecast or declare the full
practical goal complete.

## Literature informing the distinction

[Tango's discussion of MLEs](https://www.tangotiger.net/hateMLEs.html) identifies
call-up selection, exposure weighting, development time, population regression
and context as problems in interpreting minor-to-major translations. These
motivate keeping arrival timing distinct from observed hitting, not assuming
that merely extending follow-up solves selection.

[Jensen, McShane and Wyner](https://arxiv.org/abs/0902.1360) describe sharing
information across players and time while accounting for age and position.
Their MLB study motivates a partially pooled development representation; it
does not validate its use for DSL players. [Sackmann's development analysis](https://tht.fangraphs.com/the-young-and-the-aging/)
also cautions against transferring growth patterns between differently selected
populations. No new college data collection is part of this work.
