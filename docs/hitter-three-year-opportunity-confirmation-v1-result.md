# Three-year opportunity confirmation: results

Completed 2026-09-22. [Predeclared experiment](hitter-three-year-opportunity-confirmation-v1-plan.md).

## Decision in plain language

The new playing-time model beats the delivered playing-time estimates in all three
years, including for minor leaguers. But a five-model ensemble, given exactly the
same inputs, beats the single LightGBM candidate in every year. The candidate
therefore does **not** pass the complete confirmation rule.

Connecting the new PA to an independently projected hitting rate improves overall
three-year batting/replacement value error. However, it worsens next-year value
for young upper-minors hitters beyond the limit declared before testing. The
smaller learned correction also fails the delivery gates. **No forecast or explorer
is changed.** This is not a full-WAR improvement: fielding, position and baserunning
are outside this multi-year value target.

The important new gap is prospect opportunity. These models do forecast increasing
MLB playing time for today's minor leaguers, but they still underestimate the
amount those players collectively earn. Better individual accuracy does not, by
itself, establish well-calibrated arrival probabilities or league-wide totals.

## Playing time across Years 1–3

Normal-season PA RMSE, with each forecast origin weighted equally; lower is better:

| Horizon | Delivered PA model | Fixed LightGBM candidate | Harmonized ensemble |
| --- | ---: | ---: | ---: |
| Year 1 | 69.26 | 62.63 | 62.33 |
| Year 2 | 86.39 | 79.40 | 78.85 |
| Year 3 | 98.34 | 90.58 | 89.63 |

The candidate improves on delivered PA in all five, four and three eligible
origins, respectively. Its paired MSE differences and 95% whole-player bootstrap
intervals are −874.7 [−1019.4, −726.8], −1158.1 [−1376.1, −945.1], and
−1465.3 [−1790.4, −1159.9]. These are MSE intervals, not RMSE intervals.

Against the harmonized ensemble, candidate MSE is worse by 37.6 [8.5, 65.8],
86.3 [36.5, 132.4], and 171.1 [104.0, 246.0]. Candidate MAE is marginally better
than the ensemble, but the predeclared squared-error comparison fails in all
three horizons. The other PA and supported-subgroup safeguards pass.

The ensemble is the previous five-member architecture refitted on the same
77 features, training rows and cutoffs: direct LightGBM plus LightGBM, XGBoost,
EBM and Ridge hurdle forecasts. It is not the old high-dimensional input panel.
The saved older rich ensemble is a separate Year-1 overlap diagnostic: 65.37 RMSE
versus 64.90 for the candidate on 16,305 matched rows. That different-population
result does not override the harmonized comparison.

## Minor leaguers are included—and expose a calibration gap

The prospective cohort contains every cutoff-known minor leaguer without an
already-recorded MLB debut, including players who never reach MLB. Groups are
not selected by later success. The same 9,845 player-origin observations support
all three years in the normal-calendar cumulative comparison.

Mean MLB PA per starting prospect, including zeroes:

| Horizon | Actual | Candidate | Ensemble |
| --- | ---: | ---: | ---: |
| Year 1 | 4.45 | 3.23 | 3.39 |
| Year 2 | 10.53 | 6.84 | 7.33 |
| Year 3 | 16.11 | 11.54 | 12.43 |
| Three-year total | 31.09 | 21.60 | 23.15 |

The candidate underpredicts this group's collective three-year opportunity by
about 31%; the ensemble by about 26%. The delivered model forecasts 25.80 PA per
prospect, closer in aggregate, despite worse individual three-year PA RMSE:
145.21 delivered, 127.43 candidate and 126.13 ensemble. These are means across
all starting prospects, not predicted workload conditional on making MLB.

A separate, fixed arrival-by-deadline classifier estimates a 7.2% chance of any
MLB PA within three years versus an observed 9.6%, on that same starting cohort.
This is distinct from playing in Year 3 and is not a sum of annual probabilities.
Its probabilities are monotonically reconciled across deadlines and are diagnostic,
not deployed annual activity estimates.

The upper-minors gap is especially visible. Among under-23 upper-minors hitters
without a prior debut, Year-1 arrival is predicted at 15.1% versus 20.4% actual;
three-year arrival is 31.4% versus 41.0% actual in its eligible cohort. Lower-minors
under-23 three-year arrival is much closer, 4.2% versus 4.5%. This argues for a
level-specific calibration test, not a blanket boost to every minor leaguer.

MLB returners in the minors and recent MLB debutants are scored separately. Both
show better PA accuracy than the delivered model. Actual future arrival paths
are also saved for diagnosis, but cannot qualify an adoption decision.

## Does the improvement reach delivered player value?

The delivered report predicts batting/replacement value separately from PA. We
therefore tested its actual historical value recipe, not a value manufactured by
dividing that forecast by its PA estimate. The alternative uses a separately
fitted, cutoff-safe hitting-value rate, held fixed across forecast horizons.

Three-year cumulative batting/replacement value RMSE, 12,891 normal-calendar
player-origin paths:

| Value construction | RMSE |
| --- | ---: |
| Delivered direct-value forecast | 1.216 |
| Delivered PA × independent rate (control) | 1.176 |
| Candidate PA × independent rate | 1.147 |
| Delivered value + earlier-data-fitted PA correction | 1.213 |
| Ensemble PA × independent rate (diagnostic) | 1.140 |

The full candidate product improves cumulative RMSE by about 5.7% versus delivered
value, wins all three normal origins, and has a paired MSE difference of −0.1623
[−0.2297, −0.1058]. Its three-year prospect value RMSE also improves, 0.596 to
0.571. The control demonstrates that both the changed value construction and the
new PA contribute; the whole gain must not be credited to playing time alone.

**Why it is not adopted:** for young upper-minors hitters, Year-1 value RMSE rises
from 0.453 to 0.472—an 8.5% increase in MSE, exceeding the predeclared 5% limit.
This group has 879 observations across five origins and 174 actual MLB participants,
so the guard has its required support. The ensemble product also worsens this
group (0.471 RMSE); switching engines does not solve the value-integration issue.

The candidate product is better than the old-PA product control in that group
(0.498 to 0.472). Thus the failure is not evidence that more accurate playing time
is harmful by itself. Carrying a fixed hitting rate into a differently selected
future MLB population remains an unresolved integration assumption.

The learned correction has an uncertain cumulative MSE gain, −0.00515
[−0.01389, +0.00284], and worsens Year-1 value for the inactive/unknown group.
Year-1 supported correction weights are approximately 0.67–0.81. Supported
Year-2 weights clip to zero; Year 3 never has two mature earlier normal origins
and therefore uses the predeclared zero fallback throughout. This is not evidence
that a well-supported nonzero Year-3 correction was tested and failed.

## Timing, stress tests and limits

- Six origins: 2016–19 and 2021–22; all targets end by 2025. Train only on targets
  mature at the forecast cutoff. Exclude pandemic-crossing training windows.
- Normal annual evaluation has 21,819 / 17,471 / 12,891 rows across 5 / 4 / 3
  origins. Year 3 normal origins are only 2016, 2021 and 2022. Calendar disruption
  is reported separately, never hidden or corrected using future season length.
- Candidate Years 1–2 and accepted PA reproduce the preceding screen on matched
  keys. Zero and negative value outcomes remain in scoring.
- The origin-2022 player-disjoint stress removes every evaluated player's history
  from training. Candidate PA RMSE is 89.13 / 83.80 / 96.25; ensemble is
  85.93 / 82.63 / 94.47. The ensemble also wins this stress. Removing a whole
  cutoff population changes the training population substantially; this is not
  proof of identity memorization or a literal new-prospect simulation. Player IDs
  are not predictors. The value anchor is not disjoint, so value is not scored here.
- Pandemic-crossing cumulative value RMSE is 1.011 delivered, 0.996 candidate
  product and 1.015 corrected. The old-PA product control is better at 0.970.
- The league ledger separately records actual MLB PA outside the starting cohort.
  Those are not all prospect arrivals: old seasons also include pitcher batting.
  No league total is forced and no future entrant is silently assigned to a named
  cutoff roster.
- Historical seasons and model selection are already exposed development evidence.
  Bootstrap intervals are conditional on the fitted models and historical seasons;
  they do not establish independent-season replication or adjust for all prior
  model searches. Small young-star groups remain descriptive.
- No 2026 outcomes, unverified historical workbook projections or current contract
  terms are inputs. The protected 2026 forecast and delivered multi-year v2 remain
  unchanged. This does not validate full WAR, career value or uncertainty ranges.

## Next bounded checkpoint

Use the harmonized ensemble as the stronger reference, not an automatic production
replacement. Predeclare a prospect opportunity/value test that:

1. Calibrates arrival using only earlier mature out-of-time predictions, with
   shrinkage and separate upper/lower-minors support; retains all non-arrivals.
2. Distinguishes entry into MLB from workload after entry and future hitting value
   conditional on receiving those opportunities. Compare to the existing direct
   value forecast and simple rate products, rather than assuming independence.
3. Tests individual PA/value accuracy, level/age arrival calibration, aggregate
   prospect opportunity, supported subgroup harms and three-year delivered value
   together. Preserve older-player and star checks and a separate outsider ledger.

Do not select an uplift from the percentages above or retune this completed
experiment. Obtain more mature historical out-of-time support before relying on
a learned Year-3 integration coefficient. No new data-driven experiment has been
fit after seeing these scores.

## Reproduction and audit

Package: `model_artifacts/hitter-three-year-opportunity-v1-2026-09-22/` contains
keyed predictions, cold-start predictions, three-year paths, all group/calibration/
growth/league tables in `report.json`, and source/artifact hashes. It contains
79,713 player-origin-horizon rows and 26,571 complete paths across all calendars.

From the repository with its existing environment and data:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_three_year_opportunity_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_three_year_opportunity_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_three_year_opportunity_v1.py --verify
```

The fit cache is keyed by input/code/plan fingerprint `e6e2bd3375d4407a`.
Verification checks chronology, disjoint stress IDs, mature correction support,
keys, finite forecasts, cumulative arrival monotonicity, value arithmetic and
three-year sums. The focused regression suite passes 88 tests; Ruff and diff
checks pass. Both original-freeze and unchanged multi-year artifact verifiers pass.
