# Relative-exposure encoding did not improve the hitter forecast

2026-10-02. Seventy saved heads replay; 17 player walkthroughs complete.
No frozen forecasts, deployed explorer or protected 2026 results changed.

The [fixed test](practical-hitter-v35-contract.md) shared event opportunities
across leagues before entering the same 199-feature assembly. It retained the
legacy MLB quality/workload features. All 30,506 forecasts and V34 training
memberships stayed unchanged. This distinguishes it from a clean event-outcome
model and limits what a failure can reject.

| Scope | V34 control | New rate only | New PA only | Both new heads |
|---|---:|---:|---:|---:|
| All-row value RMSE | 0.44060 | 0.44160 | 0.44061 | 0.44171 |
| V24-matched value RMSE | 0.90886 | 0.91165 | 0.90851 | 0.91163 |
| Public-matched value RMSE | 1.01638 | 1.01796 | 1.01334 | 1.01556 |
| Brief-debut value RMSE | 0.7643 | 0.7694 | 0.7637 | 0.7690 |

Conditional future-active batting-rate RMSE rises 1.82465→1.83112 wins/600 PA,
weighted by actual PA within equally weighted years. Brief-debut conditional
rate RMSE rises 2.27810→2.29498. The rate-only value squared-error change is
+0.000877, nominal 95% player-cluster interval +0.000210 to +0.001592;
brief-debut +0.007808, interval +0.002146 to +0.013920. Thus this rate encoding
has adverse development evidence, not just an absence of a large gain.

New PA RMSE is 124.792 versus 124.889 on V24 matches; public 144.159 versus
144.487 and Steamer 135.019. Public MAE 111.323 remains about 20.5% worse than
Steamer 92.399. These small workload differences do not establish a replacement
forecast. Public converted-value/snapshot-date qualifications remain unchanged.

## Why baseball cases matter here

Winn's 498-PA AAA season (18 HR, 83 K) is present, but its favorable rate
deviations are diluted while his separate poor-MLB quality inputs remain.
His rate falls −0.797→−0.993 and PA 306→288 against 637 actual. Steer also loses
rate despite 23 current upper-minor HR. Judge's debut forecast gains PA but
loses batting rate; it does not resolve the desired reconciliation.

Judge 2024 improves 548→563 PA and 5.88→6.08 value, but his event input values
are exactly unchanged: this is a changed training mapping, not reweighted own
minor history. Bellinger 2018 loses 608→528 PA despite two substantial MLB
seasons. Cowser's largest gain reduces a false high; Alvarez's lower PA reduces
a later-absence miss without demonstrating injury foresight. McLain's rate-only
value improves while his combined playing-time forecast deteriorates severely.
Ordinary Murphy/Flowers cases work reasonably; Nola's close total partly hides
component offsets. See the [full evidence and walkthrough](evidence/practical-hitter-v35/player-walkthrough.md)
and [manual case ledger](../config/practical_hitter_v35_case_notes.json).

Upper-minor PA allocation improves from 93,314 to 96,278 against 102,951 actual,
but upper-minor contribution RMSE worsens 0.3014→0.3028. A better group total
does not certify individual forecasts. Lower minors remain substantially
overallocated. The overall goal is not complete.

## Decision

Do not adopt this batting or combined encoding; PA-only evidence is uncertain.
Keep V33b working forecast and V34 source-repaired research control. This rejects
one shared-denominator encoding with retained legacy quality features, not
component modeling, minor-league evidence or MLB equivalencies in general.

Next use a coherent event-outcome likelihood: predict the probabilities of actual
MLB batting events, then convert those events to batting runs. This makes the
baseball target explicit and prevents confusing another linear re-expression
of the same value target with a genuinely different approach. Keep the workload
head fixed, and review rates and delivered value separately.
