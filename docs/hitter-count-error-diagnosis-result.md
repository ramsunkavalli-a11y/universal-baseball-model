# What the completed count comparison actually lost

2026-10-05. No new fits, forecasts, playing-time changes or 2026 outcome access.
This is a diagnosis of the exposed 2016–24 origins predicting 2017–25 MLB
performance, excluding the canceled 2020 target. Retain the incumbent.

The count replacement improved overall event-probability scores and got pooled
homers close to reality, but it did not place enough of that production on the
right players. Hitting RMSE rose from 1.80481 to 1.81347; delivered
batting-plus-replacement RMSE rose from 0.43513 to 0.43811. That is not full WAR.
The [original result](hitter-count-baseline-result.md) remains unchanged.

## This is not just a playing-time problem

For a player who actually bats in MLB, the delivered forecast error equals
hitting error at expected PA plus PA error valued at observed hitting. Both
models have exactly the same expected PA. We can therefore separate the change
in squared hitting error, its interaction with workload error, and the separate
error change for players who do not appear. We never assign absent players a
zero hitting-ability label. This is retrospective explanation, not information
the model can use at forecast time.

Across the original 30,506 forecasts, using unchanged equal-origin row weights:

| Part of delivered mean-squared error change | Count minus incumbent |
| --- | ---: |
| Squared hitting error at expected PA | +0.00463328 |
| Interaction with unchanged workload error | −0.00234469 |
| Non-arrival error | +0.00031149 |
| Total | +0.00260009 |

Positive means worse. Hitting gets worse even when the jobs forecast is held
fixed; workload errors hide some of the damage. Improving playing time is still
important, but it cannot by itself explain or certify this hitting replacement.

## Where the loss comes from

The following are contributions to the **same global score**, not independently
reweighted subgroup RMSEs. Each section partitions the original population.
Do not add different sections together: they describe overlapping players.

| Recent MLB evidence, normalized 1/.8/.6 recency-weighted PA | Forecasts | Active labels | Global delivered MSE change |
| --- | ---: | ---: | ---: |
| None | 24,852 | 803 | −0.00037470 |
| Under 200 | 2,226 | 920 | −0.00023326 |
| 200–599 | 1,433 | 994 | −0.00002680 |
| 600–1,199 | 1,386 | 1,226 | +0.00172872 |
| 1,200 or more | 609 | 595 | +0.00150614 |

The last two groups contribute +0.00323486—more than the overall loss because
other groups offset some of it. This is not only a handful of rookie misses.
Their own hitting RMSEs worsen from 1.63471 to 1.65542 and 1.38894 to 1.42835.
The 600–1,199 group worsens in hitting in five of seven origins, including
2016–18; the largest-exposure group also worsens in five. A 2021-only explanation
does not fit the evidence.

It is not simply excessive optimism about high-strikeout sluggers either.
Among players with at least 200 weighted recent MLB PA, both 4%-plus homer
groups and the below-4% group contribute losses. The below-4% group contributes
+0.00227598, compared with +0.00021908 for high-HR/high-K and +0.00071300 for
high-HR/lower-K. These are descriptive raw MLB profiles, not park-neutral talent
classes or a warrant to create a post-result branch.

The 30,253 original forecasts without NPB/KBO history contribute +0.00257058,
or 98.9% of the net overall loss. Fixing the overseas examples alone will not
repair the full result. Lower-minor next-year gains also do not validate lifetime
talent: the current dominant DSL group has **zero** next-year MLB hitting labels.

## A second, smaller but genuine overseas problem

The provisional foreign past baseline transfers local dominance, not a proven
MLB equivalency. The learner must correct it. In the actual saved fits for Suzuki,
Lee and Yoshida, the fixed penalty dominates the individual foreign-share
coordinates: penalty/data diagonal curvature ratios for HR range from about
50 to 285, versus 14 to 56 for K. Likelihood and penalty gradients nearly cancel.
This is coordinate geometry with correlated covariates, not an effective
posterior sample size or proof that removing the penalty would win.

Suzuki's NPB HR-versus-other coefficient contrast is −0.02140. At his 52.2%
NPB share it contributes only about −0.01117 to the HR-versus-other log odds.
Lee's KBO contrast contributes about −0.00163; Yoshida's NPB contrast about
−0.00306. Common covariates can still change their forecasts, but these small
league-specific corrections cannot be called established league translations.
The active NPB/KBO training people are few; never-debut active foreign players
are fewer still. The [player review](hitter-count-error-diagnosis-player-review.md)
shows why seemingly good delivered values can conceal this problem.

## What this diagnosis establishes—and does not

Confirmed: original forecasts and PA are retained; exact error identities and
overall scores independently replay; all twelve group families partition the
same global change; thirteen additions have a separate count-only decomposition;
all thirteen prior source/model walks remain linked and reviewed. At join time
the authoritative forecast replacement reference is used rather than stale
feature-matrix scoring metadata (maximum discrepancy 0.00000254164 per PA).
That discarded metadata is not a talent input; no fit or forecast was repaired.

Not established: which coupled modeling change caused the mature-MLB loss.
The replacement changed production representation, removed four MLB-quality
features along with old pooled rates, imposed a common 1,200-PA prior, and used
an eight-event count likelihood. Its likelihood also weights future PA whereas
the prior scalar rate fit has its own weighting. Near-correct aggregate homers
do not distinguish those mechanisms. Khris Davis's error is genuine hitting
overprediction, while Judge 2023 improves; neither justifies a player-specific
rule. The small exposed gain in some prospect groups is not independent
validation or permission to splice favorable arms together.

## One coherent next checkpoint

There are two priorities, not a new feature menu:

1. **Main question:** can these same past-only inputs predict future MLB batting
   value better when learned directly, rather than through the present event
   likelihood? The next contract should hold the source matrix, fold membership,
   eligibility, PA and original anchors fixed and compare direct-rate learning
   with the saved count model. Declare any output/penalty/weighting differences
   explicitly; a win would not by itself identify which removed feature mattered.
   Review mature-MLB cohorts, all origins and the retained thirteen players before
   disposition. No algorithm tournament, guessed blend or subgroup hybrid.
2. **Separate context issue:** the sparse overseas controls are not a sufficient
   MLB translation. Preserve the raw histories, but qualify that integration.
   Do not tune a foreign penalty on these famous cases or let a narrow foreign
   repair substitute for the main question. A future adjustment needs a
   cutoff-safe, explicitly supported league-calibration contract.

The present diagnosis is complete, not an accuracy improvement. The incumbent,
team-filtered explorer, both frozen packages and the already completed one-time
2026 evaluation remain unchanged. The long hitter goal remains active.

Reproduction: `scripts/diagnose_hitter_count_errors.py`,
`scripts/qualify_hitter_count_error_diagnosis.py`, and the generated
`hitter-count-error-diagnosis` receipts. Public compact evidence is under
`reports/model-evidence/hitter-count-error-diagnosis/report.json`.
