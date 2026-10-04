# Prospect hitting evidence improves modestly without solving player value

2026-10-03. Rankings plus historically fitted level translations improve the
linear model's future MLB hitting predictions for debutants. The improvement
is modest, and its effect on delivered value remains uncertain. Retain this
as a tested hitting alternative for the practical model's integration step;
keep the V68/V53/V63 candidate and existing research explorer unchanged.
Protected 2026 and deployment remain untouched. The overall goal is active.

## What changed and what was actually tested

The [locked comparison](hitter-talent-bridge-v74-contract.md) adds nine fresher
ranking inputs to the existing 199-input hitting head, then adds twelve inputs
describing coherent translated events and their exposure. A third arm uses
the same inputs with a small fixed tree model. Playing time does not change.
Each translation is fitted separately for the held player group and each
feature row's own historical cutoff, including training rows. No final modern
translation lookup is imported into early history. Individual rookie buckets,
DSL and short-season data remain distinct. RK134 has no usable connection;
its evidence is marked unsupported rather than assigned an invented offset.

All 30,506 forecast identities, exits and non-arrivals remain. There are 105
new hitting heads, 210 full/active preflight checks, 35 original-head replays,
and an independent replay of all 105 new heads. Nine source examples were
saved before fits. Graph support is not equivalent to sufficient conditional
MLB training support: the detailed Kurtz and Langford intersections have zero
active examples, Maitan has zero broad examples, and several older prospect
profiles have fewer than twenty. These people remain in scoring.

This is development evidence from already exposed years. The graph pools
park/opponent context and selected movers; it is not a fully park-neutral MLE.
Ranks describe overall prospect standing, not a dedicated hitting grade.

## Correct response units matter

The first scorer inherited an origin-centered evaluation label while describing
it as the future-season-centered training label. It also compared rates with
season-value bounds, then failed on a console label after saving all outputs.
The [unit correction](hitter-talent-bridge-v74-score-unit-correction.md) preserves
those artifacts and independently reconstructs the intended response from actual
counts. No fits or predictions change. The primary figures below use the target
declared before fitting: batting wins per 600 PA above the realized future MLB
average. Common-origin scores remain a separately labeled sensitivity view.
All initial scores were independently recomputed, and all forecasts pass the
correct, deliberately broad mathematical rate bounds. That is not a baseball
validation claim. Regression examples reproduce both unit distinctions.

## Matched results

There are 787 debutants with observed MLB batting. Rate scores give equal
weight to years and actual PA within each year. Delivered-value scores retain
all 24,199 never-debuted forecasts, including zero MLB outcomes, and use the
same common-origin event-value reference and fixed opportunity forecasts.

| Hitting model | Future MLB hitting RMSE | Delivered-value RMSE |
| --- | ---: | ---: |
| Existing | 2.6144 | 0.152257 |
| Add rankings | 2.6002 | 0.151956 |
| Add rankings and translated events | 2.5831 | 0.151662 |
| Same inputs with trees | 2.6021 | 0.151835 |

The translated linear bundle improves rate RMSE by about 1.2%. Its paired
rate MSE difference is -0.1627, nominal 95% player-clustered interval
[-0.3011, -0.0560]. The ranking-only interval also favors improvement. Tree
rate uncertainty includes no improvement. These are nominal development
intervals across a bounded comparison, not untouched-test confirmation or
proof that translation alone caused the gain.

Delivered-value improvement is about 0.4% in RMSE. Its paired MSE difference
is -0.000181 with interval [-0.000418, +0.000038]. That does not establish
a reliable whole-player-value win. The equal-active-observation rate sensitivity
also improves, from 5.0512 to 4.9988, but tiny MLB samples make that much noisier.

Upper-minor active rate RMSE improves 2.5914 to 2.5632. Lower-minor active
rate improves 3.2655 to 3.1791, but there are only 54 observed active rows
and almost no direct next-year MLB evidence for ordinary DSL players. Only
eleven new draftees and eight thin-professional-sample players supply observed
rates. Do not turn their favorable pooled figures into broad talent certification.

## Annual paths and totals still expose problems

| Origin | Existing rate RMSE | Translated linear rate RMSE | Predicted value total | Actual value total |
| --- | ---: | ---: | ---: | ---: |
| 2016 | 2.9145 | 2.8388 | 25.98 | 21.28 |
| 2017 | 2.4880 | 2.4896 | 20.36 | 23.57 |
| 2018 | 2.7572 | 2.7123 | 24.04 | 64.28 |
| 2021 | 2.5018 | 2.4911 | 28.72 | 35.36 |
| 2022 | 2.6220 | 2.5842 | 31.98 | 31.07 |
| 2023 | 2.5183 | 2.5496 | 36.52 | 5.12 |
| 2024 | 2.4663 | 2.3895 | 27.06 | 34.07 |

These are identical never-debuted cohorts; values are custom batting plus
replacement, not full WAR. Hitting does not improve every origin, nor repair
the 2018 shortfall, 2023 overprediction or 2021 readiness deficit. Playing-time
totals are unchanged by construction. On the 2,627 matched current hitters,
PA RMSE stays 138.33 versus Steamer 135.38, and MAE stays 106.41 versus 92.08.
The 15.56% MAE gap still misses the practical plan's 15% target. Public event
forecasts retain their original environment/date qualifications; the corrected
relative response is not used to invent a clean named-system talent win.

## Sixteen real player reviews

The complete [stats to forecast walkthrough](../reports/model-evidence/hitter-talent-bridge-v74/player-walkthrough.md)
and [machine-readable cases](../reports/model-evidence/hitter-talent-bridge-v74/reviewed-cases.json)
retain all fixed and outcome-selected examples, original failures and four
origin-selected peers per case. Already debuted cases receive an additional
MLB-quality/exposure peer check after the original minor-PA/rank rule proved
a weak match; original peers remain and no forecast changes.

- Kurtz rises from -0.063 to +1.024 hitting wins per 600 PA, using his 50 PA
  and ranking rather than assuming a full sample. His expected playing time
  is still ten PA before 489 actual. The sparse-support warning is material.
- Langford rises +0.688 to +1.439, overshooting his modestly above-average first MLB
  season. His actual 557 PA still greatly exceed the fixed 215 expected.
- Julio rises +0.754 to +1.216, moving toward actual MLB hitting. His rankings
  help more directly than the translated block, which has a negative net term.
- Alonso improves only +0.286 to +0.592 before a major breakout. His translation
  block contributes almost zero to the new linear sum; refitted original terms
  and rankings also matter. The model still underrates his first MLB season.
- Holliday is retained as the largest linear harm. Trees reduce his hitting
  estimate, but fixed PA and rate still overpredict his first MLB contribution.
  One difficult debut is not a reason to penalize all top young prospects.
- Trees help Merrill and hurt Chourio. Same-fit probes show that Merrill's gain
  is not simply a beneficial translation adjustment, while Chourio's pooled
  translated profile elicits a harmful tree response. Earlier low-level history,
  development, selected movers and context deserve caution, not a blanket ban.
- Maitan's strikeout-heavy production tempers ranking optimism, but his zero
  MLB PA cannot validate the forecast of hypothetical MLB hitting. Judge and
  Winn retain their existing forecasts in the primary assembly. The tree's
  all-player sensitivity compresses Judge despite extensive MLB evidence.

## Disposition and next work

The player checkpoint is complete; execution, support, predictive evidence and
deployment remain separate. Keep the translated linear alternative available,
not discarded because the whole-model interval is uncertain. Do not replace
the established hitting branch with this tree or begin another parameter sweep.
The current candidate remains unchanged and the whole goal is not complete.

Next follow the practical plan's integration step: one bounded comparison of
delivered contribution that uses this tested talent evidence alongside opportunity,
rather than assuming the product of independently fitted averages is finished.
Audit response units explicitly at that boundary, retain the original candidate
and this rate/value decomposition, preserve all non-arrivals, and inspect the
same consequential players and origin totals. No blanket Belt/unsigned penalty,
no protected 2026 access, and no new college-data collection.
