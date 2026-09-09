# Historical contract source audit: 2025

**Status:** viable private retrospective reconstruction input; parser and identity gate next  
**Audited:** 2026-09-09

A public GitHub gist described as “Cots 2025 Player Contract Data” contains exactly
30 team CSV files at revision `e06fef21f5b9df5bb5bf72a4ed456ce23382a508`.
Rows include player name, 2025 service, options, contract description, 2025–2029
labor-payroll amounts and future `A1`–`A4`, option and free-agent states.

The extract was created 2026-01-31, after the season. It can support only
`retrospective_event_cutoff`, not a vintage-information claim. It has no declared
redistribution license and no MLBAM IDs, so raw/bulk data must remain private and
it cannot become the primary contract authority.

The Phase 1 identity gate will require a unique same-team normalized-name match to
the MLBAM-keyed FanGraphs Opening Day table plus agreement on service time when both
sources report it. Ambiguous names, team disagreements and service disagreements
remain review. Accepted rows can fill the 2025 historical replay contract path;
FanGraphs remains the primary current contract source.
