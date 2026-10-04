# Batting value totals and actual model misses

2026-10-04. Most of the dramatic annual swings in the current hitter report
come from comparing next-year batting with the previous year's league average.
They are not evidence that the same players suddenly generated vastly different
shares of a fixed WAR budget. The reviewed forecast still improves after using
the actual season's league reference, but meaningful hitting and playing-time
misses remain. No prediction, model, frozen forecast or explorer was changed.

This extends the [earlier environment supplement](hitter-value-integration-v76-environment-supplement.md)
to the current prospect-plus-MLB-Statcast assembly. It does not discover that
issue for the first time, rerun earlier fits or replace their original scores.
The [audit contract](hitter-season-value-ledger-contract.md) was saved before
scoring. All 30,506 forecasts, exits/non-arrivals and public-match identities stay.

## Use the season reference for the player value question

FanGraphs' [wRAA definition](https://library.fangraphs.com/offense/wraa/) measures
batting above league average, and its [position-player WAR calculation](https://library.fangraphs.com/war/war-position-players/)
also adjusts for parks and leagues and converts runs to wins. Our measure remains
a simpler fixed-event batting-plus-replacement quantity: recentering it does not
make it full WAR, adjust parks or certify park-neutral hitting ability.

The old observed response uses the origin league reference. Its difference from
season-relative contribution is exactly actual PA times the change in the MLB
event index divided by 11.93. Target-season conditions belong in an observed
historical label; they were never given to the earlier forecast. The saved
hitting heads already learned future-season-relative rates. Their forecast
means and known origin replacement reference are unchanged.

For future WAR-like research interpretation, use the season-relative measure and
report the old fixed-reference production question separately. This is an
estimand decision, not permission to rescore arbitrary failed tests until one
wins. Every new comparison must specify the target before fitting, hold controls
and membership fixed, and preserve earlier records. The current explorer still
shows the original common-reference contribution with its existing warning;
this audit supplies a separate corrected interpretation, not a silent UI change.

## The annual ledger

Values below are custom batting-plus-replacement wins for the same known origin
cohorts, not complete teams or published WAR.

| Season predicted | Forecast | Actual against prior league | Actual against same season | League-reference difference |
| --- | ---: | ---: | ---: | ---: |
| 2017 | 597.16 | 706.55 | 638.31 | +68.25 |
| 2018 | 607.92 | 505.46 | 631.27 | -125.81 |
| 2019 | 599.53 | 815.42 | 639.61 | +175.81 |
| 2022 | 607.35 | 463.91 | 568.34 | -104.44 |
| 2023 | 575.96 | 737.65 | 571.77 | +165.88 |
| 2024 | 607.81 | 421.34 | 564.70 | -143.36 |
| 2025 | 559.69 | 613.85 | 571.43 | +42.42 |

For 2019, the apparent 215.89 shortfall shrinks to 40.08 under the intended
season-relative interpretation. For 2024, the apparent 186.48 overforecast
shrinks to 43.11. Those remaining errors are real. A league reference cannot
explain the wrong allocation among players, an unexpected absence or a breakout.

The complete MLB source is not the forecast cohort. In 2017-2019 the omitted
source contains 5,270/5,129/5,129 pitcher PA, with roughly -65 to -66 custom
contribution. The pitcher examples include deGrom, Greinke, Scherzer and Bumgarner.
Consequently the known hitter cohort can deliver around 631-640 while the full
MLB source delivers about 570. Do not force a non-pitcher cohort to the latter
number. This source distinction was also noted in earlier allocation work; the
new receipt quantifies it for this exact panel and response.

Omitted hitting is real too: Ohtani contributes 367 PA in 2018, Suzuki 446 in
2022, Yoshida/Conforto/Schanuel 580/470/132 in 2023, and Jung Hoo Lee 158 in
2024. These are not all new prospects. The cohort is therefore not universally
complete, even though its latest year's missing PA is just 46. The source roster
has no 2022 Conforto row, and the model feature panel has no 2022 Conforto row
despite retaining 2021 and 2023. That establishes a coverage hole, not its precise
transaction/source cause. Do not invent a zero forecast, assume an absent roster
record means no job, or retrospectively add an origin-known player without
verifying the dated evidence.

## Improvement remains modest and qualified

On the season-relative response, previous-current contribution RMSE is 0.43795
and the main reviewed assembly is 0.43513, about 0.64% smaller. Its nominal
player-cluster paired MSE interval is -0.00410 to -0.00108. Every evaluated
origin improves. These are exposed development years; the interval does not
account for repeated model selection or common season shocks.

Never-debut contribution RMSE improves 0.14889 to 0.14823, but its paired interval
still includes harm. Minor measurements versus the precision exposure control
also remain uncertain: MSE difference -0.000127, interval -0.000539 to +0.000296
among eligible players. Do not promote that overlay. Correcting the response
does not turn its thin support or harmful individual mechanisms into validation.

The 2,627 public matches retain the same PA forecasts and archive qualification.
Converted season-relative contribution RMSE is 1.02398 for the main assembly,
versus 1.03365 previous-current and 1.09011 for unchanged Steamer conversion.
The latter assumes the projected league reference equals the origin reference;
this sensitivity is not certified neutral public forecasts or native WAR
superiority. PA absolute error remains 15.56% worse than Steamer and fails the
declared 15% practical allowance. Nothing in this audit repairs that.

## Totals can hide mistakes

The exact main residual is split into:

- Opportunity: actual minus predicted PA, valued at forecast hitting and replacement.
- Hitting: observed minus forecast hitting, applied to actual PA.
- League conditions: the extra term included only in the old origin-reference label.

This is accounting, not causal attribution or a new joint model. Across all
years, actual season-relative value exceeds forecast by 30.00. The opportunity
term is +188.73 while hitting is -158.73. A small net shortfall conceals large
opposing component errors. Among never-debut players, the corresponding terms
are +48.32 and -35.55. Among lower-minor never-debut players both are negative;
a universal playing-time or talent boost would be inappropriate.

Thirteen player-origin walks trace raw statistics, every fitted hitting input
and term, actual PA inputs/intermediates, event counts, league references and
four origin-selected peers. The [complete walkthrough](../reports/model-evidence/hitter-season-value-ledger/player-walkthrough.md)
includes the following substantive checks:

- Judge, 2019: forecast 4.53 versus 3.69 season-relative value; the older 4.13
  actual obscures part of the overforecast. Judge, 2025: the 3.21 value shortfall
  remains 1.68 opportunity and 1.53 hitting, with only .16 league-reference effect.
- Kurtz, 2025: 10 versus 489 PA and 1.02 versus 5.15 hitting per 600. Opportunity
  explains 2.31 of the shortfall and hitting another 3.36; league effects only .11.
- Kwan, 2022: 116 versus 638 PA and -.25 versus +1.62 hitting. Removing the
  league reference makes the season-relative miss larger, not smaller.
- Bichette, 2025: the genuine rebound miss is about .50 opportunity and 2.56
  hitting. Fixing tiny minor-contact influence did not repair this MLB estimate.
- Caminero, 2025: the main branch helps but retains .96 opportunity and 1.73
  hitting shortfall. His advancing-player peers often receive much more MLB use.
- Belt, 2024: zero actual PA leaves no observed hitting rate. His .98 miss is
  entirely opportunity under either label; the unexpected employment outcome is
  not justification to erase similar productive older hitters.
- Acuña, 2024: the largest main harm has -3.47 opportunity and -1.15 hitting
  residual. Later absence remains risk, not permissible forecasting information.
- Brian Anderson, 2023: forecast .6058 and actual .6045 look nearly exact, but
  +.368 opportunity error cancels -.369 hitting error. This is not correct
  decomposition. Thames and the young Caceres case preserve missing-history and
  unobserved-long-term-talent limitations rather than fabricating good forecasts.

Broad peer selection is itself qualified: some Bichette peers lack his established
MLB record, and Kwan peers are not equivalent low-strikeout AAA hitters. The saved
rule is outcome-blind but does not establish equivalent talent, pedigree or health.
Do not use those peer failures to excuse every model miss.

## Verification and next work

Every observed vector and both league references match independently grouped
dated MLB stints. All 30,506 predictions remain bit-identical. All per-row
accounting identities pass, 154 endpoint components are independently checked,
thirteen actual player walks are complete and sixteen focused tests pass. All
31 protected files remain unchanged; no protected 2026 results were opened.
Execution and review completion are not model approval.

Evidence is in `reports/model-evidence/hitter-season-value-ledger`, including the
compact per-row ledger, scores, intervals, omitted-player source review, exact
case inputs and hashes. The audit and independent reviewer preserve completed
outputs; neither fits or selects a replacement model.

The next coherent repair is opportunity/source integration, not another generic
learner or era feature sweep. First reconcile cutoff-known returners and temporary
absence against the actual eligibility and roster inputs, with current rows
retained and additions separately identified. Use the existing availability
tests before borrowing a rule. Keep elite thin entrants and their support gap
in scope. This audit narrows the aggregate-value diagnosis but does not complete
the hitter goal, uncertainty, full WAR or long-term player valuation.

Additive source follow-up: the [returner review](hitter-returner-coverage-result.md)
now supplies the saved Conforto panel/roster check and explains the membership
construction. Rankings extend to January while other inputs and population remain
through prior December. The three recently active omitted returners contribute
only 604 PA, alongside 607 omitted non-return origins. This is a narrow population
timing gap, not an explanation for the original within-cohort workload errors.
All original ledger forecasts, scores, receipts and conclusions remain intact.
