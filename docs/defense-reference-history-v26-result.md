# Outfield history improves after correcting the starting expectation

Centering outfield observations before reducing the weight of small samples
improves later MLB defensive-quality prediction in this fixed historical test.
Keep the correction as a research baseline. It does not finish prospect defense,
player development, opportunity forecasting or full hitter value, and it does
not change the frozen forecast or explorer.

The practical change is simple: a player with little evidence should start near
the average at his position, not inherit a large center-field penalty or corner
bonus from incompatible reference points. A player with no MLB evidence remains
unknown, even when the numerical forecast uses that starting expectation.

## The comparison and its limits

The [contract](defense-reference-history-v26-contract.md) fixes three seasons of
history, recency weights 1, 0.5 and 0.25, and a 3,000-out reliability prior.
No coefficients, features, ages or weights were fitted or tuned. LF/CF/RF
observations subtract an origin-known seasonal position reference before
shrinking. Each reference excludes all people in the forecast player's held
group. Intrinsic range remains a separate output. Infield and catcher forecasts
are unchanged.

The old comparator shrinks raw range first and subtracts the same origin
reference afterward. Neutral assigns zero relative OF skill, retaining other
component histories in the value test. All arms use identical player identities
and aligned outcomes. This does not compare against a newly trained age-adjusted
model; older calibrated raw forecasts cannot be relabeled as centered forecasts.

The main target is 2023–2025 pooled MLB quality from a 2022 origin. Measured
quality requires 1,500 same-position outs in two seasons and no missing positive
same-position exposure. Exit, low exposure, position changes and missing
measurements remain unknown. This is conditional evidence among measured MLB
defenders, not a defensive grade for every minor leaguer. There are 13,402
retained historical position forecasts; the headline group has 144 OF rows for
116 people. Each person receives equal total weight across their positions.

## Later defensive quality

All errors below are runs per 500 defensive innings. Lower error is better.

| Quality comparison | People | Old history error | Corrected error | Neutral error |
| --- | ---: | ---: | ---: | ---: |
| Main 2022 OF origin over 2023–2025 | 116 | 2.48650 | 2.28984 | 2.47203 |
| Separate 2021 OF stress origin over 2022–2024 | 115 | 2.31021 | 2.15456 | 2.35747 |
| Main 2022 all positions with infield unchanged | 261 | 2.37364 | 2.28516 | 2.49986 |

Main OF error improves by 0.19665, about 7.9%. The paired 95% interval for
corrected minus old error is −0.35338 to −0.03983. Corrected beats neutral by
0.18218, interval −0.32849 to −0.04191. Mean absolute error falls 2.00198 to
1.80702. These are development results, not a fresh independent holdout. Person
resampling conditions on the measured population and saved source references;
it does not cover survival selection, reference estimation or annual shocks.

LF, CF and RF errors each improve: 2.59260→2.30280, 2.58380→2.51277 and
2.30045→2.20131. Older, prime and young groups improve; the one unknown-age
person worsens 0.68166→1.32663. All history-size groups improve, but tiny
histories still have 2.53885 error. Main OF bias remains optimistic at +0.39035
versus old +0.43991. CF bias crosses −0.60981→+0.58667; lower squared error
is not perfect calibration. Infield has not improved under this unchanged arm.

## Delivered defense and player value

The separate integration holds batting, position and projected exposure fixed
for 12,432 player origins in 2022–2024, measuring 2023–2025. The 318 unknown
integrated outcomes cover 372,452 actual defensive outs; they remain unknown,
not zero. Both methods use the same complete subset.

| Delivery target | Old equal-year error | Corrected error | Change interval |
| --- | ---: | ---: | --- |
| Twelve-component defensive runs | 1.51896 | 1.49530 | −0.03255 to −0.01389 runs |
| Defense for actual MLB defenders only | 4.13640 | 4.07178 | Descriptive subset |
| Batting plus position plus defined defense in wins | 0.430404 | 0.429686 | −0.001541 to +0.000167 wins |

Delivered-defense error improves about 1.6%, in all three years. The actual
defender check prevents nonarrivals from being the sole explanation. Expanded
value improves only about 0.17%, with an interval including no improvement;
2022 worsens slightly and 2023–2024 improve. This is not a robust total-WAR gain.

Current MLB defensive error improves 3.77276→3.71543; upper minors improves
0.95797→0.93505. Upper-minors corrected results are essentially neutral OF
(0.93500): removing an artificial prior penalty is not skill identification.
Lower minors worsens 0.231136→0.231255 and inactive players worsens
0.166679→0.167568, with slight expanded-value deterioration too. Do not delete
these groups or call near-zero contribution errors good talent projections.

## Totals remain too optimistic

| Observed season | Complete people | Actual defined defensive runs | Old forecast | Corrected forecast |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 4,139 | +53.293 | +94.821 | +98.901 |
| 2024 | 4,083 | +3.552 | +94.141 | +96.770 |
| 2025 | 3,892 | −37.562 | +110.388 | +118.743 |

The correction worsens these totals slightly. The unchanged first-base range
forecasts are −5.010 versus −64.600 actual in 2023, −13.678 versus −29.987 in
2024, and −11.545 versus −60.952 in 2025. Framing forecasts +27.415 versus
+8.453, +13.055 versus +7.166, and +19.166 versus +3.190. Other infield groups
have large errors in both directions. This is not just an OF problem.

Full qualified native first-base range totals are themselves negative: −62.633,
−32.562 and −43.465. Raw-zero shrinkage and a position-relative prior are
different assumptions. Review the references and priors; do not assume those
measurements are wrong or automatically zero every infield position. FanGraphs
specifically describes seasonal OF centering in its
[2022 WAR correction](https://blogs.fangraphs.com/a-fangraphs-war-fielding-update/);
that statement alone does not establish a corresponding infield rule.

The complete subset is not the entire league and its twelve-component target
is not FanGraphs WAR; totals need not equal zero. Do not impose a quota or use
future centers to conceal the miss. The [totals diagnosis](../reports/model-evidence/defense-reference-history-v26/totals-diagnosis.json.gz)
reproduces every channel sum without changing forecasts or targets.

## Baseball checks and disposition

The [player walkthrough](defense-reference-history-v26-player-review.md) covers
sixteen groups and 64 records, with gains, losses, false highs/lows, ordinary
cases, nonarrivals and origin-selected peers. Trout improves −1.242→−0.405 CF
quality against −0.273 actual. Castellanos improves −1.463→−1.811 RF against
−2.027. Siani's artificial penalty disappears, but −0.093 still misses later
+5.293 talent. Adell worsens −1.921→−0.038 CF against −6.566. Hernández's
delivery worsens because projected CF gives way to poor actual SS innings.
Witt's strong shortstop development is still missed; catcher controls are
unchanged. These gaps remain alongside the positive OF result.

Retain corrected position-relative history and explicit unknown-quality
fallback as a practical research baseline, not an integrated deployment or
minor talent validation. Next reconcile unchanged component priors/opportunities
behind first-base/catcher totals, then use compatible older quality and contextual
minor evidence to test later MLB talent. Avoid another prior/recency tournament.

All 13,402 quality forecasts, 12,432 value forecasts, 37,296 OF channels,
references, eligibility, support, scores, intervals and selections independently
replay. Nine unit tests pass. A raw-source supplement replays 428 minor splits
and 582 annual position records. A disk-full receipt failure was preserved;
the unchanged verifier reran successfully. See [storage recovery](defense-reference-history-v26-storage-note.md).
Integrity, conditional prediction, unresolved baseball failures and deployment
approval are separate. The broad defense goal stays active.

The initial finalizer stopped before producing a final receipt because its
explorer check used the initial build's HTML hash, which predates the already
published name/mobile display repairs. A separate receipt-aware finalizer verifies
that full saved hash chain, the final HTML/template and unchanged data. The
initial script remains preserved; no forecasts, UI or old receipts changed.
