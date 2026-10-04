# Correcting player comparison fields without changing forecasts

2026-10-04. During the required player review, the scored table's inherited
ranking columns were found beside newly joined actual feature columns ending
in `_right`. The fitting inputs and support tags use the correct reviewed
ranking vintage. The first score script's peer distances, however, read the
older unsuffixed ranking fields. This is a player-reporting defect, not a
change in models, eligibility, labels, primary scores or outcome-selected cases.

Keep the original scored predictions, cases, peers and score script unchanged.
The additive review reads each actual fold feature row and names its actual
rank and draft inputs explicitly. Rebuild peer distances using those feature
values, not the inherited prediction metadata. Save both original and corrected
peer identities with their level statistics. Do not describe an old displayed
ranking as the ranking the new model fitted. All rate heads and score selections
remain fixed. No new fits or parameter tuning follow this correction.
