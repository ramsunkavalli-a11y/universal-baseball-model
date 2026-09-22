# Full hitter 2026 forecast freeze

Status: **complete and verified before opening 2026 outcomes**

The current hitter development model is now frozen on the exact 3,907-player population from the locked playing-time forecast. The forecast file hash is `d1953a28d35d87d141ecc65ec4b107906edad877982e79c0d3a216245b9e4708`.

## What is in the forecast

- 3,720 hitters receive the selected five-model batting forecast.
- 187 hitters who were in the playing-time universe but lacked a 2025 batting record receive a clearly labeled, playing-time-scaled population prior.
- 3,511 hitters have complete 2025 detailed-contact evidence.
- 3,718 hitters have a usable position profile.
- 3,764 hitters have at least one baserunning evidence channel; the remaining 143 are neutral.
- 87 hitters have catcher-defense evidence.
- General non-catcher defense remains exactly zero because its development model failed to improve total-value prediction.

The final number is partial WAR: batting plus replacement, position, baserunning, and catcher defense. It is not presented as full WAR while general defense remains unresolved.

## Sanity checks

All 31 frozen files and inputs reproduce their recorded hashes. Player IDs match the locked playing-time universe exactly. Forecast probabilities remain between zero and one, expected playing time remains between zero and 704 PA, every required prediction is finite, component arithmetic recomposes exactly, and the uncertainty bands are ordered and nested.

The forecast remains intentionally conservative about playing time. Even established MLB stars are regressed because the model predicts expected PA across injury, role loss, and absence risk. The 2026 confirmation will score that choice against both the older cohort model and the parametric level baseline rather than adjusting it after seeing the season.

## Locked evaluation

The evaluator cannot open a target file unless the caller explicitly declares the regular season complete and supplies an evaluation date of October 1, 2026 or later. It also rejects a changed forecast, a changed manifest, duplicate players, incomplete outcomes, or a target population different from the frozen 3,907 players.

The selected model stays in place by default. The stats-only-arrival routed challenger can replace it only if it improves partial-WAR RMSE with a fully favorable paired-player uncertainty range, does not worsen batting RMSE, and avoids material harm in every predeclared supported subgroup.

No 2026 participant or outcome information was read during fitting, packaging, verification, or the synthetic evaluator dry run.
