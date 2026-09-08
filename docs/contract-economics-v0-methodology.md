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

The free-agent market price, discount rate and arbitration shares are explicit caller
assumptions with their own model IDs. v0 deliberately has no built-in dollar-per-WAR
answer. Publishing a default before an ex-ante market fit would create false precision.

## Implemented states

- `guaranteed_contract`: salary is unavoidable and bad performance remains a liability.
- `pre_arbitration`: known salary or the applicable CBA minimum; the club may tender or
  non-tender.
- `arbitration` / `arbitration_eligible` / `super_two_eligible`: known salary when
  available, otherwise a transparent configured share of free-agent-equivalent value,
  never below the applicable minimum; the club may tender or non-tender.
- `club_option`: the club chooses the better of exercising or declining and paying the
  stated buyout.
- `player_option` / `player_opt_out`: the player is assumed to choose the branch that is
  worse for the club, exposing the adverse optionality.
- `free_agent` / `free_agent_eligible`: free-agent-equivalent production is still shown,
  but the incumbent club owns no control value.
- `mutual_option`, `vesting_option` and unknown states: no value is invented. They enter
  review until the trigger or negotiated decision model exists.

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
2. a chronologically fitted free-agent market function using information available at
   signing time;
3. an internal historical arbitration dataset and chronological validation;
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

