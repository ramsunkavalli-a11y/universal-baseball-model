# Historical support for minor league defensive talent testing

2026-10-06. This is a coverage and measurement audit, not a predictive model
comparison. It asks whether the existing minor-league ground-ball evidence can
be tested against later MLB range quality without changing positions silently,
labeling non-arrivals as poor defenders, or using future labels in training.

## Fixed source and population

Use the sealed annual outcome-complete ground-ball ledger for 2016–2019 and
2021–2024. Reconstruct player-by-position origins for each of those seasons,
including 2019, rather than reuse the last test's next-year eligibility. Include
2B, 3B and SS with at least 25 weighted team ground-ball exposures at that
position across the last three calendar years, with weights 1, 0.5 and 0.25.
These are team balls while occupying the position, not individualized chances.
Recent source seasons absent from the file remain absent, not zero performance.
The canceled 2020 minor season is not a new player cohort or a development zero.

Keep every eligible player-position. Join only origin-known name, age, level and
role columns from the existing panel. Unmatched metadata remains unknown. Flag
prior MLB defensive exposure from the 2004–2025 official usage ledger, truncated
at the origin. Report players without prior MLB defense separately from returners;
do not call that flag proof of no MLB batting debut. Keep infield cameos and
source league 130 exposure visible rather than assume every rookie row is DSL.
Source histories beginning in 2016 are left-truncated for older players.

## Fixed later MLB measurement windows

Inventory 3, 5 and 7 calendar years following each origin, ending no later than
2025. Only a fully elapsed window can supply a completed quality label. Partial
windows remain in the ledger with their observed exposure but no scored label.
Never select a best season or extend an individual's window until he succeeds.

Native range runs are player-season aggregates, whereas defensive outs are
available by position. A same-position measurement therefore requires a season
with positive native outs at the origin position, all reported native outs at
that position, and agreement from official usage that no other fielding position
was occupied. Preserve null range measurements. Do not distribute aggregate runs
among positions in proportion to innings. Differences between native and official
outs are reported; their definitions need not give identical denominators.

For coverage, a substantial same-position label requires at least 1,500 pooled
native outs and two measurable seasons. The quality rate is 1,500 times pooled
range runs divided by pooled native outs. This is runs per 500 innings, not runs
per 1,500 chances or a final talent grade. The exposure threshold is a fixed
screen against cameos, not an estimated stabilization point. Report measurement
age and elapsed time; eventual developed performance is not exact origin talent.

Also inventory seasons restricted to the 2B/3B/SS group, allowing movement within
that group. This is a different, mixed-position outcome, not a replacement for
same-position quality. Retain the future position mix explicitly. A fit using
that outcome would need a separate position/development contract. Never treat
later outfield range as confirmation of origin shortstop quality.

Use official future usage to distinguish no recorded MLB fielding, fielding
elsewhere, mixed positions, insufficient measurement and mature quality.
No recorded fielding is not proof of no MLB batting appearance. In all these
unmeasured cases quality is unknown, never zero. Report selection differences
between measured and unmeasured origin profiles; success among selected arrivals
cannot certify the entire DSL population.

## Actual chronological support

For every fully observed origin and every player-ID-modulo-5 held-player fold,
count only training labels whose complete window ended by the test origin.
Exclude held-fold players across all their origins and positions. Count distinct
people, distinct origins and matching origin-known level, age band, position and
prior-MLB-defense profiles. Repeated seasons and positions are not new people.
Twenty matching people is only a sparse-support warning, not model approval.
For orientation, report whether a fold has 30 distinct people and two training
origins; that describes a possible small comparison, not statistical adequacy.
Support flags must not depend on the test player's future performance.

Inspect the existing older minor-fielding inventory for its actual columns and
years. Position usage alone does not recreate a pre-2016 ground-ball quality
feature. Do not claim that mature later outcomes solve missing older inputs.

## Review and next decision

No fits, predictive losses or promotion are authorized by this audit. Preserve
source fingerprints, all eligible identities, annual target paths, support tables
and unresolved source semantics. Verify protection hashes before and after.

Walk through the fixed cases from the preceding range experiment, including
Witt, Volpe, Peña, Abrams, Lawlar, Mayer, Downs, Mateo, Rafaela, Edwards, Peguero
and Linares. Show minor exposures and adjustments, later position-specific
measurement, window maturity and actual training support. Add three origin-known
peers per fixed case using age, level, position and exposure, without consulting
their future success. Gains, deteriorations and prediction errors are not
applicable because this audit produces no forecast.

After the walkthrough, choose the next step from support and measurement quality,
not favorable player rates. If only a narrow test is supported, state that scope.
If longer lower-minors paths lack chronological examples, name the missing
inputs/labels and do not rerun the next-year contribution test as a substitute.
Keep the current forecast and explorer unchanged; access no additional 2026
outcomes. The full nonbatting talent and player-value goal remains unfinished.
