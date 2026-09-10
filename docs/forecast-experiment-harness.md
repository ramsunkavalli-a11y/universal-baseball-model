# Forecast experiment harness

**Status:** reusable guardrail implemented 2026-09-10

Broad searches are allowed, but every search must now freeze and hash its target,
player universe, horizon, incumbent, complete candidate family, selection origins and
outer origin. The harness rejects duplicate candidates, unordered or overlapping
origins, and outcomes that are not fully observable by the declared data boundary.

Every outer comparison must use one unique player row and the same observed outcome
for every model. A second hash records that exact evaluation cohort. Binary forecasts
must be finite probabilities and are evaluated with log loss, Brier error, calibration
and a paired player bootstrap. The conservative promotion helper requires favorable
paired intervals for both proper scores, an accepted calibration review, no material
supported-subgroup failure and genuinely fresh confirmation.

This implements the binding model-search policy in reusable code. It does not make a
demographic, PBP or other feature valid by itself. Features still enter only the
question they can defend: demographics may affect development or opportunity but may
not directly add talent; current physical measurements remain excluded from historical
claims without vintage evidence; skill, opportunity, workload and economics remain
separate until path assembly.

The existing 176-candidate prospect audit was rerun through the harness for hitters
and pitchers across arrival, meaningful role, established role and positive components
given meaningful workload. All eight experiment and cohort hashes are now stored in
the machine-readable result. Scores and selected candidates are unchanged, so no
player value changed. The audit remains retrospective development evidence and still
requires a later untouched confirmation.

The same common-cohort layer now supports continuous outcomes. It records mean scale,
bias, MAE and RMSE, then bootstraps paired squared-error and absolute-error differences.
The linked career replays expose why both views matter:

- the arrival-only pitcher path improves RMSE from `0.558` to `0.551`, but worsens MAE
  from `0.154` to `0.199`; the paired MAE interval is wholly unfavorable;
- the arrival-only hitter path improves MAE from `0.310` to `0.220`, but worsens RMSE
  from `0.955` to `0.978` and worsens absolute mean bias.

Both therefore fail the reusable promotion gate. This protects against optimizing the
many zero/failure outcomes at the expense of the smaller group with material MLB WAR,
or optimizing the tail while making typical player error worse.

The split is concrete. For pitchers who later arrived, the pooled path lowers RMSE
`1.574 -> 1.509`; for the 3,201 non-arrivals it worsens RMSE `0.092 -> 0.166` by
assigning too much expected value. For hitters, the pooled path greatly reduces error
on 2,841 non-arrivals (`0.289 -> 0.087`) but predicts only `0.185` WAR for arrivals
who actually averaged `1.117`, worsening their RMSE `2.556 -> 2.718`. The next useful
career challenger must improve the arrival/quality dependence, not choose one side of
this tradeoff.

A frozen one- through four-year prefix diagnostic shows the same structure at every
horizon. Pitcher candidate MAE is worse in all four prefixes and no paired MSE interval
is reliably favorable. Hitter candidate RMSE is worse in all four prefixes; its later
MAE gains come from moving the majority of forecasts toward zero. The linked-path
failure therefore is not merely long-horizon extrapolation.

A bounded 25%/50%/75% blend sensitivity was then recorded as exposed-cohort research.
For hitters, the 25% linked blend improves every point diagnostic: RMSE `0.955 ->
0.945`, MAE `0.310 -> 0.285`, and absolute bias `0.063 -> 0.027`. Its paired MSE
interval crosses zero and the weight was viewed on development data, so it cannot be
promoted. Pitcher blends improve RMSE and mean bias, but all three reliably worsen
MAE. Preserve the 25% hitter blend as a later frozen challenger; redesign the pitcher
arrival/positive-tail link rather than selecting a compromise after the fact.
