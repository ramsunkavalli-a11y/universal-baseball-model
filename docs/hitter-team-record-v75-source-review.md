# Team record source audit and player checks

2026-10-03. The team's completed prior record is not an input in the current
251-input opportunity model. Earlier roster-capacity comparisons do not settle
this different hypothesis. The historical context has now been reconstructed
and reviewed; no playing-time models were fitted and no forecasts changed.

## What the source can provide

Across 63,282 source rows, 55,366 have a usable MLB record after dated club,
roster and transaction reconciliation. In the unchanged 30,506-forecast
evaluation population, 28,894 have usable context; among 24,199 never-debut
forecasts, 23,174 do. All unknowns and non-arrivals remain in the cohort.
The historical affiliation listing correctly captures Nashville's transitions
from Oakland in 2018 to Texas in 2019 and Milwaukee in 2021.

The first source pass is preserved. Dated acquisitions/releases supply 11,406
source-row overrides, including confirmations of the same parent, not 11,406
proven errors. A further 282 rows have no resolved owner after a rights event.
Unknown records stay unknown, not .500 evidence. Full minor-league rights and
pre-2015 transactions are not certified, so last-club ownership remains a
qualified proxy when no better evidence exists.

## Eight player walkthroughs

The machine-readable review contains actual three-year level statistics,
all 251 existing opportunity inputs, the proposed record input, source dates,
the unchanged appearance and conditional-PA forecasts, actual subsequent MLB
counts, and four peers selected using only origin-known profiles per player.
Those peers retain both later arrivals and failures. The source review does
not generate or attribute a new model improvement.

| Player and origin | Dated MLB organization record | Current expected PA | Following year MLB PA | Check |
| --- | --- | ---: | ---: | --- |
| Nick Kurtz 2024 | Oakland 69–93 | 10.2 | 489 | Draft signing confirms parent; weak club context cannot substitute for readiness |
| Wyatt Langford 2023 | Texas 90–72 | 214.9 | 557 | Strong club still provided substantial debut playing time |
| Julio Rodríguez 2021 | Seattle 90–72 | 254.1 | 560 | Dated roster supplies organization; existing readiness still matters |
| Pete Alonso 2018 | New York Mets 77–85 | 215.0 | 693 | Las Vegas was a Mets affiliate then, not Oakland |
| Cody Bellinger 2016 | Los Angeles Dodgers 91–71 | 102.6 | 548 | A contender can promote and use an excellent prospect |
| Jackson Holliday 2023 | Baltimore 101–61 | 351.2 | 208 | Opposite error direction to the underpredicted debutants |
| Kevin Maitan 2017 | Los Angeles Angels 80–82 | 2.0 | 0 | Last batting club falsely implied Atlanta; dated signing corrects owner |
| Aaron Judge 2024 | New York Yankees 94–68 | 530.8 | 679 | Established-player primary forecast must remain unchanged |

Maitan's December 16 signing is present in the existing transaction capture
and independently corroborated by [the Angels report](https://www.mlb.com/angels/news/angels-agree-with-kevin-maitan-livan-soto-c262892874).
This led to a general source rule, not a player-specific patch. A separate
2020 Freitas discrepancy was traced to the already-repaired forty-man capture
being stored outside the older all-years roster table; that capture is now
included. Origin-2020 MLB winning percentage uses actual wins plus losses,
while canceled minor production remains unobserved.

## What to test and what not to conclude

The [locked comparison](hitter-team-record-v75-contract.md) adds only record
and its knownness indicator, holds hitting fixed, and includes a control with
knownness alone. This isolates record information from source availability.
Read the [source amendment](hitter-team-record-v75-source-amendment.md) with it.
Full/active training-fold support checks must precede any fits. After scoring,
saved-model player reviews are required before retaining or rejecting the idea.

A prior poor record could open a prospect opportunity, but it could also
correlate with weaker organizations or a rebuilding timetable. Strong teams
also promote young players. These are competing hypotheses, not conclusions
from the eight examples. The future season's record is never an input. No
claim is made yet that this improves PA, fixes the COVID-related cohort error,
or improves player value. The research candidate and protected 2026 stay unchanged.
