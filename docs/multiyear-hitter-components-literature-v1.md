# Multi-year hitter components: literature and recovered evidence

Research checkpoint, 2026-09-22. This is a methods review and experiment design,
not a claim that a newly proposed method has won. Historical development remains
exposed; the frozen 2026 forecasts are not rewritten.

## Main conclusion

Do not restart from an algorithm tournament. Recover the existing component
winners, separate skill from exposure and positional accounting, and test direct
future-year components on common, correctly measured run targets. There are three
different questions: is the skill repeatable; does it transfer into MLB; and does
it improve the integrated player forecast? They need separate evidence.

## What the literature actually supports

### 1. Range: opportunity, spatial smoothing and shrinkage

[Jensen, Shirley and Wyner (2009), Bayesball](https://arxiv.org/pdf/0802.4317)
model out probability across continuous batted-ball locations, partially pooling
fielders at the same position. They then integrate against opportunity density
and run consequences. Their method performs differently by position, and the
paper explicitly warns that year-to-year consistency assumes sufficiently stable
ability. It proposes longitudinal ability evolution as a further extension.
It is not proof that any repeatable defensive residual is already an MLB WAR
projection. Their measured coordinates and estimated starting positions also do
not establish the semantics or precision of our public-feed coordinates.

UBM implication: retain the park-adjusted MiLB range evidence, verify which
opportunities are assigned to which fielders, keep adjacent-fielder attribution
and coordinate uncertainty visible, and distinguish a future skill-rate test
from future run totals. A native-run label is preferable to reconstructing runs
from a standardized success-rate score and an independently estimated denominator.

[Mitchel Lichtman's UZR primer (2010)](https://blogs.fangraphs.com/the-fangraphs-uzr-primer/)
describes position/contact-specific context, park adjustments and the need for
multi-year evidence with recency and aging. Infield surface/speed and outfield
geometry are not interchangeable park effects. This supports our visitor-defense
park separation, but does not establish that a single universal park coefficient
or an offensive park factor adequately adjusts defense.

[Colin Wyers (2010), comparing fielding methods](https://www.baseballprospectus.com/news/article/12399/manufactured-runs-how-do-you-solve-a-problem-like-derek-jeter/)
raises the problem of opportunity distributions and disagreement among defensive
measures. We should evaluate source coverage and measurement assumptions, not
equate agreement with another noisy metric to ground-truth skill.

### 2. Throwing and running are opposite sides of an opportunity

[Carruth and Jensen (2007)](https://arxiv.org/pdf/0705.3257) evaluate catcher and
outfielder arms using advancement opportunities, including holds as well as outs.
They use run-expectancy consequences and hierarchical shrinkage across four years.
Counting assists alone misses deterrence; caught-stealing percentage alone ignores
whether attempts happen. Their method motivates an opportunity denominator, not
a license to infer complete deterrence from incomplete attempt narratives.

[Lichtman's UBR primer (2011)](https://blogs.fangraphs.com/ultimate-base-running-primer/)
credits advancement relative to comparable base/out opportunities. Its connection
to outfield arm evaluation is particularly relevant to our crossed runner/fielder
model. The run value of a hold or advance depends on the situation; raw bases gained
and running speed are not equivalent to value.

[FanGraphs' BsR explanation](https://library.fangraphs.com/offense/bsr/) separates
steals, non-steal advancement and double-play avoidance. Our accepted running model
has the first two channels; it deliberately lacks a separate GIDP residual. We
must not silently claim a one-for-one reproduction of every public BsR component.

UBM implication: preserve separate steal propensity, steal success and advancement
channels. Future hitting/on-base opportunity and future running skill can be
dependent. Compare a fixed-rate-times-PA forecast with a direct future-run forecast,
using all starting players. Keep MiLB advancement as a diagnostic unless its MLB
translation earns value inclusion. Do not count both an omnibus running total
and its stolen-base subcomponent.

### 3. Catchers: separate participants, mechanisms and native run units

[Judge, Pavlidis and Brooks (2015), Moving Beyond WOWY](https://www.baseballprospectus.com/news/article/25514/moving-beyond-wowy-a-mixed-approach-to-measuring-catcher-framing/)
use crossed effects for pitcher, batter, catcher and umpire, with contextual
covariates. Their retro version can work without pitch-location tracking. This
is a relevant all-level idea, but an unlocated called-strike residual still needs
transfer and identifiability tests before we call it framing talent.

[BP's Catching Up (2016)](https://www.baseballprospectus.com/news/article/28193/prospectus-feature-catching-up/)
describes minor-league/retro coverage and participant-replacement calculations.
An effect estimated on the log-odds scale is not directly a run total: evaluate
the change in outcome probability in the same contexts and then value it.

[A Hierarchical Bayesian Model of Pitch Framing (2017)](https://arxiv.org/pdf/1704.00823)
uses participant/context effects and count-specific run values. A called strike
does not have the same consequence in every count, and a value estimated among
taken pitches differs from one including swinging strikes. Our battery walk
residual must not be added on top of framing or pitcher command without checking
overlap. Existing battery results do not yet support such an addition.

[BP's errant-pitch review (2015)](https://www.baseballprospectus.com/news/article/27849/prospectus-feature-passed-balls-and-wild-pitches-getting-it-right/)
distinguishes passed-ball and wild-pitch mechanisms instead of treating their sum
as pure catcher ability. That supports our decision to reject weak all-level
blocking residuals rather than manufacture a catcher adjustment from them.

MLB approved an ABS challenge system for 2026 in September 2025.
[Dated announcement](https://www.mlb.com/amp/press-release/press-release-mlb-announces-abs-challenge-system-coming-to-the-major-leagues-beginning-in-the-2026-season.html)
Our inference: traditional framing persistence is a rules-dependent scenario,
not an unconditional guarantee. Full ABS implies no umpire-call framing credit;
challenge ABS does not imply zero framing. We will not fit an arbitrary reduction
from 2026 results, invent a full-ABS adoption date, or relabel challenge decision
skill as already measured. Throwing and blocking remain separate.

### 4. Position is usage, not an extra defensive talent score

[FanGraphs positional adjustment](https://library.fangraphs.com/misc/war/positional-adjustment/)
prorates a fixed relative-position schedule by actual use. This accounting is
distinct from performance relative to other fielders at that position. A catcher
label alone should not grant a full season of positional credit. Future DH use,
time at multiple positions, and moving off a position matter.

UBM implication: use the successful one-year position-share architecture as a
benchmark, but reconstruct its coefficients at each historical cutoff. Test direct
Year-2/3 destinations or defensive exposure rather than repeatedly applying one
transition table without validation. Train conditional role models on observable
future roles, then evaluate expected value on the full starting population with
non-arrivals retained. Never select future MLB arrivals as the whole-model cohort.

### 5. Aging and multi-year dependence

[Tango's aging discussion](https://tangotiger.net/archives/artAging.shtml) explains
why pooling different players at different ages and retaining only players with
substantial consecutive-year playing time can distort aging estimates. Matched
survivors are not a random sample. Defensive decline, position change and losing
playing time need not be separate independent events.

Our inference: fit distinct horizons using mature labels and retain zero MLB
production in unconditional tests. Use source-only age/level/exposure features and
regularization. Do not impose an unsupported universal decline curve, count 2020's
missing MiLB season as zero skill, or interpret absence as permanent retirement.

Outside baseball, [Hyndman and Athanasopoulos' forecast reconciliation](https://otexts.com/fpp3/reconciliation.html)
uses forecast-error covariance to combine related totals and components coherently.
This motivates estimating how component errors interact on earlier out-of-time
predictions. It does not justify forcing a partial player cohort to sum to a full
league WAR target, or forcing uncertain component skills to zero because a noisy
batting forecast dominates total error. Our integration gate should require clear
component benefit and rule out material total-value harm; an uncertain tiny total
gain should remain explicitly provisional, as in the earlier running decision.

## Existing UBM work: what to recover, what not to repeat

| Piece | Recovered result | What it authorizes now |
| --- | --- | --- |
| Position-share transition | `position-role-2025-confirmation-result.json`: confirmed one-year shares; threshold 0.65 | Reuse architecture, refit dated transitions; not automatic three-year confirmation |
| Prospect position history | `prospect-shortstop-retention-result.md`: conditional MLB role improved, some positions worsened; later history confirmation withheld | Mandatory comparator/diagnostic, not a catcher haircut or universal promotion |
| Steals | `player-value-v1-steal-projection-selection-result.json`: B2_k5 attempt and B2_k45 success passed | Retain separate mechanisms and level/environment adjustment |
| Advancement | `player-value-v1-advancement-projection-selection-result.json`: A2_k25 passed | Strong one-year MLB component; horizon extension needs testing |
| One-year running integration | `hitter-clean-slate-model-v2-milestone.md`: component 0.0745→0.0592 WAR RMSE; total gain small/uncertain | Provisional additive component, not independent proof of full-WAR gain |
| Direct public catcher | Same milestone: component 0.0976→0.0861; total improved in three years, interval crosses zero | Conservative provisional one-year component; separate framing/rules exposure |
| Defensive exposure | Same milestone: 2025 exposure 449→375 outs RMSE | Reuse exposure architecture; it did not rescue the old skill bridge |
| General defense | Old standardized-success-rate/run bridge worsened total value | Keep original production neutral; new native-run test is a different hypothesis |
| MiLB infield/outfield range | RE24 ratings repeat; MLB value bridge failed | Keep ratings/coverage for diagnosis, do not automatically add MLB runs |
| MiLB runner | RE24 signal and advancement component improved; total value slightly worse | Diagnostic and candidate evidence, not an already accepted WAR addition |
| Catcher deterrence/blocking | Both tested; absent or tiny uncertain predictive gains | Closed absent materially better source/denominator |
| Catcher battery support | Walk signal, but new-pitcher transfer uncertain and DIPS value failed | No game-calling WAR; avoid double counting |

Scope warning from the code audit: the older chronological position-value script
loads one frozen transition table trained through 2024 even for earlier origins.
Likewise the standardized defense bridge loads 2022–24 conversion parameters.
The 2025-only confirmations keep their scope, but those fixed tables are not
cutoff-specific historical refits. New multi-year tests must reconstruct their
own earlier-only transformations or use fixed, genuinely exogenous accounting.

## Source improvements identified before fitting

The older general-defense value target has only 256 player-position rows in 2025.
The public native fielding-run leaderboard provides over 600 player rows per
recent full season, including separate range, arm and catcher components. This
is a meaningful measurement/coverage change, not another weight search over the
same failed target. Native labels are still estimates, not observed true talent.

MLB describes native defensive components on a common run scale, with complete
fielding-run coverage beginning in 2018. [Definition](https://www.mlb.com/glossary/statcast/fielding-run-value)
Source inspection independently finds blocking absent in 2016–17 and first-base
receiving absent before 2021. Never treat a missing entire component-year as zero.
All new requests specify completed years no later than 2025. Yearless responses
require identity/exposure and cross-year fingerprint checks before use.

The current all-level fielding cache covers selected older origin years and
2021–25, not every intermediate year. Missing historical fielding remains a
coverage flag; a primary-position label or MiLB PBP first-touch record is not an
invented innings total. Older current-rate tables that contain 2026 evidence are
not reusable as pre-2026 forecasts.

## Review limits and decisions

Some BP full pages deny automated access; descriptions above use the indexed
primary-source text, not inaccessible proprietary equations. Academic methods and
the relevant derivations/limitations were checked in the author papers. Search
results for ABS incidentally surfaced current-season snippets; these are excluded
from every predictor, outcome, model choice and numerical scenario. No protected
2026 evaluation data or leaderboard was requested or scored.

Next: certify native labels and coverage, freeze the bounded horizon/component
comparison, test it, then assemble the versioned player explorer. Do not delay
delivery for a speculative full career simulator or make every failed historical
idea a fresh candidate. Neutral and missing are visibly different in the UI.
