# Late-season role source review

All fifteen historical full-calendar-year MLB PA totals match prior official player-season counts exactly. Two nonoverlapping final thirty-day windows have valid counts inside annual totals. Sixty dated official requests, schedules deduplicated by gamePk and officialDate, no postponed entries treated as played. No 2026 outcomes.

Window gamesPlayed differs from annual team-summed source games for many people; the exact cause is not established. New game/PA-per-appearance predictors are withheld before fitting. The ten candidate inputs are availability, late/preceding PA and PA per scheduled league-average team game for current/prior years. They do not measure starts or diagnoses.

## Nick Kurtz at 2024 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| No own MLB record in these complete captures | 0 | 0 | 0 | Year-level denominators preserved | Year-level denominators preserved |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 0.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 0.0, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

Kurtz has no MLB PA in either source year; certified complete MLB windows therefore contribute zero PA and zero pace, not zero talent. His 35 A and 15 AA PA remain in the unchanged base features. This addition cannot directly tell whether an elite drafted hitter is ready to leap from AA to an MLB starting job. A refit may still change his forecast through global splits, so no exact unchanged-forecast promise is made.

## Anthony Volpe at 2022 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| No own MLB record in these complete captures | 0 | 0 | 0 | Year-level denominators preserved | Year-level denominators preserved |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 0.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 0.0, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

Volpe likewise has no MLB window record in 2021/2022. His actual 497 AA and 99 AAA PA remain base evidence, but the new MLB-only job signal cannot describe his late AAA promotion or a future spring starting-job competition. The certified zero is MLB opportunity, not absent minor history or poor talent. This is an explicit scope limitation, not a reason to drop him from scoring.

## Aaron Judge at 2016 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2016 | 95.0 | 63.0 | 32.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 32.0, 'late_usage_0_preceding_pa': 63.0, 'late_usage_0_late_pace': 1.1455847255369929, 'late_usage_0_preceding_pace': 2.3333333333333335, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

Judge's 95 debut-season MLB PA split into 63 in the preceding window and 32 in the last thirty days. Late MLB opportunity is actually declining, not an increasingly established September regular. The roughly 1.15 versus 2.33 PA per scheduled average team game inputs reflect that. His future breakout is not entitled to reverse this known history. No inference of a diagnosed injury or its recovery is inserted from these counts.

## Aaron Judge at 2024 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2023 | 458.0 | 113.0 | 111.0 | 26.46667 | 27.06667 |
| 2024 | 704.0 | 117.0 | 105.0 | 27.20000 | 25.66667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 105.0, 'late_usage_0_preceding_pa': 117.0, 'late_usage_0_late_pace': 4.090909090909091, 'late_usage_0_preceding_pace': 4.301470588235294, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 111.0, 'late_usage_1_preceding_pa': 113.0, 'late_usage_1_late_pace': 4.100985221674877, 'late_usage_1_preceding_pace': 4.269521410579346}.

Established Judge has 117 preceding and 105 late PA in 2024, following 113/111 in 2023. Late pace roughly 4.09 PA per average team game reflects a strong existing job, consistent with 704 annual PA. The smaller raw late total partly reflects the 25.67-game league window rather than 27.2 preceding games; both counts and transparent denominators remain visible. It does not force a 700-PA forecast or certify future health.

## Brent Rooker at 2022 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2021 | 213.0 | 74.0 | 59.0 | 26.53333 | 27.26667 |
| 2022 | 36.0 | 29.0 | 0.0 | 26.73333 | 27.60000 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 29.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 1.084788029925187, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 59.0, 'late_usage_1_preceding_pa': 74.0, 'late_usage_1_late_pace': 2.1638141809290956, 'late_usage_1_preceding_pace': 2.78894472361809}.

Rooker has 29 preceding and zero late MLB PA in 2022, versus 74/59 in 2021. This correctly separates his tiny declining MLB role from 365 AAA PA and 28 HR in the unchanged source. The late-role signal could plausibly lower opportunity, which would be wrong for his later breakthrough. Do not interpret zero late MLB PA as proof he lacked hitting talent or tune the window to recover this player.

## Albert Pujols at 2021 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2020 | 163.0 | 69.0 | 76.0 | 25.46667 | 28.86667 |
| 2021 | 296.0 | 28.0 | 28.0 | 26.53333 | 27.26667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 28.0, 'late_usage_0_preceding_pa': 28.0, 'late_usage_0_late_pace': 1.0268948655256724, 'late_usage_0_preceding_pace': 1.0552763819095476, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 76.0, 'late_usage_1_preceding_pa': 69.0, 'late_usage_1_late_pace': 2.6327944572748265, 'late_usage_1_preceding_pace': 2.7094240837696337}.

Pujols has 28 PA in each 2021 window, versus 69 preceding and 76 late in shortened 2020. Current late pace is about 1.03 PA per average team game and genuinely describes a smaller batting role. Full-year PA reconciliation is exact. Both months of 2020 remain observed and are schedule-denominated, not invented 162-game exposures. There is still no 2021-origin retirement, and these counts alone cannot foresee his much better final season.

## Dansby Swanson at 2016 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2016 | 145.0 | 51.0 | 94.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 94.0, 'late_usage_0_preceding_pa': 51.0, 'late_usage_0_late_pace': 3.3651551312649164, 'late_usage_0_preceding_pace': 1.8888888888888888, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

Swanson has 51 preceding and 94 late MLB PA, covering all 145 debut-season PA. Late pace rises to about 3.37 per scheduled average team game from 1.89. That is direct, legitimate origin evidence of increasing opportunity and the main hypothesized beneficiary. It is not a guarantee of next-season hitting quality; the batting estimate remains a separate fixed head in the eventual workload comparison.

## David Dahl at 2016 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2016 | 237.0 | 112.0 | 87.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 87.0, 'late_usage_0_preceding_pa': 112.0, 'late_usage_0_late_pace': 3.1145584725536994, 'late_usage_0_preceding_pace': 4.148148148148148, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

Dahl has 112 preceding and 87 late PA within 237 annual PA. Late pace falls about 4.15 to 3.11 per average team game, while still representing considerable opportunity. His later zero MLB season has not been used to set the window or label injury. This opposite-risk debut is important because a late-job addition could still overestimate future participation even with perfect source reconstruction.

## Fernando Tatis Jr. at 2022 cutoff

| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2021 | 546.0 | 74.0 | 106.0 | 26.53333 | 27.26667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 0.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 0.0, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 106.0, 'late_usage_1_preceding_pa': 74.0, 'late_usage_1_late_pace': 3.8875305623471883, 'late_usage_1_preceding_pace': 2.78894472361809}.

Tatis has no 2022 MLB PA but retains 74 preceding and 106 late PA from 2021, with 546 annual PA. The two-year input can distinguish prior substantial MLB opportunity from never-debuted zero history. It does not add a specific suspension, remaining ineligibility, medical recovery or expected return date. A finite-absence star-return problem may therefore remain even if the source is correct. Retain his difficult row in every comparison.

## Source decision

The ten PA-only timing inputs are usable for the one preregistered comparison. This is an execution/source conclusion, not a predictive gain. It does not establish minor-league jobs, finite-absence causes or future roster depth. The original 239 predictors and historical evaluation population are unchanged. Retrospective performance corrections and unverified roster-only universe entries remain qualified. Do not claim either the earlier rest-of-season result or these nine examples validates next-calendar-year performance.
