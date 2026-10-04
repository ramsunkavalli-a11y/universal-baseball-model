# Separate entrant workload training does not improve the candidate

2026-10-04. Keep the current workload construction. The matched comparison
removes established hitters from conditional training, but does not improve
prospect PA or delivered-value forecasts. Seventy new models replay and thirteen
actual player walkthroughs are complete. These are development results, not
deployment approval. Protected 2026 and the frozen forecast are unchanged.

The useful new finding is diagnostic: low PA forecasts for several stars do
not mean every prospect's conditional workload is too low. Across actual
debutants, conditional PA totals are almost exact, while arrival allocation,
individual workload and hitting errors remain substantial. A blanket PA boost
would target the wrong problem.

## What changed and what stayed fixed

The [locked comparison](hitter-prospect-workload-specialization-contract.md)
keeps all 30,506 forecasts, including 24,199 never-debut records and every
certified non-arrival. Four conditional-workload arms use identical 253 inputs
and tree settings: pooled versus first-arrival-only training, each with current
2011+ origins or all restored 2008–10 origins added. Specialized active subsets
contain 372–1,038 distinct people with current history, or 593–1,254 with older
history. Save support qualifications; total training size is not enough.

All arms use exactly the current debut probabilities, status rules and hitting
rate. Previously debuted forecasts remain bit-identical. Secondary value
ledgers use the previously reviewed translated/ranking hitting rate, declared
before fitting. Neither alternative rate nor new probability is fitted here.
Value is custom batting plus replacement in win units, not published full WAR,
club-control value or trade value. The public-player workload gap cannot be
fixed by a prospect-only change.

The [legacy clarification](hitter-prospect-workload-specialization-legacy-clarification.md)
matters. The old detailed workload result trained on both established and
first-time active hitters. Its prospect-only label described forecast routing.
Although its helper lacked explicit player exclusion, there is **zero active
training identity overlap with its never-debut query prospects in all twelve
cells**. Established-query overlap is not grounds to dismiss that primary
prospect result. Different inputs, weighting, sources and later integration
failures limit its transfer to today's candidate; do not call it disproved.

## Matched scores and baseball totals

Equal-target-year losses; raw totals across all seven origins. Lower error is
better. The many zero-PA prospects make these RMSEs much smaller than public
established-player RMSEs; they are different populations.

| Never-debut forecast | PA RMSE | PA MAE | Value RMSE | Expected PA total |
| --- | ---: | ---: | ---: | ---: |
| Current pooled training | 27.2521 | 4.7639 | .152257 | 81,849 |
| Pooled plus older training | 27.2569 | 4.8214 | .152462 | 83,369 |
| Separate entrant training | 27.2634 | 4.8178 | .152871 | 82,868 |
| Separate entrants plus older training | 27.3294 | 4.8438 | .153135 | 82,635 |
| Actual | — | — | — | 98,328 |

Separate current-history training minus pooled PA MSE is +.6152, nominal paired
95% interval [-16.7606,+17.4490]; value MSE +.0001875
[-.0001129,+.0004722]. With older history, specialization minus matched pooled
PA MSE is +3.9548 [-11.5193,+18.4076], and value +.0002056
[-.0000730,+.0004759]. Small, uncertain losses do not prove specialization can
never help, but provide no coherent benefit for this recipe. Intervals use
1,000 player-clustered draws on exposed historical development years; they do
not account for the project's entire experiment history or every season shock.

The stronger translated/ranking value anchor remains .151662. Separate
workload with that same rate gives .152387 or .152548, not an integration win.
Conditional PA RMSE among the 787 actual entrants worsens 122.16 to 123.69 or
126.05. That selected-participant diagnostic does not replace full scoring.

Upper-minors PA RMSE worsens 55.127 to 55.164 or 55.344 and value errors also
worsen. Lower-minors PA RMSE improves 7.966 to 7.924 or 7.904, but MAE worsens
and expected PA rises from 7,055 to 7,376/7,670 against only 5,194 actual.
Do not select a lower-minors exception after seeing this small tradeoff.
The 2021 prospect total remains 11,261/10,374 against 18,944 actual; 2023
remains too high at 15,422/14,942 against 11,697. This is not just one COVID
outlier. The public 2,627-player comparison is exactly unchanged: PA RMSE
138.33 and MAE 106.41 versus Steamer 135.38 and 92.08, with existing date and
coverage qualifications. MAE remains slightly outside the practical allowance.

Clipping to at least one conditional PA affects 262 separate-current and 214
separate-older forecasts; none exceed 800. Most are non-arrivals, but Jake
Rogers 2018 and Hayden Senger 2024 have negative separate-current predictions
before clipping and subsequently record 128/78 MLB PA. Senger also clips in
the older arm. The regressor can be physically qualified even when the product
is tiny; a bounded mean alone does not establish a good prospect forecast.

## What the accounting reveals

The [post-fit diagnostic](hitter-prospect-workload-specialization-diagnostic.md)
does not alter any forecast. For the 787 people who actually debuted, the
current conditional mean sums to 98,088 PA versus 98,328 actual, a difference
of only -240. After applying their probabilities, 54,656 PA are discounted;
38,417 expected PA go to players who did not arrive. Together those terms give
the full forecast shortfall of 16,479 PA. This is exact retrospective arithmetic,
not a causal decomposition or a model allowed to know future arrivals.

The near-exact sum hides allocation errors. In the raw pooled group with
10–50% predicted debut probability, average probability is 20.1% versus 26.4%
observed arrival; expected PA is 25,466 versus 37,423. Among its entrants,
conditional PA averages 114 versus 122 actual. Below 1% predicted probability,
the model expects 54 arrivals versus fourteen actual. At 80% or more, it
expects 58 versus 53. These differing directions rule out a blanket probability
increase as well. Only 67 forecasts occupy that last group; few-event and
origin qualifications remain.

The 2021 conditional sum among actual entrants is 19,701 versus 18,944 actual,
while expected debut count is 77.6 versus 158. In 2018 both conditional sum
and arrival allocation fall short. In 2023 conditional PA is too high. Thus
one generic workload correction cannot repair all years. The origin-known
top-20 rank group also underforecasts PA, 11,061 versus 13,827, with 38.4
expected arrivals versus 45 observed; it is not just a collection of famous
successful players chosen afterward. These are pooled diagnostic totals,
not a substitute for equal-year error, player review or future validation.

## Thirteen player walkthroughs

Every forecast below is at the end of the listed year for the next calendar
year. All original histories, actual 253 inputs, four saved tree traces,
support counts and outcome-blind peer selection are preserved in the case
evidence. Trace contributions are fitted path accounting, not causal effects.
Fixed hitting and arrival probabilities are shown so PA and value gains cannot
be mistaken for automatic talent improvements.

**Kurtz 2024:** age 21, 35 A plus fifteen AA PA, four HR, twelve walks and ten
K; rank .63 and high draft pedigree are present. Fixed debut probability 6.06%
times conditional 168 gives 10.18 expected PA. Separate training gives 179/159
conditional and 10.82/9.64 expected, against 489. Removing the negative
zero-MLB paths lowers the reference from about 279 to 114 rather than producing
a regular workload. Refined support remains zero; the four peers have much
weaker pedigree. Fixed hitting -.063 versus 5.150 is a separate major miss.

**Langford 2023:** age 21, 200 professional PA including eighty AA/AAA, ten
HR, 36 walks and 34 K, rank .95. Probability stays 59.91%; conditional falls
359 to 341/323, expected PA 215 to 204/194 versus 557. The specialized rank
path is about +100/+95 rather than +147, on a much lower reference. Refined
support is zero. Hitting .688 versus .549 is fairly close, so the new workload
reduction hurts value. Mostly weaker non-arriving peers do not justify the miss.

**Alonso 2018:** age 23, 574 AA/AAA PA, 36 HR, 73 walks and 128 K, with
earlier A-minus/A-plus production present. Probability 80.36% times conditional
268 gives 215 PA; specialization gives 210/197 versus 693. Scouting's path
shrinks while AAA role and power remain positive. Refined support is seven.
Thaiss, VanMeter, Mercado and Walsh's 164/260/482/87 PA show varied opportunity,
not a certainty of 693. Hitting .286 versus 3.283 also misses; this remains
both new arms' largest false-low value case.

**Acuna 2017:** age nineteen, 612 A-plus/AA/AAA PA, 21 HR, 43 walks and 144
K, rank .99 preserved. Probability 48.22% stays fixed. Conditional 211 becomes
237/205 and expected 102 becomes 114/99 versus 487. Scouting gains on a lower
specialized reference do not solve the low mean. Active refined support is
zero or one. Only two strict peers, Adames and Bauers, qualify. Fixed hitting
.164 versus 3.681 remains a distinct unresolved talent error.

**Julio 2021:** age twenty, 340 A-plus/AA PA, thirteen HR, 42 walks and 66 K;
2019 exposure is retained and no 2020 production invented. Fixed probability
80.51% converts conditional 316 to 254 PA. Separate heads lower it to 282/238,
expected 227/192 versus 560. Prior-rank path contributions shrink; refined
support stays nine. The older specialization is the largest value harm in
that arm. Abrams' 302 PA and weaker peers' zero/37 are timing controls, not
explanations for this star miss.

**Holliday 2023:** age nineteen, 581 PA across A through AAA, twelve HR, 99
walks and 118 K; current/prior ranking evidence is present. Fixed probability
88.68% times conditional 396 gives 351 PA. Specialized means 318/324 give
282/288, nearer 208, as a lower reference and negative A-plus exposure paths
offset pedigree. Helpful workload reduction still gives +1.165/+1.188 value
against -.503: fixed hitting +.621 misses realized -2.838. Keep this false high
visible. Langford succeeds among selected peers while several others do not.

**Hector Martinez 2016:** age seventeen, 204 DSL PA, four HR, 33 walks and
49 K after 186 PA in 2015. Fixed probability .15% yields .089 current PA and
.057/.091 new PA; actual is zero. No active teenage-DSL profile exists in either
training history, so paths transferred from other levels are unsupported.
Actual MLB rate is null. Immediate non-arrival does not settle lifetime talent.

**Yordan 2018:** age 21, 379 AA/AAA PA with twenty HR, forty walks and 92 K.
Fixed probability 43.40%; separate-current conditional rises 166 to 247 through
rank, AA doubles and AAA exposure, lifting expected PA 72 to 107 against 369.
This is that arm's largest value gain, but .374 still misses 4.968 and fixed
hitting .249 misses 5.648. Support 31/35 is better than the thin-history cases;
selected Rodgers/Longhi/Bradley/Castro still differ in pedigree and timing.

**Anthony 2024:** age twenty, 540 AA/AAA PA, eighteen HR, 77 walks and 127 K,
following strong 2023 advancement. Probability stays 92.13%. Current conditional
352 gives 324 expected PA, reasonably near 303 actual. Separate-current
conditional falls to 238, expected 220, as earlier-level role paths restrain
the model. It worsens a reasonable workload forecast and, with hitting already
too low, produces that arm's largest value harm. The older head gives 280 PA.
Basallo/Campbell/Shaw/Teel's 118/263/437/297 show relevant opportunity variation.

**Demeritte 2018:** age 23, 494 AA PA, seventeen HR, 56 walks and 140 K,
after substantial AA/A-plus histories. Fixed probability 9.42% and new means
60/71 produce only 5.63/6.66 PA versus 186. Values .0143/.0169 almost equal
.0157 actual only through opposing errors: hitting -.325 is much better than
realized -2.379 while workload is far too low. This ordinary-by-value selection
is not a well-predicted player. Add a genuinely ordinary control rather than
calling cancellation success.

**Walker 2022:** age twenty, 536 AA PA, nineteen HR, 57 walks and 116 K,
rank .97 after A/A-plus advancement. At fixed probability 63.92%, specialization
raises conditional 243 to 290/336 and expected 155 to 185/215 versus 465.
Scouting and AA production help. Older specialization's largest value gain
still predicts .819 against 2.829. Refined support fourteen is sparse; Winn,
Meadows, Pages and Rafaela show 137/145/0/89 PA, not equivalent star talent.

**Engel 2016:** age 24, 582 A-plus/AA/AAA PA, seven HR, 56 walks and 131 K,
after 608 A-plus PA. Fixed probability 63.45%; conditional 159 becomes 63/137,
expected 101 becomes 40/87 versus 336. The new heads worsen PA, yet reduce
positive value because hitting -.308 fails to foresee -4.703. A value-score
gain is therefore not a good workload forecast. This older arm false high
remains .223 versus -1.470. Riddle among selected peers gets 247 PA.

**Vavra 2021:** the supplementary ordinary case uses a transparent post-fit
rule requiring both PA and hitting to be reasonably close, not value alone.
Age 24, 218 minor PA including 184 AA, five HR, 34 walks and 48 K, with 453
A PA in 2019. Fixed probability 49.57% and conditional 173 give 86 PA; separate
heads give 96/75 versus 103. Fixed hitting -.025 versus -.146 is close, and
value .265/.298/.232 versus .238 does not hide a Demeritte-sized cancellation.
Support is 99/116. This reasonable partial-season forecast within 2021 prevents
calling every member of that cohort broken. It is illustrative, not independent
confirmation or a tuning case.

## Decision and coherent next work

Do not adopt either specialized head or select a post-result hybrid. Preserve
current opportunity and both reviewed hitting anchors. Removing zero-MLB paths
is not inherently a correction: established and entrant workload references
differ, and the saved predictions—not an isolated negative path—must decide.

This closes the pooled-versus-separate conditional-training question for the
declared recipe. The next material question is arrival allocation and history
meaning across eras, rather than another conditional PA multiplier. Earlier
prospect history/calibration and canceled-block tests already exist: generic
calibration overforecast later cohorts, and omission helped 2021 but harmed
2022. Do not repeat either blindly or tune a COVID boost. Reconcile those source
semantics against the current calendar-lag features, then predeclare any
structural correction with fixed workload/rate and whole-cohort checks. Public
established-workload and fuller value integration remain in the controlling
plan, not silently abandoned for prospects.

Evidence: [scores](../reports/model-evidence/hitter-prospect-workload-specialization/scores.json),
[intervals](../reports/model-evidence/hitter-prospect-workload-specialization/intervals.json),
[twelve primary case traces](../reports/model-evidence/hitter-prospect-workload-specialization/cases.json),
[ordinary supplement](../reports/model-evidence/hitter-prospect-workload-specialization/ordinary-case-supplement.json),
[allocation diagnostic](../reports/model-evidence/hitter-prospect-workload-specialization/allocation-diagnostic.json),
[completed review receipt](../reports/model-evidence/hitter-prospect-workload-specialization/completed-review.json).

Reproduction requires the existing local sealed source/model artifacts; tracked
receipts are not a standalone distribution of raw data or private public-system
exports. Three fit/connection tests and one allocation identity test pass;
checks and saved-head replays certify execution, not full model validation.
The diagnostic helper's two failed preliminary runs stopped before writing
evidence and were repaired without any model refit or forecast change.
