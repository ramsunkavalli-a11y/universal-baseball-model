# First additive 2027 hitter value assembly

2026-10-09, fixed before materialization. Assemble the reviewed batting/PA,
running, position and defensive contributions without new fits. This produces
a development full-component WAR estimate, not an approved explorer or proven
trade value. Historical whole-value and contract/control gates remain required.

Convert the existing batting wins/600 back to runs with its original fixed 10
runs/win. Divide the final additive runs by one common forecast environment:
the completed 2026 league's 21,769 runs and 43,079 2/3 innings imply the existing
Tango/FanGraphs runs-per-win convention. Use 570 full-season replacement wins
per 183,849 reference PA. This is a dated environment assumption, not a claim
to know the 2027 run environment. Do not award replacement twice.

Use the existing position schedule per 1,458 innings and per 162 DH starts.
Keep projected position mix, no league quotas. Running uses its reviewed
steal/advancement components. The twelve defensive channels use their actual
position-specific/native exposure forecasts. DP and GIDP retain the previously
selected explicit population expectation of zero. Non-OF arm is also an explicit
unmeasured comparable estimate, not borrowed OF skill.

ABS: continue the 2026 challenge-rule scenario for the 2027 base, without claiming
that future rule changes are known. Initial-call framing and challenge skill
are different components under [MLB's documentation](https://baseballsavant.mlb.com/abs-metrics-documentation).
One MLB challenge season does not establish reliable year-to-year individual
skill: use a disclosed zero-centered challenge prior, not its noisy raw runs.
Show a separate full-ABS sensitivity with initial-call framing removed, not a
forecast that full ABS is certain. Catcher throwing and blocking remain.

Batting context needs honest naming. The selected practical hitter target is
fixed-weight, league-relative observed production. It is NOT certified park-
neutral talent. Existing no-correction decisions cannot certify a different
model, and another park subtraction is not automatically appropriate. Retain
zero additional park credit in this development assembly and label the batting
reference `observed_context`, with a park-context limitation. [FanGraphs' WAR
definition](https://library.fangraphs.com/war/war-position-players/) includes park
adjustment. Therefore this development output must not be presented as an exact
FanGraphs WAR implementation or portable context-neutral talent. Reconcile this
limitation in the matched whole-value comparison before the release decision;
do not silently change/retrain batting here.

## Fixed reference, not a forced universal ranking total

Refresh the repository's fixed-cohort centering convention, leaving its older
2024 constant intact. Freeze reference membership as every positive-PA official
MLB hitter in completed 2026 (662 people, 183,849 realized PA). Use their **2027
projected PA and components**, not realized production, for the common centering
numerator and denominator. A reference member outside the hitter forecast has
explicit zero projected exposure; preserve the identity and report it. Sum
batting, running, defense and position, excluding replacement and park; divide
the negative sum by the identical reference projected PA. Apply this single
constant per projected PA to every player. Do not derive it from all prospects
or change it when filtering teams. This defines average relative to this dated
reference population; it does not prove calibration or make future league
totals match a quota. Preserve raw and centered totals for review.

Every row must contain all component names, evidence/units and source dates.
Unknown roles remain incomplete full-value rows even if a numeric development
subtotal can be computed. Preserve negatives. Replay fixed players and extreme
totals, verify component sums, ensure DH-only players have no fielding credit,
and check the reference balance separately from historical accuracy.
