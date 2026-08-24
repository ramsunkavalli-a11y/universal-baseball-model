# Hitter v2 Stage 2c E1 prescore checkpoint

Status: **SCORER FROZEN; E1 NOT YET FIT OR SCORED**  
Date: 2026-08-24

## Authorized evaluation

Only `E1_NESTED_PULLED_OFFB_POWER` may be fit and scored. It adds the two
predeclared pulled-air features to the frozen C0 offset and may alter only
`P(HR | contact)`. V2023 is fit from V2022; V2024 is fit from pooled V2022 and
V2023. V2022 remains a zero-fit training-origin diagnostic.

The selection gate requires E1 to improve terminal proper scores in every
V2023/V2024 fold and player/PA view, HR-conditional log loss against C0 in all
four views, pooled future wOBA and batting-runs/600 RMSE in both views, and to
avoid a material supported-level reversal. The exact thresholds and metric
definitions are frozen in `docs/hitter-v2-stage2c-e1-scoring-contract.json`.

Evidence-band, level-transition, coverage, calibration, correlation, MAE, and
HR Brier results are reported but cannot select the model.

## Stop rules

- E1 failure is terminal for this ladder on disclosed development outcomes.
- E2 cannot rescue a failed E1 and is not fit or scored by this command.
- No result may trigger tuning, threshold changes, or grid expansion.
- Protected 2026, tracking, Stage 3, and WAR remain forbidden.
- An E1 pass authorizes only freezing a separate E2 scorer before E2 is run.

The frozen command is:

`.venv\Scripts\python.exe scripts/score_hitter_v2_stage2c_e1_development.py`

Ruff and the 12 focused Stage 2c tests pass before this freeze. The candidate
has not been fit and no Stage 2c outcome has been scored at this checkpoint.
