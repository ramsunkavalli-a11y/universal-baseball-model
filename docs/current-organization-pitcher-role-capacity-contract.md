# Current-organization pitcher role capacity contract

Status: frozen before the 2025 confirmation and current-team scoring run.

## Question

Do controlled pitcher workload paths claim more starter, swingman, or relief batters faced than one current organization can reasonably supply?

This is a roster-context question. It is not a new pitcher talent model and it must not change the organization-neutral trade-value view.

## Evidence and chronology

- Development seasons: 2021-2024 MLB team pitching totals from the certified StatsAPI season-stat source.
- Confirmation season: 2025, used only after the development rule and role definitions are frozen.
- Current application: the existing 2026-2032 controlled pitcher paths and current organization ownership.
- No outside FV, prospect ranking, contract opinion, or future outcome is an input.

## Historical role definitions

For each observed pitcher-team-season:

- `STARTER`: starts are at least half of games pitched.
- `SWINGMAN`: at least one start, but starts are less than half of games pitched.
- `RELIEVER`: zero starts.

Every observed batter faced is assigned to exactly one role. Low-workload pitchers remain in the evidence; their small batter-faced totals naturally limit their influence.

For each team-season, calculate the share of team batters faced assigned to each role. The development capacity for a role is its median 2021-2024 team share, normalized so the three capacities sum to one team workload pool.

## Current allocation

Each player's already team-capped expected batters faced is divided fractionally using the existing conditional probabilities of starter, swingman, and reliever roles. This avoids turning the highest probability into a false certain role.

Within each organization-season-role:

1. Sum controlled expected batters faced.
2. Compare that sum with the frozen role capacity.
3. If it exceeds capacity, reduce every player-role component proportionally.
4. If it is below capacity, do not increase any player. Keep the unused share explicit.
5. Sum the three adjusted role components back to a player total.

## Required checks

- Historical role shares close to one for every team-season.
- Frozen capacity shares sum to one.
- Current role probabilities are finite, nonnegative, and sum to one within tolerance.
- Role capacities sum to the existing team pitcher capacity.
- No player or role component is increased.
- The 2025 season is reported as a descriptive stability check, not used to revise the frozen rule.
- Talent rates, WAR rates, contract status, and portable trade values remain unchanged.

## Decision rule

Keep this as a current-organization scenario layer only if it closes mechanically and gives interpretable capacity pressure. Historical replay of roster construction is required before it can affect any displayed team-fit result. It cannot affect the organization-neutral ranking in this phase.

