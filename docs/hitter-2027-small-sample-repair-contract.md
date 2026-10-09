# One bounded repair: translated hitting evidence must reflect sample size

2026-10-08, before fitting. Part of the 2027 v1 finalization plan; no new model
tournament and no changes to frozen 2026 artifacts.

The documented Lovich failure is a representation defect: 26 Single-A PA can
create an extreme translated event profile. The existing linear model receives
reliability as a separate additive input, which cannot directly scale each event
coefficient by that reliability. This test makes that interaction explicit.

Candidate: multiply the eight centered translated event inputs by the existing
`supported_PA / (supported_PA + 1200)` reliability. Retain every other feature,
the translation graph, pedigree, samples, weights, Ridge alpha=100 and feature
scaling. No new shrinkage strength is searched. In probability space this is a
mixture of the translated profile and its existing origin/held-player MLB
reference; it does not discard level, age or pedigree predictors. Refit with
the same representation in training and testing, rather than editing a player's
prediction after seeing his results. The old model is reproduced on every fold.

Population: the saved 30,506 chronological held-player evaluations from V74,
with the same 35 training/test partitions. Only never-debut deployment changes;
incumbent predictions and all playing-time predictions stay fixed. Training
targets are future MLB batting rate conditional on observed PA, using the
existing positive-PA weighting. Non-arrivals stay in delivered-value scoring;
their batting quality is unknown, never labeled average or zero. These exposed
historical seasons are development evidence.

Before fits, rerun the existing fold preflight and count distinct active-training
players by stage, debut status, age band and supported translated exposure
(<50, 50–199, 200–599, 600+). Save unsupported cases, not drop them. Compare
candidate/old feature ranges. No transformation can use a later year or held
player to refit the saved translation graph.

Main measures: PA-weighted future-relative MLB batting-rate RMSE and MAE among
never-debut players who appear; unweighted rates and fixed-opportunity delivered
batting-plus-replacement errors alongside them. Keep target units explicit and
also report the common-origin environment sensitivity rather than mixing them.
Report years, upper/lower minors, draft status and exposure bands; 2021 is a
separate stress year. No claim of full-WAR improvement from this batting test.

Use the finalization plan's 5% incumbent-baseline guardrail on both rate RMSE
and MAE and delivered-value RMSE/MAE, but don't adopt a candidate solely because
it is within that tolerance. A reasonability repair can be useful with roughly
unchanged accuracy. Material subgroup harm needs a baseball explanation before
release. Tiny-sample predictions must lose the extreme translated-event push;
the refit must not simply restore it by exploding coefficients.

After scores, inspect the largest gain, harm, false high, false low and an
ordinary active player, plus fixed Kurtz (2024), Langford (2023), Maitan (2017)
and Holliday (2023), with origin-only peers and source-to-linear-contribution
calculations. Probe Lovich's saved 2025 inputs using the same refitted 2025-origin
production recipe without changing the frozen forecast. Do not substitute his
2026 performance as a tuning objective or claim this tests eventual DSL talent.
Disposition follows the walkthrough; a losing honest comparison does not
invalidate shrinkage generally or authorize another arbitrary weight search.
