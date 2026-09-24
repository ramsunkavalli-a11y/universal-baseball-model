# Conditional workload: a useful improvement, not yet a value-model replacement

2026-09-23. Completed under the [fixed plan](hitter-conditional-workload-v1-plan.md).

## Plain-language result

The detailed model does a better job estimating how much a prospect will play
after reaching MLB. Holding the repaired participation probabilities fixed,
it beats the stronger existing ensemble in Years 1, 2 and 3. It passes all
predeclared workload acceptance checks. Retain D as the preferred research
conditional-workload head for never-debuted minor leaguers.

This is not a change to the live explorer or the frozen 2026 forecast. It is
not yet evidence that the full WAR/value model improves. Players who already
had an MLB debut are unchanged in the primary experiment.

## What was tested

All three heads use the same corrected historical records, eligible training
players and identity weights. Conditional training includes positive MLB PA;
evaluation of expected PA includes every starting prospect, including those
who never reach MLB. Each annual horizon has its own model, multiplied by the
fixed probability of playing in that particular season.

- A: basic 84-feature direct conditional-PA mean.
- D: detailed 892-feature direct conditional-PA mean.
- M: detailed probabilities of brief, part-time and regular workloads, combined
  with past-training-only mean PA within those categories.

These are fixed LightGBM fits without a new tuning search. The rich versus
basic comparison isolates the feature package, not the contribution of any one
feature. I is repaired participation with the inherited workload head; E is
the stronger harmonized ensemble; B is accepted C2.

## Expected PA error

Equal-origin RMSE, in plate appearances; lower is better. This measures all
starting prospects, not just successful major leaguers.

| Forecast | Accepted B | Inherited I | Basic A | Detailed D | Role mixture M | Ensemble E |
|---|---:|---:|---:|---:|---:|---:|
| Year 1 | 32.79 | 29.89 | 28.89 | **28.60** | 29.07 | 29.63 |
| Year 2 | 57.69 | 52.26 | 51.44 | **50.81** | 51.30 | 51.92 |
| Year 3 | 74.76 | 67.62 | 66.99 | **66.28** | 67.09 | 67.08 |
| Three-year total | 144.96 | 127.03 | 123.53 | **121.67** | 123.94 | 126.18 |

Three-year D versus E is a 3.6% RMSE reduction, or 7.0% MSE reduction. The
paired player-bootstrap 97.5% interval for the MSE difference is
[-1912.32, -418.77] PA squared. D improves two of three origins versus E;
2016 is slightly worse. It improves all three versus I, interval
[-2058.22, -685.86], and all three versus A, interval [-770.39, -174.72].
The A comparison is supporting evidence, not a third candidate-selection gate.

Three-year MAE improves from 35.05 (I) and 35.27 (E) to 33.12 (D).
Mean absolute cohort-total PA error improves from 24,696 (I) and 26,061 (E)
to 23,862 (D). All 23 supported annual subgroup/cohort harm checks pass versus I.
Conditional PA RMSE among actual participants improves versus I in all three
horizons, though D does not beat basic A on that metric in every horizon.

The three-year comparison contains 9,833 prospect-origin records, 942 with
positive PA somewhere in the three-year window. Annual origins are
2016/17/18/21/22 for H1, 2016/17/21/22 for H2, and 2016/21/22 for H3.
Complete three-year totals use 2016/21/22. Windows crossing 2020 are excluded.

## What did not work, and what remains wrong

The role mixture improves over the inherited workload model but fails the
fixed acceptance rule. Its cumulative advantage over E is uncertain
(MSE interval [-1286.66, 46.15]); Year 3 is slightly worse than E, and its
aggregate PA error is worse than I. Do not promote it or tune its bins to these
results. This does not disprove all role-distribution or career-path approaches.

The 2021-origin cohort is still badly underpredicted. Over three years, D
predicts 72,078 PA versus 121,444 actual, up from I's 65,943. Conversely, D
slightly overshoots 2022: 98,994 versus 97,303. Better individual errors do
not mean totals or the post-cancellation transition are solved.

For Jeremy Pena at the 2021 cutoff, the conditional forecast rises from
118 to 142 PA; with the same 64.8% participation probability, expected PA rises
from 76 to 92, versus 558 actual in 2022. Ezequiel Duran rises from 20 to 29
expected PA versus 220 actual. These remain large misses; neither player was
given a manual adjustment. An expected value need not equal a successful
player's realized outcome, but these examples and the cohort shortfall show
that substantial future workloads remain difficult to identify.

M's expected regular counts also remain low: for the 2021-origin cohort,
2.1 versus 9 actual in Year 1 and 22.7 versus 46 in Year 3. D estimates a mean,
not an explicit regular-role probability; do not turn its mean into such a
probability. Actual future-regular slices are diagnostics, not selection rules.

## Verification and limits

36 fitted heads, four exact future-data mutation replays, 52,181 annual
prediction rows, and 23 focused unit tests verify. The independent verifier
checks chronology, active-player weights, saved references, role means,
probability products, unchanged non-prospect forecasts and reproduced metrics.
The prior transfer archive and original 2026 freeze also verify. No protected
2026 outcomes were opened.

These remain exposed historical development folds, with only three complete
cumulative origins. Player-bootstrap intervals account for repeated players,
not all shared season shocks; the wider intervals address two candidate heads,
not the project's entire experiment history. Treat this as a research selection,
not untouched confirmation or a claim about Years 4–6.

Artifacts: `model_artifacts/hitter-conditional-workload-v1-2026-09-23/`.
The prefit manifest locks input/code hashes and feature lists; the archive
includes references, predictions, fit records and scores. Reproduction also
requires the existing repaired panel and local prerequisite artifacts named
in the manifest; the archive is not a standalone raw-data distribution.

## Next bounded step

Freeze F participation plus D conditional workload as the prospect workload
research candidate. Predeclare and test the connection to delivered value
across Years 1–3, keeping the stronger ensemble and cohort-total checks.
Do not multiply old direct nonbatting totals by new PA / tiny old PA.
Use supported component opportunity/rate models or refitted direct totals;
first establish which existing components have valid exposure definitions.
Keep batting, position, running, general defense and catcher effects separately
auditable. No full-model deployment, explorer refresh or extrapolated Years 4–6
claim follows automatically from this workload result.
