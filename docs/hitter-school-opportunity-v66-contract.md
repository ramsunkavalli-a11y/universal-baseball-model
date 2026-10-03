# Test recovered school background in next year playing time

2026-10-03 before fits. Test the reviewed cached-school overlay against the
retained next-year hitter opportunity system. Does seeing older college/HS/JC
backgrounds more consistently improve future MLB use without creating excess
prospect jobs? This is not a new algorithm competition or a guarantee for named
college stars.

Keep the exact 63,282 source identities, 30,506 evaluation identities, 35
chronological whole-player folds and retained mature training memberships.
Exclude target 2020; flag the missing minor season and reorganization as before.
Sources and all labels remain unchanged. The candidate replaces only
draft_hs, draft_jc and draft_college with the reviewed broad-background indicators.
All other 248 opportunity inputs, including precise draft_class_unknown, remain
exactly retained source values. Precise class can be unknown while broad college
background is known. Do not invent school years, classify aliases, infer an
unknown international signing as zero talent or collect new college data.

Institution classification uses only non-outcome cached pick metadata dated no
later than each origin. It does not use future performance or later school
records for earlier origins. This is an external metadata lookup, not a
target-learned preprocessing step. Its reconstructed historical dating and
exact-name ambiguity qualifications remain. Preserve unknown backgrounds.

Use the same histogram boosting classifier and conditional regressor: 250
iterations, depth 3, minimum leaf 30, learning rate .05, L2 10, no early stopping,
seed 31. Equal-origin training weights within each head; conditional PA trains
only on earlier active MLB outcomes. Bound conditional PA [1,800]; retain exact
hard-unavailable/retired policies. No tuning or post-result subgroup blend.
Hitting is held exact V53. Compute offense using the reviewed corrected V63
common-origin reference. It is batting plus replacement, not full WAR.

Before all seventy fits, verify source hashes, column-level isolation, chronology,
player separation and broad/refined background-entry training support separately
for participation and active-PA heads. Retain sparse/unsupported players in
headline scores. Replay all seventy saved baseline heads from their actual inputs
and all seventy candidate heads before interpreting differences. Profile counts
are warnings, not individual confidence intervals.

Primary: equal-origin delivered-offense MSE on all retained identities. Also
report PA RMSE/MAE/bias, appearance Brier/log loss, raw PA/appearance/value totals,
2,627 matched public forecasts, never-debut upper/lower groups, existing MLB,
recovered-school rows, first-year top picks and every origin. Report paired
whole-player nominal 95% development intervals, not untouched confirmation.
No automatic acceptance for a tiny pooled gain. Meaningful readiness improvement
must coexist with sensible lower-minor allocation, adequate ordinary/established
performance and no new major forecast mechanism error. Public practical thresholds
remain 10% RMSE/15% MAE versus Steamer, not redefined after fitting.

Fixed reviews: Kurtz 2024, Langford 2023, Bellinger 2016, Alonso 2018, Salas 2024,
Moniak 2016, Swanson 2016 and Burger 2017. Add largest offense gain/harm, false
high/low and an ordinary active case using fixed score ordering. Select four
same-origin stage/debut peers by known age, exposure and draft-rank distance,
without outcome selection. Trace raw stats, actual old/new flags and dated
institution evidence, support, saved classifier/regressor paths, probability,
conditional PA, product, fixed hitting, offense and reality. Fixed-fit school
reversion probes explain mechanics only, not a deployable model or causal effect.

No disposition or next modeling experiment before the actual player review.
Keep the coherent research candidate if this source substitution fails, but do
not discard the recovered facts or reject all prospect information. No protected
2026 outcome access or frozen/deployed forecast changes; no automatic promotion.
