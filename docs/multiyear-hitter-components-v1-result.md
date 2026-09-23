# Hitter component milestone: what changed

2026-09-22. **A separate, provisional 2026–2028 player-value explorer is ready.**
The original frozen 2026 forecast and the existing multi-year batting and PA
forecasts are unchanged. No 2026 outcomes were opened.

## Main result

Adding the tested component-selection procedure improves error versus leaving
those components out of the existing multi-year batting forecast:

| Prediction | Batting-only forecast, scored against the expanded target | Component procedure |
| --- | ---: | ---: |
| Next year | 0.513 | 0.486 |
| Second year | 0.582 | 0.564 |
| Third year | 0.612 | 0.599 |
| Three-year total | 1.347 | 1.277 |

Numbers are equal-origin RMSE in wins-equivalent: lower is better. Both columns
predict the **same expanded component target on the same players**. This is not
a comparison with the old one-year full/partial-WAR model, nor with FanGraphs.
The three-year reduction is about 5.2%. The paired player-history bootstrap MSE
difference is -0.184, with a 95% interval of -0.271 to -0.086.

**Important limit: only two normal, complete three-year origins remain (2021 and
2022).** Blocking begins in 2018, so the 2016 origin lacks its Year-1 full label.
Annual normal tests have four, four and three origins respectively. Player
bootstrap intervals do not establish robustness across many independent seasons.
The numerical release checks pass, but cumulative subgroup support is below the
three-origin threshold. This is a development release, not confirmation.

Most of the cumulative gain comes from current MLB players (RMSE 2.939→2.742).
Upper-minors improvement is small (1.103→1.098); lower-minors value is almost
unchanged (0.4912→0.4911). All starting minor leaguers are retained, including
players who never reach MLB. Do not describe this as having solved MiLB defense.

## What worked, and what did not

- **Position and running:** recovered methods remain useful in all three years.
  Their component improvements beat neutral with favorable player-bootstrap
  intervals. Removing them from the combined forecast worsens value accuracy.
- **General defense:** the broader native-run history produces a useful MLB
  signal. The earlier-selected procedure improves component and total-value
  error in Years 1–2. Its historical Year-3 forecasts remained neutral because
  earlier selection evidence was insufficient. The final 2025 selector chooses
  the regressed benchmark in all three years; that Year-3 choice remains
  provisional, not a separately confirmed breakthrough.
- **Framing:** useful near-term historical signal, weak longer-range evidence.
  The 2025 selector uses regressed framing in Years 1–2 and neutral in Year 3.
  That zero is an evidence decision, not a biological aging cliff or a claim
  about when full ABS will arrive. The explorer offers a zero-framing sensitivity.
- **Catcher throwing:** component prediction improves near-term, but its small
  contribution slightly worsens integrated error in Years 1–2. It stays visible
  as a provisional challenger component, not a newly confirmed standalone gain.
- **Blocking:** small uncertain Year-1 gain; Year-2 component error is slightly
  worse than neutral. No standalone promotion is supported. Its displayed
  Year-1/2 challenger estimates remain explicitly provisional; Year 3 is neutral.
- **A more flexible direct model did not broadly replace the old recipes.** A
  fixed direct-ridge stack has cumulative error 1.282 versus 1.278 for the
  recovered/regressed benchmark stack. The earlier-fold selector reaches 1.277;
  this tiny difference is not proof that elaborate model selection is valuable.
- The earlier failed MiLB range-to-MLB bridges, catcher deterrence/blocking and
  battery/game-calling additions were **not silently promoted or retuned**.

## What the displayed model is built upon

| Layer | Current implementation |
| --- | --- |
| Year-1 batting + replacement | Existing five-model LightGBM / XGBoost / EBM / ridge ensemble and its missing-data fallback |
| Years 2–3 batting + replacement | Existing direct horizon-specific ridge forecasts |
| MLB participation and PA | Existing all-level opportunity estimates; accepted established-hitter probability update retained |
| Position | Source-only observed role shares; dated transition benchmark; direct future-run ridge selected for Year 1 |
| Steals | Recovered B2_k5 attempt and B2_k45 success methods for Years 1–2; direct total model selected for Year 3 |
| Advancement | Recovered A2_k25 method for Years 1–2; direct total model selected for Year 3 |
| General defense | Three-year 1/.5/.25 MLB native range/arm/DP runs, heavily regressed, scaled by unchanged expected PA |
| Catchers | Separate regressed framing, throwing and blocking; horizon-specific neutral fallbacks |

The new component model has no algorithm or hyperparameter search. Its fixed
ridge has age, level, workload, ordinary hitting/steal rates, position shares,
lagged component runs/rates and explicit availability indicators. It learns
future component totals on **all starting players**, not just eventual MLB
survivors. Native MLB defensive runs are historical measurement labels and
lagged performance evidence; no new pitch-tracking, sprint-speed or exit-velocity
inputs were added. These native measurements do not exist at all minor levels.

Future component labels mature by each fit cutoff; earlier completed out-of-time
folds alone choose each component's model. Pandemic-crossing paths are separate
stress tests and excluded from main fitting/selection. Later 2023/24 component
diagnostics use a different PA proxy and do not enter selection or release gates.

## Measurement corrections and remaining limits

Recovered 2016–2025 native MLB run labels cover over 600 player rows in most years,
versus the old 256 qualified player-position rows in the 2025 bridge target.
Yearless downloads were independently checked against dated defensive exposure;
component sums were checked against published totals. Missing blocking eras and
unmeasured active defenders stay unknown, not zero. Calendar 2020 exposure is
not multiplied into a full season. Historical publication vintages are not
archived, so retrospective metric revisions remain a limitation.

The code audit also found fixed future-trained transition/conversion tables in
some older pooled historical scripts. Those pooled claims are not upgraded to
cutoff-safe evidence. Their 2025-only confirmations keep their narrower scope;
this experiment reconstructs its own dated fits and accounting.

This remains a **component ledger**, not exact FanGraphs WAR. It omits first-base
receiving and a separate GIDP-avoidance running residual. Value and playing time
are not yet jointly reconciled. Nine current players have a direct Year-1
position estimate more than one run outside the simple PA-scaled position
schedule; that diagnostic is not a physical impossibility or a post-hoc haircut.
The underlying PA and direct value forecasts can disagree about implied use.
No reliable whole-model uncertainty ranges are published.

## Explorer and reproducibility

- Local explorer: `http://127.0.0.1:8775/`.
- 3,907 named players; 2025 organization (any batting stint), stage, search,
  component view, year/growth sorting, and framing-scenario controls.
- The 85 multi-organization players appear under every recorded 2025 organization.
  The 187 without 2025 batting stints stay in a visible unknown-organization group;
  this filter is not current rights ownership. Names-only public identity requests
  filled display gaps without changing inputs, affiliations or model decisions.
- Player detail shows every component and future MLB PA/chance. Batting-only
  view is batting **plus replacement production**, not a rate/talent ranking.
- Package: `model_artifacts/multiyear-hitter-components-v1-2026-09-22/`.
- Run the source audit/certification, fit, score, report and verify scripts of
  the same suffix. Source requests stop in 2025; cached local sources are hashed.
- The [research review](multiyear-hitter-components-literature-v1.md) links the
  primary literature and recovered project evidence; the [frozen plan](multiyear-hitter-components-v1-plan.md)
  records the experiment and release boundary.

From the repository root, after the existing multi-year source packages are
available, the reproducible sequence is:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/audit_multiyear_hitter_components_v1.py
.venv/Scripts/python.exe -X utf8 scripts/source_multiyear_native_components_v1.py
.venv/Scripts/python.exe -X utf8 scripts/certify_multiyear_native_components_v1.py
.venv/Scripts/python.exe -X utf8 scripts/fit_multiyear_hitter_components_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_multiyear_hitter_components_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_multiyear_hitter_components_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_multiyear_hitter_components_v1.py
.venv/Scripts/python.exe -m http.server 8775 --bind 127.0.0.1 --directory reports/generated/multiyear-hitter-components-v1
```

The first source step requires network only if its completed-season cache is
absent. Old source-root paths are recorded in the audit and must be remapped if
running on another machine. The report's optional ID/name-only lookup is display
metadata, not a protected-outcome request.

Verification: 30 focused regression/unit tests pass; the read-only artifact audit
checks 168 component fits and 724,521 player/component/horizon predictions,
including chronology, identity, formula recomposition and unchanged batting/PA.
The original 31-file freeze and prior horizon package also verify unchanged.
Browser checks confirm the 35-player Giants upper-minors filter, player detail,
batting-only switch and removal of framing without changing other components.
All 3,907 players have display names. No browser errors were reported in that check.

Next useful work is joint role/exposure consistency and the already-identified
minor-league arrival gap, followed by a separately declared MiLB defensive
translation test using the broader native labels. Do not start another engine
tournament, force a partial cohort to a league WAR total, or reopen weak battery
effects just because the new explorer makes missing components visible.
