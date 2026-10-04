# What the current hitter candidate actually uses

2026-10-03. This review reconciles the current next-year hitter candidate with
earlier source and modeling work. It changes no forecast and fits no new model.
The useful finding is not a newly discovered winning injury feature: corrected
return information was tested in earlier alternatives and did not produce a
sound overall replacement. The current branch nevertheless needs clearer
availability scenarios and a better-qualified historical roster source.

The audit retains all 63,282 source rows and 30,506 historical forecasts. Seven
actual player forecasts are independently replayed through 21 saved heads,
including batting. Raw count histories, every opportunity input, saved path
terms, cutoff-known transaction records, requested roster captures and training
support are preserved in the evidence below. The completed comparison preceding
this inventory is [the delivered-value test](hitter-value-integration-v76-result.md).

## The components feeding the current forecasts

This is the research candidate described in [the model card](practical-hitter-candidate-v72-model-card.md),
not every component developed anywhere in the repository. Inspecting the actual
saved predictor lists gives the following map.

| Forecast component | What enters it | What does not enter it |
| --- | --- | --- |
| Any MLB appearance next year | A shallow histogram gradient-boosting classifier with 251 inputs: separate-level batting history, age, position, exposure, workload and quality, draft evidence, games and role history, reconstructed listing and fresher preseason prospect ranks | Corrected medical observation states, injury type, suspension duration, current employment states, salary and previous-season team record |
| PA if the player appears | A separate histogram gradient-boosting regression using the same 251 inputs | The same medical, legal, contract and team-record omissions; it is not a promised job |
| Batting contribution per 600 PA | A regularized linear model with 199 inputs, including age, position, separate-level exposure and pooled batting components, MLB quality and draft evidence | Fresher prospect-list inputs, an explicit foreign-performance translation, park-neutralized contact results, opponent-quality adjustments and detailed medical states |
| Expected batting plus replacement | Expected PA times the PA-weighted batting yield plus an origin-known replacement reference, with the previously documented PA-dependent bounds | Defense, baserunning, position value, native FanGraphs WAR, a calibrated joint distribution and trade value |
| Definitive availability | Separate origin-known permanent-ineligibility and reported-retirement rules can set final appearance and PA to zero | A rule declaring every injury, free agent, finite suspension or unresolved restriction permanently unavailable |

For pooled batting inputs, the three history years have weights 1, .8 and .6.
Event rates use a fixed 100-opportunity prior with their own denominator; unknown
foreign production is not supplied by that prior. Batting training weights actual
future MLB PA. This estimates a contribution-weighted conditional rate, not
unconditional current MLB talent for every minor leaguer. Explicit translated
components and rankings were tested in [the batting bridge](hitter-talent-bridge-v74-result.md),
but are not silently included in this current rate head.

The 2020 shortened MLB schedule is separately handled in workload references.
The canceled MiLB season is not invented as poor play. Histories and transactions
are cut off at December 31; the coming-season prospect lists have their separately
qualified publication dates. Calling this a fully matched Opening Day forecast
would overstate its available job and health information.

## Earlier availability work was tested but did not establish a replacement

The source adapter in [the observed-return review](hitter-observed-return-v60-result.md)
corrected recorded medical observation intervals. An activation or a dated MLB
PA window can establish that an interval no longer remains unresolved under
that definition. It does not establish full medical recovery, an exact injury
duration, or a future season without limitations.

[The workload-reference comparison](hitter-workload-anchor-v61-result.md) did
use that repaired information in both a direct PA model and a model predicting
an adjustment to demonstrated workload. Neither won overall. The anchored
version reduced absent-former-regular RMSE but predicted 7,974 PA against 4,556
actual and increased average absolute error. Its Tatis gain therefore cannot
justify a comeback boost for the entire group. Source repair and architecture
changed together versus the old anchor, so that result does not isolate the
effect of corrected medical information.

[The smooth comparison](hitter-bounded-workload-v62-result.md) also used the
repaired states. Its unrestricted common-calendar terms allocated too much PA
to mostly-zero prospects. That is a representation failure, not evidence that
all smooth models or injury information are useless.

[Employment source repairs](hitter-employment-v70-result.md) distinguished some
December announcements from later effective dates and retained missing older
coverage. [The subsequent matched employment test](hitter-employment-v71-result.md)
found no useful overall upgrade. A generic assignment can even be an All-Star
assignment, not a guaranteed contract. The corrected source facts remain worth
keeping, but are not verified current job guarantees.

This inventory confirms that the current saved opportunity heads receive none
of the repaired status inputs. It does **not** establish that adding them would
improve the current two-head construction, and does not reopen the closed queue
of small health, employment or penalty sweeps.

## The current forecasts do not support a blanket return adjustment

These are descriptive groups from cutoff-known captured states, not a new
predictive comparison or clinical cohorts. No outcomes define membership.
Counts are player-year forecasts, with repeated people identified separately.

| Previously debuted and zero current-year MLB PA | Forecasts | Distinct people | Expected next-year PA | Actual next-year PA |
| --- | ---: | ---: | ---: | ---: |
| Captured organization acquisition | 1,071 | 617 | 7,926 | 6,867 |
| Captured MLB scope exit | 477 | 271 | 4,045 | 3,280 |
| Captured MLB return state | 56 | 51 | 4,717 | 4,186 |
| Captured IL state | 3 | 3 | 228 | 242 |
| Unknown state | 141 | 86 | 96 | 93 |

The captured-return group is already about 13% overallocated despite major
individual misses. Acquisition and scope-exit groups also get more PA than
observed. These labels can include old records and incomplete histories, and
the population includes historical pitcher-batting identities. Do not reclassify
people after seeing their next-year outcomes or infer a causal recovery effect
from these totals. The full group tables remain in the audit report.

## Seven actual player reviews

All forecasts below target the following calendar year's MLB performance.
Batting rate is custom batting wins above the MLB average per 600 PA; value is
the compatible custom batting-plus-replacement proxy, not full WAR. The peers
were chosen within origin, stage and prior-debut status by age and three-year
MLB workload, without future outcomes. They are deliberately labeled generic
workload controls: they are not matched injury, legal, position or foreign-talent
comparisons. Broad and refined saved support counts are both retained.

### Fernando Tatis Jr. after 2022

The source records a wrist IL entry and an 80-game suspension, alongside 546
MLB PA and 42 HR in 2021, 257 PA and 17 HR in 2020, and 14 AA rehab PA in 2022.
Closing medical observation when suspension supersedes it is not clinical
recovery. No precise calendar suspension end is invented. The raw requested
December 31 40Man capture omits him; his current feature is therefore zero.

The replay gives 13.40% appearance probability and 296.16 PA if active, hence
39.68 expected PA against 635 actual. His batting estimate retains prior quality
at +1.289 per 600, producing .209 expected value against 3.333 actual. In the
saved path, off-listing contributes about -.550 log-odds to appearance and -24
PA to conditional use, while zero recent workload contributes about -94 PA to
the latter. These are within-fit arithmetic terms, not causal effects.

Only six distinct players match the saved broad active elapsed/state/regular
intersection. Bauers, Diaz, Peters and Long later get 272, 26, zero and zero PA;
none is an equivalent suspended star. This is a substantial temporary-absence
and opportunity miss, not evidence that retained talent guarantees a full return
or that a name-specific override would be valid.

### Matt McLain after 2024

The source includes shoulder surgery, a transfer to the 60-day IL and an
October 28 Cincinnati activation. He previously had 403 MLB PA and 16 HR in
2023, plus 180 AAA PA and 12 HR; 2022 included 452 AA PA and 17 HR. His 2024
MLB PA is zero. The independently read raw Cincinnati year-end 40Man response
contains 38 people but no McLain, agreeing with the model's zero listing input.

Appearance is 44.67%, active PA 294.75 and expected PA 131.65 against 577.
The batting rate is +.251 per 600 and value .466 against .706 actual. Off-listing
and zero current workload reduce opportunity in the saved paths; the corrected
observation closure is not an input. The activation and requested-set absence
are conflicting roster context. The transaction collection does not certify
that no subsequent removal occurred, so this is not yet a proven membership
repair or permission to force the flag to one.

Broad training profiles are well populated, but that is not shoulder-surgery
return support. Workload peers Marcano, Mauricio, Franco and Apostel later get
zero, 184, zero and zero PA for very different reasons. Their outcomes do not
explain away McLain. Reconcile listing provenance before refitting around it.

### Gavin Lux after 2023

Knee surgery and a November 6 IL activation are captured. He is present in the
requested roster, unlike McLain. Prior MLB workloads are 471 and 381 PA, with
six and seven HR; current MLB workload is zero. Observation closure is not a
claim of full recovery or an exact missed-days measurement.

Appearance 77.13% times active PA 287.53 gives 221.77 expected PA against 487.
The +3.644 roster log-odds path term raises appearance, while zero current
workload reduces conditional use by roughly 85 PA. Batting rate is -.243 per
600 and expected value .597 against 1.193 actual. Earlier versions' hitting
estimates must not be substituted for these current numbers.

The broad active intersection contains six people. Aquino, Neuse, Hoskins and
Bradley have zero, zero, 517 and zero future PA and are not all clinical return
controls. Lux is a missed comeback; group overforecasting shows why treating
this as a universal comeback allocation rule is unsafe.

### Wander Franco after 2023

Restricted status and administrative leave are cutoff-known, alongside 491
current MLB PA, 17 HR and positive prior production. The requested roster lists
him, but reserve listing does not establish playing eligibility. Later legal
findings or a ban cannot be backdated into the forecast.

The ordinary opportunity heads give 99.05% appearance and 564.86 active PA,
hence 559.49 expected PA and 2.698 expected value versus zero actual. Normal
recent exposure and listing dominate without a leave-state predictor. Nearly
certain appearance is inadequately qualified given the known unresolved status.

Garcia, Kelenic, Taveras and Sanchez later get 528, 449, 529 and 537 PA, but none
is an administrative-leave control. One case cannot validate zero for all
restrictions. The candidate needs visible qualified availability scenarios;
this audit has not fitted their probabilities.

### Brandon Belt after 2023

The source records hamstring and back IL entries followed by activations, then
November free agency, not retirement. His 2023 production includes 404 PA,
19 HR and 60 unintentional walks, after 298 and 381 PA in prior years. The
year-end listing omits him. That does not prove he could not find a new team.

Appearance 64.63% times 377.77 active PA gives 244.16 expected PA; batting rate
is +.686 per 600, and expected value 1.035. He actually gets zero PA. Age and
off-listing reduce opportunity while production supports retained hitting.
Gomes, Solano, Grandal and Maldonado later get 96, 309, 243 and 147 PA, though
their positions and hitting differ.

This remains a reasonable forecast that missed an unusual unsigned outcome,
as the user explicitly noted. Keep it in scores. Do not turn it into an obvious
retirement case or invent an unsigned-player penalty. The separately reviewed
productive-free-agent cohort has close aggregate workload already.

### Tucupita Marcano after 2024

The ledger contains declared and sourced permanent ineligibility by origin.
It preserves a June 4 availability date and a June 6 source URL; this inventory
does not certify an earlier publication vintage. This timing qualification
does not move the evidence past December's forecast cutoff.

The permanent-eligibility wrapper sets final appearance and expected PA to
zero, despite a fitted conditional PA output of 181.43 and a batting estimate
of -1.023 per 600. Actual next-year PA and value are zero. That is a sound
origin-known eligibility constraint, not a statistical batting-model success.
Mauricio, McLain, Feliciano and Apostel are workload controls with 184, 577,
zero and zero future PA, not legal-status controls. Do not extend this definitive
rule to unknown or temporary restrictions.

### Eric Thames after 2016

A November 29 Milwaukee signing and a sourced foreign-return fact are captured.
His three recent domestic count windows are empty because the retained source
does not contain his Korean performance. Medical scope is unknown. Neither
fact establishes zero talent or a clean health history. He is present in the
requested roster, but that input cannot substitute for foreign production or
the assurance of the known multi-year MLB agreement.

Appearance 20.67% times active PA 100.49 gives 20.78 expected PA against 551.
The batting fallback is -.711 per 600; value .039 against 4.134 actual. The
roster log-odds term is strongly positive, but empty domestic workload still
pulls both opportunity and batting forecasts down.

Exposito, Tosoni, Cooper and Green share empty domestic windows and all get
zero future PA; they are not matched foreign performers with an MLB deal.
Even populated broad profiles cannot close that missing-source gap. Do not
boost every roster-only player to solve Thames or claim the project already
has a complete international projection system.

## Decision and the next useful work

Keep the current candidate and earlier negative results, with these limits
visible. No new predictive gain is established. The source and forecast replay
checks pass; that does not resolve unsupported profiles, medical uncertainty,
foreign performance or the public benchmark gap. Public PA MAE remains 15.56%
above Steamer on the qualified matched historical sample, outside the practical
15% allowance. Protected 2026 and the frozen forecast remain unchanged.

The next bounded task is **historical roster provenance**, not another status
feature or library sweep. Reconcile returned 40Man sets with dated transactions
and independent contemporaneous membership evidence across the cohort. McLain
is a diagnostic case, not the repair rule. Preserve missing and conflicting
evidence rather than certifying endpoint absence as nonmembership. Check both
false negatives and future signings leaking into past listings, and keep the
existing original forecasts and population intact. Only after that source review
should a documented fair comparison alter roster inputs.

Availability scenarios and missing international histories belong in the final
candidate's qualifications. They are not solved by this inventory. The broader
practical hitter goal, including supported talent/workload improvement and the
team-filtered handoff, remains active.

Evidence: [all source and saved-model traces](../reports/model-evidence/hitter-candidate-integration-audit/cases.json),
[descriptive groups and actual predictor lists](../reports/model-evidence/hitter-candidate-integration-audit/report.json),
[seven manual reviews](../reports/model-evidence/hitter-candidate-integration-audit/reviewed-cases.json),
[completed inventory](../reports/model-evidence/hitter-candidate-integration-audit/final-report.json).
