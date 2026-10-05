# Count errors: hitting versus playing time in actual players

2026-10-05. All thirteen cases from the completed comparison are retained. This
adds exact error explanations to the already replayed raw-count, level/reference,
prior, fitted-logit, source-removal and origin-selected production-peer walks in
[the count player review](hitter-count-baseline-player-review.md). It does not
refit a model, replace peers after viewing outcomes or reopen 2026.

The machine-readable cases retain row IDs, origins, routes and selection reasons
and hash-link the original detailed walks. Judge 2016 remains the largest false
low; Tatis 2021 the largest false high; Judge 2023 and Khris Davis 2018 the largest
gain and harm; Misner the ordinary case. These outcome-selected cases explain
errors; the full-cohort results, not the anecdotes, decide the experiment.

Below, H is hitting-rate error at the unchanged expected PA; O is workload error
valued at actual batting. H + O equals delivered-value error for active players.
Units are batting-plus-replacement wins, **not full WAR**. A dash for a non-arrival
means no observed hitting rate, not zero talent. The three-decimal display is
rounded; stored identities use full precision.

| Player and origin | Incumbent H | Count H | Unchanged O | Reading |
| --- | ---: | ---: | ---: | --- |
| Yordan Alvarez 2018 | −0.625 | −0.621 | −3.708 | Tiny hitting gain; large workload miss remains |
| Aaron Judge 2016 | −2.617 | −2.842 | −4.405 | Hitting and workload both too low |
| Nick Kurtz 2024 | −0.070 | −0.078 | −5.605 | Very low expected PA dominates |
| Seiya Suzuki 2021 | — | +0.744 | −1.296 | Addition: optimistic hitting hides low PA |
| Jung Hoo Lee 2024 | −0.284 | +0.159 | −1.805 | Closer hitting, still low workload |
| Masataka Yoshida 2024 | +0.612 | +1.195 | +0.646 | Both errors point high |
| Kevin Maitan 2017 | — | — | — | Non-arrival: no hitting label |
| Geraldo Perdomo 2024 | −2.884 | −2.630 | −1.897 | Partial gain, breakout still missed |
| Fernando Tatis Jr. 2021 | — | — | — | Non-arrival: expected value gets worse |
| Stevie Wilkerson 2018 | +0.066 | +0.055 | −0.083 | Better hitting removes lucky cancellation |
| Aaron Judge 2023 | −3.269 | −2.772 | −2.636 | Genuine hitting improvement, still low |
| Khris Davis 2018 | +3.633 | +4.691 | +0.022 | Almost entirely hitting deterioration |
| Kameron Misner 2024 | +0.026 | −0.032 | +0.034 | Delivered gain hides worse squared hitting error |

## Eight focal explanations

**Judge 2016.** Known evidence is 95 MLB PA with four HR and 42 K plus 410
current AAA PA with 19 HR and 98 K, and earlier AA/A. The translated/shrunk
starting hitting rate −0.726 becomes −0.171, below incumbent +0.264; actual
2017 is +5.330, 52 HR and 678 PA. The held fit predicts HR 3.65% and K 31.35%
versus actual 7.67% and 30.68%. Thus the model recognizes strikeouts but misses
damage and walks. At 309.9 expected PA, H worsens by 0.225 and interacts with a
large low-workload error: delivered squared error rises 3.20973. Count rate-error
contributions from HR and unintentional walks are −3.682 and −2.823 per 600 PA.
The saved source-removal probe and weak production peers remain relevant; this
is not a 57-PA DSL glitch or evidence that all similar prospects should be Judges.

**Judge 2023.** Three MLB seasons with 37/62/39 HR and 458/696/633 PA supply
clear production; no recent minor/foreign counts are involved. Baseline +2.757
becomes +4.455, above old +3.899 but below actual +7.558. HR 7.76% is near actual
8.24%, and the saved common-profile/tracking contrasts raise HR versus other.
H improves by 0.497 and delivered squared error falls 5.61727. Walks, singles
and doubles remain low. Production peers include later declines; this genuine
gain does not certify a post-result superstar branch or all established players.

**Khris Davis 2018.** His 610/652/654 MLB PA and 42/43/48 HR contain no recent
minor/foreign source to blame. The +1.428 baseline becomes +3.395, versus old
+2.288 and actual −1.518. Forecast HR 7.60% exceeds actual 4.32%; the saved common
HR correction strengthens an already powerful past profile. Expected PA 572.8
is relatively close to actual 533. Delivered squared error rises 8.84607, of
which 8.79987 is the hitting-squared term. HR contributes +3.916 per 600 to count
rate error, doubles +1.489, partly offset by singles −1.477. This is a plausible
decline the model failed to anticipate, not evidence of an origin-known injury
or a reason to discard valid old homer counts.

**Kurtz 2024.** There are only 50 professional PA: 35 A (four HR) and 15 AA
(zero HR), alongside cutoff-known draft/scouting information. The shared prior
makes production 4% of the initial pool; +0.238 becomes +0.576, below old +1.024.
Actual hitting is +5.150. At just 10.2 expected PA versus 489 actual, the hitting
change affects little expected value, but the workload interaction amplifies the
loss. HR error is −3.775 per 600. The prior production peers include no-arrivals;
this exceptional rapid ascent does not justify a universal first-year PA boost.
No school-data, pedigree or opportunity rerun follows from this diagnosis.

**Suzuki 2021.** His 1,659 NPB PA across 2019–21 contribute 1,311.4 recency-weighted
PA and 52.2% of the pooled mass. A local-dominance starting rate +3.921 becomes
+3.505, versus actual +1.175; it is not an established MLB equivalency. HR 5.59%
exceeds actual 3.14%, and walks are also high. This is a source addition with no
incumbent. The supplemental count-only decomposition shows H +0.744 and O −1.296:
value 1.719 versus actual 2.271 benefits from opposing errors at 191.5 expected
PA versus 446 actual. The saved fit's NPB-share HR correction is tiny relative
to the imposed penalty; active never-debut NPB support is only two people.
Neither the delivered cancellation nor turning the penalty off is validation.

**Lee 2024.** Current MLB evidence is 158 PA (two HR, 13 K) alongside 685.8
weighted KBO PA. Baseline +1.840 becomes +1.083, versus old −0.646 and actual
+0.463. The foreign-removal probe confirms that Korean production drives this
correction, not a change in jobs. At 153.6 expected PA versus 617, H moves from
−0.284 to +0.159 while O stays −1.805. Delivered squared error falls 1.65276;
most of that change is the interaction (−1.59730), not the hitting-squared term
(−0.05545). HR remains too high (2.78% versus 1.30%); actual twelve triples also
matter. A positive Lee example is not a calibrated KBO population result.

**Yoshida 2024.** Two MLB seasons supply 885 weighted PA; eight AAA PA are
negligible. NPB contributes 304.8 weighted PA, 12.7% of the pool, yet its local
dominance still lifts the baseline to +1.597. Fitted +1.061 exceeds old +0.327
and actual −0.444. The saved foreign-removal probe changes hitting by −0.777;
removing AAA changes only about −0.005. H and O are both high at 476.2 expected
PA versus 205 actual; delivered squared error rises 1.80674. Even relatively
close HR (2.63% versus 1.95%) does not validate the total rate: walks contribute
+0.920 per 600 to its error. The NPB-share coefficient is weakly supported and
heavily penalized. This diagnoses a context-transfer limitation, not old minors
dominating an established MLB hitter.

**Misner 2024.** Fifteen MLB PA with ten K coexist with two 519-PA AAA seasons
with 17/21 HR and a 510-PA AA season. Baseline −0.733 becomes −2.250 versus old
−1.840 and actual −2.026. The fitted K probability 37.51% exceeds actual 31.80%.
At 84.5 expected PA versus 217, the new H slightly overshoots low while O is high.
Delivered squared error improves 0.00356 even though the hitting-squared term
worsens 0.00031. The saved production-aware peers, rather than a demographic
pitcher analogue, are used. A nearly exact delivered forecast can still have
incorrect ingredients; do not declare this row an unqualified success.

## Five retained counterexamples and limits

Yordan's 379 current AA/AAA PA with 20 HR produce only a tiny change; earlier
57 DSL PA contribute 34.2 weighted PA, not dominant evidence. The large next-year
workload error remains. Perdomo's multi-season MLB low-power record has little
minor evidence; improved hitting still misses a later MLB breakout. Wilkerson's
mixed MLB/AAA/AA history moves hitting closer while delivered accuracy worsens
because the incumbent benefited from cancellation. Maitan's 176 rookie PA with
two HR do not create an observed next-year hitting label. Tatis's 546 current
MLB PA with 42 HR make high conditional talent plausible, but his actual next-year
absence makes delivered error worse; future absence cannot retroactively become
a preseason zero-talent target. Their unchanged detailed stats, source mechanics,
support and unsuccessful peers remain in the original thirteen-walk package.

This review is complete. It reinforces the rejection of the fixed count
replacement, not a rejection of count data, minor/foreign histories or all event
models. Cohort loss is broad enough that an overseas-only or famous-player fix
is insufficient. The next bounded comparison must isolate learning future
batting value on identical past inputs, with the incumbent kept as an anchor.
