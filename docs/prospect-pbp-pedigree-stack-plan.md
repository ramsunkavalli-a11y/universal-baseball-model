# Prospect PBP plus pedigree stacking check

Status: **FROZEN BEFORE SCORING; DESCRIPTIVE ONLY**  
Frozen: 2026-09-09

## Question

Does the contact-shape opportunity signal from the first PBP hurdle test add anything
after the stronger aggregate `baseball_pedigree` feature set is already present?

The 2024 outer outcome was inspected in the earlier core-comparator test. This check
therefore cannot confirm or promote a model regardless of its result. Its only purpose
is to determine whether the PBP signal was mainly standing in for draft/signing and
baseball-development information.

## Frozen design

- Outcome: at least 200 MLB PA in the season immediately after each prospect origin.
- Origins: train on 2021, select on 2022, descriptively score 2023 against 2024.
- Incumbent: `baseball_pedigree`, aggregate production regression `50`, logistic
  `C = 1.0`.
- Challengers: the exact `coverage`, `trajectory`, `direction` and `combined` PBP
  families from the first frozen test.
- Contact regression: `50, 200, 600`; logistic `C = 0.03, 0.1, 0.3, 1.0`.
- Select on 2022 log loss with Brier no worse than incumbent; score one selected
  challenger on the descriptive 2023/2024 outer comparison.
- Keep identical players, including non-arrivals and missing-PBP rows.
- Report proper scores, calibration, reliability groups, supported subgroups and
  player-level paired uncertainty.

No feature, interaction or threshold may be changed after viewing the score. The
conditional-quality use is not reopened because its first test was underpowered and
failed calibration. No result from this check may directly alter FV or player value.
