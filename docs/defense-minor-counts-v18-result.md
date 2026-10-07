# Minor fielding counts and later MLB talent

The saved minor-league data contain real fielding counts, not just innings and
positions. They can support a small, carefully qualified range-talent test.
They do not currently support a convincing lower-minors catcher-talent test.
No prediction changed in this audit and no accuracy improvement is claimed.

## What is now available

The extraction recovers 324,454 minor fielding records from 291 existing
captures, covering 2009–2019 and 2021–2024. Putouts, assists, errors, throwing
errors, double plays and the applicable catcher counts are recorded throughout.
Every recorded chances total equals putouts plus assists plus errors; throwing
errors never exceed total errors. All accepted identities, innings and games
match the earlier usage ledger. Missing 2020 minor baseball stays absent.

The early rookie records combine rookie leagues. Their attached club/league
does not establish that all counts belong to DSL or a particular complex team.
Modern DSL and complex records are separate. Short-season and advanced-rookie
levels remain visible rather than being relabeled as modern Single-A.

The independent replay covers all raw records, 127,811 eligible origin-position
rows, 280,088 future component/window labels, 224,670 support rows and 360
chronological held-player cells. Fifteen focused unit tests pass. These checks
establish trustworthy calculations, not predictive success.

## The prospect sample is much smaller than the pooled sample

A player with MLB defensive experience who appears in Triple-A is not an
ordinary prospect example. Separating those players materially changes the
amount of evidence available. For the 2022 origin and the fixed 2023–2025
quality window, there are 63 distinct measurable range players without prior
MLB fielding, versus 188 in the mixed population. A player can supply multiple
positions; the position counts must not be added as independent people.

| Component | Earlier training people without MLB fielding, across held-player folds | Measured 2022-origin prospects by principal minor level |
| --- | --- | --- |
| Range | 137–153 | AA 33, AAA 9, High-A 12, Single-A 7, complex 2 |
| Catcher blocking | 8–14 | AA 3, AAA 1, High-A 2, Single-A 1 |
| Catcher throwing | 1–4 | AA 1, AAA 1, High-A 1 |

The level counts may overlap in range because a player's different positions
can have different principal levels. Every prospect joint profile remains below
the 20-person warning threshold. Modern complex/DSL profiles have no same-level
training examples in these folds. Combining them with the older undifferentiated
rookie source does not create certified DSL support.

Five years allows more players time to reach MLB, but gives fewer chronologically
finished examples to train on. At the 2019 origin, the five-year range comparison
has 63–80 earlier prospect training people per fold; catcher throwing has 2–5,
and blocking only 1–2. Pre-2016 MLB defensive exposure lacks the native range
measurement. That excludes many older established players from these labels;
the remaining older labels favor later arrivals. A long input history alone
does not solve that selection problem.

## What the player review shows

The [saved walkthrough](../reports/model-evidence/defense-minor-counts-v18/player-walkthrough.md)
contains twelve focal players and 36 peers chosen by origin level, position,
age and exposure without consulting future results. The machine-readable
traces retain each source scope and annual native/official position path.

Witt had five errors in 122 rookie chances in 2019. His MLB shortstop range
runs were −6.88 in 2022, +9.76 in 2023 and +11.36 in 2024. The three-year window
contains only one measured MLB season and is therefore not a developed-quality
label. The five-year pooled rate is +2.03 native runs per 500 innings, with only
three matching earlier prospect training people in his fold. This is an
example of development and sparse evidence, not permission to tune to Witt.

Volpe had nine errors in 137 advanced-rookie chances; Abrams had twelve in 141
mostly rookie chances. Their later five-year shortstop rates are +2.07 and
−4.30 runs per 500 innings respectively. Their age, small samples and very thin
training support prevent those two outcomes from validating a simple error
cutoff. All three origin-selected peers for Abrams lack a measured MLB fielding
outcome in the window. They are not assumed to be bad defenders.

Peña's 2019 evidence spans Single-A and High-A and retains all 2,269 shortstop
outs. His five-year pooled rate is +0.53 runs per 500 innings. Neither his
promotion nor only one level's counts should replace the complete origin
record. His nearest-age peers also show why later MLB availability must not
be inferred from favorable fielding counts alone.

Rafaela's largest 2019 exposure was at second base. Through the five-year
window he had only 169 MLB second-base outs but 4,350 outs at other positions.
His center-field performance is not evidence of second-base quality. Edwards
likewise moved toward shortstop; his 27 second-base outs with missing range
measurement remain unknown. Bae, selected as a peer from origin information,
barely qualifies at second base with 1,504 native outs across three seasons.
These cases require position-specific labels and a separate position-transfer
model, not indiscriminate pooling of all future defense.

Bailey's 2022 High-A catcher record contains 29 caught stealings in 97 attempts,
12 passed balls, 31 wild pitches and three credited pickoffs. His later throwing
rate is +8.70 native runs per 100 tracked attempts; blocking is −0.12 per 1,000
chances. Those components are different skills. His throwing comparison has
only one exact matching prospect training person, and blocking has none. A
catcher's raw caught-stealing rate includes the pitcher and runner matchup;
the count is not already an adjusted catcher arm grade.

Raleigh's 2019 caught-stealing rate was 34/115; Kirk's was 30/80. Their five-year
native throwing rates are +1.40 and +2.30 per 100 attempts. Their origin-selected
peers include Campusano, Amaya and Melendez. Some have too few later tracked
attempts to supply throwing quality, although their blocking quality is
measurable. Melendez's subsequent outfield move is retained. Opportunity and
position selection cannot be compressed into a single catcher defense number.

Eldridge's first available 2023 record is primarily right field, not his later
first-base role. Both future windows remain incomplete as of the permitted
2025 outcome boundary. Sutton's nine shortstop chances are not a stable talent
measurement. Rojas's 2009 five-year window includes real MLB shortstop exposure
before native tracking; it is unmeasured, not average or poor defense. These
cases prevent sample size, role changes and source coverage from becoming
invented certainty.

The unused fixed-ID tuple in the original audit runner contained five incorrect
IDs. It did not select the extracted population, labels or support. The review
resolves the contract's fixed names against the source, records the corrected
IDs, and preserves the original sealed runner. Do not reuse that tuple.

## What the older screen actually established

The August screen reported forward correlations for fielding percentage
(0.129), range factor (0.228), errors (−0.0841), throwing errors (−0.0991), catcher
caught-stealing percentage (0.203) and passed balls (−0.152). Double plays did
not pass its threshold. These are pooled Spearman correlations after the
screen's position treatment, not prediction-error improvements.

Its inputs aggregate affiliated levels, including MLB, and its outcomes select
next-year MLB players at the same primary position. It therefore did not test
pure minor-to-MLB transfer or separate all prior-MLB returners from prospects.
Within-fold feature/target standardization is not a frozen deployable forecasting
procedure. Retain the screen as a reason to investigate these features, neither
as proof of prospect defense nor as evidence that traditional range/error
features broadly failed. The original contracts and results remain unchanged.

## What the literature adds

Stoltz's 2014 shortstop study found that teenage error rates improve with age
and that age-18 fielding percentage weakly distinguishes later outcomes. His
older-player observations were selected survivors, and the same-season MLB
fielding-percentage/UZR relationship was not a validated minor-to-MLB forecast.
The useful implication here is to compare age and exposure before treating
errors as talent, not to import his thresholds as run values.
[Original study](https://blogs.fangraphs.com/kenny-peoples-walls-and-how-shortstop-fielding-develops/).

Smith's TotalZone work estimates plays relative to opportunities and accounts
for batter/pitcher handedness, pitcher context, positioning and parks. Double
play turning is separate from range. Some plausible adjustments did not improve
agreement with advanced measures; he also rejected an adjustment that failed
player reasonability checks. For this dataset, putouts plus assists per inning
are candidate evidence, not an already context-neutral fielding grade.
[Original method](https://tht.fangraphs.com/measuring-defense-for-players-back-to-1956-part-2/).

## Decision and next comparison

Use range, which has materially more genuine prospect training support, for
one transparent count-feature comparison. Keep age/position/exposure baselines,
training-only level expectations, substantial regression of small samples and
explicit unsupported-level fallbacks. The primary development origin is 2022;
2021 is a separately reported COVID/reorganization stress cohort. Use the fixed
three-year same-position MLB quality window, not next-year delivered runs.
This answers a near-MLB prospect question, not all eventual DSL talent.

The 2019 five-year traces remain an important longer-path diagnostic, but their
different historical-label selection prevents an unqualified long-horizon
claim. Catcher prospect throwing/blocking need more comparable historical MLB
quality measurements before fitting a complex transfer model. Do not lower
measurement requirements after seeing Bailey or turn unknown peers into zeros.

If range evidence survives, test its effect on value separately with arrival
and position exposure fixed; do not claim whole-player value from conditional
quality alone. The practical MLB quality baselines remain in place. Lower-minor
talent, position transfers, catcher history support and longer-horizon integration
remain unfinished. Frozen forecasts, the explorer and 2026 selection are
unchanged; the full defense goal stays active.
