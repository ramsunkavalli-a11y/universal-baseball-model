# Peak talent upside probabilities

Last updated: 2026-09-12  
Status: **VALIDATED CONDITIONAL UPSIDE LAYER AVAILABLE**

## What this fixes

The peak component models intentionally shrink noisy prospect performance toward the
population. Their mean is conservative and can make many players look similar. A
shrunken mean is not the same statement as "this player has average talent."

This layer keeps that mean and adds two probabilities from historical forecast errors:

- above-average peak: more than 0 runs above average per 600 PA or 800 BF;
- impact peak: more than 10 runs above average per 600 PA or 800 BF.

These are conditional talent probabilities for players with enough later evidence to
observe ages 24–26. They are not arrival, playing-time or career-value probabilities.

## Chronology and validation

Every historical residual is produced by a peak model fitted only on earlier peak
windows. The 2018–2019 windows select how residual uncertainty is pooled; 2023–2025
confirm it. Public rank and FV are never used.

The global residual-distribution probabilities beat a constant base-rate forecast on
both Brier score and log loss in all three confirmation years for both hitters and
pitchers and for both thresholds.

- Hitters: age/evidence-specific refinements were unstable, so the global residual
  distribution is retained for both probabilities.
- Pitchers: age-band residual distributions passed the confirmation rule for both
  probabilities. Evidence-band refinements were not selected.

This is important discipline: uncertainty is widened using observed historical miss
rates, but low evidence does not automatically receive a made-up upside bonus.

## Current examples

| Player | Mean peak runs | Above-average peak | Impact peak |
|---|---:|---:|---:|
| Rainiel Rodriguez | +9.6 / 600 PA | 74.5% | 50.6% |
| Sebastian Walcott | +7.4 / 600 PA | 69.6% | 45.3% |
| Jesús Made | +3.6 / 600 PA | 61.0% | 36.8% |
| Josuar Gonzalez | -7.3 / 600 PA | 34.1% | 15.4% |
| Braylon Doughty | -14.7 / 800 BF | 21.4% | 10.2% |
| Seth Hernandez | -30.2 / 800 BF | 6.0% | 2.2% |

Seth Hernandez remains a direct missing-input disagreement: the official lower-level
feed does not provide the pitch velocity, movement or arsenal evidence behind his
public reputation. The upside layer describes uncertainty in the evidence the model
has; it does not fabricate the evidence it lacks.

Generated tables are in `reports/generated/peak-talent-upside/`. The comparison audit
also carries both probability fields for every model-top-25/external-top-50 case.
