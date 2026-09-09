# Prospect play-by-play hurdle test plan

Status: **FROZEN BEFORE SCORING**  
Frozen: 2026-09-09

## Question

Does affiliated play-by-play contact shape improve a hitter prospect's next-season
MLB opportunity or component quality beyond the existing aggregate-results model?

This is a research test, not permission to change Model FV. It does not use an
outside FV, prospect rank, team depth chart, or current organization.

## Why this is a separate test

The earlier batted-ball tests asked whether exit velocity and sweet-spot rate improved
current contact-shape or contact-value estimates. Contact shape failed development.
Contact value lowered MSE in every 2023 fold but worsened MAE and calibration, so it
failed confirmation. Those candidates remain rejected and will not be retuned here.

This test asks a later-outcome question using the broadly available historical contact
profile: trajectory and spray direction. It keeps opportunity separate from quality,
consistent with the existing prospect hurdle model.

## Data and chronology

- Predictor origins: completed 2021, 2022 and 2023 affiliated seasons.
- Outcomes: the immediately following MLB season, respectively 2022, 2023 and 2024.
- Training origin: 2021.
- Candidate selection origin: 2022.
- One untouched outer comparison: 2023.
- Every profile row must have `game_date` in its predictor season and strictly before
  January 1 of the outcome year.
- Players without PBP remain in the denominator. Missing PBP is represented by a
  coverage indicator and population-prior feature values, never by dropping players.
- The player universe is the existing age-eligible pre-MLB snapshot cohort, including
  non-arrivals and zero future MLB outcomes.

The source is retrospective event-cutoff corrected history, not a vintage-information
set. That label must remain on the result.

## Incumbent and bounded candidates

The incumbent is the current aggregate `core` prospect design: age, level, affiliated
workload/history, 40-man state, role and four regressed production rates.

PBP candidates add only pre-cutoff, empirically regressed contact shares:

1. `trajectory`: GB, LD and IFFB shares; OFFB is the omitted fourth category.
2. `direction`: pull and opposite-field shares; center is omitted.
3. `combined`: the five trajectory and direction terms above.

All candidates also carry contact count and a PBP-observed indicator. Contact shares
are regressed to training-population rates using pseudo-contact strengths
`50, 200, 600`. Logistic regularization is selected from `C = 0.03, 0.1, 0.3, 1.0`.
No additional feature, interaction, cutoff, or threshold may be added after viewing
the 2022 or 2023 score.

## Outcomes

Score two distinct one-year outcomes:

1. **Meaningful opportunity:** at least 200 MLB PA in the following season.
2. **Positive component quality, conditional on meaningful opportunity:** neutral
   wOBA components at or above that MLB season's league rate.

The second outcome is scored only among observed meaningful-role players, but the
first retains everyone. Contact shape may not directly add WAR or create a talent
floor.

## Selection and outer decision

- Select the candidate on 2022 by log loss, requiring Brier no worse than incumbent.
- Refit that one candidate on the combined 2021 and 2022 origins.
- Judge it once on the 2023 origin / 2024 outcome.
- Promotion requires lower outer log loss and Brier, acceptable calibration, no
  material damage in a supported level/age/workload/handedness/source-coverage group,
  and a player-level paired bootstrap interval that does not indicate clear harm.
- Report cohort sizes, observed and predicted rates, reliability groups, calibration
  intercept/slope and player-level paired uncertainty.
- Small or mixed gains remain research-only and require a later fresh confirmation.

## Statistical guardrails

- Regress rates; do not treat a small contact sample as true talent.
- Compare identical players for incumbent and challenger.
- Use calendar folds, not random player splits.
- Preserve outcome, opportunity and evidence denominators separately.
- Do not infer that contact-direction tendencies are intrinsically valuable without
  evidence against the future outcome.
- Catcher or other position status stays in the shared incumbent. It cannot enter as
  a special preference in only the PBP challenger.
- Pitch-sequence features are excluded: their historical capability is not universal
  across levels. Pitchers require a separate source-complete process test.
