# What the strongest existing hitter model actually uses

2026-10-04. The saved model, not an old summary, is the benchmark for the next
repair. All 175 necessary saved heads reproduce the 30,506 original forecasts
across 35 chronological, whole-player cells. No new model was fitted. The audit
shows that the failed overseas integration changed much more than adding Japan
and Korea, and that the incumbent still has substantial opportunity gaps.

## The model branches and the changed comparison

For players who have never debuted, the incumbent uses the translated prospect
Ridge: 199 numeric-history inputs, nine dated scouting inputs and twelve
translation/profile inputs. For players with a prior debut and some measured
MLB contact in the three-year window, it uses the MLB tracking Ridge with 262
inputs. Previously debuted players without that tracking use the 199-input
numeric-history Ridge. Two separate gradient-tree heads estimate participation
and PA conditional on participating using 251 inputs. Their product gives
expected PA. Batting rate times PA plus replacement gives delivered batting
value, not full WAR or trade value.

The current benchmark does not include the later minor-tracking adjustment as
an approved improvement. It also does not incorporate every park, opponent or
contact experiment elsewhere in the project. The translated prospect profile
uses selected same-season movers and is not fully park/opponent neutral.

The 199-input manifest contains 98 pooled event-rate fields in total: seven MLB
and 91 non-MLB. The raw inventory's descriptive `raw_minor_rate_fields=105`
entry is incorrect and is qualified by this actual name count. Replay feature
lists came from the saved manifests, not that descriptive count, so all 175
head replays and coefficient accounting are unaffected.

The three rate branches use fixed units, not a learned StandardScaler. Their
training weight is equal-origin row balancing multiplied by uncapped actual
future PA, then normalized globally. This is not equal total PA weight per
origin. The failed integration instead capped PA at 300, gave each origin equal
total weight, added status and raw foreign columns, changed dated context and
replaced routed talent heads with one integrated standardized Ridge. Its loss
cannot be assigned to international statistics alone or entirely to scaling.

## Player evidence and exact coefficient accounting

Cases were selected before this replay from the completed failed experiment:
known design failures, ordinary controls and a non-arrival. The original
38-case review retains the outcome-selected gains, harms and comparison peers.
This audit is a mechanics review, not another model selection experiment.

| Player and origin | Known production | Incumbent forecast | What the replay establishes |
| --- | --- | --- | --- |
| Yordan Alvarez 2018 | 2016 DSL 57 PA, 12 UBB, 7 K; 2018 AA 190 PA, 12 HR and AAA 189 PA, 8 HR | 72.2 PA; +0.455 batting wins per 600 | The old DSL BB input is 0.3326 in fixed units and contributes +0.0011, rather than the failed integration's +6.01. Translation/scouting matter, but future 369 PA and +5.648 hitting remain badly underestimated. |
| Andrew Benintendi 2017 | 2015 short season 153 PA, 24 UBB; 2017 MLB 658 PA, 20 HR, 112 K | 635.5 PA; +1.085 hitting | Short-season walks contribute −0.0055, not the failed domestic head's −1.2605. Recent MLB quality and workload have larger effects. Actual is 661 PA and +2.218 hitting; this is reasonable regression but still low. |
| Shohei Ohtani 2018 | MLB debut 367 PA, 22 HR, 102 K, plus older NPB production | 391.0 PA; +1.576 hitting | The MLB tracking branch preserves current production: pooled MLB quality contributes +0.575 and current quality +0.352. Actual is 425 PA and +1.674 hitting. Older foreign input was absent, not negatively interpreted. The failed overseas rate of −6.533 was a new distortion. |
| Jung Hoo Lee 2024 | 158 MLB PA, 2 HR, 13 K, plus earlier KBO production | 153.6 PA; −0.646 hitting | MLB contact contributes positively (+0.228 from pooled K), but old KBO is absent. Actual is 617 PA and +0.463 hitting. The incumbent misses workload and may discard useful foreign evidence; the failed +9.444 hitting forecast is not the remedy. |
| Masataka Yoshida 2024 | 580 and 421 newer MLB PA, 15 and 10 HR, 81 and 52 K | 476.2 PA; +0.327 hitting | Current MLB quality/workload dominate the sum; old NPB does not have a free rare-feature coefficient. Actual is 205 PA and −0.444 hitting. The current forecast still overpredicts both parts; the failed +5.140 hitting exaggerates the error. |
| Aaron Judge 2024 | 696, 458 and 704 MLB PA with 62, 37 and 58 HR | 530.8 PA; +4.935 hitting | Pooled quality contributes +2.408, current quality +1.211, EV95 +0.305 and mean EV +0.216. Strong talent is recognized, but actual 679 PA and +6.287 hitting remain higher. No scaling repair can be assumed to solve star regression. |
| Aaron Judge 2016 | AAA 410 PA, 19 HR, 98 K; MLB 95 PA, 4 HR, 42 K | 309.9 PA; +0.264 hitting | The tracked branch is used after a brief debut. Mean EV and EV95 contribute about +0.10 each, but are insufficient to recognize the breakout: actual 678 PA and +5.330 hitting. This is an unresolved brief-debut/branch limitation, not evidence that the first MLB sample should erase AAA. |
| Nick Kurtz 2024 | A 35 PA, 4 HR and AA 15 PA; dated draft/scouting evidence | 10.2 PA; +1.024 hitting | The current prospect profile already contributes +0.807 through translated other and +0.185 through HR; draft/rank contribute positively. Actual 489 PA and +5.150 hitting demonstrate that readiness, not simply missing production columns, is a large gap. |
| Fernando Tatis Jr. 2022 | 2020 MLB 257 PA, 17 HR; 2021 MLB 546 PA, 42 HR; known finite suspension | 39.7 PA; +1.313 hitting | Talent is preserved through old MLB quality, but participation is only 0.134 and conditional workload 296.2. Actual 635 PA and +0.727 hitting. Temporary absence is still confused with exit. Do not backdate an observed return or guess remaining suspension games. |
| Rhys Hoskins 2023 | Prior MLB 443 and 672 PA, 27 and 30 HR; missed 2023, cutoff-known new signing | 26.3 PA; +0.037 hitting | Participation 0.101, conditional PA 260.9. Old MLB quality survives, but the job evidence is not in this incumbent. The failed integration improves PA to 225, versus actual 517 and +0.133 hitting. Retain that useful source correction while repairing talent. |
| Brandon Belt 2023 | Latest MLB 404 PA, 19 HR, 141 K; unsigned, not known retired | 244.2 PA; +0.547 hitting | Age subtracts 0.854, but quality remains positive. Actual zero PA does not reveal a batting rate. His surprising non-signing is a retained uncertainty case, not justification for inventing retirement. |
| Hernán Pérez 2017 | Latest MLB 458 PA, 14 HR, 79 K | 353.5 PA; −0.676 hitting | Pooled quality contributes −0.337. Actual 334 PA and −1.034 hitting. Ordinary workload is close, rate modestly optimistic; there is no rare-feature dominance. |
| Wilmer Flores 2016 | MLB 335 PA, 16 HR, 48 K plus earlier 510/274 PA | 391.4 PA; +0.296 hitting | Workload, age and modest quality effects yield a plausible ordinary forecast. Actual 362 PA and +0.656 hitting; the incumbent is not universally more accurate than the failed head on every player. |

Suzuki before 2022, Ohtani before 2018, Yoshida before 2023, Lee before 2024 and
Bogusevic before 2017 have no incumbent rows. All five remain explicit absences,
not zero forecasts. Their actual foreign/domestic histories and non-arrivals
are retained in the completed addition review. A replacement can reconstruct
features from those histories, but cannot manufacture an old benchmark result.

The raw inventory initially copied the legacy anchor's `next_batting_rate` and
`next_value` fields into its case `actual` entry. Those are not the compatible
future-environment-relative labels used in the completed overseas comparison.
No scores or forecasts were computed from those copied entries. This review
and the appended aligned case receipt use `actual_relative_rate` and
`actual_relative_value`; the original inventory is preserved and qualified.
The discrepancy is a reminder to label targets explicitly, not a new forecast
failure or a reason to overwrite historical evidence.

## Precision is not the same as a recency score

The existing foreign component profile has a 5/4/3 recency-weighted exposure.
That is a pooling convention, not a count of independent plate appearances.
For Ohtani 2018, 613 recent NPB PA become 2,070 weighted units; Lee 2024 has
1,014 PA and 3,429 units; Yoshida 2024 has 508 PA and 1,524 units. Thames 2021
has only two NPB PA, represented as ten units. Passing those numbers directly
as binomial precision would invent information. The repair must decode actual
count/lag evidence and explicitly declare any recency normalization.

## Consequence for the repair

Preserve the unchanged routed incumbent as a mandatory benchmark. Build the
replacement from actual inputs rather than its fitted predictions: using those
predictions in training would be supervised stacking and need nested out-of-
sample construction. Keep MLB tracking and scouting families. Replace redundant
raw lower-level talent columns with a coherent translated minor event profile,
with sample influence constrained relative to recent MLB evidence. Add only
the existing translated foreign event profile, not dozens of unrestricted raw
and translated versions. Source precision and sparse translation support remain
separate. Professional activity and finite absence also require explicit job
representation; foreign talent alone will not supply an MLB role.

The readable player inventory is complete. This establishes reproducibility
and the representation choices, not predictive improvement. New fits require
the next exact contract and source/support checks. Protected 2026, the current
explorers and the broad goal's unfinished practical deliverables are unchanged.
