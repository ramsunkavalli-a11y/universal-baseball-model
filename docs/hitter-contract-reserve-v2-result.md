# Contract opportunity and pitcher-batting reserve: checkpoint result

Completed 2026-09-22 under the [frozen plan](hitter-contract-reserve-v2-plan.md).
Two distinct outcomes: corrected reserve accounting tested; contract feature test
blocked by historical source coverage, not rejected on predictive performance.
No production forecast, hitting rate, explorer or protected 2026 outcome changed.

## Pitcher batting: the reserve is better, the allocation still fails

The old outsider reserve mixed incoming/unlisted hitters with pitchers taking
batting turns. A conservative historical proxy now removes pitcher-slot PA from
the universal-DH reserve: >=100 batters faced and <200 batting PA in that completed
historical season. The high-batting-volume guard preserves two-way hitter use.
This is an approximation, not an exact PBP classification of defensive roles.

Only origins 2022 and 2023 receive this correction, because the universal DH was
known at their year-end cutoffs. Do not retroactively assume it at year-end 2021.
The remaining outsider reserve uses only mature earlier cohorts; batting ability,
participation, calibration groups and every v1 allocation parameter stay fixed.

| Year being predicted | Old outsider reserve PA | Corrected reserve PA | Actual outsider PA |
|---|---:|---:|---:|
| 2024 | 7,282 | 2,214 | 2,981 |
| 2025 | 6,262 | 2,118 | 2,290 |

The correction improves fixed-rate value errors versus the **failed old-reserve
allocation**, with paired MSE difference -0.001333 and player-cluster interval
[-0.002454, -0.000248]. That does not establish improvement over the accepted model.

Across 8,248 player/origin rows in those same two tests:

| Measure, lower is better | Accepted PA | Corrected-reserve group allocation |
|---|---:|---:|
| PA RMSE | 87.622 | 87.281 |
| Fixed-rate partial-value RMSE | 0.49699 | 0.49902 |
| Top-50 PA RMSE | 213.57 | 228.89 |
| Top-50 partial-value RMSE | 2.1217 | 2.1777 |
| Under-26 top-50 PA RMSE | 161.94 | 165.90 |

Overall PA improves in both tests but its paired MSE interval [-156.85, +43.77]
includes zero. Fixed-rate value worsens in both (MSE difference +0.002018,
interval [-0.000547, +0.004621]); top/young-top guards fail. Only two rule-known
origins are available, below the three-origin promotion requirement. Keep the
reserve separation as accounting groundwork, **not a delivered PA adjustment**.
Matching the league total still does not identify which hitters deserve the PA.

Value here is batting plus replacement at the identical independently estimated
rate, not full WAR. The separately delivered direct-value RMSE is 0.50069 and is
not substituted or rescaled. These exposed development years and player-cluster
intervals do not measure uncertainty over future season shocks.

## A useful additional historical replay

Reconstructed accepted-v2 Year-2 opportunity at origin 2023, forecasting 2025.
The exact adapter first reproduces saved origin-2022 probabilities, conditional PA
and expected PA within rtol 1e-8 / atol 1e-7. It reuses the original hurdle and
accepted established-player probability update; no new model selection. The
4,093-player origin-2023 replay is now saved for subsequent comparisons.

## Contracts: loaded, but not a historical training panel

The user was correct that earlier work loaded these data and attached contract
costs. The audit finds:

- The current normalized payroll liabilities come from the 2026 team workbooks.
  These can support that dated economics layer, not earlier forecast inputs.
- The Cot's bridge contains 1,289 player records, 1,192 accepted identity matches,
  and 6,445 annual cells covering 2025–2029. The extract was created January 31,
  2026, and lacks signing/amendment dates needed to reconstruct older information.
- The 2023–2025 Opening Day tables contain service, options and roster-role fields,
  not salary or remaining guaranteed money. Projected workload is not a salary.
- The user confirmed that no earlier payroll files were loaded. A public 2023
  FanGraphs payroll page check returned HTTP 403; no bypass was attempted.

Assigning contract costs to all players can include CBA-based minimum/arbitration
estimates. That is not evidence of observed historic salary/guarantee coverage.
Neither current contracts nor costs derived from our own projected performance
can be silently treated as independent historical salary evidence.

The source gate therefore allows **zero** chronological contract-model training
or test origins from these loaded sources. No salary challenger was fitted, and
no statement that contracts fail to help is justified. No private player-level
contract records were added to GitHub. The audit publishes aggregate counts,
schema/timing findings and local source hashes only.

## Next action

Obtain earlier payroll snapshots or a certified signing/amendment history, with
stable IDs, released/retired players retained, known-as-of dates, guaranteed versus
option years, and explicit missing/unsigned states. Use a single predeclared test
of salary/remaining commitment beyond performance, age and PA history. A later
snapshot can qualify only if its historical event reconstruction is independently
certified, not because the text mentions an old contract start year.

FanGraphs describes historical-season payroll views in its
[2025 payroll-page announcement](https://blogs.fangraphs.com/the-2025-rosterresource-payroll-pages-are-live/);
those are a possible acquisition route, not certified cutoff-safe data yet.
Do not keep tuning the failed stage/PA allocation while this missing input is
unresolved. The older no-contract forecast remains the comparison benchmark.

## Artifacts and reproduction

`model_artifacts/hitter-contract-reserve-v2-2026-09-22/` contains compact scored
rows, the extra accepted replay, group/age/ledger results, source hashes and the
separate contract-source audit. Run:

```
scripts/test_hitter_dh_reserve_v2.py --verify
scripts/audit_hitter_contract_opportunity_sources_v1.py --verify
```

Omit `--verify` to reproduce. Five new tests cover historical pitcher removal,
two-way protection, rule timing, future-data isolation and contract-date gates.
Both original freeze and delivered-v2 hash checks remain required.
At this checkpoint both hash checks pass, all new files pass lint, and the combined
focused model/contract suite passes 76 tests.
