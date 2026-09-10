# Prospect current-position source plan

Status: frozen before rebuilding the position-value sensitivity.

## Decision rule

Use current official StatsAPI fielding outs as the primary prospect position source.
Sum positive outs into the five frozen position groups and choose the largest group,
with fixed group order only as a tie-break. If a player has no positive fielding outs,
fall back to the corrected games-based prospect role. Use MLBAM's listed primary
position only when neither usage source exists.

This hierarchy uses observed work before a roster label. It changes no skill statistic,
positional-run schedule, arrival probability, or historical test target.

## Required checks

Report coverage and agreement among all three sources, ensure one row per player, and
rebuild the private transition-value sensitivity. Keep the playable default unchanged
until the resulting movement is reviewed.

No outside FV, organization depth, or subjective position override is allowed.
