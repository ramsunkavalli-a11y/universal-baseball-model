# V40 source audit execution correction

2026-10-03, before any model or source disposition. The first coverage diagnostic
tested `level_group == 'mlb'`, but the pinned universal source uses `MLB`.
That incorrectly classified its MLB shape counts as minor counts. Inspecting
the actual source schema/level sums caught it immediately; no projection fit,
adoption or user-reported coverage claim used the wrong split.

The initial audit and availability table are preserved as
`audit-before-level-case-repair.json` and
`source-availability-before-level-case-repair.parquet` under the V40 generated
folder. Match the exact source label, assert the allowed level set, test MLB/
minor partitioning, and rerun before the source walkthrough. Source bytes,
player membership and scientific contract do not change. No protected outcomes.
The old gradient table still contains minor contacts only; the broader universal
shape table is a distinct source that does contain MLB measurements.
