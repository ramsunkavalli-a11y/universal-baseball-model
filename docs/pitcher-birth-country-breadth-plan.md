# Pitcher stable-demographic breadth plan

**Status:** frozen before scoring

## Question

Does reported birth country add repeatable information to the existing pitcher
age-relative-to-level and throwing-hand adjustment when forecasting future MLB
component outcomes?

## Candidates

Compare the incumbent with four fixed families: age/hand, country only, additive
age/hand/country, and age-by-country interactions. Country indicators are USA,
Dominican Republic and Venezuela; all other or unknown countries are the reference.
The existing five coherent outcome probabilities are adjusted together with the same
fixed player-scale penalty used by the current demographic audit.

Current height and weight are explicitly excluded. They can change for young players,
so using the 2026 profile value in a 2023 or 2024 forecast would leak future
information. No physical feature may enter until a dated historical source exists.

## Test

Use five deterministic player folds to produce out-of-fold 2024 development scores.
Choose the lowest log loss only among families that also beat the incumbent Brier
score. Fit that one family on all 2024 rows and report its already-inspected 2025
result as additional development evidence, not untouched confirmation.

Report log loss, Brier, calibration and country subgroups. No current 2026 outcome,
outside FV, player rank, contract or target number of high-value pitchers may enter.
No result from this run can be promoted without a later untouched origin.
