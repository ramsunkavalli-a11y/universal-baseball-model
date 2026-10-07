# Double play data can support a limited MLB history test

2026-10-07. Separate adjusted MLB double-play credit exists and is not already
included in the reviewed twelve-channel defense assembly. Keep it separate from
range and first-base receiving. The source audit and player review are complete;
no double-play forecast has yet been fitted, scored or deployed.

## What the data measures

All 13,304 native position rows in 2016–2025 replay against their saved raw
responses, including individual component sums and independent official innings.
There are 4,995 infield rows with known DP credit and 4,990 with certified
exposure. Null credit remains unknown, not an observed average defender.

The responses contain `dp_runs` but no eligible DP chances, initial/pivot roles
or expected conversions. Batting PA and defensive innings are not those missing
opportunity counts. Raw minor `doublePlays` counts do not contain the difficulty
adjustment. [Savant defines the separate channel](https://baseballsavant.mlb.com/leaderboard/fielding-run-value)
as 0.4 runs for an added double play. Its native credit can be used without
reconstructing the adjustment, but a runs-per-inning forecast must assume future
traffic broadly resembles the reference setting; it cannot isolate mechanical
conversion talent from chance frequency.

Annual saved league totals range from −13.20 to +7.36 DP runs rather than being
exactly zero. No omitted pitcher DP credit explains this: whole raw totals match
infield totals. This small offset is retained, not forced to zero or called an
extraction bug. The tracking-era boundary around 2020 and the limited eligible
play scope remain measurement qualifications. The audit does not certify the
underlying vendor model, historical publication dates or equal error by era.

## Which players can be tested

The source preserves 4,776 MLB-history and 45,095 minor origin-position records.
MLB eligibility inherits the existing range-history origins, not all people with
any DP measurement. Quality is pooled same-position DP credit over the next three
calendar years, with at least 500 innings across two measured seasons and no
positive official exposure with missing qualified DP credit. It measures later
adjusted MLB quality, not arrival, WAR or six years of control.

| Origin and population | Eligible people | Eligible positions | Measured people | Measured positions |
| --- | ---: | ---: | ---: | ---: |
| 2021 MLB history | 454 | 859 | 150 | 166 |
| 2022 MLB history | 469 | 884 | 145 | 159 |
| 2021 minor prospect | 1,828 | 3,535 | 43 | 46 |
| 2022 minor prospect | 1,818 | 3,510 | 34 | 37 |

At the 2022 cutoff, fully matured training labels supply 162–191 distinct earlier
MLB-history people after each held-player exclusion. Minor training supplies
70–85, but almost no measured rookie/DSL target examples; modern lower-level
quality cannot be inferred from large unmeasured cohort counts. Three-year
non-arrivals and position changes are unknown same-position quality, not poor
defense. The 2021 origin is a separate stress check. Canceled minor time in 2020
is not an invented zero season. All 49,871 labels, 56 groups and 20 support folds
replay independently.

## Player checks

These are unshrunk source rates and measured future rates, both DP runs per
500 innings. They are not fitted grades. The walks cover 30 player origins and
73 position records, including annual paths and three origin-only peers for
each fixed source case. Peers are chosen by position/level, age and recorded
exposure, not by later success.

- Semien 2B: recent −0.657 becomes future +0.340. Straight persistence would miss
  the direction. His peers Wong, Leury García and Muncy lack enough later 2B
  measurements or leave the position; none becomes a zero-quality observation.
- Giménez 2B: +0.225 versus future +0.549. His 2023/2024 credit is positive,
  2025 negative. Paredes, Rodolfo Castro and Nick Allen have insufficient later
  same-position samples, so they do not corroborate a talent claim.
- Lindor SS: +0.060 versus +0.355. Swanson falls from +0.923 to +0.138; Seager
  moves from −0.854 to approximately zero; DeJong from +0.044 to −0.668. These
  ordinary comparisons show why both signs and small samples need regression.
- Arenado 3B: +0.427 versus +0.199; Muncy +1.221 versus +0.159. Duffy has 61
  official third-base outs in 2024 without DP measurement, making the complete
  future quality label unknown rather than an inferred zero-credit season.
- Goldschmidt 1B: +0.024 versus +0.059. This is distinct from receiving throws.
  Solano is −0.100 versus +0.446; Belt lacks sufficient later same-position
  exposure. One first baseman's receiving skill cannot fill missing DP credit.
- Witt SS: +0.079 versus +0.140, with slightly negative 2023/2024 and positive
  2025. Perdomo's −0.414 versus +0.732 illustrates development or context change
  that a static history may miss. Luis García Jr. leaves the measured SS path;
  Soto's tiny later exposure includes missing DP measurements.
- Frick 3B: zero recorded double plays over 171 AA outs, while his much larger
  2B and SS stints have 20 and 12. Zero 3B successes without eligible chances
  does not establish poor skill. Same-age, similarly exposed AA third-base peers
  Yolbert Sánchez, Manny Rodríguez and Ripken Reyes have 2, 1 and 0 double plays;
  all four lack later measured MLB quality. The first selection wrapper chose
  Frick's principal 2B origin; a preserved supplemental review supplies the
  contract's explicit 3B case and its own peers. Coverage results never changed.

## Decision and next step

Test one transparent, regressed same-position MLB-history DP estimate against
neutral credit. Accept the runs-per-inning traffic limitation explicitly, test
all supported infield positions, and retain unknown prospect quality. Do not
fit a minor raw-count transfer or tune a difficulty model from nonexistent
chances. Do not transfer the range grade or other positions into DP skill.

The fixed history rule should first face later MLB quality and player review,
then a separate unchanged-opportunity delivered-value comparison if useful.
The historical cohorts are development evidence. Sparse fallback, older
compatible labels, minor defensive talent and full value integration remain
unfinished. Frozen forecasts, explorer and 2026 model selection are unchanged.
