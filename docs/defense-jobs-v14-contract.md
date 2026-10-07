# Test position forecasts against the jobs available

2026-10-07. Improve next-calendar-year MLB position exposure and its contribution
to player value without changing hitting, playing time or defensive skill. This
is an opportunity integration test, not a new defensive-talent test. Better league
accounting alone will not certify better individual forecasts.

## Fixed population and measurements

Use all 12,432 saved forecasts at origins 2022, 2023 and 2024, with targets 2023,
2024 and 2025. Retain exits, minor leaguers, zero-PA defenders and unsupported
profiles. Use the reviewed annual position source and the separately certified
simultaneous P/DH starts from the completed DH audit. Correct own DH history,
training DH outcomes and scored DH outcomes identically in both arms. Old frozen
reports stay unchanged. Missing native defensive measurements remain null.

Expected MLB PA and the reviewed batting-plus-replacement contribution stay
fixed. The twelve saved history-quality recipes and held-player native opportunity
conversions stay fixed. There is no new quality fit, Statcast feature search,
batting repair, 2026 outcome query, production promotion or explorer alteration.
This research target omits running, some defensive channels and contracts; it is
not full WAR, peak talent, six years of control or trade value.

## One comparison and one mechanism diagnostic

The primary reference is the existing repertoire forecast reconstructed with
corrected DH source definitions, the same saved training identities, group rules,
100-PA pseudo-sample and fielding repertoire. Recompute DH numerators but retain
its original fielding calculations. The candidate represents eight fielding
positions and DH jointly, then limits each position to its cutoff-known available
jobs. Save the unconstrained joint allocation as a mechanism diagnostic, not an
alternative candidate to select after seeing results.

Express DH starts as job-time units using the origin's full-MLB average outs per
position start. This is an explicit game-time approximation, not DH innings. In
training labels use the mature label season's measured conversion; prediction
inputs use only the origin conversion. Own role history uses three MLB seasons
weighted 1, 1/2 and 1/4, including zero-field DH records. Without recent MLB use,
use the latest minor position record, then a roster position if available. Keep
unknown roles unknown. A returning MLB player's record is not replaced by rehab
usage. A pure DH role is not a missing position.

Learn conditional nine-role proportions only from mature target seasons 2022 or
later, with positive future job exposure and PA, excluding the entire held-player
fold. Include pure-DH futures. Select the first group with 20 distinct people and
10 effective job-exposure people: role with prior-MLB status, role, family with
status, family, all. Preserve sparse detailed profile counts separately; a broad
fallback is not proof of lower-minor support. Mix own and learned proportions by
the existing weighted MLB PA reliability, PA/(PA+100). Do not allocate catching
without origin-known catching history or a catcher roster position. Unknown roles
receive no invented assignment or measured quality.

Hold each player's total forecast job exposure to the source-corrected reference
potential fielding outs plus DH job-time units. Thus the test changes allocation,
not batting PA. Missing-role exposure remains a separate unassigned reserve.

## Physical constraints without forced totals

Use the full origin MLB inventory for each fielding position and DH, not the
future observed inventory. Reserve at each position the largest omitted-player
fraction in mature same-rule target cohorts available by that origin. This is a
conservative historical coverage allowance, not a prediction of future entrants.
Also reserve unknown-role job time uniformly across the nine caps as accounting,
not as a forecast of their positions. Never assign the reserve defensive value.

If known job exposure exceeds total available capacity, reduce all known job
totals proportionally; do not change expected batting PA. Otherwise preserve row
job totals exactly. Minimize relative entropy from the unconstrained nine-role
allocation subject to those row totals and position upper bounds. Preserve all
structural zeros. Columns need not fill: unused capacity remains explicit. A
sparse linear feasibility check precedes the convex nine-variable dual solve.
Stop on infeasibility, nonconvergence or failed residual/zero checks; do not add
new positions, change caps or tune a new solver after scores are visible.

The dual is sum_i r_i log(sum_j p_ij exp(-lambda_j)) + sum_j c_j lambda_j,
lambda >= 0. Its gradient is capacity minus allocated column mass. The resulting
allocation is r_i p_ij exp(-lambda_j) divided by the row sum. This is a constrained
information projection, not learned player development or MinT reconciliation.
[Computational Optimal Transport](https://arxiv.org/html/1803.00567v2) supplies
background on entropy and constrained allocations.
[Forecast reconciliation](https://otexts.com/fpp3/reconciliation.html) motivates
coherent totals; neither source establishes baseball accuracy for this recipe.

## Scoring and baseball review

Primary loss is equally weighted origin RMSE on the identical expanded measured
value target, with person-clustered paired 95% intervals using 2,000 draws and
seed 712001. Report position-run and native-defense RMSE separately, nine-role
job-cell error, actual-defender and measured-history subsets, age/stage profiles,
all origins and all twelve observed channels. Partial native rows remain in all
observed channel and position checks even when expanded value is unknown.
Repeat expanded accounting without framing as a rule sensitivity, not a forecast
of ABS policy. Matched and full MLB totals, omitted-player jobs, unknown-role
reserve and unused capacity remain separate.

An interval excluding no expanded-value improvement is positive development
evidence, not automatic adoption. A greater-than-5% error deterioration in any
origin's position or native-defense metric requires repair/rejection of this
candidate even if total value improves through cancellation. Smaller changes are
reported, not automatic microscopic vetoes. Physical consistency is necessary
but cannot excuse implausible role switches or weak training support.

Fixed walks: Ohtani at all three origins, Schwarber 2023, Alvarez 2024, Witt 2024,
Eldridge 2024, Bailey 2024, Raleigh 2024, Rafaela 2024, Chourio 2023 and Franmil
Reyes 2022. Add largest expanded gain/harm, false high/low, defense gain/harm and
an ordinary defender. Each has three peers selected on origin-known role, stage,
age, PA and role distribution, with complete source histories so tiny higher-level
stints are visible. Walk source, reliability, selected prior, unconstrained and
constrained roles, fixed quality, position/defense/value arithmetic and reality.
Discuss harms and quality missingness before disposition or another experiment.

## Integrity and scope

All fold identities, cutoff checks, support counts, source hashes, code, tests
and this contract are sealed before group numerators are fitted. Preserve old
contracts/results. Any necessary execution correction needs an archived version
and additive amendment. Independently replay group estimates, allocation
constraints, native arithmetic, metrics and case calculations. The full defense
goal remains active after this comparison; minor talent and longer-horizon use
still need their own supported evidence.
