# Hitter model status and the next useful work

2026-10-05. We have a reproducible, evaluated next-year hitter research model.
We do not yet have a finished universal player-value model. The later research
has identified useful component information, but has not earned replacement of
the selected combined forecast. Keep the selected model and its completed 2026
evaluation unchanged. The immediate work is to diagnose prospect evidence and
readiness, not restart an algorithm tournament.

This review follows the [locked review scope](hitter-candidate-readiness-review-contract.md).
The [machine receipt](../reports/model-evidence/hitter-candidate-readiness/report.json)
checks provenance without fitting, rescoring or changing forecasts.

## What the selected model actually does

The model estimates next calendar year's MLB hitting ability, chance of playing,
and playing time if the player appears. It multiplies the resulting expected PA
by hitting value plus a fixed replacement allowance. A prospect can have useful
future ability but little expected MLB contribution next year. That distinction
is necessary; it does not establish the prospect's eventual upside or market value.

| Part | Selected construction | Important limit |
| --- | --- | --- |
| Prospect hitting | Regularized linear model with 220 inputs, including level history, translated events, dated scouting and profile inputs | The translation is not fully park and opponent neutral; thin elite and very young profiles have limited MLB-outcome support |
| Previously debuted hitter with MLB tracking | Regularized linear model with 262 inputs, adding MLB Statcast measurements | Availability differs across players and years; minor-league tracking is not an approved addition |
| Previously debuted hitter without tracking | Regularized linear model with 199 inputs | Less direct information about contact quality |
| Chance of MLB playing time | Histogram gradient-boosted trees with 251 inputs | Roster/status and ranking vintages are qualified; an absence can resemble an exit |
| PA conditional on appearing | Separate histogram gradient-boosted trees with the same 251 inputs | Conditional workload and arrival can both be wrong, even when their product looks close |

The 199-input history includes 98 pooled event-rate fields: seven MLB and 91
non-MLB fields. An older descriptive inventory called these 105 minor-rate
fields; the appended audit corrects that count. Do not infer omitted information
from that obsolete description. The rate models use fixed units rather than a
learned standardization step, and training weights include uncapped future PA.

The [incumbent audit](hitter-incumbent-representation-review.md) and new readiness
check establish that all five **ordered** feature lists match the frozen package.
Settings and model families agree for all 175 historical and 25 frozen heads.
The historical and 2026 coefficients are not identical: their training dates and
training populations differ. The frozen construction includes the documented
2020-source membership correction and 2025 source checks. Matching names or
feature counts alone would not have established this connection.

## What the completed comparisons support

The later event/count representation has 123, 132 and 186 inputs in its three
hitting routes, not the selected model's 199, 220 and 262. It is a different
research construction. Seven restored MLB event inputs improve that construction
against its own predecessor. They do not establish that it should replace the
stronger selected assembly.

On the same 30,506 historical forecasts, with the same PA and compatible targets:

| Hitting construction | Hitting error per 600 PA | Delivered contribution error |
| --- | ---: | ---: |
| Current incumbent | 1.8048 | 0.43513 |
| Research model with seven restored MLB inputs | 1.7992 | 0.43537 |
| Same research inputs without an imposed hitting baseline | 1.8066 | 0.43586 |

Lower is better. Hitting error weights actual MLB PA; delivered error includes
every forecast, including non-arrivals, and gives each origin equal weight.
The restored research model improves hitting and average absolute contribution
error, but its squared contribution error is a small, uncertain loss. Removing
the fixed baseline does not improve the combined forecast. These historical
years have been repeatedly used in development; nominal intervals are not fresh
confirmation. Preserve these distinctions instead of calling everything a win
or rejecting the value of detailed baseball information.

The older playing-time reports contain contribution errors around 0.4534.
They used a different scoring reference. The compatible ledger above is around
0.4351. That difference is **not** a newly earned improvement. PA quantities can
be compared across those reports where their membership and definitions match;
their contribution errors cannot simply be placed on one leaderboard.

## Playing time tests that are already finished

Each of the following has a completed player review. Do not repeat it unchanged
or interpret its result as rejecting every version of the broader idea.

| Completed comparison | What it supports | Decision |
| --- | --- | --- |
| [Fresher prospect rankings](hitter-preseason-readiness-v68-result.md) | A clearer upper-minors readiness improvement over the older source | Included in the selected research recipe, with publication-date limits |
| [Deeper trees and LightGBM conditional PA](hitter-positive-workload-capacity-result.md) | More flexibility worsened overall workload and contribution errors | Keep the shallower head; close this capacity comparison |
| [Separate entrant workload training](hitter-prospect-workload-specialization-result.md) | Removing established players from training did not improve the matched candidate | No specialized replacement or blanket prospect PA boost |
| [Hitting estimate added to opportunity](hitter-talent-opportunity-result.md) | Tiny uncertain gains; arrival scores slightly worsened | Do not add this encoding as a demonstrated improvement |
| [Available-season history](hitter-available-season-history-result.md) | Better arrival scores, including useful pandemic-history behavior; negligible uncertain contribution gain | Keep as qualified research, not a 2021-only adjustment |
| [Smooth model with fresher ranks](hitter-smooth-preseason-v73-result.md) | Better than its own older-source version, not a clear combined winner over current trees | Keep the current trees; close the exact comparison |
| [Complete employment correction](hitter-employment-comparison-v2-result.md) | Valid source repairs, but no demonstrated matched model gain | Keep the parser corrections, not a promoted refit |
| [Nonmedical observation inputs](hitter-nonmedical-opportunity-result.md) | All forecasts were identical because the trees never split on the tested fields | An uninformative predictive test, not evidence that availability is irrelevant |
| [Playing time uncertainty](hitter-workload-risk-result.md) | Useful spread around fixed means in some populations | Qualified workload-risk research; it cannot repair readiness means |

The older [rich workload result](hitter-conditional-workload-v1-result.md) is not
disproved by the newer separate-training failure. They changed different inputs
and training populations. The [membership clarification](hitter-prospect-workload-specialization-legacy-clarification.md)
found zero active-training overlap with its never-debut queries; missing explicit
exclusion was not proof of contamination of that primary prospect result.
Different targets, feature provenance and incomplete modern player walks still
prevent silently importing it into the selected model.

## What still prevents completion

Historical upper-minors players without a prior MLB debut receive 74,239 PA
against 92,891 actual. Lower-minors players instead receive 7,055 against 5,194.
The whole cohort receives 1,228,733 against 1,270,493. These are sums across
seven historical forecast origins, not a single-season league budget. A blanket
prospect multiplier would push the already-overallocated lower group the wrong
way. Aggregate agreement among actual debutants' conditional PA also hides large
errors in which players arrive and how their workloads are distributed.

On 2,627 matched public forecasts, current PA error is 138.33 versus Steamer's
135.38; average absolute error is 106.41 versus 92.08, about 15.56% worse. The
complete employment arm gets average error to 105.28, inside the old 15% working
allowance, but does not improve the combined forecast convincingly. That threshold
is a diagnostic target, not a magic boundary between good and bad models. The
meaningful readiness/allocation and source gaps matter more than arguing over
a fraction of a percentage point. Public rate conversions and information dates
remain qualified; ordinary ZiPS talent-only PA is not unconditional playing time.

The player walks make these problems concrete. Historical Kurtz gets about ten
expected PA before 489, and Alvarez gets 72 before 369; pedigree is already
present, so saying merely "add scouting" misses the question. Tatis gets about
forty before 635 after an absence, despite preserved hitting ability. These need
evidence and support checks, not manual player boosts. Belt's 244 before zero is
an unusual employment outcome after good production, not evidence that every
unsigned productive veteran should disappear. Refsnyder's almost exact research
contribution combines opposing PA and hitting errors; a close final number is
not automatically a sound forecast. Full walks and unsuccessful peers remain in
the linked reports, including the [twenty latest cases](hitter-absolute-rate-player-review.md).

Foreign entrants and returns do not have universal coverage. Missing forecasts
are unknown, not predictions of zero. Low-level hitting estimates also require
care: a teenager's immediate non-arrival does not validate an unsupported MLB
ability estimate or disprove eventual star upside. Joint hitting/workload risk,
well-supported later horizons, fielding, running, catcher and positional value,
contract/control years and trade value have not been completed by this next-year
batting test. Existing component research must be reconciled separately, not
silently bolted onto its mean.

## The 2026 evaluation is already complete

The user-authorized evaluation occurred once, after the candidate was frozen in
commit `e661958`. This review verifies that the completion receipt identifies the
same forecast and freeze hashes, and that scoring followed freezing. All 53
frozen package files are unchanged. It reads existing completion metadata, not
raw outcomes or a new score. The earlier verifier's "not yet evaluated" flag
describes when that file was written; it is not current status.

The [completed evaluation and its qualifications](hitter-final-2026-result.md)
remain authoritative. It did not establish superiority to a matched public
system and did not authorize full-model deployment. Do not reevaluate or tune
the same 2026 candidate. Any later model work treats the exposed season as
development evidence, not a second protected test. The separate
[team-filtered explorer](hitter-final-2026-explorer.md) remains unchanged; this
review has not reverified its live browser/server state.

## One coherent next action

Keep the selected recipe and evaluated forecast as references. Close the
representation/offset sequence without a subgroup hybrid or more offset tuning.
Next audit **historical source exposure and actual training support** for thin
high-pedigree entrants and established upper-minors hitters. Map the prior rich
workload and cross-level tests before proposing a fit; do not assume these ideas
are new. Distinguish a late-season cameo from sustained experience, and genuine
absence from missing history, using dated counts and games already captured.
Follow those records through the selected hitting and opportunity inputs and
saved paths, with unsuccessful peers retained.

That audit must establish a concrete, nonduplicative representation defect or
support gap before any replacement is fitted. Then permit at most one bounded
historical repair on the unchanged original population, with established-player
benchmarks, arrivals and non-arrivals, origin/cohort totals and complete player
walks. If no fixable defect is demonstrated, stop rather than manufacture another
feature trial. Entrant coverage and a genuinely comparable public benchmark
remain separate release requirements. Team record, new college collection,
algorithm tournaments and individual prospect multipliers are not in the queue.

The practical hitter goal remains active. This review improves the decision
record and prevents repeated tests; it does not change forecasts or claim an
accuracy gain.

Verification: 51 focused tests pass, including feature order, mismatched forecast
hashes, evaluation timing, retuning and incomplete player-review guards. Both
freeze verifiers pass: 53 files and 4,030 players in the selected package, and
31 files and 3,907 players in the legacy package. An initial test command named
a nonexistent test file and collected no tests; the corrected complete command
passed without any model or evidence change. These are execution checks, not
new predictive evidence.
