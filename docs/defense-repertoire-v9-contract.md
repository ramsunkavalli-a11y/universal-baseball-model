# Preserve observed positions when forecasting defensive time

2026-10-07. Repair the role-average allocation defect found in the completed
opportunity review. Estimate total MLB defensive exposure separately from its
allocation across a player's own observed positions. A first baseman does not
receive catcher innings because other first basemen previously caught.

## Same target and one repair

Retain all 12,432 origin-2022–2024 forecasts, official eight-position outs,
separate DH starts, held-player folds and fixed expected PA from the sealed
opportunity comparison. Retain all four old forecast vectors unchanged as
anchors. Reuse the already checked native count conversions; do not refit skill,
arrival, PA or choose coefficients with 2026 outcomes. These historical years
are development evidence. This is not eventual defensive-talent validation.

For every player/origin reconstruct the current MLB fielding-out vector from
the official source. A fallback repertoire uses the most recent minor season
within three years, including all its levels. If absent, use the most recent
older MLB defensive season within that window; if absent, the cutoff-known
defensive roster position is explicitly weak evidence. A DH-only or unknown
label with no defensive history does not invent a catcher or other position.
Preserve an unallocated-opportunity flag instead of claiming known neutral skill.

Current MLB outs and fallback outs become separately normalized eight-position
shares. Mix them using `a = origin_MLB_PA / (origin_MLB_PA + 100)`, then
renormalize the resulting nonzero share vector. If only one vector is available,
use it. No allocation goes outside this player's observed/fallback repertoire.
The fixed 100-PA pseudo-sample represents roughly a few weeks of regular batting
opportunities; it is a transparent stability assumption, not an optimal learned
threshold. Do not tune it or sweep alternatives after results.

Select one dominant origin role for the scalar prior. Use the similarly blended
current MLB and latest fallback **start** shares across eight positions plus
DH; fall back to observed outs or the roster label when starts are missing.
Groups are mutually exclusive, not fractional donors of entire position vectors.
The broad families are catcher, 1B, middle/third infield (2B/3B/SS), outfield,
DH and unknown. Family pooling estimates total time only; it never gives the
recipient a donor's positions or skill.

## Scalar means and sparse support

Learn two conditional ratios: future total eight-position outs per future MLB
PA and future DH starts per future MLB PA. Start with dominant role and career
stage, then family/stage, role, family, all active training batters. Use a group
only with at least 20 distinct contributing people and 10 effective people;
person mass is summed training PA across that person's seasons. Save each
chosen group and its profile counts before any outcome numerator is computed.
These pooling thresholds do not certify transport of minor defensive ability.

Training outcomes must be available by the origin, have positive actual PA,
and exclude all seasons of each held player. Nonarrivals, exits and defense-only
zero-PA players remain in scoring. Missing data remains unknown. Repeated rows
cannot increase distinct-player support. No age-bin search or new model family.

Shrink the individual's current MLB total-outs/PA and DH-starts/PA ratios toward
the supported scalar group using the same `a`. With no current MLB PA, use the
scalar prior alone. Multiply by the unchanged expected PA. Allocate the total
outs using the player's own repertoire vector. If the repertoire is unknown,
keep the scalar potential exposure separately unallocated, assign no fabricated
position outs, and report that missing-value limitation in totals and scoring.
DH starts remain a separate scalar output and never count as defensive outs.

This does not solve future position development or known planned assignment
changes. Historical repertoire is a conservative forecast-time constraint, not
a claim that a player can never learn another position. Record evidence of
future assignments with dates separately; no named news-based forecast overrides
are added to this comparison. Unknown future roles and the older PA cache's
finite-return defect remain explicit limits before delivered-value claims.

## Decision and player review

Primary loss is equal-origin mean eight-position-cell RMSE, contrasting the
repair with the stronger PA-ratio anchor. Use 2,000 paired whole-person draws,
seed 708007. Report old role-average comparisons, all stage/age errors, each
position and full/matched totals, entrants/continuing/exits/nonarrivals, DH starts,
all known native counts and positive-only native counts, profile fallbacks,
unallocated exposure and historical-range warnings. No target-row deletion.

A research integration candidate must have reasonable player allocations, no
more than 2% overall RMSE deterioration versus the ratio anchor, no stage/age
group of at least 100 rows worsening over 10% in development origins, and each
development total within 20% of matched actual. A small tradeoff can be sensible
if it fixes a documented role failure; these are practical tolerances, not proof
of superiority or deployment approval. If it fails, retain verified sources and
the stronger anchor, diagnose the failure without retuning the pseudo-sample.

Keep all 13 prior focal cases and three origin-only peers, then add the new
largest gain/loss and total-exposure false high/low, plus an unknown-repertoire
case if present. Trace source rows, current/fallback vectors, dominant group,
actual support, shrinkage arithmetic, PA and position/native outputs to reality.
Separate known-at-cutoff plans, later injuries, upstream PA errors, unknown
quality and position transport. Independently replay every forecast and scalar
group before a final decision. Complete the baseball review before the next
delivered-runs/value experiment. Frozen forecasts and explorer remain unchanged.
