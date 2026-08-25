# Hitter v2 Stage 2e failure postmortem

## Scientific conclusion

J0R solved its numerical problem but not the forecasting problem. Pitcher and
platoon context improved matched historical event likelihood in every fitted
node, yet the resulting player adjustment slightly worsened future event scores
and future wOBA/runs. Opponent context is therefore retained as descriptive
context, not promoted as a hitter-talent correction.

C0 is the useful lead. It beat Marcel on future wOBA RMSE in 22 of 24 supported
V2022 subgroup cells in both views, 23 of 25 player-weighted and 17 of 25
PA-weighted V2023 cells, and 23 of 25 player-weighted and 24 of 25 PA-weighted
V2024 cells. Its failure is inconsistency rather than absence of signal.

## What C0 is missing

C0 independently shrinks nested terminal components with component-specific
recency, but it does not model forward development or translate observations to
a common level. Its recurring weak cells—older hitters, AAA, demotions, and
some low-evidence PA-weighted groups—are consistent with that omission. V2022,
where no earlier origin existed and all components used the conservative literal
default, won only six of twelve marginal components against Marcel. In V2023
and V2024, chronology-selected C0 won eleven or twelve components in most views.

The current raw affiliated future-wOBA target also mixes two things: hitter
talent and the level/environment in which the player happened to receive future
PA. A neutral batting-talent model should instead place both history and the
evaluation outcome on a common reference-level scale using translations learned
strictly before the forecast date. Target-year level may label an evaluation
row, but it may never enter the forecast.

## What does not advance

J0R improved only three to five of twelve marginal outcome scores per fold/view,
with recurring harm in UBB, K, and HBP. It won future-wOBA RMSE in only three to
eight supported subgroup cells per fold/view. It cannot be retuned or used as
the base of a relabeled successor.

Contact direction remains scientifically plausible, especially pulled air
contact, but the earlier Stage 2c failure shows that an unrestricted shape
adjustment is not ready to carry the forecast. It may be tested only after the
neutral hierarchical outcome base passes, as a low-dimensional, evidence-
shrunk residual increment on identical players and targets.

## Recommended architecture

The next distinct candidate is `H0_NEUTRAL_HIERARCHICAL_OUTCOMES`: a common-
reference-level hierarchical terminal-outcome projection with mover-based level
translations, age-relative-to-level development, component-specific shrinkage,
and explicit calibration. Its optional successor is
`H1_CONTACT_SHAPE_INCREMENT`, limited to predeclared contact contrasts and exact
H0 fallback. Estimated distance and tracking remain a later richer capability
tier rather than a universal requirement.

The diagnostic used only disclosed V2022–V2024 evidence. It fitted and scored no
new candidate and did not open protected 2026.
