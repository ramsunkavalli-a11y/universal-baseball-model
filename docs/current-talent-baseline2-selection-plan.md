# Current Talent Baseline 2 — multi-season results-only selection plan

Last updated: 2026-08-17  
Status: **PREDECLARED; implement/evaluate without changing the frozen Baseline 1 comparator.**

## Purpose

Baseline 2 is the final simple **results-only** Current Talent baseline required by `docs/current-talent-validation-contract.md` before process, tracking, or scouting evidence is allowed to compete.

It asks one narrow baseball question:

> Does carrying a hitter's translated prior-season result profile into the current-season estimate improve present-talent prediction beyond the frozen season-to-date Baseline 1?

Baseline 2 does **not** add exit velocity, launch angle, bat speed, swing decisions, pitch tracking, scouting grades, prospect rankings, aging curves, playing time, defense, or WAR.

## Frozen comparator

The comparator remains `hl180_ps100_fitted` exactly as frozen in `docs/current-talent-simple-baseline-freeze.md`:

- season-to-date player evidence only;
- 180-day recency half-life;
- fitted training-only environment translation;
- empirical-Bayes prior strength = 100 effective core events;
- Baseline 0 age-band width = 2.0 years;
- Baseline 0 minimum preferred age+level peers = 12.

Do not retune any of those settings during this gate.

## Baseline 2 candidate family

Reuse the existing certified player-game result evidence, translation layer, 12-bin core profile, and empirical-Bayes machinery. The only new candidate dimension is **how far before the current season player-specific evidence is allowed to reach**.

All B2 candidates retain:

- half-life = 180 days;
- prior strength = 100 effective core events;
- fitted translation;
- the same frozen Baseline 0 prior used by the frozen B1 comparator at each cutoff;
- the same target construction, scoring, calibration, and strata rules.

Candidate history windows:

1. `b2_365d` — all eligible player-game evidence in the 365 days before the cutoff, exponentially weighted with the frozen 180-day half-life;
2. `b2_730d` — all eligible player-game evidence in the 730 days before the cutoff, exponentially weighted with the frozen 180-day half-life.

The frozen B1 season-to-date profile is the reference and is **not** counted as a B2 candidate.

Why only these two candidates: the gate is intended to test whether prior-season result history has incremental value, not to launch another broad hyperparameter search. A 365-day window gives roughly one year of history; 730 days permits a second prior season where certified history exists. The 180-day decay keeps very old events from receiving equal weight merely because the window is longer.

## Isolation rule

To make the comparison interpretable, B2 changes **player-specific history only**.

At each cutoff:

1. construct the frozen B1 season-to-date translated player evidence;
2. construct Baseline 0 from that frozen B1 evidence/context exactly as before;
3. score frozen B1 using that Baseline 0;
4. construct each B2 translated player profile from its longer history window;
5. shrink each B2 player profile toward the **same frozen Baseline 0 prior** with the same prior strength of 100.

Do not recompute a different age/level population prior from the longer B2 history. Otherwise the experiment would mix a player-history change with a population-prior change.

## Chronological development / confirmation

Certified multi-season evidence currently begins in 2021, so the first B2 test must start in 2022 rather than pretending earlier history exists.

### Development folds

Use only:

- 2022-07-15;
- 2022-08-01;
- 2022-09-01.

Predictor evidence may use certified 2021 data plus eligible 2022 events strictly before each cutoff.

Select between `b2_365d` and `b2_730d` using:

1. primary: equal-fold mean event-weighted multinomial log loss;
2. secondary: equal-fold mean event-weighted multinomial Brier score;
3. calibration, components, levels/strata, and coverage as guardrails.

No 2023 alternative-candidate results may be used to select the B2 window.

### Confirmation folds

After one B2 candidate is selected on 2022, evaluate only:

- the selected B2 candidate;
- frozen B1 `hl180_ps100_fitted`;
- Baseline 0 as the common simple prior/reference where required by diagnostics;

on:

- 2023-07-15;
- 2023-08-01;
- 2023-09-01.

Predictor evidence may use certified 2021–2023 events strictly before each cutoff.

Do not evaluate the losing B2 candidate on 2023. Do not reselect on 2023.

## Promotion rule

Promote B2 only if all of the following hold:

1. selected B2 has lower equal-fold mean 2022 log loss than frozen B1;
2. selected B2 does not materially worsen 2022 Brier score or calibration;
3. the 2022 advantage is not produced by a structural coverage change;
4. the selected B2 candidate retains a lower mean log loss than frozen B1 on the three 2023 confirmation folds;
5. no major evaluated level/evidence stratum shows catastrophic harm.

If the selected B2 candidate fails confirmation, **keep frozen B1 as the simple Current Talent baseline**. Do not search 2023 for a different history window.

A tiny numerical edge that is unstable across folds/strata is insufficient reason to add complexity; the validation contract explicitly prefers the simpler model when gains are negligible relative to fold variation.

## Coverage boundary

This B2 gate is deliberately results-only and therefore uses the same certified result-profile coverage as B1. It should not create a new league-availability problem.

The first richer process/tracking challenger comes **after** B2. For that later gate, structural feature availability must be modeled explicitly by source-capability tier / league rather than fabricating missing lower-level features or silently dropping evidence-poor leagues. A richer feature may be useful only in MLB or selected affiliated leagues; that is allowed, but its validation must distinguish:

- universal frozen-results estimate available everywhere;
- richer-data estimate where the feature is genuinely observed;
- fallback to the universal estimate where it is not;
- separate scoring by capability tier so an MLB-only gain cannot masquerade as universal improvement.

## Implementation constraints

- Reuse `EvidenceWindow` and the existing translated player-evidence pipeline; do not create a second result-profile engine.
- Multi-season input concatenation must preserve canonical player-game grain and reject duplicate season/game/player rows.
- Translation remains training-only and leakage-safe at each cutoff.
- B2 must use the same 12 core bins and target environment projection as frozen B1.
- Keep heavy historical materialization/evaluation manual-only after the gate is complete; deterministic unit tests remain in normal CI.
- Do not begin process/tracking source acquisition until this B2 results-only gate is either frozen or explicitly rejected.

## Immediate implementation batch

1. add a deterministic multi-season universal-evidence combiner/loader path that reuses already certified season artifacts;
2. add B2 candidate construction that shares the frozen B0 prior and differs from B1 only in the player-history window;
3. unit-test chronology, history-window inclusion/exclusion, shared-prior isolation, and duplicate-grain rejection;
4. only then wire the 2022 development workflow.
