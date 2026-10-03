# Shared prospect model: keep useful readiness signal, not the full model

2026-10-03. All 105 heads replayed; seven actual source-to-fit player reviews
complete. Established MLB forecasts and protected 2026 are unchanged.

The smooth prospect opportunity model improves never-debut PA RMSE from
27.745 to 27.547 and upper-minor PA RMSE from 56.242 to 55.792. Langford's
expected PA rises from 43 to 214 versus 557 actual, and Kurtz from 2 to 28
versus 489. These are real partial improvements, not adequate forecasts.

The full model loses: never-debut offense RMSE .154072 to .160075 and
conditional hitting RMSE 2.6467 to 2.8690. Exact fitted terms reveal rare
rookie-league rate columns magnified by very small training standard deviations.
Holliday's earlier 2 K in 33 rookie PA supplies an implausibly large positive
rate contribution, helping push his forecast to +4.38 batting wins/600 versus
-3.31 actual. Azocar's close offense total hides two offsetting errors.

Do not adopt the complete model. Its PA-only product has a very small uncertain
offense gain; it is a research candidate, not a proved joint improvement.
The next documented comparison keeps the model family and compares fixed
baseball units. Changing units also changes effective regularization under
unchanged numeric penalties; that qualification is essential.

See [the full player walkthrough](../reports/model-evidence/practical-hitter-prospect-pooling-v54/player-walkthrough.md)
for source histories, actual fits, peer comparisons, totals and intervals.
