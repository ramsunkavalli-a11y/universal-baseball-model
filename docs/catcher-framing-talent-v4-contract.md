# Test a practical catcher framing talent baseline

Locked before fitting, 2026-10-06, after the source/support walkthrough. The
modern source provides 165 eligible catchers at the 2022 origin, but only 55
have sufficiently measured 2023–2025 framing quality. Actual chronological
training has 45–54 people from two mature origins, 2018–2019, depending on the
held-player fold. Every training history is left-truncated by the 2018 source
boundary. These limits are explicit, not hidden by counting repeated rows.

## Fixed target and comparison

Keep every one of the 889 source-audited origins and all quality labels unchanged.
Predict native framing runs per 1,000 received non-swing pitches in the following
three calendar years. A measured quality pool needs a complete window, two
measured seasons, at least 6,000 pitches and no missing positive native catcher
exposure. Non-arrival or insufficient future samples mean unknown ability.
Only MLB 2018–2025 sources are usable; do not reuse modern 2016–2017 zero
placeholders, lower-minors framing proxies or 2026 outcomes.

Three references, without tuning:

- Neutral framing, zero quality increment.
- Transparent history: recency weights 1, 0.5, 0.25, with 1,000 times weighted
  framing runs divided by weighted actual received pitches plus 6,000. This
  fixed rough prior is not a fitted stabilization claim. Tiny samples therefore
  directly contribute very little rather than receiving a decorative flag.
- Small calibration: history rate, reliability n/(n+6,000), age centered at 27
  divided by ten, its square, age-missing indicator and history × reliability.
  Weighted-standardized Ridge alpha 10, fitted only within the training cell;
  each training person has total weight one across their repeated origins.

All training labels must mature by the origin. Exclude every record belonging
to the held person's ID-mod-5 fold. A fit requires 40 distinct people and two
mature origin years; otherwise use the transparent history fallback. Forty is
a minimum execution guard for this six-input regularized calibration, not a
full-profile validation certificate. Save all checks before fitting, including
age × history-pitch bands, left truncation, missing ages and input-range
extrapolation. Unknown/sparse players remain predicted and visible.

## Scoring and decisions

Primary comparison is the ordinary 2022 origin, measured future quality with
equal weight per person. Report RMSE, MAE, bias and paired 2,000-draw person
bootstrap intervals for history versus neutral and calibration versus history.
Keep 2021 separate: its calibration falls back because only one mature training
origin exists. Report all eligibility/measurement counts, age and exposure
groups, and oracle-exposure totals. Those totals are not forecasts of workload,
catcher value or full WAR.

Retain a practical history baseline if it identifies later receiving better
than neutral, even if age calibration adds nothing. Inspect magnitude and
uncertainty, systematic profiles and actual baseball behavior rather than vetoing
an input over microscopic bias. No penalty/prior/age sweeps after scores.
One ordinary origin, selected survivors and short historical support cannot
certify all-catcher development, minor talent or future rule-regime value.

Mandatory player review: the fixed support cases Hedges, Realmuto, Grandal,
Sánchez, Kirk and Raleigh; preserve Bailey's lack of eligible 2022 MLB history.
Retain tiny-sample Lin/Reetz as unknown-quality examples. Add largest gain/loss,
false high/low and ordinary median cases. Reuse three peers selected by origin,
age and history pitch exposure, without future selection; include the original
dated pitches/runs, shrinkage, exact fitted contributions, future annual paths,
actual support and the coherent zero-history fixed-fit explanation. Complete
the walkthrough before disposition or another component fit.

## Role in the defense goal

This supplies an MLB-history receiving-quality baseline in native units. The
same quality should not automatically deliver the same value under traditional
calls, ABS challenges or full ABS. Awarded framing opportunities and future
rules belong in the subsequent exposure/value layer. Players without measured
MLB framing retain an uncertain prior, not an observed average ability grade.
Throwing, blocking and minor catching remain separate. No selected forecast,
explorer or completed 2026 evaluation changes.
