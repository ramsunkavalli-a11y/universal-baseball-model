# Pitcher affiliated-rate regression audit plan

Status: frozen before score.

## Question

Does the current 800-BF population prior shrink translated minor-league pitcher
components too aggressively, contributing to compressed pitcher prospect value?

## Chronology

- Development target: 2024 MLB. Translation and player evidence may use 2023 only.
- Confirmation target: 2025 MLB. Translation and player evidence may use 2023-2024.
- Each population contains pitchers with earlier affiliated BF, zero earlier MLB BF,
  and positive MLB BF in the target year. Target membership is never a predictor.
- No 2026 outcome, contract value, outside FV, or subjective prospect label is used.

## Candidates and selection

Hold the translation method, recency weights, level discounts, component definitions,
and MLB population prior fixed. Test regression priors of 100, 200, 400, 600, 800,
1,200, and 1,600 BF.

Select the lowest 2024 component log loss among candidates that also beat the
incumbent 800-BF prior on component Brier score. Break a numerical tie by choosing
the value closest to 800 BF. Freeze that one choice before opening the 2025 score.

## Promotion gate

Promote only if the selected candidate beats 800 BF on both component log loss and
component Brier score in 2025. Report player counts, BF, bootstrap uncertainty for
both score differences, predicted-versus-observed component rates, and implied
neutral runs-above-average spread. Treat the run-rate view as diagnostic because one
season of pitcher outcomes is noisy; the proper component scores control the decision.
