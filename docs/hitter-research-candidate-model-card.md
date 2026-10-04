# Current hitter research candidate

2026-10-04. This candidate estimates next-calendar-year MLB hitting, playing
time and delivered offense. It is useful for examining forecasts and finding
mistakes, but it is not yet the finished player-value model. Its playing-time
errors and prospect misses remain important. Nothing here replaces the frozen
2026 forecast or its published explorer.

## What the model predicts

Hitting ability is the expected hitting contribution over 600 MLB plate
appearances, without a position bonus, defense or replacement credit. A minor
leaguer's number refers to MLB hitting, not production at his current level.
It is an estimate conditional on playing; we cannot observe MLB hitting ability
for someone who never appears. His zero delivered offense is not zero talent.

Playing time has two parts: the probability of any MLB plate appearances and
the expected plate appearances if he plays. Their product gives expected PA.
For example, a 50% chance of playing with 300 PA if active means 150 expected
PA, not a prediction that he will necessarily receive 150.

Delivered offense multiplies expected PA by the hitting contribution plus
replacement credit. The units are fixed-event batting-plus-replacement wins,
not official FanGraphs WAR. This does not include baserunning, position value,
fielding, catcher defense, salary, trade value or years of club control.

## What the model uses

The hitting estimate is a regularized linear model with 199 inputs. Three
seasons of outcome counts are represented separately by level, alongside age,
listed position and available draft evidence. The model learns from later MLB
outcomes, weighting participants by their actual PA. Separate level inputs let
it learn translations; they do not automatically make each minor park neutral.

Playing time uses two scikit-learn histogram gradient-tree models with 251
inputs. These include production and workload history, age, level, draft
evidence, roster/status information and dated prospect rankings. A recent lack
of PA is not treated as a medical diagnosis. Exceptional availability has
explicit warnings rather than a fabricated universal injury explanation.

The candidate does not currently include the separately tested detailed contact
block, explicit learned park/opponent adjustments, team record or a complete
diagnosed-injury model. Those earlier experiments did not establish a reliable
gain for their tested versions; they did not disprove the underlying ideas.

The selected research uncertainty model draws integer hitting outcomes and
links hitting variation to possible workload while preserving the current
expected offense. It removes physically impossible count combinations. Its
roughly 0.4% overall range-error improvement is modest, and every fitted
workload/hitting slope reaches the declared bound. It is not a better point
forecast or a validated player-specific K/BB/HR distribution.

## How the historical test works

There are 30,506 forecasts for 11,020 people, including non-arrivals. Target
years are 2017–2019 and 2022–2025. Each forecast uses preceding-season
statistics and the documented following-preseason ranking date. All training
outcomes must already be mature, and the tested player's entire group is
excluded from training. The canceled 2020 MiLB season is not bad performance;
2020 MLB targets are excluded from scoring.

These years have already been used for development. They are not a fresh
holdout. Historical sources, ranking dates and affiliations are reconstructed,
not fully certified archived preseason snapshots. A large training sample does
not guarantee enough examples of an elite prospect with little professional PA.

## What the public comparison says

The same 2,627 player-seasons have both public hitting forecasts and candidate
forecasts. Hitting rates can be measured for the 2,088 seasons with actual MLB
PA. Years get equal weight; hitting errors within each year are PA-weighted.

| Matched error | Candidate | Steamer | ZiPS |
| --- | ---: | ---: | ---: |
| Hitting per 600 PA RMSE | 1.7435 | 1.7746 | 1.7534 |
| PA RMSE | 138.33 | 135.38 | Not treated as equivalent workload |
| PA average absolute error | 106.41 | 92.08 | Not treated as equivalent workload |
| Delivered offense RMSE | 1.0605 | 1.1187 | Not treated as equivalent workload |

All hitting/value comparisons use a custom event conversion and common origin
league reference. Public archive dates and environment offsets qualify these
numbers: the small hitting advantage is not proof of better park-neutral talent.
The PA average absolute error is about 15.56% worse than Steamer, beyond the
declared 15% practical allowance. That requirement has not been waived.

## Player checks that matter

Nick Kurtz's 2025 forecast is about 10 expected PA against 489 actual. Bryan
Reynolds's 2019 forecast is about 13 against 546. These are substantial readiness
misses, not problems solved by wider hitting ranges. Conversely, promising
prospects with zero next-year MLB PA must remain in the test; selecting only
eventual stars would make the same system look unrealistically confident.

Aaron Judge's 2025 new P90 offense is about 8.76 against 9.39 actual, better
than the previous range but still short. Austin Hedges's 2022 lower range moves
in the wrong direction. Terrance Gore's impossible combinations disappear, but
his upper range becomes less accurate. Ben Rortvedt's nearly correct delivered
offense hides a large PA underestimate and too-optimistic hitting estimate.

Brandon Belt's surprising unsigned season remains a real forecast miss, not
evidence that every older productive hitter deserves a blanket penalty.
Wander Franco's exceptional availability remains a separate scenario gap.

All eighteen selected player reviews, including gains and harms, are preserved
in the [count-risk walkthrough](hitter-event-count-risk-walkthrough.md). The
[range result](hitter-event-count-risk-result.md) has the full score and support
qualifications. The [common-value review](hitter-compatible-value-v63-result.md)
explains the units and public comparisons.

## What must happen before this is finished

The next substantive model work must address systematic readiness/workload
misses and public playing-time accuracy, not another width-tuning sweep.
Any change must keep identical evaluation membership, be tested on future MLB
outcomes and receive actual player walkthroughs before disposition. Team and
cohort totals cannot be made credible merely by deleting missing players or
scaling everyone to a desired sum.

Full hitter value still needs supported fielding, running, catcher and position
components. Longer paths need mature horizon-specific training support and a
distinction between calendar years and actual club control. Salary, contract
rights, future entrants and uncertain career outcomes belong in a separate
valuation layer. These requirements remain part of the active project goal;
finishing an explorer does not satisfy them.

## Local research explorer

The new standalone view lives in
`D:/UBM-Source-Cache/hitter-risk-research-explorer/dist`. It has season,
organization, stage, name/MLBAM ID and evidence filters; sortable hitting,
workload and offense; saved uncertainty comparisons; source statistics and all
actual encoded inputs; eighteen completed reviews; and filtered CSV export.
Organization is the reconstructed origin-year affiliation, not a future roster.
Unresolved affiliations stay visible and duplicate names retain distinct IDs.

From the repository, rebuild with
`.venv/Scripts/python.exe -X utf8 scripts/build_hitter_risk_research_explorer.py`,
then verify and assemble the hitting benchmark with
`.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_risk_research_explorer.py`.
These commands require the existing local sealed artifacts; a fresh Git clone
without those data is not sufficient. They fit no new models. The initial
builder receipt and later data/browser receipts are separate.

Serve only that `dist` directory on loopback. The verified local view is
`http://127.0.0.1:8860/`; the process must remain running for it to work. A live
preview is a research handoff, not publication or forecast promotion. Browser
checks cover the filters, identities, player evidence, range comparison,
benchmark and narrow-screen layout. The CSV download event timed out in the
in-app browser; saving the file remains unverified. The separate
[milestone receipts](../reports/model-evidence/hitter-risk-research-explorer)
record these limits and distinguish application checks from model accuracy.
