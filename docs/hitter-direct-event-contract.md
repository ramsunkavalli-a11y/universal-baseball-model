# Direct event conversion for future MLB hitting

2026-10-04. This bounded development check asks whether the already saved
next-year event probabilities predict MLB events and batting contribution better
when converted with defined event values, without another talent regression.
No new model, adjustment, penalty, blend or source is fitted or selected.
The completed shared-event comparison and its 45 player walks are prerequisites.
The incumbent remains the benchmark, not the failed shared regression alone.

## Fixed target and membership

Retain the same 30,506 original forecasts and thirteen separate additions, five
whole-player folds and seven origins. Targets end in 2025; 2020 remains excluded.
Predict next calendar year's MLB batting wins per 600 PA and delivered batting
plus replacement contribution. Non-arrivals have zero contribution and no
observed MLB hitting rate. This does not measure full WAR, career upside,
control years or trade value.

## Exact forecasts

Recover the saved US and combined US plus foreign eight-event probabilities
from each row's own held-fold features and MLB reference. Event order is other,
K, unintentional BB, HBP, 1B, 2B, 3B, HR. Convert directly:
`rate = (predicted_probability - held_origin_MLB_reference) dot event_values
* 600 / (10 * neutral_wOBA_scale)`.
The weights and scale are the existing compatible batting definition, not newly
chosen from results. The prediction assumes a future relative environment like
the origin reference; actual future environment is used only in observed labels.

Apply each direct rate to originally never-debuted players with supported
evidence. Original previously debuted players retain exactly current UBM talent
and all original players retain current probability, conditional PA and expected
PA. The additions retain the previous shared experiment's job forecasts and use
the direct rate when supported. For a missing US profile, the domestic arm keeps
the current rate, or previous shared domestic rate for an addition. A missing
combined profile similarly falls back to current or previous shared foreign.
Missing evidence is not an observed average talent. Persist every application
and fallback flag. The benchmark and fallback are not chosen after scoring.

Delivered contribution is expected PA times `(rate / 600 + replacement_rate)`
using the unchanged comparison table's origin replacement rate. Keep both failed
shared regression arms visible, and do not claim this fixes playing time.

## Source and support checks before scoring

Verify source hashes, prior completed review, exact identities, cutoff and fold
graphs, mutually exclusive future counts, coherent positive probabilities,
feature reconstruction and routing. Use saved domestic translation profiles for
the past-US component anchor; reconstruct addition profiles from their saved
source walks. Compare all 45 retained case profiles with saved inputs. Seal
contract, code, tests and source hashes before evaluation. No new head means no
new training split; preserve the existing head-profile counts and graph and
persistence support qualifications. Missing forecasts remain in contribution
scoring; probability comparisons report their exact supported population.

## Scores and calibration

Primary comparisons are incumbent versus direct conversion on original-cohort
contribution RMSE and equal-origin, actual-PA-weighted hitting RMSE. Also report
MAE, bias, totals, each origin, never-debut upper and lower minors, all non-arrivals,
source-exposure bins, foreign newcomers and the thirteen additions separately.
Use nominal paired player-cluster intervals, 2,000 draws, seed 84, fixed original
origin weights. These exposed development intervals are not a fresh test.

On supported actual MLB participants, score the full categorical event forecast
with per-PA log loss and multiclass Brier, equal weighting of origins and PA
weighting within origin. Compare future US with past US and held-origin reference
on the identical US-supported participants. Compare combined future probabilities
with reference on their stated supported participants. The incumbent scalar rate
does not specify eight probabilities; do not invent them to compare log loss.
Report predicted and actual K, BB, hit and HR frequencies, including conditional
cohort totals and fixed probability calibration bins [0,.05,.10,.20,.30,.50,1].
Actual future PA weights here diagnose conditional performance; they are not
forecast playing time and do not establish arrival accuracy. Show low-exposure
and lower-minor behavior rather than letting established MLB PA dominate.

## Player review and decision

Retain all 45 preceding cases. Add the largest gain, harm, false high, false low
and ordinary active case for each direct arm among changed original forecasts.
Select four same-origin peers by origin stage, age, minor exposure and scouting,
without their outcomes. Reconstruct real source counts, graph and persistence
probabilities, direct event-value terms, PA products and actual MLB events; show
source-removal sensitivity without refitting. Review gains and losses together.
No disposition or next model test before this walkthrough is complete.

A selected replacement needs improvement in both primary losses and no unexplained
systematic lower/upper-minor or cohort-total failure. If direct conversion loses,
retain the incumbent and describe whether event calibration or scalar integration
explains the loss; do not reject all component evidence. Transporting persistence
from selected MLB returners to minors and pooling without age/pedigree are explicit
assumptions. Neither this experiment nor proper probability scores certify them.
No explorer promotion, candidate freeze or protected 2026 access in this check.
