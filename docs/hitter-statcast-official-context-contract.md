# Historical game context and contact discrepancy review

2026-10-04. Recover official historical venue/team authority for MLB 2015 through
2022 and diagnose the twenty one-contact season residuals found by the captured
Statcast audit. This is bounded source review, with no fit or forecast change.
Preserve the earlier failed receipts and their exact count definitions.

Fetch official MLB regular-season schedules and season-specific team authority
for these eight seasons. Reuse captured 2023 and 2024 metadata. Retain full
responses and byte hashes. Join actual game/venue identity, not a team's current
home park or dimensions. Require unique game IDs and no cross-season records.

For only the twenty already recorded player-season discrepancies, fetch official
MLB regular-season batting game logs. Reconstruct season AB, K, SF, SH and hit
counts from the game logs and compare them with the existing dated backbone.
Join source contacts at game/player grain, including games with zero source rows.
Save all game-level differences, rather than guessing from an annual total.
Fetch full historical game feeds for only the discrepant games to identify the
official terminal plays and scoring/identity exceptions. Limit these to at most
forty games; if exceeded, stop and document the unexpected scope.

All requests specify a season through 2022 or a game in its verified historical
schedule. Do not request protected 2026 or a current-season default. Raw responses
may include unused descriptive metadata, but no such metadata becomes a feature.
Use at most two concurrent requests and three bounded transport attempts; verify
and reuse existing successful captures rather than restarting them. Store these
small captures inside the current workspace. Keep source identifiers, official
outcome attribution and physical contact identity separate.

Classify each residual as explained scoring semantics, missing capture, official
revision, physical-versus-charged identity difference, or unresolved. A matching
annual sum alone cannot certify the correct records. Do not impute a missing
launch measurement or alter a raw response to make the denominator match. If
an ordinary source contact must be excluded for interference or another special
result, declare that rule explicitly in a new measurement adapter and retain
the original row in an exclusion ledger. Explain the resulting measurement
universe and its official reconciliation before use.

After these checks, materialize the full historical measurement source in a new
version and complete the existing source-case walks with earlier history and
unchanged current inputs/forecasts. Count actual distinct active training people
and profile/sample coverage in each outer fold at each row's own origin.
Approval remains separate from a future predictive result. Team-record testing,
the two older Current Talent challengers, frozen forecasts and explorers stay closed.
