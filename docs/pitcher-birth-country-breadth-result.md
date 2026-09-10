# Pitcher stable-demographic breadth result

**Status:** all new families rejected; development diagnostic only

Five player-held-out folds were used for the 2024 development season. The incumbent
scored 0.976699 log loss and 0.515806 Brier. Country-only scored 0.976874 and
0.515953, slightly worse on both. Adding birth country to age and handedness was
worse still. The age-by-country interactions also failed.

No family cleared the rule requiring improvement in both proper scores, so the
incumbent was selected and the 2025 country breakouts are correctly all zero change.
There is no supported USA, Dominican Republic, Venezuela or other-country adjustment.
This says only that these coarse labels did not improve this forecast; it is not a
claim that national origin has no relationship to baseball development.

The cross-validated 2024 score for the existing age/hand family was also worse than
the incumbent, despite its small favorable 2025 point result in the earlier audit.
That reinforces its current provisional status: it should not be treated as a strong
or general demographic law, and it needs a later untouched origin before broader use.

Current height and weight were excluded because using 2026 measurements for young
players in historical forecasts would leak future information. They can be tested
only after dated historical measurements are available.

No 2026 result, outside FV, rank, contract or target pitcher count entered the test.
Machine-readable details are in `pitcher-birth-country-breadth-result.json`.
