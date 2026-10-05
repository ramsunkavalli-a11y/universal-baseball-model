# Direct event conversion does not replace the hitter model

Player walkthrough complete. The fixed no-fit comparison retains 30,506 original
forecasts plus thirteen additions, and ends in 2025. It does not open 2026.
Current UBM remains the selected historical benchmark. Direct event conversion
worsens both primary losses and produces an unreasonable prospect total.

## What the test establishes

The [contract](hitter-direct-event-contract.md) compares already saved next-year
US and combined US/foreign event probabilities with their defined batting-value
conversion. Playing time and original MLB talent routing are unchanged. No new
heads, blends, penalties or source data are fitted. All 45 prior source profiles
reconstruct before scores. The [47 player walks](hitter-direct-event-player-review.md)
include new outcome-selected Torres and Collins cases and origin-only peers.

| Original cohort measure | Current UBM | Direct combined events |
| --- | ---: | ---: |
| Contribution RMSE | 0.435133 | 0.437596 |
| Actual-PA-weighted hitting RMSE | 1.804813 | 1.849335 |
| Predicted batting plus replacement wins | 4,155.43 | 3,904.25 |
| Observed wins on the same membership | 4,185.43 | 4,185.43 |
| Never-debut predicted wins | 194.67 | −56.51 |
| Never-debut observed wins | 207.44 | 207.44 |

The nominal paired player-cluster 95% interval for the contribution squared-loss
increase is +0.00106 to +0.00326; for hitting squared loss it is +0.09692 to
+0.22608. These are exposed development intervals, not fresh confirmation.
Six of seven origins worsen contribution RMSE; 2022 improves. Upper-minor
never-debut hitting RMSE worsens 2.563 to 2.925, and lower minors 3.179 to 3.443.
This is not a 2021-only failure. Non-arrival contribution errors improve, but
making positive contributors too pessimistic more than offsets that improvement.

## Useful event information is not calibrated player value

Among 786 original never-debuted participants with US evidence, future event
log loss improves from the past translated profile's 1.48387 to 1.47997 and
multiclass Brier from 0.70763 to 0.70702. Both also beat the reference profile.
These proper event scores are conditional on MLB participation; the scalar UBM
forecast does not specify eight probabilities and is not assigned invented ones.

The future profile's equal-origin, actual-PA-weighted K rate is 25.60%, close to
25.50% actual. Its HR rate is only 2.13% versus 2.79% actual. Log loss gives all
plate appearances a proper probability score, but batting value gives rare HR
more consequence than ordinary outs. A small overall probability improvement
does not establish an adequate power forecast. Even established-player diagnostic
probabilities underpredict HR, 2.78% versus 3.22%, despite past translated 3.27%.
Those diagnostic probabilities do not replace established-player forecasts.

The persistence fit optimizes squared error in relative log coordinates, not
the arithmetic mean event distribution or batting loss. Its calibration inputs
use recency-weighted historical MLB environments, whereas the shared US graph
profile centers on the current held origin reference. Borrowing it for minor
development is another assumption. These are documented design differences,
not a claim that one isolated cause explains every power miss. The result does
not reject direct event-value conversion as a mathematical method; it rejects
using these particular transported probabilities as ready forecasts.

Kurtz improves from 1.024 to 2.980 hitting wins/600, but ten expected PA still
misses his 489-PA debut. Engel's direct negative forecast is closer to his poor
debut. Torres, Yordan, Alonso and Kwan worsen. Suzuki improves, whereas Lee's
positive direct forecast worsens his poor debut. On thirteen additions, total
predicted contribution improves 1.72 to 4.29 against 8.34 actual, but weighted
hitting RMSE worsens 2.865 to 3.101. This mixed, sparse result is not a foreign
model certification.

## Calculation correction and integrity

Independent reconstruction checks 2,752 score/frequency fields and all 47 case
products. Fourteen new/conversion/source checks pass. The original probability
and contribution outputs are preserved.

One reporting defect is corrected by an appended receipt: inverting log exposure
left tiny floating-point residues that initially labeled 9,713 rows as foreign
instead of fourteen. Residues below one millionth of a PA are now zero only in
scope metadata. The actual fourteen have at least 70.8 supported foreign PA.
The corrected foreign scope has 410 actual PA, not 40,694. No forecast, fit,
overall score, player selection or other scope membership changes. The original
receipt remains visible; use `corrected-scores.json` and corrected foreign intervals.

## Decision and next boundary

Do not promote either direct arm. Preserve the current routed numeric, scouting,
translated prospect and MLB tracking heads and their qualified public comparisons.
The shared regression and direct conversion questions are now answered for this
saved design; do not repeat them without a specific calibration/design repair.

Move to assembling and auditing that strongest existing model's 2025-origin
inputs and a separate team-filtered research explorer. Freeze the model, sources,
membership and evaluation rules before retrieving authorized 2026 results.
Selection as the best existing development model is not certification: prospect
workload, foreign coverage, known availability and the public playing-time gap
remain real. Full defense, full WAR, control years and trade value remain separate.
