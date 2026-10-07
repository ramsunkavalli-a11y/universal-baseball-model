# Test defensive skill within the player value forecast

2026-10-07. This is a development comparison on exposed historical years, not a
new protected test. The source and player review is complete. The question is
whether the existing defensive-talent estimates help forecast delivered MLB
defensive runs, and whether those runs improve a broader player-value forecast.
It does not replace the pooled future-MLB quality tests with a next-year target.

## Fixed population and comparisons

Keep all 12,432 player-origin identities at the 2022, 2023 and 2024 origins,
targeting 2023–2025. Preserve non-arrivals, exits, missing channels, source
support flags and the full-MLB remainder. Use only the reviewed source ledgers
and saved forecasts; no new fit, tuning, data acquisition or outcome-based
forecast override is allowed in this comparison.

Cross the three saved opportunity arms (PA-scaled historical usage, own-repertoire
repair, supported position transition) with three fixed quality recipes:

- Neutral: zero defensive quality, with the same positional adjustment.
- History: the previously fixed opportunity-shrunk channel histories.
- Calibrated range: the history recipe with the separately saved age/range
  estimate where a saved chronological fit exists and a measured MLB history
  is present; otherwise keep the history fallback. Preserve sparse profiles
  and extrapolation warnings, not a claim of universal support.

The primary contrast is history versus neutral within the own-repertoire arm.
Calibrated range versus history and the two other opportunity arms are fixed
secondary comparisons, not a search for the best-looking combination. The
opportunity arms were already reviewed and retain their failures. Keep their
PA, position shares and native-opportunity conversions unchanged.

Batting is the reviewed season-relative ledger's `combined_value`, using exactly
the same saved expected PA. It already includes replacement. Do not refit its
hitting model, add replacement again, substitute a different PA forecast or
claim this is the latest frozen production route. Show the unchanged preseason
batting reference as context, not another selectable integration arm.

## Exact accounting

Range runs equal predicted position outs × predicted range rate / 1,500.
Framing/blocking use their saved forecast opportunities × rate / 1,000;
throwing, OF arms and receiving use opportunities × rate / 100. Add distinct
channels only once. Zero history has an unknown-quality mean-zero fallback,
not a measured average grade; no calibrated range is invented for a newcomer.
Do not use actual future counts as forecast inputs.

Position runs sum position-specific projected outs times the published schedule
divided by 4,374 outs: C +12.5, 1B -12.5, 2B/3B/CF +2.5, SS +7.5,
LF/RF -7.5. The available DH exposure is starts, so use -17.5 × DH starts /162
as an explicitly approximate research definition, with the identical definition
in outcomes. It is not a reconstruction of published DH WAR. Unallocated field
time receives no invented roster-position adjustment and remains flagged.

Expanded common-win value = unchanged batting-plus-replacement + (position runs
+ defined defensive runs)/10. The measured target uses season-relative batting,
actual official position/DH exposure and measured native defensive numerators.
It excludes baserunning, DP, non-OF arms, exact season-specific runs-per-win,
full park/league WAR corrections and contract/control/option value. Call it
expanded value, not full WAR. No league-WAR quota is imposed.

## Missing measurement and scores

Unknown applicable channel targets stay null. Keep every forecast in the saved
outputs and coverage report. Primary summed-defense/expanded-value scoring uses
the fixed complete-defined-measurement subset, explicitly identifying the
excluded-from-score participant count and exposure. That subset contains all
certified non-arrivals but only about 82–85% of actual defenders; it is not a
full-population accuracy claim. Also score each channel on its own observed
measurement set, and report participant-only and measured-history subsets.
Never let a zero native denominator turn non-arrival into an observed quality.

Report per-origin and equal-origin mean RMSE, MAE, bias and exact matched totals;
primary errors are delivered native runs and expanded common wins. Use 2,000
paired person-cluster draws, seed 712001, preserving each player's origins.
These nominal intervals do not account for earlier model selection or common
year shocks. Show groups by origin stage, known age, current MLB exposure and
quality-history availability. Groups with at least 100 complete forecast rows
are descriptive checks, not automatic vetoes for a microscopic loss. Also show
actual defenders so a large population of non-arrivals cannot conceal harm.

Actual-count diagnostics apply these identical quality estimates to measured
future opportunities only to separate quality from opportunity errors. They
are oracle diagnostics, not usable forecasts or new eventual-talent validation.
No isolated actual OF count is fabricated for mixed positions. Compare positional
adjustments separately; inspect whether a role change falsely improves value
by cancelling a batting or defensive-quality error.

As an accounting sensitivity only, repeat expanded-value errors with framing
removed from both sides (full ABS scenario). This is not a claim about when
ABS arrives or a learned effect of the challenge system. Non-framing catcher
quality and positional uncertainty remain.

## Player review and decision

Keep the nine source focal cases and their 27 peers. Add, for the primary
contrast, the biggest delivered-defense gain/loss, biggest expanded-value
gain/loss, largest false high/low, and one ordinary participant; add calibration
gain/loss if distinct. Select three peers by the same origin-known stage,
dominant-role, nearest-age/exposure rule. Trace dated stats, actual history
arithmetic, native and position opportunity, each channel's runs, batting,
positional value, complete/partial status, all compared forecasts and reality.
Include minors/non-arrivals, unsupported young development and real reversals.
Outcome-selected cases explain mechanisms, not independent confirmation.

Retain useful MLB skill even if broader value loses because other errors cancel;
likewise a broader-value win alone does not validate a skill model. Integration
needs aligned skill/delivery evidence, sensible positions and no source/unit
failure. Finish the player walkthrough and independent accounting/score replay
before a disposition or another experiment. No automatic promotion: the known
young development, sparse minor talent and role-plan gaps require practical
research limitations. Frozen forecasts/explorer and 2026 selection stay unchanged.

Sources: [position schedule](https://library.fangraphs.com/misc/war/positional-adjustment/)
and [component definition changes](https://blogs.fangraphs.com/2024-fangraphs-war-update/).
