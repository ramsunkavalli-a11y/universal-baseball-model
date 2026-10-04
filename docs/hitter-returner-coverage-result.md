# Missing returners and preseason population timing

2026-10-04. The current research forecast has a small, confirmed coverage hole:
its later preseason prospect rankings do not update its earlier player population.
Established hitters absent from the prior season can therefore be missing even
after securing another opportunity. This does not explain the much larger
playing-time errors among players who already have forecasts.

The [source audit contract](hitter-returner-coverage-contract.md) was saved before
the new audit. No models were fitted, no player prediction changed, and all
30,506 original evaluation rows remain. Missing rows are not zero predictions.
The earlier [value ledger](hitter-season-value-ledger-result.md) and all its
receipts stay intact; this review supplies the previously pending Conforto
source check and narrows the next population repair.

## What the population builder does

The builder combines origin snapshot people with a window-complete older
post-arrival panel. That older source covers only elapsed years zero through
five. Roster status becomes a feature, not an extra source of eligible people.
For older players absent from the snapshot, the support source cannot rescue
membership. That is exactly what happens to Conforto, Sanó and Alfaro.

The later preseason extension deliberately changes only prospect-ranking inputs;
its contract preserves all other prior-December features and membership. The
dates in its saved forecasts are ranking information dates, not proof that all
player inputs or rosters were refreshed then. This is not a newly discovered
future-information leak or an incorrectly dated December roster. It is incomplete
population coverage for a comprehensive forecast offered at the later date.

The mechanical builder was replayed for every reviewed person, including cases
where snapshots preserve older absent players. Cespedes, Wright and Tulowitzki
remain eligible even though the older support panel cannot include them. Do not
claim that every hitter disappears after six years or every absence removes a row.

## How large this particular gap is

The deliberately permissive, outcome-blind review population contains positive
MLB batting in the previous three calendar seasons, with latest-season largest
stint position not pitcher code 1. It includes unemployed/retired people and
non-primary position codes; it is not an approved current-hitter or job rule.
Foreign newcomers and people without recent MLB history are outside this check.

| Forecast season | Review population | Missing origins | Missing non-returners | Missing returners | Missing next-year PA |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2017 | 880 | 83 | 83 | 0 | 0 |
| 2018 | 876 | 72 | 72 | 0 | 0 |
| 2019 | 868 | 88 | 88 | 0 | 0 |
| 2022 | 846 | 81 | 81 | 0 | 0 |
| 2023 | 905 | 87 | 86 | 1 | 470 |
| 2024 | 946 | 99 | 98 | 1 | 95 |
| 2025 | 927 | 100 | 99 | 1 | 39 |

Across 6,248 reviewed player-origins, 610 are missing; 607 never play the next
MLB season. The three returners supply 604 PA in total. No omitted candidate
appears in the stored origin-year roster. These are player-origin records, not
610 distinct players or 610 probable jobs. Merely adding all old hitters cannot
be assumed to improve calibration or any existing matched loss.

## Dated signing evidence

Conforto's signing was [officially announced January 6, 2023](https://www.mlb.com/press-release/giants-agree-to-two-year-contract-with-outfielder-michael-conforto).
That precedes the saved January 26 ranking date. [Sanó's agreement was reported
January 23, 2024](https://www.espn.com/mlb/story/_/id/39372420/miguel-sano-signs-minor-league-deal-angels),
before January 26, while his current official transaction history records
February 1. Reported agreement and recorded official date are not interchangeable.
[Alfaro's Brewers transaction is dated January 16, 2025](https://www.mlb.com/brewers/roster/transactions/2025/01),
before the saved January 24 ranking date.

These dated original/official sources are reviewed historical evidence, not
certified contemporaneous captured tables or new fitted features. The precise
historical preseason roster reconstruction remains undone. The audit does not
backdate an official roster, assign the three named players custom probabilities,
or use a later successful return to select new eligibility.

## Actual player checks

Nine distinct player-origin walks are saved with raw PA/HR/K/walk history,
snapshot/support/roster joins, original model intermediates where a row exists,
and four comparisons selected without future outcomes. The [walkthrough](../reports/model-evidence/hitter-returner-coverage/player-walkthrough.md)
includes both returns and failures:

- Conforto had 479 MLB PA and 14 HR in 2021, no 2022 MLB production, and no
  origin row forecasting his 470 PA in 2023. His hitting forecast was missing,
  not zero or statistically rejected.
- Sanó's 532 PA/30 HR in 2021 fell to 71/one in 2022; he is absent at the
  2023 origin and later receives 95 PA. A minor agreement is not entitlement to
  regular playing time or a restored earlier hitting rate.
- Alfaro's 274 PA/seven HR in 2022 and 52/one in 2023 are still available,
  but the 2024 origin is absent. His 39 PA return is a small coverage failure.
- Wright and Tulowitzki are retained despite zero origin-year MLB PA and
  older careers; they receive only three and thirteen next-year PA. Snapshot
  retention and future playing capacity are different questions.
- Cespedes is retained and receives no next-year PA. Davis, the later Belt
  origin and Abreu are omitted and also receive none. A generic return boost
  would not be justified by these cases. Belt's retained forecast for 2024
  remains a separate, already-reviewed surprising employment miss.

The peers match last MLB season and three-season PA similarity only. They are
source contrasts, not equivalent talent, age, contract or health comparisons.
No downstream forecast is fabricated for a missing origin.

## Verified limits and next repair

All 6,248 review identities reconstruct independently; removing or altering
future rows leaves eligibility unchanged. The actual population union replays,
all three positive omissions and non-return examples are reviewed, the previous
ledger hashes verify, sixteen focused tests pass and 31 protected files remain
unchanged. Source review completion does not approve the permissive inclusion
rule, certify retirement status, or validate a repaired forecast.

Use a separately declared, systematic preseason population refresh through the
same information date as the projection, not three named exceptions. Preserve
existing forecasts as the matched benchmark and score new rows separately.
Audit new contracts/roster eligibility, free-agent ambiguity and foreign entrants
before fitting. Do not repeat a model sweep or use this small hole to explain
Kurtz, Kwan, Judge or other already-covered workload/talent misses. Their existing
failed forecasts remain in scope, and the full hitter goal remains active.
