# Preserve larger MLB position evidence when a minor stint is short

2026-10-09. The joint-budget player review is complete; its source-selection
defect is documented in hitter-2027-joint-role-result.md. This is the only
follow-up to that comparison, not a weight search. All targets, folds, scores,
eligibility, upstream PA and fixed cases remain identical.

Change only fallback evidence. Instead of selecting a minor season and deleting
older MLB evidence, pool the latest minor season with all older MLB evidence in
the same three-year window, in actual field/DH-equivalent outs, using the already
established 1, 0.5, 0.25 recency weights. Normalize after summing exposure, not
before. Thus a two-game rehab does not have equal influence to a full MLB season.
Current MLB versus fallback still uses the unchanged 100-PA reliability. This
does not claim that historical position predicts a new assignment perfectly.
No fielding roles not actually observed (or roster fallback if none) are donated.

The original failed/provisional candidate and its receipts remain intact. Store
this repair separately and review the same players plus new objective extrema.
Proceed to provisional 2027 assembly only if the fixed 5% error tolerance holds,
the targeted evidence-erasure bug is demonstrably removed, and current-player
checks do not reveal an equivalent logic failure. Carry warnings for prospects,
DH/field reversals and absent role history; full release still needs full-WAR
and financial checks. A tiny pooled gain is not proof of improved talent.
