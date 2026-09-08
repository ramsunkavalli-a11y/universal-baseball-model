# StatsAPI team-control methodology

**Status:** CBA calculation layer, conservative StatsAPI transaction materializer and
batched official opening-state construction implemented; contract join and broad
historical validation remain open.

## Decision

Official MLB roster, person, schedule and transaction responses are the scalable
source for player identity, organization candidates, dated roster states and the
inputs to CBA calculations. FanGraphs and other sources are reserved for contract
terms and bounded exception checks. A missing or ambiguous history receives a review
flag; it is not silently treated as zero service or unused options.

## Implemented rules

`team_control.py` accepts inclusive, dated roster-state intervals and official season
windows. It unions overlaps before applying these published rules:

- MLB active-roster and MLB injured-list days earn service, capped at 172 per season;
- explicitly excluded suspension days do not earn service;
- 20 optioned days use one option year, with at most one charged per season;
- the fourth-option test uses the published 90-day full-professional-season rule;
- Rule 5 timing uses five protection seasons for players signed at age 18 or younger
  and four for players signed at age 19 or older;
- three service years trigger standard arbitration eligibility and six trigger
  statutory free-agency eligibility;
- Super Two is calculated only when the input is explicitly marked as a complete
  league-wide pool. A team-only input produces a reviewable candidate, never an
  invented cutoff. The league calculation uses the top 22% of the eligible
  two-to-three year pool with at least 86 days in the latest season.

The output includes service in `Y.DDD` form, used/allowed/remaining option years,
professional seasons, Rule 5 year/status, statutory eligibility, the Super Two cutoff,
confidence and explicit review reasons.

## Source boundary

StatsAPI person `rosterEntries` are fetched in bounded batches and interpreted by
`roster_entry_source.py` at each official season opening. A more recent, specific
rehab, injured or minor-league entry takes precedence over a broad older MLB entry;
unknown or conflicting entries go to review.

The opening state and transaction history are converted into dated intervals by
`control_events.py`. Its versioned
grammar accepts specific option, recall, call-up, selection, outright, release and MLB
injured-list events. Rehab assignments preserve the existing MLB injured-list state.
Generic descriptions such as `roster status changed` remain in a review queue and do
not change the state. The replay starts from a dated official opening roster snapshot;
if none exists, it starts only at the first specific transition and does not invent the
earlier part of the season. Historical coverage gaps, grievance/service awards,
fourth-option rulings and Super Two cutoff ties remain bounded review cases.

The later payroll join owns guaranteed salaries, contract years, club/player/mutual
options, opt-outs, buyouts, retained/deferred money, incentives and no-trade clauses.
Those terms may override the statutory path but never rewrite the underlying CBA
calculation.

## Phase-one completion gates

1. Materialize a full MLB organization from `fullRoster`, people roster entries and
   transactions using saved source captures.
2. Compare calculated service, options and Rule 5 results with the Padres FanGraphs
   depth-chart sample; use differences to improve general rules or create narrow
   exceptions.
3. Run the service/Super Two calculation league-wide before assigning a cutoff.
4. Import the 30 team payroll files and overlay only unique contract terms.
5. Publish coverage, ambiguity and exception counts beside every result.

## References

- MLB Service Time glossary: https://www.mlb.com/glossary/transactions/service-time
- MLB Minor League Options glossary:
  https://www.mlb.com/glossary/transactions/minor-league-options
- MLB Rule 5 Draft glossary: https://www.mlb.com/glossary/transactions/rule-5-draft
- MLB Salary Arbitration glossary:
  https://www.mlb.com/glossary/transactions/salary-arbitration
