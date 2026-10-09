# Small-sample hitting repair: sensible protection, not an accuracy upgrade

2026-10-08. One predeclared change, 35 chronological/player-held fits, unchanged
membership and playing time. This is development evidence for the 2027 build.
The frozen 2026 forecast and explorer have not changed.

The translated event profile now receives the reliability weight the old model
only saw as a separate additive feature. The existing 1,200-PA reliability
constant was used without searching alternatives. All other features remain,
including age, level production and pedigree. Every saved baseline head replays.

## What the comparison says

Among 24,199 never-debut forecasts, 787 have next-year MLB batting observations.
PA-weighted batting-rate error changes from 2.5726 to 2.5858 batting wins per
600 PA: **0.51% worse**, not an improvement. Absolute error changes from 1.9397
to 1.9441, **0.23% worse**. The player-cluster interval for the RMSE difference
is -0.0008 to +0.0328. Fixed-opportunity batting-contribution RMSE worsens 0.16%
and absolute error 1.05%. These are batting-plus-replacement units, not full WAR.

Rate error improves at three of seven origins and worsens at four. The most
recent tested origin, 2024 predicting 2025, worsens 2.55%. Lower-minors rate
error worsens 1.10%, on only 54 measured MLB seasons. The 50–199 effective-PA
group worsens about 12.4%, on twelve observations; the below-50 group has only
one MLB observation. Do not call these thin groups validated because pooled
loss is nearly unchanged. Non-arrivals remain in contribution scoring, but their
unobserved batting quality is not treated as zero.

## Players explain the tradeoff

Rates below are batting wins per 600 PA relative to the measured target-season
MLB environment. Playing-time forecasts are held fixed, so this experiment
cannot repair their large misses.

| Origin/player | Old rate | Repaired rate | Later measured rate | What the calculation shows |
|---|---:|---:|---:|---|
| 2024 Nick Kurtz | +1.02 | +0.14 | +5.15 | Only 50 affiliated PA; the translated profile contributes +0.79 before repair and +0.03 after it. The remaining features do not supply a strong enough advanced-college/prospect estimate. Only four comparable active-training profiles. |
| 2023 Wyatt Langford | +1.44 | +0.98 | +0.55 | 200 PA across four levels. The event contribution falls +0.47 to +0.06, while age/pedigree/other evidence still gives about +0.93. The rate estimate improves. |
| 2018 Pete Alonso | +0.59 | +0.47 | +3.28 | A substantial AA/AAA power record remains in separate inputs, but this repair slightly lowers an already-low estimate. It is the largest contribution deterioration. |
| 2023 Jackson Holliday | +0.83 | +0.71 | -2.84 | Still a large false high. The small improvement is mostly changed coefficients on the other features, not removal of an extreme translated-event term. |
| 2017 Kevin Maitan | -0.38 | -0.10 | Unobserved | No MLB PA the following year. Shrinking negative evidence also raises estimates; this is not a universal downward penalty. There are zero matching active-training profiles, so the talent number remains weakly supported. |
| 2021 Jose Azocar | -1.33 | -1.27 | -1.50 | Ordinary contribution-error case. The batting-rate forecast was reasonable, but 11.7 expected PA versus 216 actual shows that opportunity is a separate limitation. |

All six cases and their 18 origin-only peers were traced through actual source
counts, translation references, features, linear terms, opportunity and outcomes.
The cases collectively cover the fixed diagnostics, largest gain/harm, false
high/low and ordinary active categories; overlapping categories were not replaced
with extra flattering cases. Source comparisons include unsuccessful players,
not just stars. Kurtz's nearby Cam Smith also received about ten expected PA
before actually getting 493; that is an opportunity/profile issue that this
batting-rate experiment did not change. Langford's peers include Matt Shaw,
who did not reach MLB in the tested next season. Alonso's peers Katoh and Basto
also had no next-year MLB observation.

## The known Lovich failure

The nondeployed production probe refits the same historical recipe and examines
the saved **2025 inputs**, without using 2026 outcomes. Lovich's grade moves
from +1.1692 to -0.0774. The specific translated-event contribution falls from
**+1.1445 to +0.0164**. His 26 A-ball PA no longer create nearly his entire
positive hitting grade. The coefficients have not simply recreated that boost.

Concepcion illustrates the opposite direction: the same old-input probe moves
from -0.8217 to -0.1395 as a -0.9207 translated-event contribution shrinks to
-0.0337. This is a reliability mechanism, not an override for Lovich. Neither
number is a newly deployed forecast or a validated current-MLB-equivalent talent
grade for every lower-level player. A next-year conditional MLB rate learned
from those who arrive has selection limits when displayed for distant prospects.

## Decision and next step

**Retain this as a qualified v1 reasonability safeguard, not a claimed accuracy
upgrade or a fully validated sparse-prospect talent model.** Pooled loss remains
within the predeclared 5% practical tolerance, and the known mechanical failure
is genuinely removed. The short-record/advanced-prospect prior remains a visible
weakness; the twelve-observation subgroup and Kurtz prevent an unqualified claim.
No new reliability-weight search is authorized by this result.

Carry the candidate alongside the unchanged anchor into the final integrated
comparison. Do not publish unsupported lower-minor hitting rates as equally
certain/current ability rankings. Retain pedigree/profile estimates and label
their evidence; do not infer that all tiny samples deserve the MLB average.
The next work stays within the finalization plan: finish the 2026 source and
membership refresh and connect the existing nonbatting estimators to the explicit
component ledger, then judge the assembled model and its named-player cases.

The machine evidence is in `reports/model-evidence/hitter-2027-v1/`: provisional
score tables, player/source/coefficient walkthrough and production-probe receipts.
This written review completes their pending baseball interpretation; model
deployment and the overall 2027 goal remain open.
