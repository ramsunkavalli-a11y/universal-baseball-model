# An event model can be coherent and still forecast hitting badly

2026-10-02. Thirty-five saved logit heads converge/replay; 13 player reviews
complete. This [fixed comparison](practical-hitter-v36-contract.md) keeps V34
playing time and all test identities, but changes the batting likelihood and
uses 144 count/context features without legacy batting-value quality predictors.
No protected 2026 results, frozen forecasts or deployed explorer change.

Future MLB event counts reconstruct the old batting-rate labels exactly before
fitting. Eight probabilities are nonnegative and sum to one. Proper count log
loss is 1.47950 versus league-environment-only 1.49159: the model learns useful
event variation. That does not answer whether its batting-value forecast is good.

## Predictive result

Conditional batting-rate RMSE rises 1.82465→1.90816 wins/600 PA. Its squared-error
change is +0.31175, nominal paired player-cluster 95% interval +0.21689 to +0.41597.
All-row contribution RMSE rises 0.44060→0.45923; squared-error change +0.01676,
interval +0.01061 to +0.02366. V24-matched value RMSE worsens 0.90886→0.93480;
public matched 1.01638→1.04874. Brief-debut rate error is nearly unchanged, not
a substantive win. Playing-time error is exactly unchanged by construction.

Public converted Steamer/ZiPS rate losses have material positive mean offsets;
the raw comparison does not certify pure-talent superiority of the old control.
No public forecast inputs were used in fitting this candidate.

## What the player calculations revealed

Judge's known 2024 record includes 58 HR in 704 PA plus two exceptional prior
seasons, yet the model predicts only 3.93% HR and drops his batting rate from
4.55 to 1.64 wins/600. Chris Davis goes the other way: a declining 2017 power
record produces 6.01% projected HR, partly from positive learned K-to-HR
cross-effects. Those are meaningful representation/calibration failures, not
merely unavoidable later breakouts or injuries.

McNeil's low K/high contact is recognized, but weak predicted walks/power offset
it. Winn still fails to receive useful translation of his long strong AAA year.
Lux's batting rate nearly matches the realized return year, but fixed workload
is far too low. Kurtz gets a modestly positive batting grade but almost no PA.
Alvarez is the largest gain largely because conservative talent compression
reduces a later-absence false high; that is not injury prediction. Marte's close
total partly offsets workload and rate errors. Full source/event/conversion and
origin-peer evidence is in the [player walkthrough](evidence/practical-hitter-v36/player-walkthrough.md)
and [case judgments](../config/practical_hitter_v36_case_notes.json).

## Decision and next work

Do not adopt the naked event logit. Keep V33b working forecast and V34 repaired
source as research control. Physical event accounting and improved count loss
cannot override adverse batting-value evidence or implausible established power.
This rejects this fixed specification, not all coherent component forecasting.

Next test an empirical own-MLB-count anchor with learned residual adjustments,
keeping this likelihood/settings and fixed workload. A projection should not
have to reconstruct an established hitter's basic record from correlated
predictors alone. This is a new predeclared structural hypothesis, not retuning
the penalty after seeing Judge or redefining the objective as event log loss.
