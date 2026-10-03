# Repaired 2020 cohort: useful source repair, not the forecasting solution

2026-10-02. Source and experiment player reviews complete. Practical hitter goal
remains active. No protected 2026 results, frozen forecasts or deployed explorer
were changed.

## What changed

Reconstructed 5,133 observable origin-2020 hitters rather than retaining 597
incomplete legacy rows. Historical roster-row positions, actual 2020 MLB counts,
previous minor-league records and immutable birthdates define this population.
The canceled MiLB season is not invented production or evidence of retirement.
All 597 old identities are retained; all non-2020 source rows are bit-exact.
This observable population covers every 2021 MLB hitter in the audited target.
The 4,782 PA outside it belong to pitchers batting, not missed hitter arrivals.
Unobserved international entrants still cannot be claimed as a complete roster.

The comparison keeps the same 199 model features, fixed settings, 30,506 test
rows, whole-player folds and next-year targets. Only later training sets receive
the reconstructed cohort. Forty new heads replay exactly; earlier forecasts are
bit-exact. Target-2020 forecasts remain excluded. Contracts:
[source reconstruction](practical-hitter-2020-cohort-contract.md) and
[fixed comparison](practical-hitter-2020-extension-test.md).

## What the comparison found

| Identical test population | V33b PA RMSE | Repaired-source PA RMSE | V33b value RMSE | Repaired-source value RMSE |
|---|---:|---:|---:|---:|
| All 30,506 rows | 61.619 | 61.652 | 0.44121 | 0.44060 |
| V24 matched, 4,396 rows | 124.651 | 124.889 | 0.90951 | 0.90886 |
| Earlier N matched, 21,819 rows | 61.225 | 61.271 | 0.44458 | 0.44424 |
| Public active matched, 1,789 rows | 143.965 | 144.487 | 1.01787 | 1.01638 |

All source-extension paired 95% player-cluster intervals include no difference.
For the public rows, PA squared-error change is +150.7, interval −78.1 to +422.5;
value squared-error change is −0.00303, interval −0.01212 to +0.00477. These are
development comparisons, not a fresh untouched holdout.

Public Steamer PA RMSE is 135.019 and MAE 92.399; repaired-source MAE is 111.577,
20.8% worse, still outside the plan's 15% tolerance. Public knowledge-date and
count-to-value conversion differences remain qualified. Value here is batting
plus replacement, not full WAR; a converted-value win cannot establish better
pure hitting talent. The near-zero rows make the all-population RMSE look small;
do not use that number alone to call this model decent.

## Baseball checks

2021 expected PA increases 166,920 to 168,633 versus 181,583 actual: an improvement
of 1,713, with a 12,950 shortfall remaining. 2023 allocation worsens, rising to
185,096 versus 182,194 actual. Across test years, upper-minor PA remains about
9,637 short; lower-minor allocation remains about 4,713 too high. These are fixed
matched-cohort totals, not full league totals forcibly normalized to an answer.

Fifteen complete stats → inputs → saved-fit terms → forecasts → actual walkthroughs
are in `reports/generated/practical-hitter-v34/player-walkthrough.md`, with
machine-readable evidence in `cases.json` and manual judgments in
[the case ledger](../config/practical_hitter_v34_case_notes.json).

Judge's 2024 forecast rises 534 to 548 PA and 5.68 to 5.88 batting-plus-replacement
wins, versus 679/9.23 actual. Riley loses projected PA despite a known 662-PA,
33-HR season: 579 to 530 versus 693 actual. Kurtz falls 50 to 42 PA versus 489
actual; his fourth-overall college pedigree is present, not newly discovered.
Lux's missed-season return improves 200 to 215 PA versus 487 actual, but generic
inactive peers are mostly failed marginal players. McLain's apparently close
value still masks large opposing workload and batting-rate errors. McNeil 2018
is correctly unchanged: later training outcomes cannot repair an earlier forecast.

## Decision and next step

Keep the source repair. Do not call it an established forecasting gain or
automatically promote V34 over V33b. Use the repaired-source version as the
fixed control for the next research comparison, retaining V33b as an anchor.
Missing 2020 origins were a real flaw but are not the main explanation for
opportunity, fast-entry and brief-debut talent misses.

Next test the representation of competing MLB/MiLB evidence and sample reliability
within the existing model family. A brief poor debut should not automatically
erase a much longer strong upper-minor record; equally, old minor-league success
must not dominate years of MLB evidence. Learn and test that distinction rather
than hand-boosting a few famous prospects or launching another library sweep.
