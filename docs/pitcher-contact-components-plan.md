# Pitcher contact-component expansion plan

Status: frozen before score.

## Question

Does separating singles, doubles, and triples allowed from the current pitcher
`other` bucket improve future MLB component forecasts and safely widen conditional
pitcher quality?

## Source and components

Reproject the already saved official StatsAPI season captures. The pitching payloads
contain hits, doubles, triples, home runs, BF, strikeouts, walks, and HBP at every
affiliated level. Use eight mutually exclusive BF outcomes: SO, UBB, HBP, 1B, 2B,
3B, HR, and other out.

The incumbent five-part profile is expanded to the same eight outcomes by assigning
its broad `other` probability according to the prior MLB season's contact mix. Thus
both models are scored on exactly the same target and denominator.

## Tango-style regression and chronology

BABIP/contact suppression is less stable than strikeout or walk skill, so the richer
candidate must earn its use under heavier regression. On the 2024 development target,
test 800, 1,600, 2,400, and 4,000 BF priors while holding translation, recency, and
level discounts fixed. Select the lowest component log loss among candidates that
also improve Brier versus the expanded incumbent. Freeze that one candidate before
opening 2025.

- 2024 target: fit translation and profiles from 2023 only.
- 2025 target: fit translation and profiles from 2023-2024 only.
- Population: prior affiliated BF, zero prior MLB BF, positive target-year MLB BF.
- Target membership is never a feature.

Promote only if the frozen candidate improves both 2025 component log loss and Brier.
Report player-bootstrap intervals, contact calibration, and neutral run-rate spread.
No current 2026 outcome, pitch-process fields from uncertified feeds, outside FV,
contract data, grade count, or post-confirmation tuning is allowed.
