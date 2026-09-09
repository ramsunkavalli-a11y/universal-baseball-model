# Contract Economics v0 methodology

**Status:** frozen implementation boundary for the first static annual economics
layer. This layer is downstream of projection, playing time and WAR. It must not alter
those upstream estimates to make contract values look reasonable.

## Purpose and separation

Contract Economics v0 keeps four quantities distinct:

1. projected on-field WAR;
2. free-agent-equivalent value of that WAR;
3. value of the actual contract and team-control rights; and
4. later trade value, which is outside this module.

The annual calculation is:

`free-agent-equivalent value - actual or modeled salary cost`

The result is then adjusted only for a legal decision attached to the current control
state. Contract status is never a multiplier on WAR.

## Existing inputs

The repository already provides:

- official StatsAPI player, roster, 40-man, service and transaction evidence;
- a dated FanGraphs opening service/options baseline with source hashes;
- league-wide Super Two and future control paths;
- 915 resolved FanGraphs payroll identities, 3,720 annual terms, 180 clauses and
  417 other payments; and
- separate player-value and uncertainty components that can eventually supply the WAR
  input after their integration is validated.

FanGraphs remains a snapshotted contract source, not an infallible authority. MLB's
2022–2026 Basic Agreement is the authority for the versioned minimum salaries. The
ruleset ends after 2026; a future CBA must be a new ruleset, not a silent edit.

## Required annual input

Each row represents one player, organization and season and supplies:

- dated player and organization IDs;
- projected WAR mean and optional lower/upper estimates;
- the contract/control state;
- known salary when available;
- buyout when an option is modeled;
- arbitration class when salary must be approximated; and
- projection and contract source IDs.

For in-season use, rows must first pass through the remaining-rights timeline. Current-
season projected WAR means only production after the as-of date, and known salary means
only the unpaid/transferred obligation. Already-produced WAR and already-paid salary do
not enter trade value. `current_season_committed` prevents an in-season row from
receiving a fictional offseason non-tender option.

The free-agent market price, discount rate and arbitration shares are explicit caller
assumptions with their own model IDs. The accepted 2026 market reference is now the
published FanGraphs three-tier curve: under 1, 1–2 and 2+ full-season projected WAR.
Future tier growth remains a named scenario. A flat rate remains supported for
sensitivity work; a current rest-of-season estimate cannot select a full-season tier.

## Implemented states

- `guaranteed_contract`: salary is unavoidable and bad performance remains a liability.
- `current_season_committed`: remaining current-season salary is valued as committed;
  already-earned production and paid salary are outside the row.
- `pre_arbitration`: known salary or the applicable CBA minimum; the club may tender or
  non-tender.
- `arbitration` / `arbitration_eligible` / `super_two_eligible`: known salary when
  available, otherwise a transparent configured share of free-agent-equivalent value,
  never below the applicable minimum; the club may tender or non-tender. The Phase 1
  FanGraphs shares are 15%/35%/50%/75% for classes 1–4 and apply to prior-season WAR
  value so salary responds with the correct one-year lag.
- `club_option`: the club chooses the better of exercising or declining and paying the
  stated buyout.
- `player_option` / `player_opt_out`: the player is assumed to choose the branch that is
  worse for the club, exposing the adverse optionality.
- `mutual_option`: Phase 1 uses the normal expiration outcome and charges the stated
  buyout. At one fixed exercise price, the player and club generally prefer opposite
  branches; the model does not invent a negotiated extension or valuation disagreement.
- `free_agent` / `free_agent_eligible`: free-agent-equivalent production is still shown,
  but the incumbent club owns no control value.
- `vesting_option` and unknown states: no value is invented. They enter review until the
  trigger model exists.

A dated review-only overlay can block a player-season when reliable sources disagree
about its legal option structure or when multiple years share one linked decision.
These records add provenance and a specific review reason; they never overwrite the
primary contract/control source. Adding a salary or buyout later does not remove the
block. The structure must first be reconciled explicitly.

A separate narrow correction overlay is allowed only for stronger, dated evidence
such as official MLB reporting. Every correction names the expected prior status and
fails if that status has changed, so a stale exception cannot silently survive a
future primary-source refresh.

For tender and option states, `optionality premium` is the modeled control value minus
the value if the salary/exercise branch were an unavoidable guarantee. It can be
positive for club rights and negative for player rights.

## Discounting and uncertainty

Nominal annual values are discounted to the snapshot year with an explicit annual
rate. The rate is an economic timing assumption, not an extra performance-risk haircut.
Optional WAR bounds are passed through the same monotone market curve and decision
rules as sensitivity bounds. They are not labeled probabilities.

v0 does not claim a stochastic multi-year present value. A later version must accept
correlated player paths and use information available at each decision date; it must
not give the club perfect hindsight over a simulated career.

## Fail-closed rules

- Duplicate player/organization/season rows fail.
- Missing market assumptions, unsupported future CBA minimums, invalid arbitration
  classes and missing option buyouts enter review or fail before aggregation.
- Known guaranteed salaries are not replaced by arbitration or minimum estimates.
- Player options are not treated as club options.
- Free agents do not receive incumbent-club control value.
- CBT, team budget, trade demand and package balancing remain outside v0.

## Source and model gaps

The engine can be implemented now, but a league-wide dollar ranking should wait for:

1. a validated multi-year whole-player WAR surface covering hitters, pitchers,
   prospects and inactive/no-history players;
2. post-2026 market growth and successor-CBA assumptions beyond the accepted 2026
   FanGraphs tier reference and the independent one-year signing-time scale check;
3. an internal historical arbitration dataset and chronological validation beyond
   the externally tested FanGraphs Phase 1 baseline;
4. player-ID-linked buyouts and correct effective years for opt-outs; and
5. correlated future performance paths for probability-weighted option decisions.

Until then, the output is a transparent research baseline under named assumptions, not
a trade-value product.

## Sources

- MLBPA, *2022–2026 Basic Agreement*, Article VI(A), minimum salary schedule:
  https://www.mlbplayers.com/_files/ugd/4d23dc_d6dfc2344d2042de973e37de62484da5.pdf
- MLB, service-time and arbitration definitions:
  https://www.mlb.com/glossary/transactions/service-time
  and https://www.mlb.com/glossary/transactions/salary-arbitration
- FanGraphs, 2026 free-agent dollars-per-WAR method and three-tier result:
  https://blogs.fangraphs.com/what-are-teams-paying-for-a-win-in-free-agency-2026-edition/
- FanGraphs, 2026 arbitration-share baseline:
  https://blogs.fangraphs.com/the-details-of-our-new-prospect-valuation-methodology/
