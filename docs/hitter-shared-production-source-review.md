# Shared hitting profile source review

2026-10-05. Seven fixed player histories have been traced before fitting. The
source design can proceed to its single historical comparison; this is not
approval of its predictive accuracy or adoption.

## What the inputs mean

Each profile combines actual recent opportunities, translated to common MLB
event coordinates, and 1200 reference PA. The reported reliability is the
fraction of that constructed profile coming from supported observations. It
is not an estimated probability that a translation is correct. The prior's
strength remains a design assumption, including for high-quality prospects.

| Player and origin | Supported weighted PA | Observation share | Source findings |
| --- | ---: | ---: | --- |
| Yordan Alvarez 2018 | 726.0 | 37.69% | Old DSL 57 PA contributes 34.2 weighted PA; 2018 AA and AAA contribute 379. The old DSL sample does not outweigh his newer upper-minors record. |
| Aaron Judge 2016 | 1274.8 | 51.51% | MLB contributes 95; multiple prior minor seasons contribute 1179.8. A brief debut does not erase the substantial minor record. |
| Nick Kurtz 2024 | 50.0 | 4.00% | A 35 PA and AA 15 PA are small production evidence. Draft and scouting remain separate inputs. This test does not promise that 50 PA establish elite MLB talent. |
| Seiya Suzuki 2021 | 1311.4 | 52.22% | All observed mass is NPB, translated with 13 mover people. He has no MLB history, not zero hitting ability. His archived information date is the post-lockout preseason, not a fictional January cutoff. |
| Jung Hoo Lee 2024 | 843.8 | 41.29% | MLB contributes 158 and older KBO 685.8. KBO contributes 33.56% of the complete prior-plus-data profile, with only eight mover people supporting translation. |
| Masataka Yoshida 2024 | 1197.8 | 49.95% | Newer MLB contributes 885 weighted PA, prior NPB 304.8, and AAA eight. NPB contributes 12.71% of the profile, rather than overwhelming two MLB seasons. |
| Kevin Maitan 2017 | 176.0 | 12.79% | Only rookie production is present. This remains a weakly supported next-year MLB talent extrapolation; no arrival is not an observed talent of zero. |

All eight event probabilities are positive and sum to one. Their contrasts
sum to zero. Independent arithmetic reconstructs the smoothing, translation,
foreign reference alignment, weighted mass and single reference prior for these
cases. Both source-player and outer-test player groups are excluded from
domestic graphs/references; existing foreign profiles exclude both too.

## Limits carried into the fit

These translations use selected same-season movers and existing international
bridges. They are not complete park- and opponent-neutral estimates. Equal
weighted PA are not proven equal information across leagues; exposure cannot
create mover support. Source revisions and the existing preseason population
coverage qualifications remain. No source outcome from 2026 is used.

The existing playing-time forecast is fixed. Consequently this experiment
cannot resolve Kurtz's arrival allocation or discover a new MLB job for an
unsigned player. Original benchmark forecasts remain unchanged, and additions
have no manufactured incumbent comparison. All full/active support counts and
feature-range warnings are persisted before the 105 talent fits.

Focused tests pass for reference identity, tiny-sample bounds, dilution by MLB
evidence, coherent source removal, invalid counts and future/held-fold rejection.
Both frozen packages verify. These checks establish a runnable design, not
that the shared representation will beat the existing model.
