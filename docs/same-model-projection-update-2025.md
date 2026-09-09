# Same-model 2025 projection update

Status: projection stability evidence is complete and the matching value replay now
passes.

## What was held fixed

The March 27 opportunity fits are now stored permanently under
`model_artifacts/opportunity-v2-pre2025-replay/`. The package includes every
coefficient, standardization value, feature name, dispersion parameter and input
hash needed to reproduce the fit. The October run verifies those exact hashes and
does not refit either model.

The October 15 checkpoint adds completed 2025 performance and roster evidence. It
does not use 2026 results, future team depth or FanGraphs projections. Conditional
skill uses the same Phase 1 method with the new season of evidence. Running and
defense remain the same average-zero replay fallback.

## Result

The updated checkpoint forecasts 2026–2030 for 3,907 hitters and 5,206 pitchers.
Across the four target seasons shared with the March forecast:

- 3,039 shared hitters have a 0.689 expected-WAR correlation. The mean absolute
  player-season change is 0.113 WAR and the mean absolute four-year player change
  is 0.411 WAR.
- 3,951 shared pitchers have a 0.670 expected-WAR correlation. The mean absolute
  player-season change is 0.071 WAR and the mean absolute four-year player change
  is 0.273 WAR.
- Shared 2026 hitter WAR rises by 154.9 and pitcher WAR rises by 157.2. Most of the
  increase comes from updated opportunity, not a hidden skill-model change.
- The component universes also turn over: 868 hitters and 1,255 pitchers enter;
  852 hitters and 1,139 pitchers leave. Those rows are kept separate from the
  shared-player stability measures.

These are model-update measurements, not accuracy scores. The forecast origin moves
forward one year, so the same target season can move from a longer-horizon fallback
to the frozen next-year model. That horizon change is disclosed in the report rather
than mislabeled as pure parameter stability.

## Downstream value result

The October owner, service and cost state is now attached. The resulting replay has
4,049 material value changes and zero unexplained changes. See
[the same-model value replay](same-model-value-replay-2025.md). A dated 2025 payroll
archive would still improve a future true-vintage study, but is not required for this
Phase 1 event-cutoff gate.

Reproduce with:

```text
python scripts/materialize_historical_projection_paths_2025.py
python scripts/materialize_same_model_projection_paths_2026.py
python scripts/compare_same_model_projection_checkpoints_2025.py
```
