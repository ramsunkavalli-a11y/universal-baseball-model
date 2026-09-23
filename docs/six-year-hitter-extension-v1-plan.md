# Six-year hitter extension — frozen before fitting

Date: 2026-09-22. Scope: the same 3,907 hitters, evidence through 2025 only.

The user's objective is the full six-year MLB control period. Six future calendar
seasons are a necessary forecast layer, **not** a substitute for that objective.
Do not call a 2026–2031 sum controlled value, grant established players six fresh
service years, or treat minor-league seasons as consuming MLB service.

## First implementation

1. Preserve every existing Years 1–3 forecast. Extend annual batting + replacement
   and playing-time predictions to Years 4–6 using the recovered 2009–2025
   all-level panel, including non-arrivals in the starting denominator.
2. Compare fixed Ridge (alpha 20, existing full features) against the same Ridge
   using age/level/workload features only. Also compare a horizon-3 carry-forward
   fitted at the SAME historical cutoff. No tuning or best-year selection.
   Annual target labels must mature by the forecast cutoff. Training excludes
   paths crossing 2020. Score those test paths separately, never inflate 2020
   calendar value or PA. Report player-disjoint sensitivity, stage-specific
   errors, mean bias, and origin support. All results are development evidence.
3. Refit the established PT_FORM_U hurdle at each long horizon. This is an
   extension candidate, not evidence that the accepted Years 1–3 PA corrections
   also work at longer horizons. Do not import the failed opportunity challenger.
4. For the added components, evaluate the existing fixed historical benchmarks
   at horizons 4–6 against neutral. Do not select a new defense recipe using
   the test results. Missing native labels stay missing. Publish benchmark
   component scenarios alongside batting-only values, explicitly provisional.
5. Add a separate control accounting layer. A service year is 172 days; six
   service years determine statutory eligibility at season end, not midseason.
   Partial years can extend the calendar window; MLB injured-list service can
   accrue without PA. No-debut evidence permits a zero opening balance; missing
   evidence does not. Contract extensions, non-tenders, and ownership retention
   are separate from statutory eligibility.
6. Expose six calendar years, team filter, component breakdown, exact/unknown
   opening-service status, and an explicit unresolved controlled-value field.
   Never fill an unmodeled post-2031 prospect tail with zero.

## Evidence gates and remaining work

Years 5–6 have no normal full-path outer test in the recovered annual panel:
the mature later cohorts cross 2020. Native defense starts in 2016 (blocking
2018), limiting long-horizon component tests further. An expanded display is
not a validation pass. Report this prominently, not only in a footnote.

Full control value additionally requires a validated joint path of MLB arrival,
participation, injury/service accrual, production, and exit. The earlier workload
to service map improved observed service estimates, but whole-career endpoint
error and missing zero-workload/absent-next-tracker cases remain unresolved.
Implement and test the accounting now; do not silently promote that map.

Acceptance for this implementation: unchanged old forecasts/freeze; all new
annual outcomes strictly through 2025; reproducible tests/fit notes; no future
target converted to zero; no unsupported six-service-year total displayed.
The user's full control-value objective remains open until the joint-path and
tail validation is complete.

Primary rules: [MLB service time](https://www.mlb.com/glossary/transactions/service-time),
[MLB free agency](https://www.mlb.com/glossary/transactions/free-agency),
and [2022–26 CBA](https://www.mlbplayers.com/_files/ugd/4d23dc_d6dfc2344d2042de973e37de62484da5.pdf).
See existing `team-control-methodology.md`, `prospect-controlled-value-rebuild-plan.md`,
and `prospect-cumulative-service-mapping-result.md` for recovered work and failures.
