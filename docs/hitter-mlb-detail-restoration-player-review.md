# Player checks for restoring separate MLB batting history

2026-10-05. All seventeen actual source-to-model walks are reviewed. This
comparison does not qualify as an incumbent replacement. Separate MLB history
helps some forecasts, hurts others and leaves major source-transfer, workload
and breakout gaps. The [result](hitter-mlb-detail-restoration-result.md) gives
the matched population, uncertainty and cohort failures alongside these cases.

## Selection and how to read the calculations

Sixteen cases were fixed before fitting from the preceding completed comparison.
The mechanical largest gain, largest harm, false low and false high were already
among those cases. Ty France 2018 is added as the ordinary case: smallest absolute
restored delivered error among original forecasts with 200–399 actual next-year
PA. Outcome-selected examples diagnose behavior, not independently confirm it.
For the sixteen fixed cases, the previously saved origin-production peer selection
is unchanged. France's three distinct peers come from his actual earlier training
fold, with the same debut status and stage, selected by past production, age,
workload and pedigree distance without using future success. Failures are retained.

An origin year means the latest completed source season, predicting the following
calendar year. Information dates below are the saved preseason cutoffs, not a
claim that every source event happened on December 31. Ages are the saved model
ages, not independently updated birthdays. All cases have no extrapolation warning
on the four newly added features, but that does not prove joint profile support
or certify every older feature's range.

Hitting is batting wins above the future MLB mean per 600 PA. Delivered value is
batting plus the existing replacement term, not full WAR. A player without MLB
PA has unobserved hitting, not measured zero talent. The unchanged common
past-production baseline combines MLB and translated domestic/foreign records,
recency weights and a 1200-PA prior; foreign past production is not treated as
an already validated MLB forecast. Actual sources and references are independently
reconstructed. All fitted heads replay.

For every case, restored rate = common baseline + intercept + sum of fitted
feature effects. The table's residual includes the intercept. The precise change
from direct rate equals effects of the four new summaries plus changes to the
old coefficients and intercept. Annual and pooled summaries overlap; their
coefficients are not literal independent season weights or causal importance.

| Player and origin | Row and fold | Age and information date | Baseline | Restored residual | Direct rate | Restored rate | Actual rate |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Aaron Judge 2016 | 23934, 3 | 24, 2017-01-28 | −0.726057 | +0.471953 | −0.095499 | −0.254103 | +5.329876 |
| Eric Thames 2017 | 27981, 4 | 30, 2018-01-27 | +3.149685 | −0.080469 | +3.071788 | +3.069216 | +0.622421 |
| Kevin Maitan 2017 | 31364, 4 | 17, 2018-01-27 | −1.132281 | +0.832418 | −0.360172 | −0.299862 | Unobserved |
| Khris Davis 2018 | 32325, 3 | 30, 2019-01-27 | +1.428279 | +0.993504 | +2.433075 | +2.421783 | −1.518480 |
| Stevie Wilkerson 2018 | 32754, 3 | 26, 2019-01-27 | −1.112917 | −0.246834 | −1.424622 | −1.359751 | −1.650306 |
| Yordan Alvarez 2018 | 35088, 2 | 21, 2019-01-27 | −0.467743 | +0.939487 | +0.493018 | +0.471745 | +5.647887 |
| Austin Nola 2021 | 42235, 2 | 31, 2022-03-18 | +0.610894 | −0.877876 | −0.340647 | −0.266982 | −0.924711 |
| Fernando Tatis Jr. 2021 | 43296, 0 | 22, 2022-03-18 | +2.085676 | +1.175479 | +2.989775 | +3.261156 | Unobserved |
| Seiya Suzuki 2022 | 47765, 1 | 27, 2023-01-26 | +2.577305 | +0.021317 | +2.719118 | +2.598622 | +1.996717 |
| Aaron Judge 2023 | 50698, 3 | 31, 2024-01-26 | +2.756953 | +1.017037 | +3.511296 | +3.773990 | +7.557649 |
| Kameron Misner 2024 | 55509, 3 | 26, 2025-01-24 | −0.733207 | −1.226180 | −2.016094 | −1.959387 | −2.025635 |
| Geraldo Perdomo 2024 | 55587, 1 | 24, 2025-01-24 | −0.264995 | −0.428146 | −0.636747 | −0.693141 | +2.727891 |
| Nick Kurtz 2024 | 57052, 2 | 21, 2025-01-24 | +0.238192 | +0.415547 | +0.688155 | +0.653739 | +5.150009 |
| Masataka Yoshida 2024 | 57778, 3 | 30, 2025-01-24 | +1.596821 | −0.233760 | +1.322127 | +1.363061 | −0.443798 |
| Jung Hoo Lee 2024 | 58061, 1 | 25, 2025-01-24 | +1.839976 | −0.528863 | +1.407146 | +1.311113 | +0.463100 |
| Seiya Suzuki 2021 addition | 63309, 1 | 27.37, 2022-03-18 | +3.920524 | −0.545772 | +3.591051 | +3.374751 | +1.174589 |
| Ty France 2018 | 34339, 1 | 23, 2019-01-27 | −0.964989 | +0.940129 | +0.037504 | −0.024860 | −1.059985 |

Judge, Thames, Davis, Wilkerson, Nola, Tatis, Suzuki 2022, Misner, Perdomo,
Yoshida and Lee use the tracking route. Maitan, Alvarez, Kurtz, Suzuki's addition
and France use the prospect route. Route names describe this saved model's
selection, not universal tracking coverage. Machine evidence contains the actual
intercepts, all transformed feature inputs, coefficients and effects, not only
the terms discussed below.

In each sensitivity calculation, removing minor or foreign evidence rebuilds
the affected common profile and controls while retaining actual MLB summaries.
Artificially zeroing the four summaries still leaves MLB evidence in the common
pool. These are explanatory probes under unchanged parameters, not causal
experiments or independently evaluated replacements. Support counts below are
distinct full/active training people in the declared joint quality profile, not
counts of exact statistical twins. Peers are a separate broader comparison.

## Aaron Judge before the rookie breakout

His 2016 MLB debut has 95 PA, four homers and 42 strikeouts. AAA adds 410 PA,
19 homers and 98 strikeouts, with earlier A/AA/AAA history in the source window.
The poor MLB debut is −2.387 unshrunk batting wins per 600, shrunk to −0.175
by 95/(95+1200). The new summaries add −0.052771 and relearning the old inputs
adds −0.105834, moving the direct forecast down another −0.158604. The fitted
intercept is −0.270355; the full residual still raises the baseline to −0.254103.
Removing minor evidence raises the fitted rate by +0.555648, an artificial
warning about this representation, not proof that his minors should be ignored.

Expected PA remains 309.9 versus 678 actual. Restored delivered value is 0.825
versus direct 0.907, incumbent 1.093 and actual 8.115. The conditional forecast
worsens too. Support is 215/178; peers d'Arnaud 2013, Alonso 2011 and Taylor
2014 later hit +0.064, +0.367 and −2.038 respectively. This is a real breakout
miss, not an erroneous debut or proof that all such players become Judge.

## Eric Thames remains the largest delivered harm

The latest MLB source is 551 PA, 31 HR, 163 K and 70 unintentional walks in 2017.
KBO source years 2016/2015 supply 529/595 PA and 40/47 HR, 780.2 recency-weighted
foreign PA. Latest MLB quality is +0.762; the common baseline is already +3.150.
New MLB terms add +0.253074, almost entirely offset by −0.255645 from the old
coefficient changes. Restored +3.069 remains far above actual +0.622. Removing
foreign evidence changes the fitted rate by −2.401024 to about +0.668; that
mechanically identifies dominance of foreign history but does not validate the
artificial alternative or a new league translation.

Expected 444.4 PA versus 278 actual produces 3.640 value versus 1.144 actual and
1.641 incumbent. Joint support is 0/0. Earlier KBO peers Kang 2015 succeeds
at +2.658, Park 2016 does not appear and Hyun Soo Kim 2016 hits −2.605. Adding
positive MLB history cannot by itself teach adaptation in a nearly unsupported
profile; this major harm must not be concealed by Suzuki's gain.

## Kevin Maitan has no next year MLB talent observation

The source is 176 rookie PA, two HR and 49 K at age 17, with no MLB counts in
any of the three covered years. All four summaries are zero evidence. New terms
contribute zero; changes to older coefficients raise the rate +0.060310. Age
contributes +0.985687 to the fitted residual and the scouting-list indicator
+0.221388, against other negative terms and an intercept of −0.279977.
Removing minor evidence raises the rate by +1.102409 under this fit.

Expected 1.985 PA and 0.005115 delivered value versus zero actual stay in overall
scoring. His conditional hitting cannot be scored and this says nothing definitive
about lifetime failure. Joint support is 2682/3, a large eligible group but almost
no active next-year talent labels. Origin-selected Jhan Rodriguez, Starlin Balbuena
and Cesar Mejia all fail to appear next year too; they are retained rather than
replaced with eventual stars.

## Khris Davis has a genuine strong history before declining

MLB seasons 2018/2017/2016 contain 654/652/610 PA and 48/43/42 HR. Annual
summaries are +0.872/+0.764/+0.568 and pooled +1.228. The new terms contribute
+0.332043, including +0.239238 from pooled quality; old coefficient changes
subtract −0.343335. Restored +2.422 is almost unchanged from direct +2.433,
above incumbent +2.288, but below the earlier count forecast +3.395.

Actual hitting falls to −1.518. Expected 572.8 PA versus 533 actual delivers
4.076 versus 0.293 actual. Neither small MLB history nor foreign mixing explains
this miss. Support is 81/80; Frazier 2016 later hits +0.795, Dozier 2017 −0.415
and Morales 2013 −1.828. Their outcomes show real decline risk, not advance
knowledge of Davis's decline. Adding truthful positive history leaves it unresolved.

## Stevie Wilkerson improves delivered error through a tradeoff

His 2018 record has 49 MLB PA, no HR and 16 K, plus 86 AAA PA with four HR,
21 AA PA and six rookie PA; earlier A/AA records remain. Latest MLB summary is
−0.202. Added terms lower the forecast −0.057657, but old coefficient changes
raise it +0.122528, so the net forecast rises from −1.425 to −1.360. The tracking
fit includes a mean-exit-velocity effect −0.185872 and intercept −0.397964;
this change does not add new tracking data. Removing minor history adds +0.988067.

Actual hitting is −1.650, so the rate worsens versus direct. Expected 109.5 PA
versus 361 actual yields value 0.0891 versus 0.1190 actual, closer than direct
0.0773. Better delivered error is not better talent. Support is 465/308; Luis
Martinez 2011 has only 19 future PA and −8.876 noisy hitting, while Alex D. Mejia
and Cameron Perkins do not appear. Tiny peer outcomes are not stable talent labels.

## Yordan Alvarez remains a false low

The 2018 AA/AAA record totals 379 PA, 20 HR and 92 K. Earlier A/A+ records and
57 DSL PA remain, the latter only 34.2 recency-weighted observations. There is
no MLB history, hence no added-summary effect. Old coefficients alone lower
direct +0.493 to +0.472. The common baseline is −0.468 and the fitted residual
+0.939487, including intercept −0.345478. Removing minor history raises the
fitted rate +0.363074; the compressed representation still needs care.

Expected 72.2 PA versus 369 actual and actual +5.648 hitting produce 0.279
forecast value versus 4.610 actual. Separate MLB features cannot fix a predebut
breakout themselves. Support is 1398/318, broader than exact Alvarez comparables.
Sánchez 2013 does not appear; Singleton 2013 and Pederson 2013 later hit −1.193
and −2.106, the latter on 38 PA. Not every young power profile realizes this upside.

## Austin Nola loses an earlier cancellation

His MLB records are 194 PA/two HR in 2021, 184/seven in shortened 2020 and
267/ten in 2019, plus 39 latest AAA PA and older 229 AAA PA. The actual 184
short-season observations are not inflated. Pooled MLB quality is +0.244;
new terms add +0.049445 and other changes +0.024219. Direct −0.341 becomes
−0.267, moving farther from actual −0.925 despite a −0.635644 fitted intercept.
Removing minor evidence lowers the fitted rate −0.136971.

Expected 245.9 PA versus 397 actual yields restored value 0.6611 versus 0.6322
actual. Direct 0.6309 was almost exact partly through opposing hitting/workload
errors. Support is 298/172. Flaherty 2018 and Shane Robinson 2016 later have
22 and 35 PA with extreme negative rates; Clint Robinson does not appear.
They support caution around fringe workloads, not a stable prediction of Nola's decline.

## Fernando Tatis Jr. separates talent from absence

His 2021 MLB season has 546 PA and 42 HR; the source pool has 974.8 weighted
MLB PA and only 4.8 weighted AA PA. Latest MLB quality +1.348 and pooled +1.851
contribute +0.466567, partly offset by −0.195185 changes elsewhere. Direct
+2.990 rises to +3.261. Removing minor evidence changes it only −0.019958.

Expected 553.0 PA versus zero actual yields 4.738 forecast contribution versus
zero, worse than direct 4.488 and incumbent 4.423. No actual conditional hitting
exists for that year. A plausible high talent forecast can worsen a no-playing-time
miss; absence cannot be relabeled as zero ability after the fact. Support is
37/37. Montero 2012 hits −2.311, Torres 2018 +2.014 and Sanó 2015 +0.908.
Their varied outcomes do not make next-year absence predictable from this change.

## Seiya Suzuki after his first MLB year remains the largest gain

His 2022 MLB evidence is 446 PA, 14 HR, 110 K and 39 unintentional walks, plus
11 AAA PA. NPB 2021/2020 has 533/514 PA and 38/25 HR, 734.8 weighted foreign
PA. Latest MLB quality is +0.318. The added terms actually raise the fitted
rate +0.104116; the −0.224612 change to old coefficients produces the net
decline from +2.719 to +2.599. Do not describe the positive added term alone
as causing the decline. Removing foreign evidence lowers the fitted rate −2.208736.

Actual +1.997 hitting is closer, but expected 406.3 PA versus 583 actual causes
restored value 3.0316 to be farther from actual 3.7655 than direct 3.1132.
Both beat incumbent 1.3804. Joint support is only 2/1. Tsutsugo 2021 later
hits −4.271; Nick Evans and Matt Clark 2014 do not appear. A big gain in one
player does not certify transfer from NPB across such thin support.

## Aaron Judge with substantial MLB history partially recovers

MLB seasons 2023/2022/2021 have 458/696/633 PA and 37/62/39 HR. Annual shrunk
quality is +1.317/+2.408/+1.279, pooled +2.792. The new effects total +0.659591:
pooled +0.57859, latest +0.13195, preceding year −0.04213 and oldest −0.00882.
Because annual and pooled predictors overlap, those negative coefficients are
not evidence that his 62-HR season hurts talent in isolation. Other fitted
changes subtract −0.396897; the net improvement over direct is +0.262694.

Restored +3.774 remains below incumbent +3.899 and far below actual +7.558.
Expected 536.0 PA versus 704 actual gives value 5.031 versus 11.047 actual,
up from direct 4.796. Support is 113/112. Stanton 2022, Frazier 2017 and Alonso
2018 later hit −1.117, −0.540 and −2.191. These are broad trained comparisons,
not equivalent superstar histories or a claim that regression must miss this much.

## Kameron Misner moves away from an accurate rate

The source includes 15 MLB PA with ten K in 2024, AAA 519/519 PA with 17/21 HR
in 2024/2023, and AA 510 PA with 16 HR in 2022. Latest MLB quality is −0.153.
New terms contribute −0.045886 but old changes +0.102592, raising direct −2.016
to −1.959. Actual hitting is −2.026; the net movement worsens it. Removing
minor history raises the fitted rate +0.537856. The poor debut is present but
does not determine the net direction by itself.

Expected 84.5 PA versus 217 actual yields −0.0121 value versus −0.0549 actual,
farther than direct −0.0201. Earlier count value −0.0530 looked excellent despite
its less accurate −2.250 rate. Support is 848/587. Monte Harrison and Greg
Deichmann do not appear; Cole Tucker 2023 has 57 future PA and −2.859 hitting.
This is a clear reminder that delivered-error luck and talent accuracy differ.

## Geraldo Perdomo has an improving trend that the fit still underuses

MLB seasons 2024/2023/2022 have 388/495/500 PA and three/six/five HR, plus 27
latest minor PA. Annual shrunk quality improves from −0.873 to −0.105 to +0.050,
but pooled quality stays −0.417. New effects total −0.118517: the latest term
adds about +0.00511, pooled subtracts −0.08007 and the oldest subtracts −0.04690,
with the remainder in the intervening term. Old coefficient changes add +0.062124,
leaving direct −0.637 lower at −0.693. Removing minor evidence adds only +0.033583.

Actual +2.728 hitting and 720 PA contrast with expected 472.6 PA and 0.930 value
versus 5.522 actual. Incumbent −0.933 is worse on rate, but this restoration
worsens versus direct. Support is 254/244. Thole 2011 and Schafer 2011 later hit
−2.993 and −2.535; Brantley 2011 hits +0.303. Trend visibility is real, correct
breakout anticipation is not established, and these peers do not prove his leap inevitable.

## Nick Kurtz is not repaired by MLB only summaries

The saved pro source is 35 A PA with four HR/seven K and 15 AA PA with no HR/three
K. With 50 observations and the 1200-PA prior, production supplies roughly 4%
of the initial pool. No MLB quality is invented. New-summary effects are zero,
and old coefficient changes lower direct +0.688 to +0.654. Age adds +0.699986
to the residual; its −0.585066 intercept and other terms offset much of that.
Removing minor evidence lowers the fitted rate −0.285455.

Expected 10.18 PA versus 489 actual and actual +5.150 hitting give just 0.0429
value versus 5.724 actual. Support is 2538/561, not a count of equally fast
college-to-MLB stars. Brooks Lee 2022 and DeLauter 2023 do not appear next year;
Zunino 2012 later has 193 PA and −1.442 hitting. Rapid arrival and tiny-sample
talent remain unresolved; this does not justify restarting closed opportunity
experiments or collecting more college history against the user's instruction.

## Masataka Yoshida becomes more optimistic despite the later decline

His 2024/2023 MLB seasons have 421/580 PA and ten/15 HR, with 885 weighted
MLB PA, 304.8 weighted NPB PA and eight AAA PA. Annual quality +0.370/+0.356
and pooled +0.531 are genuinely positive. They contribute +0.133678 while old
changes subtract −0.092743, moving +1.322 to +1.363 versus actual −0.444.
Removing foreign evidence lowers the fit −0.893592, minor evidence just −0.001625.

Expected 476.2 PA versus 205 actual gives 2.569 value versus 0.489 actual and
1.746 incumbent. Positive MLB history has not corrected the foreign optimism.
Support is only 4/3. Aoki 2012 and Suzuki 2022 later hit +0.661 and +1.997;
Brosseau 2023 does not appear. This is an important opposite case to Suzuki's
gain, with both workload and hitting contributing to the miss.

## Jung Hoo Lee improves rate but worsens delivered error

His first MLB year has 158 PA, two HR and 13 K, alongside 685.8 weighted KBO PA.
Latest quality is −0.133, shrunk from −1.144 unshrunk batting per 600. New terms
lower the rate −0.039199 and old changes −0.056834, moving +1.407 to +1.311,
closer to actual +0.463. Removing foreign production changes the fit −1.924956;
the improved MLB representation does not establish the correct KBO translation.

Expected 153.6 PA versus 617 actual yields 0.816 versus 2.403 actual, farther
than direct 0.840 though better than incumbent 0.314. Hitting overprediction
previously concealed more of the PA shortfall. Joint support is 3/0. Ha-Seong
Kim 2021 later hits +0.193; Hwang and Hyun Soo Kim 2017 do not appear. No
active exact-profile examples means coordinate ranges alone cannot validate this estimate.

## Seiya Suzuki before entry remains a separate source addition

His three NPB years supply 1,659 raw PA, 1,311.4 weighted PA and 52.2% production
share after the prior. There is no MLB history and no incumbent forecast. All new
summary effects are zero; relearning other coefficients lowers direct +3.591
to +3.375. The baseline is +3.921 and residual −0.545772, including intercept
−0.250184. Removing foreign evidence changes the fit −4.101192 to about −0.726,
an artificial fallback, not a validated MLB entry forecast.

Actual next-year hitting is +1.175. Expected 191.5 PA versus 446 actual produces
1.677 value versus 2.271 actual, worse than direct 1.746 despite better rate.
Joint support is 2/0. Rosario 2015, Nakajima 2012 and Meneses 2020 all fail to
appear in the next year; they are not excluded. This sparse addition cannot be
treated as matched incumbent evidence or as proof that all foreign professionals are identical.

## Ty France is an ordinary delivered success with opposing errors

In 2018 France has 479 AA PA, 17 HR, 70 K, 31 unintentional walks and 25 HBP,
plus 110 AAA PA, five HR, 19 K, 13 walks and two HBP. Earlier 2017 AA/A+ and
2016 A/A+ records remain. The older HBP totals are 15/12 and 16/12 respectively;
the source is not just power and strikeouts. No MLB source exists, so the four
new terms are zero. Relearning old coefficients lowers direct +0.03750 by
−0.06236. Baseline −0.964989 plus residual +0.940129 gives restored −0.024860.

The residual includes intercept −0.242026, age +0.467147, draft-known +0.145141,
pooled AA PA +0.141152, unknown draft class −0.138119 and other saved terms.
Removing minor evidence raises the fit +0.831437. Actual next-year eight-event
counts are [93 other outcomes, 49 K, 9 unintentional walks, 7 HBP, 27 singles,
8 doubles, 1 triple, 7 HR], totaling 201 PA and −1.059985 hitting. Expected
87.00855 PA and −0.02486 hitting yield 0.264384 value versus 0.263992 actual.
The hitting error contributes about +0.1501 value and workload error −0.1497;
the almost exact final number is cancellation, not accurate subcomponents.

Support is 1444/326. The outcome-blind earlier peers Jett Bandy 2013, César
Puello 2014 and Phil Pohl 2014 all have zero next-year MLB PA. This ordinary
example must not certify talent or opportunity merely because the total is close.

## What the completed checks establish

These walks account for the actual new terms and other coefficient changes,
not speculative explanations attached to names. All original sixteen cases
remain, failures included. They show useful partial recovery, correlated
coefficient reallocations, remaining foreign adaptation gaps, insufficient active
support in important profiles and repeated talent/workload error cancellation.
No data bug is established merely by a surprising player result. No physical
rate violations or newly restored-feature range warnings arise in these cases;
joint and legacy feature qualifications still matter.

The declared primary comparison fails on delivered error versus the incumbent.
Do not adopt this fit, cherry-pick a cohort blend, reopen 2026 or equate this
next-year batting test with full player value. A source audit of the remaining
removed separate MLB event rates is the next bounded task, followed by a new
prospective contract only if that audit supports it.

Full raw counts, references, fold provenance, transformed inputs, every feature
effect, unchanged PA, actual outcomes, support, probes and failed peers are in
`reports/generated/hitter-mlb-detail-restoration/player-walks.json`; durable
machine evidence is in `reports/model-evidence/hitter-mlb-detail-restoration/report.json`.
