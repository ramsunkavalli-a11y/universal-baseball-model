# Player-error audit: what is slipping through and why

2026-09-23. Diagnosis only; no input repair, model upgrade or live forecast change.

## Bottom line

The misses are not all one problem. We found confirmed historical cohort and
roster-vintage issues, plus identifiable weaknesses involving low recent PA,
brief upper-level promotions, position and the timing of MLB opportunity.
Fix source semantics before interpreting every miss as a modeling failure.

## Representative player cases

These are the latest AE research candidate probabilities of any MLB PA the
following year, not batting talent or eventual career value. Selected cases
illustrate mechanisms; low-probability successes are expected in a calibrated model.

| Forecast made after | Player | Probability | Following-year MLB PA |
|---|---|---:|---:|
| 2021 | Jeremy Peña | 4.4% | 558 |
| 2021 | Ezequiel Duran | 1.6% | 220 |
| 2021 | CJ Abrams | 4.4% | 302 |
| 2022 | Patrick Bailey | 1.7% | 353 |
| 2022 | Zach Neto | 3.8% | 329 |
| 2022 | Malcom Nuñez | 82.0% | 0 |
| 2022 | Moisés Gómez | 77.3% | 0 |
| 2022 | Connor Norby | 80.1% | 0 |

## 1. Confirmed source problems

The 40-man source is October 15, while these are reconstructed year-end forecasts.
Peña was added November 19, 2021. [Astros transaction record](https://www.mlb.com/astros/roster/transactions/2021/11).
Duran was also added that day. [Rangers transaction record](https://www.mlb.com/rangers/roster/transactions/2021/11).
Both remain zero in the current input flag. Holding everything else fixed,
flipping that flag changes Peña from 4.4% to 34.3%, and Duran from 1.6% to 18.5%.
These are mechanical sensitivities, NOT validated replacement forecasts.
A proper fix must rebuild every training/query vintage consistently, including removals.

The debut table also omits earlier MLB players. Rubén Rivera debuted in 1995
([MLB record](https://www.mlb.com/player/ruben-rivera-121252)); Óscar Robles debuted
in 2005 ([MLB record](https://www.mlb.com/player/oscar-robles-425854)). Both are marked
as never-debuted prospects in 19 historical snapshots combined because missing debut evidence becomes false.
Therefore the archived prospect labels are not fully certified. Do not quietly rewrite old reports.

In 2017, 286 of 585 labeled AAA prospects have a Mexican League snapshot team;
none has next-year MLB PA in the target. Captured raw statistics identify league 125 (MEX).
The historical AAA classification does not make those players the same MLB opportunity
population as affiliated AAA. Retain relevant international players but distinguish
league/affiliation and veteran returners. Do not delete them merely because they are negatives.
How much this changes modern forecasts is not yet measured.

## 2. Low current workload can hide readiness

Peña (160 PA), Abrams (183) and Neto (167) have current PA among their largest
negative model contributions. That is a verified description of these fitted trees,
not proof every small sample should receive a boost. Reasons for short exposure differ.
Peña had wrist surgery in 2021. [Contemporaneous report](https://www.mlb.com/news/jeremy-pena-among-astros-prospects-added-to-40-man).
Neto was a first-round college selection. [2022 draft report](https://www.mlb.com/amp/news/zach-neto-drafted-no-13-by-angels-in-2022-mlb-draft.html).
Recent-draftee context is not equivalent to missed time or a long-term low-opportunity role.
Kurtz (50 PA, 7.8%), Cam Smith (134 PA, 5.2%) and Caglianone (126 PA, 1.7%)
are further low-current-PA examples in the 2024-origin casebook; all exceeded 200 MLB PA in 2025.
This arrival recipe has no explicit draft/college/pedigree features. Their predictive value remains to be tested.

## 3. A taste of Triple-A can receive a large readiness boost

Nuñez had only 17 AAA PA out of 493 total, and Norby 42 out of 547.
Ending at AAA is the largest positive contribution in both reviewed forecasts.
Level shares and partial-promotion features already exist; this is not simply absent data.
The question is how those features interact with season-ending level and total workload.
In the 2022-origin AAA group with under 10% AAA PA, AE expects 18.3 arrivals versus 11;
in 2023, 7.9 versus 5; in 2024, 5.9 versus 4. But 2021 still underpredicts this group.
A universal discount would therefore be unjustified.

## 4. Position and a defensive route to a roster spot

This arrival recipe has no explicit defensive-position or defensive-value input;
those components exist elsewhere in the broader value project. The distinction matters.
In 2022-origin forecasts, first basemen plus corner outfielders receive 52.4 expected
arrivals versus 19 observed; SS/CF receive 49.8 versus 50. The same directional split
appears in 2023: corners 45.4/22, SS/CF 42.4/41. These are unadjusted descriptive slices,
not proof of a causal defensive effect or an independently validated position correction.
Bailey, Delay and Serven illustrate a catcher path the batting-heavy arrival recipe
may underrepresent; catcher overestimates such as Ronaldo Hernández also exist.

## 5. Being early is not the same as being wrong about eventual arrival

Of 41 2022-origin cases with >=50% probability but zero MLB PA in 2023,
22 had MLB PA in 2024 or 2025. Norby, Barger, Pages and Manzardo are examples.
The other 19 still had none through that three-year window. This does not prove
those 19 could never succeed. Zero PA also need not mean zero MLB games.
Next-year timing, eventual arrival and sustained valuable MLB work need separate scoring.

## Priorities

1. Certify complete debut history and distinguish historical league/affiliation populations.
2. Align roster information with the actual declared forecast cutoff, for all vintages.
3. Then test position/defensive access, reason for short exposure, and promotion depth.
4. Evaluate timing separately from later arrival and delivered value; no player-specific overrides.

## Verification

19,247 archived prospect-labeled player-origin cases inspected. Two unchanged model
replays reproduce saved predictions exactly; 84 selected cases have additive tree
contributions checked against predicted probabilities. Outcomes stop at 2025.
All pattern searches are exploratory. No causal repair gain is claimed.
See casebook.md, report.json, source-findings.json and player-cases.parquet in this folder.
