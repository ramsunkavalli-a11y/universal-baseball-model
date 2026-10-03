# Current hitter research model

The next-year hitter model is usable for inspecting historical forecasts, but
not yet a finished player-valuation system. Its established-player hitting
accuracy is competitive with the public projections we matched. Playing time
is weaker, and it badly underestimates some fast-moving prospects. The explorer
separates those questions instead of hiding them inside a WAR number.

## What it predicts

For each known player, predict next calendar year's MLB hitting, probability of
any MLB plate appearance, PA if he plays, expected PA, and expected offense.
Expected PA is appearance probability times PA if active. Hitting uses a custom
fixed-event batting contribution above an average MLB hitter per 600 PA.
Expected offense adds replacement credit to batting contribution. It is not
full WAR: defense, baserunning and position are absent from this branch.
It is also not trade value, six years of service, or eventual career potential.

Players who never reach MLB remain in the test and contribute zero delivered
offense. They have no observed MLB hitting rate; zero PA does not demonstrate
zero talent. Minor-league hitting forecasts extrapolate performance conditional
on playing in MLB. A low next-year chance is not a poor prospect grade.

## How it works

The hitting model uses a regularized linear regression with 199 inputs. It learns
from future MLB participants, weighted by their actual contribution in PA. The
playing-time system uses two histogram gradient-boosting models with 251 inputs:
one predicts appearance, the other workload conditional on appearance. Their
product gives expected PA. This keeps forecasts nonnegative without pretending
every minor leaguer will get a fraction of a guaranteed MLB season.

The inputs include three seasons of batting counts separated by MLB, AAA, AA,
A-plus, A, short-season, DSL and distinct rookie leagues, plus age, MLB history,
draft information, historical prospect rankings, games and role evidence.
Recent performance gets more weight; small samples shrink toward a prior.
Missing historical ranks or signing records are not treated as zero talent.
The missing 2020 minor season is flagged separately from performance; MLB
opportunity accounts for its shortened schedule. No new college collection is
required. This branch is not certified park-neutral and does not silently
inherit every contact, park or opponent experiment elsewhere in the project.

## What the comparison tells us

The broad test retains 30,506 forecasts for seven origin years, predicting
2017–2019 and 2022–2025. Folds exclude test players from training and use mature
outcomes available by the forecast cutoff. Historical sources are reconstructed;
they are not guaranteed contemporary archived snapshots. Repeatedly examined
results are development evidence, not a new independent validation sample.

On 2,627 identical forecasts matched with both public systems, custom hitting
RMSE is 1.7435 for this model, 1.7746 for Steamer and 1.7534 for ZiPS. This does
not establish general superiority: archive timing is uncertain and these are
converted event-based units, not each provider's native target. Playing-time
RMSE is 138.49 PA versus Steamer's 135.38; average absolute error is 106.87
versus 92.08 PA. The latter is 16.1% worse, slightly outside our 15% working
goal. Converted offense RMSE is 1.0613 versus 1.1187 for Steamer, with the same
qualification. It must not be called official WAR accuracy.

## What remains wrong

Kurtz had the fourth overall pick and known college class in the inputs, yet
the model projected 2 PA before his 489-PA season. Langford was projected for
43 before 557. These are not missing names or missing draft records: elite
recent draftees have little comparable mature MLB training support. Soto's
0.13 expected PA before 494 is a more extreme immediate-readiness miss.
Conversely, Salas's low immediate chance before no MLB PA is not evidence that
his eventual potential is poor. Simply giving every high-ranked teenager
immediate MLB value would fail that baseball test.

Tatis was projected for 35 PA before 635, and McLain for 174 before 577.
Return/availability is not solved. McLain's offense estimate looks close only
because low playing time and an overly favorable hitting rate offset one
another. Established Judge was projected for 531 PA versus 679; extreme talent
and durability remain difficult. These cases are exposed with source counts,
actual saved calculations and successful and unsuccessful peers.

Expected appearances are 4,404.8 versus 4,538 actual overall, but upper minors
are 727.5 versus 858 and lower minors 88.6 versus 58. Good league totals hide
misallocated opportunity. No new probability calibrator or continuous confidence
interval is certified. The explorer's support flags are not confidence levels.

## How to use the explorer

Select a forecast season and organization, then sort by hitting alone, chance,
expected PA or offense. Actual results are hidden until selected. Click a player
for the source statistics and separate forecast quantities. Organization comes
from the requested historical December 31 roster when available; otherwise it
is the last observed primary batting club, possibly an older or rehab club.
Unknown affiliations remain unknown. Filtered totals describe known players,
not a complete future club budget or future entrants.

The research candidate is retained. The frozen 2026 forecast and deployed
explorers are unchanged. The next substantive problem is readiness for elite
new entrants, with unavailable or unsupported forecasts kept explicit—not
another generic model-library tournament or name-specific override.
