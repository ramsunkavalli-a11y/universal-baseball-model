# Public top-50 separated-outcome audit

Status: diagnostic only; outside rank and FV are not model inputs.

Matched 42 of 50 outside top-50 players to the current pre-MLB foundation.
The other 8 had reached MLB by the current checkpoint or had prior MLB experience; they are graduates, not missing prospect rows.
The comparison uses within-player-type percentiles because hitter and pitcher
partial-WAR scopes are not interchangeable. `model_lower_review` is a review
queue, not proof that either side is wrong.

| Assessment | Players |
|---|---:|
| broad_agreement | 31 |
| graduated_or_prior_mlb | 8 |
| model_lower_review | 3 |
| partial_agreement | 8 |

## Willits and Gonzalez

| Player | Public rank/FV | Exact level | Raw current PA | Arrival | Conditional rate | Expected 4y partial WAR | Assessment |
|---|---:|---|---:|---:|---:|---:|---|
| Eli Willits | 7/60 | HIGH_A | 527 | 38.0% | 1.32 | 0.65 | broad_agreement |
| Josuar Gonzalez | 30/50 | SINGLE_A | 275 | 28.0% | 1.06 | 0.19 | partial_agreement |

## Model-lower review queue

| Player | Public rank | Type | Exact level | Raw workload | Arrival | Conditional rate | Basic reason |
|---|---:|---|---|---:|---:|---:|---|
| Roch Cholowsky | 19 | hitter | HIGH_A | 46 | 12.0% | 1.04 | small current sample and low four-year arrival frequency |
| Kendry Chourio | 41 | pitcher | SINGLE_A | 354 | 17.3% | withheld | pitcher quality signal failed validation; arrival remains low |
| Roldy Brito | 48 | hitter | SINGLE_A | 553 | 21.3% | 0.90 | large low-level sample but modest arrival and conditional batting outcomes |

## Boundary

Expected outcome covers only the next four calendar years and includes batting
or pitching plus replacement. It is not six-year controlled WAR. Conditional
pitcher quality is withheld, and hitter conditional quality is shown only with
at least ten neighboring MLB arrivals. No FV inference is permitted from this audit.
