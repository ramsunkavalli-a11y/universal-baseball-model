# Simpler readiness is clearer, not more accurate overall

2026-10-03. All 70 opportunity heads replayed, eight actual player reviews
complete. Hitting and all established-player forecasts are unchanged.

The compact fit removes 92 sparse rate inputs. Langford rises from 43 to
212 expected PA versus 557, without the old rookie-doubles -42 PA term.
Holliday falls from 363 to 300 versus 208. But Julio Rodriguez falls from
224 to 143 versus 560; Bellinger and Alonso still get only 35 and 143 PA.
Fisher's close contribution again hides opposing hitting and workload errors.

Never-debut PA RMSE worsens 27.745 to 28.022, delivered-offense RMSE .154072
to .154510. The contribution MSE interval includes improvement and deterioration,
but there is no material gain to justify adoption. Upper-never totals improve
73,593 to 83,447 versus 92,891 actual; lower-never remain too high. Improved
totals are not enough. Conditional linear PA clips to a physical bound for
2,322 of 24,199 prospect rows, an additional extrapolation qualification.

Do not adopt this forecast. Close the shared/fixed/assembled/compact prospect
representation batch. Retain the real numeric source correction and baseline
hitting, and preserve the modest, uncertain detailed PA-only alternative.
No more penalty/scale sweeps on the same cases. Next material gap is timely
MLB availability and role-to-workload uncertainty. Public current-MLB PA MAE
still averages 106.87 versus Steamer 92.08, with snapshot-date qualifications.
This is next-year batting plus replacement, not full hitter WAR or player valuation.

The origin-year check is especially important: 2021-origin prospect PA falls
10,463 to 6,326 versus 18,944 actual; 2023-origin rises 14,758 to 22,091 versus
11,697 actual. Expected 2021-origin arrivals fall 80 to 45 versus 158. Overall
Brier and log loss both worsen. Cancellation flags being present does not
establish that interruption/vintage effects are correctly modeled, and this
comparison does not identify a unique COVID cause.

[Actual eight-player walkthrough](../reports/model-evidence/practical-hitter-compact-readiness-v57/player-walkthrough.md).
