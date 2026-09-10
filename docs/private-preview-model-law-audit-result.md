# Private preview model-law audit

Status: all 18 enforced structural checks pass.

The audit runs directly against the playable 2026-09-08 preview. It checks 23,640
hitter player-years, 31,656 pitcher player-years, 6,719 modeled pre-MLB hurdle rows,
9,194 internal FV rows, and 8,393 current value records.

It enforces:

- unique, complete six-year player paths;
- probabilities inside zero and one;
- hitter and pitcher outcome probabilities summing to one;
- pitcher role probabilities summing to one;
- expected workload equal to active probability times conditional workload;
- expected WAR equal to conditional WAR rate times expected workload;
- ordered, disjoint prospect hurdles that sum back to arrival probability;
- exact monotonic conversion from expected WAR to internal FV;
- player type following the available hitter/pitcher path;
- one current value record per player and ordered WAR/value intervals.

The first run found 23 MLB records whose Phase 2 mean WAR was still displayed with
old Phase 1 WAR bounds. The current-value builder now sums mean, lower, and upper WAR
from the same retained annual path. The rebuilt preview has zero interval-order
failures. This changes displayed WAR ranges, not central contract values.

Three limitations remain visible rather than being called passes: the six-year
prospect hurdle repeats two-year hazards approximately; organization-neutral value
is not a current-team allocation; and structural correctness does not replace the
protected post-2026 outcome test.

Machine-readable evidence: `docs/private-preview-model-law-audit-result.json`.
