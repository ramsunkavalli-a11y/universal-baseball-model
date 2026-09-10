# Pitcher workload environment as-of result

Status: promising development challenger; no current value change.

The cutoff-safe replay evaluated 354 pitchers from the 2018 and 2019 debut cohorts.
Every training career was complete before its evaluation date, and each league-
environment forecast used only earlier MLB seasons.

The raw tier distribution scored 228.98 CRPS with 78.8% P10-P90 coverage. Scaling
complete annual paths by forecast MLB mean BF per active pitcher lowered CRPS only
slightly to 225.30 and was not better in both years. Adding supported rotation,
opener, bulk/swing and relief cells lowered CRPS to 186.12, an 18.7% improvement, and
won in both years. This confirms that a start count alone hides important workload
structure.

The challenger is not promoted. Its P10-P90 coverage fell to 74.3%, and this isolated
test conditions on the evaluation player's eventual tier and role. It therefore does
not prove that the current model can predict that role at forecast time. Preserve the
candidate for the next dependent career-path comparison, where role probabilities and
environment uncertainty must be carried together. Do not boost raw BF or current
pitcher values from this result.

Machine-readable result: `docs/pitcher-workload-environment-asof-result.json`.
