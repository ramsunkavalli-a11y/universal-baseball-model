# StatsAPI team-control methodology

**Status:** CBA calculation layer, conservative StatsAPI transaction materializer and
batched official opening-state construction implemented; contract join and broad
league-wide validation remain open. A dated baseline can now be advanced with
post-snapshot StatsAPI service and later option years.

## Decision

Official MLB roster, person, schedule and transaction responses are the scalable
source for player identity, organization candidates, dated roster states and forward
CBA calculations. FanGraphs or another verified service source supplies a dated
accumulated-service/options baseline where the retained StatsAPI history is incomplete.
It also supplies contract terms and bounded exception checks. A missing or ambiguous
history receives a review flag; it is not silently treated as zero service or unused
options.

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

Phase one uses official MLB season windows consistently for day arithmetic. A player
who appears to qualify for a fourth option is always flagged for a final check against
the applicable minor-league calendar. That small edge group is deferred rather than
claiming false precision from a single league calendar.

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
calculation. `contract_overlay.py` accepts a payroll row only after a stable ID match;
name-only and unresolved identities stay in a separate review table.

## Phase-one completion gates

1. Materialize a full MLB organization from `fullRoster`, people roster entries and
   transactions using saved source captures.
2. Compare calculated service, options and Rule 5 results with at least two FanGraphs
   depth-chart samples; use one team as the working sample and another as a holdout.
3. Run the service/Super Two calculation league-wide before assigning a cutoff.
4. Import the 30 team payroll files and overlay only unique contract terms.
5. Publish coverage, ambiguity and exception counts beside every result.

## Payroll sample result

The 2026 Padres payroll sample successfully normalized 38 player records, 146 annual
terms, 14 explicit option/opt-out clauses and 14 other payments. All annual values and
all recognized clause language parsed. Service-time values in this workbook remain
validation references only; they do not replace the forward StatsAPI calculation. Of
the 38 player contracts, 34 attached automatically through stable IDs. Four remained
in the identity review table: two name-only newer-player matches and two stable IDs
outside the current official candidate pool because the workbook lists them as no
longer on the 40-man roster.

## Depth-chart validation sample

The 2026 Padres depth-chart sample normalized 187 players: 186 FanGraphs IDs, 62
service-time references, 37 option counts, 33 Rule 5-eligible labels and 93 future
Rule 5 dates, with no unparsed control values. The pinned Chadwick snapshot directly
linked 54 players to MLBAM IDs. For validation only, unique accent-insensitive exact
name matching linked 182 of 187 depth-chart rows to the 295 StatsAPI `fullRoster`
candidates returned on 2026-09-08. The five unmatched rows form a small transaction
and identity exception queue. Name matching is never promoted to canonical identity or
ownership evidence.

### Historical-replay decision

A from-zero 2000–2026 StatsAPI replay was rejected as the accumulated-service source.
Among 54 Padres players joined by stable FanGraphs and MLBAM IDs, only 2 results were
exact, 5 were within five days, and the median absolute error was 136 days. The feed's
retained roster history materially undercounted veteran service. Phase one therefore
uses a verified dated baseline, then calculates forward changes from StatsAPI. The
baseline is staged by `control_baseline.py`; stable ID links are accepted, exact-name
validation links require review, and unresolved identities remain unavailable. The
forward roll starts the day after the snapshot, caps service by official season, and
does not charge an option year twice when a midseason baseline already reflects it.

### Two-team holdout result

The 2026 Giants depth chart was added as a second-team holdout on 2026-09-08. Exact
normalized-name links were used only to measure the feed and never as production
identity. StatsAPI candidates covered 178 of 187 Padres rows (95.2%) and 185 of 188
Giants rows (98.4%).

The holdout confirmed that accumulated service and option history need a dated
external baseline. Raw from-zero service matched only 3 of 59 comparable Padres rows
and 1 of 61 Giants rows; median absolute error was 104 and 121 days, respectively.
Raw option counts matched 24 of 35 Padres rows and 30 of 51 Giants rows. These fields
must not be initialized from missing StatsAPI history.

Rule 5 is materially different and is suitable for the scalable CBA calculation path.
For rows with both values available, the calculated eligibility year matched 86 of 90
Padres references and 94 of 96 Giants references. Current Rule 5 eligibility matched
27 of 30 Padres labels and all 27 Giants labels. Phase one therefore uses FanGraphs
for the dated service/options baseline, StatsAPI for forward service/options changes
and the Rule 5 calculation, and a small transaction/identity queue for exceptions.
The Giants run also exposed and fixed a blank-FanGraphs-ID join defect: baseline rows
are now joined on both FanGraphs ID and reference player name, preventing blank IDs
from multiplying prospect rows.

## References

- MLB Service Time glossary: https://www.mlb.com/glossary/transactions/service-time
- MLB Minor League Options glossary:
  https://www.mlb.com/glossary/transactions/minor-league-options
- MLB Rule 5 Draft glossary: https://www.mlb.com/glossary/transactions/rule-5-draft
- MLB Salary Arbitration glossary:
  https://www.mlb.com/glossary/transactions/salary-arbitration
