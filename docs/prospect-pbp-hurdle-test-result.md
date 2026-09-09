# Prospect play-by-play hurdle test result

Status: **PROMISING FOR OPPORTUNITY; REJECTED FOR CONDITIONAL QUALITY; NO VALUE CHANGE**

This is the result of the frozen
[`prospect-pbp-hurdle-test-plan.md`](prospect-pbp-hurdle-test-plan.md). It is a
retrospective outer test, not a fresh confirmation.

## Source gate

Fresh 2021–2023 artifacts were regenerated because the original workflow artifacts
had expired. All 15 season/level jobs passed their existing source, identity, contact
and reconciliation controls.

| predictor season | summary rows | classified contacts | feature players | workflow run |
|---|---:|---:|---:|---:|
| 2021 | 180,523 | 421,766 | 4,214 | `34414373761` |
| 2022 | 197,913 | 479,253 | 3,829 | `34414375884` |
| 2023 | 194,636 | 475,974 | 3,767 | `34414377828` |

The files are retrospective event-cutoff corrected evidence, not claims about what a
historical analyst knew on that date.

## Meaningful next-season MLB opportunity

The 2022 selection fold chose the combined trajectory-plus-direction candidate with
50-contact regression and logistic `C = 1.0`. The untouched outer origin was the 2023
prospect cohort, scored on 2024 MLB results.

- Outer cohort: **3,168** players, including all non-arrivals; **17** reached 200 MLB PA.
- PBP observed: **3,155**; the 13 missing players remained in the test.
- Log loss: **0.022748 incumbent -> 0.022371 candidate**.
- Brier: **0.004890 -> 0.004865**.
- Player bootstrap log-loss difference: **-0.000377**, 95% interval
  **[-0.000653, -0.000121]**; candidate better in **99.7%** of resamples.
- Brier difference: **-0.0000247**, 95% interval
  **[-0.0000735, +0.0000176]**; candidate better in **84.7%** of resamples.
- Predicted opportunity remained high relative to observed:
  **0.80% predicted versus 0.54% observed**, improved from the incumbent's 0.81%.

Interpretation: contact trajectory and spray direction carry a small, repeatable
next-season opportunity signal beyond the frozen aggregate core comparator. The gain
is more convincing in log loss than Brier and only 17 positive outcomes exist in the
outer cohort. Keep it as a Phase 2 opportunity challenger. Do not change production
arrival probabilities until it beats the stronger pedigree-inclusive comparator and
passes a genuinely later confirmation.

## Component quality given meaningful opportunity

The selection fold chose trajectory only, with 50-contact regression and `C = 0.03`.

- Outer conditional cohort: **17** players; **4** had at-least-league-average neutral
  wOBA components.
- Log loss: **0.644671 -> 0.592965**.
- Brier: **0.226803 -> 0.200741**.
- Both bootstrap intervals crossed zero.
- Candidate calibration was unusable: intercept **8.44**, slope **21.16**.
- No subgroup had enough support for a hard stability conclusion.

Interpretation: reject this conditional-quality use. The apparent score gain is based
on far too few meaningful-role players and fails calibration. Contact direction does
not earn a WAR bonus, FV floor or catcher adjustment.

## Binding decision

- No current player value changes.
- No outside FV opinion was used.
- No catcher preference was added.
- No player was dropped for missing PBP.
- Pitch-sequence features remain excluded because coverage is not universal across
  levels.
- Next test: stack the frozen PBP opportunity challenger on the already stronger
  pedigree-inclusive aggregate model, with the result labeled descriptive because
  2024 has now been inspected. Freeze it for a genuinely later confirmation only if
  the incremental signal survives.

Machine-readable detail: [`prospect-pbp-hurdle-test-result.json`](prospect-pbp-hurdle-test-result.json).
