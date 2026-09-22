# Clean-slate hitter model: blind-spot audit

Status: **major forecast paths audited; 2026 remains sealed**

## Bottom line

The current hitter model is no longer just a batting forecast. It now separates five
questions that should not be confused:

1. How good is the player's batting?
2. Will he reach or remain in MLB, and how much will he play?
3. What position will he play?
4. How much value will he add on the bases?
5. If he catches, how much value will he add through throwing, blocking, and framing?

The major lesson from the audit is that useful information belongs in the path it
actually describes. Forty-man status helps playing time, not batting skill. Park and
opponent context helps describe past results, but the current historical coverage is
too thin to improve future value reliably. Catcher defense works when modeled in its
own native components, while generic fielding does not yet work well enough.

## What was tested and decided

### Keep: 40-man status for workload only

Exact October 15 roster membership improved expected-PA RMSE from 61.16 to 60.82 and
improved both arrival probability scores. It improved all six forward seasons.

Putting the same fields into batting-value models changed RMSE by only 0.0003, with an
uncertainty range spanning help and harm. Rescaling position and baserunning with the
new workload was also effectively neutral. The correct use is narrow: roster status
changes a player's path to playing time, not our estimate of his hitting talent.

### Keep: position

The role-transition model improved partial-WAR RMSE clearly across 2022-2025. This is
not merely a catcher or 2025 effect. Position is a durable part of the base model.

### Keep with an uncertainty label: baserunning

The baserunning model clearly predicts future steals and non-steal advancement better
than assuming every player is average. Its extra improvement after batting and
position is small and seasonally inconsistent. It remains because it is a real,
separately measured additive component, not because its whole-stack result is large.

### Keep provisionally: catcher defense

A fresh direct model uses public throwing, blocking, and framing results from the
source season, shrinks them using only earlier year-to-year transitions, forecasts
native opportunities from expected MLB PA, and converts them to runs.

- component RMSE: 0.0976 neutral to 0.0861 modeled;
- full target RMSE: 0.4515 neutral to 0.4488 modeled;
- all three target seasons, 2023-2025, improved;
- framing is the strongest contributor;
- throwing and blocking are favorable but individually uncertain.

The component improvement is clear. The whole-player improvement range narrowly
crosses zero, so this is selected for development and reserved for final 2026
confirmation.

### Do not keep: current general-position defense

The rebuilt exposure model forecasts defensive innings much better, including for
players entering MLB. Even with that repair, the public general-defense skill and run
layer slightly worsened total-value RMSE. The remaining problem is skill/value signal,
not mainly playing-time exposure. General defense stays neutral.

### Do not keep: current park/opponent package

Park, opposing-pitcher quality, and handedness are important descriptions of what
happened. The chronology-safe package has complete coverage only from 2021 onward and
helped one modern season while hurting another. It has not earned inclusion in the
forecast. Continue building the history, but do not force it into the model merely
because the variables make baseball sense.

### Do not keep: team position caps or depth penalties in portable value

A broad team playing-time cap was almost neutral for hitters. Rigid position caps
were harmful, and a flexible reallocation model still did not beat the broad cap.
Roster crowding may matter when assigning a player to a specific current team, but it
should not reduce organization-neutral player value.

## Important blind spots still open

### 1. Older affiliated position and fielding coverage

The best role history begins in 2021, so position, baserunning, and defense tests do
not span the full 2016-2025 batting history. Older official fielding coverage would
strengthen aging and level-transition evidence, but it should not block the batting
model already validated on the longer panel.

### 2. Complete 2025 source snapshot

The final 2026 forecast should not be fit until the 2025 play-by-play and component
sources are complete and frozen. This is a data-completeness requirement, not an
invitation to inspect 2026 results.

## Lower-priority ideas and why

- **Platoon splits and batter handedness:** potentially useful, but require enough
  opportunities and stable historical opponent-hand coverage. Test as a skill-rate
  split, not as dozens of sparse bins.
- **Options and transaction history:** likely useful for arrival and workload, but
  source semantics must distinguish an actual option from an ordinary assignment.
- **Organization development effects:** difficult to separate from which players an
  organization acquires. Any test needs player and time controls and must remain
  portable across organizations.
- **Prospect rankings or scouting grades:** potentially valuable for young players,
  but not universal, not consistently historical, and difficult to reproduce. They
  belong in a separately labeled evidence layer, not the public-data core.
- **Lineup slot, inning, weather, and time of day:** useful for valuing individual
  events and park context, but mostly describe opportunity and environment rather
  than durable player skill. More bins are not automatically more information; sparse
  bins can add noise and let the model memorize circumstances.

## Offseason injury history was tested and closed

The audit reconstructed official 2015-2024 disabled-list and injured-list
transactions through each October 15 cutoff. Broad prior placements, days missed,
60-day placements, current IL state, and current-spell duration were tested against
next-season PA and MLB participation.

Adding the fields to the full roster-aware workload ensemble improved PA RMSE from
60.82 to 60.70, but the uncertainty range crossed zero, MAE worsened, and both Brier
score and log loss worsened. A narrower established-player PA correction improved
RMSE only from 60.82 to 60.78 and again worsened MAE. Neither version is selected.

This closes broad transaction-count tuning on the exposed seasons. Reopening injury
work requires genuinely better information, such as consistent diagnosis/procedure
categories or a validated recovery-state source.

## Combined uncertainty is now implemented

The selected ranges are calibrated from errors in the complete partial-value stack,
not by adding separate batting, position, baserunning, and catcher ranges as if their
errors were independent. The most recent prior comparable season is used because it
was better calibrated than pooling the short modern history.

Across the two scoreable folds, 50%, 80%, and 90% ranges covered 47.9%, 78.5%, and
88.7%. In the most recent 2025 fold they covered 52.2%, 81.5%, and 90.0%. Current MLB
and lower-minors ranges were close to nominal; upper-minors coverage remains the weak
spot.

## Current development architecture

- batting value: equal mean of five complementary models;
- expected PA and arrival: the five-model workload ensemble plus 40-man evidence;
- position: confirmed role transition, scaled by the roster-blind component workload;
- baserunning: steals plus non-steal advancement;
- catcher defense: direct public throwing, blocking, and framing persistence with
  chronological shrinkage;
- general defense: neutral;
- 2026 outcomes: untouched.

The next build should complete and freeze the 2025 source snapshot, then fit the sealed
2026 forecast without accessing 2026 outcomes.
