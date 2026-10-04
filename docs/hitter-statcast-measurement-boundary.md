# Historical Statcast measurement boundary

2026-10-04. This adds a reviewed projection of the preserved MLB 2015–24 source;
it does not overwrite the original exact-count failure or authorize a forecast.
All twenty residual player-seasons match the season totals reconstructed from
official game logs. Their discrepant plays have been aligned with the feeds.

Thirteen missing source rows are batter-interference outs. The official feed
records no in-play pitch for those plays, although they count as at-bats. Seven
extra source rows are interference awards, described as reaches on an interference
error, without an official at-bat. Therefore the comparable normal contact count is
AB minus K plus SF plus SH, minus those non-contact interference outs. Source
contacts must exclude catcher interference and the seven interference awards.
Verify this corrected equality separately for every player, not just league totals.
Keep all original rows and an explicit exclusion ledger. A later interference on
an otherwise legitimate fielding-error play is NOT an interference award: Tim
Beckham's 2016 play is an example. Use the award phrase, not any occurrence of
the word interference. Do not infer a missing exit velocity from an official out.

The measurement universe is regular-season, result-producing, non-bunt in-play
contacts after excluding those awards. Keep missing speed or angle as missing,
and keep measured homers without spray coordinates. Preserve actual historical
venue, opponent pitcher, batter side and pitcher hand. Raw summaries are not
already neutralized for park or opponent; those adjustments, if learned, belong
inside the forecast training boundary.

The three conflicting completed venue records are games suspended and resumed
in another park (2019 game 565534, 2020 game 630882, 2021 game 633224). The feed's
one game-level venue describes the resumption and does not locate earlier plays.
For these games, select the completed schedule segment by each terminal play's
end timestamp and the original/resumed scheduled start timestamps. Save the
per-PA venue overrides with both schedule and play provenance. For all other
games use the unique completed venue. Fail any unmatched source PA in a split
game; do not silently apply the final park to all contacts. Earlier canonical
game-level receipts remain preserved and are not used alone for these games.
Current Savant exports retroactively label the Athletics as ATH. In 2015–24 the
season-specific MLB authority calls them OAK; normalize that display alias only
inside this declared historical range and preserve the raw team strings. This
is not evidence that those games occurred at the Athletics' current home park.

[Savant's documentation](https://baseballsavant.mlb.com/csv-docs) explicitly says
launch speed and angle include estimated values for some untracked balls.
[Tango's 2017 description](https://tangotiger.com/index.php/site/article/statcast-lab-no-nulls-in-batted-balls-launch-parameters)
explains that these estimates can use the contact description and actual result,
and can be reprocessed retroactively. The public export does not identify each
estimated row or its original publication vintage. Accordingly these are current
provider historical values, not a verified original preseason snapshot or a
camera-only dataset. Outcome-dependent estimates use results from the predictor
season, not the following-season target, but limit claims about wholly independent
contact information and strict historical availability. Do not label a complete
pair as proof that a camera measured it. Do not add current expected-outcome fields.

Save the full source walkthrough and actual chronological held-player support
before freezing the predictive comparison. Historical source integrity is not a
claim that Statcast improves next-year hitting or closes the overall model goal.
