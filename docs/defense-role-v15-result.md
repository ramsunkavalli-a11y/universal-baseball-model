# Recent position evidence is usable but is not yet a better forecast

2026-10-07. We can now recover dated fielding time and DH starts for the reviewed
MLB and minor-league cases. The important distinction is between **where a player
is being used now**, **other positions he has actually played**, and **how well he
can defend**. The prior allocator blurred the first two. This source repair does
not change defensive skill, batting, playing time or any forecast.

All 114 requested player-season-level scopes match the existing annual inventory
exactly: 281 position totals, 9,396 position-game records and 424 period cells.
The 74 distinct player-seasons include all nineteen focal cases and 57 original
peer records after deduplication, two prior-year contrasts and three prior
contributors. An independent arithmetic replay passed. Both sets of statistics
come from the same official provider; agreement is not an independent guarantee
that the provider has no omissions. Raw responses, dates, requests and hashes
remain local. The [source receipt](../reports/model-evidence/defense-role-v15/source-review.json)
and [player walkthrough](../reports/model-evidence/defense-role-v15/player-walkthrough.md)
retain scope and calculation details.

## What the player records tell us

Witt had **4,181 SS outs and no 3B use in 2024**, with 1,346 SS outs after August 1.
The prior candidate still allocated 221 third-base outs, mainly because older
assignments and broad groups remained in the role calculation. Henderson, De La
Cruz and Volpe supply the same useful contrast: their current SS assignments
were clear, yet the pooled recipe spread some time elsewhere. This is a role
representation defect, not proof their defensive-quality estimates are right.

Buxton had **2,301 MLB CF outs in 2024**, including 484 after August 1, and no
late-season MLB DH starts. The prior candidate assigned just 1,510 CF outs and
32 DH starts because 2023 remained in its blended role vector. His 2023 source
shows 80 MLB DH starts and a later AAA stint with one CF start and three DH
starts. That minor appearance is evidence of an attempted return, not a full
healthy CF season. His much larger 2024 CF record is the established current
assignment. Neither record predicts whether he will stay healthy.

Ohtani's hitter role is DH, not unknown. The reviewed totals are **153, 135 and
159 DH starts for 2022, 2023 and 2024**. The 51 missing simultaneous P/DH starts
from 2022–2023 are propagated by actual game date exactly once. Two games require
the already certified starting-role rule rather than a later DH appearance.
Pitching outs stay separate; no defensive innings are invented for DH. Pure DH
should not trigger a generic infield fallback. Ozuna and Vogelbach show related
problems, while Rooker cautions against assuming that a late DH-only stretch
permanently rules out his previously observed outfield use.

Schwarber's DH share of LF/DH starts rose from **28 of 106 before August** to
**29 of 54 afterwards** in 2023. This is useful direction, but not enough to
explain all of the following season's 144 DH starts. His separately dated
November assignment plan is an omitted context input. Conversely, Gurriel's
2023 history included 50 DH starts but his following season had only three.
Judge's late-2023 use was RF/DH even though his separately dated December
expectation was CF. Recent history helps; blindly continuing it also misses.
Assignment reports remain diagnostics here, not manually inserted forecasts.

Eldridge's four 2024 levels show only **1B and DH**. His AAA record is seven 1B
starts and one DH start in September; AA adds eight 1B starts and one DH start.
Those brief upper-level stints must not erase 85 lower-level 1B starts. His
earlier RF use is real: 296 Single-A outs and 318 complex-league outs in 2023.
There is no cutoff-known 2B/3B history to explain the prior candidate's 46 combined
outs there. Bride and Aranda were different: their own origin records already
contained substantial 2B/3B use. A shared primary 1B label discarded that
difference. Wagaman's two prior 3B starts are also real, but he had no represented
August-onward record in that season; a missing late stint is not a zero-role
vector or proof he forgot a position.

Carter is the opposite caution. His short September MLB use was mostly LF,
while his larger AA record was mostly CF. Dawson had just one MLB DH start but
a substantial AAA outfield record. Giving either a blanket current-MLB-only role
would compress important evidence. Chourio's six-game AAA assignment was mostly
RF, but his larger AA role was CF. A highest-level-only rule would exaggerate
that tiny late stint. Their complete level records and non-arriving peers remain
in the trace; no later MLB quality is inferred for non-arrivals.

Rafaela's 2024 logs retain both SS and CF. They do not tell us, by themselves,
that his next season will be CF/2B. Hernández legitimately has a wider repertoire.
Kirk's current catching use should not be displaced by much older DH volume,
but his five late-2024 DH starts are not a permanent switch either. Bailey and
Raleigh still have important fixed workload or quality errors. Alvarez, Acuña,
Reyes and several catcher peers show how opportunity losses can overwhelm a
sensible role. Abrams's near-perfect old final value still concealed a large
defensive-quality miss. Franco's late record ending August 12 cannot be used as
a talent diagnosis; the old fixed opportunity anchor omits later availability
repairs. These are separate failures, not reasons to tune position totals until
the value error happens to cancel out.

## Existing PBP can supplement roles but cannot replace innings

The inventory covers **244 files and 7,034,246 terminal-PA snapshots** from
2016–2019 and 2021–2024. Dates are populated and parse correctly. All eight
fielder IDs are present except for 21 High-A rows in June 2024, where all eight
are missing. The fixed cases have 15,732 distinct observed position-game
presences. These counts describe the files that exist, not certified complete
league coverage. Rookie aggregates do not establish DSL coverage. The canceled
2020 MiLB season is not evidence of zero defensive ability.

A snapshot can show that someone appeared at a position on a date. It does not
give exact innings, starting status or DH use. The official logs provide those
denominators for the reviewed scopes. Do not count terminal PAs as defensive
innings or treat missing snapshots as absence.

## Failed sources and claim limits

The plural `sportIds` request silently supplied MLB-only records. It returned
nothing for Eldridge and omitted Buxton's known AAA use. The successful route is
an explicit singular `sportId` request for each represented level. The initial
responses and additive scope amendment are retained; an empty result was never
converted into zero minor-league usage.

The date-range endpoint advertised 775 total splits but returned none. It cannot
supply a usable late-season denominator. All recent-period calculations instead
use verified game logs, split at the predeclared August 1 date. This split is a
source diagnostic, **not a chosen model recency weight**.

The source walkthrough is complete, including all original peers and the five
additional contrasts. No model was fitted or scored, so there is **no accuracy
gain to report**. Source integrity, predictive improvement and permission to
deploy remain separate. The frozen forecasts, explorer and 2026 selection are
unchanged. The separate Lovich small-sample batting defect is still open.

## Next repair

Use one coherent role comparison after population-wide input readiness, not
another algorithm or prior-strength tournament. Keep a full observed repertoire
separate from current assignment; preserve each level's actual sample and dates;
distinguish no current MLB record from observed pure DH; and retain plausible
position changes without importing every infielder's jobs into every first
baseman. Small September stints and temporary health-related assignments need
explicit reliability and fallback rules.

Before fitting, declare those rules for every training and forecast row, verify
the cutoffs and distinct-player support, and certify any expanded dated source
scope. The 74 reviewed player-seasons alone cannot supply the whole model's
features. Do not fit only the chosen examples or pretend PBP has exact innings.
Keep the same 12,432 evaluation identities, quality and batting recipes, PA,
physical budgets and missing-player reserves. Score individual position use,
position runs, delivered defense and expanded value separately; then repeat the
fixed player and peer walkthrough before any disposition. This tests assignment
and delivery. Lower-minor defensive talent and longer-horizon player valuation
remain separate unfinished parts of the active goal.
