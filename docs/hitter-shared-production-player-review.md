# Player review of the shared production test

2026-10-05. Ten player forecasts have been traced from archived statistics to
shared inputs, exact fitted coefficients, fixed PA and observed next-year MLB
results. Seven were chosen before fitting. Judge also supplies the largest
delivered-value deterioration and false low; Perdomo the largest gain, Tatis the
false high, and Wilkerson the closest ordinary delivered-value prediction.
Outcome-selected examples explain the experiment, not independent confirmation.

## Forecasts and actual results

Hitting is batting wins per 600 PA relative to the target year's MLB environment.
The original model's expected PA are fixed; Suzuki has no original forecast and
uses the separately declared research opportunity reference. Delivered value is
batting plus replacement, not full WAR. No PA means no observed hitting rate.

| Player and origin | Old hitting | Shared hitting | Actual hitting | Fixed expected PA | Actual PA |
| --- | ---: | ---: | ---: | ---: | ---: |
| Yordan Alvarez 2018 | +0.455 | +0.169 | +5.648 | 72.2 | 369 |
| Aaron Judge 2016 | +0.264 | −0.010 | +5.330 | 309.9 | 678 |
| Nick Kurtz 2024 | +1.024 | +0.366 | +5.150 | 10.2 | 489 |
| Seiya Suzuki 2021 | No forecast | −0.896 | +1.175 | 191.5 | 446 |
| Jung Hoo Lee 2024 | −0.646 | −0.557 | +0.463 | 153.6 | 617 |
| Masataka Yoshida 2024 | +0.327 | +0.485 | −0.444 | 476.2 | 205 |
| Kevin Maitan 2017 | −0.380 | +0.134 | Unobserved | 2.0 | 0 |
| Geraldo Perdomo 2024 | −0.933 | −0.721 | +2.728 | 472.6 | 720 |
| Fernando Tatis Jr. 2021 | +2.919 | +3.096 | Unobserved | 553.0 | 0 |
| Stevie Wilkerson 2018 | −1.289 | −1.192 | −1.650 | 109.5 | 361 |

## What actually drives the cases

Alvarez's 2018 AA 190 PA with 12 HR and AAA 189 PA with eight HR are retained;
old DSL is only 34.2 weighted PA. The fitted eight event terms contribute just
+0.013. Removing all minor production and its exposure controls raises hitting
by 0.112 in the unchanged model. That probe is artificial, not a recommendation
to ignore his stats. It establishes that the new shared representation does
not recognize his strong production better. His full/active profile has
1398/318 people, but broad profile counts do not certify an Alvarez analogue.

Judge's AAA 410 PA, 19 HR and 98 K coexist with his MLB 95 PA, four HR and 42 K.
His shared event terms contribute +0.126, but changing the representation also
refits every retained coefficient and the intercept. His forecast falls from
+0.264 to −0.010. Delivered value falls from 1.093 to 0.951 before actual 8.115.
This is the largest deterioration; merely retaining more minor mass did not
solve his brief-debut forecast. Full/active profile support is 219/181 people.

Kurtz's A 35 PA with four HR, ten UBB and seven K plus AA 15 PA with two UBB
and three K supply only 4% of the prior-plus-data profile. Event terms contribute
+0.037; age contributes +0.578 and being currently listed +0.198. Other retained
terms and the intercept complete +0.366. His previously useful unattenuated
translation profile was replaced, so this is not an isolated test of adding a
new source. Hitting and opportunity remain seriously low. Broad 2538/561 support
does not contradict the earlier finding of only one active matching fresh-college
job analogue. Brooks Lee, Clint Frazier and Zunino emerge from the specified
origin-known distance; their next-year PA are 0, 142 and 193, not full seasons.

Suzuki's 1311.4 normalized weighted NPB PA and 13 mover people survive the source
join. The constructed historical event value is +0.937, not a forecast, while
the fitted shared event terms contribute only +0.078. The model also retains
an intercept −0.378, incomplete-list scouting sentinels and missing draft
context; for example, the old rank sentinel at lag two contributes −0.182.
These are retained source encodings, not a newly established missing-rank bug.
Removing foreign mass changes the prediction by only +0.010. Exact full/active
profile support is four/two. Broad US comparisons in the first receipt are not
foreign-professional analogues: the appended qualification instead finds Rainel
Rosario, Hwang and Nakajima, with next-year MLB PA 0, 57 and 0. They are imperfect
age/league/quality matches, not evidence Suzuki should have been assigned zero.

Lee's 158 MLB PA and 685.8 weighted KBO PA produce a modest improvement. Removing
foreign mass lowers the unchanged-model forecast by 0.088. His observed +0.463
remains higher, and the fixed 154 PA are far below 617. Exact full/active support
is twelve/two. Foreign-aware comparisons include Ha-Seong Kim, Nishioka and
Brandon Allen; their next-year PA are 582, 14 and 0. Yoshida's newer MLB 421/580
PA and old NPB 304.8 weighted PA are appropriately ordered, but his hitting
forecast rises away from actual −0.444. Foreign removal lowers it by 0.037.
Retained pooled MLB quality contributes +0.350. Exact support is five/four;
foreign-aware comparisons Aoki, Kang and Tsutsugo show very different outcomes.
Neither case supports a blanket foreign boost.

Maitan's rookie 176 PA, 49 K and two HR lower the fitted forecast relative to a
source-removal probe, but the refitted age/scouting/context baseline still raises
his hitting above the incumbent. Exact full/active support is 2682/three. He
has no next-year MLB PA: delivered value rises slightly from 0.0049 to 0.0066,
but there is no observed hitting rate to validate either forecast. Origin-known
comparisons include Devers, who also has zero MLB PA the following year. This
one-year test cannot establish that either player lacks eventual MLB talent.

Perdomo's recent MLB 388/495/500 PA, three/six/five HR and 58/86/103 K produce
the largest gain, but hitting −0.721 and expected 473 PA remain far below actual
+2.728 and 720. Delivered value rises 0.741 to 0.908 before actual 5.522. His
small minor sample has only a −0.004 removal effect; this is chiefly changed
MLB representation, not a minor-source triumph. Tatis's 2021 546 PA and 42 HR
support high conditional talent, but his following zero PA give no hitting
label. Increasing his hitting at unchanged expected 553 PA worsens delivered
value from 4.423 to 4.587. Later absence must not be interpreted as zero talent.

Wilkerson's MLB debut is 49 PA with 16 K and no HR, alongside AAA 86 PA with
four HR and older AA/Aplus work. Minor removal raises hitting by 0.159. His
delivered forecast 0.120 almost equals actual 0.119, yet expected PA are only
110 versus 361 and hitting is too optimistic. Opposing errors cancel; this is
not a successful prediction of both components. Origin-known comparisons Garver,
Muno and Barnes yield 335, zero and 262 subsequent MLB PA.

## What the direction checks do and do not prove

All 105 fitted heads give a positive partial contrast for HR replacing other
outs. Ninety-five give a positive K-versus-other contrast, triggering review.
This is not automatically a baseball impossibility: both events have zero
immediate value in the target, and replacing a batted out with K while holding
hits fixed changes implied BABIP. These coefficients also condition on existing
MLB quality and tracking. Do not impose a new sign constraint simply because
of this alert or claim that a standalone coefficient is a causal effect.

The important measured fact is that shared event terms still contribute little
for the no-MLB cases even though they no longer require seven sparse foreign
slopes. A plausible design explanation is that retained MLB quality summaries
absorb production, leaving residual event relationships that do not transfer as
a complete talent relationship to players without MLB quality. That is a
hypothesis for a separately contracted baseline design, not a demonstrated fix.
Selected-mover translation, sample-prior strength and context effects also
remain unresolved; no loss is attributed entirely to one coefficient family.

The machine receipts preserve full source histories, every fitted term, removal
probes, exact support, comparison selection and both favorable and unfavorable
outcomes. The walkthrough is complete. The candidate is not adopted because
it worsens matched historical hitting and delivered value, not because minor
or international production has been shown useless.
