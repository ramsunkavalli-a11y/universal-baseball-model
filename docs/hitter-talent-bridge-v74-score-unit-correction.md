# Correcting evaluation units without changing forecasts

2026-10-03. Preserve the V74 contract, all 105 fitted heads and initial scoring
artifacts. Three reporting problems were found during the mandatory player and
unit review, before disposition. No parameter, predictor, forecast or cohort
changes are authorized by this correction.

The inherited V68 feature table trains on batting rate relative to the realized
target-season MLB average. Its scored table instead carries the V63 common-rate
label centered on the origin-season MLB average. This is a deliberate distinction
in V63, but V74's first scorer inherited the common label while describing it as
the target-season label. The difference is constant within each origin and reaches
0.581803 wins per 600 PA. Restore the contract's primary batting score using the
original training-table label, independently reconstructed from actual event
counts and the target-season environment. Retain the initial common-rate scores
as a separately labeled sensitivity view. Actual future environments are used
only to validate the response, never as prediction inputs. The delivered-value
comparison remains V63's common-origin value with the same expected PA and origin
replacement reference in every arm. This is a mechanical integration check;
it is not proof of correctly modeling environment or workload dependence.

The first physical check compared rate forecasts with V63 season-value bounds
computed at the old baseline PA. It has no valid interpretation. Recompute rate
bounds in rate units, centered on the realized target-season environment; these
are permissive mathematical event bounds, not evidence of good baseball forecasts.
Keep the incorrect initial counts visible in the correction artifact, not in a
model-validity claim.

Finally, the scorer wrote scores, intervals, cases and verification successfully
and then exited with a console-only KeyError for a public benchmark label. The
independent review runner recomputes every saved score, verifies all fitted
predictions and restores explicit response units. No model fits are repeated.
The original runner remains sealed. Corrected scores and bounds receive new
filenames so the first artifacts and failure can still be inspected.
