# Historical hitter candidate: inspectable, not finished

2026-10-04. The reviewed forecasts are now together in a separate team-filtered
research explorer at <http://127.0.0.1:8801/>. It defaults to predictions of 2025
from information through 2024, not a changed 2026 forecast. This milestone fits
no new model and reproduces the already scored combined forecasts exactly.

## What the candidate uses

- Before MLB debut: the reviewed translated prospect Ridge branch, combining
  production at separate levels, age, position, draft and dated rankings.
- Previously debuted, with own recent MLB launch measurements: the reviewed MLB
  Statcast Ridge branch, combining production, measurement counts, exit velocity,
  launch angle and contact-quality summaries.
- Previously debuted without those measurements: the existing rate fallback.
- Playing time: the existing appearance-probability and conditional-PA gradient
  tree heads. Expected PA remains their bounded product. No new injury, job or
  team-record adjustment was added.

The uncertain precision-aware minor measurement and exposure heads are visible
comparisons, not adopted. No older uncertainty ranges were attached to the new
means. No defense, running, positional bonus, full WAR or trade value is claimed.

## What improved, and what has not

Across the unchanged 30,506 forecasts, future MLB participant hitting RMSE is
1.8048 versus 1.8233 for the previous current forecast, about 1.0% smaller.
Delivered batting-contribution RMSE is 0.4512 versus 0.4534, about 0.5% smaller.
These are exposed historical development results, not new independent validation.

Playing time is unchanged. On 2,627 identical public matches, PA RMSE is 138.33
versus Steamer's 135.38; average absolute error is 106.41 versus 92.08, 15.56%
worse and outside the predeclared 15% allowance. Converted batting-contribution
error is smaller, but that is not proof of native WAR or park-neutral hitting
superiority. Public archive vintages and environment conversions remain qualified.

Known-cohort PA is 1,228,733 predicted versus 1,270,493 actual across all origins.
Contribution is 4,155.43 predicted versus 4,264.19 actual, with large annual
over- and undershoots. Near-matching 2025 PA totals do not establish accurate
player allocation or consistent league-wide value. The explorer exposes all
seven origin totals rather than only the pooled number.

Hitting-only means league-relative batting wins per 600 PA, excluding replacement.
The observed rate uses the future season's reference; the delivered contribution
label uses the fixed origin reference. Those two observed columns do not directly
multiply into one another. A zero-PA player has unobserved hitting ability, not
zero talent. Totals describe known origin cohorts, not future rosters, new entrants
or contracts. These next-year endpoints do not certify eventual DSL talent or
six-year control value.

## Player checks that prevent an overly positive summary

- Judge, predicting 2025: main hitting rises from 4.53 to 4.94 per 600; actual is
  6.29. PA remains 531 versus 679. Statcast helps this case but does not solve
  either the remaining talent error or workload shortfall.
- Kurtz, predicting 2025: translated hitting improves from -0.06 to +1.02, but
  only 10 PA are predicted versus 489 actual. The earlier comparable workload
  profile has zero people. Calling this a solved elite-prospect forecast would
  be indefensible; actual hitting of 5.15 is also well above the point estimate.
- Bichette, predicting 2025: the precision comparison no longer lets eighteen
  recent minor contacts swamp 1,192 MLB measurements. Its hitting adjustment is
  only -0.019 to -0.021. Yet actual hitting is +2.42 and PA 628 versus 465: fixing
  an integration defect is not the same as predicting the rebound correctly.
- Caminero, predicting 2025: the main MLB branch improves hitting from +0.28 to
  +0.59; actual is +2.18. The unadopted minor measurement comparison lowers it to
  +0.40 despite strong AAA contact. PA is 419 versus 653. This contrary case is
  visible, not hidden by the pooled improvement.
- Belt, predicting 2024: 244 PA expected and zero actual, with actual hitting
  correctly absent. His unexpected failure to find a job is an opportunity miss,
  not observed evidence of bad hitting talent.
- Kwan, predicting 2022: translated hitting is -0.25 versus +1.62 actual and
  116 PA versus 638. Thames, predicting 2017, has no own recent source history,
  uses the untracked fallback, and misses both hitting and opportunity badly.
  International coverage and advancing contact profiles remain real limitations.
- Juneiker Caceres, predicting 2025: the source shows 167 PA at league 130, with
  its broad raw rookie label. There is no future MLB rate to validate his -0.14
  point estimate or eventual talent. Missing draft/ranking/measurement evidence
  and zero supported hitting/workload profiles are shown explicitly.

Eight fixed display walks preserve actual source statistics, all fitted inputs,
selected branch and observed results. The earlier full component reviews and
contrary peers also appear in the player dialog; they are not new confirmation.

## Export and browser verification

Every row and its rate/PA inputs match the saved fitted sources. Thirty-five
chronological held-player cells replay the selected rate and both raw PA heads.
The minor comparisons replay where supported and retain exact fallback elsewhere.
Both actual labels reconstruct from event counts; 244 endpoint score components
were independently checked. Seven focused tests pass. Thirty-one protected files
remain unchanged, and protected 2026 outcomes were not opened.

In the actual browser, season, team, stage, search, ascending/descending hitting
sort, comparison selection, result hiding, non-arrival handling and expanded
player inputs/reviews were checked. The final handoff shows Giants upper minors
for 2025. The browser download-event check timed out; CSV delivery is not verified.
This browser limitation is recorded separately from data and model approval.

Compact evidence, all shared linear heads, eight selected input arrays, receipts,
reviews and screenshots are in
`reports/model-evidence/hitter-integrated-research-explorer`. The approximately
156 MB full display export stays local under
`reports/generated/hitter-integrated-research-explorer/dist`.

Reproduction requires the existing reviewed panels and fitted heads recorded in
the manifest. A fresh export runs
`scripts/build_hitter_integrated_research_explorer.py`, then
`scripts/verify_hitter_integrated_research_explorer.py`; both preserve completed
receipts rather than overwriting them. Serve the existing dist directory with
`python -m http.server 8801 --bind 127.0.0.1 --directory reports/generated/hitter-integrated-research-explorer/dist`.
`scripts/finalize_hitter_integrated_research_explorer.py` preserves the compact
evidence after manual browser review. No reproduction step refits the models.

## Direction from here

Keep the MLB Statcast and prospect branches as useful research candidates. Do
not repeat completed comparisons or promote the uncertain minor overlay. The
overall practical hitter/value goal remains active: playing-time allocation and
elite thin entrants, consistent contribution environments/cohort totals,
minor translation/measurement support, uncertainty, and long-horizon player
value remain unresolved. Use the now-visible sources and misses to choose the
next bounded repair; do not interpret this explorer milestone as solving them.
