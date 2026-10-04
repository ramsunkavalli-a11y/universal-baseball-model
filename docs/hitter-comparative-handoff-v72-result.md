# Hitter comparison explorer is ready

2026-10-03. The local research explorer now shows the chosen fresher-ranking
candidate and the original model side by side. No new models were fitted. The
comparison preserves all 30,506 historical forecasts and explicitly labels the
later preseason ranking dates. It does not change the frozen 2026 forecast or
any deployed explorer.

Open [the local explorer](http://127.0.0.1:8791/) while its server is running.
It opens to Giants current MLB hitters for forecast season 2025. That means
performance in 2025, not 2026. Switch the season, organization or stage to inspect
prospects and other historical cohorts. The model selector updates expected
PA, probability, conditional PA, offense, ranking metadata and actual earlier
profile support together. Hitting stays identical between the arms.

Browser checks cover all seven seasons, Giants/all-team and stage filters, player
search, model switching and hiding/revealing actual results. Kurtz's detail shows
two original PA versus ten for the candidate, and 489 actual only after results
are enabled. Langford shows 43 versus 215 before 557 actual. Raw source counts,
separate quantities, fixed-hitting arithmetic and completed comparison notes are
available without pretending those misses are solved. No browser errors were
observed. The probability bands are descriptive, not a fitted recalibration.

All displayed arm arithmetic and original forecast identity are verified against
the saved evidence. Historical team labels retain the previously reviewed
roster/last-club evidence; they are not post-outcome destinations. Actual rates
remain unobserved for zero-PA players, not fabricated zero talent. Known-player
team totals are not a complete future roster budget.

See [the chosen candidate model card](practical-hitter-candidate-v72-model-card.md)
for the full construction and limits. Public PA average absolute error remains
15.56% worse than Steamer. Upper-minor readiness improves, but immediate arrivals,
workload allocation, extreme talent and calibrated continuous uncertainty remain
unfinished. Graduation and employment additions are not adopted. Close that
patch queue and address thin-sample readiness/talent as the next substantive
modeling milestone. The broader goal stays active.
