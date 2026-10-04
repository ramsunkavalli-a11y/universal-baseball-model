# Why young prospect hitting needs longer follow up

2026-10-04. The completed source audit changes the next experiment: three years
is still too short to learn much about teenage DSL hitters. Six years provides
real future MLB examples, but the model must retain the time to arrival rather
than apply those players' later performance to next year. No forecasts changed
and no new model was fitted.

## What the data establishes

The audit retains all 63,282 source origins and 30,506 evaluated forecasts.
It constructs 379,692 annual follow-up observations; 63,093 after 2025 remain
censored and null. All existing next-year PA and active batting-rate labels
reproduce exactly. All 14,857 MLB inventory person-seasons reconcile to dated
counts. The raw source also has 3,578 zero-PA person-seasons absent from the
positive-PA inventory; these were checked as zero rather than discarded as
unexplained join failures. Three focused tests cover cancellation, censoring,
label maturity, held players and future-outcome mutation.

For a common historical group of 1,603 distinct people represented by 1,673
age-at-most-17 DSL origins from 2011–18, nobody has MLB PA in Year 1 or Year 2.
Only one distinct person plays in Year 3. In Years 4, 5 and 6, respectively,
14, 38 and 49 distinct people play. Excluding short-season 2020 MLB outcomes
from training evidence leaves 11, 33 and 44. These are participants in each
annual window, not necessarily first debuts or counts to add across years.
No one is selected into this group using a future MLB outcome.

The actual training folds confirm the practical difference:

| Evaluation scope | Forecast rows | Median active people using Year 1 only | Using completed annual Years 1–3 | Using completed annual Years 1–6 |
| --- | ---: | ---: | ---: | ---: |
| DSL at age at most 17 | 2,293 | 0 | 1 | 33 |
| Predominantly lower exposure below 21 | 10,344 | 0 | 3 | 29 |
| Entire population | 30,506 | 8 | 51 | 72 |

Counts match origin age band, dominant level and prior-debut state, excluding
the whole held-player fold and all labels after each cutoff. They are distinct
people, not repeated player seasons. For the DSL group the refined
rank/new-draft/exposure intersection still has a median of only three active
people with six years. Distant-arrival support does not create Year-1 support.
The exact annual-horizon counts are saved separately to prevent that inference.

Requiring every training origin to have a completely mature six-year window
discards useful completed annual observations and leaves no window at the
2016 cutoff: the source starts in 2011. Pooled annual observations avoid that
loss while preserving horizon identity. They do not permit using future labels
or calling a short follow-up window a complete career.

## Eleven player walkthroughs

These are source and target-design checks, not predictions from a new model.
The saved cases contain actual three-year dated counts, origin inputs, all six
annual outcomes, existing next-year outputs where available and peers chosen
without future outcomes. For origins outside the existing evaluation years,
no saved forecast or actual evaluation fold is invented.

**Renato Nunez and Jeimer Candelario in 2011.** Both are seventeen-year-old
DSL third basemen. Nunez has 207 PA, five HR, six total walks and 42 K;
Candelario has 305 PA, five HR, fifty walks and 42 K. Neither plays MLB in
Years 1–4. Nunez receives 15 and 16 PA in Years 5–6; Candelario 14 and 142.
Candelario's Year-6 observed rate is +1.213 custom batting wins/600, compared
with -7.535 in fourteen Year-5 PA. These are noisy selected MLB samples, not
a measured development curve. Same-position peers mostly remain at zero
within six years; Jose Rondon receives 26 Year-5 PA among Nunez's peers.
The success cases cannot justify predicting that every similar teenager will
arrive. Nor would a next-year-only test identify either player's later hitting.

**Edmundo Sosa and Magneuris Sierra in 2013.** Seventeen-year-old DSL Sosa
has 198 PA, three HR, 22 walks and fifteen K; Sierra has 252 PA, one HR,
29 walks and 33 K. Sosa receives only three and ten MLB PA in Years 5–6.
Sierra receives 64, 156 and 42 in Years 4–6. Sierra's observed rates vary
from -.717 to -6.193 to +1.454. Arrival and useful production are distinct.
The matched origin peers include Dennis Santana, who later supplies two PA
in each of Years 5–6: this is MLB batting activity, not certification that
he stayed a hitter. Jose Siri has zero PA within Sierra's six-year window,
but the certified inventory records his first MLB batting in 2021, Year 8;
that must not be reported as a failed MLB career. Role changes and later
arrivals remain limits of a calendar-window batting target.

**Rafael Devers in 2014 and Ronald Acuna Jr. in 2015.** At seventeen,
Devers has 302 recorded rookie PA, seven HR, 35 walks and fifty K; Acuna
237 rookie PA, four HR, 28 walks and 42 K. Neither plays MLB in the first
two years. Devers receives 240/490/702 PA in Years 3–5, and 248 in shortened
2020 Year 6. Acuna receives 487/715/202/360 in Years 3–6, with Year 5
shortened. Devers's first-season rate is +1.143 and his second -.298;
Acuna's first +3.681. There is no uniform straight-line annual improvement.
Most peers do not arrive within the window; Luis Alexander Basabe receives
18 Year-6 PA among Devers's peers. Acuna's exact group has only two peers,
Yepez and Carpio; neither has PA within six years. Limited peer count is
reported rather than silently widening the group or picking successful peers.

**Kevin Maitan in 2017.** Seventeen, 176 rookie PA, two HR, eleven total
walks and 49 K. Earlier reports use ten unintentional walks; the definitions
are consistent, not a newly missing walk. All six future MLB PA observations
are zero, so all batting-rate labels are unobserved. The current 1.52% arrival
chance and 1.99 expected next-year PA remain unchanged. His fold has zero
Year-1 coarse active analogues, two using completed annual Years 1–3, and
four using Years 1–6; the refined six-year intersection has zero. Mark
Vientos, the sole exact-group peer, receives 41 and 233 PA in Years 5–6.
This supplies delayed-arrival evidence and a contrasting outcome without
requiring immediate debut for either teenager.

**Pete Alonso in 2018.** Age 23, 574 AA/AAA PA, 36 HR, 76 total walks
(73 unintentional) and 128 K. Current expected next-year PA is 215 versus
693 actual, and hitting rate +.286 versus observed +3.283. His actual-fold
coarse active support is already 48 people at Year 1 and rises only to 53
across six annual years. The refined six-year intersection has four. This is
not mainly a missing distant-DSL-label problem. Matched peers Thaiss, Mercado,
Neuse and Mateo have diverse annual paths, including zero-PA years. The
underestimated immediate workload and power must remain visible after any
longer-horizon talent experiment.

**Aaron Judge in 2024.** Age 32, 696/458/704 PA and 62/37/58 HR in the
three history years. Current 531 expected PA and +4.534 batting wins/600
compare with 679 and +6.287 in 2025. His coarse profile already has 584
active Year-1 people; six-year pooling raises that only to 592. It cannot be
advertised as solving elite-star support. Castellanos, Suarez, Diaz and Soler
are exposure/age controls, not equivalent talent. All their 2026–30 outcomes,
like Judge's, remain null and unread.

**Nick Kurtz in 2024.** Age 21, 35 A PA with four HR, ten walks and seven K,
plus fifteen AA PA with two walks and three K. The current forecast is ten
PA and -.063 batting wins/600 versus 489 and +5.150 actual in 2025. His
coarse active group rises from fifteen immediate examples to 312 across
six annual years, but the elite-ranked new-draftee/thin-history intersection
still has zero. Balogh, Jenkins, Marget and Bender have similar tiny
professional exposures but not equal pedigree; their zero 2025 PA does not
explain away Kurtz's miss. Future labels after 2025 remain null. More pooled
examples cannot substitute for missing relevant entry profiles.

**Juneiker Caceres in 2024.** Sixteen, 167 DSL PA, eighteen K, nineteen
total walks (seventeen unintentional), no HR. Current .067 expected PA and
+.499 batting wins/600 remain unchanged; actual 2025 PA is zero with no
measured batting rate. His fold has zero immediate active analogues, two
using annual Years 1–3 and 53 using Years 1–6, including forty exact Year-6
people. They support learning about later selected arrivals, not validating
his current +.499 estimate. His four origin peers also have zero next-year
PA, and their later outcomes remain censored. A less optimistic rate would
not by itself establish a better projection.

## Consequence for the next comparison

Keep the current model and the reviewed translated/ranking alternative as
anchors. The next bounded test should distinguish level-specific age effects
from learning across future horizons: first a next-year representation control,
then an annual horizon-aware shared model using only mature Years 1–6 labels.
Keep horizon terms and exact-horizon support explicit. This is a testable
sharing assumption, not evidence that six-year hitters were MLB-ready earlier.

Score next-year MLB hitting and delivered value on the original identities,
with current opportunity fixed; preserve non-arrivals in value scoring and
established-player forecasts in the primary prospect assembly. Inspect actual
players, group totals and harms before disposition. Conditional batting of
never-arrivals remains unidentified; longer follow-up does not magically solve
that selection problem. This audit does not complete the full practical goal,
change the frozen forecast or authorize deployment.

Evidence: [source and actual-fold report](../reports/model-evidence/hitter-followup-support/report.json),
[stats and annual player paths](../reports/model-evidence/hitter-followup-support/cases.json),
[review receipt](../reports/model-evidence/hitter-followup-support/final-report.json).
