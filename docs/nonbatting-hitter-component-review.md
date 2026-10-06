# Nonbatting hitter value: keep useful work, fix the boundaries

2026-10-05. This is the completed literature/component-review checkpoint for
[the milestone](nonbatting-hitter-milestone-plan.md). It does not declare a
full hitter model or six years of club control finished. The current 8810 explorer
and selected 4,030-player 2026 freeze remain **batting plus replacement only**.
Older 3,907-player partial WAR and newer component research are different packages.

## What should be kept

| Part of value | Useful existing recipe | What its evidence actually establishes | Current decision |
| --- | --- | --- | --- |
| Stealing | Attempt and success models with shrinkage; selected B2/k45 recipe | Separate opportunities from conversion; historical future-value component evidence | Keep as research baseline; do not repeat its weight search |
| Taking extra bases | Opportunity-based advancement; selected A2/k25 | Existing MLB running histories help the Years 1–3 component benchmark | Keep; joint opportunities/GIDP and later-horizon support remain open |
| Position | Actual position shares, chronology-fitted transitions and positional run schedule | Position is distinct from fielding quality; direct position-history test improved squared error | Preserve observed role/history; repair the interpretation of the old failure, not its sealed result |
| MLB range/arm/DP | Regressed native histories; old tracked/universal Defense handoff | MLB skill measures have real near-term information; old standardized range test beat zero slightly | Keep distinct benchmarks, not an automatic add-on to the current batting mean |
| Minor range | Complete ground-ball ledger; old universal traditional-fielding U1 | Source availability, some persistence and limited transport—not all-level future-MLB skill | No newly promoted minor-range adjustment; retain missing/support uncertainty |
| Catcher throwing/blocking | Repaired C2 source/model handoff; separate component labels | Older 2025 standardized MLB confirmation improved MSE about 11%/16% on 79/78 catchers | Keep repaired research recipes; do not confuse those gains with full WAR or proof of minor transfer |
| Framing | Repaired tracked MLB F1; regressed native scenario | Older MLB confirmation improved standardized MSE about 35% on 48 catchers | Keep MLB research evidence; use explicit rule scenarios, no fixed six-year framing bonus |

The original catcher result selecting C1/no blocking is superseded by the repaired
C2 results. The original closed-framing result is superseded by repaired MLB F1;
minor framing remains unsupported. This reconciliation avoids relaunching a
source-defective old search or discarding the later winner.

Sources: [Defense handoff](player-value-v1-defense-production-handoff.md),
[range confirmation](defense-v1-2025-confirmation-result.json),
[catcher repair](defense-v1-catcher-repair-2025-confirmation-result.json),
[framing repair](defense-v1-framing-2025-confirmation-result.json),
[Years 1–3 component study](multiyear-hitter-components-v1-result.md).
Older confirmation cohorts have not been globally recertified under today's
mandatory player-review rules. Their positive evidence is worth retaining, not
a license to bypass current integration checks.

## An older "failure" that needs a more sensible interpretation

The [position-history confirmation](prospect-position-history-confirmation-result.json)
lowered position RMSE 0.17606 → 0.16870 and position-adjusted partial-WAR RMSE
0.70670 → 0.70395. It was withheld under a predeclared absolute-total-bias rule:
partial-WAR bias changed -0.014861 → -0.014938 per player. That is a worsening
of about 0.000077 WAR per player, roughly 0.25 WAR across 3,291 prospects.
The component bias itself improved. Its contract explicitly did NOT allow MAE
to veto a mean forecast.

Keep the original decision intact. But do not report this as position history
failing to improve projections, or make fielding neutral because the role model
"failed." Future integration needs economically meaningful total-calibration
tolerances alongside uncertainty and player checks, not a zero-tolerance bias
veto. One older cohort spanning the short 2020 season still does not establish
universal future-role accuracy.

## What the defensive literature suggests

The accessible foundational work offers measurement ideas, not a ready-made
validated DSL-to-MLB projection system.

1. **Estimate opportunities, not just errors/assists.**
   [Smith's original Total Zone](https://tht.fangraphs.com/measuring-defense-for-players-back-to-1956/)
   allocates estimated opportunities when exact responsibility is unavailable.
   [The revision](https://tht.fangraphs.com/measuring-defense-for-players-back-to-1956-part-2/)
   distinguishes park/handedness/pitcher and baserunner context, and notes plausible
   extra adjustments did not clearly improve agreement. This directly exposes
   UBM's earlier through-hit omission, but does not prove the repaired proxy
   will forecast MLB skill.
2. **Pool sparse players toward position peers.**
   [Bayesball](https://arxiv.org/abs/0802.4317) uses spatial evidence and shared
   information across fielders. The lesson for UBM is partial pooling and honest
   uncertainty—not pretending public scorer coordinates contain true starting
   positions. [Lichtman's primer](https://blogs.fangraphs.com/the-fangraphs-uzr-primer/)
   supports combining multiple years and regressing noisy measurement. In UBM,
   cohort support and exposure must accompany a numerical rating.
3. **Arms need holds, advances AND outs.**
   [Carruth/Jensen](https://arxiv.org/abs/0705.3257) pool throwing estimates across
   opportunities. [Marchi's minor-league application](https://tht.fangraphs.com/cannons-in-the-bushes/)
   uses runner/base situations rather than assists alone, while explicitly
   leaving regression, parks and MLB translation unfinished. UBM can extend
   runner-state extraction to outfielder arms, but first needs opportunity/
   attribution certification; an impressive assist total is insufficient.
4. **Tracking improves the description of difficulty, where coverage permits.**
   [OAA's official description](https://www.mlb.com/glossary/statcast/outs-above-average)
   requires movement/time/starting-position information. UBM's public EV/LA and
   fielder-ID columns do not by themselves reproduce that geometry. This is
   our data-interface inference, not a claim that Statcast is unhelpful.

MLB's [2024 release](https://www.mlb.com/news/minor-league-statcast-data-compared-to-mlb)
described full Triple-A coverage from 2023, partial earlier coverage and selected
Florida State League parks. That is historical release coverage, not a verified
2026 inventory. Our existing 2024 probe transported AAA/FSL tracking, but its
minor-to-MLB fitted transfer gate had ZERO eligible players. It was insufficient,
not a demonstrated predictive loss. Generic OAA links in Savant navigation do
not establish that public minor-league OAA exists for our requested population.

The sensible tracking route is to inventory actual linked historical balls,
available difficulty fields and matured MLB fielders, then compare richer versus
coarse measurement on the SAME players/balls. Missing tracking must remain a
coverage flag. Do not label a homemade EV/LA model "minor OAA" or use a full
minor season for one arm and a tracked one-week subset for another.

## What the new bounded test found

The [complete-exposure play-share comparison](minor-infield-play-share-result.md)
tested a new coarse measurement against native future MLB range, rather than
subsequent minor-league scorer statistics or offsetting a batting error.
It is not a model upgrade: delivered RMSE changes only 0.014% and the interval
crosses zero; conditional weighted error worsens. Witt/Peguero improve, Peña/
Mayer are missed, Edwards worsens, and Rafaela's tiny "gain" mostly concerns
future outfield value. All models/inputs replay and 13 player-origins are walked.

Recent A/rookie starters provide ZERO substantial next-year MLB infield labels.
Therefore this is a useful near-term value test but not a sufficient test of
their eventual defensive talent. Changing the endpoint to five years without
auditing mature chronological training support would repeat the earlier long-
horizon mistake. Do not tune this play-share recipe or declare lower-minor
defense impossible. Future role, pitcher contact mix, positioning and scorer
differences remain concrete measurement/transport gaps.

## A coherent component layer still has to respect exposure

The central model boundary is:

    MLB participation/workload → future position exposure → position value
                                                       → range / arm / DP
                                                       → catcher-specific exposure
    runner opportunities → attempt / success / advancement → running value

Position value is not a reward for good defense. A catcher who does not catch
cannot receive a full catcher-season positional bonus. A hitter projected mostly
at DH cannot receive full-time range value. Catcher blocking uses at-risk pitch
opportunities; throwing uses distinct battery/runner situations; framing uses
eligible taken-pitch/rule context. Their historical skill denominators are not
interchangeable with projected PA or a generic "defense exposure" column.

The older component benchmark shrinks many defensive histories with batting
PA and scales them by expected PA. That is a delivered-runs-per-batting-workload
recipe, not pure fielding talent. It must not be silently advertised as a
per-inning ability model. The new experiment uses defensive outs for prior MLB
range; it does not solve the full future exposure map or replace the old package.

Avoid double-counting: range, arm, DP, catcher receiving/throwing/blocking,
position and running are separate ledgers. Confirm each source's overlap before
summing. Neutral adjustment for an unsupported prospect is a modeling fallback,
not proof of average defense or negligible uncertainty. Current-team filters
must not imply future roster rights. Six calendar seasons remain different from
six MLB service/control seasons.

## Next execution boundary, in order

1. **Catcher throwing/blocking population source gate.** Scale the already frozen
   event/time/exposure extractor to a predeclared historical population, retaining
   failed games and missing-event mass. The independent 128-game source sample
   passes; it is not enough to fit a league-wide skill model. Do not redo that
   sample or invent zero events for absent feeds. See
   [the existing exposure result](catcher-exposure-v1-result.md).
2. **One repaired all-level catcher comparison only after that gate.** Separate
   pitcher/runner/catcher context; target future MLB component outcomes, not just
   minor repeatability. Keep pickoff-CS separate. Blocking includes uncaught-
   third-strike risk with empty bases. Deterrence still needs nonpitch risk spells:
   attempts divided by pitches is not a complete all-attempt denominator.
3. **Common native-unit exposure integration.** Preserve current batting/PA
   predictions and component baselines. Compare additions against the same
   component target/PA/players before comparing their joint total. Require
   player/position walkthroughs and meaningful matched-total tolerances. Do not
   optimize a fielding conversion to cancel an existing batting miss.
4. **Longer-range minor ability and tracking gate.** Inventory mature cohort
   support, historical measurement definitions and linked tracked coverage before
   locking a transported-talent experiment. Use the coarse ledger for audit;
   don't reinterpret next-year rookie nonparticipation as talent failure. Existing
   old U1 is a benchmark to examine, not a new weight/algorithm search.

MLB history can support a starting nonbatting layer sooner than sparse lower-
minor talent can. That is a sensible staged delivery, not an excuse to publish
unsupported lower-minor precision. Years 1–3 findings have only two normal
complete three-year origins; Years 4–6 remain provisional. The earlier long-
horizon profile-support failures are not repaired by this milestone.

## Current disposition

Literature review, component reconciliation and one repaired-measurement comparison
are complete. A validated integrated nonbatting forecast is NOT complete. No
production predictions, explorer or completed 2026 evaluation changed. The next
work is the source/exposure boundary above, not another round of minor play-share
weights or an unrelated hitter opportunity experiment.
