# Hitter age-relative-to-level and batting-side result

Status: rejected on untouched 2025 confirmation; no values changed.

All four stable-demographic families improved both component log loss and Brier on
the 2024 development target. The selected age-by-batting-side interaction reduced
development log loss from 0.988074 to 0.986447 and Brier from 0.465840 to 0.465512.

That result did not survive the frozen 2025 check. Among 112 arriving hitters and
15,300 target PA, log loss worsened by 0.000623 and Brier worsened by 0.000214. The
player-bootstrap intervals crossed zero and had clearly positive upper bounds.

The candidate worsened both scores for every supported split: younger-for-level,
older-for-level, right-handed, and left-handed hitters. Seven switch hitters improved,
which is far too small and was not an authorized promotion subgroup.

## Decision

Reject age-relative-to-level, batting side, and their interactions as direct hitter
component adjustments. They may remain context or subgroup fields, but they do not
earn a skill bonus. Height, weight, birth country, position, outside FV, and current
2026 outcomes were not used.

Machine-readable evidence: `docs/hitter-age-level-batting-side-result.json`.
Frozen protocol: `docs/hitter-age-level-batting-side-plan.md`.
