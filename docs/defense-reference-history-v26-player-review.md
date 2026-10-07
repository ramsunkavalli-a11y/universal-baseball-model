# Outfield defense correction and player review

The correction removes a misleading position penalty from sparse center-field
history and an artificial bonus from sparse corner history. It helps the
measured MLB group, but does not yet identify defensive prospects or forecast
development and role changes well. The following are calculations from fixed
historical forecasts, not player overrides or a new deployed model.

## What each number measures

An origin of 2022 uses only 2020–2022 evidence. Later quality pools 2023–2025
MLB range at the stated position; it requires 1,500 measured outs across two
seasons with no missing positive same-position exposure. Delivered defense is
the separate following-year sum of twelve defined components. Expanded value
adds fixed batting and position contributions, using ten runs per win. It is
not full WAR. Incomplete or unmeasured quality remains unknown, not bad talent.

Annual observations first subtract the held-player-excluding seasonal position
reference. The latest three seasons have weights 1, 0.5 and 0.25. If weighted
centered runs are R and weighted defensive outs N, the corrected relative
forecast is 1,500R/(N+3,000). Raw talent and position-relative contribution remain
separate. The old comparator shrank raw runs and then subtracted the origin
reference; that gave sparse records a large position offset despite little
evidence. Neutral below means zero OF quality, not zero catcher/infield/arm skill.

All sixteen selected groups, their 64 player records, annual observations,
intermediate calculations and 428 raw minor splits are preserved in
[the calculation record](../reports/model-evidence/defense-reference-history-v26/player-walks.json.gz).
The independent source review also checks 582 annual position records. Minor
counts show what was available, but do not enter this MLB-history-only correction.

## Fixed players and their comparisons

The first eight focal players and three peers each were fixed before scoring.
Peers use only origin stage, role, age and exposure. Quality diagnostics use
same-position age and history exposure; a catcher with a tiny LF stint can
therefore be selected. Such comparisons are not evidence of comparable overall
athletic profiles. Full annual paths and missing measurements remain visible.

### Mike Trout and sparse corner records

Trout's 2020–2022 CF observations are −1.112, +0.938 and +2.686 raw runs over
1,363, 885 and 2,813 outs. After seasonal references and recency, N=3,596.25,
R=−1.7826 and reliability is 54.5%. His relative forecast moves −1.242 to
−0.405 runs per 500 innings; the later measured rate is −0.273 over 2,652 CF
outs. The 2025 RF move is recorded separately, not added to the CF quality label.
Following-year defense improves −2.836 to −1.311 against +0.742 actual, yet
expanded value worsens 3.136 to 3.289 against 2.785 because other forecasts
already overshoot. Better defense alone need not improve total value.

Enrique Hernández's 24 weighted LF outs have only 0.79% reliability. The old
relative +0.914 becomes +0.020, a sensible near-prior estimate. His CF forecast
instead rises −0.527 to +0.407 from genuine positive CF history. Odúbel Herrera
has no later MLB fielding: quality remains unknown, but raising delivered
defense −0.215 to +0.070 worsens total value when actual participation is zero.
Adam Engel has only 63 measured later CF outs and three unmeasured LF outs;
his following-year total is unknown, not a convenient zero error.

### Ian Happ and corner-field decline

Happ's weighted LF raw runs +1.7527 become +5.2560 centered runs over 4,434.5
weighted outs, with 59.6% reliability. His relative LF rate falls +1.533 to
+1.060; actual three-year rate is +0.347. Annual relative LF runs are −2.848,
+2.769 and +2.761, so the result is not a uniform decline. His delivered defense
falls +2.116 to +1.417 against −0.647, but expanded value falls 2.257 to 2.187
against 2.959 because batting/workload underprediction dominates.

Randy Arozarena's LF rate +0.722 to +0.081 is closer to −0.708 later actual.
Andrew Benintendi +1.289 to +0.743 is also closer, but still misses −2.551.
Tyler O'Neill +2.335 to +1.809 remains far above −0.138. His CF/RF moves and
reduced exposure stay separate; centering is not an aging or health model.

### Juan Soto and a position move

Soto's 5,766.25 weighted RF outs yield raw −9.6083 and centered −6.8262 runs.
With 65.8% reliability, RF quality moves −0.910 to −1.168, closer to −1.677
over the later RF seasons. Sparse LF history moves +1.194 to −0.125 versus
−0.801 later. However the 2023 exposure forecast assigns 3,351 RF outs; he
actually plays 4,035 LF outs. Delivered defense −4.383 to −4.959 worsens versus
−0.736. Correcting quality does not repair the role forecast.

Cal Mitchell's 27 later RF outs lack a valid range value, leaving quality and
delivered totals unknown. Oswaldo Cabrera's extensive minor infield record is
available, but small MLB position records and several later missing stints
prevent an all-component delivered label. Andrew Vaughn is forecast substantial
LF/RF exposure but actually moves to 3,688 first-base outs in 2023. Old total
defense −3.018 happened to match −3.024 actual; corrected −3.776 worsens it.
That coincidence is not evidence the old outfield assumption was correct.

### Cody Bellinger and cross-position talent

Bellinger's CF N=4,932.75 and centered R=+1.8951 give +0.358 relative quality,
up from −0.294. Later CF rate is −1.747, so quality worsens. Following-year
defense improves −0.548 to +0.548 versus +2.369, because he also contributes
at first base; the model projects only 82 first-base outs versus 1,265 actual.
The same player can improve delivery while worsening the conditional CF target.

Lane Thomas's CF −1.843 to −0.647 moves away from later −2.557, while his
future RF quality is unmeasured because of an 18-out missing stint. Jose Siri's
CF +1.560 to +2.536 is closer to +3.717. Jake Meyers +0.680 to +1.886 is closer
to +2.812. Both latter cases still have following-year workload underprediction.

### Nick Castellanos and older right fielders

Castellanos's 2020–2022 RF runs −3.010, −6.193 and −9.061 become weighted
relative −9.7336 over 5,062.75 outs. His rate moves −1.463 to −1.811 versus
−2.027 later, with 62.8% reliability. Delivered defense improves −3.927 to
−4.592 against −6.142, but expanded value falls 1.153 to 1.086 against 1.736.
Actual 671 PA exceed projected 501; the correction cannot supply that workload.

Hunter Renfroe's RF +0.343 to +0.020 is closer to −1.395 later. Randal Grichuk
+1.070 to +0.572 is closer to −1.793, but remains optimistic. Hunter Dozier's
third-base history is unchanged; tiny later OF exposure and a missing LF value
leave the integrated outcome unknown. No nonarrival is reclassified as poor skill.

### Ceddanne Rafaela before and after MLB evidence

At the 2022 origin Rafaela has no measured MLB range. His 2022 minor record
includes 1,496 AA and 835 High-A CF outs, plus shortstop use; it does not enter
this candidate's quality estimate. Legacy CF reference accounting produces
−0.621 projected defensive runs despite no quality history. Corrected contribution
is zero, explicitly unknown talent. Actual 2023 defense is +0.223. The later
CF annual relative runs +0.959, +2.193 and +14.419 demonstrate an eventual
strong defender that this prior did not identify in advance.

Johan Rojas likewise has no origin MLB history and later positive CF evidence
(annual relative +2.808, +3.415, +3.116). Jorge Barrosa has no 2023 participation
and only small later measured samples; Diego Hernandez has no later MLB fielding.
All receive unknown-quality priors. Removing their artificial CF penalty is
not proof of a minor-league defensive forecast.

### Bobby Witt Jr and unchanged infield development

Witt's rookie SS −6.884 runs over 2,477 outs are shrunk to −1.885 per 500
innings. The correction leaves this unchanged. Later annual SS runs are +9.756,
+11.357 and +18.165, pooled +4.893 per 500 innings. Delivered defense remains
−3.718 versus +9.756 actual in 2023. This large miss stays open; it cannot be
credited to an outfield repair or assumed unpredictable without further evidence.

Geraldo Perdomo −0.089 versus +0.596 later SS quality also remains unchanged.
Luis García Jr's second-base −0.976 versus −0.730 later is fairly close, but the
exposure forecast incorrectly retains 1,907 SS outs when he plays second base.
Livan Soto has only 45 measured future SS outs and six missing outs; quality
is unknown and projected 303 PA versus 12 actual remains a workload failure.

### Willson Contreras and catcher controls

Contreras's measured catcher components are unchanged: projected +0.354
defensive runs versus −4.114 actual in 2023. PA is close (494 versus 495),
so this is not just workload. His later first-base move is recorded rather
than treated as future catching evidence. Omar Narváez +2.726 versus +0.073,
Christian Bethancourt +0.751 versus −1.867 and Andrew Knapp −0.410 versus
zero delivered runs also remain unchanged. Knapp has no 2023 participation;
his 51 catcher outs in 2024 do not retroactively change that delivery label.
Catcher improvement is not claimed by this test.

## Outcome selected quality cases

These examples diagnose exposed development results, not independent validation.
Same-position peers were chosen using only origin age and history exposure.

| Case at 2022 origin | Weighted outs and centered runs | Reliability | Old rate | Corrected rate | Later measured rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Michael Siani CF largest gain and false low | 190 and −0.1979 | 6.0% | −1.876 | −0.093 | +5.293 |
| Jo Adell CF largest loss | 24 and −0.0761 | 0.8% | −1.921 | −0.038 | −6.566 |
| Alec Burleson RF false high | 183 and −0.2538 | 5.7% | +0.585 | −0.120 | −6.694 |
| Will Benson LF median error | 96 and −0.2029 | 3.1% | +0.780 | −0.098 | −1.843 |

Siani's 2024 CF +9.314 relative runs over 2,515 outs drive the gain, but the
corrected mean remains far below his later skill. His peers show why a generic
young-CF boost would be unsound: Jihwan Bae and Jarred Kelenic have insufficient
later CF exposure, while Alek Thomas's +0.754 correction is worse against
−1.418 later. Kelenic's later LF quality also remains unknown due to missing outs.

Adell's CF history is just a recency-weighted 2020 stint. His later CF rate is
dominated by 2025's 2,172 outs and −10.391 relative runs. The correction's
near-neutral prior therefore worsens the miss. Esteury Ruiz's CF −0.087 is
closer than −1.819 to later −0.801; Símon Muzziotti has no later MLB fielding.
Fernando Tatis Jr has almost no later CF but +3.317 later RF quality versus
corrected −0.192. His inherited 2023 exposure forecast of only 40 PA and SS
use is plainly inadequate, reflecting the known interruption/role problem.
No suspension repair was made in this defense-only comparison.

Burleson's bad later RF result persists across all three annual relative run
totals (−1.718, −5.060, −2.241), not one anomalous inning. His sparse raw history
cannot identify that weakness. His peers are Gilberto Celestino (no later MLB),
Tatis and Ruiz; the latter two have insufficient same-position comparison
evidence or very different later skill. This is not a supported talent prior
for all young right fielders.

Benson is selected for median absolute error, not because the prediction is
especially accurate. His later LF runs are consistently negative, while RF is
positive overall. Will Brennan moves predominantly to RF, with +1.647 later
quality; Travis Swaggerty has no later MLB fielding. William Contreras's tiny
LF stint makes him an origin age/exposure peer but his real career is catching:
the OF change barely alters his forecast, and unchanged catcher defense misses
−4.387 projected versus +10.047 actual in 2023. Position-selected sparse peers
are a weak athletic comparison even when the selection rule is reproducible.

## Outcome selected delivered value cases

At the 2024 origin, Rafaela's CF raw +5.383 becomes centered +2.536 over
2,069 weighted outs. CF rate rises −0.437 to +0.750. Defense improves −2.154
to −0.762 against +16.680 in 2025, the largest delivered-defense gain, but
still misses badly. The exposure forecast retains 1,456 SS outs and only
1,764 CF outs; actual is zero SS and 3,502 CF. Rojas improves defense +1.468
to +2.902 against +4.490, but total value worsens with overpredicted PA. Michael
Harris II +0.779 to +2.267 defense moves away from +0.577 actual. Andy Pages
−1.871 to −0.802 is closer to +8.787 but still underestimates the breakout.
Their three-year quality windows remain incomplete; one-year delivery is not
a substitute mature talent label.

Hernández at 2022 is the largest delivered-defense loss: −0.950 becomes +0.525
versus −13.516 actual. The model expects mostly CF, but the next year contains
1,653 SS outs and −9.313 SS runs. The correction worsens a role/skill miss;
it is not a coding reversal. His peers Trout, Aaron Judge and Herrera include
both improvement and exit. Judge's CF estimate −1.484 to −0.481 is worse
against later −3.557, yet expanded 2023 value 4.423 to 4.474 is closer to 4.482.
Batting and other-channel errors can offset a bad defensive rate.

Jackson Chourio at 2023 is the largest expanded-value gain: removing an unknown
CF prior penalty lifts defense −2.322 to zero and value 0.663 to 0.895 against
3.294 actual in 2024. The model expects CF but he plays LF/RF. Peers Roman
Anthony and David Calabrese do not play MLB in 2024; raising their value moves
away from zero. James Wood plays LF with negative range instead of projected
CF/RF; zero defense is worse than −0.610 against −3.274 actual, although total
value improves because the batting/workload forecast is low. The gain is not
new advance identification of Chourio's defense.

Luis Robert Jr at 2023 is the largest expanded-value loss. His CF weighted
raw +13.089 becomes relative +6.098 over 5,227 outs, 63.5% reliability. CF rate
rises +0.409 to +1.112, defense +1.426 to +2.944 versus −3.261 actual, and
value 3.071 to 3.223 versus 0.200. Projected 532 PA versus 425 and high batting
also contribute. Later relative CF runs reverse from −2.017 in 2024 to +2.525
in 2025, so this is not proof of permanent defensive decline. Brandon Marsh
and Jazz Chisholm Jr improve delivered defense, but their projected CF roles
do not match later LF or infield use. Lars Nootbaar's +0.761 to +1.452 defense
worsens against −1.162; the history/position estimates remain imperfect.

## Judgment and next action

The correction has a defensible mechanism and a positive measured-MLB quality
result, with real individual losses retained. Keep it as the position-consistent
research history baseline, not a full defense or WAR deployment. Unknown
prospects remain unknown; age/development and cross-position selection still
matter. The fixed tests do not compare against a freshly trained, properly
centered age model. Earlier calibrated raw forecasts cannot be relabeled as
that comparison.

The totals diagnostic locates significant unchanged first-base and catcher
misses. Before another learner, reconcile each component's reference, missing
exposure and opportunity definition. Do not force complete-subset totals to
zero or tune priors to these named outcomes. Then use compatible older MLB
quality to support a longer-horizon minor-to-MLB talent test. No frozen forecast,
explorer or 2026 model-selection state changes here.
