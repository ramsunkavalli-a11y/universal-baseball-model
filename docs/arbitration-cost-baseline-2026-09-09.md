# Arbitration cost baseline — 2026-09-09

**Status:** Phase 1 external baseline connected; internal historical fit is Phase 2

The named Phase 1 salary approximation uses FanGraphs' current prospect-valuation
method: 15% of prior-season free-agent WAR value for Arb 1, 35% for Arb 2, 50% for
Arb 3, and 75% for Arb 4. FanGraphs reports choosing this structure after testing
alternatives against actual arbitration payouts. It is a defensible broad baseline,
not a player-specific hearing forecast.

The implementation now preserves the one-year salary lag. Projected arbitration cost
for season `t` uses projected WAR from `t-1`, valued at season `t` market rates, then
applies the class share and the applicable minimum-salary floor. It does not use the
same season's projected WAR unless `t` is the first forecast year and no prior full-
season path exists.

Current coverage contains 23,261 arbitration player-years with a true prior projected
season and 388 first-horizon rows using the clearly labeled same-season proxy. Ten
current Super Two tracks progress through Arb 1–4 correctly. Known contract/payroll
salaries always override the approximation.

This does not model the traditional statistics, comparable-player arguments, awards,
filing strategy or settlements that drive individual arbitration cases. Building a
chronological internal salary dataset and testing those details is Phase 2. It also
does not resolve the successor CBA or post-2026 minimum salaries.

Primary source: FanGraphs, *The Details of Our New Prospect Valuation Methodology*.
