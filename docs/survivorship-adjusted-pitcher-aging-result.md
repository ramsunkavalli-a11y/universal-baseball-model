# Survivorship-adjusted pitcher aging result

**Status:** tested and rejected as an aging replacement; return model retained for
future opportunity work; no production value changed.

## What was tested

Every MLB pitcher season from the retained 2015–2025 history was kept, including
pitchers with no pitching workload the following year. A next-year return model used
only source age and batters faced. Small age-by-workload cells shrink first to their
workload band and then to the full pitcher population. Returning adjacent-season
rate pairs were then given bounded inverse-return weights.

This does not give a vanished pitcher a fake component rate. It changes the mix used
to estimate the conditional aging curve, while the separate opportunity path still
owns the probability of returning and the zero-production outcome.

## Result

- The return model was useful on the untouched 2022–2025 period: Brier score
  **0.1756**, versus **0.2116** for one population return rate; log loss was
  **0.5244**, versus **0.6146**.
- The adjusted fitted aging curve improved slightly over the same fitted curve
  without survivor weighting: standardized log loss **0.967486** versus
  **0.967521**.
- It still lost to both Tango (**0.967142**) and no aging (**0.967202**).
- The bounded weights ranged from **0.76** to **1.74**, so the result was not driven
  by extreme weights.

## Decision

Keep Tango pitcher aging. Do not promote the fitted curve merely because the bias
correction moved it in the right direction. Reuse the validated age/workload return
model as a challenger inside the opportunity and attrition path, where it belongs.

The next dropout work should apply the same separation to hitters, then score return,
workload and conditional performance jointly. Broader uncertainty work should use
the discrete non-return probability rather than one symmetric Normal range.

[Machine-readable result](survivorship-adjusted-pitcher-aging-result.json)
