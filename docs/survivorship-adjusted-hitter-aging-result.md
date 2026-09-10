# Survivorship-adjusted hitter aging result

**Status:** fitted age curve rejected; hitter return model retained for opportunity
research; no production value changed.

The test uses regressed seven-part hitter component profiles from 2015–2025. A
partially pooled age-by-prior-PA model predicts next-season MLB return. Returning
adjacent-season pairs then receive bounded inverse-return weights so the conditional
age curve better represents the source population. Players who disappear remain
zero-production outcomes in the separate opportunity score; they are not assigned
fake batting rates.

## Result

- The return model strongly beats a population-only probability on 2022–2025:
  Brier **0.1439 vs 0.2152** and log loss **0.4340 vs 0.6219**.
- Survivor weighting slightly improves the newly fitted age curve: standardized
  component log loss **1.044929 vs 1.044953**.
- The adjusted curve still loses to no aging (**1.044730**).
- Marcel also loses to no aging (**1.044760**).

## Decision

Retain no aging as the frozen simple hitter challenger for protected 2026
confirmation. Reuse age and prior workload in the participation/attrition model, where
they provide real predictive value. Do not turn that return advantage into a batting
skill adjustment.

Any future hitter skill-aging curve needs a new model form or evidence class and must
beat both no aging and Marcel on a later zero-inclusive production test.

[Machine-readable result](survivorship-adjusted-hitter-aging-result.json)
