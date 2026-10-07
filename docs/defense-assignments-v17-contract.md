# Learn current assignments separately from older position experience

2026-10-07. Test one coherent replacement for primary-position group borrowing.
Predict a hitter's next-season MLB role shares from observed position use,
keeping current MLB, every current minor sport, recent qualified use and older
repertoire separate. This is an assignment test, not a defensive-talent test.
The defensive quality estimates and expected playing time stay fixed.

## Target and fixed comparison

Use the same 12,432 player/origin forecasts for origins 2022–2024 and mature
targets through 2025. Non-arrivals remain in delivered-value and exposure scores;
their defensive skill is not labeled zero. Partial native targets remain partial.
Training uses the same saved held-player chronological cells and positive-PA,
positive-job-mass labels under the universal-DH policy, target 2022 or later.
Their conditional labels are the nine actual role masses divided by their sum:
C, 1B, 2B, 3B, SS, LF, CF, RF and DH. DH mass uses the target year's existing
reviewed outs-per-start conversion; it is not invented fielding innings.

Primary contrast: the new constrained assignment versus the saved constrained
joint-role forecast. Secondary anchor: the saved own-repertoire reference.
Use identical predicted job mass per person, predicted PA, batting, twelve native
skill recipes, conversion tables, league capacities and omitted-player/unknown
reserves. The same capacity reconciliation operates on the new role seed. This
isolates assignment; it cannot repair an incorrect workload or quality forecast.

## Inputs and estimation

The completed population source is `defense-role-v16/calendar-repair`.
Only origin-year and earlier inputs are allowed. Never join its later outcomes
or current hydrated biography metadata into features. Current outs and DH starts
come with independent certification flags; uncertain measurements use a numeric
placeholder plus a missing flag, not a claim of measured zero. Unresolved-period
exposure is kept separate from known late use and is never assigned a point date.

For current sports 1, 11, 12, 13, 14 and 16, use all nine role exposure counts,
with field outs divided by the origin outs-per-start proxy and DH in starts.
Scale each count as log(1 + starts-equivalent)/log(163), preserving sample size
as well as role. Include field- and DH-coverage flags. Tiny MLB/AAA stints cannot
erase other levels because they remain separate inputs. Sport 16 still combines
DSL and complex contexts; this qualifies role evidence, not defensive quality.

Include known late MLB/minor role counts, their unplaced period mass, previous
two seasons of MLB and minor role counts separately, full pre-origin observed
position indicators, roster position, stage, age and prior-debut status. These
are role/development inputs, not a new injury, performance or team-record model.
No fixed recency mixture or primary-role prototype supplies the prediction.

Fit a nine-output fractional multinomial logit conditional mean. Minimize the
sum of fractional cross-entropy plus one-half the squared non-intercept
coefficients. Each training person has total weight one across their included
seasons. This is a fixed regularized model, not a tuned algorithm tournament;
the unit coefficient penalty is a declared weak regularizer on scaled inputs,
not claimed optimal. Stop on failed convergence or invalid shares.

Fractional shares including zero/one boundaries have a suitable statistical
framework in [Mullahy's share-model paper](https://www.nber.org/papers/w16354).
Its published abstract supports conditional-mean share modeling; the specific
features, regularizer and support policy here are our choices, not a baseball
method prescribed by that paper. Historical FanGraphs practice also separates
[position-specific opportunity from rate projections](https://blogs.fangraphs.com/2013-positional-power-rankings-introduction/).
This test does not reconstruct their human depth charts or future assignment plans.

## Support and fallbacks

Audit every actual fold before any fit: source completeness, chronological
labels, fixed identities and player disjointness. Count distinct people by
stage, age, current dominant role, MLB exposure band, and current-source coverage,
including joint profiles. Twenty matching people is a warning threshold, not
proof of enough data. Persist every training identity and count.

An unseen stage/current-dominant-role profile falls back to the player's current
observed MLB-plus-minor role mass, then older own role evidence, then roster
position. Missing certified DH counts are not filled from raw disagreements.
Sparse but seen profiles retain explicitly qualified predictions. The existing
origin-catching-evidence guard remains unchanged, with renormalization after
masking; it is a conservative policy, not a physical-impossibility claim.
Existing unknown-role mass remains in the same reserve rather than being given
arbitrary defensive value. Do not remove unsupported evaluation rows.

## Scoring and required player review

Primary loss is equal-origin expanded-value RMSE on the identical measured
subset. Report person-cluster paired 95% intervals against both saved anchors.
Report role-cell exposure errors and conditional role-share error, positional
runs, delivered native defense, no-framing scenario, actual defenders and
measured-history subsets separately. Show origin/stage/age groups and matched
position totals; a league total improvement cannot certify individual choices.
An origin's position or native-defense error more than 5% worse is a tolerance
failure to explain, not an automatic whole-idea rejection.

Retain the nineteen existing focal and 57 origin-blind peer walks. Add largest
expanded/native gains and harms, major false highs/lows and an ordinary defender
after scoring; choose three extra peers from origin-known stage, age, role and
workload, without future outcomes. Show source stats, actual feature vector,
fitted role-logit terms, support/fallback, pre/post-cap role allocation, fixed
quality, position/defense/value calculations and later reality. Check whether
a final gain is merely cancellation between component errors.

No disposition before that review and independent arithmetic replay. A nominal
gain with implausible assignments or unsupported minor profiles remains research.
Preserve failed/inconclusive results, stop for actual data/design defects, and
do not retune on the named cases. No forecast/explorer promotion or 2026 outcome
selection. The broader defense goal remains active, including minor defensive
talent identification and multi-year development/opportunity.
