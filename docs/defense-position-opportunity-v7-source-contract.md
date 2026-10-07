# Defensive position history and opportunity preparation

2026-10-06. This is the source and support checkpoint for connecting the reviewed
defensive skills to player value. It prepares actual position usage, not another
defensive-talent learner. No forecast, explorer or completed 2026 evaluation is
changed. A separate comparison contract and completed source walkthrough are
required before fitting the opportunity bridge.

## Question and boundaries

Can the existing historical fielding sources provide reliable, cutoff-known
position evidence for MLB players and prospects? The next integration needs
eight separate defensive-out forecasts, plus distinct catcher and arm/receiving
opportunities. It must not award innings from a roster label, substitute batting
PA for fielding outs, or give every prospect zero defensive exposure because he
has no prior MLB innings. Future MLB defensive quality remains the skill target;
coming-season fielding exposure is a separate value ingredient.

The existing playing-time estimates are fixed. Historical development inputs
are the saved `hitter-preseason-readiness-v68` predictions (`preseason_pa`), not
the older `baseline_pa` or workload-model-v2 estimates. These cached estimates
are not an exact historical replay of the later repaired 2026 production package.
Historical targets stop at 2025; 2026 results are never read for this checkpoint.

## Sources and exact scopes

1. Official MLB fielding inventory, 2004–2025, supplies observed MLB defensive
   outs. Its overlapping 2021–2025 records must match the separately certified
   position-role source exactly before they replace those duplicate copies.
2. The saved 2009–2019 affiliated fielding captures supply earlier minor-league
   position history. Reconstruct all 66 captures and compare every saved value.
   A sport-wide season query can attach aggregate totals to one returned club
   and league. Use its player/sport scope; do not infer exact team innings or
   split older rookie history into DSL, complex and advanced rookie from that
   attached league label.
3. Add only the 2019 Appalachian/Pioneer fielding supplement. That source uses
   sport 5442, separate from the 2019 sport-16 capture. Check the raw sport IDs
   and reproduce its records before addition. Older supplements are subsets of
   older combined rookie totals and must not be added again. Shared player IDs
   across the two 2019 scopes are not themselves duplicate games.
4. The certified 2021–2024 and 2025 league-specific position-role captures supply
   current minor history. League 130 is DSL, not complex ball, in the new view.
   Preserve the old files and their original labels. Team labels remain metadata,
   not an authorization for team-level allocation without a separate scope audit.

Keep pitcher outs and DH starts visible, but neither counts as position-player
defensive outs. Canonical outs are integer conversions of baseball innings
notation. Missing source history remains unknown. The canceled 2020 minor season
is explicitly absent, not a season of individual zero defensive ability.

## Preparation checks

Save a normalized source table, annual player/scope usage, and three-calendar-year
origin summaries. Keep MLB and minor history separate and retain both defensive
outs and starts; do not relabel starts as innings. Nine-position start vectors
may describe role, while eight-position out vectors describe actual defense.
The summaries use fixed weights 1, 0.5 and 0.25 only to describe history; those
weights are not selected opportunity-model coefficients.

Verify source hashes, complete capture/page counts, exact reconstruction,
identities, source-scope duplicates, DH zero outs, and positional conservation.
Report small historical conservation discrepancies rather than manufacturing
corrections. Compare team totals too, but do not reject correct player-level
records solely because an aggregate season query lacks exact team splits.

The current exported 2021–2024 and 2025 artifacts are a later acquisition than
the original receipts in `docs`. Use the `report.json` supplied inside each
artifact for byte hashes and raw captures; retain the older receipt identities
as a version comparison, not as certification of this different acquisition.
Require both matching artifact-local hashes and complete reconstruction. Equal
row counts alone do not establish that two acquisitions contain identical data.

Attach origin summaries to every saved historical forecast without dropping
players. Before any fit, count distinct active training players for each actual
time/held-player fold at the 2022, 2023 and 2024 origins. Training labels must be
available by that origin; exclude the held player's entire history. Describe
support by origin stage, age, actual primary starting role, and defensive sample
size, including intersections and missing history. Keep DHs and eventual exits.
This audit is not proof that 20 matching people suffice for reliable estimation.

## Baseball review and allowed disposition

Trace fixed cases before any fit: Baty and Álvarez in 2019, Betts in 2023, Varsho
in 2022, Schwarber in 2023, De La Cruz in 2022 and Eldridge in 2024. Add any source
failure case. For each, show raw scopes, actual positions, starts, outs, history
summary and three peers selected solely from origin age/stage/position/history.
No forecast improvement or rejection is claimed from this source checkpoint.

Keep the old Player Value v1 contracts and verdicts unchanged. Their prior-year
MLB persistence structurally gives entrants zero exposure; their continuing-only
allocation test cannot establish entrant allocation. The later machine exposure
winner is useful development evidence, but used a different playing-time input,
excluded catcher outs and did not hold players out. Do not repeat its tournament
or present it as current-package validation.

## Literature informing the separation

[FanGraphs positional adjustment](https://library.fangraphs.com/misc/war/positional-adjustment/)
scales defensive position value by innings and accounts for DH separately.
[The original depth chart explanation](https://blogs.fangraphs.com/introducing-fangraphs-depth-charts-and-standings/)
separates projected performance from allocated opportunities. These support the
separation of skill, position and exposure, not a copied coefficient or a claim
that raw minor-league defensive results are already translated MLB talent.
