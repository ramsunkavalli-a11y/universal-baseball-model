# Empirical anchor repairs elite power but does not beat the working model

2026-10-03. Thirty-five saved fits replay and 15 player reviews are complete.
The [predeclared repair](practical-hitter-v37-contract.md) starts from actual
three-year MLB event counts plus a fixed 100-opportunity league prior, then
learns residual odds with the same V36 likelihood/settings/context. Workload
and all test players are unchanged. See the [before-fit code isolation record](practical-hitter-v37-execution-amendment.md).
No protected 2026 outcomes, frozen forecasts or deployed explorer changes.

## What it accomplished and what it did not

| Rate or value loss | Working V34 control | Naked event model | Simple MLB anchor | Anchored event model |
|---|---:|---:|---:|---:|
| Conditional rate RMSE, wins/600 | 1.82465 | 1.90816 | 1.96423 | 1.88577 |
| All-row contribution RMSE | 0.44060 | 0.45923 | 0.45990 | 0.44969 |
| V24-matched contribution RMSE | 0.90886 | 0.93480 | 0.95272 | 0.93399 |
| Public-matched contribution RMSE | 1.01638 | 1.04874 | 1.08726 | 1.05731 |
| Brief-debut conditional rate RMSE | 2.27810 | 2.28092 | 2.49988 | 2.40681 |

The learned correction beats the simple count anchor, and the anchored model
beats the naked model overall. Neither beats the actual working control.
Anchored versus control rate squared-error change is +0.22681, nominal 95%
player-cluster interval +0.16978 to +0.28463; contribution +0.008087, interval
+0.005092 to +0.011183. Public opportunity loss cannot change in a rate-only
comparison; conversion/knowledge-date qualifications remain in force.

Judge 2024 retains an 8.05% empirical HR anchor and forecasts 6.89%, repairing
the naked model's implausible 3.93%. His resulting batting rate +4.601 is near
the working +4.553, not a substantial new gain. McNeil gets a better contact
estimate and Olson/Acuña retain useful earlier production.

The same anchor is too strong for tiny debuts: Winn's 137 PA get about 58%
reliability and a −3.146 anchor rate; adjustments recover only to −2.522 despite
498 strong AAA PA. Judge's 95-PA debut similarly dominates his longer minor
record. McLain's old strong debut becomes too optimistic. Lux's simple anchor
is good, but the learned adjustment worsens it. Davis still gets an overly
optimistic rebound. Tatis' later zero-PA year and Alvarez's later absence worsen
delivered value without demonstrating irrational origin talent estimates.
Alek Thomas' apparently excellent total still offsets rate/workload errors.

See the [complete source-to-anchor-to-events walkthrough](evidence/practical-hitter-v37/player-walkthrough.md)
and [case ledger](../config/practical_hitter_v37_case_notes.json). These cases
distinguish known representation failures from unpredictable later absences;
do not turn every delivered-value loss into a talent haircut.

## Decision and coherent next step

Do not adopt this fixed-prior anchor/residual specification. Preserve its useful
accounting and source infrastructure, and retain V33b working forecast plus
V34 repaired-source control. This is not a rejection of all component forecasts
or empirically learned event-specific reliability.

Close the current event-model batch rather than tuning the same approach until
it beats exposed results. The stronger existing batting head remains in place.
Next inspect available historical games/role evidence for expected playing time:
equal PA can describe frequent pinch-hitting or fewer games as a starter, which
the current aggregate PA history alone does not distinguish. Audit source
coverage and representative players before fitting that addition. Do not call
games missed an injury diagnosis or promise to foresee future injuries.
