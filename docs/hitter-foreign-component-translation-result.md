# Overseas hitting evidence is connected but the first adjustment loses important skills

2026-10-04. The Japan and Korea histories now have chronological, player-separated
component profiles ready for the hitter pipeline. The first fitted adjustment
is not approved as a replacement for batting talent. It compresses important
contact and power differences in several consequential player checks. Preserve
the source counts and both successful and failed cases; do not declare that
overseas information is useless because this particular adjustment is too blunt.

## What changed

The [pre-fit contract](hitter-foreign-component-integration-contract.md) estimates
eight mutually exclusive MLB events from overseas batting history using a small,
regularized forward-mover model. It produces 3,205 profiles for the existing
641 source origins across five outer folds. These are inputs, not 3,205 newly
eligible hitter forecasts. Training rows exclude their own fold as well as the
outer fold, and each row uses completed observations through its own origin.

League references include every reviewed player, not just MLBAM-matched people.
The crosswalk covers 742,456 of 1,287,308 NPB PA and 331,342 of 976,828 KBO PA.
Using only those people to define league average would select the reference
population. Known excluded player folds are subtracted; unmapped identities
cannot receive verified fold assignment and remain an explicit limitation.

The original 63,282 feature rows, 30,506 evaluation forecasts and all non-arrivals
remain unchanged. No new workload head, batting-plus-replacement forecast,
full WAR estimate, explorer update or protected 2026 result was produced.

## What the fitting can establish

There are only 17 qualified direct Japanese and 10 Korean hitter mover people
through 2024. Actual chronological folds have fewer. The adjustment estimates
next-season MLB production conditional on an observed move and enough target
PA, not pure league strength, a job probability or a career outcome. Reverse
movers and AAA bridges were not silently pooled into this selected population.

The ridge penalty pulls component slopes toward zero, while league intercepts
and an origin MLB reference provide the baseline. Thus production differences
can be compressed toward a typical mover profile. Re-centering and softmax
ensure valid event probabilities but do not make that compression appropriate.
The K slope before Lee's 2024 debut is only .215; before Ohtani's debut it is
.079, while the HR slope is .342. Those are fitted mechanics, not independently
validated reliability weights. The predictor uses three observed overseas
seasons; calibration pairs use one source season, another representation limit.

Independent reconstruction verifies every source event, full league reference,
all 1,680 constrained component optima and all 3,205 profiles. Sixteen focused
tests and the unchanged 31-file protected forecast check pass. This establishes
execution integrity, not predictive improvement or model readiness. There is
no new whole-model accuracy score to announce at this input checkpoint.

## Player review

The complete arithmetic walkthrough records actual yearly counts, references,
coefficients, component probabilities, support, saved model intermediates and
outcome-blind comparisons. The percentages below are raw event probabilities
per PA, not WAR. Observed future percentages are descriptive checks, not true
latent talent or evidence that every forecast should equal one realized season.

| Player and projected year | Recent foreign PA | Adjusted K percent | Observed MLB K percent | Adjusted HR percent | Observed MLB HR percent |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ohtani 2018 | 732 | 22.0 | 27.8 | 2.90 | 5.99 |
| Suzuki 2022 | 1,659 | 21.3 | 24.7 | 2.91 | 3.14 |
| Yoshida 2023 | 1,455 | 16.8 | 14.0 | 2.61 | 2.59 |
| Jung Hoo Lee 2024 | 1,558 | 20.8 | 8.2 | 2.82 | 1.27 |
| Ha-Seong Kim 2021 | 1,823 | 23.3 | 23.8 | 3.84 | 2.68 |
| Hyeseong Kim 2025 | 1,754 | 20.7 | 30.6 | 2.04 | 1.76 |
| Park 2016 | 1,749 | 21.4 | 32.8 | 3.41 | 4.92 |
| Thames 2017 | 1,638 | 21.6 | 29.6 | 3.58 | 5.63 |

Ohtani's recency-weighted NPB history has 27.2% K and 4.83% HR. The fit lowers
both to a relatively ordinary MLB profile. His 367 debut-year MLB PA contain
102 K and 22 HR. Eleven Japanese and five Korean training people in his fold
do not certify a comparable two-way/power profile. This is a failure of the
first adjustment's representation, not missing Japanese data. He still has no
original saved forecast row; this checkpoint does not fabricate one.

Suzuki's recency-weighted source has 14.9% K and 5.75% HR. Thirteen Japanese
and six Korean mover people yield 21.3% and 2.91%; his 446 MLB PA show 24.7%
and 3.14%. Power is a reasonable descriptive match, while contact remains too
optimistic. His Japanese profile peers have no following MLB PA. Staying in
Japan does not imply zero hitting talent, and those peers cannot validate an
arrival probability. His original missing forecast remains missing.

Yoshida's low-strikeout source, 6.83% after smoothing and recency weighting,
becomes 16.8%, compared with 14.0% in 580 MLB PA. The adjusted 2.61% HR is close
to 2.59% observed. This is an encouraging contrasting case, not an overall
validation. His same broad support is thirteen Japanese and six Korean people;
no original forecast exists. All three overseas profile peers stay outside MLB.

Jung Hoo Lee's 2024 profile is the clearest contact warning. His recent KBO
history has only 5.88% K, but seven Korean mover people and the shared .215 K
slope lead to 20.8% projected. His first 158 MLB PA have 13 K, or 8.23%. Before
2025, with 1,014 older KBO PA, the foreign-only adjustment remains at 20.4%
against 11.5% observed in 617 MLB PA. The second check is not a full projection:
his 158 MLB PA were deliberately not blended into this foreign component.
They must be retained and appropriately weighted by the main talent model.

Ha-Seong Kim before 2021 has 1,823 KBO PA and four direct Korean training people
in his fold. The adjusted 23.3% K matches 23.8% observed better than his 12.3%
source rate, but HR is too high. Before 2023 only the 622-PA 2020 KBO season
remains in the foreign window. The adjustment yields 22.2% K and 3.42% HR,
versus 19.8% and 2.72% in 626 MLB PA. His two intervening MLB seasons are more
relevant current evidence and are not erased or replaced by this component.

Hyeseong Kim's 1,754 KBO PA contain a recency-weighted 12.4% K and 1.43% HR.
Nine Korean mover people yield 20.7% and 2.04%, against 30.6% and 1.76% in
170 MLB PA. Power is closer than contact. The unchanged current model predicts
only .36 expected MLB PA and -1.033 custom batting wins per 600. This checkpoint
does not repair his opportunity forecast or justify inflating it automatically.

Park's 1,749 KBO PA have 23.4% K and 8.30% HR after weighting/smoothing. Only
one Korean mover person qualifies in his early fold. The translation suppresses
both to 21.4% and 3.41%, while his 244 MLB PA have 32.8% K and 4.92% HR.
Power reduction alone is directionally sensible; compression of strikeouts in
this power/contact profile is not supported by that description. This sparse
case cannot determine a universal Korean adjustment.

Thames before 2017 has 1,638 KBO PA, including 529 PA and 40 HR in 2016. Three
Korean training people give 21.6% K and 3.58% HR, versus 29.6% and 5.63% in
551 MLB PA. The original model still has 20.8 expected PA and -.711 batting
wins per 600. Neither low estimate is corrected yet. His earlier 2015-origin
profile has 1,109 KBO PA and a fitted hypothetical MLB rate, but he stays in
Korea in 2016 and has zero MLB PA: that zero is not an observed hitting rate.
Peers include Kang with substantial MLB play and Navarro with none. Foreign
talent and opportunity cannot be equated.

Tanaka before 2013 has 1,387 recent NPB PA and five Japanese training people.
The adjustment increases K from 8.60% to 16.6%, versus 8.82% in just 34 MLB PA.
His observed zero HR is a tiny sample, not proof of zero power talent. Aoki,
one outcome-blind Japanese profile peer, has 674 MLB PA the following year;
other peers have none. This mixture illustrates why conditional hitting cannot
stand in for arrivals or workload. Fukudome before 2008 lies outside the sealed
preseason input population; his 590 observed MLB PA are shown, but no translated
profile or prediction is fabricated.

Tsutsugo before 2020 has 1,738 NPB PA. The adjustment yields 22.6% K and 3.50%
HR, versus 27.0% and 4.32% in 185 MLB PA. That target is the shortened 2020
season and is descriptive only, not comparable full-season workload evidence
or a primary mover fit. His raw 21.3% source K rises little under this fit.

The earlier ordinary source controls, Aoki and Choo in 2024, remain outside
the 641-input population even though their reviewed source has 129 and 302 PA.
No source-only hitter rate becomes an assumed MLB job. Unmapped source identities
also remain in references without invented forecasts or fuzzy identity matches.
These exclusions are recorded rather than quietly replacing them with famous
successful movers.

## Decision and next action

Keep the complete count/reference construction and chronological input adapter.
Withhold the first affine translation as a replacement talent estimate. It has
some sensible matches, but preserves too little contact/power distinction in
important cases, with sparse historical support. Do not fix named players,
retune the penalty until their outcomes look good, or reject the source itself.

The main pipeline should preserve raw, league-relative production and its
exposure alongside adjustment/support information, rather than receiving only
this compressed point estimate. The end-to-end contract still needs coherent
status and role evidence, qualified additions with real domestic histories,
and a fair comparison with the fixed anchors and public benchmarks. A stable
measurement-error-aware component mapping is a substantive alternative if
needed, not another unlimited parameter sweep. No deployment or broad goal
completion is approved at this checkpoint.
