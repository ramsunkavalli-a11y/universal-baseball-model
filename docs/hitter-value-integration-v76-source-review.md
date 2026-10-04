# Checking the batting contribution response before fitting

2026-10-03. Source review complete for the integration comparison. No new models
have been fitted at this checkpoint. All eight event responses independently
match the dated MLB counts for every one of the 63,282 source rows; their sum
equals actual future MLB PA. Reconstructed common-origin value matches the
compatible-value source and all 30,506 current scored responses. This is source
and arithmetic evidence, not a new predictive result.

## Response arithmetic and named checks

The following observations are historical target labels, not inputs available
to the player's earlier forecast. Event counts are mutually exclusive: an HR
is not also a single, and intentional walks are not unintentional walks. The
residual category includes other PA outcomes. Each raw count must be nonnegative.
The common-origin contribution calculation subtracts the known origin MLB
average event index from the realized event-weighted production and adds the
schedule-corrected replacement reference once.

| Player and origin | Actual next year MLB PA | Actual HR | Actual unintentional BB | Reconstructed custom contribution | Current expected PA |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kurtz 2024 | 489 | 36 | 60 | 5.837777 | 10.184 |
| Langford 2023 | 557 | 16 | 48 | 1.795953 | 214.918 |
| Julio Rodríguez 2021 | 560 | 28 | 36 | 3.937064 | 254.107 |
| Alonso 2018 | 693 | 53 | 66 | 6.598031 | 215.033 |
| Judge 2024 | 679 | 53 | 88 | 9.393216 | 530.753 |
| Maitan 2017 | 0 | 0 | 0 | 0 | 1.985 |
| Reynolds 2018 | 546 | 16 | 46 | 4.695907 | 12.670 |
| Lugo 2017 | 101 | 1 | 7 | -0.234617 | 81.899 |

For Kurtz, the 489 PA comprise 154 other outcomes, 151 K, 60 UBB, two HBP,
58 singles, 26 doubles, two triples and 36 HR. Against the 2024 origin index
.30533385 and replacement .003122875/PA, they yield 5.837777 custom contribution.
The model was entitled to his fifty professional A/AA PA at forecast time, not
that subsequent MLB success. The existing ten expected PA remains an anchor,
not a response relabeled to make the player look correct.

Langford's 200 professional PA include 80 AA/AAA PA; Julio's 340 A+/AA PA follow
the canceled 2020 MiLB season, not a zero-talent season. Alonso's 574 AA/AAA PA
and 36 HR represent substantial power evidence. Their actual first MLB seasons
have different workloads and production; a common prospect multiplier cannot
be inferred from their successful outcomes alone.

Judge's 704-PA, 58-HR origin season and two earlier MLB seasons supply extensive
MLB evidence. His observed 9.393216 here is custom batting-plus-replacement
contribution, not published full WAR. Maitan's 176 rookie PA at age seventeen
have zero next-year MLB contribution but no observed future MLB batting rate.
Reynolds' 383 AA PA, seven HR and forty walks do not imply the observed 546
MLB PA was guaranteed; they do identify a material existing false-low case.
Lugo's 557 AA PA and thirteen HR lead to 101 MLB PA with negative contribution:
the response must retain this negative value, not feed it into a Poisson loss.

## Provenance and claim limits

Seventy actual full/active checks and 105 current saved-head replays are sealed
before new fitting. Predictor transformations use the existing audited graph
at each row's own origin and exclude the whole tested player fold. The eight
origin environment shares and replacement reference are known aggregate context;
target environment and future counts remain labels only. Each model's actual
full or active subset is recorded separately.

The first preparation attempt omitted raw age from review-only metadata; the
second used a numerical finite check directly on a column object unsupported by
the installed library. Both were repaired before the preflight was sealed or
any new model fitted. Features, targets, parameters and evaluation identities
did not change. Counts and unit arithmetic passed before these execution fixes.

Current and translated-linear anchors remain unchanged. Missing foreign
production, historical prospect-list date qualifications, unsupported profile
intersections and older roster-only membership limitations remain visible.
Protected 2026 outcomes are not read. The [contract](hitter-value-integration-v76-contract.md)
controls fitting and scoring. Actual forecast walkthroughs are still required
after the experiment; this source review cannot substitute for them.
