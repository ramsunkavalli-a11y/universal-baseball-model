# Production fallback preserves gains but does not solve readiness

2026-10-03. A positive historical-ranking forecast with a count-based fallback
helps future MLB workload overall and avoids downgrading unlisted new draftees.
It still allocates too much immediate opportunity to some highly ranked players
far from MLB. The practical model is not finished; twenty actual player reviews
are complete before this decision.

The rule uses the saved ranking head for 450 current verified listings and the
saved count/games mean for everyone else. Rates, membership and policies stay
unchanged. No new models are fitted, no players removed and no future outcomes
enter the gate. This is a design repair motivated by exposed earlier results,
not independent confirmation. Target is next-calendar-year MLB PA and batting
plus replacement wins, not full WAR, present-day talent or six control years.

Broad PA RMSE improves 61.149 to 60.772 and contribution RMSE .43947 to .43852.
Nominal player-cluster PA-MSE change interval is -79.09 to -10.57; contribution
MSE interval -0.001642 to -0.000106. MAE is essentially unchanged. Public PA
MAE is 110.928 versus Steamer 92.399, about 20.1 percent worse and outside the
15 percent practical tolerance. Public value error slightly worsens versus games.

Never-debut upper-minor predicted PA becomes 90,793 versus 92,891 actual, closer
than 83,284 from the count control. Top20 total becomes 37,532 versus 38,273
actual, while top20 individual PA RMSE remains improved at 176 versus 215.
But lower-minor totals become 12,315 versus 6,072 actual, worse than either
the games control or unrestricted ranking forecast. The seventy ranked lower-
minor forecasts account for 3,769 expected PA versus 836 actual. Across all
cohorts total PA nearly matches (1,273,416 versus 1,270,493), but offsets across
years and stages mean this is not adequate calibration. The 2023-origin excess
grows to 194,137 versus 182,194 actual.

The player walks retain Volpe and Rodriguez readiness gains and return Kurtz,
Langford, Bellinger and Alonso to their original forecasts—still large misses,
not hindsight fixes. Mayer rises 45 to 256 PA and has no next-year MLB PA.
Salas, an eighteen-year-old with mostly High-A evidence, rises zero to 232
despite no next-year appearance. Only seven distinct training players match his
coarse rank/age/stage profile. Devers provides the necessary opposite case:
the same rule improves 1 to 147 PA versus 240 actual, but only two training
people match his coarse profile. A blanket ban on lower-level prospect credit
would erase that gain rather than learn the transition process.

Vientos keeps almost exact workload (233 projected and actual), but misses
batting value badly. Farmer's near-exact contribution offsets understated PA
and overly optimistic hitting. Brinson/Frazier/Andujar remain harms. These
examples prevent accurate products or famous successes from certifying the
whole system. All actual inputs, head choice, reconstructed paths and origin-
selected peers are saved in the
[twenty-player walkthrough](../reports/model-evidence/practical-hitter-scouting-v48/player-walkthrough.md).

Retain the fallback as a research comparison, not a working/frozen/deployed
promotion. The next substantive experiment should separate **probability of
playing MLB next year** from **PA conditional on playing**, rather than treat
rank as an undifferentiated immediate-workload bonus. Use the already audited
count/ranking panel and matched no-ranking counterpart. The earlier four-state
pipeline does not settle this simpler binary architecture with historical
scouting, and all future exits must remain in probability scoring. This is one
bounded mechanism comparison, not another library/threshold sweep. Conditional
batting talent, health/job context and long-term value still remain separate
unresolved work.
