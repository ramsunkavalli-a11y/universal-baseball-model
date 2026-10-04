# Korean professional batting history is collected and reviewed

2026-10-04. Official first-team regular-season KBO batting is now collected for
2005–2024 without a member login. The complete collection and its independent
reconstruction are finished. This supersedes the pending-collection checkpoint,
not the earlier receipts. It is a usable source, not evidence of better forecasts.

## Coverage and verification

The collection contains 6,473 player-season rows and 976,828 PA, including 1,460
zero-PA rows. Both official stat groups have identical player-ID membership in
each season. All 110,041 normalized count fields were reconstructed separately
from archived player pages, and sixteen summable count fields match official
team totals in every season. Player games are not summed into team games.
Expected club counts account for the 2013 and 2015 expansions: eight, nine and
ten clubs in their respective periods. Korea's actual 2020 season remains present;
the absence of affiliated US minor-league baseball does not remove it.

There are fifty PA not enumerated by the displayed outcome columns. They remain
explicit residuals, not invented outs. Undefined rates remain missing. The two
bulk groups provide seventeen counting fields, but not SB/CS, historical positions,
all-player birthdays or stint-level park exposure. Pitcher batting remains in
the source and must not be mistaken for an approved hitter population.

Seven player cases are reviewed, including all six earlier cases and an ordinary
2013 expansion-season player selected by a fixed ID rule. Sixteen positive-PA
recent season lines match thirteen shared counts each in the official English
rendering. That is 208 matched counts from another rendering of the same provider,
not independent-provider validation. The ordinary 2013 player has seven PA and
an absent English display name; the Korean name and source ID are retained, and
no MLB identity is guessed.

The new history helper uses only years at or before the origin. Future-row
deletion and adversarial mutations leave the seven reviewed histories unchanged.
An incomplete three-year source window cannot become a complete rate feature.
An absent row in a fully collected year means no recorded first-team PA, not
zero talent, poor health or no Futures/other-league work. Professional experience
before 2005 remains unknown. Sixteen KBO tests pass; the combined KBO, NPB and
preseason-source suite passes all forty-two tests. All thirty-one protected files
remain unchanged. No new fits, forecasts or protected outcomes were used.

## What the histories show

Jung Hoo Lee's 2021–2023 history contains 1,558 PA and a 5.91% K rate. Ha-Seong
Kim's 2018–2020 history contains 1,823 PA and a 12.56% K rate. Hyeseong Kim's
2022–2024 history contains 1,754 PA and a 12.66% K rate. These are substantial
professional records, not empty domestic-history fallbacks.

Byung-Ho Park's 2013–2015 history has an 8.12% HR rate and a 22.81% K rate.
Eric Thames' 2014–2015 history has a 7.57% HR rate and a 17.13% K rate; the
fully covered 2013 season has no KBO first-team PA for him. This does not mean
he was inactive elsewhere. Their similar power and different strikeout profiles
argue for separate component translation rather than a generic league bonus.
None of these raw rates is already park-adjusted or translated to MLB.

Hyeseong Kim's unchanged 2024-origin saved inputs also need a cutoff review:
age was imputed as 27, position unknown, stage inactive, and 40-man status zero.
The separately collected January 24, 2025 ledger lists him at second base on the
Dodgers' 40-man roster and records a January 3 agreement. His verified birth date
is January 27, 1999. The old expected MLB PA is still 0.3409. This establishes
missing input evidence, not a corrected prediction. Among 30,506 matched old
forecast rows, 107 have old negative/new positive 40-man flags and 36 the reverse.
Different cutoff dates and roster semantics must be checked before calling all
143 differences errors or overwriting them.

## Remaining integration work

Only five fixed cases have verified MLBAM joins; a complete cross-league identity
mapping is not yet qualified. Current profile salaries, retirement labels and
roles cannot be reused as historical predictors. Records downloaded today do
not independently establish their original publication vintage.

Continue the existing foreign-history and preseason-population integration plan:
verify dated identity, age, role and employment context; estimate component-wise
league translations with adequate historical mover support; then compare on
fixed original and additional-player cohorts with player walkthroughs. Separate
conditional MLB talent from the chance of an MLB job. Do not promote raw foreign
rates, alter the frozen forecast, rerun closed team-record tests, or claim the
practical hitter goal is complete.

[Player walkthrough](../reports/model-evidence/kbo-hitting-history/player-walkthrough.md)
and [aggregate review](../reports/model-evidence/kbo-hitting-history/review.json)
record the source checks and hashes. The immutable private collection remains in
`reports/generated/kbo-hitting-history`; raw pages remain in
`data/quarantine/kbo-hitting-source-probe`. Bulk data are not committed publicly.
Primary sources are the [KBO historical player forms](https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx),
[team counts](https://www.koreabaseball.com/Record/Team/Hitter/Basic1.aspx) and
[official English player records](https://eng.koreabaseball.com/Teams/PlayerInfoHitter/Summary.aspx?pcode=67304).
