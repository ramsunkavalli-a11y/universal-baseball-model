# Finish the 2027 hitter model v1

User-authorized scope, 2026-10-08. This plan supersedes the next-step ordering
in the October 8 stopping-point handoff, not its findings or frozen artifacts.
The deliverable is a working player-value model and explorer, not another
component-research handoff. The active goal stays open through release.

## Product and accounting

Project 2027 and subsequent seasons from information available at the dated
build cutoff. Keep talent, MLB opportunity, annual contribution and the value
of organization rights distinct. Show batting, stolen-base running, advancement,
fielding, catcher receiving/blocking/throwing, position, league/park adjustment
and replacement in runs; divide their sum by one explicit runs-per-win factor.
Show the same additive contributions in WAR. Do not call batting plus replacement
full WAR, add replacement twice, or add position-relative fielding to an
incompatible positional baseline. Park normalization inside batting must not
be applied again as an extra credit.

Every component gets a specified estimator, evidence tier and uncertainty
description. Use measured individual history when useful, a tested statistical
profile when transferable, and an explicit comparable-player estimate when
individual information is inadequate. An honest near-zero estimate is allowed;
fabricating individual differences just to avoid zero is not improvement.
Unknown measurements are not zero talent. Catcher framing under future rules is
an explicit rules scenario, not an assumption of unchanged value forever.
The 2026 source also reports ABS challenge runs separately from initial-call
framing; retain that separate component without claiming one season validates
lasting challenge skill.

Value belongs to rights in the player, not simply six calendar years of WAR.
Use existing service, salary, arbitration, option, buyout and liability work.
Update its date and replace its old projected WAR. Prospects have uncertain MLB
arrival dates; service can accrue on MLB IL without PA. Follow the remaining
control and guaranteed-payment tails beyond 2032 when necessary. Separate known
contract costs from projected costs. Guaranteed obligations survive zero playing
time and lost rights. Unresolved linked options remain visible with scenario
values, not fabricated exact net dollars. A hitter-only Ohtani projection cannot
be charged the entire two-way contract and called complete player surplus.

## Reuse map and remaining work

1. **Inputs and membership.** Reconcile the completed 2026 official counts with
   local September 28 FanGraphs/BP exports; acquire level-specific minor counts,
   current fielding/running measurements and dated roster/service updates where
   missing. FanGraphs' combined-level MiLB rows are not level-specific seasons.
   Preserve no-PA injured/suspended/unsigned players, new entrants and foreign
   professionals. Read existing archives in place and retain compact receipts.
2. **Batting and opportunity.** Start from the evaluated routed hitter model,
   not the older Phase 1 financial forecasts. Repair the documented sparse-sample
   translation defect (Lovich's 26 A-ball PA) in the actual predictor arithmetic;
   a reliability flag alone cannot fix it. Extend reusable source builders to
   the new origin with explicit dates, not year-renaming saved forecasts. Retain
   the existing tracking and non-tracking routes, pedigree, level and age inputs.
   Known absences affect availability separately from talent and role.
3. **Running and fielding.** Reuse the previously tested running estimators and
   corrected native range, OF reference, catcher opportunity and first-base
   recipes. Reconcile their exposure units with the new playing-time forecast.
   Check older/modern fielding compatibility before pooling them. Use a bounded
   age/position/minor-evidence model for unmeasured defenders only where future
   MLB quality support permits it; otherwise disclose the profile estimate.
   Do not restart closed weight searches or the team-record experiment.
4. **Annual paths and rights.** Reuse defensible aging, arrival and retention
   work after checking each horizon's training support. Do not revive the failed
   unsupported Year-6 fits or rejected donor-path forest as a validated model.
   Preserve coherent within-player paths for nonlinear pricing/option scenarios;
   point forecasts and unvalidated uncertainty must be labeled separately.
5. **Integration and release.** Assemble the component ledger, historical
   comparisons, named-player review, current organization/control valuation and
   a new team-filtered 2027 explorer. Keep the old explorer and forecasts intact.

Complete each component's source-to-player review before moving to the next
experiment. Prefer one justified repair and the strongest existing estimator
over a new algorithm tournament. A weak component does not justify endlessly
reopening all the others.

## Practical checks, fixed before new fits

- Historical development: keep the existing identity-locked evaluation cohorts;
  report 2023–25 separately and pooled, with earlier normal years where supported.
  Report 2021 as a COVID stress year, not the sole selection driver. The already
  opened 2026 season is additional development evidence, not a new blind test.
- Batting quality: future MLB rate on covered players, exposure-weighted and
  player-weighted. Defense/running talent: pooled future MLB quality per native
  opportunity on mature follow-up; non-arrivals have unknown quality. Delivered
  PA and full WAR: retain all eligible players, including exits and non-arrivals.
- Use unchanged matched identities and definitions against the current model,
  a simple recent-history/age baseline, and dated public projections where
  available. Compare public full WAR to full WAR; compare batting only to the
  same batting measure. Separate public-system coverage from all-minors coverage.
- Release thresholds are practical engineering limits, not significance claims:
  no more than 5% worse RMSE or MAE than the strongest eligible existing baseline
  on the primary matched target; at most 15% worse than the matched public system
  on either metric. Report the absolute errors and uncertainty, not just pass/fail.
  A breach requires an explained repair or a clearly restricted release scope.
- Investigate PA totals differing by more than 10% and batting/full-WAR totals
  differing by more than 15% from matched realized totals, using an absolute
  5-WAR floor for small groups. These are investigation triggers, not automatic
  rejection of a noisy small cohort. Show MLB incumbents, recent arrivals,
  upper minors, lower minors, age, position, evidence coverage and year.
- Separate the current-rights universe from future complete league rosters.
  Undrafted future entrants and future acquisitions are not allocated to today's
  organization. Do not scale every player to force league totals to look right.
- Walk through six to eight cases per experiment: gain, harm, false high, false
  low, ordinary case and focal failures, with outcome-blind comparison players.
  Fixed cross-model cases include Lovich, Eldridge, Concepcion, Judge, Tatis,
  Ohtani and a catcher/defensive specialist selected from source coverage.
  Keep failed cases in the review; no player-specific outcome-driven overrides.
- Block release for duplicate identities, future inputs, unsupported units,
  omitted components disguised as measured zeros, double counting, unreconciled
  sums, stale rights passed off as current, or truncated liabilities. Do not
  confuse these integrity tests with demonstrated predictive accuracy.

## Explorer acceptance

The first season is 2027. Filters include current organization, level/stage,
position and evidence tier. Each player shows annual expected PA, arrival/
retention probability, batting talent, each runs/WAR component and total WAR;
then controlled WAR, gross market value, expected salary/obligations, discounted
net value and contract/control assumptions. Clicking a component explains its
source, estimator, exposure and evidence quality. Display mean value separately
from upside/downside scenarios. Show source dates and incomplete-control/financial
cases plainly, without ranking incomplete subtotals as full net value.

Release requires verified calculations, historical and player reviews, browser
checks, a concise model card, and a checkpoint commit. Report what actually
changed and what did not work in ordinary baseball language. This document
alone, a source inventory, or accounting unit tests do not finish the goal.
